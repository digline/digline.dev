#!/usr/bin/env -S uv run python
"""Every link to one of this site's own assets carries the hash of its content.

tools/hooks/assets.py links the stylesheets in assets/ and the fonts in
assets/fonts/ as ``<path>?v=<hash>``, so that a changed file is a new URL. This
reads the build and fails when that is not what was written:

  * a page's <link>, <script> or <img>/<source> pointing at an own stylesheet,
    script or font (assets/*.css, assets/*.js, assets/fonts/*) without ?v=;
  * a ?v= that is not the hash of the file site/ holds under that path;
  * a url() in an own stylesheet pointing at a font without ?v=, or with the
    wrong one;
  * a linked asset that is not in site/ at all.

Material's own files, assets/stylesheets/ and assets/javascripts/, carry their
hash in their names and are left alone.

    usage: tools/check-assets.py site
           tools/check-assets.py --selftest

--selftest needs no build: it writes a small site with a stylesheet, a font
and a page, versioned as the hook versions them, and checks that it passes,
then plants each failure in turn and checks that each is refused.
"""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import sys
import tempfile
from urllib.parse import urlsplit

OWN = re.compile(r"^assets/(?!stylesheets/|javascripts/)(?:fonts/[^/]+|[^/]+\.(?:css|js))$")
_ATTR = re.compile(r"""<(?:link|script|img|source)\b[^>]*?\b(?:href|src)=["']([^"']+)["']""", re.I)
_URL = re.compile(r"""url\(\s*["']?([^"')]+)["']?\s*\)""")
_HASH = re.compile(r"^v=([0-9a-f]{12})$")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def _check_link(site: str, where: str, base_dir: str, url: str, problems: list[str]) -> None:
    parts = urlsplit(url)
    if parts.scheme or parts.netloc:
        return
    if parts.path.startswith("/"):
        target = os.path.normpath(os.path.join(site, parts.path.lstrip("/")))
    else:
        target = os.path.normpath(os.path.join(base_dir, parts.path))
    rel = os.path.relpath(target, site).replace(os.sep, "/")
    if not OWN.match(rel):
        return
    if not os.path.isfile(target):
        problems.append(f"{where}: links {url}, and site/{rel} does not exist")
        return
    match = _HASH.match(parts.query)
    if not match:
        problems.append(f"{where}: links {rel} without its hash (?v=…)")
        return
    with open(target, "rb") as fh:
        actual = digest(fh.read())
    if match.group(1) != actual:
        problems.append(f"{where}: links {rel}?v={match.group(1)}, and the file's hash is {actual}")


def check(site: str) -> tuple[list[str], int]:
    problems: list[str] = []
    links = 0
    for folder, _, names in os.walk(site):
        for name in sorted(names):
            path = os.path.join(folder, name)
            rel = os.path.relpath(path, site).replace(os.sep, "/")
            if name.endswith(".html"):
                with open(path, encoding="utf-8") as fh:
                    urls = _ATTR.findall(fh.read())
            elif name.endswith(".css") and OWN.match(rel):
                with open(path, encoding="utf-8") as fh:
                    urls = [u for u in _URL.findall(fh.read()) if not u.startswith("data:")]
            else:
                continue
            for url in urls:
                before = len(problems)
                _check_link(site, rel, folder, url, problems)
                target = urlsplit(url)
                if not target.scheme and len(problems) == before and "?v=" in url:
                    links += 1
    return problems, links


def selftest() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as site:
        os.makedirs(os.path.join(site, "assets", "fonts"))
        os.makedirs(os.path.join(site, "assets", "stylesheets"))
        os.makedirs(os.path.join(site, "page"))
        font = b"not really a font"
        with open(os.path.join(site, "assets", "fonts", "f.woff2"), "wb") as fh:
            fh.write(font)
        css = f'@font-face {{ src: url("fonts/f.woff2?v={digest(font)}") }}'
        with open(os.path.join(site, "assets", "fonts.css"), "w") as fh:
            fh.write(css)
        with open(os.path.join(site, "assets", "stylesheets", "main.abc.min.css"), "w") as fh:
            fh.write("body{}")
        css_hash = digest(css.encode())

        def page(html: str) -> None:
            with open(os.path.join(site, "page", "index.html"), "w") as fh:
                fh.write(html)

        def css_file(text: str) -> None:
            with open(os.path.join(site, "assets", "fonts.css"), "w") as fh:
                fh.write(text)

        good = (f'<link rel="stylesheet" href="../assets/fonts.css?v={css_hash}">'
                '<link rel="stylesheet" href="../assets/stylesheets/main.abc.min.css">'
                '<script async src="https://example.org/count.js"></script>'
                '<img src="../assets/favicon.svg">')
        page(good)
        problems, links = check(site)
        if problems:
            failures.append(f"a versioned site was refused: {problems}")
        if links != 2:
            failures.append(f"the versioned site should count 2 links (page, font), counted {links}")

        planted = [
            ("a stylesheet without its hash",
             lambda: page('<link rel="stylesheet" href="../assets/fonts.css">'), "without its hash"),
            ("a root-relative stylesheet without its hash",
             lambda: page('<link rel="stylesheet" href="/assets/fonts.css">'), "without its hash"),
            ("a stale hash",
             lambda: page('<link rel="stylesheet" href="../assets/fonts.css?v=000000000000">'),
             "and the file's hash is"),
            ("a font without its hash in a stylesheet",
             lambda: (page(good), css_file('@font-face { src: url("fonts/f.woff2") }')),
             "links assets/fonts/f.woff2 without its hash"),
            ("an own asset that is not there",
             lambda: (css_file(css), page('<script src="../assets/app.js?v=000000000000"></script>')),
             "does not exist"),
        ]
        for label, plant, needle in planted:
            plant()
            problems, _ = check(site)
            if not any(needle in p for p in problems):
                failures.append(f"{label}: not refused ({problems})")
            else:
                print(f"assets selftest: refused, as it must — {label}")
    for failure in failures:
        print(f"assets selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("assets selftest: a versioned site passes; five ways of linking an own asset "
          "without its hash refused")
    return 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    if len(argv) != 1:
        print(__doc__.split("usage:")[1].split("\n\n")[0], file=sys.stderr)
        return 2
    problems, links = check(argv[0])
    for problem in problems:
        print(f"assets: {problem}", file=sys.stderr)
    if problems:
        print("assets: own assets are versioned by tools/hooks/assets.py; link a stylesheet "
              "through the `versioned` filter or mkdocs.yml's extra_css.", file=sys.stderr)
        return 1
    if not links:
        print("assets: no versioned link to an own asset in the build, which cannot be right",
              file=sys.stderr)
        return 1
    print(f"assets: {links} links to own stylesheets and fonts, every one with its content's hash")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
