#!/usr/bin/env -S uv run python
"""Every dispatch the site accepts is one it deploys, and the other way round.

digline/digline tells this repository to rebuild by a `repository_dispatch`:
`digline-release` when a version is on PyPI, and `digline-docs` when its
documentation moved on `main`. A dispatch type has to be in two places in
.github/workflows/docs.yml, and the two go together:

  * in `on.repository_dispatch.types`, or the dispatch starts nothing;
  * in the Deploy job's `if:`, as `github.event.action == '<type>'`, or the
    dispatch builds the site and stops there. That is the defect digline#521
    describes the other way round: a change that reaches digline's `main` and
    not the site.

So this fails on:

  * a type the workflow accepts and does not deploy;
  * a type the Deploy condition names and the workflow does not accept — a
    condition no event can reach;
  * either of the two types digline sends, missing from the workflow;
  * a branch of the Deploy condition that reads a dispatch's action without
    asking, in that branch, whether the event is a dispatch.

It reads the one workflow. It does not prove that digline sends the dispatch:
that half lives in digline's own workflows, and is checked there.

    usage: tools/check-deploy.py [.github/workflows/docs.yml]
           tools/check-deploy.py --selftest

--selftest needs no network: it writes a workflow of each shape in turn and
checks each is refused or passed.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile

import yaml

#: What digline/digline sends, and why each one rebuilds the site.
SENT = {
    "digline-release": "publish.yml, once a version is on PyPI: the docs at its tag",
    "digline-docs": "a push to digline's main that moved its docs: the docs at main's tip",
}

ACTION = re.compile(r"github\.event\.action\s*==\s*'(?P<type>[^']+)'")
IS_DISPATCH = "github.event_name == 'repository_dispatch'"


def problems(path: str) -> tuple[list[str], set[str]]:
    """(problems, the dispatch types the workflow accepts)."""
    with open(path, encoding="utf-8") as fh:
        workflow = yaml.safe_load(fh)
    # PyYAML reads the key `on` as the boolean True.
    on = workflow.get(True) or workflow.get("on") or {}
    accepted = set((on.get("repository_dispatch") or {}).get("types") or [])
    condition = str(((workflow.get("jobs") or {}).get("deploy") or {}).get("if") or "")
    deployed = {match.group("type") for match in ACTION.finditer(condition)}
    found: list[str] = []
    for kind in sorted(accepted - deployed):
        found.append(f"{kind}: accepted as a dispatch and not in the Deploy job's `if:`, so it builds "
                     "the site and does not publish it")
    for kind in sorted(deployed - accepted):
        found.append(f"{kind}: named in the Deploy job's `if:` and not in on.repository_dispatch.types, "
                     "so no event reaches that branch of the condition")
    for kind, why in SENT.items():
        if kind not in accepted:
            found.append(f"{kind}: digline sends it ({why}), and the workflow does not accept it")
    # Branch by branch: a dispatch asked about in one branch does not cover an
    # action read in another.
    for branch in condition.split("||"):
        named = ACTION.search(branch)
        if named and IS_DISPATCH not in branch:
            found.append(f"{named.group('type')}: the Deploy job's `if:` reads github.event.action "
                         f"without `{IS_DISPATCH}` in the same branch")
    return found, accepted


_WORKFLOW = """name: docs
on:
  push:
    branches: [main]
  repository_dispatch:
    types: [{types}]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - run: echo build
  deploy:
    needs: build
    if: >-
      (github.event_name == 'push' && github.ref == 'refs/heads/main'){condition}
    runs-on: ubuntu-latest
    steps:
      - run: echo deploy
"""


def _branch(kind: str, *, ask: bool = True) -> str:
    event = f"{IS_DISPATCH} && " if ask else ""
    return f" ||\n      ({event}github.event.action == '{kind}')"


def selftest() -> int:
    failures: list[str] = []
    both = "digline-release, digline-docs"
    cases = [
        ("both types, accepted and deployed",
         both, _branch("digline-release") + _branch("digline-docs"), None),
        ("the docs dispatch accepted and not deployed",
         both, _branch("digline-release"), "digline-docs: accepted as a dispatch and not in"),
        ("the docs dispatch deployed and not accepted",
         "digline-release", _branch("digline-release") + _branch("digline-docs"),
         "digline-docs: named in the Deploy job's `if:` and not in"),
        ("the docs dispatch missing from both",
         "digline-release", _branch("digline-release"),
         "digline-docs: digline sends it"),
        ("the release dispatch missing from both",
         "digline-docs", _branch("digline-docs"),
         "digline-release: digline sends it"),
        ("a condition that does not ask whether the event is a dispatch",
         both, _branch("digline-release") + _branch("digline-docs", ask=False),
         "digline-docs: the Deploy job's `if:` reads github.event.action without"),
    ]
    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "docs.yml")
        for label, types, condition, needle in cases:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(_WORKFLOW.format(types=types, condition=condition))
            found, _ = problems(path)
            if needle is None:
                if found:
                    failures.append(f"{label}: refused, and it must pass ({found})")
                else:
                    print(f"deploy selftest: passes, as it must — {label}")
            elif not any(needle in problem for problem in found):
                failures.append(f"{label}: not refused ({found})")
            else:
                print(f"deploy selftest: refused, as it must — {label}")

    for failure in failures:
        print(f"deploy selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("deploy selftest: both dispatches accepted and deployed pass; a type accepted and not deployed, "
          "deployed and not accepted, either of digline's two missing, and a condition that does not ask "
          "for a dispatch are refused")
    return 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    if len(argv) > 1:
        print(__doc__.split("\n\n")[-2], file=sys.stderr)
        return 2
    path = argv[0] if argv else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                             ".github", "workflows", "docs.yml")
    found, accepted = problems(path)
    for problem in found:
        print(f"deploy: {problem}", file=sys.stderr)
    if found:
        return 1
    print(f"deploy: {len(accepted)} dispatch type(s) in {os.path.basename(path)}, every one accepted and "
          f"deployed: {', '.join(sorted(accepted))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
