"""The translations of the presentation pages and the Handbook: refused unless
they hold together, and linked to their originals with hreflang.

tools/languages.py says which languages and which pages, and how a translation
is written: docs/<lang>/<page>, its front matter naming its language and its
original. This hook does three things with them.

── before anything renders (on_files) ───────────────────────────────────────
Every file under a language's folder is read, and the build fails when

  * it is not one of the pages that may be translated (languages.PAGES: the
    six presentation pages and the Handbook's nine), at the path of its
    original: docs/it/why.md and docs/it/handbook/02-cases.md, not
    docs/it/perche.md nor docs/it/product/guide.md;
  * its ``lang:`` is not the name of its folder, or that language has no
    catalog, i18n/<lang>.yml, for the words the templates show around it;
  * its ``translation_of:`` is missing, is not the path it stands at, or names
    an original the build does not have;
  * its ``template:`` is not its original's, so it would not be laid out as
    the page it translates;
  * it has no ``description:`` of its own;
  * it is not ``search: exclude: true`` — the search index is the English
    site's.

── while pages render (on_page_context) ──────────────────────────────────────
An English page with translations, and each of its translations, gets
``page.meta.hreflang``: one absolute link per language the page exists in —
English first, then languages.LANGUAGES' order — and ``x-default``, the
English page. overrides/partials/seo.html writes them into <head>. A page
with no translation gets nothing, and its HTML is what it was.

The same pages get ``page.meta.language_switch``, the language menu in the
bar (overrides/partials/header.html): one entry per hreflang link but
x-default — the same list, so the menu and the links cannot disagree — each
language by its own name (languages.NAMES), the page's own marked current.
Every page with translations, a presentation page or a Handbook page: the menu
has a slot of its own in the bar, the second, on every page of the site
(tools/check-bar.py).

── previous and next on a translation (on_files, on_nav, on_page_context) ────
A translation is not in the nav (not_in_nav), so it has no place of its own
in a sequence. overrides/main.html gives it its original's: the same previous
and next, which localize() below then sends to their
translations where they exist. What the template cannot know is what those
pages are called in the page's language, so each translation of a page read
in order gets ``page.meta.pager_titles``: the English source path of every
page translated into its language → its title there. That title is the
translation's <h1> up to its first colon — "2. Casi", not the whole of "2. Casi:
l'asset che nessuno costruisce" — because that is how the English names its
pages in the nav, and the build fails on a Handbook chapter whose nav title is
not its <h1> up to the colon (on_nav): the rule is read off the English, not
assumed. A page with no translation in the language keeps its English title,
marked lang="en".

── the drawer and the sidebar on a translation (on_page_context) ─────────────
Material draws the site's nav in the drawer, and on a wide screen the part of
it the page is in, in the sidebar; for a translation that is the whole
English nav, every entry of it. So a translation of a Handbook page gets ``page.meta.translation_nav``
instead, and overrides/partials/nav.html draws it with Material's own macro:
the pages translated into its language, in the nav's order, under their own
titles; the Handbook whole — each chapter under its translated title, or in
English, marked EN, until it is translated — open, the page itself current,
with its table of contents; and last, the documentation, which is English,
which its words say. A page translated tomorrow is in it the day it is, with nothing to
change: the tree is read from the translations there are.

Wherever a link leaves the page's language for English — an entry of that
tree, the pager's previous or next — its title says so: lang="en" on the
words, and the EN mark after them, which the reader sees and a screen reader
does not read (the link's lang says it).

── the ids of a translation's headings (on_page_content, on_page_context) ───
A link written for an English page's section — /why/#a-prompt-is-not-code —
leads, once sent to the translation, to the same section. A translation up to
date with its original (its source_sha is the original's now) gets its
original's heading ids, by position — its permalinks, its own #links and its
toc with them — and the build fails when its headings are not as many, at the
same levels (tools/check-translations.py's d) says the same after the build).
A translation behind its original keeps its own ids, whatever its headings:
they may not be the original's any more, and the English site stays free to
change.

── as each translation is written (on_post_page) ─────────────────────────────
A reader who chose a language stays in it. Every <a href> of a translation —
the bar, the logo, the hero, the body, the closing band, the footer — that
leads to an English page with a translation in the page's language is sent to
that translation instead: /why/ becomes /it/why/ on an Italian page, and a link
to a page with none, the documentation's, stays English. The #fragment and the
?query are kept, and so is the link's form: relative (written from the site's
root, as base_url writes it), root-relative, or absolute to site_url. Which
pages have a translation is not written anywhere: it is the files in
docs/<lang>/ (translations_in), so a page translated tomorrow is covered
without a change here. Links with hreflang — the language menu, and the
notice's link to the original — are left alone: they lead to another language
on purpose.

── after the build (on_post_build) ──────────────────────────────────────────
Every page in site/ is read again, and the build fails when its hreflang
links are not exactly the ones its group should have — none, for a page with
no translation — or when a translation's <html lang> or og:locale is not its
language. And every page under a language's folder fails it when one of its
<a href> without hreflang — relative, root-relative or absolute to site_url,
with or without its final slash, normalized first — leads to the English page
of a page translated into that language, or to a path under /<lang>/ that
site/ does not have (link_problems).

Every page of site/, English or not, fails it when a link with a #fragment
leads to a page site/ has and that page has no such id — a warning only, not
a failure, when the page is a translation behind its original — or when a
home, English or translated, has no id="install" (STABLE_IDS: the footer and
other sites link to it) (anchor_problems).

And every page of site/, the 404 included, fails it on an href that starts
with // (protocol_relative_problems): a link relative to the protocol leads to
another host — //why/ to a host named "why" — which is what {{ base_url }}/why/
wrote on the 404 until the templates wrote base_url.rstrip('/').

    usage: tools/hooks/translations.py --selftest

--selftest needs docs/product/ synced (`make docs`). It checks each refusal
above on front matter of its own, then copies the site into a temporary
directory, adds the fake translations of tools/testdata/translations/ — their
front matter from there, their text each English page as it is today,
pseudo-translated and stamped by tools/translation.py — with a catalog per
language copied from en.yml, builds it with --strict, and reads
the result: the hreflang of every page, the language of the translations, the
bar, the footer and the closing band on a translation, the search index,
llms.txt, the sitemap, check-llms.py, check-translate.py and check-glyphs.py.
Then it tampers with the built hreflang and checks that each change is
refused; plants links in the built Italian home and checks that the link gate
refuses each one it must (/why/, https://digline.dev/why/, ../why/, /why,
../why/index.html#x, /it/docs/) and passes the others (/it/why/, /docs/);
plants links with #fragments and renames ids, and checks that the anchor
gate refuses a missing id, a home without id="install" and a renamed id on
/product/metrics/, and passes /it/why/#<an English id>; checks the ids of the
up-to-date Why translations are English Why's, and refuses a heading fewer or
at another level; adds an Italian Start in the test alone, with links written in a
translation's Markdown, and makes Italian Why behind its original with two
headings swapped, builds again and checks that links are rewritten and gated
with no change here, and that Italian Why keeps its own ids with warnings, not
errors; builds with an up-to-date German Why a heading fewer, refused; and
builds once more with a translation that has no description.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

from urllib.parse import unquote, urljoin, urlsplit

import yaml
from markupsafe import Markup, escape
from mkdocs.exceptions import PluginError

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
import catalog  # noqa: E402  tools/catalog.py
import languages  # noqa: E402  tools/languages.py

_FRONT_MATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*\r?\n", re.S)

X_DEFAULT = "x-default"


def front_matter(path: str) -> dict:
    """A file's front matter; {} when it has none."""
    try:
        with open(path, encoding="utf-8") as fh:
            match = _FRONT_MATTER.match(fh.read())
    except OSError:
        return {}
    if not match:
        return {}
    data = yaml.safe_load(match.group(1))
    return data if isinstance(data, dict) else {}


def refusals(src_uri: str, meta: dict, originals: dict[str, dict], catalogs: set[str]) -> list[str]:
    """What is wrong with one translation, as the build says it.

    src_uri    its path under docs/, under a language's folder
    meta       its front matter
    originals  the English presentation pages the build has: path → front matter
    catalogs   the languages that have an i18n/<lang>.yml
    """
    where = f"docs/{src_uri}"
    lang = languages.language_of(src_uri)
    rest = src_uri.split("/", 1)[1]
    if rest not in languages.PAGES:
        return [f"{where}: only the presentation pages and the Handbook are translated ({', '.join(languages.PAGES)}), "
                f"each at its original's path, and {rest} is not one of them"]
    problems = []
    if meta.get("lang") != lang:
        problems.append(f"{where}: lang is {meta.get('lang')!r}, and the page is in the {lang}/ folder")
    elif lang not in catalogs:
        problems.append(f"{where}: lang {lang} has no catalog, i18n/{lang}.yml, for the words around the page")
    original = meta.get("translation_of")
    if not original:
        problems.append(f"{where}: no translation_of, the English page it translates")
    elif original != rest:
        problems.append(f"{where}: translation_of is {original!r}, and a translation stands at its "
                        f"original's path, {rest}")
    elif original not in originals:
        problems.append(f"{where}: translation_of {original}, which the build does not have")
    elif meta.get("template") != originals[original].get("template"):
        problems.append(f"{where}: template is {meta.get('template')!r}, and {original} is laid out by "
                        f"{originals[original].get('template')!r}")
    if not str(meta.get("description") or "").strip():
        problems.append(f"{where}: no description of its own")
    search = meta.get("search")
    if not (isinstance(search, dict) and search.get("exclude") is True):
        problems.append(f"{where}: not `search: exclude: true` — the search index is the English site's")
    return problems


def hreflang(original: str, group: dict[str, str], site_url: str) -> list[dict[str, str]]:
    """The hreflang links of a page in a group: English, then each translation
    in LANGUAGES' order, then x-default, the English page.

    group  language → the source path of the translation in that language
    """
    base = site_url.rstrip("/") + "/"
    english = base + languages.page_url(original)
    links = [{"lang": languages.ORIGINAL, "href": english}]
    links += [{"lang": lang, "href": base + languages.page_url(group[lang])}
              for lang in languages.LANGUAGES if lang in group]
    links.append({"lang": X_DEFAULT, "href": english})
    return links


