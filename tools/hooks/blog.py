"""The day a post was published, and everything the site says because of it.

`date:` in a post's front matter is the one place that day is written. It was
there before this hook and nothing read it: the date on /blog/ was typed a
second time, in prose, and the post itself never said when it was written.
Everything below is now read from that one line:

  * the line under the lede on the post, `<time datetime="…">` — the machine
    spelling in the attribute, the reader's in the text
    (`page.meta.published`, `published_display`, overrides/partials/opening.html);
  * `article:published_time` on the card, beside `article:modified_time`, which
    is `page.update_date` — the day the page last *changed*, which seo.py
    already works out for `<lastmod>` and which is a different fact;
  * the JSON-LD `BlogPosting` on each post, beside the `SoftwareApplication`
    the home carries and built the same way, from what the page already says;
  * the list on /blog/, its dates included. The index has a placeholder and no
    entry of its own, the way product/adr/ and product/examples/ do — see
    indexes.py, whose shape this follows.

`og:type` is `website` on /blog/, which is a list of articles and not one, and
stays `article` on the posts. No other page of the site is touched: seo.py
decides for all of them.

── what fails the build ─────────────────────────────────────────────────────
  * a post with no `date:`, or one that is not a date;
  * a `date:` after the day the build runs — a post cannot already have been
    published tomorrow, and check-sitemap.py refuses the `<lastmod>` that
    would go with it;
  * blog/index.md with no placeholder to fill;
  * after the build: a post whose `article:published_time` in site/ is not the
    `date:` its front matter declares.

The first three are read off disk in `on_files`, before a page is rendered, so
the build stops on the line to fix rather than thirty pages later. The fourth
needs the build, because it is the one that checks the wiring rather than the
source: it is what would notice the template dropping the tag, or a second hook
overwriting the value.

    usage: tools/hooks/blog.py --selftest
"""

from __future__ import annotations

import datetime
import json
import os
import posixpath
import re
import sys

import yaml
from mkdocs.exceptions import PluginError

# seo.py sits beside this file, and mkdocs puts a hook's folder on sys.path
# while it loads it: the person behind the site is named once, there.
from seo import AUTHOR

INDEX = "blog/index.md"

# A post is a page under blog/ that is not the index. Written as a path and not
# as a nav group, because the URL is what makes it a post: llms.py, sitemap.xml
# and the reader all read blog/ and none of them can see a nav section.
_POST = re.compile(r"^blog/(?!index\.md$)[^/]+\.md$")

_SLOT = re.compile(r"<!--\s*posts:.*?-->", re.S)
_FRONT_MATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*\r?\n", re.S)

# The month as a reader writes it. Spelled out here rather than taken from
# `strftime("%B")`, which answers in the locale of whoever is building: the
# site is in English on every machine that builds it.
MONTHS = ("January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December")

# src_uri → the date its front matter declares, filled in on_files and read
# everywhere else. One reader, so the list on the index and the card on the
# post cannot come to different answers about the same line.
_posts: dict[str, dict] = {}


def _fail(problem: str) -> PluginError:
    return PluginError(f"blog: {problem}")


def human(date: datetime.date) -> str:
    """2026-09-13 → "13 September 2026", the way the index already wrote it."""
    return f"{date.day} {MONTHS[date.month - 1]} {date.year}"


