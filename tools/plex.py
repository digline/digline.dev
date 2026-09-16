"""Which characters the pages draw in IBM Plex, and whether the woff2 files have
a glyph for each.

Every page on the site draws its text in IBM Plex Sans and IBM Plex Mono, served
from assets/fonts/ as subsets declared in assets/fonts.css. A character outside
a subset is not an error a browser reports: it draws that one glyph in the
system face. Two tools share what is here:

  * tools/subset-fonts.py cuts the subsets from BASE, RANGES and the characters
    counted here;
  * tools/check-glyphs.py fails the build when a page shows a character its
    face has no glyph for, NO_PLEX_GLYPH aside.

There are two kinds of page, and they are read the same way over different
stylesheets:

  * a presentation page — its <main> carries `dg-page` — is read inside that
    <main>, over pages.css and the page's own <style> blocks: that class is
    what puts --sans-page on the text;
  * a documentation page — Material's, its <body> carries
    `data-md-color-scheme` — is read inside <body>, over Material's own
    stylesheet from the build, then chrome.css and theme.css, in the order the
    page loads them. Material names its faces through --md-text-font-family and
    --md-code-font-family; theme.css sets those to --sans-page and --mono-page,
    and a custom property set to a Plex variable counts as that variable.

Which face draws a piece of text is decided by the stylesheets, not by a list
here: every rule that sets `font-family` or `font` is read, and the nearest
element one of them matches decides, the later rule winning at the same
element. A rule naming Plex means Plex; any other family (--sans on the bar and
the band, say) means a system face, whose text is not counted. `inherit` sets
nothing.
"""

from __future__ import annotations

import glob
import os
import re
from html.parser import HTMLParser

# Always in the subsets, whatever the pages say today: printable ASCII, and the
# punctuation prose and digline's output reach for. A new sentence that uses
# only these needs no new cut.
BASE = {chr(c) for c in range(0x20, 0x7F)} | set("–—‘’“”…·→−×•")


def _span(first: int, last: int) -> set[str]:
    return {chr(c) for c in range(first, last + 1)}


# Also always in the subsets: whole blocks a page can reach for without anyone
# thinking of it as a new character — Latin-1 (accents, §, «»), the rest of
# General Punctuation, the vulgar fractions, the arrows, the mathematical
# operators (≈ ≥), and in Mono the box drawing a tree printed in a code block
# is made of. A code point in these that Plex does not have is simply not cut
# in; it matters only if a page shows it, and then NO_PLEX_GLYPH decides.
RANGES = {
    "sans": (_span(0x00A0, 0x00FF) | _span(0x2010, 0x202F) | _span(0x2150, 0x215F)
             | _span(0x2190, 0x219F) | _span(0x2200, 0x226F)),
    "mono": (_span(0x00A0, 0x00FF) | _span(0x2010, 0x202F) | _span(0x2150, 0x215F)
             | _span(0x2190, 0x219F) | _span(0x2200, 0x226F) | _span(0x2500, 0x257F)),
}

# Characters IBM Plex itself has no glyph for — not in the subsets, and not in
# the complete fonts they are cut from (tools/subset-fonts.py, SOURCES) — which
# a page may show anyway: the browser draws each in the system face, from the
# fallbacks after Plex in --sans-page and --mono-page (tokens.css). Nothing
# better can be served, so the glyph check lets these through; subset-fonts.py
# refuses to cut when one of them turns out to be in the complete font after
# all, or when a page shows a character missing from it that is not listed.
#
#   ∧ U+2227 LOGICAL AND — in neither family. ADR 0009's table of boundary
#     operators writes `<=` ∧ `<=`, in text.
#   U+2500–257F, box drawing — Plex Mono has the whole block, Plex Sans none of
#     it. The trees in the documentation are in code blocks, in Mono; one drawn
#     in running text (none today) would show its lines in the system face.
NO_PLEX_GLYPH = {
    "sans": {"∧"} | _span(0x2500, 0x257F),
    "mono": {"∧"},
}

# Text a presentation page shows that is in no HTML, by the class of the element
# that shows it: `content: "$ "` on .install__cmd::before, the step counters of
# .steps li, and the Copy / Copied label the closing band's script adds beside
# each .install.
GENERATED = {
    "install__cmd": ("mono", set("$")),
    "steps": ("sans", set("123")),
    "install": ("sans", set("CopyCopied")),
}

