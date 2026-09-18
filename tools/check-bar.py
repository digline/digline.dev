#!/usr/bin/env -S uv run python
"""The bar is three buttons wide on every page, so the entries never move.

overrides/partials/header.html is one bar for both shells. The first of the
three buttons is search where there is something to search, and the language
menu everywhere else — every presentation page is translated, and spends that
slot on the menu. This reads the build and fails when that is not what was
written:

  * a documentation page — the Material shell — without the search icon in
    .dg-actions, or without the ``__search`` checkbox the icon toggles, or with
    more than one of either: the icon is a <label for="__search">, and the
    checkbox is what opens the overlay, so one without the other is a button
    that does nothing;
  * a page outside that shell — every presentation page, translations
    included — carrying any ``for="__search"`` at all, in the bar or anywhere
    below it: there is no search index behind it there, and a label that
    toggles a checkbox no page has is a dead button;
  * a presentation page without the language menu, or with more than one: the
    first slot is held once, by search or by the menu. A new presentation page
    with no translations trips this, and that is the point — it would leave the
    slot empty and start the movement again, so it is either translated or
    given something inert to hold the space with;
  * a documentation page carrying the language menu, which already spends that
    slot on the icon;
  * a page that is neither shell, or both at once, which means the marker this
    reads has moved and the rest of this check is measuring nothing;
  * a site with no page, no documentation page or no presentation page at all,
    which cannot be right and would pass by counting nothing.

The page is parsed, not searched: a ``for="__search"`` inside a script is a
string, not an attribute, and is not counted.

    usage: tools/check-bar.py site
           tools/check-bar.py --selftest

--selftest needs no build: it writes a four-page site — a documentation page,
two presentation pages and a translation of one of them — checks that it
passes and counts what it found, then plants each failure in turn and checks
that each is refused.
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
TOGGLE = "__search"

# Tags that close themselves whether or not the HTML says so: counted as open
# would leave the parser inside .dg-actions for the rest of the page.
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


def _classes(attrs: dict[str, str | None]) -> list[str]:
    return (attrs.get("class") or "").split()


class _Page(HTMLParser):
    """What the bar of one page is made of."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.docs = False
        self.presentation = False
        self.checkboxes = 0
        self.icons = 0  # the bar's own <label class="md-header__button" for="__search">
        self.labels = 0  # <label for="__search"> anywhere on the page, the overlay's included
        self.langs = 0
        self._depth = 0  # how deep we are inside .dg-actions, 0 outside it

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
            if BUTTON in classes:
                self.icons += 1
        if LANG in classes and self._depth:
            self.langs += 1
        if (self._depth or ACTIONS in classes) and not void:
            self._depth += 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs, void=True)

    def handle_endtag(self, tag):
        if tag not in VOID and self._depth:
            self._depth -= 1


def check(site: str) -> tuple[list[str], dict[str, int]]:
    problems: list[str] = []
    counted = {"pages": 0, "documentation": 0, "presentation": 0, "icons": 0,
               "language menus": 0}
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
            counted["icons"] += page.icons
            counted["language menus"] += page.langs
            if page.docs == page.presentation:
                both = "both shells at once" if page.docs else "neither shell"
                problems.append(f"{rel}: {both}")
                continue
            if page.docs:
                counted["documentation"] += 1
                if page.icons != 1:
                    problems.append(f"{rel}: {page.icons} search icon(s) in .{ACTIONS}, not 1")
                if page.checkboxes != 1:
                    problems.append(f"{rel}: {page.checkboxes} #{TOGGLE} checkbox(es), not 1")
                if page.langs:
                    problems.append(f"{rel}: the language menu on a page that has search")
            else:
                counted["presentation"] += 1
                if page.labels:
                    where = "in the bar" if page.icons else "below the bar"
                    problems.append(f'{rel}: {page.labels} <label for="{TOGGLE}"> {where}, '
                                    "on a page without search")
                if page.checkboxes:
                    problems.append(f"{rel}: a #{TOGGLE} checkbox on a page without search")
                if page.langs != 1:
                    problems.append(f"{rel}: {page.langs} language menu(s) in .{ACTIONS}, not 1 — "
                                    "the first slot is held once, by search or by the menu")
    if not counted["pages"]:
        problems.append(f"{site}: no page at all")
    elif not counted["documentation"]:
        problems.append(f"{site}: no documentation page at all, so no icon was asked for")
    elif not counted["presentation"]:
        problems.append(f"{site}: no presentation page at all, so no bar was compared")
    return problems, counted


ICON = f'<label class="{BUTTON} md-icon" for="{TOGGLE}" title="Search"><svg></svg></label>'
MENU = (f'<details class="{LANG}"><summary>EN</summary>'
        '<ul><li><a href="../it/">Italiano</a></li></ul></details>')

