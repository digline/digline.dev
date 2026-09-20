#!/usr/bin/env -S uv run python
"""Every action a workflow uses, pinned to a full commit, with its tag beside it.

A tag is a name the other repository can move: `actions/checkout@v5` is
whatever that repository decides `v5` means on the morning the job runs, and a
branch is worse. What runs in CI here — with a token, on a push to `main` —
has to be a commit nobody can change under us. So every `uses:` in
.github/workflows/ is a 40-character commit sha, and the version it was is
written after it as a comment, because a sha alone says nothing to a reader:

    uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09 # v5.1.0

This reads the workflows and fails on:

  * a tag (`@v5`), a branch (`@main`) or a short sha — anything that is not
    40 hexadecimal characters;
  * a pinned action with no comment after it, or a comment that does not name
    a version (`# v5.1.0`, `# v5`): the sha is then a number no one can read,
    and RUNBOOK.md's procedure for updating it has nothing to check against.

A local action (`uses: ./…`) and a container (`uses: docker://…`) are not
pinned this way and are left alone; there are none here today.

    usage: tools/check-actions.py [.github/workflows]
           tools/check-actions.py --selftest

--selftest needs no network: it writes workflows with each of those failures
in turn, and one that is pinned as it should be, and checks each is refused or
passed.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile

# `uses:` as a workflow writes it, with whatever follows on the line.
USES = re.compile(r"^\s*(?:-\s*)?uses:\s*(?P<ref>\S+)\s*(?P<rest>.*?)\s*$")
SHA = re.compile(r"\A[0-9a-f]{40}\Z")
# The comment after it: a version, as the other repository tags it.
VERSION = re.compile(r"\A#\s*(?P<tag>v?\d+(?:\.\d+)*(?:[-.][0-9A-Za-z.]+)?)\s*$")
LOCAL = ("./", "docker://")


def problems(folder: str) -> tuple[list[str], int]:
    """(problems, actions read) over every workflow in `folder`."""
    found: list[str] = []
    read = 0
    for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
        if not name.endswith((".yml", ".yaml")):
            continue
        with open(os.path.join(folder, name), encoding="utf-8") as fh:
            for number, line in enumerate(fh, start=1):
                match = USES.match(line.rstrip("\n"))
                if not match:
                    continue
                ref, rest = match.group("ref"), match.group("rest")
                if ref.startswith(LOCAL):
                    continue
                read += 1
                where = f"{name}:{number}"
                action, _, version = ref.partition("@")
                if not SHA.match(version):
                    what = "nothing" if not version else f"{version!r}"
                    found.append(f"{where}: {action} is used at {what}, and an action is used at a full "
                                 "40-character commit — a tag and a branch move under us")
                elif not VERSION.match(rest):
                    found.append(f"{where}: {action} is pinned, and the version it is at is not written after "
                                 f"it — {rest!r}, wanted a comment naming the tag, as in `# v5.1.0`")
    return found, read


def selftest() -> int:
    failures: list[str] = []
    pinned = "      - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09 # v5.1.0\n"
    header = "name: t\non: push\njobs:\n  a:\n    runs-on: ubuntu-latest\n    steps:\n"
    cases = [
        ("a full sha with its tag", pinned, None),
        ("a full sha with a tag and words after it",
         "      - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09 # v5.1.0\n", None),
        ("a local action", "      - uses: ./.github/actions/thing\n", None),
        ("a step that only runs a command", "      - run: echo uses: actions/checkout@v5\n", None),
        ("a tag", "      - uses: actions/checkout@v5\n", "is used at 'v5'"),
        ("a branch", "      - uses: actions/checkout@main\n", "is used at 'main'"),
        ("a short sha", "      - uses: actions/checkout@fbc6f39\n", "is used at 'fbc6f39'"),
        ("a sha of 39 characters", "      - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c0\n",
         "is used at 'fbc6f3992d24b796d5a048ff273f7fcc4a7b6c0'"),
        ("no version at all", "      - uses: actions/checkout\n", "is used at nothing"),
        ("a full sha with no comment", "      - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09\n",
         "the version it is at is not written"),
        ("a full sha with a comment that names no version",
         "      - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09 # the checkout\n",
         "the version it is at is not written"),
        ("a full sha commented with a branch",
         "      - uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09 # main\n",
         "the version it is at is not written"),
    ]
    with tempfile.TemporaryDirectory() as folder:
        for label, step, needle in cases:
            with open(os.path.join(folder, "t.yml"), "w", encoding="utf-8") as fh:
                fh.write(header + pinned + step)
            found, read = problems(folder)
            if needle is None:
                if found:
                    failures.append(f"{label}: refused, and it must pass ({found})")
                else:
                    print(f"actions selftest: passes, as it must — {label}")
            elif not any(needle in problem for problem in found):
                failures.append(f"{label}: not refused ({found})")
            else:
                print(f"actions selftest: refused, as it must — {label}")
        # A folder of several workflows: every one is read, and the count is
        # what it found, not what the last file had.
        with open(os.path.join(folder, "t.yml"), "w", encoding="utf-8") as fh:
            fh.write(header + pinned + pinned)
        with open(os.path.join(folder, "u.yaml"), "w", encoding="utf-8") as fh:
            fh.write(header + "      - uses: actions/checkout@v5\n")
        found, read = problems(folder)
        if (read, len(found)) != (3, 1) or "u.yaml:7" not in found[0]:
            failures.append(f"several workflows: read {read}, found {found}")
        else:
            print("actions selftest: every workflow of the folder read, each line said with its file")

    for failure in failures:
        print(f"actions selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("actions selftest: a pinned action with its tag, a local action and a command pass; a tag, a "
          "branch, a short sha, a sha one character short, no version, and a pin with no version after it "
          "are refused")
    return 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    if len(argv) > 1:
        print(__doc__.split("\n\n")[-2], file=sys.stderr)
        return 2
    folder = argv[0] if argv else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                               ".github", "workflows")
    found, read = problems(folder)
    for problem in found:
        print(f"actions: {problem}", file=sys.stderr)
    if found:
        return 1
    print(f"actions: {read} action(s) in {os.path.basename(folder)}, every one at a full commit with its "
          "version beside it")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
