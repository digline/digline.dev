"""Which characters the presentation pages draw in IBM Plex, and whether the
woff2 files have a glyph for each.

The presentation pages draw their body in IBM Plex Sans and IBM Plex Mono,
served from assets/fonts/ as subsets. A character outside a subset is not an
error a browser reports: it draws that one glyph in the system face. Two tools
share what is here:

  * tools/subset-fonts.py cuts the subsets from the characters counted here;
  * tools/check-glyphs.py fails the build when a page shows a character its
    face has no glyph for.

A presentation page is any page whose <main> carries `dg-page`: that class is
what puts --sans-page on the text, in pages.css. Which face draws a piece of
text is decided by the stylesheets, not by a list here: every rule in pages.css
and in the page's own <style> blocks that sets `font-family` or `font` is read,
and the nearest element one of them matches decides. A rule naming --sans-page
or --mono-page means Plex; any other family (--mono or --sans, say) means a
system face, whose text is not counted.
"""

from __future__ import annotations

import os
import re
from html.parser import HTMLParser

# Always in the subsets, whatever the pages say today: printable ASCII, and the
# punctuation prose and digline's output reach for. A new sentence that uses
# only these needs no new cut.
BASE = {chr(c) for c in range(0x20, 0x7F)} | set("–—‘’“”…·→−×•")

# Text a page shows that is in no HTML, by the class of the element that shows
# it: `content: "$ "` on .install__cmd::before, the step counters of .steps li,
# and the Copy / Copied label the home's script adds beside each .install.
GENERATED = {
    "install__cmd": ("mono", set("$")),
    "steps": ("sans", set("123")),
    "install": ("sans", set("CopyCopied")),
}

FAMILIES = ("sans", "mono")
_PLEX_VARS = {"--sans-page": "sans", "--mono-page": "mono"}
_PLEX_NAMES = {"IBM Plex Sans": "sans", "IBM Plex Mono": "mono"}
_COMPOUND = re.compile(r"^([a-z][a-z0-9]*)?((?:\.[\w-]+)*)$")
_STYLE = re.compile(r"<style[^>]*>(.*?)</style>", re.S | re.I)
_MAIN = re.compile(r"<main\b[^>]*\bclass=\"[^\"]*\bdg-page\b", re.I)
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
    """(weight, woff2 path) for each Plex family, from pages.css's @font-face."""
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


def face_rules(css_text: str) -> list[tuple[list[tuple[str, set[str]]], str | None]]:
    """(selector as compounds, "sans" | "mono" | None) for every rule that
    sets a font family, in source order; None is a face that is not Plex.
    Pseudo-classes, pseudo-elements and combinators other than the descendant
    one are left out: the generated text is GENERATED."""
    import tinycss2

    rules = []
    for rule in _qualified_rules(css_text):
        family, sets_family = None, False
        for d in _declarations(rule.content):
            if d.lower_name in ("font", "font-family"):
                sets_family = True
                value = tinycss2.serialize(d.value)
                family = next((f for var, f in _PLEX_VARS.items() if var in value), None)
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


# ── the pages ────────────────────────────────────────────────────────────────


def is_presentation_page(html: str) -> bool:
    return bool(_MAIN.search(html))


def presentation_pages(site: str) -> list[str]:
    """Every HTML file in the build whose <main> is a .dg-page, sorted."""
    pages = []
    for folder, _, files in os.walk(site):
        for name in files:
            if name.endswith(".html"):
                path = os.path.join(folder, name)
                with open(path, encoding="utf-8") as fh:
                    if is_presentation_page(fh.read()):
                        pages.append(path)
    return sorted(pages)


def plex_text(html: str, pages_css: str) -> dict[str, set[str]]:
    """The characters of the text inside <main class="dg-page">, by the Plex
    face that draws them, GENERATED included where its element is. Markup,
    attributes, <script> and <style> are not text; text in a system face is
    not counted."""
    rules = face_rules(pages_css)
    for block in _STYLE.findall(html):
        rules += face_rules(block)
    found: dict[str, set[str]] = {f: set() for f in FAMILIES}

    class Reader(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.chain: list[tuple[str, set[str]]] = []

        def handle_starttag(self, tag, attrs):
            if tag in _VOID:
                return
            classes = set((dict(attrs).get("class") or "").split())
            self.chain.append((tag, classes))
            if any(t == "main" and "dg-page" in c for t, c in self.chain):
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
            if "script" in tags or "style" in tags:
                return
            if not any(t == "main" and "dg-page" in c for t, c in self.chain):
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
