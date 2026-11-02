#!/usr/bin/env -S uv run python
"""Every committed uv.lock, at the `revision` declared for it here.

The `revision` at the top of a lock is the format of the uv that last wrote
it, not something this repository chose: a uv that rewrites a lock writes its
own number. A pull request that only meant to move a version can move the
format with it, in a diff that reads as one more line. #233 was that: two
minor bumps from Dependabot, whose uv 0.13.5 also took the lock from 3 to 5.
It was set aside, and #235 applied the same two versions at 3.

So this reads two lists and holds them equal:

  * DECLARED below, written by hand: each lock, the `revision` it reads, and
    why;
  * `git ls-files -- uv.lock '*/uv.lock'`: the locks that are committed.

and fails on:

  * a committed lock with no row here, and a row here with no lock in the tree;
  * a lock whose `revision` is not the one declared for it, naming the file and
    both numbers.

A new lock is recorded, not assumed. A moved `revision` is either relocked with
the uv that wrote it, or its row changes here with the reason. Digline holds
its own locks the same way, in its tests/test_lock_revision.py.

    usage: tools/check-lock-revision.py [repository]
           tools/check-lock-revision.py --selftest

--selftest needs no network and does not read this repository's lock: it
builds a git repository of its own in a temporary folder, writes locks into it,
and checks that each case is refused or passed.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import tomllib

#: The lock, the `revision` it reads, and why it reads that.
DECLARED: dict[str, tuple[int, str]] = {
    "uv.lock": (
        3,
        "3 since #235 (ed4fe131, 2026-11-02), relocked with uv 0.11.14; "
        "Dependabot's uv 0.13.5 in #233 moved it to 5, and a version change "
        "does not change the lock's format",
    ),
}


def tracked(root: str) -> list[str] | None:
    """The committed locks under `root`, or None when git cannot say."""
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--", "uv.lock", "*/uv.lock"],
        cwd=root, capture_output=True, text=True, check=False,
    )
    if listed.returncode != 0:
        return None
    return sorted(entry for entry in listed.stdout.split("\0") if entry)


def problems(root: str, declared: dict[str, tuple[int, str]], locks: list[str]) -> list[str]:
    """One sentence per lock that has no row, per row that has no lock, and
    per lock that does not read its declared `revision`."""
    found: list[str] = []
    for name in sorted(set(locks) - set(declared)):
        found.append(f"{name}: committed, and has no row in DECLARED — record its revision "
                     "and why, rather than assuming one")
    for name, (expected, reason) in sorted(declared.items()):
        if name not in locks:
            found.append(f"{name}: declared here, and not a committed lock in the tree")
            continue
        with open(os.path.join(root, name), "rb") as fh:
            revision = tomllib.load(fh).get("revision")
        if revision != expected:
            found.append(f"{name}: revision {revision!r}, declared {expected} ({reason}). A uv other "
                         "than the one that wrote it has rewritten it: relock with that uv, or change "
                         "the row here and say why")
    return found


def selftest() -> int:
    failures: list[str] = []
    head = "version = 1\nrevision = {}\nrequires-python = \">=3.12\"\n"
    row = (3, "the selftest's own lock")
    with tempfile.TemporaryDirectory() as root:
        init = subprocess.run(["git", "init", "-q", root], capture_output=True, text=True, check=False)
        if init.returncode != 0:
            print(f"lock revision selftest: git init failed: {init.stderr.strip()}", file=sys.stderr)
            return 1

        def write(name: str, revision: object) -> None:
            path = os.path.join(root, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(head.format(revision) if revision is not None else "version = 1\n")
            subprocess.run(["git", "add", "--", name], cwd=root, check=True)

        def case(label: str, declared: dict[str, tuple[int, str]], needle: str | None) -> None:
            locks = tracked(root)
            if locks is None:
                failures.append(f"{label}: git could not list the locks")
                return
            found = problems(root, declared, locks)
            if needle is None:
                if found:
                    failures.append(f"{label}: refused, and it must pass ({found})")
                else:
                    print(f"lock revision selftest: passes, as it must — {label}")
            elif not any(needle in problem for problem in found):
                failures.append(f"{label}: not refused as {needle!r} ({found})")
            else:
                print(f"lock revision selftest: refused, as it must — {label}")

        write("uv.lock", 3)
        case("a lock at its declared revision", {"uv.lock": row}, None)
        write("uv.lock", 5)
        case("a lock moved from 3 to 5", {"uv.lock": row}, "uv.lock: revision 5, declared 3")
        write("uv.lock", None)
        case("a lock with no revision at all", {"uv.lock": row}, "uv.lock: revision None, declared 3")
        write("uv.lock", 3)
        write("examples/one/uv.lock", 3)
        case("a committed lock with no row", {"uv.lock": row}, "examples/one/uv.lock: committed, and has no row")
        case("both locks with their rows", {"uv.lock": row, "examples/one/uv.lock": row}, None)
        case("a row with no lock in the tree", {"uv.lock": row, "examples/one/uv.lock": row,
                                                 "examples/two/uv.lock": row},
             "examples/two/uv.lock: declared here, and not a committed lock")
        # A lock on disk that git does not hold is not a committed lock: it is
        # neither required to have a row nor read.
        path = os.path.join(root, "scratch", "uv.lock")
        os.makedirs(os.path.dirname(path))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(head.format(5))
        case("an untracked lock on disk", {"uv.lock": row, "examples/one/uv.lock": row}, None)

    for failure in failures:
        print(f"lock revision selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("lock revision selftest: a lock at its revision, two locks with their rows and an untracked "
          "lock pass; a lock moved to another revision, a lock with none, a committed lock with no row "
          "and a row with no lock are refused")
    return 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    if len(argv) > 1:
        print(__doc__.split("\n\n")[-2], file=sys.stderr)
        return 2
    root = argv[0] if argv else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    locks = tracked(root)
    if locks is None:
        print(f"lock revision: git could not list the committed locks in {root}", file=sys.stderr)
        return 1
    # The positive control: the site's own lock is committed, so an empty
    # listing is a broken query and not a tree with no locks.
    if "uv.lock" not in locks:
        print(f"lock revision: git lists no uv.lock at the root of {root} — {locks}", file=sys.stderr)
        return 1
    found = problems(root, DECLARED, locks)
    for problem in found:
        print(f"lock revision: {problem}", file=sys.stderr)
    if found:
        return 1
    print(f"lock revision: {len(locks)} committed lock(s), each with its row and at its declared revision")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