DOCS_PAGE = ('<!doctype html><html lang="en"><body>'
             f'<input class="md-toggle" type="checkbox" id="{TOGGLE}" autocomplete="off">'
             f'<header><div class="{ACTIONS}">{ICON}'
             f'<div class="md-search"><label class="md-search__overlay" for="{TOGGLE}"></label>'
             '<input class="md-search__input"></div>'
             '<a class="dg-icon" href="https://github.com/digline/digline"></a>'
             '<button class="dg-icon" id="__dg_palette"></button>'
             "</div></header>"
             '<div class="md-content" data-md-component="content"><article>Handbook</article></div>'
             "</body></html>")

PAGE = ('<!doctype html><html lang="{lang}"><body>'
        f'<header><div class="{ACTIONS}">{MENU}'
        '<a class="dg-icon" href="https://github.com/digline/digline"></a>'
        '<button class="dg-icon" id="__dg_palette"></button>'
        "</div></header>"
        '<main class="dg-page"><h1>{title}</h1></main>'
        f"<script>var s = 'for=\"{TOGGLE}\" is a string here';</script>"
        "</body></html>")


def selftest() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as site:
        for folder in ("handbook", "start", "contact", os.path.join("it", "start")):
            os.makedirs(os.path.join(site, folder))
        start = PAGE.format(lang="en", title="Start here")
        contact = PAGE.format(lang="en", title="Contact")
        translated = PAGE.format(lang="it", title="Da qui")
        pages = {"handbook": DOCS_PAGE, "start": start, "contact": contact, "it/start": translated}

        def write(**changed: str) -> None:
            for where, html in {**pages, **changed}.items():
                path = os.path.join(site, where.replace("/", os.sep), "index.html")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(html)

        write()
        problems, counted = check(site)
        if problems:
            failures.append(f"a clean site was refused: {problems}")
        expected = {"pages": 4, "documentation": 1, "presentation": 3, "icons": 1,
                    "language menus": 3}
        if counted != expected:
            failures.append(f"the clean site should count {expected}, counted {counted}")

        planted = [
            ("a presentation page with the icon",
             {"start": start.replace(MENU, ICON + MENU)},
             'start/index.html: 1 <label for="__search"> in the bar'),
            ("a translation with the icon",
             {"it/start": translated.replace(MENU, ICON + MENU)},
             'it/start/index.html: 1 <label for="__search"> in the bar'),
            ("a documentation page without the icon",
             {"handbook": DOCS_PAGE.replace(ICON, "")},
             "handbook/index.html: 0 search icon(s)"),
            ('a <label for="__search"> below the bar of a page without search',
             {"contact": contact.replace("<h1>Contact</h1>", f'<label for="{TOGGLE}">Search</label>')},
             'contact/index.html: 1 <label for="__search"> below the bar'),
            ("a presentation page with no translations, so nothing holding the first slot",
             {"contact": contact.replace(MENU, "")},
             "contact/index.html: 0 language menu(s)"),
            ("a presentation page holding the first slot twice",
             {"start": start.replace(MENU, MENU + MENU)},
             "start/index.html: 2 language menu(s)"),
            ("a language menu outside the bar, which holds nothing in it",
             {"contact": contact.replace(MENU, "").replace("<h1>Contact</h1>", MENU)},
             "contact/index.html: 0 language menu(s)"),
            ("the language menu on a page that has search",
             {"handbook": DOCS_PAGE.replace(ICON, ICON + MENU)},
             "the language menu on a page that has search"),
            ("a documentation page without the checkbox the icon toggles",
             {"handbook": DOCS_PAGE.replace(
                 f'<input class="md-toggle" type="checkbox" id="{TOGGLE}" autocomplete="off">', "")},
             f"0 #{TOGGLE} checkbox(es), not 1"),
            ("a presentation page carrying the checkbox",
             {"contact": contact.replace("<body>", f'<body><input type="checkbox" id="{TOGGLE}">')},
             f"a #{TOGGLE} checkbox on a page without search"),
            ("a page in neither shell",
             {"contact": contact.replace('<main class="dg-page">', "<main>")},
             "contact/index.html: neither shell"),
            ("a page in both shells at once",
             {"contact": contact.replace('<main class="dg-page">',
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

        # A site with only one kind of page counts nothing worth counting.
        for label, kept, needle in (
            ("a site with no documentation page", ("start", "contact", "it/start"), "no documentation page at all"),
            ("a site with no presentation page", ("handbook",), "no presentation page at all"),
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
    print("bar selftest: a clean site passes with 1 documentation page carrying the icon and "
          "3 presentation pages on the language menu, a for=\"__search\" in a <script> not among "
          "them; every planted failure refused")
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
    print(f"bar: {counted['pages']} pages — {counted['documentation']} with the Material shell, "
          f"every one carrying the search icon and its checkbox and no language menu; "
          f"{counted['presentation']} presentation pages, none carrying either, every one "
          f"holding that same slot with the language menu")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
