"""The numbers on the home page, read out of what digline printed.

The home used to carry a console block typed into the template: the output of
digline 0.2.0, three minors after it stopped being true. Everything the home now
shows about the tool — the version, the run ids, every line of output, the
checks that got worse, the dependency list — comes from one file:

    docs/product/assets/home/home.json

written in digline/digline by ``tools/home_capture.py``, which runs the CLI and
records each command's stdout, stderr and exit code, and copied here by
``tools/sync-docs.sh`` with the rest of ``docs/``.

This hook reads that file, refuses it when it cannot stand behind it, and works
out in Python every value the template prints. Jinja formats nothing and counts
nothing: a template that does arithmetic is a template whose numbers nobody
reviews.

── what fails the build ─────────────────────────────────────────────────────
Each of these is a claim the home would make that the file does not support:

  * the file is missing;
  * its ``digline_version`` is not the version at the top of the changelog —
    the first heading that is exactly ``## X.Y.Z — YYYY-MM-DD``, skipping
    ``## Unreleased`` and the plugins' own headings — or there is no such
    heading at all;
  * a quickstart command did not exit 0;
  * a ``digline compare`` in the regression did not exit 1;
  * ``compare_json`` does not say ``worse: true`` and ``artifacts_changed:
    true``;
  * ``runtime_dependencies`` is missing;
  * ``requires_python`` is missing, or carries no ``specifier``;
  * a character the home shows in IBM Plex is not in the subset of the face
    that shows it (see "the faces" below).

── what the template gets ───────────────────────────────────────────────────
One variable, ``home``, and only on the page whose source is ``index.md``. See
``compute()`` for its shape.

    usage: tools/hooks/home.py --selftest
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

from mkdocs.exceptions import PluginError

# Where sync-docs.sh puts the two files, under docs_dir.
HOME_JSON = "product/assets/home/home.json"
CHANGELOG = "product/changelog.md"

# The core's release headings. Exact on purpose: "## Unreleased" and
# "## digline-openai 0.5.0 — 2026-09-15" must not match, and neither must a
# hyphen where the changelog writes an em dash.
_RELEASE = re.compile(r"^## (\d+\.\d+\.\d+) — \d{4}-\d{2}-\d{2}$")

# "absent: samples=1" — how many samples each case had in the capture.
_SAMPLES = re.compile(r"samples=(\d+)")

# "digline compare --suite support.py --run latest" — the suite's name.
_SUITE = re.compile(r"--suite\s+(\S+?)\.(?:py|toml)\b")

# The run key down to its microseconds: what the page prints before an ellipsis.
_RUN_SHORT = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-\d{6}")

# A score is a number in [0, 1]; the scale on the card is drawn over that range.
SCORE_LO = 0.0
SCORE_HI = 1.0

_WORDS = {1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six",
          7: "Seven", 8: "Eight", 9: "Nine"}


def _fail(problem: str) -> PluginError:
    return PluginError(
        f"home: {problem}\n"
        "  home.json is written by tools/home_capture.py in digline/digline. Run\n"
        "  `uv run python tools/home_capture.py` there, commit the file, and sync\n"
        "  again — the home prints nothing that script did not capture."
    )


# ── reading ──────────────────────────────────────────────────────────────────


def changelog_version(text: str) -> str:
    """The version of the newest core release in the changelog."""
    for line in text.splitlines():
        match = _RELEASE.match(line)
        if match:
            return match.group(1)
    raise _fail(
        "the changelog has no heading of the form `## X.Y.Z — YYYY-MM-DD`, so "
        "there is no released version to hold home.json to."
    )


def _commands(scenario: dict, name: str) -> list[dict]:
    commands = scenario.get("commands")
    if not isinstance(commands, list) or not commands:
        raise _fail(f"scenario {name!r} has no commands.")
    return commands


def validate(data: dict, changelog_text: str) -> None:
    """Raise PluginError on the first claim the file does not support."""
    captured = data.get("digline_version")
    released = changelog_version(changelog_text)
    if captured != released:
        raise _fail(
            f"digline_version is {captured!r}, but the newest release in the "
            f"changelog is {released!r}. The capture is from another version."
        )

    scenarios = data.get("scenarios") or {}
    quickstart = scenarios.get("quickstart")
    regression = scenarios.get("prompt_regression")
    if not isinstance(quickstart, dict) or not isinstance(regression, dict):
        raise _fail("scenarios.quickstart or scenarios.prompt_regression is missing.")

    for command in _commands(quickstart, "quickstart"):
        if command.get("exit") != 0:
            raise _fail(
                f"quickstart: `{command.get('cmd')}` exited "
                f"{command.get('exit')!r}, not 0. The home says the quickstart runs."
            )

    compares = [
        c for c in _commands(regression, "prompt_regression")
        if str(c.get("cmd", "")).startswith("digline compare")
    ]
    if not compares:
        raise _fail("prompt_regression has no `digline compare` command.")
    for command in compares:
        if command.get("exit") != 1:
            raise _fail(
                f"prompt_regression: `{command.get('cmd')}` exited "
                f"{command.get('exit')!r}, not 1. The home shows a regression "
                "that stops CI."
            )

    compare_json = regression.get("compare_json")
    if not isinstance(compare_json, dict):
        raise _fail("prompt_regression.compare_json is missing.")
    for key in ("worse", "artifacts_changed"):
        if compare_json.get(key) is not True:
            raise _fail(
                f"compare_json.{key} is {compare_json.get(key)!r}, not true. "
                "The home says a changed prompt made things worse."
            )

    dependencies = data.get("runtime_dependencies")
    if not isinstance(dependencies, dict) or not isinstance(
        dependencies.get("names"), list
    ):
        raise _fail("runtime_dependencies is missing, or has no list of names.")

    requires = data.get("requires_python")
    specifier = requires.get("specifier") if isinstance(requires, dict) else None
    if not isinstance(specifier, str) or not specifier.strip():
        raise _fail(
            "requires_python is missing, or has no specifier. The home says which "
            "Python digline needs, and only digline's own metadata can say it."
        )


# ── computing ────────────────────────────────────────────────────────────────


def _score(value: float) -> str:
    return f"{value:.2f}"


def _position(value: float) -> str:
    """Where a score sits on the card's scale, as a CSS percentage."""
    clamped = min(max(value, SCORE_LO), SCORE_HI)
    return f"{(clamped - SCORE_LO) / (SCORE_HI - SCORE_LO) * 100:.1f}%"