def language_switch(links: list[dict[str, str]], lang: str, site_url: str) -> dict:
    """The language menu of a page, from its hreflang links: every language the
    page exists in, in their order, its path under the site, and the page's own
    marked current."""
    base = site_url.rstrip("/") + "/"
    items = [{"lang": link["lang"], "name": languages.NAMES[link["lang"]], "code": link["lang"].upper(),
              "path": link["href"][len(base):], "current": link["lang"] == lang}
             for link in links if link["lang"] != X_DEFAULT]
    return {"current": next(item for item in items if item["current"]), "items": items}


# ── the hooks mkdocs calls ───────────────────────────────────────────────────

# original → {language → translation}, for the originals that have any.
_groups: dict[str, dict[str, str]] = {}
# language → {original → the short title of its translation}: the pager's words.
_titles: dict[str, dict[str, str]] = {}

_H1 = re.compile(r"(?m)^# +(.+?)\s*#*\s*$")


def short_title(markdown: str) -> str | None:
    """A page's <h1>, from its Markdown, up to its first colon: what the nav
    calls a chapter. None for a page with no # heading."""
    found = _H1.search(markdown)
    if not found:
        return None
    return found.group(1).split(":", 1)[0].strip()


def translations_in(files) -> dict[str, dict[str, str]]:
    """The groups of a build, refusing any translation that does not hold together."""
    pages = {f.src_uri: f for f in files.documentation_pages()}
    originals = {page: front_matter(pages[page].abs_src_path) for page in languages.PAGES if page in pages}
    catalogs = {lang for lang in languages.LANGUAGES
                if os.path.isfile(os.path.join(catalog.DIRECTORY, f"{lang}.yml"))}
    problems: list[str] = []
    groups: dict[str, dict[str, str]] = {}
    for src_uri in sorted(pages):
        if not languages.is_translation(src_uri):
            continue
        found = refusals(src_uri, front_matter(pages[src_uri].abs_src_path), originals, catalogs)
        problems += found
        if not found:
            groups.setdefault(src_uri.split("/", 1)[1], {})[languages.language_of(src_uri)] = src_uri
    if problems:
        raise PluginError(f"translations: {len(problems)} problem(s):\n  " + "\n  ".join(problems))
    return groups


def on_files(files, config, **kwargs):
    _headings.clear()
    _behind.clear()
    _groups.clear()
    _groups.update(translations_in(files))
    _titles.clear()
    sources = {f.src_uri: f for f in files.documentation_pages()}
    for original, group in _groups.items():
        for lang, src_uri in group.items():
            with open(sources[src_uri].abs_src_path, encoding="utf-8") as fh:
                text = fh.read()
            # Its own title: a presentation page's title:, a Handbook page's
            # <h1> up to the colon.
            title = str(front_matter(sources[src_uri].abs_src_path).get("title") or "").strip() or short_title(text)
            if title:
                _titles.setdefault(lang, {})[original] = title
    return files


class Current:
    """The page itself, in its translation's drawer: Material's macro knows it
    for the page (== page) and draws it current, with its table of contents,
    under its title up to the colon, as the other entries are."""

    def __init__(self, page, title):
        self._page = page
        self.title = title

    def __getattr__(self, name):
        return getattr(self._page, name)

    def __eq__(self, other):
        return other is self._page or other is self

    def __hash__(self):
        return hash(self._page)


class NavEntry:
    """What Material's partials/nav-item.html reads of an item of the nav, for
    the tree a translation's drawer is drawn from: a page (url), or a section
    (children), open when it holds the page."""

    def __init__(self, title, url=None, children=None, active=False, is_index=False):
        self.title = title
        self.url = url
        self.children = children
        self.active = active
        self.is_index = is_index
        self.is_page = children is None
        self.is_section = children is not None
        self.is_link = False
        self.meta = {}
        self.typeset = None
        self.encrypted = False
        self.pages = None


def english(title: str) -> Markup:
    """A title that leads to an English page, from a page in another language:
    the words marked English, and the mark the reader sees, held to the last
    word (.dg-nowrap) so that a title that wraps never leaves it alone on a
    line. overrides/main.html writes the pager's the same way."""
    head, _, last = str(title).rpartition(" ")
    return Markup('<span lang="en">{}</span><span class="dg-nowrap"><span lang="en">{}</span>'
                  '<span class="dg-en" aria-hidden="true">EN</span></span>').format(head + " " if head else "", last)


def translation_nav(nav, page, lang: str) -> list[NavEntry]:
    """The tree of a translation's drawer: the module's docstring."""
    translated = {original: group[lang] for original, group in _groups.items() if lang in group}
    titles = _titles.get(lang, {})
    here = page.meta.get("translation_of")
    tree: list[NavEntry] = []
    for item in nav.items:
        if item.is_page and item.file.src_uri in translated:
            original = item.file.src_uri
            tree.append(NavEntry(titles.get(original) or item.title, languages.page_url(translated[original])))
        elif item.is_section and any(child.is_page and child.file.src_uri in languages.HANDBOOK_PAGES
                                     for child in item.children):
            children = []
            for child in item.children:
                original = child.file.src_uri
                if original == here:
                    children.append(Current(page, titles.get(original) or page.title))
                elif original in translated:
                    children.append(NavEntry(titles.get(original) or child.title,
                                             languages.page_url(translated[original]), is_index=child.is_index))
                else:
                    children.append(NavEntry(english(child.title), child.url, is_index=child.is_index))
            tree.append(NavEntry(catalog.t("bar.handbook", lang=lang), children=children,
                                 active=any(isinstance(child, Current) for child in children)))
    # Its words say it is English; no mark after them.
    tree.append(NavEntry(catalog.t("nav.english_docs", lang=lang), "product/guide/"))
    return tree


def on_nav(nav, config, files, **kwargs):
    """The rule the pager's titles rest on, held to the English: every Handbook
    chapter's nav title is its <h1> up to the colon."""
    problems = []
    for page in nav.pages:
        src_uri = page.file.src_uri
        if src_uri not in languages.HANDBOOK_PAGES or not page.title:
            continue
        with open(page.file.abs_src_path, encoding="utf-8") as fh:
            short = short_title(fh.read())
        if short != page.title:
            problems.append(f"{src_uri}: its nav title is {page.title!r} and its <h1> up to the colon {short!r} — "
                            "a translation's pager names it by the second, so they must be the same")
    if problems:
        raise PluginError("translations: " + "\n  ".join(problems))
    return nav


def notice(meta: dict, repo: str, original: str) -> dict:
    """What a translation's notice says: whether its original has changed since
    — tools/translation.py's status(), the function tools/check-translations.py
    reports with — the day of the commit it was made from, and where the
    original is."""
    import translation  # tools/translation.py

    date = translation.commit_date(repo, meta.get("source_commit"))
    if date is None:
        raise PluginError(f"translations: {meta.get('lang')}/{original}: source_commit "
                          f"{meta.get('source_commit')!r} is not a commit this repository has, so its notice "
                          "has no date. The history must be whole (fetch-depth: 0).")
    return {"stale": bool(translation.status(meta, repo)), "date": date,
            "original": languages.page_url(original)}


def on_page_context(context, page, config, nav, **kwargs):
    src_uri = page.file.src_uri
    original = src_uri.split("/", 1)[1] if languages.is_translation(src_uri) else src_uri
    if original in _groups:
        page.meta["hreflang"] = hreflang(original, _groups[original], config["site_url"])
        page.meta["language_switch"] = language_switch(page.meta["hreflang"],
                                                       languages.language_of(src_uri) or languages.ORIGINAL,
                                                       config["site_url"])
    if languages.is_translation(src_uri):
        repo = os.path.dirname(os.path.abspath(config["config_file_path"]))
        page.meta["translation_notice"] = notice(page.meta, repo, original)
        page.meta["pager_titles"] = dict(_titles.get(languages.language_of(src_uri), {}))
        if original in languages.HANDBOOK_PAGES:
            page.meta["translation_nav"] = translation_nav(nav, page, languages.language_of(src_uri))
        # Up to date: its original's heading ids, so a #link written for the
        # English page lands on the same section. Behind: its own, whatever
        # its headings — they may not be the original's any more.
        if behind(page.meta, repo, original):
            _behind.add("/" + page.url)
        else:
            page.content, mapping = english_ids(page.content, _headings.get(original, []), src_uri)
            _retitle(page.toc, mapping)
    return context


