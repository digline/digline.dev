"""The two indexes under Docs, filled from what they index.

Neither page lists anything by hand. Each carries a placeholder, an HTML comment
naming this file, and this hook replaces it in the page's Markdown:

  * ``product/examples/`` — pages/product/examples/index.md, installed by
    tools/sync-docs.sh. One tile per page in the nav's ``Examples`` group, in
    the nav's order: the page's label in the nav as its name, and under it the
    question its title asks, by the home's rule (``page_question`` in home.py:
    the title after its colon, or the whole title when it has none). A title
    with no colon that is not a question either ("I'm writing a prompt and have
    no application yet") says what the name already says, and its tile has no
    second line. A link in
    the group that leads off this site — digline/brief — is a line of its own
    under the tiles, marked as external.
  * ``product/adr/`` — written by tools/sync-docs.sh. A table of every record
    in the build (``product/adr/[0-9]*.md``), in filename order: its number, its
    title as a link, its status and its date. All four are read from the lines
    above the record's first ``## ``, where every record states them:

        # ADR 0006 — Repeated samples and the noise floor
        - Status: accepted — implemented on `adr-0006`; ships in core 0.4.0
        - Date: 2026-09-02

    The status is the first word of its line, as written; whatever follows it
    on that line and the lines under it is the record's to explain. Any other
    line of that list (Amended, Corrected, Assumes, Touches) is not read.

Filled in the Markdown, in on_page_markdown, rather than in the rendered HTML:
the search index, the table of contents and the Markdown copy llms.py writes
beside the page all carry the list, not the placeholder.

── what fails the build ─────────────────────────────────────────────────────
  * either index has no placeholder, or the nav has no Examples group holding
    at least one page;
  * an example page has no ``# Title``;
  * a record has no ``# ADR NNNN — Title`` as its first line of text, or a
    number that is not the one its filename starts with, or no ``- Status:``
    word, or no ``- Date:`` that is a date, above its first ``## ``;
  * after the build: a tile's page was not written into site/, or its question
    is not what that page's title asks there.

The fix for a record or an example is in digline/digline, and the message says
which file: anything changed under docs/product/ here is overwritten by the
next sync.

    usage: tools/hooks/indexes.py --selftest
"""

from __future__ import annotations

import datetime
import os
import posixpath
import re
import sys
from html import escape

import markdown as _markdown
from mkdocs.exceptions import PluginError

# home.py sits beside this file, and mkdocs puts a hook's folder on sys.path
# while it loads it: the rule for a question is written once, there.
from home import page_question, page_title

EXAMPLES_INDEX = "product/examples/index.md"
DECISIONS_INDEX = "product/adr/index.md"
EXAMPLES_SECTION = "Examples"

_EXAMPLES_SLOT = re.compile(r"<!--\s*examples:.*?-->", re.S)
_DECISIONS_SLOT = re.compile(r"<!--\s*decisions:.*?-->", re.S)

_RECORD = re.compile(r"^product/adr/(\d{4})-[^/]*\.md$")
_ADR_TITLE = re.compile(r"\A# ADR (\d{4}) — (\S.*?)\s*$")
_STATUS = re.compile(r"^- Status:[ \t]*([A-Za-z]+)", re.M)
_DATE_LINE = re.compile(r"^- Date:[ \t]*(.*?)[ \t]*$", re.M)
_H1 = re.compile(r"\A# (\S.*?)[ \t]*$", re.M)


def _fail(problem: str) -> PluginError:
    return PluginError(f"indexes: {problem}")


# ── the Decisions table ──────────────────────────────────────────────────────