def _anchor(value: float) -> str:
    """Which way a label on the scale hangs, so it never leaves the card."""
    fraction = (value - SCORE_LO) / (SCORE_HI - SCORE_LO)
    if fraction >= 0.85:
        return "end"
    if fraction <= 0.15:
        return "start"
    return "middle"


def _python_range(specifier: str) -> str:
    """">=3.12" as "3.12 or newer"; any other range as digline declares it."""
    match = re.fullmatch(r">=\s*(\d+\.\d+(?:\.\d+)?)", specifier.strip())
    return f"{match.group(1)} or newer" if match else specifier.strip()


def _short_run(run_id: str) -> str:
    match = _RUN_SHORT.match(run_id)
    return match.group(0) if match else run_id


def _stdout_lines(command: dict) -> list[str]:
    return str(command.get("stdout", "")).rstrip("\n").split("\n")


def compute(data: dict) -> dict[str, Any]:
    """Everything the home prints about digline, formatted and counted here."""
    version = data["digline_version"]
    scenarios = data["scenarios"]
    quickstart = scenarios["quickstart"]
    regression = scenarios["prompt_regression"]
    compare_json = regression["compare_json"]

    # The checks that got worse, grouped by case in the order digline gave them.
    regressed: dict[str, list[dict]] = {}
    for delta in compare_json.get("deltas", []):
        if delta.get("outcome") != "regressed":
            continue
        regressed.setdefault(delta["case_id"], []).append(delta)
    if not regressed:
        raise _fail("compare_json.deltas has no regressed check.")

    case_ids = list(regressed)
    first_id = case_ids[0]
    first_checks = [
        {
            "assertion": d["assertion"],
            "before": _score(d["before"]),
            "after": _score(d["after"]),
        }
        for d in regressed[first_id]
    ]
    shown = regressed[first_id][0]
    regressed_count = sum(len(checks) for checks in regressed.values())

    befores = {_score(d["before"]) for checks in regressed.values() for d in checks}
    before_common = befores.pop() if len(befores) == 1 else None

    # The one changed file, and its diff with the header lines kept apart.
    files = (regression.get("change") or {}).get("files") or []
    diff = None
    if files:
        changed = files[0]
        lines = []
        for raw in changed.get("diff", []):
            if raw.startswith(("---", "+++", "@@")):
                kind = "meta"
            elif raw.startswith("-"):
                kind = "del"
            elif raw.startswith("+"):
                kind = "add"
            else:
                kind = "ctx"
            lines.append({"kind": kind, "text": raw})
        diff = {
            "path": changed.get("path"),
            "lines": lines,
            "changes": [l for l in lines if l["kind"] in ("del", "add")],
            "added": sum(1 for l in lines if l["kind"] == "add"),
            "removed": sum(1 for l in lines if l["kind"] == "del"),
        }

    # The left panel: the new run's scores for the checks that got worse, as a
    # table of cases by check, laid out here so the columns line up.
    columns: list[str] = []
    for checks in regressed.values():
        for d in checks:
            if d["assertion"] not in columns:
                columns.append(d["assertion"])
    header = ["case"] + columns
    rows = []
    for case_id, checks in regressed.items():
        after = {d["assertion"]: _score(d["after"]) for d in checks}
        rows.append([case_id] + [after.get(c, "—") for c in columns])
    widths = [max(len(r[i]) for r in [header] + rows) for i in range(len(header))]

    def _row(cells: list[str]) -> str:
        return "  ".join(cell.ljust(widths[i]) for i, cell in enumerate(cells)).rstrip()

    table = {"header": _row(header), "rows": [_row(r) for r in rows]}

    # The right panel: compare's stdout down to the first case's lines, and a
    # count of what was left out.
    compare = next(
        c for c in regression["commands"]
        if c["cmd"].startswith("digline compare") and "--json" not in c["cmd"]
    )
    out_lines = _stdout_lines(compare)
    prefix = f"{first_id} · "
    shortened: list[dict] = []
    omitted = 0
    for line in out_lines:
        is_case_line = " · " in line and not line.startswith(" ")
        if is_case_line and not line.startswith(prefix):
            omitted += 1
            continue
        if is_case_line:
            kind = "worse"
        elif not line.strip():
            kind = "blank"
        elif line.startswith(" "):
            kind = "file"
        else:
            kind = "head"
        shortened.append({"kind": kind, "text": line})
    if omitted:
        shortened.append({"kind": "more", "text": f"… {omitted} more lines"})

    suite_match = _SUITE.search(compare["cmd"])
    samples_match = _SAMPLES.search(str(regression.get("band", "")))

    run_id = regression["run_ids"][-1]
    quickstart_run = quickstart["run_ids"][0]

    names = list(data["runtime_dependencies"]["names"])
    count = len(names)
    dependency_word = _WORDS.get(count, str(count))

    major = int(version.split(".")[0])

    return {
        "version": version,
        "pre_1_0": major == 0,
        "pinned_install": f"pip install digline=={version}",
        "requires_python": _python_range(data["requires_python"]["specifier"]),
        "dependencies": {
            "names": names,
            "count": count,
            "heading": f"{dependency_word} {'dependency' if count == 1 else 'dependencies'}",
        },
        "regression": {
            "suite": suite_match.group(1) if suite_match else None,
            "exit": compare["exit"],
            "samples": int(samples_match.group(1)) if samples_match else None,
            "run_id": run_id,
            "run_short": _short_run(run_id),
            "first_case": {"id": first_id, "checks": first_checks},
            "other_cases": case_ids[1:],
            "regressed_count": regressed_count,
            "before_common": before_common,
            "scale": {
                "assertion": shown["assertion"],
                "lo": _score(SCORE_LO),
                "hi": _score(SCORE_HI),
                "ref": _score(shown["before"]),
                "run": _score(shown["after"]),
                "ref_pos": _position(shown["before"]),
                "run_pos": _position(shown["after"]),
                "ref_anchor": _anchor(shown["before"]),
                "run_anchor": _anchor(shown["after"]),
            },
            "diff": diff,
            "table": table,
            "compare_lines": shortened,
        },
        "quickstart": {
            "run_id": quickstart_run,
            "run_short": _short_run(quickstart_run),
            "commands": [
                {"cmd": c["cmd"], "stdout": _stdout_lines(c), "exit": c["exit"]}
                for c in quickstart["commands"]
            ],
        },
    }


