#!/usr/bin/env python3
"""Read sitemap.xml out of a built site and say whether it is telling the truth.

Three questions, and a non-zero exit on the first no:

  * does it parse, with the right namespace and a <loc> in every <url>?
  * is every <loc> under site_url, unique, and a page that is actually in the
    build output — i.e. does the file the URL resolves to exist?
  * does every <lastmod> read as a date, and is it not in the future?

It also says what is in the build and *not* in the sitemap, because that is the
failure nobody notices: a page ships, nothing breaks, and it is simply never
crawled.

    usage: tools/check-sitemap.py [site-dir]
"""

from __future__ import annotations

import datetime
import os
import sys
import xml.etree.ElementTree as ET

NS = "http://www.sitemaps.org/schemas/sitemap/0.9"
SITE_URL = "https://digline.dev/"

# Built by the theme, not pages: they are not in the sitemap and should not be.
NOT_PAGES = {"404.html"}


def main(site: str) -> int:
    errors: list[str] = []

    path = os.path.join(site, "sitemap.xml")
    if not os.path.isfile(path):
        print(f"no sitemap at {path}", file=sys.stderr)
        return 1

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        print(f"sitemap.xml is not valid XML: {e}", file=sys.stderr)
        return 1

    if root.tag != f"{{{NS}}}urlset":
        errors.append(f"root element is {root.tag}, expected {{{NS}}}urlset")

    today = datetime.date.today()
    seen: set[str] = set()
    listed: set[str] = set()

    for url in root.findall(f"{{{NS}}}url"):
        loc = url.findtext(f"{{{NS}}}loc")
        if not loc:
            errors.append("a <url> has no <loc>")
            continue
        if loc in seen:
            errors.append(f"{loc} is listed twice")
        seen.add(loc)

        if not loc.startswith(SITE_URL):
            errors.append(f"{loc} is not under {SITE_URL}")
            continue

        # https://digline.dev/why/ → site/why/index.html
        rel = loc[len(SITE_URL) :]
        if rel == "" or rel.endswith("/"):
            rel = rel + "index.html"
        target = os.path.join(site, *rel.split("/"))
        if not os.path.isfile(target):
            errors.append(f"{loc} → {os.path.relpath(target, site)} does not exist")
        else:
            listed.add(os.path.relpath(target, site))

        lastmod = url.findtext(f"{{{NS}}}lastmod")
        if lastmod is None:
            errors.append(f"{loc} has no <lastmod>")
            continue
        try:
            when = datetime.date.fromisoformat(lastmod.strip()[:10])
        except ValueError:
            errors.append(f"{loc} has an unreadable <lastmod>: {lastmod!r}")
            continue
        if when > today:
            errors.append(f"{loc} has a <lastmod> in the future: {lastmod}")

    # The other direction: pages in the build that nothing points a crawler at.
    built = {
        os.path.relpath(os.path.join(dirpath, name), site)
        for dirpath, _, names in os.walk(site)
        for name in names
        if name.endswith(".html")
    }
    missing = sorted(built - listed - NOT_PAGES)
    if missing:
        errors.append("in the build but not in the sitemap: " + ", ".join(missing))

    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"sitemap.xml: {len(seen)} URLs, every one a page in {site}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "site"))