class _Head(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang: str | None = None
        self.locale: str | None = None
        self.links: list[tuple[str, str]] = []
        # The language menu: how many there are, its summary's words, and its
        # entries as (lang, hreflang, href, text, aria-current).
        self.switches = 0
        self.summary: tuple[str, str] | None = None
        self.entries: list[list] = []
        self._in = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = (attrs.get("class") or "").split()
        if tag == "details" and "dg-lang" in classes:
            self.switches += 1
        elif tag == "summary" and "dg-lang__summary" in classes:
            self.summary = [attrs.get("aria-label") or "", ""]
            self._in = "summary"
        elif tag == "a" and self.switches and self._in in (None, "menu") and "dg-lang__item" in classes:
            self.entries.append([attrs.get("lang"), attrs.get("hreflang"), attrs.get("href"), "",
                                 attrs.get("aria-current")])
            self._in = "entry"
        if tag == "html" and self.lang is None:
            self.lang = attrs.get("lang")
        elif tag == "meta" and attrs.get("property") == "og:locale":
            self.locale = attrs.get("content")
        elif tag == "link" and "hreflang" in attrs:
            self.links.append((attrs["hreflang"], attrs.get("href") or ""))

    def handle_endtag(self, tag):
        if tag == "summary" and self._in == "summary":
            self.summary = (self.summary[0], self.summary[1].strip())
            self._in = None
        elif tag == "a" and self._in == "entry":
            self.entries[-1][3] = self.entries[-1][3].strip()
            self._in = None

    def handle_data(self, data):
        if self._in == "summary":
            self.summary[1] += data
        elif self._in == "entry":
            self.entries[-1][3] += data

    handle_startendtag = handle_starttag


def check_site(site: str, groups: dict[str, dict[str, str]], site_url: str) -> tuple[list[str], dict]:
    """Every page's hreflang links against its group's, and every translation's
    language, as written into site/."""
    expected: dict[str, list[tuple[str, str]]] = {}
    language: dict[str, str] = {}
    switches: dict[str, dict] = {}
    for original, group in groups.items():
        links = hreflang(original, group, site_url)
        for src_uri in [original] + list(group.values()):
            path = languages.page_url(src_uri) + "index.html"
            expected[path] = [(link["lang"], link["href"]) for link in links]
            language[path] = languages.language_of(src_uri) or languages.ORIGINAL
            switches[path] = language_switch(links, language[path], site_url)
    problems: list[str] = []
    counted = {"pages": 0, "links": 0, "menus": 0, "entries": 0}
    for folder, dirs, names in os.walk(site):
        dirs.sort()
        for name in sorted(n for n in names if n.endswith(".html")):
            path = os.path.relpath(os.path.join(folder, name), site).replace(os.sep, "/")
            head = _Head()
            with open(os.path.join(folder, name), encoding="utf-8") as fh:
                head.feed(fh.read())
            counted["pages"] += 1
            counted["links"] += len(head.links)
            wanted = expected.get(path, [])
            if head.links != wanted:
                problems.append(f"{path}: hreflang {head.links or 'none'}, wanted {wanted or 'none'}")
            problems += _switch_problems(path, head, switches.get(path), site_url)
            counted["menus"] += head.switches
            counted["entries"] += len(head.entries)
            if path in language and languages.is_translation(path):
                if head.lang != language[path]:
                    problems.append(f"{path}: <html lang={head.lang!r}>, and the page is {language[path]}")
                if head.locale != language[path]:
                    problems.append(f"{path}: og:locale {head.locale!r}, and the page is {language[path]}")
    for path in expected:
        if not os.path.isfile(os.path.join(site, path)):
            problems.append(f"{path}: a page of a translated group, and site/ does not have it")
    return problems, counted


def _switch_problems(path: str, head: "_Head", switch: dict | None, site_url: str) -> list[str]:
    """A page's language menu against the one its hreflang group gives it: none
    on a page without translations."""
    if switch is None:
        return [f"{path}: a language menu, and the page has no translation"] if head.switches else []
    if head.switches != 1:
        return [f"{path}: {head.switches} language menus, and a page with translations has one"]
    problems = []
    current = switch["current"]
    if not head.summary or head.summary[1] != current["code"] or current["name"] not in head.summary[0]:
        problems.append(f"{path}: the menu's summary is {head.summary}, and it should show {current['code']} "
                        f"with a name that says {current['name']}")
    page_url = "https://site.invalid/" + path[: -len("index.html")]
    got = [(lang, hl, urlsplit(urljoin(page_url, href or "")).path, text, aria)
           for lang, hl, href, text, aria in head.entries]
    wanted = [(item["lang"], item["lang"], "/" + item["path"], item["name"], "page" if item["current"] else None)
              for item in switch["items"]]
    if got != wanted:
        problems.append(f"{path}: the menu's entries are {got}, wanted {wanted}")
    return problems


# ── the links of a translation ───────────────────────────────────────────────


def translated_paths(groups: dict[str, dict[str, str]]) -> dict[str, set[str]]:
    """language → the URL paths of the English pages translated into it:
    {"it": {"/", "/why/"}}."""
    paths: dict[str, set[str]] = {lang: set() for lang in languages.LANGUAGES}
    for original, group in groups.items():
        for lang in group:
            paths[lang].add("/" + languages.page_url(original))
    return paths


def destination(href: str, page_path: str, site_url: str):
    """Where an href of the page at page_path ("/it/why/") leads on this site:
    (path, form) — the path normalized to a page's ("/why", "/why/index.html"
    and "../why/" all "/why/"), and the form it was written in, "absolute",
    "root" or "relative". None for a link off the site, a mailto:, or a
    #fragment of the page itself."""
    if not href or href.startswith("#"):
        return None
    parts = urlsplit(href)
    site = urlsplit(site_url)
    if parts.scheme or parts.netloc or href.startswith("//"):
        if parts.scheme not in ("http", "https", "") or parts.netloc != site.netloc:
            return None
        form = "absolute"
    else:
        form = "root" if href.startswith("/") else "relative"
    path = urlsplit(urljoin(f"{site.scheme}://{site.netloc}{page_path}", href)).path
    if path.endswith("/index.html"):
        path = path[: -len("index.html")]
    elif not path.endswith("/") and "." not in path.rsplit("/", 1)[-1]:
        path += "/"
    return path, form


_A_TAG = re.compile(r"<a\s[^>]*>", re.I)
_HREF = re.compile(r'(\shref=)(["\'])(.*?)\2', re.S)


def localize(html: str, page_path: str, lang: str, translated: set[str], site_url: str) -> str:
    """The page's links to English pages that have a translation in lang, sent
    to the translation: see the docstring's on_post_page."""
    site = urlsplit(site_url)
    to_root = "../" * page_path.strip("/").count("/") + ("../" if page_path.strip("/") else "")

    def one_tag(tag: re.Match) -> str:
        text = tag.group(0)
        if re.search(r"\shreflang=", text, re.I):
            return text

        def one_href(m: re.Match) -> str:
            href = m.group(3)
            found = destination(href, page_path, site_url)
            if found is None or found[0] not in translated:
                return m.group(0)
            path, form = found
            target = f"/{lang}{path}"
            parts = urlsplit(href)
            tail = (f"?{parts.query}" if parts.query else "") + (f"#{parts.fragment}" if parts.fragment else "")
            if form == "absolute":
                new = f"{parts.scheme}://{parts.netloc}{target}{tail}"
            elif form == "root":
                new = f"{target}{tail}"
            else:
                new = f"{to_root or './'}{target[1:]}{tail}"
            return f"{m.group(1)}{m.group(2)}{new}{m.group(2)}"

        return _HREF.sub(one_href, text, count=1)

    return _A_TAG.sub(one_tag, html)


# ── the ids of a translation's headings ──────────────────────────────────────

# src_uri → the (level, id) of each heading of the page's Markdown, in order,
# as the toc extension wrote them: every page, read in on_page_content, which
# mkdocs runs for every page before it renders any (on_page_context).
_headings: dict[str, list[tuple[str, str]]] = {}
# The URL paths of the translations behind their originals ("/it/why/"): their
# headings keep their own ids, and a link to one of them with an id they do not
# have is a warning, not an error.
_behind: set[str] = set()

_HEADING = re.compile(r'<(h[1-6])\b([^>]*?)\sid="([^"]*)"')
_SAME_PAGE = re.compile(r'(\shref=")#([^"]*)(")')


def headings_of(html: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(3)) for m in _HEADING.finditer(html)]


def english_ids(html: str, english: list[tuple[str, str]], where: str) -> tuple[str, dict[str, str]]:
    """A translation's content with the ids of its original's headings, by
    position, its own #links to them following: (html, own id → English id).
    Refused when the headings are not as many, at the same levels."""
    own = headings_of(html)
    if [level for level, _ in own] != [level for level, _ in english]:
        raise PluginError(f"translations: {where}: its headings are {[level for level, _ in own]}, and its original's "
                          f"{[level for level, _ in english]} — the ids of a translation up to date with its original "
                          "are its original's, by position, so the two must have the same headings")
    mapping = {mine: theirs for (_, mine), (_, theirs) in zip(own, english)}
    count = iter(english)
    html = _HEADING.sub(lambda m: f'<{m.group(1)}{m.group(2)} id="{next(count)[1]}"', html)
    html = _SAME_PAGE.sub(lambda m: f"{m.group(1)}#{mapping.get(m.group(2), m.group(2))}{m.group(3)}", html)
    return html, mapping


def _retitle(items, mapping: dict[str, str]) -> None:
    for item in items:
        item.id = mapping.get(item.id, item.id)
        _retitle(item.children, mapping)


def on_page_content(html, page, config, files, **kwargs):
    _headings[page.file.src_uri] = headings_of(html)
    return html


def behind(meta: dict, repo: str, original: str) -> bool:
    """A translation made from another version of its original than the one there is now."""
    import translation  # tools/translation.py

    return meta.get("source_sha") != translation.source_sha(repo, original)


def on_post_page(output, page, config, **kwargs):
    lang = languages.language_of(page.file.src_uri)
    if lang is None:
        return output
    translated = translated_paths(_groups)[lang]
    return localize(output, "/" + page.url, lang, translated, config["site_url"])


