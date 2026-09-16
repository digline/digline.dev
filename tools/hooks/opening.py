"""The opening band — the reading pages, and every page Material renders.

Each of those pages opens the way the home does: a band on the home's ground
(--wash) with the title in the home's title style, an optional kicker above it,
and the first paragraph under it as the lede. The words stay where they are, in
the page's Markdown: `# Title`, then the first paragraph. This hook takes the
rendered page apart at that seam and hands the template three pieces, so no
page has to repeat its title or move its first paragraph into front matter.

    kicker:  `kicker:` in the page's front matter, or nothing
    title:   the inside of the page's first <h1>, its anchor included
    title_id the <h1>'s id, so #why still lands on the title
    lede:    the inside of the <p> that follows the <h1> at once, or None
    body:    everything else, in order

The template gets `opening` (the first four) and `body`. Two kinds of page get
them, and they are held to different rules:

  * the reading pages, by template — why, start, about, contact — rendered by
    their own file in overrides/ through _shell.html. Their layout is built
    round a lede, so each must start with an <h1> and a paragraph, or the
    build fails.
  * every page without a template of its own — the documentation Material
    renders, from agents to the ADRs — through overrides/main.html, which puts
    the band in Material's `hero` block above the sidebars and the body where
    page.content would be. These are written to be read on GitHub as well, and
    many do not open on a paragraph (an ADR opens on its status list): when the
    <h1> is followed at once by a <p>, that is the lede; otherwise the band
    shows the title alone and the body keeps everything after it. The build
    fails only when there is no <h1> at all — and when the page is one
    tools/sync-docs.sh copies out of digline/digline, the message says the fix
    belongs there, since anything changed here is overwritten on the next sync.

Material's own 404 page is not a page to mkdocs and reaches no hook: its band is
set in overrides/404.html.

    usage: tools/hooks/opening.py --selftest
"""

from __future__ import annotations

import os
import re
import sys

from mkdocs.exceptions import PluginError

# The templates that open with the band and are built round a lede.
READING = {"why.html", "start.html", "about.html", "contact.html"}

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_READING = re.compile(
    r"\A\s*<h1(?P<attrs>[^>]*)>(?P<title>.*?)</h1>\s*<p>(?P<lede>.*?)</p>(?P<body>.*)\Z",
    re.S,
)
_H1 = re.compile(r"<h1(?P<attrs>[^>]*)>(?P<title>.*?)</h1>", re.S)
_LEDE = re.compile(r"\A\s*<p>(?P<lede>.*?)</p>", re.S)
_ID = re.compile(r'\bid="([^"]*)"')


def _title_id(attrs: str) -> str | None:
    found = _ID.search(attrs)
    return found.group(1) if found else None


def split(content: str, source: str) -> tuple[dict, str]:
    """A reading page: an <h1> and a paragraph, first, or the build fails."""
    match = _READING.match(content)
    if not match:
        raise PluginError(
            f"opening: {source} must start with `# Title` and a first paragraph — "
            "they become the page's opening band."
        )
    return {
        "title": match.group("title"),
        "title_id": _title_id(match.group("attrs")),
        "lede": match.group("lede"),
    }, match.group("body")


def upstream(src_uri: str, native: set[str]) -> str | None:
    """Where in digline/digline a page under product/ comes from — the file to
    fix — or None for a page written in this repository. `native` is the
    pages/product/ files that sync-docs.sh installs from here."""
    if not src_uri.startswith("product/"):
        return None
    rest = src_uri[len("product/"):]
    if rest in native:
        return None
    if rest == "changelog.md":
        return "CHANGELOG.md"
    if rest == "roadmap.md":
        return "ROADMAP.md"
    if rest == "docker.md":
        return "docker/README.md"
    if rest == "adr/index.md":
        return "docs/adr/ (tools/sync-docs.sh writes the index from the records' titles)"
    if rest.startswith("examples/"):
        return f"examples/{rest[len('examples/'):-len('.md')]}/README.md"
    return f"docs/{rest}"


def split_docs(content: str, source: str, native: set[str]) -> tuple[dict, str]:
    """A documentation page: the first <h1> is the title, and the <p> right
    after it, if there is one, the lede. No <h1> fails the build."""
    match = _H1.search(content)
    if not match:
        origin = upstream(source, native)
        where = (" The page is copied from digline/digline by tools/sync-docs.sh, so the "
                 f"fix belongs there, in {origin}: an edit here is overwritten on the next sync."
                 if origin else "")
        raise PluginError(
            f"opening: {source} has no `# Title` — every page opens on its <h1>, which "
            f"becomes the title of its opening band.{where}"
        )
    before, after = content[:match.start()], content[match.end():]
    lede = _LEDE.match(after)
    body = before + (after[lede.end():] if lede else after)
    return {
        "title": match.group("title"),
        "title_id": _title_id(match.group("attrs")),
        "lede": lede.group("lede") if lede else None,
    }, body


