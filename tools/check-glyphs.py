#!/usr/bin/env -S uv run python
"""Every character a page shows in IBM Plex has a glyph there.

Plex is served as subsets, cut by tools/subset-fonts.py. A browser that meets a
character outside a subset draws it in the system face and says nothing, so
this reads the build instead: every page in site/ — the presentation pages,
whose <main> is a .dg-page, and the documentation Material renders — the text
each Plex face draws on it, prose in Sans and code in Mono (tools/plex.py), and
the cmap of every woff2 site/assets/fonts.css declares. One character short
fails, naming the page, the file and the character, and saying how to cut the
subsets again.

The characters Plex itself has no glyph for, in NO_PLEX_GLYPH in tools/plex.py,
are let through: the browser draws them in the system face, and nothing better
can be served. One of them that a subset turns out to have is refused as well —
the list would no longer say what is true.

    usage: tools/check-glyphs.py site
           tools/check-glyphs.py --selftest

--selftest needs no build: it writes a four-page site with the fonts and the
stylesheets in docs/assets/ and Material's own stylesheet. A clean presentation
page and a clean documentation page must pass, the second with the characters
of NO_PLEX_GLYPH in its prose and its code; the same two pages with ✱ (U+2731)
in their Sans and their Mono text must be refused in all six faces each. The
clean pages must count text in both faces, so a reader that stopped seeing a
kind of page would fail rather than pass by counting nothing.
"""

from __future__ import annotations

import glob
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import plex  # noqa: E402

HOW = """\
glyphs: to cut the subsets again —
glyphs:     make docs
glyphs:     uv run tools/subset-fonts.py     # counts every page, cuts docs/assets/fonts/
glyphs:     make build
glyphs: then commit docs/assets/fonts/*.woff2. A character Plex itself has no glyph
glyphs: for is refused by subset-fonts.py by name; it belongs in NO_PLEX_GLYPH in
glyphs: tools/plex.py, with a line saying where it appears."""


def check(site: str, quiet: bool = False) -> tuple[list[str], dict]:
    """The problems, and what was counted: pages and characters by kind."""
    assets = os.path.join(site, "assets")
    fonts_css = os.path.join(assets, plex.FONTS_CSS)
    pages = plex.site_pages(site)
    counted = {kind: {"pages": 0, "sans": set(), "mono": set()} for kind in plex.KINDS}
    if not any(kind == "presentation" for _, kind in pages):
        return [f"{site}: no page with <main class=\"dg-page\">, which cannot be right"], counted
    if not any(kind == "documentation" for _, kind in pages):
        return [f"{site}: no page rendered by Material, which cannot be right"], counted

    sheets = {kind: plex.stylesheets(assets, kind) for kind in plex.KINDS}
    problems = []
    allowed_seen: dict[str, set[str]] = {}
    for page, kind in pages:
        with open(page, encoding="utf-8") as fh:
            chars = plex.plex_text(fh.read(), sheets[kind], kind)
        name = os.path.relpath(page, site)
        counted[kind]["pages"] += 1
        for family in plex.FAMILIES:
            counted[kind][family] |= chars[family]
            for ch in chars[family] & plex.NO_PLEX_GLYPH[family]:
                allowed_seen.setdefault(f"{ch} ({family})", set()).add(name)
        wanted = {f: chars[f] - plex.NO_PLEX_GLYPH[f] for f in plex.FAMILIES}
        for path, missing in plex.glyph_gaps(fonts_css, wanted):
            problems.append(f"{name}: {os.path.relpath(path, site)} has no glyph for "
                            f"{plex.describe(missing)}")

    # The list of what Plex lacks has to stay true of the files served.
    for path, present in _allowed_but_present(fonts_css):
        problems.append(f"{os.path.relpath(path, site)} has a glyph for "
                        f"{plex.describe(present)}, which NO_PLEX_GLYPH in tools/plex.py "
                        "says Plex does not have: take it off the list")

    if not quiet and not problems:
        for kind in plex.KINDS:
            c = counted[kind]
            print(f"glyphs: {c['pages']} {kind} pages — {len(c['sans'])} characters in Sans, "
                  f"{len(c['mono'])} in Mono, every one in its subset")
        for label, names in sorted(allowed_seen.items()):
            print(f"glyphs: {label} has no Plex glyph and is drawn in the system face, on "
                  f"{len(names)} page(s): {', '.join(sorted(names))}")
    return problems, counted


