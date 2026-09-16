#!/usr/bin/env -S uv run python
"""Every character a presentation page shows in IBM Plex has a glyph there.

Plex is served as subsets, cut by tools/subset-fonts.py. A browser that meets a
character outside a subset draws it in the system face and says nothing, so
this reads the build instead: every page in site/ whose <main> is a .dg-page,
the text each Plex face draws on it (tools/plex.py), and the cmap of every
woff2 site/assets/pages.css declares. One character short fails, naming the
page, the file and the character.

    usage: tools/check-glyphs.py site
           tools/check-glyphs.py --selftest

--selftest needs no build: it writes a two-page site with the fonts in
docs/assets/, one page clean and one with ✱ (U+2731) in Sans and in Mono text,
and the check must pass the first and refuse the second in all six faces.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import plex  # noqa: E402


def check(site: str, quiet: bool = False) -> list[str]:
    css_path = os.path.join(site, "assets", "pages.css")
    with open(css_path, encoding="utf-8") as fh:
        pages_css = fh.read()
    pages = plex.presentation_pages(site)
    if not pages:
        return [f"{site}: no page with <main class=\"dg-page\">, which cannot be right"]
    problems = []
    for page in pages:
        with open(page, encoding="utf-8") as fh:
            chars = plex.plex_text(fh.read(), pages_css)
        name = os.path.relpath(page, site)
        gaps = plex.glyph_gaps(css_path, chars)
        for path, missing in gaps:
            problems.append(f"{name}: {os.path.relpath(path, site)} has no glyph for "
                            f"{plex.describe(missing)}")
        if not quiet and not gaps:
            print(f"glyphs: {name} — {len(chars['sans'])} Sans, {len(chars['mono'])} Mono, "
                  "every one in its subset")
    return problems


def selftest() -> int:
    with tempfile.TemporaryDirectory() as site:
        shutil.copytree(os.path.join(ROOT, "docs", "assets", "fonts"),
                        os.path.join(site, "assets", "fonts"))
        shutil.copy(os.path.join(ROOT, "docs", "assets", "pages.css"),
                    os.path.join(site, "assets", "pages.css"))
        page = ('<main class="dg-page"><p>{0}</p><pre>{0}</pre></main>'
                '<script>var never = "✱";</script>')
        os.makedirs(os.path.join(site, "clean"))
        with open(os.path.join(site, "clean", "index.html"), "w", encoding="utf-8") as fh:
            fh.write(page.format("digline compare → exit 1"))
        if check(site, quiet=True):
            print(f"glyphs selftest: a clean page was refused: {check(site, quiet=True)}",
                  file=sys.stderr)
            return 1
        os.makedirs(os.path.join(site, "planted"))
        with open(os.path.join(site, "planted", "index.html"), "w", encoding="utf-8") as fh:
            fh.write(page.format("digline ✱ compare"))
        problems = check(site, quiet=True)
        if len(problems) != 6 or not all("planted" in p and "U+2731" in p for p in problems):
            print(f"glyphs selftest: ✱ was not refused in all six faces: {problems!r}",
                  file=sys.stderr)
            return 1
    print("glyphs selftest: a clean page passes; ✱ refused in all six faces, as it must")
    return 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    if len(argv) != 1:
        print(__doc__.split("usage:")[1].split("\n\n")[0], file=sys.stderr)
        return 2
    problems = check(argv[0])
    for problem in problems:
        print(f"glyphs: {problem}", file=sys.stderr)
    if problems:
        print("glyphs: cut the subsets again — tools/subset-fonts.py says how.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
