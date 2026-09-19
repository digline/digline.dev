#!/usr/bin/env -S uv run python
"""The bar is four slots wide on every page, so the sections never move.

overrides/partials/header.html is one bar for both shells, and its actions are
four round buttons in this order: search, language, GitHub, the theme. What a
slot holds depends on the page; that it is there does not. Search is the icon
on a page with an index to search — the documentation, the Material shell —
and an empty slot on a presentation page. Language is the menu on a page with
translations, whichever shell, and an empty slot on every other page. An empty
slot is an inert <span class="dg-slot"> the size of a button. This reads the
build and fails on:

  * a bar that is not those four slots in that order: one missing, one more,
    two swapped, anything else in .dg-actions (Material's .md-search, the
    field the icon opens, sits beside the icon and is not a slot);
  * a documentation page whose search slot is empty, or without the
    ``__search`` checkbox the icon toggles, or with more than one: the icon is
    a <label for="__search">, and the checkbox is what opens the overlay, so
    one without the other is a button that does nothing;
  * a presentation page whose search slot is not empty, or carrying any
    ``for="__search"`` or the checkbox anywhere on the page: there is no index
    behind it there, and a label that toggles a checkbox no page has is a dead
    button;
  * a page with translations — hreflang links in its <head> — whose language
    slot is empty, and a page without them whose language slot holds a menu;
    a menu with fewer than two languages in it, which offers nothing (never a
    menu with "English" alone);
  * an empty slot that is not inert: not a <span>, not aria-hidden="true",
    with a tabindex, a role or an href, or anything inside it;
  * a page that is neither shell, or both at once, which means the marker this
    reads has moved and the rest of this check is measuring nothing;
  * a site with no page, no documentation page or no presentation page at all,
    which cannot be right and would pass by counting nothing.

The page is parsed, not searched: a ``for="__search"`` inside a script is a
string, not an attribute, and is not counted.

    usage: tools/check-bar.py site
           tools/check-bar.py --selftest

--selftest needs no build: it writes a five-page site — a documentation page
with translations and one without, a presentation page with translations and
one without, and a translation — checks that it passes and counts what it
found, then plants each failure in turn and checks that each is refused.
"""

from __future__ import annotations

import os
import sys
import tempfile
from html.parser import HTMLParser

# What each shell leaves in the page. The Material one marks its content, the
# presentation one its main: one of the two, never both.
DOCS_MARKER = ("div", "data-md-component", "content")
PAGE_MARKER = "dg-page"

ACTIONS = "dg-actions"
BUTTON = "md-header__button"  # what the bar's own icon is, next to the overlay's labels
LANG = "dg-lang"
LANG_ITEM = "dg-lang__item"
SLOT = "dg-slot"
TOGGLE = "__search"

# The four slots, in order: what may be in each.
SLOTS = (("search", "empty search"), ("language", "empty language"), ("github",), ("theme",))

# Tags that close themselves whether or not the HTML says so: counted as open
# would leave the parser inside .dg-actions for the rest of the page.
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


def _classes(attrs: dict[str, str | None]) -> list[str]:
    return (attrs.get("class") or "").split()


def _kind(tag: str, attrs: dict[str, str | None]) -> str | None:
    """What a child of .dg-actions is, as a slot; None for the one thing beside
    the slots, Material's .md-search."""
    classes = _classes(attrs)
    if "md-search" in classes:
        return None
    if tag == "label" and attrs.get("for") == TOGGLE and BUTTON in classes:
        return "search"
    if tag == "details" and LANG in classes:
        return "language"
    if SLOT in classes:
        if f"{SLOT}--search" in classes:
            return "empty search"
        if f"{SLOT}--lang" in classes:
            return "empty language"
        return "empty ?"
    if tag == "a" and "dg-icon" in classes:
        return "github"
    if tag == "button" and attrs.get("id") == "__dg_palette":
        return "theme"
    return f"<{tag} class={' '.join(classes) or '-'}>"


