"""The translations of the presentation pages: refused unless they hold together,
and linked to their originals with hreflang.

tools/languages.py says which languages and which pages, and how a translation
is written: docs/<lang>/<page>, its front matter naming its language and its
original. This hook does three things with them.

── before anything renders (on_files) ───────────────────────────────────────
Every file under a language's folder is read, and the build fails when

  * it is not one of the five presentation pages (languages.PAGES), at the
    path of its original: docs/it/why.md, not docs/it/perche.md nor
    docs/it/handbook/index.md;
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

── after the build (on_post_build) ──────────────────────────────────────────
Every page in site/ is read again, and the build fails when its hreflang
links are not exactly the ones its group should have — none, for a page with
no translation — or when a translation's <html lang> or og:locale is not its
language.

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
refused, and builds once more with a translation that has no description.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser

from urllib.parse import urljoin, urlsplit

import yaml
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
        return [f"{where}: only the presentation pages are translated ({', '.join(languages.PAGES)}), "
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
    _groups.clear()
    _groups.update(translations_in(files))
    return files


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


def on_post_build(config, **kwargs):
    problems, _ = check_site(config["site_dir"], _groups, config["site_url"])
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
        ("a page that is not a presentation page", "it/agents.md", dict(good, translation_of="agents.md"),
         "agents.md is not one of them"),
        ("a presentation page at another path", "it/perche.md", good, "perche.md is not one of them"),
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
    for name in ("mkdocs.yml", ".lastmod.tsv"):
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
        for name in sorted(os.listdir(os.path.join(FIXTURE, lang))):
            meta, _ = translation.read_page(os.path.join(FIXTURE, lang, name))
            with open(os.path.join(into, "docs", lang, name), "w", encoding="utf-8") as fh:
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
    for label, src_uri, meta, needle in _refusal_cases():
        found = refusals(src_uri, meta, originals, {"it", "de"})
        if needle is None:
            expect(label, found, [])
        elif not any(needle in p for p in found):
            failures.append(f"{label}: not refused ({found})")
        else:
            print(f"translations selftest: refused, as it must — {label}")

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
                  "about.md": {"it": "it/about.md"}}

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
        expect("the bar marks Why on /it/why/",
               bool(re.search(r'<a class="dg-nav__optional" href="[./]*why/" aria-current="page">', it_why)), True)
        closing = re.search(r'<p class="closing__links">(.*?)</p>', it_why, re.S).group(1)
        expect("the closing band leaves Why out on /it/why/", re.findall(r'href="[./]*([a-z/]*)"', closing),
               ["product/guide/", "agents/", "comparison/"])
        expect("the footer marks About on /it/about/",
               bool(re.search(r'href="[./]*about/" aria-current="page"', _read(site, "it/about/index.html"))), True)
        expect("the Italian home is the home", 'class="hero__title"' in _read(site, "it/index.html"), True)
        expect("the Italian Why links the Handbook in English",
               'href="../../handbook/01-what-you-are-shipping/"' in it_why, True)

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
               ["de/why/", "it/", "it/about/", "it/why/"])

        for script in ("check-llms.py", "check-translate.py", "check-sitemap.py", "check-glyphs.py"):
            run = subprocess.run([sys.executable, os.path.join(root, "tools", script), site],
                                 capture_output=True, text=True)
            expect(f"{script} on the built fixture", run.returncode, 0)
            if run.returncode:
                print(run.stdout[-1500:] + run.stderr[-1500:], file=sys.stderr)

        problems, counted = check_site(site, groups, SITE_URL)
        expect("the post-build check on the built fixture", problems, [])
        expect("hreflang links counted", counted["links"], 4 * 3 + 3 * 2 + 3 * 2)

        # The language menu: on the seven pages with alternatives, with the
        # languages each exists in, and on no other page.
        expect("language menus and their entries counted", (counted["menus"], counted["entries"]),
               (7, 3 * 3 + 2 * 2 + 2 * 2))
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
        for path in ("start/index.html", "contact/index.html", "product/guide/index.html", "404.html"):
            html = _read(site, path)
            expect(f"no language menu, and no script for one, on {path}",
                   (links(path).switches, "details.dg-lang" in html), (0, False))
        expect("the menu's script on a page with the menu", 'querySelector("details.dg-lang")' in _read(site, "why/index.html"), True)

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
    print("translations selftest: 11 refusals on front matter; the fixture builds with --strict — hreflang on "
          "the three translated pages and their four translations and on nothing else, their languages, the "
          "bar, the footer and the closing band on a translation, out of search and llms.txt, in the sitemap, "
          "and check-llms, check-translate, check-sitemap and check-glyphs pass on it; the language menu on the "
          "seven pages with alternatives, right, and on no other; 12 tamperings refused; a translation with no "
          "description stops the build")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        raise SystemExit(selftest())
    print(__doc__.split("\n\n")[-2], file=sys.stderr)
    raise SystemExit(2)
