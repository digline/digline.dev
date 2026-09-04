#!/usr/bin/env python3
"""Read llms.txt out of a built site and say whether it is telling the truth.

The same three questions check-sitemap.py asks, about the other machine-readable
file at the root:

  * is it the format — an H1, a one-line summary, and sections of links?
  * is every URL under site_url and a file that is actually in the build?
  * is every page in the build listed, or is something simply invisible to an
    agent that reads this file and nothing else?

The last one is the reason this exists. A missing description fails the build
already; a page that quietly stops being listed fails nothing, and llms.txt
would go stale in the one way nobody would notice.

    usage: tools/check-llms.py [site-dir]
"""

from __future__ import annotations

import os
import re
import sys

SITE_URL = "https://digline.dev/"

# Built by the theme, not pages: the same exception the sitemap check makes.
NOT_PAGES = {"404.html"}

LINK = re.compile(r"^- \[([^\]]+)\]\(([^)]+)\)(?::\s*(.+))?$")


def _page_of(rel: str) -> str:
    """The rendered page a listed URL stands for, as a path inside site/.

    A link is normally the page's Markdown — /why.md — and mkdocs writes the
    page itself at why/index.html. One link is a directory URL (the landing,
    which has no Markdown of its own), and that is already the page.
    """
    if rel == "" or rel.endswith("/"):
        return rel + "index.html"
    if rel.endswith(".md"):
        stem = rel[: -len(".md")]
        if os.path.basename(stem) == "index":
            return stem + ".html"
        return stem + "/index.html"
    return rel


def main(site: str) -> int:
    errors: list[str] = []

    path = os.path.join(site, "llms.txt")
    if not os.path.isfile(path):
        print(f"no llms.txt at {path}", file=sys.stderr)
        return 1

    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()

    if not lines or not lines[0].startswith("# "):
        errors.append("does not open with an H1 naming the site")
    if not any(line.startswith("> ") for line in lines[:6]):
        errors.append("has no one-line summary under the H1")
    if not any(line.startswith("## ") for line in lines):
        errors.append("has no sections")

    seen: set[str] = set()
    listed: set[str] = set()

    for n, line in enumerate(lines, 1):
        if not line.startswith("- "):
            continue
        match = LINK.match(line)
        if not match:
            errors.append(f"line {n} is a list item but not a described link: {line}")
            continue
        title, url, description = match.groups()

        if not description or not description.strip():
            errors.append(f"{url} is listed with no description")
        if not title.strip():
            errors.append(f"{url} is listed with no title")

        if url in seen:
            errors.append(f"{url} is listed twice")
        seen.add(url)

        if not url.startswith(SITE_URL):
            errors.append(f"{url} is not under {SITE_URL}")
            continue

        rel = url[len(SITE_URL) :]
        page_rel = _page_of(rel)
        # A directory URL is served by the page itself; there is no second file
        # behind it to look for.
        file_rel = page_rel if rel == "" or rel.endswith("/") else rel

        target = os.path.join(site, *file_rel.split("/"))
        if not os.path.isfile(target):
            errors.append(f"{url} → {os.path.relpath(target, site)} does not exist")
            continue

        page = os.path.join(site, *page_rel.split("/"))
        if not os.path.isfile(page):
            errors.append(
                f"{url} has no rendered page: "
                f"{os.path.relpath(page, site)} does not exist"
            )
            continue
        listed.add(os.path.relpath(page, site))

    # The other direction: a page that is in the build and in nobody's index.
    built = {
        os.path.relpath(os.path.join(dirpath, name), site)
        for dirpath, _, names in os.walk(site)
        for name in names
        if name.endswith(".html")
    }
    missing = sorted(built - listed - NOT_PAGES)
    if missing:
        errors.append("in the build but not in llms.txt: " + ", ".join(missing))

    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"llms.txt: {len(seen)} URLs, every one a page in {site}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "site"))
