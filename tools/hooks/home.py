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
  * ``cli_commands`` or ``checks`` is missing, has no ``source``, or has no
    ``items``;
  * a command in ``cli_commands`` has no group in COMMAND_GROUPS below, or
    COMMAND_GROUPS names a command digline does not have;
  * the nav's ``Commands:`` group lists something that is not a command page,
    or a command page no group in COMMAND_GROUPS names (see
    ``split_commands()``: the nav's command subgroups are these groups);
  * a command has no page of its own, product/<name>/, no heading in the guide
    or in a Reference page that names it, and is not written in the guide's
    text either (see ``command_link()`` for the order they are tried in);
  * a check's ``kind`` is not one of CHECK_KINDS, or its ``anchor`` is not an
    id on product/metrics/;
  * the stack band under "How it fits" cannot find what it prints (see
    ``stack()``): a provider's package in the synced documentation, an
    example's page or its title, the image name on product/docker/ or the
    package name on product/mcp/.

The pages and anchors are looked for twice: in the rendered Markdown, before
the home is rendered, to build its links; and in site/ after the build, to
check that the files the links point to are the ones that were written.

The characters the home shows in IBM Plex are checked after the build, on the
HTML, with the other presentation pages: tools/check-glyphs.py.

── what the template gets ───────────────────────────────────────────────────
One variable, ``home``, and only on the page whose source is ``index.md``. See
``compute()`` for its shape, and ``grids()`` for its ``commands`` and
``checks``.

    usage: tools/hooks/home.py --selftest
"""

from __future__ import annotations

import json
import os
import re
import sys
from html import unescape as html_unescape
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
          7: "Seven", 8: "Eight", 9: "Nine", 10: "Ten", 11: "Eleven",
          12: "Twelve", 13: "Thirteen", 14: "Fourteen", 15: "Fifteen",
          16: "Sixteen", 17: "Seventeen", 18: "Eighteen", 19: "Nineteen",
          20: "Twenty"}

# How the home groups digline's commands: a choice this site makes, not
# something digline declares. Every command home.json lists must be in exactly
# one group, and every name here must be a command home.json lists, so a
# command added or removed in digline stops the build here until it is placed.
COMMAND_GROUPS = (
    ("record", "Record and approve", ("run", "promote")),
    ("compare", "Compare", ("compare", "diff", "explain", "report")),
    ("history", "History", ("list", "log", "register", "view")),
    ("maintenance", "Maintenance", ("rejudge", "migrate")),
)

# The kinds a check declares (digline's `KIND`), in the order the home shows
# them, with the words it shows them with. An unknown kind stops the build.
CHECK_KINDS = (
    ("deterministic", "Deterministic", "No model involved. Same output, same verdict."),
    ("judged", "Judged", "A second model scores the answer, and its noise is measured."),
    ("budget", "Budgets", "A ceiling on cost or latency, scored graded rather than pass/fail."),
    ("aggregate", "Aggregates", "One verdict over the whole run."),
    ("wrapper", "Wrappers", "Takes the nature of the check it wraps."),
)

# The stack band under "How it fits": which providers, examples and other ways
# to run digline the home shows, in its order, with the name each row carries.
# Everything else a row prints is read from the build by ``stack()``: the
# package a provider is installed as, the question an example's page asks, the
# image and the package name the Docker and MCP pages open on.
STACK_PROVIDERS = (
    ("Anthropic", "digline-anthropic"),
    ("OpenAI-compatible", "digline-openai"),
    ("Amazon Bedrock", "digline-bedrock"),
)
STACK_EXAMPLES = (
    ("LangChain", "product/examples/langchain.md"),
    ("LlamaIndex", "product/examples/llamaindex.md"),
    ("LangGraph", "product/examples/langgraph.md"),
    ("LangChain4j", "product/examples/langchain4j.md"),
)
STACK_RUN = (
    ("Docker image", "product/docker.md"),
    ("MCP server", "product/mcp.md"),
)

# Where a command without a page of its own is written about, and where the
# checks' cards are: source paths under docs/, and their URLs on the site.
GUIDE = "product/guide.md"
METRICS = "product/metrics.md"


def _fail_site(problem: str) -> PluginError:
    """A refusal whose fix is on this site, not in digline's capture."""
    return PluginError(
        f"home: {problem}\n"
        "  The grouping, the kinds and where each command links to are decided in\n"
        "  tools/hooks/home.py (COMMAND_GROUPS, CHECK_KINDS)."
    )


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

    for key in ("cli_commands", "checks"):
        block = data.get(key)
        if not isinstance(block, dict):
            raise _fail(f"{key} is missing.")
        if not isinstance(block.get("source"), str) or not block["source"].strip():
            raise _fail(f"{key} has no source: the home says where every list comes from.")
        items = block.get("items")
        if not isinstance(items, list) or not items:
            raise _fail(f"{key}.items is missing or empty.")

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


def command_groups(cmd: str) -> list[str]:
    """A command cut where a line may break: each word on its own, except a
    flag and the value after it, which stay one group (`--suite support.py`).
    The groups joined with a space are the command, character for character."""
    words = cmd.split(" ")
    groups: list[str] = []
    i = 0
    while i < len(words):
        word = words[i]
        if (word.startswith("-") and "=" not in word and i + 1 < len(words)
                and words[i + 1] and not words[i + 1].startswith("-")):
            groups.append(f"{word} {words[i + 1]}")
            i += 2
        else:
            groups.append(word)
            i += 1
    return groups


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
        "pinned_install_groups": command_groups(f"pip install digline=={version}"),
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
                {"cmd": c["cmd"], "groups": command_groups(c["cmd"]),
                 "stdout": _stdout_lines(c), "exit": c["exit"]}
                for c in quickstart["commands"]
            ],
        },
    }


