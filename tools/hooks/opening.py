"""The opening band — the reading pages, and four pages of the documentation.

Each of those pages opens the way the home does: a band on the home's ground
(--wash) with the title in the home's title style, an optional kicker above it,
and the first paragraph under it as the lede. The words stay where they are, in
the page's Markdown: `# Title`, then the first paragraph. This hook takes the
rendered page apart at that seam and hands the template three pieces, so no
page has to repeat its title or move its first paragraph into front matter.

    kicker:  `kicker:` in the page's front matter, or nothing
    title:   the inside of the page's first <h1>, its anchor included
    title_id the <h1>'s id, so #why still lands on the title
    lede:    the inside of the first <p> after it
    body:    everything after that paragraph

The template gets `opening` (the first four) and `body`. Two kinds of page get
them:

  * the reading pages, by template — why, start, about, contact — rendered by
    their own file in overrides/ through _shell.html;
  * four documentation pages, by path — the three section indexes Material
    renders (How digline compares, Handbook, Writing) and digline for agents —
    rendered by overrides/main.html, which puts the band in Material's `hero`
    block, above the sidebars, and the body where page.content would be.

A page of either kind whose content does not start with an <h1> and a <p> fails
the build: the band would otherwise be empty, or would swallow the wrong
paragraph. So does a documentation page named below that the build does not
have, or that has a template of its own: a renamed index would otherwise lose
its band without a word.

    usage: tools/hooks/opening.py --selftest
"""

from __future__ import annotations

import re
import sys

from mkdocs.exceptions import PluginError

# The templates that open with the band.
READING = {"why.html", "start.html", "about.html", "contact.html"}

# The documentation pages that open with it, by their path under docs/: pages
# a reader arrives on from the bar or the home, before the documentation
# proper. Every one must be in the build and must be Material's.
DOCS = {"agents.md", "blog/index.md", "comparison/index.md", "handbook/index.md"}

_OPENING = re.compile(
    r"\A\s*<h1(?P<attrs>[^>]*)>(?P<title>.*?)</h1>\s*<p>(?P<lede>.*?)</p>(?P<body>.*)\Z",
    re.S,
)
_ID = re.compile(r'\bid="([^"]*)"')


def split(content: str, source: str) -> tuple[dict, str]:
    match = _OPENING.match(content)
    if not match:
        raise PluginError(
            f"opening: {source} must start with `# Title` and a first paragraph — "
            "they become the page's opening band."
        )
    title_id = _ID.search(match.group("attrs"))
    return {
        "title": match.group("title"),
        "title_id": title_id.group(1) if title_id else None,
        "lede": match.group("lede"),
    }, match.group("body")


def opens(meta: dict, src_uri: str) -> bool:
    """Whether a page opens with the band."""
    return meta.get("template") in READING or src_uri in DOCS


def check_docs(pages: dict[str, dict]) -> None:
    """Every page in DOCS is in the build ({src_uri: meta}), and none of them
    has a template: those are reading pages, and belong in READING."""
    missing = sorted(DOCS - pages.keys())
    if missing:
        raise PluginError(
            f"opening: {', '.join(missing)} named in DOCS but not in the build — "
            "a page that moved takes its entry in tools/hooks/opening.py with it."
        )
    templated = sorted(uri for uri in DOCS if pages[uri].get("template"))
    if templated:
        raise PluginError(
            f"opening: {', '.join(templated)} named in DOCS but rendered by a template "
            "of its own — a reading page goes in READING."
        )


# The documentation pages named in DOCS that this build has rendered, with their
# front matter: filled while the pages are, checked once they all have been.
_seen: dict[str, dict] = {}


def on_pre_build(config, **kwargs):
    _seen.clear()


def on_page_markdown(markdown, page, config, files, **kwargs):
    if page.file.src_uri in DOCS:
        _seen[page.file.src_uri] = dict(page.meta)
    return markdown


def on_post_build(config, **kwargs):
    check_docs(_seen)


def on_page_context(context, page, config, nav, **kwargs):
    if opens(page.meta, page.file.src_uri):
        opening, body = split(page.content or "", page.file.src_uri)
        opening["kicker"] = page.meta.get("kicker")
        context["opening"] = opening
        context["body"] = body
    return context


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
                print(f"opening selftest: refused, as it must — {label}")
            return
        failures.append(f"{label}: accepted, which it exists to refuse")

    # A reading page and a documentation page render the same way: the h1, its
    # permalink and its id, then the first paragraph, then the rest.
    rendered = ('<h1 id="how-digline-compares">How digline compares<a class="headerlink" '
                'href="#how-digline-compares" title="Link to this section">&para;</a></h1>\n'
                '<p>The space is <em>crowded</em>.</p>\n<h2 id="a">A</h2>\n<p>Rest.</p>')
    opening, body = split(rendered, "comparison/index.md")
    expect("title", opening["title"], 'How digline compares<a class="headerlink" '
           'href="#how-digline-compares" title="Link to this section">&para;</a>')
    expect("title_id", opening["title_id"], "how-digline-compares")
    expect("lede", opening["lede"], "The space is <em>crowded</em>.")
    expect("body", body, '\n<h2 id="a">A</h2>\n<p>Rest.</p>')

    # Which pages open with the band.
    expect("reading page by template", opens({"template": "why.html"}, "why.md"), True)
    for uri in sorted(DOCS):
        expect(f"{uri} by path", opens({}, uri), True)
    expect("home", opens({"template": "home.html"}, "index.md"), False)
    expect("a documentation page not named", opens({}, "product/guide.md"), False)
    expect("an index not named", opens({}, "product/adr/index.md"), False)

    # What is refused: a page that does not start with a title and a paragraph,
    # a named page the build does not have, and a named page with a template.
    refused("no h1 first", lambda: split("<p>Lede.</p><h1>T</h1>", "agents.md"),
            "must start with `# Title`")
    refused("a list where the lede should be",
            lambda: split("<h1>T</h1>\n<ul><li>x</li></ul>", "handbook/index.md"),
            "must start with `# Title`")
    everything = {uri: {} for uri in DOCS}
    check_docs(everything)
    refused("a named page missing",
            lambda: check_docs({u: m for u, m in everything.items() if u != "blog/index.md"}),
            "blog/index.md named in DOCS but not in the build")
    refused("a named page with a template",
            lambda: check_docs(everything | {"agents.md": {"template": "why.html"}}),
            "agents.md named in DOCS but rendered by a template")

    for failure in failures:
        print(f"opening selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print(f"opening selftest: split as expected; {len(DOCS)} documentation pages and "
          f"{len(READING)} templates open with the band; refusals refused")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        raise SystemExit(selftest())
    print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
    raise SystemExit(2)