FAMILIES = ("sans", "mono")
KINDS = ("presentation", "documentation")
FONTS_CSS = "fonts.css"
_PLEX_VARS = {"--sans-page": "sans", "--mono-page": "mono"}
_PLEX_NAMES = {"IBM Plex Sans": "sans", "IBM Plex Mono": "mono"}
_VAR = re.compile(r"var\(\s*(--[\w-]+)")
_COMPOUND = re.compile(r"^([a-z][a-z0-9]*)?((?:\.[\w-]+)*)$")
_STYLE = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
_MAIN = re.compile(r"<main\b[^>]*\bclass=\"[^\"]*\bdg-page\b", re.I)
_MATERIAL = re.compile(r"<body\b[^>]*\bdata-md-color-scheme=", re.I)
_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
         "meta", "source", "track", "wbr"}


# ── the stylesheets ──────────────────────────────────────────────────────────


def _declarations(content) -> list:
    import tinycss2

    return [d for d in tinycss2.parse_blocks_contents(content, skip_comments=True,
                                                      skip_whitespace=True)
            if d.type == "declaration"]


def _qualified_rules(css_text: str):
    """Every qualified rule in a stylesheet, @media contents included."""
    import tinycss2

    def walk(nodes):
        for node in nodes:
            if node.type == "qualified-rule":
                yield node
            elif node.type == "at-rule" and node.lower_at_keyword == "media" and node.content:
                yield from walk(tinycss2.parse_rule_list(node.content, skip_comments=True,
                                                         skip_whitespace=True))

    return walk(tinycss2.parse_stylesheet(css_text, skip_comments=True, skip_whitespace=True))


def font_faces(css_path: str) -> dict[str, list[tuple[str, str]]]:
    """(weight, woff2 path) for each Plex family, from fonts.css's @font-face."""
    import tinycss2

    with open(css_path, encoding="utf-8") as fh:
        css_text = fh.read()
    faces: dict[str, list[tuple[str, str]]] = {f: [] for f in FAMILIES}
    for node in tinycss2.parse_stylesheet(css_text, skip_comments=True, skip_whitespace=True):
        if node.type != "at-rule" or node.lower_at_keyword != "font-face":
            continue
        values = {d.lower_name: tinycss2.serialize(d.value).strip()
                  for d in _declarations(node.content)}
        family = _PLEX_NAMES.get(values.get("font-family", "").strip("\"'"))
        url = re.search(r"url\(\s*[\"']?([^\"')]+)", values.get("src", ""))
        if family and url:
            path = os.path.normpath(os.path.join(os.path.dirname(css_path), url.group(1)))
            faces[family].append((values.get("font-weight", "400"), path))
    return faces


def face_rules(*css_texts: str) -> list[tuple[list[tuple[str, set[str]]], str | None]]:
    """(selector as compounds, "sans" | "mono" | None) for every rule that
    sets a font family, in source order across the stylesheets given, which
    are read in the order a page loads them; None is a face that is not Plex.
    A custom property whose value names a Plex variable counts as that
    variable wherever it is used, as in a browser, where a variable is
    resolved when the page is laid out and not where it is written; its last
    declaration in the stylesheets wins. Pseudo-classes, pseudo-elements,
    attribute selectors and combinators other than the descendant one are left
    out: the generated text is GENERATED."""
    import tinycss2

    declared: dict[str, str] = {}
    for css_text in css_texts:
        for rule in _qualified_rules(css_text):
            for d in _declarations(rule.content):
                if d.name.startswith("--"):
                    declared[d.name] = tinycss2.serialize(d.value)
    aliases = dict(_PLEX_VARS)
    for _ in range(len(declared)):
        before = dict(aliases)
        for name, value in declared.items():
            if name not in _PLEX_VARS:
                aliases[name] = next((aliases[v] for v in _VAR.findall(value)
                                      if aliases.get(v)), None)
        if aliases == before:
            break

    rules = []
    for css_text in css_texts:
        for rule in _qualified_rules(css_text):
            family, sets_family = None, False
            for d in _declarations(rule.content):
                value = tinycss2.serialize(d.value)
                if d.name.startswith("--"):
                    continue
                if d.lower_name in ("font", "font-family") and value.strip() != "inherit":
                    sets_family = True
                    family = next((aliases[v] for v in _VAR.findall(value) if aliases.get(v)),
                                  None)
            if not sets_family:
                continue
            for selector in tinycss2.serialize(rule.prelude).split(","):
                compounds = []
                for part in selector.split():
                    match = _COMPOUND.match(part)
                    if not match:
                        compounds = []
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