# ── the two grids ────────────────────────────────────────────────────────────

_ID = re.compile(r'\bid="([^"]+)"')
_HEADING = re.compile(r'<h[2-6][^>]*\bid="([^"]+)"', re.I)
_INLINE = re.compile(r"</?(?:span|code|a|em|strong|b|i|kbd|mark|abbr)\b", re.I)


def ids_in(html: str) -> set[str]:
    return set(_ID.findall(html))


def first_mention(html: str, name: str) -> str | None:
    """The id of the heading above the first place `digline <name>` is written
    in a page's rendered HTML, "" when that place is above every heading, or
    None when it is not written. The words are read across tags, because a
    highlighted shell line puts `digline` and the command in spans of their
    own."""
    text = ""
    where: list[tuple[int, int]] = []   # (offset in text, offset in html)
    for piece in re.finditer(r"<[^>]*>|[^<]+", html):
        if piece.group(0).startswith("<"):
            # An inline tag joins the words either side of it; any other tag
            # ends one, so "compare</pre><h2>2." is not "compare2.".
            if not _INLINE.match(piece.group(0)):
                text += "\n"
            continue
        where.append((len(text), piece.start()))
        text += piece.group(0)
    found = re.search(rf"\bdigline\s+{re.escape(name)}\b(?!-)", text)
    if not found:
        return None
    in_text, in_html = next((t, h) for t, h in reversed(where) if t <= found.start())
    position = in_html + (found.start() - in_text)
    headings = [m.group(1) for m in _HEADING.finditer(html) if m.start() < position]
    return headings[-1] if headings else ""


_HEADING_BLOCK = re.compile(r'<h([2-4])\b[^>]*\bid="([^"]+)"[^>]*>(.*?)</h\1>', re.I | re.S)
_CODE = re.compile(r"<code\b[^>]*>(.*?)</code>", re.I | re.S)


def _plain(fragment: str) -> str:
    return html_unescape(re.sub(r"<[^>]*>", "", fragment))


def heading_naming(page_html: str, name: str, in_text: bool,
                   bare_name: bool = True) -> str | None:
    """The id of the first h2–h4 in a page that names the command: a <code>
    in it holding `digline <name>`, or — with bare_name — the name alone as a
    word of its own (`compare`, not `Case.compare` or `compare-all`); or, with
    in_text, its text writing `digline <name>`. None when no heading does."""
    command = re.compile(rf"\bdigline\s+{re.escape(name)}(?![\w\-])")
    word = re.compile(rf"(?<![\w.\-]){re.escape(name)}(?![\w\-])")
    code_match = word if bare_name else command
    for match in _HEADING_BLOCK.finditer(page_html):
        inner = match.group(3)
        if any(code_match.search(_plain(code)) for code in _CODE.findall(inner)):
            return match.group(2)
        if in_text and re.search(rf"\bdigline\s+{re.escape(name)}(?![\w\-])", _plain(inner)):
            return match.group(2)
    return None


def _url(src_uri: str) -> str:
    """product/api.md as the site serves it: product/api/."""
    return src_uri[: -len(".md")] + "/"


def command_link(name: str, pages: set[str], guide_html: str,
                 reference: list[tuple[str, str]]) -> tuple[str, str] | None:
    """Where a command's tile sends a reader, and why, trying in this order:

      1. its own page, product/<name>/;
      2. the first h2–h4 in the guide that writes `digline <name>`, or the
         name in code;
      3. the first h2–h4 in a Reference page, in the order of the nav, with
         `digline <name>` in code — the name alone does not count there, where
         a heading like "What `run` costs" on the MCP page is about a tool of
         the same name, not the command;
      4. the heading above the first place the guide's text writes
         `digline <name>`.

    None when all four come up empty."""
    if f"product/{name}.md" in pages:
        return f"product/{name}/", "page"
    anchor = heading_naming(guide_html, name, in_text=True)
    if anchor:
        return f"{_url(GUIDE)}#{anchor}", "guide heading"
    for src_uri, page_html in reference:
        anchor = heading_naming(page_html, name, in_text=False, bare_name=False)
        if anchor:
            return f"{_url(src_uri)}#{anchor}", "reference heading"
    anchor = first_mention(guide_html, name)
    if anchor is not None:
        return _url(GUIDE) + (f"#{anchor}" if anchor else ""), "guide text"
    return None