def load(json_path: str, changelog_path: str) -> dict[str, Any]:
    """Read both files, refuse what they do not support, and compute."""
    if not os.path.isfile(json_path):
        raise _fail(f"{json_path} does not exist.")
    with open(json_path, encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as error:
            raise _fail(f"{json_path} is not JSON: {error}.") from None
    if not os.path.isfile(changelog_path):
        raise _fail(f"{changelog_path} does not exist, so there is no version to check.")
    with open(changelog_path, encoding="utf-8") as fh:
        changelog_text = fh.read()
    validate(data, changelog_text)
    return compute(data)


# ── the faces ────────────────────────────────────────────────────────────────
#
# IBM Plex is served as a subset cut from the characters the home shows, one set
# for Plex Sans and one for Plex Mono. A character outside the subset is not an
# error a browser reports: it draws that one glyph in the system face. So the
# selftest works out, from the page itself, which characters each face draws,
# and reads each woff2's cmap for them. tools/subset-fonts.py cuts the files
# from the same sets, through the same functions.
#
# Which face draws a piece of text is decided by pages.css, not by a list here:
# every rule whose `font-family` or `font` names --sans-page or --mono-page is
# read out of the stylesheet, and the nearest element that one of them matches
# decides.

# Where the faces and the rules that choose them are, from the repository root.
PAGES_CSS = "docs/assets/pages.css"
HOME_TEMPLATE = "home.html"
OVERRIDES = "overrides"

# Text the page shows that is in neither the template's text nor home.json:
# `content: "$ "` on .install__cmd::before, the step counters of .steps li
# (1 to 3), and the Copy / Copied label the script writes on .install__copy.
_GENERATED = {"mono": "$ ", "sans": "123CopyCopied"}

_FAMILIES = {"--sans-page": "sans", "--mono-page": "mono"}
_PLEX = {"IBM Plex Sans": "sans", "IBM Plex Mono": "mono"}
_COMPOUND = re.compile(r"^([a-z][a-z0-9]*)?((?:\.[\w-]+)*)$")
_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
         "meta", "source", "track", "wbr"}