def read_post(text: str, src_uri: str, today: datetime.date) -> dict:
    """Title, description and date of one post, from its front matter.

    Parsed as YAML rather than by regex because `description:` is a folded
    block in every post the site has, and folding it back by hand is a second
    implementation of something PyYAML is already here to do — mkdocs reads the
    same lines with the same parser a moment later.
    """
    front = _FRONT_MATTER.match(text)
    if not front:
        raise _fail(f"{src_uri} has no front matter, so it declares no `date:`.")
    try:
        meta = yaml.safe_load(front.group(1)) or {}
    except yaml.YAMLError as error:
        raise _fail(f"the front matter of {src_uri} is not YAML: {error}") from None
    if not isinstance(meta, dict):
        raise _fail(f"the front matter of {src_uri} is not a mapping.")

    date = meta.get("date")
    if date is None:
        raise _fail(
            f"{src_uri} has no `date:` in its front matter. A post says when it "
            "was published, once, and the line under its lede, the card, the "
            "JSON-LD and the list on /blog/ are all read from that line:\n"
            "    date: YYYY-MM-DD")
    if isinstance(date, datetime.datetime) or not isinstance(date, datetime.date):
        raise _fail(
            f"{src_uri} has `date: {date}`, which is not a day. Write it "
            "YYYY-MM-DD, with no time and no quotes.")
    if date > today:
        raise _fail(
            f"{src_uri} has `date: {date.isoformat()}`, which is after today "
            f"({today.isoformat()}). A post cannot have been published "
            "tomorrow, and the sitemap this build writes would be refused for "
            "the same reason.")

    title = str(meta.get("title") or "").strip()
    if not title:
        raise _fail(f"{src_uri} has no `title:`, so the list on /blog/ has "
                    "nothing to name it.")
    description = re.sub(r"\s+", " ", str(meta.get("description") or "")).strip()
    if not description:
        raise _fail(f"{src_uri} has no `description:`, so the list on /blog/ has "
                    "nothing to say about it. seo.py refuses the same page for "
                    "the same reason.")
    return {"date": date, "title": title, "description": description}


def posts_list(posts: list[tuple[str, dict]]) -> str:
    """The entries on /blog/: newest first, under a heading per year.

    The shape the index had when it was written by hand — **date** — [title],
    then the post's own sentence — because that is what it looked like, not
    because anything here depends on it.
    """
    if not posts:
        raise _fail("no post to list on /blog/: no blog/<name>.md in the build.")
    lines: list[str] = []
    year: int | None = None
    for src_uri, post in sorted(posts, key=lambda p: (p[1]["date"], p[0]), reverse=True):
        if post["date"].year != year:
            year = post["date"].year
            # Every entry ends on a blank line, so the heading needs none in
            # front of it.
            lines += [f"## {year}", ""]
        # A `]` in a title would close the link early. Nothing has one; the day
        # something does is not the day to find out.
        title = post["title"].replace("]", "\\]")
        href = posixpath.basename(src_uri)
        lines += [f"**{human(post['date'])}** — [{title}]({href})", "",
                  post["description"], ""]
    return "\n".join(lines).rstrip("\n")


def blogposting(page, config, post: dict, modified: str, description: str) -> str:
    """The `BlogPosting` of one post.

    Everything in it is on the page already: the title a reader sees, the
    sentence under it in the card, the card's image, the canonical URL, the two
    dates and the one author. No publisher, no counts, no ratings — the rule
    seo.py states for the home's node holds here too, that a field nothing on
    the site can be checked against should not be written.

    `headline` is the post's `title:`, which is its `<h1>` — not its
    `seo_title`, which on one post is a different sentence written for a search
    result, and not `page.title`, which mkdocs replaces with the post's label
    in the nav where the nav gives one, and the nav gives a short one. The
    headline of an article is the title it is read under.
    """
    data = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post["title"],
        "description": description,
        "image": page.meta["og_image"],
        "url": page.canonical_url,
        "datePublished": post["date"].isoformat(),
        "dateModified": modified,
        "inLanguage": page.meta.get("lang") or config["theme"]["language"],
        "author": {"@type": "Person", "name": AUTHOR},
    }
    # The same spelling seo.py uses, and for the same reason: `</` cannot
    # appear inside a <script> block whatever it is quoting.
    return json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")


# ── the hooks mkdocs calls ───────────────────────────────────────────────────


def on_files(files, config, **kwargs):
    """Every post's front matter, read and held to the rules, before anything
    is rendered."""
    today = datetime.date.today()
    _posts.clear()
    for f in files.documentation_pages():
        if not _POST.match(f.src_uri):
            continue
        with open(f.abs_src_path, encoding="utf-8") as fh:
            _posts[f.src_uri] = read_post(fh.read(), f.src_uri, today)
    return files