def grids(data: dict, pages: set[str], guide_html: str, metrics_ids: set[str],
          reference: list[tuple[str, str]] = ()) -> dict[str, Any]:
    """The Commands and Checks sections: grouped, linked and counted here.

    pages        the source paths the build has (``product/diff.md``, …)
    guide_html   the guide's rendered content
    metrics_ids  the ids on the metrics page
    reference    (source path, rendered content) of each Reference page, in
                 the order of the nav
    """
    commands = data["cli_commands"]["items"]
    names = [c["name"] for c in commands]
    grouped = [name for _, _, members in COMMAND_GROUPS for name in members]
    ungrouped = [n for n in names if n not in grouped]
    if ungrouped:
        raise _fail_site(
            f"digline has commands the home does not group: {', '.join(ungrouped)}. "
            "Put each in a group of COMMAND_GROUPS."
        )
    unknown = [n for n in grouped if n not in names]
    if unknown:
        raise _fail_site(
            f"COMMAND_GROUPS names commands digline does not have: {', '.join(unknown)}."
        )
    helps = {c["name"]: c["help"] for c in commands}

    groups = []
    for key, label, members in COMMAND_GROUPS:
        items = []
        for name in members:
            found = command_link(name, pages, guide_html, list(reference))
            if found is None:
                raise PluginError(
                    f"home: `digline {name}` has no page of its own (product/{name}/), no "
                    "heading in the guide or in a Reference page names it, and it is not "
                    "written anywhere in the guide, so the Commands grid has nowhere to "
                    "send a reader.\n"
                    "  The fix is in digline/digline: a page for the command, or "
                    f"`digline {name}` written in docs/guide.md."
                )
            href, place = found
            items.append({"name": name, "help": helps[name], "href": href, "place": place})
        groups.append({"key": key, "label": label, "commands": items})

    checks = data["checks"]["items"]
    kinds = [k for k, _, _ in CHECK_KINDS]
    strange = sorted({c["kind"] for c in checks} - set(kinds))
    if strange:
        raise _fail_site(
            f"checks of a kind the home does not know: {', '.join(strange)}. "
            "Add the kind to CHECK_KINDS, with its words."
        )
    missing = [c["name"] for c in checks if c["anchor"] not in metrics_ids]
    if missing:
        raise _fail(
            f"no card on product/metrics/ for {', '.join(missing)}: the anchor in "
            "home.json is not an id on the page."
        )
    kind_groups = []
    for key, label, description in CHECK_KINDS:
        # Alphabetical, without regard to case, rather than in digline's
        # declaration order, which a reader has no way to see.
        members = [{"name": c["name"], "href": f"product/metrics/#{c['anchor']}"}
                   for c in sorted((c for c in checks if c["kind"] == key),
                                   key=lambda c: (c["name"].casefold(), c["name"]))]
        kind_groups.append({"key": key, "label": label, "description": description,
                            "count": len(members), "checks": members})

    count = len(names)
    return {
        "commands": {
            "count": count,
            "heading": f"{_WORDS.get(count, str(count))} commands",
            "groups": groups,
        },
        "checks": {
            "total": len(checks),
            "kinds_word": _WORDS.get(len(CHECK_KINDS), str(len(CHECK_KINDS))).lower(),
            "kinds": kind_groups,
        },
    }


# ── the stack band ───────────────────────────────────────────────────────────

_H1_TEXT = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.I | re.S)
_FIRST_P = re.compile(r"<p\b[^>]*>(.*?)</p>", re.I | re.S)


def page_title(page_html: str, source: str) -> str:
    """An example's page title, as plain text, without its permalink."""
    match = _H1_TEXT.search(page_html)
    title = _plain(re.sub(r'<a class="headerlink".*?</a>', "", match.group(1), flags=re.S)).strip() if match else ""
    if not title:
        raise _fail_site(f"the stack band reads its question from the title of {source}, which has none.")
    return title


def page_question(page_html: str, source: str) -> str:
    """The question an example's page asks: its title after the colon
    ("My pipeline is LangChain: what changed when I upgraded it?"), or the
    whole title when it has none."""
    title = page_title(page_html, source)
    _, colon, after = title.partition(":")
    return after.strip() if colon and after.strip() else title


