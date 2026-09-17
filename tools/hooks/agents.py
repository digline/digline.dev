"""/agents/: its links to AGENTS.md at a release, and the quotation that closes it.

The page closes on rule 1 of digline's AGENTS.md, quoted in
overrides/agents.html — not in docs/agents.md, so that a translation of the
page never rewrites digline's words. Those words are digline's and change
there, so they are held to a release: tools/sync-docs.sh writes
.agents-rule.json (tools/agents_rule.py) — the latest v* tag the checkout it
copies from contains, that tag's commit, and rule 1's text at that tag. This
hook does two things with it.

── before the page renders (on_page_markdown) ────────────────────────────────
The page's links to AGENTS.md and to the skill's folder are written in its
Markdown as links to digline's main, which is where a reader of the source
finds them. On the site they lead to the release tag instead, so a file
renamed on main tomorrow does not break them: each of LINKS is replaced by
its form at the tag. A link of LINKS the Markdown does not have fails the build
— a rewrite that silently matches nothing is how a page goes back to main. The
template gets ``page.meta.agents_rule``: the tag, and AGENTS.md's URL at it.

── after the build (on_post_build) ───────────────────────────────────────────
site/agents/index.html must hold exactly one <blockquote class="agents-rule__quote">,
and its text, whitespace normalized, must be rule 1's at the tag, rendered
from its Markdown the same way. The build fails otherwise, and when
.agents-rule.json is missing or has no rule or no tag. Only that element is
read: a blockquote the Markdown writes, or anything else the page says, has no
say in it. The caption under it is the template's too, printed from
page.meta.agents_rule: it must name digline at the file's tag and link to
AGENTS.md at that tag, and so must the quotation's cite — a tag typed into the
template instead would fail as soon as the file moved to the next release
(caption_problems).

The search index is checked too, since the page left Material's template:
search/search_index.json must hold /agents/ with its title and its opening in
readable text, an entry for each tile (each <h3> in a .tile of the page), and
no translated page (search_problems).

    usage: tools/hooks/agents.py --selftest
"""

from __future__ import annotations

import json
import os
import re
import sys
from html.parser import HTMLParser

from mkdocs.exceptions import PluginError

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(TOOLS)

PAGE = "agents.md"
RULE_FILE = ".agents-rule.json"
QUOTE_CLASS = "agents-rule__quote"
REPOSITORY = "https://github.com/digline/digline"
# The page's links to digline's main, and their form at a release tag.
LINKS = {
    f"{REPOSITORY}/blob/main/AGENTS.md": REPOSITORY + "/blob/{tag}/AGENTS.md",
    f"{REPOSITORY}/tree/main/.claude/skills/operating-digline": REPOSITORY + "/tree/{tag}/.claude/skills/operating-digline",
}


def load(path: str) -> dict:
    """.agents-rule.json, refused when it cannot stand behind a quotation."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as error:
        raise PluginError(f"agents: {path} cannot be read ({error}). tools/sync-docs.sh writes it: "
                          "run `make docs` against a digline checkout.") from None
    if not isinstance(data, dict) or not str(data.get("tag") or "").startswith("v"):
        raise PluginError(f"agents: {path} names no release tag, so there is no release to quote")
    if not str(data.get("rule") or "").strip():
        raise PluginError(f"agents: {path} has no rule 1 of AGENTS.md at {data.get('tag')}: nothing to hold the "
                          "quotation on /agents/ to")
    return data


def at_tag(markdown: str, tag: str, source: str) -> str:
    """The page's links to digline's main, at the tag; refused when one is missing."""
    missing = [url for url in LINKS if url not in markdown]
    if missing:
        raise PluginError(f"agents: {source} has no link to {', '.join(missing)} — the page's links to AGENTS.md "
                          "and the skill are written to main and led to the release tag here")
    for url, form in LINKS.items():
        markdown = markdown.replace(url, form.format(tag=tag))
    return markdown


class _Text(HTMLParser):
    """The text of every <blockquote class="agents-rule__quote">, one string each."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.quotes: list[str] = []
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        if self._depth:
            if tag == "blockquote":
                self._depth += 1
            return
        if tag == "blockquote" and QUOTE_CLASS in (dict(attrs).get("class") or "").split():
            self._depth = 1
            self.quotes.append("")

    def handle_endtag(self, tag):
        if self._depth and tag == "blockquote":
            self._depth -= 1

    def handle_data(self, data):
        if self._depth:
            self.quotes[-1] += data


