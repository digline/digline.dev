"""site/feed.xml: the posts, newest first, for somebody who subscribes.

RSS 2.0, written from what the build already knows. Nothing here reads a file
or parses a date: `tools/hooks/blog.py` is the one reader of a post's front
matter and leaves what it found on `page.meta`, and `tools/hooks/seo.py` leaves
the description and the title there unescaped — this turns those into a
channel and its items, and writes the one file.

  * an item per post: its title, its canonical URL as both link and guid, its
    own sentence, and `date:` as an RFC 822 `pubDate`;
  * the channel is /blog/ — its title and its sentence, and the newest post's
    date as `lastBuildDate`, so a build that adds nothing changes nothing;
  * `<atom:link rel="self">`, which is the one thing a feed has to say about
    itself that no page says for it.

**The summary, not the post.** An item carries the sentence that is already the
page's description and a link back. A feed that carries the whole post is a
second copy of it, kept by hand, and this site has just spent two changes
taking second copies out.

Why a hook and not the plugin: the same answer llms.py gives. mkdocs-rss-plugin
is alive and would work, and it pins `mkdocs==1.6.1` exactly, brings four
dependencies for one file this repository can write with the standard library,
and takes its discovery link from Material's base.html — which means every
documentation page and none of the presentation pages, the opposite of where
this site wants it.

The `<link rel="alternate">` is written by overrides/partials/seo.html, from
`page.meta.feed_url`, which this sets on the posts, on /blog/ and on the home,
and nowhere else: the feed is an alternative reading of the blog, not of
product/api/. The home carries it because pasting a domain into a reader is how
most people subscribe, and the root is where a reader looks.

── what fails the build ─────────────────────────────────────────────────────
  * no post has a date to write — meaning blog.py found no post at all, which
    it refuses first;
  * /blog/ was not built, so the channel has no title and no sentence.

Everything else about the file is checked after it is written, by
tools/check-feed.py, which reads it the way check-sitemap.py reads sitemap.xml.

    usage: tools/hooks/feed.py --selftest
"""

from __future__ import annotations

import datetime
import email.utils
import os
import sys
import xml.etree.ElementTree as ET

from mkdocs.exceptions import PluginError

FEED = "feed.xml"
INDEX = "blog/index.md"
ATOM = "http://www.w3.org/2005/Atom"

# The channel — title and sentence — and one entry per post, both filled from
# page.meta as the pages go by. Module state, like llms.py's nav: on_post_build
# is handed a config and nothing else.
_channel: dict[str, str] = {}
_items: list[dict] = []


def _fail(problem: str) -> PluginError:
    return PluginError(f"feed: {problem}")


def rfc822(day: datetime.date) -> str:
    """A date as RSS writes one: "Sun, 13 Sep 2026 00:00:00 +0000".

    A post declares the day it was published and not the minute, so the minute
    is midnight UTC — stated once here rather than implied by whatever the
    machine building the site thinks the time is.
    """
    when = datetime.datetime.combine(day, datetime.time.min,
                                     tzinfo=datetime.timezone.utc)
    return email.utils.format_datetime(when)


def document(channel: dict, items: list[dict], feed_url: str) -> str:
    """The whole file, as a string, from the channel and the items."""
    if not items:
        raise _fail("no post to put in the feed.")
    for key in ("title", "link", "description"):
        if not channel.get(key):
            raise _fail(f"the feed's channel has no {key}: /blog/ was not built, "
                        "or carries nothing to say what it is.")

    ET.register_namespace("atom", ATOM)
    rss = ET.Element("rss", {"version": "2.0"})
    node = ET.SubElement(rss, "channel")
    ET.SubElement(node, "title").text = channel["title"]
    ET.SubElement(node, "link").text = channel["link"]
    ET.SubElement(node, "description").text = channel["description"]
    ET.SubElement(node, "language").text = channel.get("language") or "en"
    # Where this file is, said by the file: a feed that has been copied, or
    # that a reader found at a mirror, still names its own home.
    ET.SubElement(node, f"{{{ATOM}}}link",
                  {"href": feed_url, "rel": "self",
                   "type": "application/rss+xml"})

    ordered = sorted(items, key=lambda i: (i["published"], i["link"]), reverse=True)
    # The newest post, not the moment of the build: two builds of the same
    # posts write the same bytes, and a reader is told nothing changed.
    ET.SubElement(node, "lastBuildDate").text = rfc822(ordered[0]["published"])

    for item in ordered:
        entry = ET.SubElement(node, "item")
        ET.SubElement(entry, "title").text = item["title"]
        ET.SubElement(entry, "link").text = item["link"]
        ET.SubElement(entry, "description").text = item["description"]
        ET.SubElement(entry, "pubDate").text = rfc822(item["published"])
        # The link is the identity: these URLs do not move, and a reader that
        # has seen one must not be shown it again because a title was edited.
        ET.SubElement(entry, "guid", {"isPermaLink": "true"}).text = item["link"]

    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")
    return ET.tostring(rss, encoding="unicode", xml_declaration=True) + "\n"


# ── the hooks mkdocs calls ───────────────────────────────────────────────────


def on_config(config, **kwargs):
    _channel.clear()
    _items.clear()
    return config