class _Anchors(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.anchors: list[tuple[str, bool]] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "a" and attrs.get("href") is not None:
            self.anchors.append((attrs["href"], "hreflang" in attrs))

    handle_startendtag = handle_starttag


def link_problems(site: str, groups: dict[str, dict[str, str]], site_url: str) -> tuple[list[str], int]:
    """Every link of every page under a language's folder in site/: one to the
    English page of a page translated into that language, or to a path under
    /<lang>/ that site/ does not have, is a problem. (problems, links read)"""
    translated = translated_paths(groups)
    problems: list[str] = []
    read = 0
    for lang in languages.LANGUAGES:
        for folder, dirs, names in os.walk(os.path.join(site, lang)):
            dirs.sort()
            for name in sorted(n for n in names if n.endswith(".html")):
                path = os.path.relpath(os.path.join(folder, name), site).replace(os.sep, "/")
                page_path = "/" + (path[: -len("index.html")] if name == "index.html" else path)
                parser = _Anchors()
                with open(os.path.join(folder, name), encoding="utf-8") as fh:
                    parser.feed(fh.read())
                for href, has_hreflang in parser.anchors:
                    found = destination(href, page_path, site_url)
                    if found is None:
                        continue
                    read += 1
                    target = found[0]
                    if target in translated[lang] and not has_hreflang:
                        problems.append(f"{path}: {href!r} leads to the English {target}, "
                                        f"and it has a translation, /{lang}{target}")
                    if target.startswith(f"/{lang}/"):
                        on_disk = os.path.join(site, target[1:])
                        if not (os.path.isfile(os.path.join(on_disk, "index.html")) if target.endswith("/")
                                else os.path.isfile(on_disk)):
                            problems.append(f"{path}: {href!r} leads to {target}, which site/ does not have")
    return problems, read


class _Ids(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("name"):
            self.ids.add(attrs["name"])
        if tag == "a" and attrs.get("href"):
            self.hrefs.append(attrs["href"])

    handle_startendtag = handle_starttag


# Ids other pages and other sites link to: the page must keep them.
STABLE_IDS = {"": ("install",)}


def anchor_problems(site: str, site_url: str, behind_paths: set[str] = frozenset()
                    ) -> tuple[list[str], list[str], int]:
    """Every link with a #fragment, on every page of site/, to a page site/ has:
    the id missing there is an error — a warning when that page is a
    translation behind its original — and every id of STABLE_IDS must be on its
    page, in every language. (errors, warnings, links read)"""
    parsed: dict[str, _Ids] = {}

    def page(relative: str) -> _Ids | None:
        if relative not in parsed:
            full = os.path.join(site, relative)
            if not os.path.isfile(full):
                parsed[relative] = None
            else:
                parser = _Ids()
                with open(full, encoding="utf-8") as fh:
                    parser.feed(fh.read())
                parsed[relative] = parser
        return parsed[relative]

    errors: list[str] = []
    warnings: list[str] = []
    read = 0
    for folder, dirs, names in os.walk(site):
        dirs.sort()
        for name in sorted(n for n in names if n.endswith(".html")):
            relative = os.path.relpath(os.path.join(folder, name), site).replace(os.sep, "/")
            page_path = "/" + (relative[: -len("index.html")] if name == "index.html" else relative)
            for href in page(relative).hrefs:
                fragment = unquote(urlsplit(href).fragment)
                if not fragment:
                    continue
                if href.startswith("#"):
                    target, target_file = page_path, relative
                else:
                    found = destination(href, page_path, site_url)
                    if found is None:
                        continue
                    target = found[0]
                    target_file = target[1:] + "index.html" if target.endswith("/") else target[1:]
                there = page(target_file)
                if there is None:
                    continue
                read += 1
                if fragment not in there.ids:
                    message = f"{relative}: {href!r} leads to #{fragment}, which {target} does not have"
                    if target in behind_paths:
                        warnings.append(message + " (a translation behind its original: its headings keep their own ids)")
                    else:
                        errors.append(message)
    for base, ids in STABLE_IDS.items():
        for lang in ("",) + languages.LANGUAGES:
            relative = (f"{lang}/" if lang else "") + (base + "/" if base else "") + "index.html"
            there = page(relative)
            if there is None:
                continue
            for wanted in ids:
                if wanted not in there.ids:
                    errors.append(f"{relative}: no id {wanted!r}, which links on this site and elsewhere lead to")
    return errors, warnings, read


class _Hrefs(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.hrefs: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name == "href" and value is not None:
                self.hrefs.append((tag, value))

    handle_startendtag = handle_starttag


def protocol_relative_problems(site: str) -> tuple[list[str], int]:
    """Every href of every page of site/ that starts with //: (problems, pages read)."""
    problems: list[str] = []
    pages = 0
    for folder, dirs, names in os.walk(site):
        dirs.sort()
        for name in sorted(n for n in names if n.endswith(".html")):
            relative = os.path.relpath(os.path.join(folder, name), site).replace(os.sep, "/")
            parser = _Hrefs()
            with open(os.path.join(folder, name), encoding="utf-8") as fh:
                parser.feed(fh.read())
            pages += 1
            for tag, href in parser.hrefs:
                if href.startswith("//"):
                    problems.append(f"{relative}: <{tag} href={href!r}> is relative to the protocol, a link to "
                                    f"the host {urlsplit(href).netloc or '(none)'!r}, not to this site")
    return problems, pages


def on_post_build(config, **kwargs):
    problems, _ = check_site(config["site_dir"], _groups, config["site_url"])
    problems += link_problems(config["site_dir"], _groups, config["site_url"])[0]
    errors, warnings, _ = anchor_problems(config["site_dir"], config["site_url"], _behind)
    problems += errors
    problems += protocol_relative_problems(config["site_dir"])[0]
    for warning in warnings:
        print(f"WARNING -  translations: {warning}", file=sys.stderr)
    if problems:
        raise PluginError(f"translations: {len(problems)} problem(s) in site/:\n  " + "\n  ".join(problems))


# ── the selftest ─────────────────────────────────────────────────────────────

FIXTURE = os.path.join(ROOT, "tools", "testdata", "translations", "docs")
FIXTURE_CATALOGS = os.path.join(ROOT, "tools", "testdata", "translations", "i18n")


def _merge(into: dict, overlay: dict) -> None:
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(into.get(key), dict):
            _merge(into[key], value)
        else:
            into[key] = value

# When the fixture's English site is committed: a day in the past, which the
# fake translations' notices must show.
ENGLISH_DATE = "2026-01-15T12:00:00Z"
SITE_URL = "https://digline.dev/"


def _refusal_cases() -> list[tuple[str, str, dict, str | None]]:
    good = {"lang": "it", "translation_of": "why.md", "template": "why.html",
            "description": "Una descrizione.", "search": {"exclude": True}}
    return [
        ("a translation that holds together", "it/why.md", good, None),
        ("a page that is not a presentation page", "it/comparison/index.md",
         dict(good, translation_of="comparison/index.md"), "comparison/index.md is not one of them"),
        ("a presentation page at another path", "it/perche.md", good, "perche.md is not one of them"),
        ("a Handbook chapter at another chapter's path", "it/handbook/02-cases.md",
         dict(good, translation_of="handbook/03-ground-truth.md", template=None),
         "translation_of is 'handbook/03-ground-truth.md', and a translation stands at its original's path, handbook/02-cases.md"),
        ("a Handbook chapter under a name of its own", "it/handbook/perche.md",
         dict(good, translation_of="handbook/perche.md"), "handbook/perche.md is not one of them"),
        ("a documentation page that is not the Handbook's", "it/product/guide.md",
         dict(good, translation_of="product/guide.md"), "product/guide.md is not one of them"),
        ("a lang that is not its folder's", "it/why.md", dict(good, lang="de"), "lang is 'de', and the page is in the it/ folder"),
        ("a language with no catalog", "es/why.md", dict(good, lang="es"), "lang es has no catalog"),
        ("no translation_of", "it/why.md", {k: v for k, v in good.items() if k != "translation_of"}, "no translation_of"),
        ("a translation_of that is not its path", "it/why.md", dict(good, translation_of="start.md"),
         "translation_of is 'start.md', and a translation stands at its original's path, why.md"),
        ("an original the build does not have", "it/contact.md", dict(good, translation_of="contact.md"),
         "translation_of contact.md, which the build does not have"),
        ("another template than its original's", "it/why.md", dict(good, template="about.html"),
         "template is 'about.html', and why.md is laid out by 'why.html'"),
        ("no description", "it/why.md", dict(good, description="  "), "no description of its own"),
        ("not excluded from search", "it/why.md", {k: v for k, v in good.items() if k != "search"},
         "not `search: exclude: true`"),
        ("search: exclude that is not true", "it/why.md", dict(good, search={"exclude": "yes"}),
         "not `search: exclude: true`"),
    ]


def _copy_site(into: str) -> None:
    """The parts of the repository a build reads, into a directory of its own,
    under git so that seo.py dates the pages as it does here."""
    for name in ("mkdocs.yml", ".lastmod.tsv", ".agents-rule.json", ".operator-facts.json"):
        if os.path.isfile(os.path.join(ROOT, name)):
            shutil.copy(os.path.join(ROOT, name), into)
    ignore = shutil.ignore_patterns("__pycache__", ".DS_Store")
    for name in ("overrides", "tools", "i18n", "docs"):
        shutil.copytree(os.path.join(ROOT, name), os.path.join(into, name), ignore=ignore)
    import translation  # tools/translation.py

    # The fixture's translations, and no others: whatever the repository has
    # translated is left out of the copy.
    translation.english_only(into)

    # The English site first, committed, so that each translation is stamped
    # with a commit the copy has — its notice is dated by it. On a fixed day in
    # the past, so that a notice dated today is not mistaken for one dated by
    # its original's commit.
    git = ["git", "-C", into, "-c", "user.name=selftest", "-c", "user.email=selftest@invalid",
           "-c", "commit.gpgsign=false"]
    subprocess.run(git[:3] + ["init", "-q"], check=True)
    subprocess.run(git + ["add", "-A"], check=True)
    past = dict(os.environ, GIT_AUTHOR_DATE=ENGLISH_DATE, GIT_COMMITTER_DATE=ENGLISH_DATE)
    subprocess.run(git + ["commit", "-q", "-m", "selftest: the English site"], check=True, env=past)
    for lang in sorted(os.listdir(FIXTURE)):
        os.makedirs(os.path.join(into, "docs", lang))
        # Every folder down: the Handbook's are in <lang>/handbook/.
        for folder, dirs, names in os.walk(os.path.join(FIXTURE, lang)):
            dirs.sort()
            for name in sorted(names):
                source = os.path.join(folder, name)
                target = os.path.join(into, "docs", lang, os.path.relpath(source, os.path.join(FIXTURE, lang)))
                meta, _ = translation.read_page(source)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "w", encoding="utf-8") as fh:
                    fh.write(translation.fake_translation(into, lang, meta))
        # A fake catalog: the English words, over them the fixture's own words
        # for the language where it has any (the German bar), and the language's
        # real fixed section.
        with open(os.path.join(ROOT, "i18n", "en.yml"), encoding="utf-8") as fh:
            words = yaml.safe_load(fh)
        overlay = os.path.join(FIXTURE_CATALOGS, f"{lang}.yml")
        if os.path.isfile(overlay):
            with open(overlay, encoding="utf-8") as fh:
                _merge(words, yaml.safe_load(fh))
        # What the fake catalog was translated from: every English key, as now.
        words[translation.KEYS_FIELD] = translation.nested(translation.catalog_hashes(into))
        fixed = translation.fixed_section(os.path.join(into, "i18n", f"{lang}.yml"))
        with open(os.path.join(into, "i18n", f"{lang}.yml"), "w", encoding="utf-8") as fh:
            fh.write(yaml.safe_dump(words, allow_unicode=True, sort_keys=False, width=1000) + "\n" + fixed)
    subprocess.run(git + ["add", "-A"], check=True)
    subprocess.run(git + ["commit", "-q", "-m", "selftest: the translations"], check=True)


def _build(root: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, MKDOCS_OMITTED_FILES="warn")
    return subprocess.run([sys.executable, "-m", "mkdocs", "build", "--strict", "-f",
                           os.path.join(root, "mkdocs.yml")], cwd=root, env=env,
                          capture_output=True, text=True)


def _read(site: str, path: str) -> str:
    with open(os.path.join(site, path), encoding="utf-8") as fh:
        return fh.read()


def selftest() -> int:
    failures: list[str] = []

    def expect(label, actual, wanted):
        if actual != wanted:
            failures.append(f"{label}: got {actual!r}, wanted {wanted!r}")

    # 1. The refusals, on front matter alone.
    originals = {page: {"template": page.replace(".md", ".html").replace("index.html", "home.html")}
                 for page in ("index.md", "start.md", "why.md", "about.md")}
    originals.update({page: {} for page in ("handbook/02-cases.md", "handbook/03-ground-truth.md")})
    for label, src_uri, meta, needle in _refusal_cases():
        found = refusals(src_uri, meta, originals, {"it", "de"})
        if needle is None:
            expect(label, found, [])
        elif not any(needle in p for p in found):
            failures.append(f"{label}: not refused ({found})")
        else:
            print(f"translations selftest: refused, as it must — {label}")

    # The ids of an up-to-date translation's headings, on HTML alone: by position,
    # its own #links and its toc following, and refused on a count or a level apart.
    from mkdocs.structure.toc import AnchorLink

    english = [("h1", "why"), ("h2", "a-prompt-is-not-code"), ("h2", "the-model-changes-under-you")]
    mine = ('<h1 id="perche">Perché</h1><p><a href="#il-modello">giù</a></p>'
            '<h2 id="il-modello">Il modello</h2><h2 id="un-prompt">Un prompt</h2>')
    html, mapping = english_ids(mine, english, "it/why.md")
    toc = [AnchorLink("Perché", "perche", 1)]
    toc[0].children = [AnchorLink("Il modello", "il-modello", 2), AnchorLink("Un prompt", "un-prompt", 2)]
    _retitle(toc, mapping)
    expect("english_ids: by position, the page's own #link and its toc following",
           (headings_of(html), 'href="#a-prompt-is-not-code"' in html, [toc[0].id] + [c.id for c in toc[0].children]),
           (english, True, ["why", "a-prompt-is-not-code", "the-model-changes-under-you"]))
    for label, wrong in (("a heading fewer", '<h1 id="p">P</h1><h2 id="x">X</h2>'),
                         ("a heading at another level", '<h1 id="p">P</h1><h2 id="x">X</h2><h3 id="y">Y</h3>')):
        try:
            english_ids(wrong, english, "it/why.md")
            failures.append(f"english_ids: {label} not refused")
        except PluginError as error:
            expect(f"english_ids refuses {label}", "its headings are" in str(error), True)

    # 2. The copy the fixture starts from holds no translation of the repository's:
    # a translated page and a whole catalog, and what english_only leaves of them.
    import translation  # tools/translation.py

    with tempfile.TemporaryDirectory() as root:
        os.makedirs(os.path.join(root, "docs", "it"))
        os.makedirs(os.path.join(root, "i18n"))
        with open(os.path.join(root, "docs", "it", "why.md"), "w", encoding="utf-8") as fh:
            fh.write("---\nlang: it\n---\n\n# Perché\n")
        fixed = translation.fixed_section(os.path.join(ROOT, "i18n", "it.yml"))
        with open(os.path.join(root, "i18n", "it.yml"), "w", encoding="utf-8") as fh:
            fh.write("bar:\n  why: Perché\n\nsource_keys:\n  bar:\n    why: 1a2b3c4d5e6f\n\n" + fixed)
        translation.english_only(root)
        with open(os.path.join(root, "i18n", "it.yml"), encoding="utf-8") as fh:
            left = fh.read()
        expect("english_only: no docs/it/, and the catalog its fixed section alone, as written",
               (os.path.exists(os.path.join(root, "docs", "it")), left == fixed, bool(fixed.strip())), (False, True, True))

    # 3. The fixture, built.
    if not os.path.isfile(os.path.join(ROOT, "docs", "product", "guide.md")):
        print("translations selftest: docs/product/ is not synced; run `make docs` first.", file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as root:
        _copy_site(root)
        built = _build(root)
        if built.returncode != 0:
            print(built.stdout[-3000:] + built.stderr[-3000:], file=sys.stderr)
            print("translations selftest: the fixture did not build", file=sys.stderr)
            return 1
        site = os.path.join(root, "site")
        groups = {"index.md": {"it": "it/index.md"}, "why.md": {"it": "it/why.md", "de": "de/why.md"},
                  "about.md": {"it": "it/about.md"}, "handbook/index.md": {"it": "it/handbook/index.md"},
                  "handbook/02-cases.md": {"it": "it/handbook/02-cases.md"},
                  "handbook/03-ground-truth.md": {"it": "it/handbook/03-ground-truth.md"},
                  "handbook/08-for-teams-building-for-others.md": {"it": "it/handbook/08-for-teams-building-for-others.md"}}

        def links(path):
            head = _Head()
            head.feed(_read(site, path))
            return head

        english_why = [("en", SITE_URL + "why/"), ("it", SITE_URL + "it/why/"), ("de", SITE_URL + "de/why/"),
                       ("x-default", SITE_URL + "why/")]
        english_home = [("en", SITE_URL), ("it", SITE_URL + "it/"), ("x-default", SITE_URL)]
        expect("hreflang on Why", links("why/index.html").links, english_why)
        expect("hreflang on its Italian translation", links("it/why/index.html").links, english_why)
        expect("hreflang on its German translation", links("de/why/index.html").links, english_why)
        expect("hreflang on the home", links("index.html").links, english_home)
        expect("hreflang on the Italian home", links("it/index.html").links, english_home)
        expect("no hreflang on Start here, which has no translation", links("start/index.html").links, [])
        expect("no hreflang on a documentation page", links("product/guide/index.html").links, [])
        expect("the Italian Why's language", (links("it/why/index.html").lang, links("it/why/index.html").locale),
               ("it", "it"))
        expect("the German Why's language", (links("de/why/index.html").lang, links("de/why/index.html").locale),
               ("de", "de"))
        expect("English Why's language", (links("why/index.html").lang, links("why/index.html").locale), ("en", "en"))
        expect("a documentation page's language", (links("product/guide/index.html").lang,
                                                   links("product/guide/index.html").locale), ("en", "en"))

        it_why = _read(site, "it/why/index.html")
        expect("the bar marks Why on /it/why/, and leads to it",
               bool(re.search(r'<a class="dg-nav__optional" href="\.\./\.\./it/why/" aria-current="page">', it_why)), True)
        closing = re.search(r'<p class="closing__links">(.*?)</p>', it_why, re.S).group(1)
        expect("the closing band leaves Why out on /it/why/", re.findall(r'href="[./]*([a-z/]*)"', closing),
               ["product/guide/", "agents/", "comparison/"])
        expect("the footer marks About on /it/about/, and leads to it",
               bool(re.search(r'href="\.\./\.\./it/about/" aria-current="page"', _read(site, "it/about/index.html"))), True)
        expect("the Italian home is the home", 'class="hero__title"' in _read(site, "it/index.html"), True)
        expect("the Italian Why links a post, which stays English, in English",
               'href="../../blog/bad-evals-my-own/"' in it_why, True)

        # The Handbook, on the documentation's shell: the index and chapter 3 in
        # Italian, the other chapters not.
        it_index, it_chapter = _read(site, "it/handbook/index.html"), _read(site, "it/handbook/03-ground-truth/index.html")
        def pager(html):
            """The pager of a built page as (side, href, direction, lang, title), None without one."""
            found = re.search(r'<nav class="md-footer__inner[^"]*dg-docfoot__pager".*?</nav>', html, re.S)
            if not found:
                return None
            links = re.findall(r'<a href="([^"]*)" class="md-footer__link md-footer__link--(prev|next)".*?'
                               r'md-footer__direction">([^<]*)</span>\s*<div class="md-ellipsis">(.*?)</div>',
                               found.group(0), re.S)
            out = []
            for href, side, direction, title in links:
                marked = re.fullmatch(r'<span lang="en">([^<]*)</span><span class="dg-nowrap"><span lang="en">([^<]*)</span>'
                                      r'<span class="dg-en" aria-hidden="true">EN</span></span>', title)
                out.append((side, href, direction.strip(), "EN" if marked else "",
                            " ".join((marked.group(1) + marked.group(2) if marked else title).split())))
            return out

        chapter_2 = short_title(open(os.path.join(root, "docs", "it", "handbook", "02-cases.md"), encoding="utf-8").read())
        expect("the Italian chapter 3's pager: the Italian chapter 2 before it, in its words; chapter 4, English, marked",
               pager(it_chapter),
               # The fixture's Italian catalog is the English one: "Previous" here.
               [("prev", "../../../it/handbook/02-cases/", "Previous", "", chapter_2),
                ("next", "../../../handbook/04-checks/", "Next", "EN", "4. Checks")])
        expect("the English chapter 3's pager: as it was, no lang",
               pager(_read(site, "handbook/03-ground-truth/index.html")),
               [("prev", "../02-cases/", "Previous", "", "2. Cases"), ("next", "../04-checks/", "Next", "", "4. Checks")])
        expect("no pager on the Italian Handbook index, as on the English one",
               (pager(it_index), pager(_read(site, "handbook/index.html"))), (None, None))
        expect("no pager on an Italian presentation page", pager(it_why), None)
        expect("the Italian chapter 8's pager stops at the end of the Handbook; the English one goes on to the Guide",
               (pager(_read(site, "it/handbook/08-for-teams-building-for-others/index.html")),
                [side for side, *_ in pager(_read(site, "handbook/08-for-teams-building-for-others/index.html"))],
                pager(_read(site, "handbook/08-for-teams-building-for-others/index.html"))[-1][-1]),
               ([("prev", "../../../handbook/07-maintenance/", "Previous", "EN", "7. Maintenance")], ["prev", "next"], "Guide"))
        expect("the pager's label, from the catalog, on an English chapter and an Italian one",
               ['aria-label="Previous and next"' in _read(site, p) for p in
                ("handbook/03-ground-truth/index.html", "it/handbook/03-ground-truth/index.html")], [True, True])

        # The drawer of a translated chapter: the pages translated into Italian,
        # the Handbook whole — its own chapter current, under its short title,
        # translated ones in Italian, the rest in English marked EN — and the
        # English documentation last. An English page keeps Material's nav.
        def links_title(src_uri):
            return front_matter(os.path.join(root, "docs", src_uri))["title"]

        def drawer(html):
            nav = re.search(r'<nav class="md-nav md-nav--primary.*?</ul>\s*</nav>\s*</div>', html, re.S).group(0)
            nav = re.sub(r'<nav class="md-nav md-nav--secondary".*?</nav>', "", nav, flags=re.S)  # its toc
            return [(href, " ".join(re.sub(r"<[^>]+>", " ", text).split()), "md-nav__link--active" in cls,
                     'class="dg-en"' in text)
                    for href, cls, text in re.findall(r'<a href="([^"]*)" class="(md-nav__link[^"]*)"[^>]*>(.*?)</a>', nav, re.S)]

        it_drawer = drawer(it_chapter)
        expect("the Italian chapter 3's drawer, in the nav's order (the fixture's Italian catalog is the English one)",
               [(h, t) for h, t, a, e in it_drawer if "#" not in h],
               [("../../", "Home"), ("../../why/", links_title("it/why.md")), ("../", "Handbook"),
                ("../../../handbook/01-what-you-are-shipping/", "1. What you are actually shipping EN"),
                ("../02-cases/", chapter_2), ("./", short_title(open(os.path.join(root, "docs", "it", "handbook", "03-ground-truth.md"),
                                                                     encoding="utf-8").read())),
                ("../../../handbook/04-checks/", "4. Checks EN"), ("../../../handbook/05-the-judge/", "5. The judge EN"),
                ("../../../handbook/06-the-reference/", "6. The reference EN"),
                ("../../../handbook/07-maintenance/", "7. Maintenance EN"),
                ("../08-for-teams-building-for-others/", short_title(open(os.path.join(
                    root, "docs", "it", "handbook", "08-for-teams-building-for-others.md"), encoding="utf-8").read())),
                ("../../about/", links_title("it/about.md")), ("../../../product/guide/", "Documentation, in English")])
        titles_seen = [t for h, t, a, e in it_drawer if "#" not in h]
        expect("the Italian chapter 3's drawer: Italian pages, the Handbook whole, the English docs last",
               (titles_seen[-1].endswith("EN"), any(t.startswith("1. What you are actually shipping") and t.endswith("EN") for t in titles_seen),
                [a for h, t, a, e in it_drawer if a], len([t for t in titles_seen if t.endswith("EN")]),
                any("How digline compares" in t for t in titles_seen)),
               (False, True, [True], 5, False))
        expect("the Italian chapter 3's drawer: itself current, under its title up to the colon, the chapter 2 translated",
               ([t for h, t, a, e in it_drawer if a], chapter_2 in titles_seen),
               ([short_title(open(os.path.join(root, "docs", "it", "handbook", "03-ground-truth.md"), encoding="utf-8").read())],
                True))
        expect("an English chapter keeps Material's nav: every group, no EN mark",
               (any("How digline compares" in t for h, t, a, e in drawer(_read(site, "handbook/03-ground-truth/index.html"))),
                any(e for h, t, a, e in drawer(_read(site, "handbook/03-ground-truth/index.html")))), (True, False))

        expect("the Italian Handbook index: chapter 3 to its translation, chapter 1 in English, from /it/handbook/",
               ('href="../../it/handbook/03-ground-truth/"' in it_index, 'href="../../handbook/01-what-you-are-shipping/"' in it_index,
                'href="../../handbook/03-ground-truth/"' in it_index), (True, True, False))
        expect("the Italian chapter 3: the post in English, three folders up (in its lede, in the opening band)",
               'href="../../../blog/bad-evals-my-own/"' in it_chapter, True)
        expect("the Handbook's bar, English and Italian: search in the first slot, the language menu in the second",
               [bool(re.search(r'<div class="dg-actions">\s*<label class="md-header__button md-icon" for="__search"'
                               r'.*?</div>\s*<details class="dg-lang">', _read(site, p), re.S))
                for p in ("it/handbook/index.html", "it/handbook/03-ground-truth/index.html",
                          "handbook/03-ground-truth/index.html")], [True, True, True])
        expect("a documentation page with no translation: search, then the language slot held empty",
               bool(re.search(r'<div class="dg-actions">\s*<label class="md-header__button md-icon" for="__search"'
                              r'.*?</div>\s*<span class="dg-slot dg-slot--lang" aria-hidden="true"></span>',
                              _read(site, "handbook/04-checks/index.html"), re.S)), True)
        expect("the Italian chapter 3 and index: their language, their hreflang, the notice",
               (links("it/handbook/03-ground-truth/index.html").lang, links("it/handbook/index.html").lang,
                links("it/handbook/03-ground-truth/index.html").links,
                it_chapter.count("data-translation-notice"), "Indice" in it_chapter or "Sommario" in it_chapter),
               ("it", "it", [("en", SITE_URL + "handbook/03-ground-truth/"), ("it", SITE_URL + "it/handbook/03-ground-truth/"),
                             ("x-default", SITE_URL + "handbook/03-ground-truth/")], 1, True))
        expect("the English chapter 3: English, with the Italian as its alternative",
               (links("handbook/03-ground-truth/index.html").lang, len(links("handbook/03-ground-truth/index.html").links)),
               ("en", 3))
        def current_in_bar(html):
            nav = re.search(r'<nav class="dg-nav".*?</nav>', html, re.S).group(0)
            return re.findall(r'href="([^"]*)"[^>]*\saria-current=', nav)

        expect("the bar marks the Handbook, and only it, on /it/handbook/03-ground-truth/; not on /it/why/",
               (current_in_bar(it_chapter), current_in_bar(it_why)),
               (["../../../it/handbook/"], ["../../it/why/"]))

        # The links of a translation: to a page translated into its language, the
        # translation; to one that is not, the English page. The fixture has
        # it: index, why, about; de: why.
        def hrefs(path, pattern):
            return re.findall(pattern, _read(site, path))

        expect("on /it/why/: the logo to /it/, Start (not translated) in English, the footer's About to /it/about/",
               (hrefs("it/why/index.html", r'class="dg-brand" href="([^"]*)"'), '<a href="../../start/">' in it_why,
                'href="../../it/about/"' in it_why, 'href="../../about/"' in it_why),
               (["../../it/"], True, True, False))
        expect("on /it/: the hero's Why to /it/why/, its Start to the English page, #install kept",
               ('class="hero__link--quiet" href="../it/why/"' in _read(site, "it/index.html"),
                'class="hero__link--primary" href="../start/"' in _read(site, "it/index.html"),
                'href="../it/#install"' in _read(site, "it/index.html")), (True, True, True))
        de_why_html = _read(site, "de/why/index.html")
        expect("on /de/why/: Why to /de/why/, the logo to the English home (no German home), About in English",
               ('href="../../de/why/" aria-current="page"' in de_why_html,
                hrefs("de/why/index.html", r'class="dg-brand" href="([^"]*)"'), 'href="../../about/"' in de_why_html,
                'href="../../it/about/"' in de_why_html), (True, ["../../"], True, False))
        expect("the language menu and the notice keep their links to other languages",
               ('class="dg-lang__item" href="../../why/" lang="en" hreflang="en"' in it_why
                or bool(re.search(r'class="dg-lang__item" href="\.\./\.\./why/"[^>]*hreflang="en"', it_why)),
                bool(re.search(r'data-translation-notice>.*?<a href="\.\./\.\./why/" hreflang="en"', it_why, re.S))),
               (True, True))
        expect("English pages keep their English links", 'class="hero__link--quiet" href="./why/"' in _read(site, "index.html"),
               True)
        found, read = link_problems(site, groups, SITE_URL)
        expect("the link gate on the built fixture", (found, read > 100), ([], True))

        # The headings of a translation up to date with its original: its
        # original's ids, by position, and its permalinks with them.
        def heading_ids(path):
            return re.findall(r'<h[1-6][^>]*\sid="([^"]*)"', _read(site, path))

        expect("the Italian and German Why: English Why's heading ids, in order",
               (heading_ids("it/why/index.html") == heading_ids("why/index.html"),
                heading_ids("de/why/index.html") == heading_ids("why/index.html"), len(heading_ids("why/index.html")) > 3),
               (True, True, True))
        expect("the Italian Why's permalinks lead to the English ids",
               re.findall(r'class="headerlink" href="#([^"]*)"', it_why) ==
               re.findall(r'class="headerlink" href="#([^"]*)"', _read(site, "why/index.html")), True)
        errors, warnings, read = anchor_problems(site, SITE_URL)
        expect("the anchor gate on the built fixture", (errors, warnings, read > 50), ([], [], True))
        found, pages = protocol_relative_problems(site)
        not_found = _read(site, "404.html")
        expect("the 404: its bar and footer lead to /why/ and /#install, no href starts with //, anywhere",
               ('href="/why/"' in not_found, 'href="/#install"' in not_found, 'class="dg-brand" href="/"' in not_found,
                'class="dg-mark" src="/assets/favicon.svg"' in not_found, found, pages > 50), (True, True, True, True, [], True))

        def hrefs_planted(path, anchor):
            original = _read(site, path)
            with open(os.path.join(site, path), "w", encoding="utf-8") as fh:
                fh.write(original.replace("</body>", anchor + "</body>", 1))
            try:
                return protocol_relative_problems(site)[0]
            finally:
                with open(os.path.join(site, path), "w", encoding="utf-8") as fh:
                    fh.write(original)

        for label, path, anchor in (("the 404 with //why/", "404.html", '<a href="//why/">x</a>'),
                                    ("a page with //why/", "why/index.html", '<a href="//why/">x</a>'),
                                    ("a page with //#install", "about/index.html", '<a href="//#install">x</a>')):
            found = hrefs_planted(path, anchor)
            if not any(f"{path}: <a href=" in p and "relative to the protocol" in p for p in found):
                failures.append(f"the // gate, {label}: not refused ({found})")
            else:
                print(f"translations selftest: refused, as it must — the // gate, {label}")
        expect("the // gate passes an explicit https://github.com/… link",
               hrefs_planted("404.html", '<a href="https://github.com/digline/digline">x</a>'), [])
        expect("the install id on the homes", ['id="install"' in _read(site, p) for p in ("index.html", "it/index.html")],
               [True, True])

        search = _read(site, "search/search_index.json")
        expect("no translation in the search index",
               re.findall(r'"location":"((?:it|de|es)/[^"]*)"', search), [])
        expect("English Why is in the search index", '"location":"why/"' in search, True)
        llms = _read(site, "llms.txt")
        expect("no translation in llms.txt", re.findall(r"digline\.dev/(?:it|de|es)/\S*", llms), [])
        expect("no Markdown copy of a translation", os.path.exists(os.path.join(site, "it", "why.md")), False)
        sitemap = _read(site, "sitemap.xml")
        expect("the translations in the sitemap",
               sorted(re.findall(r"<loc>https://digline\.dev/((?:it|de)/[^<]*)</loc>", sitemap)),
               ["de/why/", "it/", "it/about/", "it/handbook/", "it/handbook/02-cases/", "it/handbook/03-ground-truth/",
                "it/handbook/08-for-teams-building-for-others/", "it/why/"])

        for script in ("check-llms.py", "check-translate.py", "check-sitemap.py", "check-glyphs.py", "check-bar.py"):
            run = subprocess.run([sys.executable, os.path.join(root, "tools", script), site],
                                 capture_output=True, text=True)
            expect(f"{script} on the built fixture", run.returncode, 0)
            if run.returncode:
                print(run.stdout[-1500:] + run.stderr[-1500:], file=sys.stderr)

        problems, counted = check_site(site, groups, SITE_URL)
        expect("the post-build check on the built fixture", problems, [])
        expect("hreflang links counted", counted["links"], 4 * 3 + 3 * 2 + 3 * 2 + 4 * (2 * 3))

        # The language menu: on the fifteen pages with alternatives — seven
        # presentation pages, eight of the Handbook — with the languages each
        # exists in, and on no other page.
        expect("language menus and their entries counted", (counted["menus"], counted["entries"]),
               (15, 3 * 3 + 2 * 2 + 2 * 2 + 8 * 2))
        de_why = links("de/why/index.html")
        expect("the German Why's menu: its summary", tuple(de_why.summary), ("Sprache: Deutsch", "DE"))
        expect("the German Why's menu: its entries", [tuple(e) for e in de_why.entries],
               [("en", "en", "../../why/", "English", None), ("it", "it", "../../it/why/", "Italiano", None),
                ("de", "de", "../../de/why/", "Deutsch", "page")])
        why_en = links("why/index.html")
        expect("English Why's menu", (tuple(why_en.summary), [tuple(e) for e in why_en.entries]),
               (("Language: English", "EN"), [("en", "en", "../why/", "English", "page"),
                                              ("it", "it", "../it/why/", "Italiano", None),
                                              ("de", "de", "../de/why/", "Deutsch", None)]))
        expect("the Italian home's menu", [tuple(e) for e in links("it/index.html").entries],
               [("en", "en", "../", "English", None), ("it", "it", "../it/", "Italiano", "page")])
        expect("the Italian chapter 3's menu", [tuple(e) for e in links("it/handbook/03-ground-truth/index.html").entries],
               [("en", "en", "../../../handbook/03-ground-truth/", "English", None),
                ("it", "it", "../../../it/handbook/03-ground-truth/", "Italiano", "page")])
        for path in ("start/index.html", "contact/index.html", "product/guide/index.html", "404.html",
                     "handbook/04-checks/index.html"):
            html = _read(site, path)
            expect(f"no language menu, and no script for one, on {path}",
                   (links(path).switches, "details.dg-lang" in html), (0, False))
        expect("the menu's script on a page with the menu", 'querySelector("details.dg-lang")' in _read(site, "why/index.html"), True)

        # The rule under the pager's titles, on the English: a chapter's nav
        # title is its <h1> up to the colon, and a chapter that breaks it stops
        # the build.
        expect("short_title: up to the first colon, trimmed; none without a # heading",
               (short_title("---\nx: 1\n---\n\n# 2. Cases: the asset nobody builds\n\nText: more.\n"),
                short_title("# 5. The judge\n"), short_title("No heading.\n")), ("2. Cases", "5. The judge", None))
        mkdocs_yml = os.path.join(root, "mkdocs.yml")
        with open(mkdocs_yml, encoding="utf-8") as fh:
            config_text = fh.read()
        with open(mkdocs_yml, "w", encoding="utf-8") as fh:
            fh.write(config_text.replace("- 4. Checks: handbook/04-checks.md", "- 4. Checks first: handbook/04-checks.md", 1))
        renamed = _build(root)
        with open(mkdocs_yml, "w", encoding="utf-8") as fh:
            fh.write(config_text)
        if renamed.returncode == 0 or "handbook/04-checks.md: its nav title is '4. Checks first'" not in renamed.stdout + renamed.stderr:
            failures.append("a chapter whose nav title is not its <h1> up to the colon: the build was not refused")
        else:
            print("translations selftest: refused, as it must — a chapter whose nav title is not its <h1> up to the colon")
        rebuilt_clean = _build(root)
        if rebuilt_clean.returncode:
            failures.append("the fixture did not build again after the nav title was put back")

        # 4. The built site, tampered with.
        def tampered(path, change):
            original = _read(site, path)
            with open(os.path.join(site, path), "w", encoding="utf-8") as fh:
                fh.write(change(original))
            try:
                return check_site(site, groups, SITE_URL)[0]
            finally:
                with open(os.path.join(site, path), "w", encoding="utf-8") as fh:
                    fh.write(original)

        tampering = [
            ("a translation's hreflang missing from its original", "why/index.html",
             lambda h: re.sub(r'\n<link rel="alternate" hreflang="de"[^>]*>', "", h), "why/index.html: hreflang"),
            ("hreflang on a page with no translation", "start/index.html",
             lambda h: h.replace("</head>", '<link rel="alternate" hreflang="it" href="https://digline.dev/it/start/"></head>'),
             "start/index.html: hreflang"),
            ("a relative hreflang", "it/why/index.html",
             lambda h: h.replace('href="https://digline.dev/it/why/"', 'href="../../it/why/"'), "it/why/index.html: hreflang"),
            ("no x-default", "de/why/index.html",
             lambda h: re.sub(r'\n<link rel="alternate" hreflang="x-default"[^>]*>', "", h), "de/why/index.html: hreflang"),
            ("a translation that says it is English", "it/about/index.html",
             lambda h: h.replace('<html lang="it">', '<html lang="en">', 1), "<html lang='en'>, and the page is it"),
            ("a translation whose og:locale is English", "it/about/index.html",
             lambda h: h.replace('property="og:locale" content="it"', 'property="og:locale" content="en"'),
             "og:locale 'en', and the page is it"),
            ("a language menu with no current entry", "de/why/index.html",
             lambda h: h.replace(' hreflang="de" aria-current="page">', ' hreflang="de">', 1), "the menu's entries are"),
            ("a menu entry with no lang", "why/index.html",
             lambda h: h.replace('class="dg-lang__item" href="../it/why/" lang="it"', 'class="dg-lang__item" href="../it/why/"', 1),
             "the menu's entries are"),
            ("a menu entry that leads elsewhere", "it/why/index.html",
             lambda h: h.replace('href="../../de/why/" lang="de"', 'href="../../de/" lang="de"', 1), "the menu's entries are"),
            ("a menu missing a language", "why/index.html",
             lambda h: re.sub(r'\n\s*<li><a class="dg-lang__item" href="\.\./de/why/"[^\n]*', "", h, count=1),
             "the menu's entries are"),
            ("a menu whose summary shows another language", "it/about/index.html",
             lambda h: re.sub(r'(<summary class="dg-icon dg-lang__summary"[^>]*>)IT', r"\1EN", h, count=1),
             "the menu's summary is"),
            ("a Handbook page with translations and no menu", "handbook/03-ground-truth/index.html",
             lambda h: re.sub(r'<details class="dg-lang">.*?</details>', "", h, count=1, flags=re.S),
             "handbook/03-ground-truth/index.html: 0 language menus"),
            ("a language menu on a Handbook chapter with no translation", "handbook/04-checks/index.html",
             lambda h: h.replace('<span class="dg-slot dg-slot--lang" aria-hidden="true"></span>',
                                 '<details class="dg-lang"><summary class="dg-icon dg-lang__summary">EN</summary></details>', 1),
             "handbook/04-checks/index.html: a language menu, and the page has no translation"),
            ("an Italian Handbook page that says it is English", "it/handbook/03-ground-truth/index.html",
             lambda h: re.sub(r'<html lang="it"', '<html lang="en"', h, count=1), "<html lang='en'>, and the page is it"),
            ("a language menu on a page with no translation", "start/index.html",
             lambda h: h.replace('<div class="dg-actions">',
                                 '<div class="dg-actions"><details class="dg-lang"><summary class="dg-icon dg-lang__summary">EN</summary></details>', 1),
             "start/index.html: a language menu, and the page has no translation"),
        ]
        for label, path, change, needle in tampering:
            found = tampered(path, change)
            if not any(needle in p for p in found):
                failures.append(f"{label}: not refused ({found})")
            else:
                print(f"translations selftest: refused, as it must — {label}")

        # The link gate: a link planted in the built Italian home, each on its own.
        def planted(path, *anchors):
            original = _read(site, path)
            with open(os.path.join(site, path), "w", encoding="utf-8") as fh:
                fh.write(original.replace("</main>", "".join(anchors) + "</main>", 1))
            try:
                return link_problems(site, groups, SITE_URL)[0]
            finally:
                with open(os.path.join(site, path), "w", encoding="utf-8") as fh:
                    fh.write(original)

        for label, anchor, needle in [
            ("a link to /why/ from /it/", '<a href="/why/">x</a>', "leads to the English /why/"),
            ("a link to https://digline.dev/why/ from /it/", '<a href="https://digline.dev/why/">x</a>',
             "leads to the English /why/"),
            ("a link to ../why/ from /it/", '<a href="../why/">x</a>', "leads to the English /why/"),
            ("a link to /why, no final slash", '<a href="/why">x</a>', "leads to the English /why/"),
            ("a link to ../why/index.html#x", '<a href="../why/index.html#x">x</a>', "leads to the English /why/"),
            ("a link to the English home, https://digline.dev", '<a href="https://digline.dev">x</a>',
             "leads to the English /"),
            ("a link to /it/docs/, which the site does not have", '<a href="/it/docs/">x</a>',
             "leads to /it/docs/, which site/ does not have"),
            ("a link to ../it/start/, not translated in the fixture", '<a href="../it/start/">x</a>',
             "leads to /it/start/, which site/ does not have"),
        ]:
            found = planted("it/index.html", anchor)
            if not any(needle in p for p in found):
                failures.append(f"the link gate, {label}: not refused ({found})")
            else:
                print(f"translations selftest: refused, as it must — the link gate, {label}")
        expect("the link gate passes /it/why/, /docs/, the English Start (not translated) and an hreflang link to /why/",
               planted("it/index.html", '<a href="/it/why/">x</a>', '<a href="/docs/">x</a>',
                       '<a href="https://digline.dev/it/why/">x</a>', '<a href="../start/">x</a>',
                       '<a href="../why/" hreflang="en">x</a>'), [])
        # The anchor gate.
        def anchors_planted(path, change):
            original = _read(site, path)
            with open(os.path.join(site, path), "w", encoding="utf-8") as fh:
                fh.write(change(original))
            try:
                return anchor_problems(site, SITE_URL)
            finally:
                with open(os.path.join(site, path), "w", encoding="utf-8") as fh:
                    fh.write(original)

        english_id = heading_ids("why/index.html")[2]
        add = lambda anchor: (lambda h: h.replace("</main>", anchor + "</main>", 1))
        expect("the anchor gate passes a link to /it/why/#<an English id>, the up-to-date translation",
               anchors_planted("it/index.html", add(f'<a href="../it/why/#{english_id}">x</a>'))[:2], ([], []))
        errors, _, _ = anchors_planted("it/index.html", add('<a href="../it/why/#inesistente">x</a>'))
        expect("the anchor gate refuses /it/why/#inesistente",
               any("leads to #inesistente, which /it/why/ does not have" in e for e in errors), True)
        errors, _, _ = anchors_planted("index.html", lambda h: h.replace(' id="install"', "", 1))
        expect("the anchor gate refuses a home without id=install (and the footer's links to it)",
               (any("index.html: no id 'install'" in e for e in errors),
                any("leads to #install, which / does not have" in e for e in errors)), (True, True))
        errors, _, _ = anchors_planted("product/metrics/index.html", lambda h: h.replace(' id="repeated"', ' id="repeated-renamed"', 1))
        expect("the anchor gate refuses the home's links to a renamed id on /product/metrics/, in English and Italian",
               sorted({e.split(":")[0] for e in errors if "#repeated, which /product/metrics/ does not have" in e}),
               ["index.html", "it/index.html", "product/metrics/index.html"])
        _groups.clear()
        _groups.update(groups)
        _behind.clear()
        not_found = _read(site, "404.html")
        with open(os.path.join(site, "404.html"), "w", encoding="utf-8") as fh:
            fh.write(not_found.replace("</body>", '<a href="//why/">x</a></body>', 1))
        try:
            on_post_build({"site_dir": site, "site_url": SITE_URL})
            failures.append("the // gate: on_post_build did not stop the build on //why/ in the 404")
        except PluginError as error:
            expect("the // gate stops the build (on_post_build)", "404.html: <a href='//why/'>" in str(error), True)
        finally:
            with open(os.path.join(site, "404.html"), "w", encoding="utf-8") as fh:
                fh.write(not_found)
        metrics = _read(site, "product/metrics/index.html")
        with open(os.path.join(site, "product", "metrics", "index.html"), "w", encoding="utf-8") as fh:
            fh.write(metrics.replace(' id="repeated"', ' id="repeated-renamed"', 1))
        try:
            on_post_build({"site_dir": site, "site_url": SITE_URL})
            failures.append("the anchor gate: on_post_build did not stop the build on a renamed id")
        except PluginError as error:
            expect("the anchor gate stops the build (on_post_build)", "#repeated, which /product/metrics/" in str(error), True)
        finally:
            with open(os.path.join(site, "product", "metrics", "index.html"), "w", encoding="utf-8") as fh:
                fh.write(metrics)
        original_home = _read(site, "it/index.html")
        with open(os.path.join(site, "it", "index.html"), "w", encoding="utf-8") as fh:
            fh.write(original_home.replace("</main>", '<a href="/why/">x</a></main>', 1))
        try:
            on_post_build({"site_dir": site, "site_url": SITE_URL})
            failures.append("the link gate: on_post_build did not stop the build on a link to /why/ from /it/")
        except PluginError as error:
            expect("the link gate stops the build (on_post_build)", "leads to the English /why/" in str(error), True)
        finally:
            with open(os.path.join(site, "it", "index.html"), "w", encoding="utf-8") as fh:
                fh.write(original_home)

        # A translation added in this test only — Italian Start — and links written
        # in a translation's Markdown: rewritten and gated, with no change to the code.
        start_meta = {"title": "Inizia qui", "template": "start.html", "lang": "it", "translation_of": "start.md",
                      "description": "Traduzione finta di Start, solo per questo test.", "search": {"exclude": True}}
        with open(os.path.join(root, "docs", "it", "start.md"), "w", encoding="utf-8") as fh:
            fh.write(translation.fake_translation(root, "it", start_meta))
        with open(os.path.join(root, "docs", "it", "about.md"), "a", encoding="utf-8") as fh:
            fh.write("\n[uno](/why/) [due](https://digline.dev/why/?x=1#the-model-changes-under-you) [tre](../why.md#a-prompt-is-not-code) "
                     "[quattro](/product/guide/) [cinque](../start.md) [sei](../index.md)\n")
        # And the Italian Why behind its original — English Why changed after it
        # was made — with two of its headings swapped: as many headings, at the
        # same levels, and still its own ids, since it is behind.
        english_why_md = os.path.join(root, "docs", "why.md")
        with open(english_why_md, encoding="utf-8") as fh:
            english_why_text = fh.read()
        with open(english_why_md, "a", encoding="utf-8") as fh:
            fh.write("\nOne sentence more in English.\n")
        it_why_md = os.path.join(root, "docs", "it", "why.md")
        with open(it_why_md, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
        h2 = [i for i, line in enumerate(lines) if line.startswith("## ")]
        lines[h2[0]], lines[h2[1]] = lines[h2[1]], lines[h2[0]]
        with open(it_why_md, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines))
        rebuilt = _build(root)
        if rebuilt.returncode != 0:
            print(rebuilt.stdout[-3000:] + rebuilt.stderr[-3000:], file=sys.stderr)
            failures.append("the fixture with Italian Start added did not build")
        else:
            with_start = dict(groups, **{"start.md": {"it": "it/start.md"}})
            home = _read(site, "it/index.html")
            about_html = _read(site, "it/about/index.html")
            body = re.findall(r'<a href="([^"]*)">(?:uno|due|tre|quattro|cinque|sei)</a>', about_html)
            expect("Italian Start added in the test: the Italian home's Start now leads to /it/start/",
                   ('class="hero__link--primary" href="../it/start/"' in home, 'href="../start/"' in home), (True, False))
            expect("links in a translation's Markdown: to /it/ with query and fragment, the documentation in English",
                   body, ["/it/why/", "https://digline.dev/it/why/?x=1#the-model-changes-under-you", "../../it/why/#a-prompt-is-not-code", "/product/guide/",
                          "../../it/start/", "../../it/"])
            expect("the link gate on it, and the post-build check", (link_problems(site, with_start, SITE_URL)[0],
                                                                     check_site(site, with_start, SITE_URL)[0]), ([], []))
            output = rebuilt.stdout + rebuilt.stderr
            expect("the Italian Why behind its original, headings swapped: its own ids, the build passes",
                   (heading_ids("it/why/index.html") != heading_ids("why/index.html"),
                    len(heading_ids("it/why/index.html")) == len(heading_ids("why/index.html"))), (True, True))
            expect("links with English ids to the Italian Why, behind: warnings in the build, not errors",
                   (output.count("WARNING -  translations:") >= 2, "(a translation behind its original" in output), (True, True))
            errors, warnings, _ = anchor_problems(site, SITE_URL, {"/it/why/"})
            expect("the anchor gate: to a translation behind, the missing ids are warnings",
                   (errors, len(warnings) >= 2), ([], True))
            groups = with_start
            found = planted("it/index.html", '<a href="../start/">x</a>')
            expect("the link gate: ../start/ from /it/, once Start is translated, is refused",
                   any("leads to the English /start/" in p for p in found), True)

        # A translation up to date with its original, with a heading fewer: the
        # build fails. English Why as it was, so German Why is up to date again.
        with open(english_why_md, "w", encoding="utf-8") as fh:
            fh.write(english_why_text)
        de_why = os.path.join(root, "docs", "de", "why.md")
        with open(de_why, encoding="utf-8") as fh:
            de_text = fh.read()
        with open(de_why, "w", encoding="utf-8") as fh:
            fh.write(re.sub(r"(?m)^## [^\n]*\n", "", de_text, count=1))
        fewer = _build(root)
        with open(de_why, "w", encoding="utf-8") as fh:
            fh.write(de_text)
        if fewer.returncode == 0 or "de/why.md: its headings are" not in fewer.stdout + fewer.stderr:
            failures.append("a translation up to date with a heading fewer: the build was not refused for it")
        else:
            print("translations selftest: refused, as it must — an up-to-date translation with a heading fewer")

        # 5. A translation that does not hold together stops the real build.
        about = os.path.join(root, "docs", "it", "about.md")
        with open(about, encoding="utf-8") as fh:
            text = fh.read()
        with open(about, "w", encoding="utf-8") as fh:
            fh.write(re.sub(r"(?m)^description:[^\n]*\n(?:  [^\n]*\n)*", "", text, count=1))
        refused = _build(root)
        if refused.returncode == 0 or "docs/it/about.md: no description of its own" not in refused.stdout + refused.stderr:
            failures.append("a translation with no description: the build was not refused for it")
        else:
            print("translations selftest: refused, as it must — a build with a translation that has no description")

    for failure in failures:
        print(f"translations selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("translations selftest: refusals on front matter; the fixture builds with --strict — hreflang on "
          "the seven translated pages and their eight translations and on nothing else, their languages, the "
          "bar, the footer and the closing band on a translation, the Handbook's index and chapter 3 in Italian "
          "with their links, their <html lang>, the bar's current entry and the pager, out of search and llms.txt, in the "
          "sitemap, and check-llms, check-translate, check-sitemap, check-glyphs and check-bar pass on it; the "
          "language menu on the fifteen pages with alternatives, the Handbook's eight included, right, and on "
          "no other; tamperings refused; a translation with no description stops the build")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        raise SystemExit(selftest())
    print(__doc__.split("\n\n")[-2], file=sys.stderr)
    raise SystemExit(2)
