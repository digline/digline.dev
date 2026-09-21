#!/usr/bin/env python3
"""The countable facts about digline's operator example, for the page about it.

`/product/operator/` is written here, in pages/product/operator.md, and not
copied from digline: it is a page about *why* you would run an operator, for a
reader who arrived from /agents/. The mechanism — what the loop does, what it
decides, what it ships — belongs to digline, changes there, and is documented
there in `examples/operator/`.

That split is the rule. This file is what makes it checkable.

The page had drifted from it three ways at once, and each one was a fact the
page restated rather than linked: it said *two* alerts shipped when three did,
it named `compare` and `diff` where the loop renders from `explain`, and it
named files of the example whose contents it was describing from memory. None
of it was visible to a build: the sentences were well formed and the links all
resolved.

So the sync reads the example instead, and writes what a sentence here is not
allowed to claim on its own:

    {
      "source": "examples/operator/",
      "tag": "v0.17.1",
      "commit": "…",
      "alerts": ["draw.md", "drift.md", "held.md"],
      "files": ["answer.py", "cases.json", …],
      "commands": ["run", "rejudge", "compare", …]
    }

`alerts` and `files` are read from the checkout at the latest release tag, the
same tag /agents/ quotes AGENTS.md at — a page that describes the released tool
should not be measured against unreleased work. `commands` is copied from the
capture digline already publishes, `docs/assets/home/home.json`, whose own list
comes from argparse rather than from a list somebody keeps: the home already
stands behind it, and a second way of deriving it would be a second thing to be
wrong.

tools/hooks/operator.py reads the file back and holds the built page to it.

Standard library only: tools/sync-docs.sh runs it with the system's python3,
before any environment exists — the same reason tools/agents_rule.py is.

    usage: tools/operator_facts.py <digline checkout>      # JSON on stdout
           tools/operator_facts.py --selftest
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

EXAMPLE = "examples/operator"
HOME_JSON = "docs/assets/home/home.json"


def git(src: str, *args: str) -> str:
    return subprocess.run(["git", "-C", src, *args], check=True, capture_output=True, text=True).stdout.strip()


def released(src: str) -> list[str]:
    return git(src, "tag", "--merged", "HEAD", "--list", "v*", "--sort=-v:refname").splitlines()


def deepen(src: str) -> bool:
    """Give a shallow checkout the history its tags have to be tested against.

    The same shape, and the same reason, as tools/agents_rule.py: `--merged
    HEAD` walks from HEAD, and in a shallow clone that walk stops at the graft.
    """
    if git(src, "rev-parse", "--is-shallow-repository") != "true":
        return False
    subprocess.run(["git", "-C", src, "fetch", "--quiet", "--tags", "--unshallow", "origin"],
                   check=False, capture_output=True, text=True)
    return True


def listing(src: str, tag: str, folder: str) -> list[str]:
    """The file names directly under `folder` at `tag`, sorted, no directories."""
    out = git(src, "ls-tree", "--name-only", f"{tag}:{folder}")
    names = [line.strip() for line in out.splitlines() if line.strip()]
    # `ls-tree` on a tree lists directories too, and a directory is not a file
    # this page could name. A trailing slash is how git marks one in `-d`, but
    # a plain listing does not mark them, so they are asked for by name.
    directories = set(git(src, "ls-tree", "-d", "--name-only", f"{tag}:{folder}").splitlines())
    return sorted(name for name in names if name not in directories)


def commands(src: str, tag: str) -> list[str]:
    """digline's subcommands, as the capture behind the home page has them."""
    home = json.loads(git(src, "show", f"{tag}:{HOME_JSON}"))
    items = home.get("cli_commands", {}).get("items") or []
    found = [item if isinstance(item, str) else item.get("name") for item in items]
    return [name for name in found if name]


def read(src: str) -> dict:
    tags = released(src)
    if not tags and deepen(src):
        tags = released(src)
    if not tags:
        raise SystemExit(f"operator_facts: {src} contains no v* release tag: nothing released to describe")
    tag = tags[0]
    # The alerts are the documents. `alerts/` also holds the cycle each one was
    # written from — draw-cycle.json beside draw.md — which is the evidence, not
    # a third alert: counting those would make the page's number wrong in the
    # other direction.
    alerts = [name for name in listing(src, tag, f"{EXAMPLE}/alerts") if name.endswith(".md")]
    if not alerts:
        raise SystemExit(f"operator_facts: {EXAMPLE}/alerts at {tag} holds no alert: the page's claim has nothing to stand on")
    found = commands(src, tag)
    if not found:
        raise SystemExit(f"operator_facts: {HOME_JSON} at {tag} names no cli_commands: nothing to hold a command against")
    return {
        "source": f"{EXAMPLE}/",
        "tag": tag,
        "commit": git(src, "rev-parse", f"{tag}^{{commit}}"),
        "alerts": alerts,
        "files": listing(src, tag, EXAMPLE),
        "commands": found,
    }


