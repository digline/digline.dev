"""/product/operator/ describes why an operator exists, and not how one works.

That page is written here, in pages/product/operator.md — it is a page about a
way digline is *used*, and digline's own docs/ has no home for one. Everything
it describes, though, lives in the other repository and changes there:
`examples/operator/` is the loop, its alerts, its configuration and its code.

The page was, for twelve days, a copy of that example's DESIGN.md with a
section taken out. DESIGN.md was amended twice in the meantime and the copy was
not, so the page said *two* alerts shipped where three did, and named `compare`
and `diff` for a layer the loop renders from `explain`. Nothing saw it: both
sentences were well formed, every link resolved, and no gate here reads the
other repository's example.

So the rule is the one RUNBOOK.md states, and this is its gate:

    A page written here may name a public API name, linked to its own page.
    It may not state a count, a command, an internal file or a decision rule
    that belongs to digline — those are the other repository's to state, and
    they change there.

Three things are refused on the built page, each read from .operator-facts.json,
which tools/sync-docs.sh writes from the checkout it copies (tools/operator_facts.py):

  * **a count of the alerts that is not the number that ship.** A cardinal —
    a digit, or `one` through `twelve` — immediately before "alert" or
    "alerts". Not *any* number near the word: the page is allowed to say "an
    alert is a document in three layers" about something that is not a count
    of alerts, and a gate that cannot tell those apart would be turned off.
  * **a digline command, named as code.** Every `<code>` whose whole text is a
    subcommand of the CLI. `promote` is the one exception and is named in
    ALLOWED below, with the reason: the page's argument is that it is *absent*
    from the operator's surface, so the word has to appear for the page to
    make its point at all.
  * **an internal file of the example, named as code.** Every `<code>` whose
    whole text is a file directly under `examples/operator/`: `loop.py`,
    `operator.toml`, `.mcp.json`. A page that names one is describing its
    contents, and its contents are not here.

── warning, then error ───────────────────────────────────────────────────────
FAIL below decides whether a disagreement stops the build. It ships as False:
the gate arrives while the page still breaks it in three places, and a gate
that turns `main` red on the commit that introduces it teaches everyone to
skip it. The page is rewritten next, and FAIL goes True in the same change —
which is the commit where the gate starts meaning something.

Named operator_page.py, not operator.py: a module called `operator` in a
folder Python puts on the path shadows the standard library's, and `collections`
imports that one — so the hook fails on import, in a traceback about `re`.

    usage: tools/hooks/operator_page.py --selftest
"""

from __future__ import annotations

import html as htmllib
import json
import os
import re
import sys
import tempfile

FACTS_FILE = ".operator-facts.json"
PAGE = "product/operator/index.html"
FAIL = False

# `promote`, and nothing else. The page says it is not on the operator's
# surface — not refused, absent — which is the whole of its argument about what
# an agent may not do. A gate that refused the word would refuse the sentence
# the page exists to make.
ALLOWED = ("promote",)

CARDINALS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}

_CODE = re.compile(r"<code[^>]*>(.*?)</code>", re.S | re.I)
_TAGS = re.compile(r"<[^>]+>")
# A word, then "alert"/"alerts". The word is looked up in CARDINALS; anything
# else — "the alerts", "real alerts" — is not a count and is not read as one.
_BEFORE_ALERT = re.compile(r"(\w+)\s+alerts?\b", re.I)


def facts(root: str) -> dict:
    """.operator-facts.json, refused when it cannot hold a page to anything."""
    path = os.path.join(root, FACTS_FILE)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        raise SystemExit(f"operator: {FACTS_FILE} is missing — tools/sync-docs.sh writes it before every build")
    except json.JSONDecodeError as broken:
        raise SystemExit(f"operator: {FACTS_FILE} is not readable JSON: {broken}")
    for key in ("alerts", "files", "commands"):
        if not data.get(key):
            raise SystemExit(f"operator: {FACTS_FILE} has no {key}: there is nothing to hold the page to")
    return data


def text_of(page: str) -> str:
    """The page's readable text, tags gone and entities resolved."""
    return htmllib.unescape(_TAGS.sub(" ", page))


def code_spans(page: str) -> list[str]:
    """The whole text of every <code>, entities resolved, stripped."""
    return [htmllib.unescape(_TAGS.sub("", found.group(1))).strip() for found in _CODE.finditer(page)]