def on_page_content(html_content, page, config, files, **kwargs):
    """After blog.py and seo.py, whose values this reads and does not repeat."""
    site_url = (config["site_url"] or "").rstrip("/") + "/"
    meta = page.meta if page.meta is not None else {}
    src_uri = page.file.src_uri

    if src_uri == INDEX:
        _channel.update({
            "title": meta.get("seo_title_text") or page.title or "",
            "link": page.canonical_url or site_url + "blog/",
            "description": meta.get("description_text") or "",
            "language": meta.get("lang") or config["theme"]["language"],
        })

    published = meta.get("article_published")
    if published:
        _items.append({
            "title": meta.get("post_title") or page.title or "",
            "link": page.canonical_url or "",
            "description": meta.get("description_text") or "",
            "published": datetime.date.fromisoformat(published),
        })

    # Where the <link rel="alternate"> goes, and the whole of it: the posts,
    # the page that lists them, and the home.
    if published or src_uri == INDEX or page.is_homepage:
        meta["feed_url"] = site_url + FEED
    page.meta = meta
    return html_content


def on_post_build(config, **kwargs):
    site_url = (config["site_url"] or "").rstrip("/") + "/"
    text = document(_channel, _items, site_url + FEED)
    with open(os.path.join(config["site_dir"], FEED), "w", encoding="utf-8") as fh:
        fh.write(text)


# ── the selftest ─────────────────────────────────────────────────────────────


def selftest() -> int:
    failures: list[str] = []

    def expect(label, actual, wanted):
        if actual != wanted:
            failures.append(f"{label}: {actual!r}, wanted {wanted!r}")

    def refused(label, call, needle):
        try:
            call()
        except PluginError as error:
            if needle not in str(error):
                failures.append(f"{label}: refused, but not for this: {error}")
            else:
                print(f"feed selftest: refused, as it must — {label}")
            return
        failures.append(f"{label}: accepted, which it exists to refuse")

    channel = {"title": "Writing — digline", "link": "https://digline.dev/blog/",
               "description": "Occasional posts.", "language": "en"}
    older = {"title": "First", "link": "https://digline.dev/blog/first/",
             "description": "The first one.",
             "published": datetime.date(2026, 9, 9)}
    newer = {"title": "Second & last", "link": "https://digline.dev/blog/second/",
             "description": 'A sentence with "quotes" & an ampersand.',
             "published": datetime.date(2026, 9, 13)}

    # 1. The date, in the spelling RSS asks for and not the one the rest of the
    #    site uses.
    expect("a date as RSS writes one", rfc822(datetime.date(2026, 9, 13)),
           "Sun, 13 Sep 2026 00:00:00 +0000")
    expect("a day that is not two digits", rfc822(datetime.date(2026, 1, 1)),
           "Thu, 01 Jan 2026 00:00:00 +0000")

    # 2. The document: newest first, whatever order the pages arrived in, and
    #    the channel's own dates and links.
    xml = document(channel, [older, newer], "https://digline.dev/feed.xml")
    root = ET.fromstring(xml)
    expect("it is RSS 2.0", (root.tag, root.get("version")), ("rss", "2.0"))
    node = root.find("channel")
    expect("one channel", len(root.findall("channel")), 1)
    expect("the channel's title", node.findtext("title"), "Writing — digline")
    expect("the channel's link", node.findtext("link"), "https://digline.dev/blog/")
    expect("the channel's sentence", node.findtext("description"), "Occasional posts.")
    expect("lastBuildDate is the newest post, not the build",
           node.findtext("lastBuildDate"), "Sun, 13 Sep 2026 00:00:00 +0000")
    self_link = node.find(f"{{{ATOM}}}link")
    expect("the feed names itself",
           (self_link.get("href"), self_link.get("rel")),
           ("https://digline.dev/feed.xml", "self"))

    entries = node.findall("item")
    expect("an item per post", len(entries), 2)
    expect("newest first", [e.findtext("title") for e in entries],
           ["Second & last", "First"])
    expect("the newest item's date", entries[0].findtext("pubDate"),
           "Sun, 13 Sep 2026 00:00:00 +0000")
    expect("guid is the link", entries[0].findtext("guid"),
           "https://digline.dev/blog/second/")
    expect("guid is a permalink", entries[0].find("guid").get("isPermaLink"), "true")
    expect("the summary, not the post", entries[0].findtext("description"),
           'A sentence with "quotes" & an ampersand.')
    expect("an ampersand is escaped in the file, once",
           xml.count("&amp; an ampersand"), 1)
    expect("the same posts write the same bytes",
           document(channel, [newer, older], "https://digline.dev/feed.xml"), xml)

    # 3. What there has to be before there is a feed at all.
    refused("no post", lambda: document(channel, [], "https://digline.dev/feed.xml"),
            "no post to put in the feed")
    for key in ("title", "link", "description"):
        short = dict(channel)
        short[key] = ""
        refused(f"a channel with no {key}",
                lambda s=short: document(s, [newer], "https://digline.dev/feed.xml"),
                f"channel has no {key}")

    # 4. The three files this reaches into, each read for what it must carry.
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def reads(path: str) -> str:
        with open(os.path.join(root_dir, path), encoding="utf-8") as fh:
            return fh.read()

    card = reads("overrides/partials/seo.html")
    expect("partials/seo.html writes the alternate link",
           'type="application/rss+xml"' in card, True)
    expect("it writes it from page.meta.feed_url",
           "page.meta.feed_url" in card, True)
    expect("docs/blog/index.md sends a reader to the feed",
           f"/{FEED}" in reads("docs/blog/index.md"), True)

    for failure in failures:
        print(f"feed selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("feed selftest: an RSS 2.0 channel with its items newest first, dates "
          "in RFC 822, a guid that is the link, an escaped ampersand and the "
          "same bytes from the same posts; a feed with no post and a channel "
          "missing each of its three fields refused")
    return 0


if __name__ == "__main__":
    raise SystemExit(selftest())