def read_record(text: str, src_uri: str) -> dict[str, str]:
    """Number, title, status and date of one record, from the lines above its
    first `## `. Anything missing fails, naming the file to fix in digline."""
    name = posixpath.basename(src_uri)
    where = f"docs/adr/{name} in digline/digline"
    head = re.split(r"^## ", text, maxsplit=1, flags=re.M)[0].lstrip()
    title = _ADR_TITLE.match(head.split("\n", 1)[0])
    if not title:
        raise _fail(
            f"{src_uri} does not open on `# ADR NNNN — Title`, so the Decisions table has "
            f"no number and no title for it. The fix belongs in {where}.")
    expected = _RECORD.match(src_uri)
    if expected and expected.group(1) != title.group(1):
        raise _fail(
            f"{src_uri} is titled ADR {title.group(1)}, and its filename says "
            f"{expected.group(1)}. The fix belongs in {where}.")
    status = _STATUS.search(head)
    if not status:
        raise _fail(
            f"{src_uri} has no `- Status: <word>` above its first `## `, so the Decisions "
            f"table cannot say whether it is accepted. The fix belongs in {where}.")
    date = _DATE_LINE.search(head)
    if not date:
        raise _fail(
            f"{src_uri} has no `- Date: YYYY-MM-DD` above its first `## `. "
            f"The fix belongs in {where}.")
    try:
        datetime.date.fromisoformat(date.group(1))
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date.group(1)):
            raise ValueError
    except ValueError:
        raise _fail(
            f"{src_uri} has `- Date: {date.group(1)}`, which is not a date written "
            f"YYYY-MM-DD. The fix belongs in {where}.") from None
    return {"number": title.group(1), "title": title.group(2),
            "status": status.group(1), "date": date.group(1)}


def decisions_table(records: list[tuple[str, str]]) -> str:
    """The table, from (src_uri, Markdown) of each record, in filename order."""
    if not records:
        raise _fail("the Decisions index has no record to list: no product/adr/NNNN-*.md "
                    "in the build.")
    rows = ['<div class="dg-decisions" markdown="1">', "",
            "| ADR | Decision | Status | Date |", "|---|---|---|---|"]
    for src_uri, text in sorted(records):
        r = read_record(text, src_uri)
        title = r["title"].replace("|", "\\|")
        rows.append(f"| {r['number']} | [{title}]({posixpath.basename(src_uri)}) "
                    f"| {r['status']} | {r['date']} |")
    return "\n".join(rows + ["", "</div>"])


def fill(markdown: str, slot: re.Pattern, content: str, src_uri: str, name: str) -> str:
    """The page with its placeholder replaced, or the build stops."""
    if not slot.search(markdown):
        raise _fail(
            f"{src_uri} has no placeholder for its list — an HTML comment opening "
            f"`<!-- {name}:` — so there is nowhere to put it.")
    return slot.sub(lambda _: content, markdown, count=1)


# ── the Examples tiles ───────────────────────────────────────────────────────


def title_html(text: str, src_uri: str) -> str:
    """The page's `# Title`, its first line, rendered the way its page renders
    it."""
    match = _H1.search(text.lstrip())
    if not match:
        raise _fail(
            f"{src_uri} has no `# Title`, so the Examples index has no question for it. "
            f"The fix belongs in examples/{posixpath.splitext(posixpath.basename(src_uri))[0]}"
            "/README.md in digline/digline.")
    return _markdown.markdown("# " + match.group(1))


def tile_question(page_html: str, source: str) -> str | None:
    """The second line of an example's tile: the question its title asks, or
    None when the title has no colon and does not end on a question mark —
    the whole title, which would only say again what the name says."""
    title = page_title(page_html, source)
    if ":" not in title and not title.endswith("?"):
        return None
    return page_question(page_html, source)


def examples_html(pages: list[dict], links: list[dict]) -> str:
    """The tiles, then the external lines.

    pages  {"name", "href", "html"} per page in the group, `html` its rendered
           `# Title`
    links  {"name", "url"} per link in the group that leaves the site
    """
    if not pages:
        raise _fail(f"the nav's {EXAMPLES_SECTION} group has no page, so its index has nothing "
                    "to show.")
    tiles = []
    for p in pages:
        question = tile_question(p["html"], p["href"])
        second = "" if question is None else f'<span class="dg-example__question">{escape(question)}</span>'
        tiles.append(
            f'<li><a class="dg-example" href="{escape(p["href"])}">'
            f'<span class="dg-example__text"><span class="dg-example__name">{escape(p["name"])}</span>'
            f'{second}</span>'
            f'<span class="dg-example__arrow" aria-hidden="true">&rarr;</span></a></li>')
    out = ['<ul class="dg-examples">', *tiles, "</ul>"]
    for link in links:
        out.append(
            f'<p class="dg-examples__external"><span class="dg-examples__tag">External</span> '
            f'<a href="{escape(link["url"])}">{escape(link["name"])}</a></p>')
    return "\n".join(out)