def opening_code(page_html: str, source: str) -> str:
    """The first thing in code in the first paragraph under a page's title:
    `ghcr.io/digline/digline` on the Docker page, `digline-mcp` on the MCP
    page."""
    heading = _H1_TEXT.search(page_html)
    rest = page_html[heading.end():] if heading else page_html
    paragraph = _FIRST_P.search(rest)
    code = _CODE.search(paragraph.group(1)) if paragraph else None
    if not code or not _plain(code.group(1)).strip():
        raise _fail_site(
            f"the stack band reads a name in code from the first paragraph of {source}, "
            "and there is none."
        )
    return _plain(code.group(1)).strip()


def stack(pages: set[str], rendered: dict[str, str], docs_text: str) -> dict[str, Any]:
    """The three blocks of the stack band, every name and line checked here.

    pages      the source paths the build has
    rendered   source path → rendered content, for the example, Docker and
               MCP pages
    docs_text  the synced documentation under product/, as Markdown, in
               which every provider's package name must be written
    """
    providers = []
    for name, package in STACK_PROVIDERS:
        if not re.search(rf"(?<![\w-]){re.escape(package)}(?![\w-])", docs_text):
            raise _fail_site(
                f"the stack band shows {name} as `{package}`, and no page under product/ "
                "writes that package name."
            )
        providers.append({"name": name, "package": package})

    def page(source: str) -> str:
        if source not in pages or source not in rendered:
            raise _fail_site(f"the stack band links to {source}, which the build does not have.")
        return rendered[source]

    examples = [{"name": name, "question": page_question(page(source), source),
                 "href": source[: -len(".md")] + "/"}
                for name, source in STACK_EXAMPLES]
    run = [{"name": name, "code": opening_code(page(source), source),
            "href": source[: -len(".md")] + "/"}
           for name, source in STACK_RUN]
    return {"providers": providers, "examples": examples, "run": run}


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


# ── the hooks mkdocs calls ───────────────────────────────────────────────────

_home: dict[str, Any] | None = None


def on_pre_build(config, **kwargs):
    """Before anything renders: a home that cannot be built stops the build."""
    global _home
    docs = config["docs_dir"]
    _home = load(os.path.join(docs, HOME_JSON), os.path.join(docs, CHANGELOG))


# What the grids need from the rest of the site, gathered while it builds:
# every page mkdocs has, the guide's rendered content, and the ids on the
# metrics page. mkdocs renders every page's Markdown before it renders any
# template, so all three are here by the time the home's template is.
_pages: set[str] = set()
_rendered: dict[str, str] = {}
_reference: list[str] = []

# The nav sections whose pages a command's tile may point into, after the guide:
# every page under them, subgroups included, in the order the nav lists them.
# "A Reference page", below, is any of those pages.
REFERENCE_SECTIONS = ("Commands", "Running it", "Reference")

# The nav group that on_config splits by COMMAND_GROUPS.
COMMANDS_SECTION = "Commands"


def split_commands(entries: list, source: str = "mkdocs.yml") -> list:
    """The flat `Commands:` list of the nav, as one subgroup per COMMAND_GROUPS
    entry that has a page in it, labelled as the home labels it.

    Each entry is a one-key mapping, label to `product/<name>.md`. Groups and
    pages come out in COMMAND_GROUPS order, whatever order the list has; a
    group with no page (Record and approve: run and promote are written in the
    guide) is left out. An entry that is not a command page, or a command no
    group names, fails the build: the grouping is decided here, once, for the
    home and the nav alike.
    """
    placed: dict[str, tuple[str, dict]] = {}
    for entry in entries:
        path = next(iter(entry.values())) if isinstance(entry, dict) and len(entry) == 1 else None
        match = re.fullmatch(r"product/([a-z][a-z0-9-]*)\.md", path) if isinstance(path, str) else None
        if not match:
            raise _fail_site(
                f"the `{COMMANDS_SECTION}:` group in {source} holds {entry!r}, which is not a "
                "`label: product/<command>.md` line. Only command pages go there.")
        placed[match.group(1)] = (path, entry)
    grouped = {name for _, _, names in COMMAND_GROUPS for name in names}
    loose = sorted(set(placed) - grouped)
    if loose:
        raise _fail_site(
            f"the `{COMMANDS_SECTION}:` group in {source} lists a page for "
            f"{', '.join(loose)}, which no group in COMMAND_GROUPS names, so the nav "
            "has nowhere to put it.")
    return [{label: [placed[name][1] for name in names if name in placed]}
            for _, label, names in COMMAND_GROUPS if any(name in placed for name in names)]