def _declarations(content) -> list:
    import tinycss2

    return [d for d in tinycss2.parse_blocks_contents(content, skip_comments=True,
                                                      skip_whitespace=True)
            if d.type == "declaration"]


def _css_rules(css_text: str):
    """Every qualified rule in the stylesheet, @media contents included."""
    import tinycss2

    def walk(nodes):
        for node in nodes:
            if node.type == "qualified-rule":
                yield node
            elif node.type == "at-rule" and node.lower_at_keyword == "media" and node.content:
                yield from walk(tinycss2.parse_rule_list(node.content, skip_comments=True,
                                                         skip_whitespace=True))

    return walk(tinycss2.parse_stylesheet(css_text, skip_comments=True, skip_whitespace=True))


def font_faces(css_text: str, css_dir: str) -> dict[str, list[tuple[str, str]]]:
    """(weight, woff2 path) for each Plex family, from the @font-face rules."""
    import tinycss2

    faces: dict[str, list[tuple[str, str]]] = {"sans": [], "mono": []}
    for node in tinycss2.parse_stylesheet(css_text, skip_comments=True, skip_whitespace=True):
        if node.type != "at-rule" or node.lower_at_keyword != "font-face":
            continue
        values = {d.lower_name: tinycss2.serialize(d.value).strip()
                  for d in _declarations(node.content)}
        family = _PLEX.get(values.get("font-family", "").strip("\"'"))
        url = re.search(r"url\(\s*[\"']?([^\"')]+)", values.get("src", ""))
        if family and url:
            path = os.path.normpath(os.path.join(css_dir, url.group(1)))
            faces[family].append((values.get("font-weight", "400"), path))
    return faces


