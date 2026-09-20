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

  * the reading pages, by template — why, start, about, contact, agents — rendered by
    their own file in overrides/ through _shell.html. Their layout is built
    round a lede, so each must start with an <h1> and a paragraph, or the
    build fails.
  * every page without a template of its own — the documentation Material
    renders, from the comparison to the ADRs — through overrides/main.html, which puts
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
READING = {"why.html", "start.html", "about.html", "contact.html", "agents.html"}

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#: An HTML comment between the title and the paragraph. It renders as nothing,
#: so the paragraph still *visually* follows the title — but it used to break
#: both patterns below, which look for the <p> immediately after the <h1>, and
#: the page silently lost its opening band. That is how the comparison index
#: lost its lede: a comment carrying an editorial rule was put under the `# H1`
#: and `make build` stayed green, because a documentation page is allowed to
#: have none. Skipped here rather than gated, and kept in the body so nothing
#: that reads a marker comment out of the built page loses it.
_COMMENTS = r"(?P<comments>(?:\s*<!--.*?-->)*)"

_READING = re.compile(
    r"\A\s*<h1(?P<attrs>[^>]*)>(?P<title>.*?)</h1>" + _COMMENTS +
    r"\s*<p>(?P<lede>.*?)</p>(?P<body>.*)\Z",
    re.S,
)
_H1 = re.compile(r"<h1(?P<attrs>[^>]*)>(?P<title>.*?)</h1>", re.S)
_LEDE = re.compile(r"\A" + _COMMENTS + r"\s*<p>(?P<lede>.*?)</p>", re.S)
_ID = re.compile(r'\bid="([^"]*)"')
_ONLY_CODE = re.compile(r"\A(?P<before>[^<]*)<code\b[^>]*>(?P<code>.*?)</code>(?P<after>[^<]*)\Z", re.S)
_ONLY_IMG = re.compile(r"\A(?P<before>[^<]*)<img\b[^>]*>(?P<after>[^<]*)\Z", re.S)


def _title_id(attrs: str) -> str | None:
    found = _ID.search(attrs)
    return found.group(1) if found else None


def split(content: str, source: str) -> tuple[dict, str]:
    """A reading page: an <h1> and a paragraph, first, or the build fails."""
    match = _READING.match(content)
    # A paragraph that only labels the page is not a first paragraph: the
    # layout of a reading page is built round a line of prose, and a lone
    # <code> or <img> in the band is markup where a sentence should be. A
    # documentation page is allowed to have none; these five are not.
    if match and labels_only(match.group("lede")):
        match = None
    if not match:
        raise PluginError(
            f"opening: {source} must start with `# Title` and a first paragraph — "
            "they become the page's opening band."
        )
    return {
        "title": match.group("title"),
        "title_id": _title_id(match.group("attrs")),
        "lede": match.group("lede"),
    }, match.group("comments") + match.group("body")


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
        return "docs/adr/ (tools/sync-docs.sh writes the index, tools/hooks/indexes.py its table)"
    if rest.startswith("examples/"):
        return f"examples/{rest[len('examples/'):-len('.md')]}/README.md"
    return f"docs/{rest}"


def _bare(before: str, after: str) -> bool:
    """Nothing around the tag but spaces and punctuation."""
    return all(
        ch.isspace() or unicodedata.category(ch).startswith("P")
        for ch in before + after
    )


def labels_only(paragraph: str) -> bool:
    """Whether a paragraph labels the page rather than opening it.

    Two shapes, and around either of them nothing but spaces and punctuation:
    a single <code>, which is `ghcr.io/digline/digline` under the Docker
    page's title; and a single <img>, which is a screenshot carrying a caption
    and not a sentence. Either one in the band would put markup where the
    layout expects a line of prose.
    """
    stripped = paragraph.strip()
    code = _ONLY_CODE.match(stripped)
    if code and "<code" not in code.group("code"):
        if _bare(code.group("before"), code.group("after")):
            return True
    image = _ONLY_IMG.match(stripped)
    if image and _bare(image.group("before"), image.group("after")):
        return True
    return False