def _repository(root: Path) -> None:
    """A repository shaped like digline's, small enough to read in one screen."""
    alerts = root / EXAMPLE / "alerts"
    alerts.mkdir(parents=True)
    for name in ("draw.md", "drift.md", "held.md"):
        (alerts / name).write_text(f"# {name}\n", encoding="utf-8")
    # The evidence beside each alert, which is not an alert.
    for name in ("draw-cycle.json", "drift-cycle.json", "held-decision.json"):
        (alerts / name).write_text("{}\n", encoding="utf-8")
    for name in ("loop.py", "dossier.py", "operator.toml"):
        (root / EXAMPLE / name).write_text("x\n", encoding="utf-8")
    home = root / HOME_JSON
    home.parent.mkdir(parents=True, exist_ok=True)
    home.write_text(json.dumps({"cli_commands": {"items": [{"name": "run"}, {"name": "compare"}, "explain"]}}),
                    encoding="utf-8")
    for args in (["init", "--quiet", "-b", "main", "."],
                 ["add", "-A"],
                 ["-c", "user.email=s@t", "-c", "user.name=s", "commit", "--quiet", "-m", "one"],
                 ["tag", "v0.1.0"]):
        subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True)


def selftest() -> int:
    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "digline"
        root.mkdir()
        _repository(root)
        facts = read(str(root))
        if facts["alerts"] != ["draw.md", "drift.md", "held.md"]:
            failures.append(f"alerts: {facts['alerts']!r} — the cycle beside each alert is not an alert")
        if "alerts" in facts["files"]:
            failures.append("files: the alerts/ directory is listed as a file")
        if facts["files"] != ["dossier.py", "loop.py", "operator.toml"]:
            failures.append(f"files: {facts['files']!r}")
        if facts["commands"] != ["run", "compare", "explain"]:
            failures.append(f"commands: {facts['commands']!r} — a string item and an object item both read")
        if facts["tag"] != "v0.1.0":
            failures.append(f"tag: {facts['tag']!r}")

        # An example with no alert at all: the page's count would have nothing
        # to be held against, and a fact file that says so is worse than none.
        bare = Path(tmp) / "bare"
        bare.mkdir()
        _repository(bare)
        for name in ("draw.md", "drift.md", "held.md"):
            (bare / EXAMPLE / "alerts" / name).unlink()
        (bare / EXAMPLE / "alerts" / ".keep").write_text("", encoding="utf-8")
        subprocess.run(["git", "-C", str(bare), "add", "-A"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(bare), "-c", "user.email=s@t", "-c", "user.name=s",
                        "commit", "--quiet", "-m", "two"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(bare), "tag", "-f", "v0.1.0"], check=True, capture_output=True)
        try:
            read(str(bare))
            # .keep is a file, so alerts is not empty — the refusal this covers
            # is the one below, where the folder itself is gone.
        except SystemExit:
            pass
        gone = Path(tmp) / "gone"
        gone.mkdir()
        _repository(gone)
        subprocess.run(["git", "-C", str(gone), "rm", "-r", "--quiet", f"{EXAMPLE}/alerts"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(gone), "-c", "user.email=s@t", "-c", "user.name=s",
                        "commit", "--quiet", "-m", "three"], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(gone), "tag", "-f", "v0.1.0"], check=True, capture_output=True)
        try:
            read(str(gone))
            failures.append("an example with no alerts/ at all was read rather than refused")
        except (SystemExit, subprocess.CalledProcessError):
            pass

    for failure in failures:
        print(f"operator_facts selftest: FAILED — {failure}", file=sys.stderr)
    if not failures:
        print("operator_facts selftest: the alerts, the example's files without its folders, and the "
              "commands read at the release tag; an example with no alerts refused")
    return 1 if failures else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        raise SystemExit(selftest())
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    print(json.dumps(read(sys.argv[1]), ensure_ascii=False, indent=2))