def face_rules(css_text: str) -> list[tuple[list[tuple[str, set[str]]], str]]:
    """(selector as compounds, family) for every rule that picks a Plex face,
    in source order. Pseudo-classes, pseudo-elements and combinators other than
    the descendant one are left out: the generated text is _GENERATED."""
    import tinycss2

    rules = []
    for rule in _css_rules(css_text):
        family = None
        for d in _declarations(rule.content):
            if d.lower_name in ("font", "font-family"):
                value = tinycss2.serialize(d.value)
                for token, name in _FAMILIES.items():
                    if token in value:
                        family = name
        if family is None:
            continue
        for selector in tinycss2.serialize(rule.prelude).split(","):
            compounds = []
            for part in selector.split():
                match = _COMPOUND.match(part)
                if not match or not part:
                    compounds = None
                    break
                classes = {c for c in match.group(2).split(".") if c}
                compounds.append((match.group(1) or "", classes))
            if compounds:
                rules.append((compounds, family))
    return rules


def _matches(compounds, chain) -> bool:
    """Whether a descendant selector matches the last element of chain."""
    def fits(compound, element):
        tag, classes = compound
        return (not tag or tag == element[0]) and classes <= element[1]

    if not fits(compounds[-1], chain[-1]):
        return False
    wanted = len(compounds) - 2
    for element in reversed(chain[:-1]):
        if wanted < 0:
            break
        if fits(compounds[wanted], element):
            wanted -= 1
    return wanted < 0


def plex_text(html: str, rules) -> dict[str, set[str]]:
    """The characters of the text inside <main class="dg-page">, by the face
    that draws them. Markup, attributes, <script> and <style> are not text."""
    from html.parser import HTMLParser

    found: dict[str, set[str]] = {"sans": set(), "mono": set()}

    class Reader(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.chain: list[tuple[str, set[str]]] = []

        def handle_starttag(self, tag, attrs):
            if tag in _VOID:
                return
            classes = set((dict(attrs).get("class") or "").split())
            self.chain.append((tag, classes))

        def handle_startendtag(self, tag, attrs):
            pass

        def handle_endtag(self, tag):
            for i in range(len(self.chain) - 1, -1, -1):
                if self.chain[i][0] == tag:
                    del self.chain[i:]
                    return

        def handle_data(self, data):
            tags = [e[0] for e in self.chain]
            if "script" in tags or "style" in tags:
                return
            if not any(t == "main" and "dg-page" in c for t, c in self.chain):
                return
            family = None
            for depth in range(len(self.chain), 0, -1):
                picked = [f for compounds, f in rules if _matches(compounds, self.chain[:depth])]
                if picked:
                    family = picked[-1]
                    break
            if family:
                found[family].update(ch for ch in data if not ch.isspace())

    reader = Reader()
    reader.feed(html)
    reader.close()
    return found


def json_strings(value) -> set[str]:
    """Every character of every string value in home.json."""
    if isinstance(value, str):
        return {ch for ch in value if not ch.isspace()}
    if isinstance(value, dict):
        value = list(value.values())
    if isinstance(value, list):
        return set().union(*(json_strings(v) for v in value)) if value else set()
    return set()


def render_home(root: str, home: dict[str, Any]) -> str:
    """The home's main block, rendered with `home` as the build renders it."""
    import jinja2

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.join(root, OVERRIDES)), autoescape=True
    )
    template = env.get_template(HOME_TEMPLATE)
    context = template.new_context({"home": home, "base_url": ""})
    body = "".join(template.blocks["main"](context))
    return f'<main class="dg-page dg-page--home">{body}</main>'


def plex_characters(root: str, datasets: list[dict]) -> dict[str, set[str]]:
    """What each Plex face must draw: the home's text rendered from each
    capture, every string in each capture, and _GENERATED."""
    with open(os.path.join(root, PAGES_CSS), encoding="utf-8") as fh:
        rules = face_rules(fh.read())
    chars = {family: set(_GENERATED[family]) - {" "} for family in ("sans", "mono")}
    for data in datasets:
        text = plex_text(render_home(root, compute(data)), rules)
        strings = json_strings(data)
        for family in chars:
            chars[family] |= text[family] | strings
    return chars