def on_page_markdown(markdown, page, config, files, **kwargs):
    """The list on /blog/, in the Markdown: the search index, the table of
    contents and the copy llms.py writes beside the page all carry the posts
    and not the placeholder."""
    if page.file.src_uri != INDEX:
        return markdown
    if not _SLOT.search(markdown):
        raise _fail(
            f"{INDEX} has no placeholder for its list — an HTML comment opening "
            "`<!-- posts:` — so there is nowhere to put it.")
    return _SLOT.sub(lambda _: posts_list(list(_posts.items())), markdown, count=1)


def on_page_content(html_content, page, config, files, **kwargs):
    """After seo.py, which is where `og_type`, `og_image`, the description and
    `page.update_date` are decided: this reads all four."""
    src_uri = page.file.src_uri
    if src_uri == INDEX:
        # A list of articles is not one.
        page.meta["og_type"] = "website"
        return html_content
    post = _posts.get(src_uri)
    if post is None:
        return html_content

    published = post["date"].isoformat()
    # Never before the day it was published: `update_date` is the last commit
    # that touched the file, which is the same day at the earliest.
    modified = max(str(page.update_date or ""), published)
    description = page.meta.get("description_text") or post["description"]

    # The title the post is read under, beside the two dates: the JSON-LD
    # below needs it, and so does the feed's item. `page.title` is not it —
    # mkdocs replaces that with the post's label in the nav, which is shorter.
    page.meta["post_title"] = post["title"]
    page.meta["published"] = published
    page.meta["published_display"] = human(post["date"])
    page.meta["article_published"] = published
    page.meta["article_modified"] = modified
    page.meta["jsonld"] = blogposting(page, config, post, modified, description)
    return html_content


_PUBLISHED = re.compile(
    r'<meta property="article:published_time" content="([^"]*)">')


def on_post_build(config, **kwargs):
    """Each post's card against the front matter it was built from."""
    site = config["site_dir"]
    for src_uri, post in _posts.items():
        written = os.path.join(site, src_uri[: -len(".md")], "index.html")
        if not os.path.isfile(written):
            raise _fail(f"{src_uri} is a post and {written} was not written.")
        with open(written, encoding="utf-8") as fh:
            found = _PUBLISHED.search(fh.read())
        if not found:
            raise _fail(
                f"{written} has no `article:published_time`. The post declares "
                f"`date: {post['date'].isoformat()}` and the card should be "
                "saying so — overrides/partials/seo.html writes it.")
        if found.group(1) != post["date"].isoformat():
            raise _fail(
                f"{written} says it was published {found.group(1)}, and "
                f"{src_uri} declares `date: {post['date'].isoformat()}`.")


# ── the selftest ─────────────────────────────────────────────────────────────