def text_of(html: str) -> list[str]:
    parser = _Text()
    parser.feed(html)
    return [" ".join(quote.split()) for quote in parser.quotes]


def rendered(rule_markdown: str) -> str:
    """Rule 1's text as a reader sees it: its Markdown rendered, tags taken off."""
    import markdown  # mkdocs' own dependency

    parser = HTMLParser(convert_charrefs=True)
    chunks: list[str] = []
    parser.handle_data = chunks.append
    parser.feed(markdown.markdown(rule_markdown))
    return " ".join("".join(chunks).split())


def quotation_problems(page_html: str, rule: dict) -> list[str]:
    quotes = text_of(page_html)
    if len(quotes) != 1:
        return [f"agents/index.html: {len(quotes)} <blockquote class=\"{QUOTE_CLASS}\">, and the page closes on one"]
    wanted = rendered(rule["rule"])
    if quotes[0] != wanted:
        return [f"agents/index.html: the quotation is not rule 1 of AGENTS.md at {rule['tag']}.\n"
                f"    on the page: {quotes[0]!r}\n    at the tag:  {wanted!r}\n"
                "  Change overrides/agents.html to the text at the tag."]
    return []


class _Caption(HTMLParser):
    """The quotation's cite, and the caption's text and links."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cites: list[str] = []
        self.captions: list[list] = []
        self._in = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = (attrs.get("class") or "").split()
        if tag == "blockquote" and QUOTE_CLASS in classes:
            self.cites.append(attrs.get("cite") or "")
        elif tag == "figcaption" and "agents-rule__source" in classes:
            self._in = True
            self.captions.append(["", []])
        elif tag == "a" and self._in:
            self.captions[-1][1].append(attrs.get("href") or "")

    def handle_endtag(self, tag):
        if tag == "figcaption":
            self._in = False

    def handle_data(self, data):
        if self._in:
            self.captions[-1][0] += data


def caption_problems(page_html: str, rule: dict) -> list[str]:
    parser = _Caption()
    parser.feed(page_html)
    url = LINKS[f"{REPOSITORY}/blob/main/AGENTS.md"].format(tag=rule["tag"])
    if len(parser.captions) != 1:
        return [f"agents/index.html: {len(parser.captions)} captions under the quotation, and it has one"]
    text, links = " ".join(parser.captions[0][0].split()), parser.captions[0][1]
    problems = []
    if f"digline {rule['tag']}" not in text:
        problems.append(f"agents/index.html: the caption reads {text!r}, and the quotation is from {rule['tag']}")
    if links != [url]:
        problems.append(f"agents/index.html: the caption links to {links}, and AGENTS.md at {rule['tag']} is {url}")
    if parser.cites != [url]:
        problems.append(f"agents/index.html: the quotation's cite is {parser.cites}, and it should be {url}")
    return problems


def search_problems(index: dict, page_html: str) -> list[str]:
    """/agents/ in the search index as a reader of the results would see it."""
    docs = index.get("docs", [])
    entries = {d.get("location"): d for d in docs}
    problems = []
    top = entries.get("agents/")
    if top is None:
        problems.append("search: no entry for agents/")
    else:
        text = " ".join(re.sub(r"<[^>]+>", " ", top.get("text") or "").split())
        if top.get("title") != "digline for agents":
            problems.append(f"search: agents/ is titled {top.get('title')!r}")
        if not text.startswith("An agent can measure everything and approve nothing."):
            problems.append(f"search: agents/ reads {text[:80]!r}, not the page's opening")
    tiles = re.findall(r'<div class="tile">\s*<h3 id="([^"]+)"', page_html)
    if not tiles:
        problems.append("search: the page has no tiles to look for")
    for tile in tiles:
        entry = entries.get(f"agents/#{tile}")
        if entry is None or not (entry.get("title") or "").strip() or not (entry.get("text") or "").strip():
            problems.append(f"search: no readable entry for the tile agents/#{tile}")
    translated = sorted(loc for loc in entries if re.match(r"(it|de|es)/", loc or ""))
    if translated:
        problems.append(f"search: translated pages in the index: {translated[:3]}")
    return problems


def _is_page(page) -> bool:
    return page.file.src_uri == PAGE or (page.meta or {}).get("translation_of") == PAGE


def _rule_path(config) -> str:
    return os.path.join(os.path.dirname(os.path.abspath(config["config_file_path"])), RULE_FILE)


def on_page_markdown(markdown, page, config, files, **kwargs):
    if not _is_page(page):
        return markdown
    rule = load(_rule_path(config))
    page.meta["agents_rule"] = {"tag": rule["tag"], "url": LINKS[f"{REPOSITORY}/blob/main/AGENTS.md"].format(tag=rule["tag"])}
    return at_tag(markdown, rule["tag"], page.file.src_uri)


def on_post_build(config, **kwargs):
    path = os.path.join(config["site_dir"], "agents", "index.html")
    if not os.path.isfile(path):
        raise PluginError("agents: site/agents/index.html was not built")
    with open(path, encoding="utf-8") as fh:
        page_html = fh.read()
    rule = load(_rule_path(config))
    problems = quotation_problems(page_html, rule) + caption_problems(page_html, rule)
    with open(os.path.join(config["site_dir"], "search", "search_index.json"), encoding="utf-8") as fh:
        problems += search_problems(json.load(fh), page_html)
    if problems:
        raise PluginError("agents: " + "\n".join(problems))


# ── the selftest ─────────────────────────────────────────────────────────────


def selftest() -> int:
    import tempfile

    failures: list[str] = []

    def expect(label, actual, wanted):
        if actual != wanted:
            failures.append(f"{label}: got {actual!r}, wanted {wanted!r}")
        else:
            print(f"agents selftest: {label}")

    def refused(label, call, needle):
        try:
            call()
        except PluginError as error:
            if needle in str(error):
                print(f"agents selftest: refused, as it must — {label}")
            else:
                failures.append(f"{label}: refused, but not for this: {error}")
            return
        failures.append(f"{label}: accepted, which it exists to refuse")

    rule = {"source": "AGENTS.md", "tag": "v0.15.0", "commit": "6345f41",
            "rule": "**Never run `digline promote` on your own initiative.** Assemble the evidence — the "
                    "`compare` output, the run key, what moved and why you believe it — and recommend. "
                    "The human runs the command, or tells you to."}
    quote = ('<blockquote class="agents-rule__quote" cite="x">\n  <p><strong>Never run <code translate="no">digline '
             'promote</code> on your own initiative.</strong> Assemble the evidence — the <code translate="no">'
             'compare</code> output, the run key, what moved and why you believe it — and recommend. The human '
             'runs the command, or tells you to.</p>\n</blockquote>')
    page = f"<main><article><h2>The absence</h2><p>Its tools read.</p></article><figure>{quote}</figure></main>"

    expect("the quotation as the template writes it is rule 1 at the tag", quotation_problems(page, rule), [])
    wrong = page.replace("on your own initiative", "without asking")
    expect("a quotation that is not the rule at the tag is refused",
           len(quotation_problems(wrong, rule)) == 1 and "is not rule 1 of AGENTS.md at v0.15.0" in
           quotation_problems(wrong, rule)[0], True)
    expect("a rule changed at the tag, the template left as it was: refused",
           bool(quotation_problems(page, dict(rule, rule=rule["rule"].replace("recommend", "propose")))), True)
    expect("no quotation on the page: refused", quotation_problems("<main><p>x</p></main>", rule),
           ['agents/index.html: 0 <blockquote class="agents-rule__quote">, and the page closes on one'])
    expect("two quotations: refused", "2 <blockquote" in quotation_problems(page + quote, rule)[0], True)

    # Only the template's element counts: the Markdown's blockquote with the right
    # words does not rescue a wrong quotation, and what the Markdown says — a tool
    # count put back, say — changes nothing either way.
    markdown_quote = f"<blockquote><p>{rendered(rule['rule'])}</p></blockquote>"
    expect("a blockquote in the Markdown with the right words does not stand in for the template's",
           bool(quotation_problems(wrong.replace("<main>", "<main>" + markdown_quote), rule)), True)
    expect("the Markdown saying 'eight tools' has no say in the quotation gate",
           quotation_problems(page.replace("Its tools read.", "Its eight tools read."), rule), [])

    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, RULE_FILE)
        refused("no .agents-rule.json", lambda: load(path), "cannot be read")
        for label, data, needle in (
            ("no rule 1 in the file", dict(rule, rule=""), "has no rule 1 of AGENTS.md at v0.15.0"),
            ("no rule key at all", {k: v for k, v in rule.items() if k != "rule"}, "has no rule 1"),
            ("no release tag", dict(rule, tag="main"), "names no release tag"),
        ):
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
            refused(label, lambda: load(path), needle)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(rule, fh)
        expect("a whole file is read", load(path)["tag"], "v0.15.0")

    markdown = ("[`AGENTS.md`](https://github.com/digline/digline/blob/main/AGENTS.md) … "
                "[`operating-digline`](https://github.com/digline/digline/tree/main/.claude/skills/operating-digline)")
    expect("the links to AGENTS.md and the skill lead to the release tag",
           at_tag(markdown, "v0.15.0", PAGE),
           "[`AGENTS.md`](https://github.com/digline/digline/blob/v0.15.0/AGENTS.md) … "
           "[`operating-digline`](https://github.com/digline/digline/tree/v0.15.0/.claude/skills/operating-digline)")
    refused("a page without the link to the skill", lambda: at_tag(markdown.split(" … ")[0], "v0.15.0", PAGE),
            "has no link to https://github.com/digline/digline/tree/main/.claude/skills/operating-digline")

    # The caption: the tag and the link are the file's, not the template's.
    caption = ('<figcaption class="agents-rule__source"><a href="https://github.com/digline/digline/blob/v0.15.0/AGENTS.md">'
               '<code translate="no">AGENTS.md</code></a>, rule 1 — digline v0.15.0</figcaption>')
    cited = page.replace('cite="x"', 'cite="https://github.com/digline/digline/blob/v0.15.0/AGENTS.md"') + caption
    expect("the caption and the cite name the file's tag", caption_problems(cited, rule), [])
    moved = dict(rule, tag="v0.16.0")
    found = caption_problems(cited, moved)
    expect("the file at another tag, the caption still at v0.15.0 (a tag typed into the template): refused",
           (any("the quotation is from v0.16.0" in p for p in found), any("the caption links to" in p for p in found),
            any("cite is" in p for p in found)), (True, True, True))
    expect("no caption: refused", "0 captions" in caption_problems(page, rule)[0], True)

    # The search index.
    tiles_html = ('<div class="tile">\n<h3 id="the-mcp-server">The MCP server</h3>'
                  '<div class="tile">\n<h3 id="the-operator">The operator</h3>')
    index = {"docs": [
        {"location": "agents/", "title": "digline for agents",
         "text": "<p>An agent can measure everything and approve nothing. Measurement is work</p>"},
        {"location": "agents/#the-mcp-server", "title": "The MCP server", "text": "<p>Its tools list runs</p>"},
        {"location": "agents/#the-operator", "title": "The operator", "text": "<p>It watches a suite</p>"},
        {"location": "why/", "title": "Why", "text": "<p>…</p>"},
    ]}
    expect("search: agents/ with its title and opening, an entry per tile, no translation", search_problems(index, tiles_html), [])
    for label, change, needle in (
        ("agents/ missing", lambda d: [e for e in d if e["location"] != "agents/"], "no entry for agents/"),
        ("agents/ unreadable", lambda d: [dict(e, text="<p></p>") if e["location"] == "agents/" else e for e in d],
         "not the page's opening"),
        ("a tile missing", lambda d: [e for e in d if e["location"] != "agents/#the-operator"],
         "no readable entry for the tile agents/#the-operator"),
        ("/it/why/ in the index", lambda d: d + [{"location": "it/why/", "title": "Perché", "text": "<p>x</p>"}],
         "translated pages in the index"),
    ):
        found = search_problems({"docs": change(index["docs"])}, tiles_html)
        expect(f"search: {label} refused", any(needle in p for p in found), True)

    for failure in failures:
        print(f"agents selftest: FAILED — {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        raise SystemExit(selftest())
    print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
    raise SystemExit(2)