def stylesheets(assets: str, kind: str) -> list[str]:
    """The stylesheets that decide the faces on a page of this kind, from the
    assets folder of a build, in the order the page loads them."""
    if kind == "presentation":
        names = [os.path.join(assets, "pages.css")]
    else:
        material = sorted(glob.glob(os.path.join(assets, "stylesheets", "main.*.min.css")))
        if not material:
            raise FileNotFoundError(f"no Material stylesheet in {assets}/stylesheets/")
        names = [material[-1], os.path.join(assets, "chrome.css"),
                 os.path.join(assets, "theme.css")]
    texts = []
    for name in names:
        with open(name, encoding="utf-8") as fh:
            texts.append(fh.read())
    return texts


# ── the pages ────────────────────────────────────────────────────────────────


def page_kind(html: str) -> str | None:
    """"presentation", "documentation", or None for a file that is neither."""
    if _MAIN.search(html):
        return "presentation"
    if _MATERIAL.search(html):
        return "documentation"
    return None


def site_pages(site: str) -> list[tuple[str, str]]:
    """(path, kind) for every page in the build, sorted by path."""
    pages = []
    for folder, _, files in os.walk(site):
        for name in files:
            if name.endswith(".html"):
                path = os.path.join(folder, name)
                with open(path, encoding="utf-8") as fh:
                    kind = page_kind(fh.read())
                if kind:
                    pages.append((path, kind))
    return sorted(pages)


def plex_text(html: str, css_texts: list[str], kind: str) -> dict[str, set[str]]:
    """The characters of the text a page draws in each Plex face: inside
    <main class="dg-page"> on a presentation page, GENERATED included where its
    element is; inside <body> on a documentation page. Markup, attributes,
    <script> and <style> are not text; text in a system face is not counted."""
    blocks = _STYLE.findall(html) if kind == "presentation" else []
    rules = face_rules(*css_texts, *blocks)
    found: dict[str, set[str]] = {f: set() for f in FAMILIES}

    def inside(chain) -> bool:
        if kind == "presentation":
            return any(t == "main" and "dg-page" in c for t, c in chain)
        return any(t == "body" for t, _ in chain)

    class Reader(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.chain: list[tuple[str, set[str]]] = []

        def handle_starttag(self, tag, attrs):
            if tag in _VOID:
                return
            classes = set((dict(attrs).get("class") or "").split())
            self.chain.append((tag, classes))
            if kind == "presentation" and inside(self.chain):
                for name in classes & GENERATED.keys():
                    family, chars = GENERATED[name]
                    found[family] |= chars

        def handle_endtag(self, tag):
            for i in range(len(self.chain) - 1, -1, -1):
                if self.chain[i][0] == tag:
                    del self.chain[i:]
                    return

        def handle_data(self, data):
            tags = [e[0] for e in self.chain]
            if "script" in tags or "style" in tags or not inside(self.chain):
                return
            for depth in range(len(self.chain), 0, -1):
                picked = [f for compounds, f in rules if _matches(compounds, self.chain[:depth])]
                if picked:
                    if picked[-1]:
                        found[picked[-1]].update(ch for ch in data if not ch.isspace())
                    return

    reader = Reader()
    reader.feed(html)
    reader.close()
    return found


def json_strings(value) -> set[str]:
    """Every character of every string value in a JSON document."""
    if isinstance(value, str):
        return {ch for ch in value if not ch.isspace()}
    if isinstance(value, dict):
        value = list(value.values())
    if isinstance(value, list):
        return set().union(set(), *(json_strings(v) for v in value))
    return set()


# ── the fonts ────────────────────────────────────────────────────────────────


def glyph_gaps(css_path: str, chars: dict[str, set[str]]) -> list[tuple[str, list[str]]]:
    """(woff2 path, characters it has no glyph for) for each face short of one."""
    from fontTools.ttLib import TTFont

    gaps = []
    for family, faces in font_faces(css_path).items():
        if not faces:
            gaps.append((f"@font-face for Plex {family}", sorted(chars[family])))
        for _, path in faces:
            cmap = TTFont(path).getBestCmap()
            missing = sorted(ch for ch in chars[family] if ord(ch) not in cmap)
            if missing:
                gaps.append((path, missing))
    return gaps


def describe(chars) -> str:
    return " ".join(f"{ch!r} U+{ord(ch):04X}" for ch in chars)