def problems(page: str, data: dict) -> list[str]:
    """Every way the page states something that is the example's to state."""
    found: list[str] = []
    shipped = len(data["alerts"])

    for match in _BEFORE_ALERT.finditer(text_of(page)):
        word = match.group(1).lower()
        said = CARDINALS.get(word, int(word) if word.isdigit() else None)
        if said is not None and said != shipped:
            found.append(
                f"the page says {match.group(0)!r}, and {shipped} ship "
                f"({', '.join(data['alerts'])}). A count of what the example holds is the "
                "example's to state: link it instead")

    commands = {name for name in data["commands"] if name not in ALLOWED}
    internal = set(data["files"])
    for span in code_spans(page):
        if span in commands:
            found.append(
                f"the page names the command `{span}` — a command belongs to digline and moves "
                "there. Say what the operator is for and link the example, which names its own")
        if span in internal:
            found.append(
                f"the page names `{span}`, a file of {data['source']} — a page here that names it "
                "is describing contents it does not hold")
    return found


def on_post_build(config, **kwargs):  # noqa: ANN001 — mkdocs' signature
    site = config["site_dir"]
    root = os.path.dirname(os.path.abspath(config["config_file_path"]))
    path = os.path.join(site, PAGE)
    if not os.path.exists(path):
        raise SystemExit(f"operator: {PAGE} is not in the build — the page this gate is about is gone")
    with open(path, encoding="utf-8") as fh:
        page = fh.read()
    found = problems(page, facts(root))
    if not found:
        print(f"operator: {PAGE} states no count, command or file of the example")
        return
    for problem in found:
        print(f"operator: {problem}", file=sys.stderr)
    if FAIL:
        raise SystemExit(f"operator: {len(found)} thing(s) on {PAGE} that belong to digline (above)")
    print(f"operator: {len(found)} warning(s) — not failing the build yet (FAIL is False in tools/hooks/operator_page.py)",
          file=sys.stderr)


def selftest() -> int:
    failures = []
    data = {
        "source": "examples/operator/",
        "alerts": ["draw.md", "drift.md", "held.md"],
        "files": ["loop.py", "operator.toml", ".mcp.json"],
        "commands": ["run", "compare", "diff", "promote", "explain"],
    }

    clean = ("<p>An <code>HttpTarget</code> exists for this, and real alerts ship beside it. "
             "<code>promote</code> is not on the operator's surface. An alert is a document "
             "in three layers.</p>")
    if problems(clean, data):
        failures.append(f"a page that keeps the rule was refused: {problems(clean, data)}")

    for page, why in (
        ("<p>Two alerts the loop produced ship with it.</p>", "a wrong count in words"),
        ("<p>It ships 2 alerts.</p>", "a wrong count in digits"),
        ("<p>the <code>compare</code> or <code>diff</code> JSON</p>", "a command named as code"),
        ("<p>an <code>.mcp.json</code> for the interactive path</p>", "an internal file named as code"),
    ):
        if not problems(page, data):
            failures.append(f"{why}: passed")

    # The count that is right is not a problem, and neither is a number that is
    # not a count of alerts — the two the gate has to tell apart.
    if problems("<p>Three alerts ship with it.</p>", data):
        failures.append("the right count was refused")
    if problems("<p>An alert is a document in three layers.</p>", data):
        failures.append("'three layers' was read as a count of alerts")
    if problems("<p><code>promote</code> is absent from the surface.</p>", data):
        failures.append("`promote` was refused, and the page's argument needs the word")

    for key in ("alerts", "files", "commands"):
        with tempfile.TemporaryDirectory() as tmp:
            short = {k: v for k, v in data.items() if k != key}
            with open(os.path.join(tmp, FACTS_FILE), "w", encoding="utf-8") as fh:
                json.dump(short, fh)
            try:
                facts(tmp)
                failures.append(f"a fact file with no {key} was accepted")
            except SystemExit:
                pass
    with tempfile.TemporaryDirectory() as tmp:
        try:
            facts(tmp)
            failures.append("a missing fact file was accepted")
        except SystemExit:
            pass

    for failure in failures:
        print(f"operator selftest: FAILED — {failure}", file=sys.stderr)
    if not failures:
        print("operator selftest: a wrong count in words and in digits, a command and an internal file "
              "each refused; the right count, a number that is not a count, `promote` and a public API "
              "name each let through; a fact file missing or short of any list refused")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else __doc__)
