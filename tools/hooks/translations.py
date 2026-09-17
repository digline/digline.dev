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


def on_page_context(context, page, config, nav, **kwargs):
    src_uri = page.file.src_uri
    original = src_uri.split("/", 1)[1] if languages.is_translation(src_uri) else src_uri
    if original in _groups:
        page.meta["hreflang"] = hreflang(original, _groups[original], config["site_url"])
    return context


class _Head(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang: str | None = None
        self.locale: str | None = None
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "html" and self.lang is None:
            self.lang = attrs.get("lang")
        elif tag == "meta" and attrs.get("property") == "og:locale":
            self.locale = attrs.get("content")
        elif tag == "link" and "hreflang" in attrs:
            self.links.append((attrs["hreflang"], attrs.get("href") or ""))

    handle_startendtag = handle_starttag


def check_site(site: str, groups: dict[str, dict[str, str]], site_url: str) -> tuple[list[str], dict]:
    """Every page's hreflang links against its group's, and every translation's
    language, as written into site/."""
    expected: dict[str, list[tuple[str, str]]] = {}
    language: dict[str, str] = {}
    for original, group in groups.items():
        links = [(link["lang"], link["href"]) for link in hreflang(original, group, site_url)]
        for src_uri in [original] + list(group.values()):
            path = languages.page_url(src_uri) + "index.html"
            expected[path] = links
            language[path] = languages.language_of(src_uri) or languages.ORIGINAL
    problems: list[str] = []
    counted = {"pages": 0, "links": 0}
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
            if path in language and languages.is_translation(path):
                if head.lang != language[path]:
                    problems.append(f"{path}: <html lang={head.lang!r}>, and the page is {language[path]}")
                if head.locale != language[path]:
                    problems.append(f"{path}: og:locale {head.locale!r}, and the page is {language[path]}")
    for path in expected:
        if not os.path.isfile(os.path.join(site, path)):
            problems.append(f"{path}: a page of a translated group, and site/ does not have it")
    return problems, counted


def on_post_build(config, **kwargs):
    problems, _ = check_site(config["site_dir"], _groups, config["site_url"])
    if problems:
        raise PluginError(f"translations: {len(problems)} problem(s) in site/:\n  " + "\n  ".join(problems))


# ── the selftest ─────────────────────────────────────────────────────────────

FIXTURE = os.path.join(ROOT, "tools", "testdata", "translations", "docs")
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

    for lang in sorted(os.listdir(FIXTURE)):
        os.makedirs(os.path.join(into, "docs", lang))
        for name in sorted(os.listdir(os.path.join(FIXTURE, lang))):
            meta, _ = translation.read_page(os.path.join(FIXTURE, lang, name))
            with open(os.path.join(into, "docs", lang, name), "w", encoding="utf-8") as fh:
                fh.write(translation.fake_translation(into, lang, meta))
        shutil.copy(os.path.join(ROOT, "i18n", "en.yml"), os.path.join(into, "i18n", f"{lang}.yml"))
    git = ["git", "-C", into, "-c", "user.name=selftest", "-c", "user.email=selftest@invalid",
           "-c", "commit.gpgsign=false"]
    subprocess.run(git[:3] + ["init", "-q"], check=True)
    subprocess.run(git + ["add", "-A"], check=True)
    subprocess.run(git + ["commit", "-q", "-m", "selftest"], check=True)


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

    # 2. The fixture, built.
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

        # 3. The built site, tampered with.
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
        ]
        for label, path, change, needle in tampering:
            found = tampered(path, change)
            if not any(needle in p for p in found):
                failures.append(f"{label}: not refused ({found})")
            else:
                print(f"translations selftest: refused, as it must — {label}")

        # 4. A translation that does not hold together stops the real build.
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
          "and check-llms, check-translate, check-sitemap and check-glyphs pass on it; 6 tamperings refused; a "
          "translation with no description stops the build")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        raise SystemExit(selftest())
    print(__doc__.split("\n\n")[-2], file=sys.stderr)
    raise SystemExit(2)