def on_config(config, **kwargs):
    """The nav's `Commands:` group, split into the home's command groups."""
    def walk(items):
        for item in items or []:
            if not isinstance(item, dict):
                continue
            for key, value in item.items():
                if key == COMMANDS_SECTION and isinstance(value, list):
                    item[key] = split_commands(value, config.config_file_path or "mkdocs.yml")
                    return True
                if isinstance(value, list) and walk(value):
                    return True
        return False

    if not walk(config["nav"]):
        raise _fail_site(f"the nav has no `{COMMANDS_SECTION}:` group to split.")
    return config


def on_files(files, config, **kwargs):
    _pages.clear()
    _pages.update(f.src_uri for f in files.documentation_pages())
    _rendered.clear()
    return files


def on_nav(nav, config, files, **kwargs):
    """The pages under the reference sections, in the order the nav lists them."""
    _reference.clear()

    def pages(items):
        for item in items:
            if getattr(item, "is_section", False):
                yield from pages(item.children)
            elif getattr(item, "is_page", False) and item.file:
                yield item.file.src_uri

    def walk(items):
        for item in items:
            if getattr(item, "is_section", False):
                if item.title in REFERENCE_SECTIONS:
                    _reference.extend(pages(item.children))
                else:
                    walk(item.children)

    walk(nav.items)
    return nav


_STACK_PAGES = {source for _, source in STACK_EXAMPLES + STACK_RUN}


def on_page_content(html, page, config, files, **kwargs):
    if (page.file.src_uri in (GUIDE, METRICS) or page.file.src_uri in _reference
            or page.file.src_uri in _STACK_PAGES):
        _rendered[page.file.src_uri] = html
    return html


def _docs_text(docs_dir: str) -> str:
    """Every Markdown file under product/, joined: where a package name must be
    written for the stack band to show it."""
    parts = []
    for folder, _, names in os.walk(os.path.join(docs_dir, "product")):
        for name in sorted(names):
            if name.endswith(".md"):
                with open(os.path.join(folder, name), encoding="utf-8") as fh:
                    parts.append(fh.read())
    return "\n".join(parts)


def _built_stack(config) -> dict[str, Any]:
    return stack(_pages, _rendered, _docs_text(config["docs_dir"]))


def _built_grids(data: dict) -> dict[str, Any]:
    return grids(data, _pages, _rendered.get(GUIDE, ""), ids_in(_rendered.get(METRICS, "")),
                 [(uri, _rendered.get(uri, "")) for uri in _reference])


def on_page_context(context, page, config, nav, **kwargs):
    """The values reach the home and no other page."""
    if page.file.src_uri == "index.md":
        home = dict(_home)
        with open(os.path.join(config["docs_dir"], HOME_JSON), encoding="utf-8") as fh:
            data = json.load(fh)
        home.update(_built_grids(data))
        home["stack"] = _built_stack(config)
        context["home"] = home
    return context


def on_post_build(config, **kwargs):
    """The links the home was built with, checked against the files written:
    each page exists in site/, and each anchor is an id on it."""
    site = config["site_dir"]
    with open(os.path.join(config["docs_dir"], HOME_JSON), encoding="utf-8") as fh:
        data = json.load(fh)
    built = _built_grids(data)
    hrefs = [c["href"] for g in built["commands"]["groups"] for c in g["commands"]]
    hrefs += [c["href"] for k in built["checks"]["kinds"] for c in k["checks"]]
    band = _built_stack(config)
    hrefs += [row["href"] for row in band["examples"] + band["run"]]
    # The questions, read again off the pages as they were written into site/.
    for (name, source), row in zip(STACK_EXAMPLES, band["examples"]):
        written = os.path.join(site, source[: -len(".md")], "index.html")
        with open(written, encoding="utf-8") as fh:
            if page_question(fh.read(), source) != row["question"]:
                raise _fail_site(f"the {name} question on the home is not the title of {written}.")
    cache: dict[str, set[str]] = {}
    for href in hrefs:
        path, _, anchor = href.partition("#")
        page = os.path.join(site, path, "index.html")
        if path not in cache:
            if not os.path.isfile(page):
                raise _fail_site(f"the home links to {href}, and site/{path} was not written.")
            with open(page, encoding="utf-8") as fh:
                cache[path] = ids_in(fh.read())
        if anchor and anchor not in cache[path]:
            raise _fail_site(f"the home links to {href}, and there is no id {anchor!r} on it.")


# ── the selftest ─────────────────────────────────────────────────────────────