def native_pages() -> set[str]:
    """The product/ pages written in this repository, under pages/product/."""
    folder = os.path.join(ROOT, "pages", "product")
    if not os.path.isdir(folder):
        return set()
    return {name for name in os.listdir(folder) if name.endswith(".md")}


def on_page_context(context, page, config, nav, **kwargs):
    template = page.meta.get("template")
    if template in READING:
        opening, body = split(page.content or "", page.file.src_uri)
    elif not template:
        opening, body = split_docs(page.content or "", page.file.src_uri, native_pages())
    else:
        return context
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

    def refused(label, call, needle, absent=None):
        try:
            call()
        except PluginError as error:
            message = str(error)
            if needle not in message:
                failures.append(f"{label}: refused, but not for this: {message}")
            elif absent and absent in message:
                failures.append(f"{label}: refused, but the message says {absent!r}: {message}")
            else:
                print(f"opening selftest: refused, as it must — {label}")
            return
        failures.append(f"{label}: accepted, which it exists to refuse")

    h1 = ('<h1 id="how-digline-compares">How digline compares<a class="headerlink" '
          'href="#how-digline-compares" title="Link to this section">&para;</a></h1>\n')
    title = ('How digline compares<a class="headerlink" href="#how-digline-compares" '
             'title="Link to this section">&para;</a>')
    native = {"operator.md", "security.md"}

    # 1. A title and a paragraph: the paragraph is the lede, and leaves the body.
    content = h1 + '<p>The space is <em>crowded</em>.</p>\n<h2 id="a">A</h2>\n<p>Rest.</p>'
    for label, (opening, body) in (
        ("reading page", split(content, "why.md")),
        ("documentation page", split_docs(content, "comparison/index.md", native)),
    ):
        expect(f"{label}: title", opening["title"], title)
        expect(f"{label}: title_id", opening["title_id"], "how-digline-compares")
        expect(f"{label}: lede", opening["lede"], "The space is <em>crowded</em>.")
        expect(f"{label}: body", body, '\n<h2 id="a">A</h2>\n<p>Rest.</p>')

    # 2. A title and no paragraph right after it — an ADR's status list: the
    #    title alone, and the body keeps everything after it, its first <p>
    #    included. A reading page in that shape is still refused.
    adr = ('<h1 id="adr-0024-the-judge-as-an-instrument">ADR 0024 — The judge</h1>\n'
           '<ul>\n<li>Status: proposed</li>\n</ul>\n<p>First paragraph.</p>')
    opening, body = split_docs(adr, "product/adr/0024-the-judge-as-an-instrument.md", native)
    expect("title only: title", opening["title"], "ADR 0024 — The judge")
    expect("title only: title_id", opening["title_id"], "adr-0024-the-judge-as-an-instrument")
    expect("title only: lede", opening["lede"], None)
    expect("title only: body", body,
           '\n<ul>\n<li>Status: proposed</li>\n</ul>\n<p>First paragraph.</p>')
    refused("title only, on a reading page", lambda: split(adr, "start.md"),
            "must start with `# Title` and a first paragraph")

    # 3. No <h1>: refused; a page copied from digline says where to fix it, and
    #    a page written here does not send anyone to digline.
    no_h1 = "<p>Only a paragraph.</p>\n<h2>A</h2>"
    refused("no h1, a copied reference page",
            lambda: split_docs(no_h1, "product/guide.md", native),
            "fix belongs there, in docs/guide.md")
    refused("no h1, a copied example",
            lambda: split_docs(no_h1, "product/examples/rag.md", native),
            "in examples/rag/README.md")
    refused("no h1, the copied changelog",
            lambda: split_docs(no_h1, "product/changelog.md", native),
            "in CHANGELOG.md")
    refused("no h1, a product page written here",
            lambda: split_docs(no_h1, "product/operator.md", native),
            "has no `# Title`", absent="digline/digline")
    refused("no h1, a page written here",
            lambda: split_docs(no_h1, "handbook/index.md", native),
            "has no `# Title`", absent="digline/digline")

    # The product pages written here are the ones pages/product/ holds today.
    found = native_pages()
    if not found:
        failures.append("pages/product/ has no page: every product/ page would be called digline's")

    for failure in failures:
        print(f"opening selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("opening selftest: title and lede, title alone and no title split or refused as they "
          f"must, on both kinds of page; {len(found)} product pages written here")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        raise SystemExit(selftest())
    print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
    raise SystemExit(2)