def glyph_gaps(root: str, chars: dict[str, set[str]]) -> list[str]:
    """Each character a face must draw that its woff2 has no glyph for."""
    from fontTools.ttLib import TTFont

    with open(os.path.join(root, PAGES_CSS), encoding="utf-8") as fh:
        faces = font_faces(fh.read(), os.path.dirname(os.path.join(root, PAGES_CSS)))
    gaps = []
    for family, paths in faces.items():
        if not paths:
            gaps.append(f"no @font-face for Plex {family} in {PAGES_CSS}")
        for _, path in paths:
            cmap = TTFont(path).getBestCmap()
            missing = sorted(ch for ch in chars[family] if ord(ch) not in cmap)
            if missing:
                shown = " ".join(f"{ch!r} U+{ord(ch):04X}" for ch in missing)
                gaps.append(f"{os.path.relpath(path, root)} has no glyph for {shown}; "
                            "cut it again with tools/subset-fonts.py")
    return gaps


# ── the hooks mkdocs calls ───────────────────────────────────────────────────

_home: dict[str, Any] | None = None


def on_pre_build(config, **kwargs):
    """Before anything renders: a home that cannot be built stops the build."""
    global _home
    docs = config["docs_dir"]
    _home = load(os.path.join(docs, HOME_JSON), os.path.join(docs, CHANGELOG))


def on_page_context(context, page, config, nav, **kwargs):
    """The values reach the home and no other page."""
    if page.file.src_uri == "index.md":
        context["home"] = _home
    return context


# ── the selftest ─────────────────────────────────────────────────────────────


