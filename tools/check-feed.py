#!/usr/bin/env python3
"""Read feed.xml out of a built site and say whether it is telling the truth.

Three questions, and a non-zero exit on the first no:

  * does it parse, as RSS 2.0, with one channel and an item that carries every
    field a reader needs?
  * is every <link> under site_url, unique, a guid of its own, and a page that
    is actually in the build — i.e. does the file the URL resolves to exist?
  * does every <pubDate> read as a date, is it not in the future, and is it the
    day the page itself says it was published?

That last one is why this is worth having. The feed and the card are written
from one line of front matter by one hook, and the check that they still agree
costs a regex: a reader's list and a link preview saying different days is the
kind of wrong nobody sees from here.

It also says what is a post in the build and *not* in the feed, and what is in
the feed and not a post — the two failures nobody notices, since a feed that
quietly drops a post and one that quietly carries the pricing page both look
like a feed.

    usage: tools/check-feed.py [site-dir]
"""

from __future__ import annotations

import datetime
import email.utils
import os
import re
import sys
import xml.etree.ElementTree as ET

SITE_URL = "https://digline.dev/"

# What a post's page says about itself, written by tools/hooks/blog.py through
# overrides/partials/seo.html. Read here, not recomputed: the point is to
# compare the feed with the page, and a second reading of the front matter
# would only compare this file with itself.
PUBLISHED = re.compile(r'<meta property="article:published_time" content="([^"]*)">')

# The posts, in the build: everything under blog/ that is not the page listing
# them. The same rule tools/hooks/blog.py applies to the sources.
POSTS = re.compile(r"^blog/(?!index\.html$)[^/]+/index\.html$")

ITEM_FIELDS = ("title", "link", "description", "pubDate", "guid")


def posts_in(site: str) -> set[str]:
    """The built pages that are posts, as paths relative to the site."""
    found = set()
    for dirpath, _, names in os.walk(site):
        for name in names:
            if name != "index.html":
                continue
            rel = os.path.relpath(os.path.join(dirpath, name), site)
            if POSTS.match(rel.replace(os.sep, "/")):
                found.add(rel.replace(os.sep, "/"))
    return found


def main(site: str) -> int:
    errors: list[str] = []

    path = os.path.join(site, "feed.xml")
    if not os.path.isfile(path):
        print(f"no feed at {path}", file=sys.stderr)
        return 1

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as e:
        print(f"feed.xml is not valid XML: {e}", file=sys.stderr)
        return 1

    if (root.tag, root.get("version")) != ("rss", "2.0"):
        errors.append(f"root element is {root.tag} version {root.get('version')!r}, "
                      "expected rss version 2.0")
    channels = root.findall("channel")
    if len(channels) != 1:
        print(f"error: feed.xml has {len(channels)} <channel>, expected 1",
              file=sys.stderr)
        return 1
    channel = channels[0]
    for field in ("title", "link", "description"):
        if not (channel.findtext(field) or "").strip():
            errors.append(f"the channel has no <{field}>")

    today = datetime.date.today()
    seen: set[str] = set()
    listed: set[str] = set()

    for item in channel.findall("item"):
        link = (item.findtext("link") or "").strip()
        for field in ITEM_FIELDS:
            if not (item.findtext(field) or "").strip():
                errors.append(f"an item ({link or 'no link'}) has no <{field}>")
        if not link:
            continue
        if link in seen:
            errors.append(f"{link} is in the feed twice")
        seen.add(link)

        guid = (item.findtext("guid") or "").strip()
        if guid and guid != link:
            errors.append(f"{link} has a <guid> that is not its link: {guid}")

        if not link.startswith(SITE_URL):
            errors.append(f"{link} is not under {SITE_URL}")
            continue

        # https://digline.dev/blog/x/ → site/blog/x/index.html
        rel = link[len(SITE_URL):]
        if rel == "" or rel.endswith("/"):
            rel = rel + "index.html"
        target = os.path.join(site, *rel.split("/"))
        if not os.path.isfile(target):
            errors.append(f"{link} → {os.path.relpath(target, site)} does not exist")
            continue
        listed.add(rel)

        raw = (item.findtext("pubDate") or "").strip()
        try:
            when = email.utils.parsedate_to_datetime(raw).date()
        except (TypeError, ValueError):
            errors.append(f"{link} has an unreadable <pubDate>: {raw!r}")
            continue
        if when > today:
            errors.append(f"{link} has a <pubDate> in the future: {raw}")

        with open(target, encoding="utf-8") as fh:
            says = PUBLISHED.search(fh.read())
        if not says:
            errors.append(f"{link} is in the feed and its page declares no "
                          "article:published_time")
        elif says.group(1) != when.isoformat():
            errors.append(f"{link} is in the feed as {when.isoformat()} and its "
                          f"page says it was published {says.group(1)}")

    # Both directions, and they are different failures: a post nobody is sent,
    # and a page sent to people who asked for the posts.
    built = posts_in(site)
    missing = sorted(built - listed)
    if missing:
        errors.append("a post in the build and not in the feed: " + ", ".join(missing))
    intruders = sorted(listed - built)
    if intruders:
        errors.append("in the feed and not a post: " + ", ".join(intruders))

    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1
    print(f"feed.xml: {len(seen)} post(s), every one in {site}/ and dated as its "
          "page is")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else "site"))