# ── the hooks mkdocs calls ───────────────────────────────────────────────────

_examples: list = []   # the pages of the Examples group, in nav order
_external: list = []   # its links off the site
_records: list = []    # the records' Files
_tiles: list = []      # (src_uri, question or None) of each tile, for on_post_build


def on_files(files, config, **kwargs):
    _records[:] = [f for f in files.documentation_pages() if _RECORD.match(f.src_uri)]
    return files


def on_nav(nav, config, files, **kwargs):
    def find(items):
        for item in items:
            if getattr(item, "is_section", False):
                if item.title == EXAMPLES_SECTION:
                    return item
                found = find(item.children)
                if found:
                    return found
        return None

    section = find(nav.items)
    if section is None:
        raise _fail(f"the nav has no `{EXAMPLES_SECTION}:` group for its index to show.")
    _examples[:] = [c for c in section.children
                    if getattr(c, "is_page", False) and c.file.src_uri != EXAMPLES_INDEX]
    _external[:] = [c for c in section.children if getattr(c, "is_link", False)]
    return nav


def on_page_markdown(markdown, page, config, files, **kwargs):
    src = page.file.src_uri
    if src == DECISIONS_INDEX:
        records = []
        for f in _records:
            with open(f.abs_src_path, encoding="utf-8") as fh:
                records.append((f.src_uri, fh.read()))
        return fill(markdown, _DECISIONS_SLOT, decisions_table(records), src, "decisions")
    if src == EXAMPLES_INDEX:
        here = posixpath.dirname(src)
        pages = []
        for child in _examples:
            with open(child.file.abs_src_path, encoding="utf-8") as fh:
                html = title_html(fh.read(), child.file.src_uri)
            href = posixpath.relpath(child.file.src_uri[: -len(".md")], here) + "/"
            pages.append({"name": child.title, "href": href, "html": html,
                          "src": child.file.src_uri})
        _tiles[:] = [(p["src"], tile_question(p["html"], p["src"])) for p in pages]
        links = [{"name": link.title, "url": link.url} for link in _external]
        return fill(markdown, _EXAMPLES_SLOT, examples_html(pages, links), src, "examples")
    return markdown


def on_post_build(config, **kwargs):
    """Each tile against the page as it was written: there, and asking the
    question the tile says it asks, or none where the tile has no second line."""
    site = config["site_dir"]
    for src, question in _tiles:
        written = os.path.join(site, src[: -len(".md")], "index.html")
        if not os.path.isfile(written):
            raise _fail(f"the Examples index links to {src}, and {written} was not written.")
        with open(written, encoding="utf-8") as fh:
            if tile_question(fh.read(), src) != question:
                raise _fail(f"the Examples index asks {question!r} for {src}, which is not "
                            f"what the title of {written} asks.")


# ── the selftest ─────────────────────────────────────────────────────────────