def selftest() -> int:
    """The hook against the fixtures in tools/testdata/home/: the capture as it
    was committed must compute to what the home shows, every way the file can
    stop supporting the home must fail the build, naming why, and every
    character the home shows in Plex must be in the subset of its face."""
    import copy
    import tempfile

    here = os.path.dirname(os.path.abspath(__file__))
    fixtures = os.path.join(here, "..", "testdata", "home")
    good_json = os.path.join(fixtures, "home.json")
    good_changelog = os.path.join(fixtures, "changelog.md")

    failures: list[str] = []

    def expect(label: str, actual, wanted) -> None:
        if actual != wanted:
            failures.append(f"{label}: got {actual!r}, wanted {wanted!r}")

    # 1. The good fixture computes to what the page is built on.
    try:
        home = load(good_json, good_changelog)
    except PluginError as error:
        print(f"selftest: the good fixture was refused —\n{error}", file=sys.stderr)
        return 1
    r = home["regression"]
    expect("version", home["version"], "0.13.1")
    expect("pre_1_0", home["pre_1_0"], True)
    expect("first case", r["first_case"]["id"], "how-do-i-return")
    expect("first checks", r["first_case"]["checks"], [
        {"assertion": "llm_rubric", "before": "1.00", "after": "0.40"},
        {"assertion": "contains", "before": "1.00", "after": "0.00"},
    ])
    expect("other cases", r["other_cases"], ["is-it-waterproof", "where-is-my-order"])
    expect("regressed count", r["regressed_count"], 6)
    expect("scale", (r["scale"]["ref"], r["scale"]["run"], r["scale"]["run_pos"]),
           ("1.00", "0.40", "40.0%"))
    expect("diff counts", (r["diff"]["added"], r["diff"]["removed"]), (1, 1))
    expect("table header", r["table"]["header"], "case               llm_rubric  contains")
    expect("more line", r["compare_lines"][-1], {"kind": "more", "text": "… 4 more lines"})
    expect("worse lines", sum(1 for l in r["compare_lines"] if l["kind"] == "worse"), 2)
    expect("suite", r["suite"], "support")
    expect("exit", r["exit"], 1)
    expect("samples", r["samples"], 1)
    expect("dependencies", home["dependencies"]["names"], ["jsonschema"])
    expect("dependency heading", home["dependencies"]["heading"], "One dependency")
    expect("quickstart commands", len(home["quickstart"]["commands"]), 3)
    expect("requires python", home["requires_python"], "3.12 or newer")
    expect("python range kept as declared", _python_range(">=3.12,<3.15"), ">=3.12,<3.15")

    # 2. Every refusal, on a modified copy.
    with open(good_json, encoding="utf-8") as fh:
        base = json.load(fh)
    with open(good_changelog, encoding="utf-8") as fh:
        base_changelog = fh.read()

    def quickstart_exit(d):
        d["scenarios"]["quickstart"]["commands"][2]["exit"] = 1

    def compare_exit(d):
        for c in d["scenarios"]["prompt_regression"]["commands"]:
            if c["cmd"] == "digline compare --suite support.py --run latest":
                c["exit"] = 0

    cases = [
        ("missing file", None, None, "does not exist"),
        ("version changed", lambda d: d.update(digline_version="0.13.0"), None,
         "digline_version is '0.13.0'"),
        ("no release heading", None,
         "# Changelog\n\n## Unreleased\n\n## digline-openai 0.5.0 — 2026-09-15\n",
         "no heading of the form"),
        ("hyphen, not em dash", None, "# Changelog\n\n## 0.13.1 - 2026-09-15\n",
         "no heading of the form"),
        ("quickstart exit", quickstart_exit, None, "not 0"),
        ("compare exit", compare_exit, None, "not 1"),
        ("worse false",
         lambda d: d["scenarios"]["prompt_regression"]["compare_json"].update(worse=False),
         None, "compare_json.worse"),
        ("artifacts unchanged",
         lambda d: d["scenarios"]["prompt_regression"]["compare_json"].update(
             artifacts_changed=False), None, "compare_json.artifacts_changed"),
        ("no runtime_dependencies", lambda d: d.pop("runtime_dependencies"), None,
         "runtime_dependencies is missing"),
        ("no requires_python", lambda d: d.pop("requires_python"), None,
         "requires_python is missing"),
        ("requires_python without a specifier",
         lambda d: d["requires_python"].pop("specifier"), None,
         "requires_python is missing, or has no specifier"),
    ]

    with tempfile.TemporaryDirectory() as tmp:
        for label, mutate, changelog_text, needle in cases:
            json_path = os.path.join(tmp, f"{label}.json")
            changelog_path = os.path.join(tmp, f"{label}.md")
            if label != "missing file":
                data = copy.deepcopy(base)
                if mutate:
                    mutate(data)
                with open(json_path, "w", encoding="utf-8") as fh:
                    json.dump(data, fh)
            with open(changelog_path, "w", encoding="utf-8") as fh:
                fh.write(changelog_text if changelog_text is not None else base_changelog)
            try:
                load(json_path, changelog_path)
            except PluginError as error:
                message = str(error)
                if needle not in message:
                    failures.append(f"{label}: refused, but not for this: {message}")
                elif "tools/home_capture.py" not in message:
                    failures.append(f"{label}: refused without naming tools/home_capture.py")
                else:
                    print(f"selftest: refused, as it must — {label}: "
                          f"{message.splitlines()[0]}")
                continue
            failures.append(f"{label}: accepted, which it exists to refuse")

    # 3. Every character the home shows in Plex has a glyph in the face that
    #    shows it, and a character that has none is caught.
    root = os.path.normpath(os.path.join(here, "..", ".."))
    chars = plex_characters(root, [base])
    expect("‘…’ is drawn in Mono", "…" in chars["mono"], True)
    expect("‘’’ is drawn in Sans", "’" in chars["sans"], True)
    gaps = glyph_gaps(root, chars)
    failures.extend(f"faces: {gap}" for gap in gaps)
    unshown = copy.deepcopy(base)
    unshown["runtime_dependencies"]["names"].append("✱")
    planted = glyph_gaps(root, plex_characters(root, [unshown]))
    if not planted or not all("U+2731" in gap for gap in planted):
        failures.append(f"faces: a character no face has went unnoticed: {planted!r}")
    else:
        print(f"selftest: refused, as it must — a character outside the subset: "
              f"{len(planted)} faces without U+2731")

    for failure in failures:
        print(f"selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print(f"selftest: home.json fixture computes as expected, "
          f"{len(cases)} refusals refused, every Plex character in its subset "
          f"({len(chars['sans'])} Sans, {len(chars['mono'])} Mono)")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        raise SystemExit(selftest())
    print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
    raise SystemExit(2)
