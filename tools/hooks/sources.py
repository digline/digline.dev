"""The repositories the site cites as a source, pinned so a link keeps its word.

A page that says what a repository contains has to lead to the state it read,
not to whatever that repository holds today. Two rules, one per repository,
both checked on the built site:

  * **digline/digline**: every link to AGENTS.md leads to it at the release tag
    the sync read (tools/sync-docs.sh, .agents-rule.json). A link at main, or at
    any other ref, fails the build (agents_md_link_problems).
  * **digline/brief**: every link leads to a full 40-character commit, the runs
    /why/ and the Handbook read their numbers from. main, a branch, a tag, a
    short sha and the repository's front page all fail the build
    (brief_link_problems): a tag can be moved, a branch moves by itself, and the
    front page is main's; the files a reader is sent to verify would not be the
    ones the page was written from. The one way past it is an entry in
    tools/claims-register.toml, [[link]]: a link that points at the project
    rather than supporting a number, named by its exact href and its exact text,
    with the file that writes it and why. The build fails on an entry whose
    quote is no longer in its file, or that no page of the site uses.

── the quotation on /agents/ and its translations ────────────────────────────
That page closes on rule 1 of digline's AGENTS.md, quoted in
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
/agents/ and each of its translations must hold exactly one
<blockquote class="agents-rule__quote">,
and its text, whitespace normalized, must be rule 1's at the tag, rendered
from its Markdown the same way. The build fails otherwise, and when
.agents-rule.json is missing or has no rule or no tag. Only that element is
read: a blockquote the Markdown writes, or anything else the page says, has no
say in it. The caption under it is the template's too, printed from
page.meta.agents_rule: it must name digline at the file's tag and link to
AGENTS.md at that tag, and so must the quotation's cite — a tag typed into the
template instead would fail as soon as the file moved to the next release
(caption_problems).

Every link to AGENTS.md on the site — the documentation copied from digline,
whose relative and main links tools/sync-docs.sh rewrites, and the pages written
here — must lead to AGENTS.md at the same release tag; one at main, or at any
other ref, fails the build (agents_md_link_problems).

The search index is checked too, since the page left Material's template:
search/search_index.json must hold /agents/ with its title and its opening in
readable text, an entry for each tile (each <h3> in a .tile of the page), and
no translated page (search_problems).

    usage: tools/hooks/sources.py --selftest
"""

from __future__ import annotations

import html as htmllib
import json
import os
import re
import sys
import tomllib
from dataclasses import dataclass
from html.parser import HTMLParser

from mkdocs.exceptions import PluginError

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
import languages  # noqa: E402  tools/languages.py

PAGE = "agents.md"
RULE_FILE = ".agents-rule.json"
QUOTE_CLASS = "agents-rule__quote"
REPOSITORY = "https://github.com/digline/digline"
# The page's links to digline's main, and their form at a release tag.
LINKS = {
    f"{REPOSITORY}/blob/main/AGENTS.md": REPOSITORY + "/blob/{tag}/AGENTS.md",
    f"{REPOSITORY}/tree/main/plugins/digline/skills/operating-digline": REPOSITORY + "/tree/{tag}/plugins/digline/skills/operating-digline",
}


def load(path: str) -> dict:
    """.agents-rule.json, refused when it cannot stand behind a quotation."""
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as error:
        raise PluginError(f"sources: {path} cannot be read ({error}). tools/sync-docs.sh writes it: "
                          "run `make docs` against a digline checkout.") from None
    if not isinstance(data, dict) or not str(data.get("tag") or "").startswith("v"):
        raise PluginError(f"sources: {path} names no release tag, so there is no release to quote")
    if not str(data.get("rule") or "").strip():
        raise PluginError(f"sources: {path} has no rule 1 of AGENTS.md at {data.get('tag')}: nothing to hold the "
                          "quotation on /agents/ to")
    return data


