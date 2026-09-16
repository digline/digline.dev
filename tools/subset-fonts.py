#!/usr/bin/env -S uv run python
"""Cut IBM Plex down to the characters the presentation pages show.

The presentation pages — every page whose <main> is a .dg-page: today the home,
start, why, about and contact — draw their body in IBM Plex Sans and IBM Plex
Mono, from docs/assets/fonts/. Each file there holds, for its family:

  * a fixed base: printable ASCII, U+0020 to U+007E, and – — ‘ ’ “ ” … · → − × •
    (tools/plex.py, BASE);
  * the characters the built pages show in that family, without markup or
    script, and without text a page puts in a system face;
  * every string in home.json, in both families.

Which text belongs to which family is read out of pages.css and each page's
own <style> blocks, by tools/plex.py. tools/check-glyphs.py uses the same code
on the build to fail it when a character has no glyph.

── when to run it ───────────────────────────────────────────────────────────
When `make build` stops at the glyph check: a page with a character outside the
base that the subsets do not have, a new capture of home.json, a rule that
moves text into Plex, or a new weight.

── how ──────────────────────────────────────────────────────────────────────
    make docs                        # docs/product/ from ../digline: the build needs it
    uv run tools/subset-fonts.py     # builds to a temporary directory, counts,
                                     # downloads, checks, cuts docs/assets/fonts/
    make build                       # the glyph check reads the new files

Then commit the woff2 files, with the sizes this script prints.

The home.json strings are those of the synced docs/product/assets/home/home.json
and of the fixture, tools/testdata/home/home.json. To bring the fixture up to
digline's capture first:

    git -C ../digline show origin/main:docs/assets/home/home.json \\
        > tools/testdata/home/home.json

── what it reads ────────────────────────────────────────────────────────────
The sources are IBM's own releases on npm, pinned by version and by SHA-256
below, fetched from jsDelivr. They are the complete fonts, not a Latin subset,
so any character Plex has can be cut in. A checksum that does not match stops
the script before anything is written.

Which files to write, and at which weight, comes from the @font-face rules in
pages.css: a new weight is a new @font-face there, and a SOURCES line here.

fonttools[woff] (pyproject.toml) does the cutting here, and reads the cmaps in
tools/check-glyphs.py.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import plex  # noqa: E402  the counting, shared with check-glyphs.py

SANS = "https://cdn.jsdelivr.net/npm/@ibm/plex-sans@1.1.0/fonts/complete/woff2/"
MONO = "https://cdn.jsdelivr.net/npm/@ibm/plex-mono@2.5.0/fonts/complete/woff2/"

# (family, weight) → (url, sha256)
SOURCES = {
    ("sans", "400"): (SANS + "IBMPlexSans-Regular.woff2",
                      "ba711a3085ff9f27440b6b9c4550cfc47c97bf36591d5da958b975bb3add8c1a"),
    ("sans", "500"): (SANS + "IBMPlexSans-Medium.woff2",
                      "5660f8a658f8bb50dbc005232f885eadffd2bc1c235c4f6fbb63469d1f9cde6d"),
    ("sans", "600"): (SANS + "IBMPlexSans-SemiBold.woff2",
                      "f78048030eab62e860efa39a0df79e2e5581bf122eb95b9bc42c0b8a4988d205"),
    ("sans", "700"): (SANS + "IBMPlexSans-Bold.woff2",
                      "fa7130d854a660b39a7fc9e6e0f2dc23dba5f1346e2adea3e1fe37b6d884133d"),
    ("mono", "400"): (MONO + "IBMPlexMono-Regular.woff2",
                      "ba204497f16b6d334cee9d1e963a831b73e3a56e1d6300a8489d18df7214b350"),
    ("mono", "500"): (MONO + "IBMPlexMono-Medium.woff2",
                      "33faf307fa6031fb4062276d7320a6d632de890cbb347576fd80cfa01077bc25"),
}

FIXTURE = os.path.join(ROOT, "tools", "testdata", "home", "home.json")
SYNCED = os.path.join(ROOT, "docs", "product", "assets", "home", "home.json")
PAGES_CSS = os.path.join(ROOT, "docs", "assets", "pages.css")

# Always in besides BASE: the no-break space, which the counting skips.
SPACES = {0xA0}


def fetch(url: str, sha256: str, into: str) -> str:
    path = os.path.join(into, os.path.basename(url))
    with urllib.request.urlopen(url, timeout=60) as response:
        body = response.read()
    digest = hashlib.sha256(body).hexdigest()
    if digest != sha256:
        raise SystemExit(f"subset-fonts: {url}\n  sha256 {digest}, pinned {sha256}. Nothing written.")
    with open(path, "wb") as fh:
        fh.write(body)
    return path


def main() -> int:
    from fontTools import subset

    if not os.path.isfile(SYNCED):
        raise SystemExit("subset-fonts: docs/product/ is not synced; run `make docs` first.")
    with open(PAGES_CSS, encoding="utf-8") as fh:
        pages_css = fh.read()

    chars = {family: set(plex.BASE) for family in plex.FAMILIES}
    with tempfile.TemporaryDirectory() as site:
        subprocess.run([sys.executable, "-m", "mkdocs", "build", "--quiet", "--site-dir", site],
                       cwd=ROOT, check=True)
        for page in plex.presentation_pages(site):
            with open(page, encoding="utf-8") as fh:
                shown = plex.plex_text(fh.read(), pages_css)
            print(f"subset-fonts: counting {os.path.relpath(page, site)}")
            for family in chars:
                chars[family] |= shown[family]
    for path in (SYNCED, FIXTURE):
        with open(path, encoding="utf-8") as fh:
            strings = plex.json_strings(json.load(fh))
        print(f"subset-fonts: counting {os.path.relpath(path, ROOT)}")
        for family in chars:
            chars[family] |= strings

    faces = plex.font_faces(PAGES_CSS)
    wanted = [(family, weight, path) for family, entries in faces.items()
              for weight, path in entries]
    unknown = [(f, w) for f, w, _ in wanted if (f, w) not in SOURCES]
    if unknown:
        raise SystemExit(f"subset-fonts: no source for {unknown}; add it to SOURCES.")

    total = 0
    with tempfile.TemporaryDirectory() as tmp:
        sources = {key: fetch(*SOURCES[key], tmp) for key in {(f, w) for f, w, _ in wanted}}
        for family, weight, out in wanted:
            options = subset.Options()
            options.flavor = "woff2"
            font = subset.load_font(sources[(family, weight)], options)
            subsetter = subset.Subsetter(options)
            subsetter.populate(unicodes=sorted(SPACES | {ord(ch) for ch in chars[family]}))
            subsetter.subset(font)
            subset.save_font(font, out, options)
            size = os.path.getsize(out)
            total += size
            print(f"subset-fonts: {os.path.relpath(out, ROOT)}  {len(chars[family])} characters  "
                  f"{size:,} bytes")
    print(f"subset-fonts: {total:,} bytes in all")
    for family in plex.FAMILIES:
        beyond = sorted(chars[family] - plex.BASE)
        print(f"  {family}, beyond the base: {''.join(beyond)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
