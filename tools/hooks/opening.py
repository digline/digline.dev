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
    <h1> is followed at once by a <p>, that is the lede — unless the <p> holds
    nothing but one <code> (an image name under a title, say), which labels the
    page rather than opening it; otherwise the band shows the title alone and
    the body keeps everything after it. The build fails only when there is no
    <h1> at all — and when the page is one
    tools/sync-docs.sh copies out of digline/digline, the message says the fix
    belongs there, since anything changed here is overwritten on the next sync.

The title is set in the gradient the home's section titles use, all of it by
default. A page written in this repository may name the part that should be,
with `accent:` in its front matter: that text, exactly as it appears in the
title, is the gradient and the rest stays --ink; a title that does not contain
it fails the build. A page copied from digline/digline has no front matter of
this repository's to carry one, and its title is in the gradient whole. The
text of the title and its id do not change: ``title_html`` wraps what is
there in a span.

Material's own 404 page is not a page to mkdocs and reaches no hook: its band is
set in overrides/404.html.

    usage: tools/hooks/opening.py --selftest
"""

from __future__ import annotations

import os
import re
import sys
import unicodedata
from html import escape as html_escape

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
_ONLY_CODE = re.compile(r"\A(?P<before>[^<]*)<code\b[^>]*>(?P<code>.*?)</code>(?P<after>[^<]*)\Z", re.S)


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


_HEADERLINK = re.compile(r'(?P<text>.*?)(?P<link>\s*<a class="headerlink"[^>]*>.*?</a>)?\s*\Z', re.S)


def title_html(title: str, accent: str | None, source: str) -> str:
    """The title with the gradient on it: a span round all of its text, or,
    with an accent, round that text alone. The permalink Markdown puts at the
    end of a heading stays outside the span. The accent has to appear in the
    title's HTML exactly as written, outside any tag, or the build fails."""
    match = _HEADERLINK.match(title)
    text, link = match.group("text"), match.group("link") or ""
    if not accent:
        return f'<span class="grad-text">{text}</span>{link}'
    literal = html_escape(accent, quote=False)
    start = text.find(literal)
    while start != -1 and text.count("<", 0, start) != text.count(">", 0, start):
        start = text.find(literal, start + 1)
    if start == -1 or "<" in literal:
        plain = re.sub(r"<[^>]*>", "", text)
        raise PluginError(
            f"opening: {source} has accent: {accent!r}, and its title, {plain!r}, does not "
            "contain it as written. The accent is the part of the title in the gradient: "
            "copy it from the title."
        )
    end = start + len(literal)
    return f'{text[:start]}<span class="grad-text">{text[start:end]}</span>{text[end:]}{link}'


def accent_for(meta: dict, src_uri: str, native: set[str]) -> str | None:
    """A page's accent: its front matter's, on a page written here; none on a
    page copied from digline, whose title is in the gradient whole."""
    return None if upstream(src_uri, native) else meta.get("accent")


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


def only_code(paragraph: str) -> bool:
    """Whether a paragraph is a single <code> and, around it, nothing but
    spaces and punctuation: `ghcr.io/digline/digline` under a title."""
    match = _ONLY_CODE.match(paragraph.strip())
    if not match or "<code" in match.group("code"):
        return False
    around = match.group("before") + match.group("after")
    return all(ch.isspace() or unicodedata.category(ch).startswith("P") for ch in around)


def split_docs(content: str, source: str, native: set[str]) -> tuple[dict, str]:
    """A documentation page: the first <h1> is the title, and the <p> right
    after it, if there is one and it is more than a lone <code>, the lede. No
    <h1> fails the build."""
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
    if lede and only_code(lede.group("lede")):
        lede = None
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
    native = native_pages()
    if template in READING:
        opening, body = split(page.content or "", page.file.src_uri)
    elif not template:
        opening, body = split_docs(page.content or "", page.file.src_uri, native)
    else:
        return context
    accent = accent_for(page.meta, page.file.src_uri, native)
    opening["title_html"] = title_html(opening["title"], accent, page.file.src_uri)
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

    # 2b. A title and a paragraph that is only code — the Docker page's image
    #     name: not a lede, and the paragraph stays at the top of the body. A
    #     paragraph with code and words round it is still a lede.
    docker = ('<h1 id="the-official-digline-image">The official digline image</h1>\n'
              '<p><code>ghcr.io/digline/digline</code></p>\n<p>The official image runs any suite.</p>')
    opening, body = split_docs(docker, "product/docker.md", native)
    expect("only code: lede", opening["lede"], None)
    expect("only code: body", body,
           '\n<p><code>ghcr.io/digline/digline</code></p>\n<p>The official image runs any suite.</p>')
    for paragraph in ("<code>pip install digline</code>.", " <code>a</code> — ", "(<code>x</code>)"):
        expect(f"only code: {paragraph!r}", only_code(paragraph), True)
    for paragraph in ("Run <code>digline</code> first.", "<code>a</code> and <code>b</code>",
                      "<code>a</code><em>b</em>", "No code at all."):
        expect(f"not only code: {paragraph!r}", only_code(paragraph), False)
    opening, _ = split_docs(h1 + "<p>Run <code>digline run</code> first.</p>", "product/guide.md", native)
    expect("code among words: lede", opening["lede"], "Run <code>digline run</code> first.")

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

    # 4. The title in the gradient: whole by default, the permalink kept out of
    #    the span; an accent that is in the title, wrapped alone; one that is
    #    not, or that runs across markup, refused.
    expect("whole title", title_html(title, None, "why.md"),
           '<span class="grad-text">How digline compares</span><a class="headerlink" '
           'href="#how-digline-compares" title="Link to this section">&para;</a>')
    expect("accent", title_html(title, "compares", "comparison/index.md"),
           'How digline <span class="grad-text">compares</span><a class="headerlink" '
           'href="#how-digline-compares" title="Link to this section">&para;</a>')
    expect("accent with an ampersand, as the title's HTML writes it",
           title_html("Cases &amp; checks", "& checks", "handbook/02-cases.md"),
           'Cases <span class="grad-text">&amp; checks</span>')
    expect("accent not matched inside a tag's attributes, only in text",
           title_html('<code class="x">x</code> and x', "x", "a.md"),
           '<code class="x"><span class="grad-text">x</span></code> and x')
    expect("a title with no permalink", title_html("404 - Not found", None, "404"),
           '<span class="grad-text">404 - Not found</span>')
    expect("an accent on a page written here", accent_for({"accent": "compares"},
           "comparison/index.md", native), "compares")
    expect("an accent on a product page written here", accent_for({"accent": "loop"},
           "product/operator.md", native), "loop")
    expect("no accent on a page copied from digline", accent_for({"accent": "photograph"},
           "product/guide.md", native), None)
    refused("an accent the title does not contain",
            lambda: title_html(title, "contrasts", "comparison/index.md"),
            "does not contain it as written")
    refused("an accent that runs across markup",
            lambda: title_html("The <code>diff</code> report", "diff report", "a.md"),
            "does not contain it as written")

    # The product pages written here are the ones pages/product/ holds today.
    found = native_pages()
    if not found:
        failures.append("pages/product/ has no page: every product/ page would be called digline's")

    for failure in failures:
        print(f"opening selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("opening selftest: title and lede, title alone, a lone <code> kept out of the band, "
          "the title's gradient whole or on its accent, and no title split or refused as they "
          f"must, on both kinds of page; {len(found)} product pages written here")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        raise SystemExit(selftest())
    print(__doc__.strip().splitlines()[-1].strip(), file=sys.stderr)
    raise SystemExit(2)