def selftest() -> int:
    """The hook against the fixtures in tools/testdata/home/: the capture as it
    was committed must compute to what the home shows, every way the file can
    stop supporting the home must fail the build, naming why."""
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
    expect("command groups", home["quickstart"]["commands"][2]["groups"],
           ["digline", "compare", "--suite support.py", "--run latest"])
    for c in home["quickstart"]["commands"]:
        expect(f"groups rejoin to {c['cmd']!r}", " ".join(c["groups"]), c["cmd"])
    expect("a flag with no value stays alone", command_groups("digline compare --json --run latest"),
           ["digline", "compare", "--json", "--run latest"])
    expect("requires python", home["requires_python"], "3.12 or newer")
    expect("python range kept as declared", _python_range(">=3.12,<3.15"), ">=3.12,<3.15")

    # 1b. The two grids, against a site of the fixture's shape: a page for some
    #     commands; a guide whose headings name one command in code and one in
    #     text, and whose text writes the rest (inline, and on a highlighted
    #     shell line, where the words are in spans of their own); two
    #     Reference pages; and a metrics page with every card. Each of the four
    #     ways a link is found is used, and each one wins over the ones after
    #     it.
    with open(good_json, encoding="utf-8") as fh:
        grid_data = json.load(fh)
    command_names = [c["name"] for c in grid_data["cli_commands"]["items"]]
    pages = {"product/guide.md", "product/metrics.md"} | {
        f"product/{n}.md" for n in command_names if n not in ("run", "promote", "compare", "list", "report")}
    guide_html = (
        '<h1 id="working">Working</h1><p>Intro.</p>'
        '<h2 id="one">1. A baseline</h2><pre><code><span class="gp">$ </span>digline'
        '<span class="w"> </span>run<span class="w"> </span>--suite s.py\n'
        '<span class="gp">$ </span>digline<span class="w"> </span>promote\n'
        '<span class="gp">$ </span>digline<span class="w"> </span>compare</code></pre>'
        '<h2 id="two">2. Reading</h2><p><code>digline report</code> and <code>digline list</code>, '
        'not <code>digline list-runs</code>.</p>'
        '<h3 id="approving">Approving with <code>promote</code></h3><p>Later.</p>'
        '<h4 id="the-list">What digline list prints</h4><p>Later still.</p>'
        '<h5 id="deep">Deep <code>report</code></h5>')
    reference = [
        ("product/api.md",
         '<h2 id="suite">Suite</h2><h3 id="case-compare"><code>Case.compare</code></h3>'
         '<h3 id="compare-all"><code>digline compare-all</code></h3>'
         '<h3 id="compare-function">The <code>compare</code> function</h3>'
         '<h3 id="compare">Reading <code>digline compare</code></h3>'
         '<h3 id="promote-api"><code>digline promote</code></h3>'),
        ("product/mcp.md",
         '<h2 id="what-run-costs">What <code>run</code> costs</h2>'
         '<h2 id="what-compare-costs">What <code>digline compare</code> costs</h2>'),
    ]
    metrics_ids = {c["anchor"] for c in grid_data["checks"]["items"]}
    g = grids(grid_data, pages, guide_html, metrics_ids, reference)
    links = {c["name"]: c["href"] for grp in g["commands"]["groups"] for c in grp["commands"]}
    expect("command count", g["commands"]["count"], 12)
    expect("command heading", g["commands"]["heading"], "Twelve commands")
    expect("group order", [grp["key"] for grp in g["commands"]["groups"]],
           ["record", "compare", "history", "maintenance"])
    expect("group sizes", [len(grp["commands"]) for grp in g["commands"]["groups"]], [2, 4, 4, 2])
    expect("a command with a page", links["diff"], "product/diff/")
    expect("2. a guide heading with the name in code, over the reference and the text",
           links["promote"], "product/guide/#approving")
    expect("2. a guide heading writing `digline <name>`, over the text", links["list"],
           "product/guide/#the-list")
    expect("3. a Reference heading with `digline <name>` in code, the first in nav order",
           links["compare"], "product/api/#compare")
    expect("3. a Reference heading with the name alone in code does not win: run falls to 4",
           links["run"], "product/guide/#one")
    expect("the name alone in a Reference heading is not enough",
           heading_naming('<h2 id="what-run-costs">What <code>run</code> costs</h2>', "run",
                          in_text=False, bare_name=False), None)
    expect("4. the guide's text, on a highlighted line", links["run"], "product/guide/#one")
    expect("4. the guide's text, inline (an h5 does not count)", links["report"], "product/guide/#two")
    places = {c["name"]: c["place"] for grp in g["commands"]["groups"] for c in grp["commands"]}
    expect("places", [places[n] for n in ("diff", "promote", "compare", "run")],
           ["page", "guide heading", "reference heading", "guide text"])
    expect("a heading in text needs `digline` before the name",
           heading_naming('<h2 id="x">Run it</h2>', "run", in_text=True), None)
    expect("a Reference heading does not count by text alone",
           heading_naming('<h2 id="x">digline compare</h2>', "compare", in_text=False), None)
    expect("a command's help", g["commands"]["groups"][0]["commands"][0]["help"],
           "execute the suite and write a run")
    expect("kind order", [k["key"] for k in g["checks"]["kinds"]],
           ["deterministic", "judged", "budget", "aggregate", "wrapper"])
    expect("kind counts", [k["count"] for k in g["checks"]["kinds"]], [12, 2, 2, 4, 2])
    expect("check total", g["checks"]["total"], 22)
    expect("kinds in words", g["checks"]["kinds_word"], "five")
    expect("a check's link", g["checks"]["kinds"][2]["checks"][0],
           {"name": "CostBudget", "href": "product/metrics/#costbudget"})
    expect("checks in alphabetical order, case aside (aggregates, which digline declares F1 first)",
           [c["name"] for c in g["checks"]["kinds"][3]["checks"]],
           ["Accuracy", "F1", "Precision", "Recall"])
    expect("checks in alphabetical order, case aside (deterministic)",
           [c["name"] for c in g["checks"]["kinds"][0]["checks"]],
           ["Affix", "Contains", "Equals", "IsJson", "JsonSchema", "Length", "Levenshtein",
            "NotContains", "PiiAbsent", "Regex", "ToolCalledWith", "ToolsCalled"])
    expect("wrappers",
           [c["name"] for c in g["checks"]["kinds"][4]["checks"]], ["FromAutoevals", "Repeated"])
    mixed = copy.deepcopy(grid_data)
    mixed["checks"]["items"] = [{"name": n, "kind": "deterministic", "anchor": "affix"}
                                for n in ("regex", "Contains", "affix", "Zeta")]
    expect("case does not decide the order",
           [c["name"] for c in grids(mixed, pages, guide_html, metrics_ids, reference)
            ["checks"]["kinds"][0]["checks"]], ["affix", "Contains", "regex", "Zeta"])
    expect("first mention above every heading", first_mention("<p>digline run</p><h2 id='x'>X</h2>", "run"), "")
    expect("a longer name is not the command", first_mention('<h2 id="a">A</h2><p>digline list-runs</p>', "list"), None)

    # 1b'. The nav's Commands group, split by COMMAND_GROUPS: groups and pages
    #      in the home's order whatever order the list has, a group with no
    #      page left out, and anything that is not a grouped command page
    #      refused.
    flat = [{"digline view": "product/view.md"}, {"digline diff": "product/diff.md"},
            {"digline migrate": "product/migrate.md"}, {"digline explain": "product/explain.md"},
            {"digline log": "product/log.md"}]
    expect("commands split by COMMAND_GROUPS, in its order", split_commands(flat), [
        {"Compare": [{"digline diff": "product/diff.md"}, {"digline explain": "product/explain.md"}]},
        {"History": [{"digline log": "product/log.md"}, {"digline view": "product/view.md"}]},
        {"Maintenance": [{"digline migrate": "product/migrate.md"}]},
    ])
    split_refusals = [
        ("a command page no group names", flat + [{"digline doctor": "product/doctor.md"}],
         "for doctor, which no group in COMMAND_GROUPS names"),
        ("a page that is not a command page", flat + [{"The Docker image": "product/examples/rag.md"}],
         "which is not a `label: product/<command>.md` line"),
        ("a subgroup instead of a page", flat + [{"More": [{"digline list": "product/list.md"}]}],
         "which is not a `label: product/<command>.md` line"),
        ("a path with no label", flat + ["product/report.md"],
         "which is not a `label: product/<command>.md` line"),
    ]
    for label, entries, needle in split_refusals:
        try:
            split_commands(entries)
        except PluginError as error:
            if needle not in str(error):
                failures.append(f"{label}: refused, but not for this: {error}")
            else:
                print(f"selftest: refused, as it must — {label}: {str(error).splitlines()[0]}")
            continue
        failures.append(f"{label}: accepted, which it exists to refuse")

    # 1c. The stack band, against pages of the shape the build has: a title with
    #     a colon, one without, the Docker and MCP pages' first paragraphs.
    stack_pages = {source for _, source in STACK_EXAMPLES + STACK_RUN}
    headerlink = '<a class="headerlink" href="#t" title="Link to this section">&para;</a>'
    stack_rendered = {
        "product/examples/langchain.md": f'<h1 id="t">My pipeline is LangChain: what changed when I upgraded it?{headerlink}</h1><p>Body.</p>',
        "product/examples/llamaindex.md": '<h1 id="t">My RAG is LlamaIndex: is it still answering from the right page?</h1>',
        "product/examples/langgraph.md": f'<h1 id="t">My agent calls the right tools, but with the right arguments?{headerlink}</h1>',
        "product/examples/langchain4j.md": '<h1 id="t">My app is <code>LangChain4j</code>: what do I put in my repo?</h1>',
        "product/docker.md": '<h1 id="t">The official digline image</h1>\n<p><code>ghcr.io/digline/digline</code></p><p>The <code>other</code>.</p>',
        "product/mcp.md": '<h1 id="t">digline over MCP</h1>\n<p><code>digline-mcp</code> is the <a href="x">MCP</a> server.</p>',
    }
    docs_text = "uv add digline-anthropic, or digline-openai; digline-bedrock (Converse API)."
    band = stack(stack_pages, stack_rendered, docs_text)
    expect("providers", [(p["name"], p["package"]) for p in band["providers"]],
           [("Anthropic", "digline-anthropic"), ("OpenAI-compatible", "digline-openai"),
            ("Amazon Bedrock", "digline-bedrock")])
    expect("questions: after the colon, or the whole title",
           [e["question"] for e in band["examples"]],
           ["what changed when I upgraded it?", "is it still answering from the right page?",
            "My agent calls the right tools, but with the right arguments?",
            "what do I put in my repo?"])
    expect("example links", band["examples"][0]["href"], "product/examples/langchain/")
    expect("run rows", [(r["name"], r["code"], r["href"]) for r in band["run"]],
           [("Docker image", "ghcr.io/digline/digline", "product/docker/"),
            ("MCP server", "digline-mcp", "product/mcp/")])

    stack_refusals = [
        ("a provider package no page writes",
         lambda p, r, t: (p, r, t.replace("digline-bedrock", "digline-aws")),
         "writes that package name"),
        ("a longer name is not the package",
         lambda p, r, t: (p, r, t.replace("digline-openai", "digline-openai-extra")),
         "`digline-openai`, and no page under product/"),
        ("an example page the build does not have",
         lambda p, r, t: (p - {"product/examples/langgraph.md"}, r, t),
         "product/examples/langgraph.md, which the build does not have"),
        ("an example page with no title",
         lambda p, r, t: (p, {**r, "product/examples/llamaindex.md": "<p>No title.</p>"}, t),
         "from the title of product/examples/llamaindex.md"),
        ("a Docker page whose first paragraph has no code",
         lambda p, r, t: (p, {**r, "product/docker.md": "<h1>Image</h1><p>No name here.</p><p><code>late</code></p>"}, t),
         "first paragraph of product/docker.md"),
    ]
    for label, mutate, needle in stack_refusals:
        try:
            stack(*mutate(set(stack_pages), dict(stack_rendered), docs_text))
        except PluginError as error:
            if needle not in str(error):
                failures.append(f"{label}: refused, but not for this: {error}")
            else:
                print(f"selftest: refused, as it must — {label}: {str(error).splitlines()[0]}")
            continue
        failures.append(f"{label}: accepted, which it exists to refuse")

    grid_refusals = [
        ("a command with no group",
         lambda d, p, h, m: d["cli_commands"]["items"].append({"name": "doctor", "help": "x"}),
         "does not group: doctor"),
        ("a group naming a command digline does not have",
         lambda d, p, h, m: d["cli_commands"]["items"].pop(
             next(i for i, c in enumerate(d["cli_commands"]["items"]) if c["name"] == "migrate")),
         "commands digline does not have: migrate"),
        ("a command with no page and no place in the guide",
         lambda d, p, h, m: None, "`digline view` has no page of its own"),
        ("a check of an unknown kind",
         lambda d, p, h, m: d["checks"]["items"][0].update(kind="heuristic"),
         "a kind the home does not know: heuristic"),
        ("a check whose card is not on metrics",
         lambda d, p, h, m: m.discard("repeated"), "no card on product/metrics/ for Repeated"),
    ]
    for label, mutate, needle in grid_refusals:
        d, p, h, m = copy.deepcopy(grid_data), set(pages), guide_html, set(metrics_ids)
        mutate(d, p, h, m)
        if label == "a command with no page and no place in the guide":
            p.discard("product/view.md")
        try:
            grids(d, p, h, m)
        except PluginError as error:
            if needle not in str(error):
                failures.append(f"{label}: refused, but not for this: {error}")
            else:
                print(f"selftest: refused, as it must — {label}: {str(error).splitlines()[0]}")
            continue
        failures.append(f"{label}: accepted, which it exists to refuse")

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
        ("no cli_commands", lambda d: d.pop("cli_commands"), None, "cli_commands is missing"),
        ("no checks", lambda d: d.pop("checks"), None, "checks is missing"),
        ("empty cli_commands", lambda d: d["cli_commands"].update(items=[]), None,
         "cli_commands.items is missing or empty"),
        ("checks without items", lambda d: d["checks"].pop("items"), None,
         "checks.items is missing or empty"),
        ("checks without a source", lambda d: d["checks"].pop("source"), None,
         "checks has no source"),
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

    for failure in failures:
        print(f"selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print(f"selftest: home.json fixture computes as expected, grids, stack band and the nav's "
          f"command groups included; "
          f"{len(cases) + len(grid_refusals) + len(stack_refusals) + len(split_refusals)} refusals refused")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        raise SystemExit(selftest())
    print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
    raise SystemExit(2)
