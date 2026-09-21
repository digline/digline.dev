#!/usr/bin/env python3
"""The Makefile's own targets, held to the one thing make will not tell you.

`make` accepts a Makefile that declares the same target twice. It keeps the
last recipe, drops the first without a word, and every target that depended on
the name still runs — the other recipe simply never does again.

That happened here. `opening:` was declared at line 39, running
`tools/hooks/opening.py --selftest`, and again at line 70, running
`tools/check-opening.py --selftest`. `build:` lists `opening` once, so for as
long as both were there **the hook's selftest never ran**: not in `make build`,
not in `make opening`, not in CI. Nothing was red. A gate that has stopped
running looks exactly like a gate that passes.

Three things are refused, each of them something make is happy to accept:

  * **a target declared more than once.** The defect above. Whatever the
    earlier recipe did is gone, and the name that used to mean both now means
    one.
  * **a target missing from `.PHONY`.** Every target here is a command, not a
    file: left out of `.PHONY`, it stops running the day a file of that name
    appears in the directory. A target that *is* a file in the tree is allowed
    and left alone, which is what `.PHONY` is for distinguishing.
  * **a name in `.PHONY` with no target.** A target renamed or deleted, with
    its old name still declared: harmless, and a lie about what this file can
    do.

And one about the dependency graph, since it is free to check here:

  * **a prerequisite naming no target.** `make` fails on it at the moment
    somebody runs that target, which may be months after the typo; this fails
    on the file.

    usage: tools/check-make.py [Makefile]
           tools/check-make.py --selftest

--selftest needs no make: it writes a Makefile with each failure in turn, and
one that is as it should be, and checks each is refused or passed.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile

# A target line: a name at column zero, then a colon that is not `:=`.
TARGET = re.compile(r"^(?P<name>[A-Za-z0-9_.@%-]+)\s*:(?!=)(?P<needs>[^=].*)?$")
PHONY = ".PHONY"


def read(path: str) -> tuple[dict[str, list[int]], dict[str, list[str]], list[str]]:
    """(targets → the lines declaring each, target → its prerequisites, .PHONY names)."""
    targets: dict[str, list[int]] = {}
    needs: dict[str, list[str]] = {}
    phony: list[str] = []
    with open(path, encoding="utf-8") as fh:
        for number, line in enumerate(fh, start=1):
            line = line.rstrip("\n")
            if line.startswith("\t") or not line.strip() or line.lstrip().startswith("#"):
                continue
            match = TARGET.match(line)
            if not match:
                continue
            name = match.group("name")
            # The prerequisites, with make's `## help` comment taken off.
            rest = (match.group("needs") or "").split("##")[0].split()
            if name == PHONY:
                phony.extend(rest)
                continue
            targets.setdefault(name, []).append(number)
            needs.setdefault(name, []).extend(rest)
    return targets, needs, phony


def problems(path: str) -> tuple[list[str], int]:
    """(problems, targets read) for one Makefile."""
    targets, needs, phony = read(path)
    where = os.path.dirname(os.path.abspath(path)) or "."
    found: list[str] = []

    for name, lines in sorted(targets.items()):
        if len(lines) > 1:
            listed = ", ".join(str(line) for line in lines)
            found.append(
                f"{name}: declared on lines {listed} — make keeps the last recipe and "
                f"drops the others without a word, so whatever the earlier one ran no "
                f"longer runs. Put the commands under one target")

    for name in sorted(targets):
        if name not in phony and not os.path.exists(os.path.join(where, name)):
            found.append(
                f"{name}: not in {PHONY} — it is a command, not a file, and it stops "
                f"running the day something called {name!r} appears here")

    for name in sorted(set(phony)):
        if name not in targets:
            found.append(f"{PHONY} names {name!r} and there is no such target — it was renamed or removed")

    for name, wants in sorted(needs.items()):
        for want in wants:
            if want not in targets and not os.path.exists(os.path.join(where, want)):
                found.append(
                    f"{name}: needs {want!r}, which is neither a target nor a file — "
                    f"make would fail on this the day somebody runs {name}")

    return found, len(targets)


GOOD = """\
.PHONY: one two both

one:             ## the first
\techo one

two:             ## the second
\techo two

both: one two    ## everything
\techo both
"""


def selftest() -> int:
    failures = []
    cases = [
        (GOOD, None, "a Makefile that is as it should be"),
        (GOOD.replace("two:             ## the second\n\techo two",
                      "two:             ## the second\n\techo two\n\ntwo:             ## again\n\techo other"),
         "declared on lines", "the same target twice — the defect this exists for"),
        (GOOD.replace(".PHONY: one two both", ".PHONY: one both"),
         f"not in {PHONY}", "a target left out of .PHONY"),
        (GOOD.replace(".PHONY: one two both", ".PHONY: one two both gone"),
         "no such target", "a .PHONY name with no target"),
        (GOOD.replace("both: one two", "both: one tow"),
         "neither a target nor a file", "a prerequisite that is a typo"),
    ]
    for body, expected, why in cases:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "Makefile")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(body)
            found, read_count = problems(path)
            if expected is None:
                if found:
                    failures.append(f"{why}: refused — {found}")
                if read_count != 3:
                    failures.append(f"{why}: {read_count} targets read, not 3")
            elif not any(expected in problem for problem in found):
                failures.append(f"{why}: passed, or was refused for another reason — {found}")

    # A target that IS a file is not a phony target, and is left alone.
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "Makefile")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(".PHONY: one\n\none:\n\techo one\n\nsite:\n\techo build\n")
        open(os.path.join(tmp, "site"), "w").close()
        found, _ = problems(path)
        if found:
            failures.append(f"a target that is a real file was refused: {found}")

    for failure in failures:
        print(f"check-make selftest: FAILED — {failure}", file=sys.stderr)
    if not failures:
        print("check-make selftest: a target declared twice, one left out of .PHONY, a .PHONY name "
              "with no target and a mistyped prerequisite each refused; a correct Makefile and a "
              "target that is a real file each passed")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    if argv[1:] == ["--selftest"]:
        return selftest()
    path = argv[1] if argv[1:] else "Makefile"
    if not os.path.isfile(path):
        print(f"check-make: no {path}", file=sys.stderr)
        return 1
    found, read_count = problems(path)
    for problem in found:
        print(f"check-make: {problem}", file=sys.stderr)
    if found:
        return 1
    print(f"check-make: {read_count} targets, each declared once, each in {PHONY}, every prerequisite a target")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