def selftest() -> int:
    failures: list[str] = []

    def expect(label, actual, wanted):
        if actual != wanted:
            failures.append(f"{label}: {actual!r}, wanted {wanted!r}")

    def refused(label, call, needle):
        try:
            call()
        except PluginError as error:
            if needle not in str(error):
                failures.append(f"{label}: refused, but not for this: {error}")
            else:
                print(f"indexes selftest: refused, as it must — {label}")
            return
        failures.append(f"{label}: accepted, which it exists to refuse")

    # 1. A record of every shape the real ones have: a note before the list, a
    #    status that runs on over lines, a status with a date after its word,
    #    Amended and Corrected lines, and a Status line further down the body
    #    that must not be read.
    note = ("# ADR 0001 — The assertion produces a three-state `Verdict`\n\n"
            "> **Note on the name (2026-08-26).** a note.\n\n"
            "- Status: accepted\n- Date: 2026-08-25\n- Touches: fixed decision 1\n\n"
            "## Context\n\n- Status: superseded\n")
    long_status = ("# ADR 0011 — The MCP server (`digline-mcp`)\n\n"
                   "- Status: accepted 2026-09-08 — the text first, the implementation\n"
                   "  written against it\n- Date: 2026-09-08\n"
                   "- Amended: 2026-09-09 — **§8 gains the check.**\n"
                   "- Corrected: 2026-09-15, before release\n\n## Context\n")
    proposed = "# ADR 0024 — A title with a | in it\n\n- Status: proposed — the text first\n- Date: 2026-09-16\n\n## Context\n"
    expect("a record with a note", read_record(note, "product/adr/0001-verdict-not-score.md"),
           {"number": "0001", "title": "The assertion produces a three-state `Verdict`",
            "status": "accepted", "date": "2026-08-25"})
    expect("a status that runs on, and Amended and Corrected ignored",
           read_record(long_status, "product/adr/0011-the-mcp-server.md"),
           {"number": "0011", "title": "The MCP server (`digline-mcp`)",
            "status": "accepted", "date": "2026-09-08"})
    table = decisions_table([("product/adr/0024-x.md", proposed),
                             ("product/adr/0011-the-mcp-server.md", long_status),
                             ("product/adr/0001-verdict-not-score.md", note)])
    expect("the table, in filename order, a pipe in a title escaped", table.split("\n"), [
        '<div class="dg-decisions" markdown="1">', "",
        "| ADR | Decision | Status | Date |",
        "|---|---|---|---|",
        "| 0001 | [The assertion produces a three-state `Verdict`](0001-verdict-not-score.md) | accepted | 2026-08-25 |",
        "| 0011 | [The MCP server (`digline-mcp`)](0011-the-mcp-server.md) | accepted | 2026-09-08 |",
        "| 0024 | [A title with a \\| in it](0024-x.md) | proposed | 2026-09-16 |",
        "", "</div>",
    ])
    page = "# Decisions\n\nWhy.\n\n<!-- decisions: filled here. -->\n"
    expect("the placeholder filled", fill(page, _DECISIONS_SLOT, "TABLE", DECISIONS_INDEX, "decisions"),
           "# Decisions\n\nWhy.\n\nTABLE\n")

    # 2. Every way a record stops saying what the table needs.
    src = "product/adr/0006-repeated-samples.md"
    good = "# ADR 0006 — Repeated samples\n\n- Status: accepted\n- Date: 2026-09-02\n\n## Context\n"
    refused("no title", lambda: read_record(good.replace("# ADR 0006 — ", "# "), src),
            "does not open on `# ADR NNNN — Title`")
    refused("a hyphen where the title has an em dash",
            lambda: read_record(good.replace(" — ", " - "), src), "does not open on")
    refused("a number that is not the filename's",
            lambda: read_record(good.replace("0006", "0007"), src),
            "is titled ADR 0007, and its filename says 0006")
    refused("no status", lambda: read_record(good.replace("- Status: accepted\n", ""), src),
            "has no `- Status: <word>`")
    refused("an empty status", lambda: read_record(good.replace("accepted", ""), src),
            "has no `- Status: <word>`")
    refused("a status only below the first ##",
            lambda: read_record(good.replace("- Status: accepted\n", "") + "- Status: accepted\n", src),
            "has no `- Status: <word>`")
    refused("no date", lambda: read_record(good.replace("- Date: 2026-09-02\n", ""), src),
            "has no `- Date: YYYY-MM-DD`")
    refused("a date that is not a date",
            lambda: read_record(good.replace("2026-09-02", "2026-09-31"), src),
            "which is not a date written YYYY-MM-DD")
    refused("a date written another way",
            lambda: read_record(good.replace("2026-09-02", "2 September 2026"), src),
            "which is not a date written YYYY-MM-DD")
    refused("the fix is named in digline",
            lambda: read_record(good.replace("- Date: 2026-09-02\n", ""), src),
            "docs/adr/0006-repeated-samples.md in digline/digline")
    refused("no records", lambda: decisions_table([]), "has no record to list")
    refused("no placeholder", lambda: fill("# Decisions\n", _DECISIONS_SLOT, "T", DECISIONS_INDEX, "decisions"),
            "has no placeholder for its list — an HTML comment opening `<!-- decisions:`")

    # 3. The Examples tiles: a title with a colon, a question without one, a
    #    statement without one (no second line), code in a title, a name that
    #    needs escaping, and the external line.
    pages = [
        {"name": "A LangChain pipeline", "href": "langchain/",
         "html": title_html("# My pipeline is LangChain: what changed when I upgraded it?\n\nBody.",
                            "product/examples/langchain.md")},
        {"name": "A LangGraph agent", "href": "langgraph/",
         "html": title_html("\n# My agent calls the right tools, but with the right arguments?\n",
                            "product/examples/langgraph.md")},
        {"name": "A prompt, no application yet", "href": "prompt-first/",
         "html": title_html("# I'm writing a prompt and have no application yet\n",
                            "product/examples/prompt-first.md")},
        {"name": "A <LangChain4j> service", "href": "langchain4j/",
         "html": title_html("# My app is `LangChain4j`: what do I put in my repo?",
                            "product/examples/langchain4j.md")},
    ]
    html = examples_html(pages, [{"name": "A whole product (digline/brief)",
                                  "url": "https://github.com/digline/brief"}])
    expect("questions: after the colon, or the whole title when it asks one",
           re.findall(r'dg-example__question">(.*?)<', html),
           ["what changed when I upgraded it?",
            "My agent calls the right tools, but with the right arguments?",
            "what do I put in my repo?"])
    expect("names, escaped", re.findall(r'dg-example__name">(.*?)<', html),
           ["A LangChain pipeline", "A LangGraph agent", "A prompt, no application yet",
            "A &lt;LangChain4j&gt; service"])
    expect("a statement with no colon: the name, and no second line",
           [t for t in html.split("\n") if 'href="prompt-first/"' in t],
           ['<li><a class="dg-example" href="prompt-first/"><span class="dg-example__text">'
            '<span class="dg-example__name">A prompt, no application yet</span></span>'
            '<span class="dg-example__arrow" aria-hidden="true">&rarr;</span></a></li>'])
    expect("tile_question: none for a statement, the question otherwise",
           [tile_question(p["html"], p["href"]) for p in pages],
           ["what changed when I upgraded it?",
            "My agent calls the right tools, but with the right arguments?",
            None, "what do I put in my repo?"])
    expect("links", re.findall(r'href="([^"]*)"', html),
           ["langchain/", "langgraph/", "prompt-first/", "langchain4j/", "https://github.com/digline/brief"])
    expect("the external line comes after the tiles, marked",
           html.split("\n")[-1],
           '<p class="dg-examples__external"><span class="dg-examples__tag">External</span> '
           '<a href="https://github.com/digline/brief">A whole product (digline/brief)</a></p>')
    refused("an example with no title",
            lambda: title_html("No heading here.\n", "product/examples/rag.md"),
            "The fix belongs in examples/rag/README.md")
    refused("a title that is not the first line",
            lambda: title_html("Intro.\n\n```sh\n# a comment\n```\n", "product/examples/rag.md"),
            "has no `# Title`")
    refused("a group with no page", lambda: examples_html([], []), "has no page")
    refused("no placeholder on the Examples index",
            lambda: fill("# Examples\n", _EXAMPLES_SLOT, "T", EXAMPLES_INDEX, "examples"),
            "`<!-- examples:`")

    # 4. The placeholders the two pages really carry.
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    with open(os.path.join(root, "pages", "product", "examples", "index.md"), encoding="utf-8") as fh:
        expect("pages/product/examples/index.md carries its placeholder",
               bool(_EXAMPLES_SLOT.search(fh.read())), True)
    with open(os.path.join(root, "tools", "sync-docs.sh"), encoding="utf-8") as fh:
        expect("tools/sync-docs.sh writes the Decisions placeholder",
               bool(_DECISIONS_SLOT.search(fh.read())), True)

    for failure in failures:
        print(f"indexes selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("indexes selftest: the Decisions table from records of every shape, the Examples "
          "tiles and their external line, and every missing field and placeholder refused")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        raise SystemExit(selftest())
    print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
    raise SystemExit(2)