class _Page(HTMLParser):
    """What the bar of one page is made of."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.docs = False
        self.presentation = False
        self.checkboxes = 0
        self.labels = 0       # <label for="__search"> anywhere on the page, the overlay's included
        self.alternates = 0   # <link rel="alternate" hreflang>: the page has translations
        self.slots: list[str] = []
        self.menu_items: list[int] = []  # the languages in each menu
        self.inert: list[str] = []       # what is wrong with the empty slots
        self._depth = 0       # how deep we are inside .dg-actions, 0 outside it
        self._slot = 0        # the depth of the empty slot we are inside, 0 when none

    def handle_starttag(self, tag, attrs, void=False):
        attrs = dict(attrs)
        classes = _classes(attrs)
        void = void or tag in VOID
        if tag == DOCS_MARKER[0] and attrs.get(DOCS_MARKER[1]) == DOCS_MARKER[2]:
            self.docs = True
        if PAGE_MARKER in classes:
            self.presentation = True
        if tag == "input" and attrs.get("id") == TOGGLE:
            self.checkboxes += 1
        if tag == "label" and attrs.get("for") == TOGGLE:
            self.labels += 1
        if tag == "link" and attrs.get("rel") == "alternate" and attrs.get("hreflang"):
            self.alternates += 1
        if self._slot:
            self.inert.append(f"<{tag}> inside it")
        if self._depth == 1:
            kind = _kind(tag, attrs)
            if kind is not None:
                self.slots.append(kind)
            if kind == "language":
                self.menu_items.append(0)
            if kind and kind.startswith("empty"):
                if tag != "span":
                    self.inert.append(f"a <{tag}>, not a <span>")
                if attrs.get("aria-hidden") != "true":
                    self.inert.append('no aria-hidden="true"')
                self.inert += [f"a {name}" for name in ("tabindex", "role", "href") if name in attrs]
                if not void:
                    self._slot = self._depth + 1
        if self._depth and LANG_ITEM in classes and self.menu_items:
            self.menu_items[-1] += 1
        if (self._depth or ACTIONS in classes) and not void:
            self._depth += 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs, void=True)

    def handle_data(self, data):
        if self._slot and data.strip():
            self.inert.append("text inside it")

    def handle_endtag(self, tag):
        if tag not in VOID and self._depth:
            if self._slot == self._depth:
                self._slot = 0
            self._depth -= 1


def check(site: str) -> tuple[list[str], dict[str, int]]:
    problems: list[str] = []
    counted = {"pages": 0, "documentation": 0, "presentation": 0, "icons": 0,
               "language menus": 0, "empty slots": 0}
    for folder, dirs, names in os.walk(site):
        dirs.sort()
        for name in sorted(names):
            if not name.endswith(".html"):
                continue
            path = os.path.join(folder, name)
            rel = os.path.relpath(path, site).replace(os.sep, "/")
            page = _Page()
            with open(path, encoding="utf-8") as fh:
                page.feed(fh.read())
            page.close()
            counted["pages"] += 1
            counted["icons"] += page.slots.count("search")
            counted["language menus"] += page.slots.count("language")
            counted["empty slots"] += sum(1 for s in page.slots if s.startswith("empty"))
            if page.docs == page.presentation:
                both = "both shells at once" if page.docs else "neither shell"
                problems.append(f"{rel}: {both}")
                continue
            if len(page.slots) != len(SLOTS) or any(got not in allowed for got, allowed in zip(page.slots, SLOTS)):
                problems.append(f"{rel}: the bar's slots are {page.slots}, and every page has four — search or "
                                "an empty slot, language or an empty slot, github, theme")
                continue
            search, language = page.slots[0], page.slots[1]
            if page.docs:
                counted["documentation"] += 1
                if search != "search":
                    problems.append(f"{rel}: an empty search slot on a documentation page, which has an index")
                if page.checkboxes != 1:
                    problems.append(f"{rel}: {page.checkboxes} #{TOGGLE} checkbox(es), not 1")
            else:
                counted["presentation"] += 1
                if search != "empty search":
                    problems.append(f"{rel}: a search icon on a presentation page, which has no index")
                elif page.labels:
                    problems.append(f'{rel}: {page.labels} <label for="{TOGGLE}"> on a page without search')
                if page.checkboxes:
                    problems.append(f"{rel}: a #{TOGGLE} checkbox on a page without search")
            if page.alternates and language != "language":
                problems.append(f"{rel}: translations (hreflang in its head), and its language slot is empty")
            if not page.alternates and language == "language":
                problems.append(f"{rel}: a language menu, and no translation (no hreflang in its head)")
            for count in page.menu_items:
                if count < 2:
                    problems.append(f"{rel}: a language menu with {count} language(s), which offers nothing")
            for wrong in page.inert:
                problems.append(f"{rel}: an empty slot that is not inert — {wrong}")
    if not counted["pages"]:
        problems.append(f"{site}: no page at all")
    elif not counted["documentation"]:
        problems.append(f"{site}: no documentation page at all, so no icon was asked for")
    elif not counted["presentation"]:
        problems.append(f"{site}: no presentation page at all, so no bar was compared")
    return problems, counted


ICON = f'<label class="{BUTTON} md-icon" for="{TOGGLE}" title="Search"><svg></svg></label>'
SEARCH_FIELD = (f'<div class="md-search"><label class="md-search__overlay" for="{TOGGLE}"></label>'
                '<input class="md-search__input"></div>')
ITALIAN = f'<li><a class="{LANG_ITEM}" href="../it/" hreflang="it">Italiano</a></li>'
MENU = (f'<details class="{LANG}"><summary class="dg-icon dg-lang__summary">EN</summary>'
        f'<ul class="dg-lang__menu"><li><a class="{LANG_ITEM}" href="./" hreflang="en">English</a></li>'
        f'{ITALIAN}</ul></details>')
EMPTY_SEARCH = f'<span class="{SLOT} {SLOT}--search" aria-hidden="true"></span>'
EMPTY_LANG = f'<span class="{SLOT} {SLOT}--lang" aria-hidden="true"></span>'
GITHUB = '<a class="dg-icon" href="https://github.com/digline/digline"></a>'
THEME = '<button class="dg-icon" id="__dg_palette"></button>'
ALTERNATES = ('<link rel="alternate" hreflang="en" href="https://digline.dev/x/">'
              '<link rel="alternate" hreflang="it" href="https://digline.dev/it/x/">')
CHECKBOX = f'<input class="md-toggle" type="checkbox" id="{TOGGLE}" autocomplete="off">'


def _docs(slots: str, head: str = "") -> str:
    return (f'<!doctype html><html lang="en"><head>{head}</head><body>{CHECKBOX}'
            f'<header><div class="{ACTIONS}">{slots}</div></header>'
            '<div class="md-content" data-md-component="content"><article>Guide</article></div>'
            "</body></html>")


def _page(slots: str, head: str = "", lang: str = "en", title: str = "Start here") -> str:
    return (f'<!doctype html><html lang="{lang}"><head>{head}</head><body>'
            f'<header><div class="{ACTIONS}">{slots}</div></header>'
            f'<main class="dg-page"><h1>{title}</h1></main>'
            f"<script>var s = 'for=\"{TOGGLE}\" is a string here';</script>"
            "</body></html>")


DOCS_PAGE = _docs(ICON + SEARCH_FIELD + EMPTY_LANG + GITHUB + THEME)
DOCS_TRANSLATED = _docs(ICON + SEARCH_FIELD + MENU + GITHUB + THEME, ALTERNATES)
PAGE_TRANSLATED = _page(EMPTY_SEARCH + MENU + GITHUB + THEME, ALTERNATES)
PAGE_ALONE = _page(EMPTY_SEARCH + EMPTY_LANG + GITHUB + THEME, title="Contact")
TRANSLATION = _page(EMPTY_SEARCH + MENU + GITHUB + THEME, ALTERNATES, lang="it", title="Da qui")


def selftest() -> int:
    failures: list[str] = []
    pages = {"product/guide": DOCS_PAGE, "handbook": DOCS_TRANSLATED, "start": PAGE_TRANSLATED,
             "contact": PAGE_ALONE, "it/start": TRANSLATION}
    with tempfile.TemporaryDirectory() as site:
        for folder in pages:
            os.makedirs(os.path.join(site, folder.replace("/", os.sep)))

        def write(**changed: str) -> None:
            for where, html in {**pages, **changed}.items():
                path = os.path.join(site, where.replace("/", os.sep), "index.html")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(html)

        write()
        problems, counted = check(site)
        if problems:
            failures.append(f"a clean site was refused: {problems}")
        expected = {"pages": 5, "documentation": 2, "presentation": 3, "icons": 2,
                    "language menus": 3, "empty slots": 5}
        if counted != expected:
            failures.append(f"the clean site should count {expected}, counted {counted}")

        planted = [
            ("three slots: the language slot missing", {"product/guide": DOCS_PAGE.replace(EMPTY_LANG, "")},
             "product/guide/index.html: the bar's slots are"),
            ("five slots: one empty slot more", {"contact": PAGE_ALONE.replace(EMPTY_LANG, EMPTY_LANG + EMPTY_LANG)},
             "contact/index.html: the bar's slots are"),
            ("the language slot before search", {"start": _page(MENU + EMPTY_SEARCH + GITHUB + THEME, ALTERNATES)},
             "start/index.html: the bar's slots are"),
            ("GitHub before the language slot", {"contact": _page(EMPTY_SEARCH + GITHUB + EMPTY_LANG + THEME)},
             "contact/index.html: the bar's slots are"),
            ("something else in the bar", {"contact": PAGE_ALONE.replace(THEME, THEME + "<span>x</span>")},
             "contact/index.html: the bar's slots are"),
            ("a documentation page with its search slot empty",
             {"product/guide": _docs(EMPTY_SEARCH + EMPTY_LANG + GITHUB + THEME)},
             "product/guide/index.html: an empty search slot on a documentation page"),
            ("a documentation page without the checkbox the icon toggles",
             {"product/guide": DOCS_PAGE.replace(CHECKBOX, "")},
             f"product/guide/index.html: 0 #{TOGGLE} checkbox(es), not 1"),
            ("a presentation page with the search icon", {"start": PAGE_TRANSLATED.replace(EMPTY_SEARCH, ICON)},
             "start/index.html: a search icon on a presentation page"),
            ('a <label for="__search"> below the bar of a presentation page',
             {"contact": PAGE_ALONE.replace("<h1>Contact</h1>", f'<label for="{TOGGLE}">Search</label>')},
             'contact/index.html: 1 <label for="__search"> on a page without search'),
            ("a presentation page carrying the checkbox",
             {"contact": PAGE_ALONE.replace("<body>", f"<body>{CHECKBOX}")},
             f"contact/index.html: a #{TOGGLE} checkbox on a page without search"),
            ("a documentation page with translations and its language slot empty",
             {"handbook": DOCS_TRANSLATED.replace(MENU, EMPTY_LANG)},
             "handbook/index.html: translations (hreflang in its head), and its language slot is empty"),
            ("a translation with its language slot empty",
             {"it/start": TRANSLATION.replace(MENU, EMPTY_LANG)},
             "it/start/index.html: translations (hreflang in its head), and its language slot is empty"),
            ("a language menu on a documentation page with no translation",
             {"product/guide": DOCS_PAGE.replace(EMPTY_LANG, MENU)},
             "product/guide/index.html: a language menu, and no translation"),
            ("a language menu on a presentation page with no translation",
             {"contact": PAGE_ALONE.replace(EMPTY_LANG, MENU)},
             "contact/index.html: a language menu, and no translation"),
            ('a menu with "English" alone', {"handbook": DOCS_TRANSLATED.replace(ITALIAN, "")},
             "handbook/index.html: a language menu with 1 language(s)"),
            ("an empty slot that is a <label>",
             {"contact": PAGE_ALONE.replace(
                 EMPTY_SEARCH, f'<label class="{SLOT} {SLOT}--search" aria-hidden="true"></label>')},
             "contact/index.html: an empty slot that is not inert — a <label>, not a <span>"),
            ("an empty slot a screen reader reads",
             {"contact": PAGE_ALONE.replace(EMPTY_LANG, f'<span class="{SLOT} {SLOT}--lang"></span>')},
             'contact/index.html: an empty slot that is not inert — no aria-hidden="true"'),
            ("an empty slot a keyboard reaches",
             {"product/guide": DOCS_PAGE.replace(
                 EMPTY_LANG, f'<span class="{SLOT} {SLOT}--lang" aria-hidden="true" tabindex="0"></span>')},
             "product/guide/index.html: an empty slot that is not inert — a tabindex"),
            ("an empty slot with words in it",
             {"contact": PAGE_ALONE.replace(EMPTY_LANG, f'<span class="{SLOT} {SLOT}--lang" aria-hidden="true">EN</span>')},
             "contact/index.html: an empty slot that is not inert — text inside it"),
            ("a page in neither shell",
             {"contact": PAGE_ALONE.replace('<main class="dg-page">', "<main>")},
             "contact/index.html: neither shell"),
            ("a page in both shells at once",
             {"contact": PAGE_ALONE.replace('<main class="dg-page">',
                                            '<main class="dg-page"><div data-md-component="content"></div>')},
             "contact/index.html: both shells at once"),
        ]
        for label, changed, needle in planted:
            write(**changed)
            problems, _ = check(site)
            if not any(needle in problem for problem in problems):
                failures.append(f"{label}: not refused ({problems})")
            else:
                print(f"bar selftest: refused, as it must — {label}")
            write()

        # A site with only one kind of page counts nothing worth counting.
        for label, kept, needle in (
            ("a site with no documentation page", ("start", "contact", "it/start"), "no documentation page at all"),
            ("a site with no presentation page", ("product/guide", "handbook"), "no presentation page at all"),
        ):
            write()
            for where in pages:
                if where not in kept:
                    os.remove(os.path.join(site, where.replace("/", os.sep), "index.html"))
            problems, _ = check(site)
            if not any(needle in problem for problem in problems):
                failures.append(f"{label}: not refused ({problems})")
            else:
                print(f"bar selftest: refused, as it must — {label}")
            write()

        for where in pages:
            os.remove(os.path.join(site, where.replace("/", os.sep), "index.html"))
        problems, _ = check(site)
        if not any("no page at all" in problem for problem in problems):
            failures.append(f"an empty site: not refused ({problems})")
        else:
            print("bar selftest: refused, as it must — an empty site")

    for failure in failures:
        print(f"bar selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("bar selftest: a clean site passes — two documentation pages, one with translations, and three "
          "presentation pages, one without, every bar four slots, a for=\"__search\" in a <script> not "
          "counted; every planted failure refused")
    return 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    if len(argv) != 1:
        print(__doc__.split("\n\n")[-2], file=sys.stderr)
        return 2
    problems, counted = check(argv[0])
    for problem in problems:
        print(f"bar: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"bar: {counted['pages']} pages, every bar four slots — {counted['documentation']} with the "
          f"Material shell, each with the search icon and its checkbox; {counted['presentation']} "
          f"presentation pages, search's slot empty; {counted['language menus']} language menu(s), each on "
          f"a page with translations; {counted['empty slots']} empty slots, every one inert")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
