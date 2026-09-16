#!/usr/bin/env -S uv run python
"""Cut IBM Plex down to the characters the home shows.

The presentation pages draw their body in IBM Plex Sans and IBM Plex Mono,
from docs/assets/fonts/. Each file there holds only the glyphs the home needs
in that family: the text of overrides/home.html, rendered from home.json,
without markup or script, plus every string in home.json. Which characters
belong to which family is read out of docs/assets/pages.css — see "the faces"
in tools/hooks/home.py, which does the counting both for this script and for
the selftest that fails when a character is missing.

── when to run it ───────────────────────────────────────────────────────────
When `make home` says a woff2 "has no glyph for" a character: new copy in
home.html, a new capture of home.json with a character the old one did not
have, a rule in pages.css that moves text from one family to the other, or a
new weight.

── how ──────────────────────────────────────────────────────────────────────
    make docs                        # home.json from ../digline, if you want it counted
    uv run tools/subset-fonts.py     # downloads, checks, cuts, writes docs/assets/fonts/
    make home                        # the selftest reads the new cmaps

Then commit the woff2 files, with the sizes this script prints.

The characters are those of the fixture, tools/testdata/home/home.json, and of
the synced docs/product/assets/home/home.json when there is one. To bring the
fixture up to digline's capture first:

    git -C ../digline show origin/main:docs/assets/home/home.json \\
        > tools/testdata/home/home.json

── what it reads ────────────────────────────────────────────────────────────
The sources are IBM's own releases on npm, pinned by version and by SHA-256
below, fetched from jsDelivr. They are the complete fonts, not a Latin subset,
so any character Plex has can be cut in (the → the home prints included). A
checksum that does not match stops the script before anything is written.

Which files to write, and at which weight, comes from the @font-face rules in
pages.css: a new weight is a new @font-face there, and a SOURCES line here.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "hooks"))

import home  # noqa: E402  the hook, for the counting

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
SYNCED = os.path.join(ROOT, "docs", home.HOME_JSON)

# Always in: the spaces the text is separated by, which the counting skips.
SPACES = {0x20, 0xA0}


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

    datasets = []
    for path in (FIXTURE, SYNCED):
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                datasets.append(json.load(fh))
            print(f"subset-fonts: counting {os.path.relpath(path, ROOT)}")
    chars = home.plex_characters(ROOT, datasets)

    css_path = os.path.join(ROOT, home.PAGES_CSS)
    with open(css_path, encoding="utf-8") as fh:
        faces = home.font_faces(fh.read(), os.path.dirname(css_path))

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
    for family in ("sans", "mono"):
        print(f"  {family}: {''.join(sorted(chars[family]))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
