"""Which languages the site is translated into, and which of its pages.

English is the original, and the only language of the documentation, the
comparison and the blog. The six presentation pages and the Handbook's nine
may have a translation in each of LANGUAGES, written in docs/<lang>/ at the
same path as the English page it translates, and served at the same path under
/<lang>/:

    docs/why.md                   →  /why/
    docs/it/why.md                →  /it/why/
    docs/it/handbook/02-cases.md  →  /it/handbook/02-cases/

A translation's front matter says what it is:

    lang: it                 the language, the name of its folder
    translation_of: why.md   the English page, one of PAGES, at the same path
    description: …           its own, in its language
    search:
      exclude: true          translations are not in the search index

tools/hooks/translations.py reads these, refuses a translation that does not
hold together, and writes the hreflang links; llms.py, check-llms.py and
check-translate.py read the prefixes here. Nothing in this file imports a
dependency: check-llms.py runs on the system's Python.
"""

from __future__ import annotations

ORIGINAL = "en"

# The languages a presentation page may be translated into, in the order their
# hreflang links are written.
LANGUAGES = ("it", "de", "es")

# Each language by its own name, as the language menu lists it: a reader looks
# for their language in their language. Not in the catalogs, which say things
# in one language; these say the same thing in every page.
NAMES = {"en": "English", "it": "Italiano", "de": "Deutsch", "es": "Español"}

# The pages that may be translated, by their source path under docs/: the six
# presentation pages, and the Handbook's index and eight chapters, in the
# nav's order. The presentation pages carry the language menu in the bar; the
# Handbook is documentation, whose bar holds search in that slot, and says its
# other languages elsewhere.
PRESENTATION_PAGES = ("index.md", "start.md", "why.md", "about.md", "contact.md", "agents.md")
HANDBOOK_PAGES = (
    "handbook/index.md",
    "handbook/01-what-you-are-shipping.md",
    "handbook/02-cases.md",
    "handbook/03-ground-truth.md",
    "handbook/04-checks.md",
    "handbook/05-the-judge.md",
    "handbook/06-the-reference.md",
    "handbook/07-maintenance.md",
    "handbook/08-for-teams-building-for-others.md",
)
PAGES = PRESENTATION_PAGES + HANDBOOK_PAGES


def language_of(path: str) -> str | None:
    """The language a source path or a site path is written in, when it is under
    one of the LANGUAGES' folders: "it/why.md", "it/why/index.html" → "it"."""
    first = path.replace("\\", "/").lstrip("/").split("/", 1)[0]
    return first if first in LANGUAGES and "/" in path.lstrip("/") else None


def is_translation(path: str) -> bool:
    return language_of(path) is not None


def page_url(src_uri: str) -> str:
    """The URL path of a page under the site root, as mkdocs writes it:
    "index.md" → "", "why.md" → "why/", "it/index.md" → "it/"."""
    stem = src_uri[: -len(".md")]
    if stem == "index":
        return ""
    if stem.endswith("/index"):
        return stem[: -len("index")]
    return stem + "/"