def at_tag(markdown: str, tag: str, source: str) -> str:
    """The page's links to digline's main, at the tag; refused when one is missing."""
    missing = [url for url in LINKS if url not in markdown]
    if missing:
        raise PluginError(f"sources: {source} has no link to {', '.join(missing)} — the page's links to AGENTS.md "
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


_AGENTS_MD = re.compile(r'href="https://github\.com/digline/digline/blob/([^/"]+)/AGENTS\.md(?:[#?][^"]*)?"')


def agents_md_link_problems(site: str, tag: str) -> tuple[list[str], int]:
    """Every link to AGENTS.md in site/'s pages, at a ref that is not the tag: (problems, links read)."""
    problems: list[str] = []
    read = 0
    for folder, dirs, names in os.walk(site):
        dirs.sort()
        for name in sorted(n for n in names if n.endswith(".html")):
            relative = os.path.relpath(os.path.join(folder, name), site).replace(os.sep, "/")
            with open(os.path.join(folder, name), encoding="utf-8") as fh:
                for ref in _AGENTS_MD.findall(fh.read()):
                    read += 1
                    if ref != tag:
                        problems.append(f"{relative}: a link to AGENTS.md at {ref}, and the site documents {tag} — "
                                        "tools/sync-docs.sh leads every link to AGENTS.md to the release tag")
    return problems, read


BRIEF = "https://github.com/digline/brief"
# Every href into the repository — its front page, with or without a slash, a
# #fragment or a ?query, and any path under it. Not digline/brief-something.
_BRIEF = re.compile(r'href="' + re.escape(BRIEF) + r'((?:[/#?][^"]*)?)"')
# The one shape that passes: a file, a folder or a commit at a full sha.
_PINNED = re.compile(r"\A/(?:blob|tree|commit)/[0-9a-f]{40}(?:[/#?]|\Z)")
# An <a> element, for the text a registered exception is known by.
_ANCHOR = re.compile(r'<a\b[^>]*?(href="[^"]*")[^>]*>(.*?)</a>', re.S)

REGISTER = os.path.join("tools", "claims-register.toml")


@dataclass(frozen=True)
class LinkException:
    """A link into a cited repository that is admitted unpinned: the file that
    writes it, the line there that writes it, its exact href, the exact text it
    is shown with, and why."""
    file: str
    quote: str
    href: str
    text: str
    why: str
    since: str


def load_link_exceptions(path: str) -> list[LinkException]:
    """The register's [[link]] entries. Every field required: an exception that
    does not say why is the thing the register exists to refuse."""
    with open(path, "rb") as fh:
        document = tomllib.load(fh)
    found = []
    for index, entry in enumerate(document.get("link", []), start=1):
        values = {}
        for name in ("file", "quote", "href", "text", "why", "since"):
            value = entry.get(name)
            if not isinstance(value, str) or not value.strip():
                raise PluginError(f"sources: {os.path.basename(path)}, link {index}: `{name}` is missing or empty")
            values[name] = value
        found.append(LinkException(**values))
    return found


def _words(text: str) -> str:
    return " ".join(htmllib.unescape(re.sub(r"<[^>]+>", " ", text)).split())


def link_exception_problems(root: str, exceptions: list[LinkException]) -> list[str]:
    """The file end of each exception: its quote still in its file, whitespace
    normalized, as whole words."""
    problems = []
    for entry in exceptions:
        try:
            with open(os.path.join(root, entry.file), encoding="utf-8") as fh:
                text = fh.read()
        except FileNotFoundError:
            problems.append(f"{REGISTER}: link {entry.href!r}: {entry.file} does not exist")
            continue
        # Whole words at both ends: a quote ending on the front page's URL is
        # not found in a line that goes on to /tree/<sha>.
        quote = re.escape(" ".join(entry.quote.split()))
        if not re.search(r"(?<!\S)" + quote + r"(?!\S)", " ".join(text.split())):
            problems.append(f"{REGISTER}: link {entry.href!r}: the quote is no longer in {entry.file} — "
                            f"{entry.quote!r}; remove the entry")
    return problems


def brief_link_problems(site: str, exceptions: list[LinkException] = ()) -> tuple[list[str], int]:
    """Every link to digline/brief in site/'s pages that is not a file, a
    folder or a commit at a full sha: (problems, links read). The repository's
    front page is refused too: it shows main, and a reader sent to it to see the
    project sees whatever main holds today, not what the page was written from.
    A link that is an entry of `exceptions` — its href and its text, both exact
    — passes; an entry no page uses is a problem."""
    problems: list[str] = []
    read = 0
    used: set[LinkException] = set()
    for folder, dirs, names in os.walk(site):
        dirs.sort()
        for name in sorted(n for n in names if n.endswith(".html")):
            relative = os.path.relpath(os.path.join(folder, name), site).replace(os.sep, "/")
            with open(os.path.join(folder, name), encoding="utf-8") as fh:
                page = fh.read()
            texts = {m.start(1): _words(m.group(2)) for m in _ANCHOR.finditer(page)}
            for match in _BRIEF.finditer(page):
                rest = match.group(1)
                read += 1
                if not _PINNED.match(rest):
                    admitted = [e for e in exceptions
                                if e.href == BRIEF + rest and e.text == texts.get(match.start())]
                    if admitted:
                        used.update(admitted)
                        continue
                    where = repr(rest) if rest.strip("/") else "its front page"
                    problems.append(f"{relative}: a link to digline/brief at {where}, and a source is cited at a "
                                    "full commit sha — a tag can be moved, a branch moves by itself, and the "
                                    "front page is main")
    for entry in exceptions:
        if entry not in used:
            problems.append(f"{REGISTER}: link {entry.href!r} shown as {entry.text!r}: no page of the site has it — "
                            "remove the entry")
    return problems, read


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


ASIDE = '<div class="aside">'


def split_aside(body: str, source: str) -> tuple[str, str]:
    """The page's body before its .aside, and the .aside to the end: the template
    sets the quotation between the two. Refused unless there is exactly one."""
    if body.count(ASIDE) != 1:
        raise PluginError(f"sources: {source} has {body.count(ASIDE)} <div class=\"aside\" markdown>, and the "
                          "quotation of rule 1 is set before the one block about the agent under test")
    before, after = body.split(ASIDE, 1)
    return before, ASIDE + after


def on_page_context(context, page, config, nav, **kwargs):
    # After opening.py, which puts the body in the context.
    if _is_page(page) and "body" in context:
        context["body"], context["agents_aside"] = split_aside(context["body"], page.file.src_uri)
    return context


def on_post_build(config, **kwargs):
    path = os.path.join(config["site_dir"], "agents", "index.html")
    if not os.path.isfile(path):
        raise PluginError("sources: site/agents/index.html was not built")
    with open(path, encoding="utf-8") as fh:
        page_html = fh.read()
    rule = load(_rule_path(config))
    problems = []
    # The page and every translation of it: the quotation is the template's, so
    # a translation carries digline's words unchanged, and this says so.
    for relative in [os.path.join("agents", "index.html")] + [
            os.path.join(lang, "agents", "index.html") for lang in languages.LANGUAGES]:
        whole = os.path.join(config["site_dir"], relative)
        if not os.path.isfile(whole):
            continue
        with open(whole, encoding="utf-8") as fh:
            html = fh.read()
        where = relative.replace(os.sep, "/")
        problems += [p.replace("agents/index.html", where, 1) for p in
                     quotation_problems(html, rule) + caption_problems(html, rule)]
    problems += agents_md_link_problems(config["site_dir"], rule["tag"])[0]
    exceptions = load_link_exceptions(os.path.join(ROOT, REGISTER))
    problems += link_exception_problems(ROOT, exceptions)
    problems += brief_link_problems(config["site_dir"], exceptions)[0]
    with open(os.path.join(config["site_dir"], "search", "search_index.json"), encoding="utf-8") as fh:
        problems += search_problems(json.load(fh), page_html)
    if problems:
        raise PluginError("sources: " + "\n".join(problems))


# ── the selftest ─────────────────────────────────────────────────────────────


def selftest() -> int:
    import tempfile

    failures: list[str] = []

    def expect(label, actual, wanted):
        if actual != wanted:
            failures.append(f"{label}: got {actual!r}, wanted {wanted!r}")
        else:
            print(f"sources selftest: {label}")

    def refused(label, call, needle):
        try:
            call()
        except PluginError as error:
            if needle in str(error):
                print(f"sources selftest: refused, as it must — {label}")
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
                "[`operating-digline`](https://github.com/digline/digline/tree/main/plugins/digline/skills/operating-digline)")
    expect("the links to AGENTS.md and the skill lead to the release tag",
           at_tag(markdown, "v0.15.0", PAGE),
           "[`AGENTS.md`](https://github.com/digline/digline/blob/v0.15.0/AGENTS.md) … "
           "[`operating-digline`](https://github.com/digline/digline/tree/v0.15.0/plugins/digline/skills/operating-digline)")
    refused("a page without the link to the skill", lambda: at_tag(markdown.split(" … ")[0], "v0.15.0", PAGE),
            "has no link to https://github.com/digline/digline/tree/main/plugins/digline/skills/operating-digline")

    # The body split at its one .aside, for the quotation to go between.
    expect("the body split before its .aside",
           split_aside('<h2>A</h2><div class="tiles"></div><div class="aside"><h2>B</h2></div>', PAGE),
           ('<h2>A</h2><div class="tiles"></div>', '<div class="aside"><h2>B</h2></div>'))
    refused("a body with no .aside", lambda: split_aside("<h2>A</h2>", PAGE), "has 0 <div")
    refused("a body with two", lambda: split_aside('<div class="aside"></div><div class="aside"></div>', PAGE), "has 2 <div")

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

    # Links to AGENTS.md anywhere on the site: at the tag, and at nothing else.
    with tempfile.TemporaryDirectory() as site:
        os.makedirs(os.path.join(site, "product", "adr"))
        def page_at(path, ref):
            with open(os.path.join(site, path), "w", encoding="utf-8") as fh:
                fh.write(f'<p><a href="https://github.com/digline/digline/blob/{ref}/AGENTS.md">AGENTS.md</a></p>')
        page_at("product/mcp.html", "v0.15.0")
        page_at("product/adr/0011.html", "v0.15.0")
        expect("links to AGENTS.md at the tag, in the copied pages", agents_md_link_problems(site, "v0.15.0"), ([], 2))
        page_at("product/adr/0011.html", "main")
        found, _ = agents_md_link_problems(site, "v0.15.0")
        expect("a link to AGENTS.md at main after the sync: refused",
               (len(found), "product/adr/0011.html: a link to AGENTS.md at main" in found[0]), (1, True))
        page_at("product/adr/0011.html", "v0.14.1")
        expect("a link to AGENTS.md at an older tag: refused",
               "at v0.14.1, and the site documents v0.15.0" in agents_md_link_problems(site, "v0.15.0")[0][0], True)

    # Links to digline/brief: a full commit sha, and nothing else.
    with tempfile.TemporaryDirectory() as site:
        os.makedirs(os.path.join(site, "why"))
        sha = "9507bb06f7dd90a4b6a624dbe77725e50819a02f"
        def brief_page(*refs):
            with open(os.path.join(site, "why", "index.html"), "w", encoding="utf-8") as fh:
                fh.write("".join(f'<a href="{BRIEF}{r}">x</a>' for r in refs))
        brief_page(f"/tree/{sha}", f"/blob/{sha}/fixtures/README.md", f"/blob/{sha}/fixtures/recompute.py",
                   f"/blob/{sha}/README.md#reporthtml", f"/commit/{sha}")
        expect("links to digline/brief at a full sha: a folder, files, an anchor, a commit",
               brief_link_problems(site), ([], 5))
        for label, ref in (("main", "/blob/main/fixtures/README.md"),
                           ("a tag", "/tree/why-2026-09/fixtures"),
                           ("a short sha", f"/blob/{sha[:7]}/fixtures/README.md"),
                           ("a branch", "/tree/why-fixtures/fixtures"),
                           ("its front page", ""),
                           ("its front page, with a slash", "/"),
                           ("its front page, at an anchor", "#readme"),
                           ("a sha with more after it", f"/blob/{sha}0/README.md"),
                           ("its issues", "/issues")):
            brief_page(ref)
            found, _ = brief_link_problems(site)
            expect(f"a link to digline/brief at {label}: refused",
                   (len(found), "and a source is cited at a full commit sha" in (found[0] if found else "")), (1, True))

        # A registered exception: its href and its text, exact, and nothing else.
        nav = LinkException("mkdocs.yml", "- A whole product (digline/brief): https://github.com/digline/brief",
                            BRIEF, "A whole product (digline/brief)", "a pointer to the project", "selftest")
        def page_with(*anchors):
            with open(os.path.join(site, "why", "index.html"), "w", encoding="utf-8") as fh:
                fh.write("".join(anchors))
        nav_html = (f'<li class="md-nav__item">\n  <a href="{BRIEF}" class="md-nav__link">\n'
                    '    <span class="md-ellipsis">\n      A whole product (digline/brief)\n    </span>\n  </a></li>')
        page_with(nav_html, f'<p><a href="{BRIEF}">A whole product (digline/brief)</a></p>')
        expect("the registered front-page link, in the nav and in a line of text, passes",
               brief_link_problems(site, [nav]), ([], 2))
        page_with(nav_html, f'<a href="{BRIEF}">newsletter judge</a>')
        found, _ = brief_link_problems(site, [nav])
        expect("the same href with other text: refused", (len(found), "its front page" in found[0]), (1, True))
        page_with(f'<a href="{BRIEF}/">A whole product (digline/brief)</a>')
        found, _ = brief_link_problems(site, [nav])
        expect("the registered text at another href: refused, and the entry unused",
               (len(found), "its front page" in found[0], "no page of the site has it" in found[1]), (2, True, True))
        page_with(f'<a href="{BRIEF}/tree/{sha}">x</a>')
        found, _ = brief_link_problems(site, [nav])
        expect("an entry no page uses: refused", found and "no page of the site has it" in found[0], True)
        with open(os.path.join(site, "mkdocs.yml"), "w", encoding="utf-8") as fh:
            fh.write("nav:\n  - A whole\n    product (digline/brief): https://github.com/digline/brief\n")
        expect("an entry whose quote is in its file passes", link_exception_problems(site, [nav]), [])
        with open(os.path.join(site, "mkdocs.yml"), "w", encoding="utf-8") as fh:
            fh.write(f"nav:\n  - A whole product (digline/brief): {BRIEF}/tree/{sha}\n")
        found = link_exception_problems(site, [nav])
        expect("an entry whose quote is gone: refused", (len(found), "no longer in mkdocs.yml" in found[0]), (1, True))
        register = os.path.join(site, "register.toml")
        with open(register, "w", encoding="utf-8") as fh:
            fh.write('[[link]]\nfile = "mkdocs.yml"\nquote = "q"\nhref = "h"\ntext = "t"\nsince = "#68"\n')
        try:
            load_link_exceptions(register)
            expect("an entry that does not say why: refused", False, True)
        except PluginError as error:
            expect("an entry that does not say why: refused", "`why` is missing" in str(error), True)

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
        print(f"sources selftest: FAILED — {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        raise SystemExit(selftest())
    print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
    raise SystemExit(2)