def split_docs(content: str, source: str, native: set[str]) -> tuple[dict, str]:
    """A documentation page: the first <h1> is the title, and the <p> right
    after it, if there is one and it is more than a lone <code> or <img>, the
    lede. No
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
    if lede and labels_only(lede.group("lede")):
        lede = None
    # A comment in the seam stays in the body rather than being eaten with the
    # lede: it is invisible either way, and dropping it would quietly delete
    # something an author wrote.
    kept = lede.group("comments") if lede else ""
    body = before + kept + (after[lede.end():] if lede else after)
    return {
        "title": match.group("title"),
        "title_id": _title_id(match.group("attrs")),
        "lede": lede.group("lede") if lede else None,
    }, body


def native_pages() -> set[str]:
    """The product/ pages written in this repository, under pages/product/, by
    their path there: `operator.md`, `examples/index.md`."""
    folder = os.path.join(ROOT, "pages", "product")
    return {
        os.path.relpath(os.path.join(dirpath, name), folder).replace(os.sep, "/")
        for dirpath, _, names in os.walk(folder)
        for name in names
        if name.endswith(".md")
    }


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
    native = {"operator.md", "security.md", "examples/index.md"}

    # 0. Every template that lays out a reading page — it extends _shell.html
    #    and opens with the band — is in READING, and nothing else is: a
    #    template left out would get no band and no body, and render empty.
    overrides = os.path.join(ROOT, "overrides")
    laid_out = set()
    for name in sorted(os.listdir(overrides)):
        if name.endswith(".html"):
            with open(os.path.join(overrides, name), encoding="utf-8") as fh:
                text = fh.read()
            if '{% extends "_shell.html" %}' in text and 'include "partials/opening.html"' in text:
                laid_out.add(name)
    expect("READING is every template that extends _shell.html and opens with the band", READING, laid_out)
    expect("agents.html is a reading page", "agents.html" in READING, True)

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

    # 2a. A comment in the seam between the title and the paragraph. It
    #     renders as nothing, so the paragraph still opens the page and is
    #     still the lede — and the comment stays in the body rather than being
    #     eaten with it. This is the regression the comparison index paid for:
    #     an editorial rule written under the `# H1` and a band that went
    #     silently empty, with `make build` green throughout.
    commented = (h1 + "<!-- naming: a rule about this page -->\n"
                 '<p>The space is <em>crowded</em>.</p>\n<h2 id="a">A</h2>')
    for label, (opening, body) in (
        ("reading page", split(commented, "why.md")),
        ("documentation page", split_docs(commented, "comparison/index.md", native)),
    ):
        expect(f"{label}: a comment in the seam leaves the lede",
               opening["lede"], "The space is <em>crowded</em>.")
        expect(f"{label}: the comment is kept in the body",
               "<!-- naming: a rule about this page -->" in body, True)

    #     And what a comment must *not* do is make a lede out of something that
    #     is not one: after it, a list, a code block or an image is still the
    #     body, and the page still opens on its title alone.
    for shape, markup in (
        ("a list", "<ul>\n<li>Status: proposed</li>\n</ul>"),
        ("a code block", '<div class="highlight"><pre>digline view</pre></div>'),
        ("an image", '<p><img alt="" src="x.png"></p>'),
    ):
        content = h1 + "<!-- a comment -->\n" + markup + "\n<p>Later.</p>"
        opening, body = split_docs(content, "product/view.md", native)
        expect(f"a comment then {shape} is not a lede", opening["lede"], None)
        expect(f"a comment then {shape} leaves the markup in the body",
               markup in body, True)
        refused(f"a comment then {shape}, on a reading page",
                lambda c=content: split(c, "start.md"),
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
        expect(f"labels only: {paragraph!r}", labels_only(paragraph), True)
    for paragraph in ("Run <code>digline</code> first.", "<code>a</code> and <code>b</code>",
                      "<code>a</code><em>b</em>", "No code at all."):
        expect(f"not a label: {paragraph!r}", labels_only(paragraph), False)
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
    refused("no h1, a product index written here",
            lambda: split_docs(no_h1, "product/examples/index.md", native),
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
