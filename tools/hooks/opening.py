"""The opening band of the reading pages — why, start, about, contact.

Each of those pages opens the way the home does: a band on the home's ground
(--wash) with the title in the home's title style, an optional kicker above it,
and the first paragraph under it as the lede. The words stay where they are, in
the page's Markdown: `# Title`, then the first paragraph. This hook takes the
rendered page apart at that seam and hands the template three pieces, so no
page has to repeat its title or move its first paragraph into front matter.

    kicker:  `kicker:` in the page's front matter, or nothing
    title:   the inside of the page's first <h1>, its anchor included
    title_id the <h1>'s id, so #why still lands on the title
    lede:    the inside of the first <p> after it
    body:    everything after that paragraph

The template gets `opening` (the first four) and `body`. A reading page whose
content does not start with an <h1> and a <p> fails the build: the band would
otherwise be empty, or would swallow the wrong paragraph.
"""

from __future__ import annotations

import re

from mkdocs.exceptions import PluginError

# The templates that open with the band.
READING = {"why.html", "start.html", "about.html", "contact.html"}

_OPENING = re.compile(
    r"\A\s*<h1(?P<attrs>[^>]*)>(?P<title>.*?)</h1>\s*<p>(?P<lede>.*?)</p>(?P<body>.*)\Z",
    re.S,
)
_ID = re.compile(r'\bid="([^"]*)"')


def split(content: str, source: str) -> tuple[dict, str]:
    match = _OPENING.match(content)
    if not match:
        raise PluginError(
            f"opening: {source} must start with `# Title` and a first paragraph — "
            "they become the page's opening band."
        )
    title_id = _ID.search(match.group("attrs"))
    return {
        "title": match.group("title"),
        "title_id": title_id.group(1) if title_id else None,
        "lede": match.group("lede"),
    }, match.group("body")


def on_page_context(context, page, config, nav, **kwargs):
    if page.meta.get("template") in READING:
        opening, body = split(page.content or "", page.file.src_uri)
        opening["kicker"] = page.meta.get("kicker")
        context["opening"] = opening
        context["body"] = body
    return context