def _allowed_but_present(fonts_css: str) -> list[tuple[str, list[str]]]:
    from fontTools.ttLib import TTFont

    found = []
    for family, faces in plex.font_faces(fonts_css).items():
        for _, path in faces:
            cmap = TTFont(path).getBestCmap()
            present = sorted(ch for ch in plex.NO_PLEX_GLYPH[family] if ord(ch) in cmap)
            if present:
                found.append((path, present))
    return found


def selftest() -> int:
    import material

    failures = []
    material_css = sorted(glob.glob(os.path.join(
        os.path.dirname(material.__file__), "templates", "assets", "stylesheets",
        "main.*.min.css")))
    if not material_css:
        print("glyphs selftest: Material's stylesheet is not where the theme keeps it",
              file=sys.stderr)
        return 1

    presentation = ('<body><main class="dg-page"><p>{0}</p><pre>{0}</pre></main>'
                    '<script>var never = "✱";</script></body>')
    documentation = (
        '<body data-md-color-scheme="default">'
        '<header class="md-header dg-bar"><a>digline ✱</a></header>'
        '<div class="md-container"><main class="md-main"><article class="md-content__inner md-typeset">'
        '<p>{0} {1}</p><pre><code>{0} {2}</code></pre>'
        '</article></main></div>'
        '<footer class="dg-foot"><p>✱ band</p></footer>'
        '<script>var never = "✱";</script></body>')
    # What Plex cannot draw, in the face that cannot draw it: ∧ in both, box
    # drawing in the prose. Box drawing in the code is in the Mono subset.
    sans_allowed = "∧ ├──"
    mono_allowed = "∧"

    with tempfile.TemporaryDirectory() as site:
        assets = os.path.join(site, "assets")
        shutil.copytree(os.path.join(ROOT, "docs", "assets", "fonts"),
                        os.path.join(assets, "fonts"))
        for name in ("fonts.css", "pages.css", "chrome.css", "theme.css"):
            shutil.copy(os.path.join(ROOT, "docs", "assets", name), os.path.join(assets, name))
        os.makedirs(os.path.join(assets, "stylesheets"))
        shutil.copy(material_css[-1], os.path.join(assets, "stylesheets"))

        def write(path, html):
            os.makedirs(os.path.join(site, path))
            with open(os.path.join(site, path, "index.html"), "w", encoding="utf-8") as fh:
                fh.write(html)

        write("clean", presentation.format("digline compare → exit 1 · §4 «x» ⅔ ≥"))
        write("clean-docs", documentation.format("digline compare → exit 1 ⅔ ≥",
                                                 sans_allowed, mono_allowed + " └── run"))
        problems, counted = check(site, quiet=True)
        if problems:
            failures.append(f"clean pages were refused: {problems!r}")
        for kind in plex.KINDS:
            for family in plex.FAMILIES:
                if not counted[kind][family]:
                    failures.append(f"a clean {kind} page counted nothing in {family}: "
                                    "the check would pass by not looking")
        if "├" not in counted["documentation"]["sans"] or "∧" not in counted["documentation"]["mono"]:
            failures.append("the documentation page's allowed characters were not counted, "
                            "so letting them through proves nothing")
        if "✱" in counted["documentation"]["sans"]:
            failures.append("text in the bar or the band was counted as Plex")

        write("planted", presentation.format("digline ✱ compare"))
        write("planted-docs", documentation.format("digline ✱ compare", "", "✱"))
        problems, _ = check(site, quiet=True)
        for page in ("planted", "planted-docs"):
            mine = [p for p in problems if p.startswith(page + os.sep) and "U+2731" in p]
            if len(mine) != 6:
                failures.append(f"✱ on {page} was not refused in all six faces: {mine!r}")
        stray = [p for p in problems if not p.startswith(("planted" + os.sep, "planted-docs" + os.sep))]
        if stray:
            failures.append(f"refusals on pages that are clean: {stray!r}")

    for failure in failures:
        print(f"glyphs selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("glyphs selftest: a clean presentation page and a clean documentation page pass, "
          "NO_PLEX_GLYPH let through in prose and code; ✱ refused in all six faces on each")
    return 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    if len(argv) != 1:
        print(__doc__.split("usage:")[1].split("\n\n")[0], file=sys.stderr)
        return 2
    problems, _ = check(argv[0])
    for problem in problems:
        print(f"glyphs: {problem}", file=sys.stderr)
    if problems:
        print(HOW, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