def selftest() -> int:
    failures: list[str] = []
    today = datetime.date(2026, 9, 18)

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
                print(f"blog selftest: refused, as it must — {label}")
            return
        failures.append(f"{label}: accepted, which it exists to refuse")

    def post(front: str) -> str:
        return f"---\n{front}\n---\n\n# A post\n\nIts lede.\n"

    good = post('title: "A post, and its subtitle"\n'
                "description: >-\n  One sentence, folded\n  over two lines.\n"
                "date: 2026-09-13")

    # 1. What a post says, and the folded description folded back.
    expect("a post's front matter", read_post(good, "blog/a-post.md", today),
           {"date": datetime.date(2026, 9, 13),
            "title": "A post, and its subtitle",
            "description": "One sentence, folded over two lines."})
    expect("the day before today is a day like any other",
           read_post(post("title: t\ndescription: d\ndate: 2026-09-17"),
                     "blog/a.md", today)["date"],
           datetime.date(2026, 9, 17))
    expect("published today", read_post(post("title: t\ndescription: d\n"
                                             "date: 2026-09-18"),
                                        "blog/a.md", today)["date"], today)
    expect("the reader's spelling", human(datetime.date(2026, 9, 13)),
           "13 September 2026")
    expect("a day that is not two digits", human(datetime.date(2026, 1, 1)),
           "1 January 2026")

    # 2. Every way a post stops saying when it was published.
    refused("no date:", lambda: read_post(
        post("title: t\ndescription: d"), "blog/a.md", today), "has no `date:`")
    refused("a date that is a sentence", lambda: read_post(
        post("title: t\ndescription: d\ndate: last Tuesday"), "blog/a.md", today),
        "which is not a day")
    refused("a date in quotes stays a string", lambda: read_post(
        post('title: t\ndescription: d\ndate: "2026-09-13"'), "blog/a.md", today),
        "which is not a day")
    refused("a date with a time on it", lambda: read_post(
        post("title: t\ndescription: d\ndate: 2026-09-13 08:00:00"),
        "blog/a.md", today), "which is not a day")
    refused("tomorrow", lambda: read_post(
        post("title: t\ndescription: d\ndate: 2026-09-19"), "blog/a.md", today),
        "which is after today")
    refused("next year", lambda: read_post(
        post("title: t\ndescription: d\ndate: 2027-01-01"), "blog/a.md", today),
        "which is after today")
    refused("no front matter at all", lambda: read_post(
        "# A post\n", "blog/a.md", today), "has no front matter")
    refused("no title", lambda: read_post(
        post("description: d\ndate: 2026-09-13"), "blog/a.md", today),
        "has no `title:`")
    refused("no description", lambda: read_post(
        post("title: t\ndate: 2026-09-13"), "blog/a.md", today),
        "has no `description:`")

    # 3. The list: newest first, a heading per year, and the placeholder.
    entries = [
        ("blog/older.md", {"date": datetime.date(2025, 12, 31), "title": "Older",
                           "description": "From the year before."}),
        ("blog/first.md", {"date": datetime.date(2026, 9, 9), "title": "First",
                           "description": "The first one."}),
        ("blog/second.md", {"date": datetime.date(2026, 9, 13),
                            "title": "Second [and a ] in it",
                            "description": "The second one."}),
    ]
    expect("the list", posts_list(entries).split("\n"), [
        "## 2026", "",
        "**13 September 2026** — [Second [and a \\] in it](second.md)", "",
        "The second one.", "",
        "**9 September 2026** — [First](first.md)", "",
        "The first one.", "",
        "## 2025", "",
        "**31 December 2025** — [Older](older.md)", "",
        "From the year before.",
    ])
    refused("an index with no post to list", lambda: posts_list([]),
            "no post to list")

    # 4. The three files this hook writes into, each read for the thing it must
    #    carry. A template that stops saying it is the failure on_post_build
    #    exists for, and it cannot run here.
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def reads(path: str) -> str:
        with open(os.path.join(root, path), encoding="utf-8") as fh:
            return fh.read()

    expect(f"docs/{INDEX} carries the placeholder",
           bool(_SLOT.search(reads(f"docs/{INDEX}"))), True)
    card = reads("overrides/partials/seo.html")
    expect("partials/seo.html writes article:published_time",
           "article:published_time" in card, True)
    expect("partials/seo.html writes article:modified_time",
           "article:modified_time" in card, True)
    expect("partials/opening.html writes the date as a <time>",
           '<time datetime="{{ page.meta.published }}">'
           in reads("overrides/partials/opening.html"), True)

    # 5. What on_post_build reads, against what it is given: the card as the
    #    template writes it, and the two ways it stops matching.
    built = ('<meta property="og:url" content="https://digline.dev/blog/a/">\n'
             '<meta property="article:published_time" content="2026-09-13">\n')
    expect("the published_time read back",
           _PUBLISHED.search(built).group(1), "2026-09-13")
    expect("a card with no published_time", _PUBLISHED.search(
        '<meta property="og:url" content="x">'), None)
    expect("another post's date read back", _PUBLISHED.search(
        '<meta property="article:published_time" content="2026-09-09">'
    ).group(1), "2026-09-09")

    for failure in failures:
        print(f"blog selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("blog selftest: a post's date read and folded back, the list newest "
          "first under a heading per year, and a missing, unparseable, quoted, "
          "timed or future date each refused")
    return 0


if __name__ == "__main__":
    raise SystemExit(selftest())
