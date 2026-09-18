#!/usr/bin/env -S uv run python
"""Every translation against its original: what a translator must not change.

For every translation of a presentation page — docs/<lang>/<page>.md, built
into site/<lang>/…/index.html — this reads the <main> of the translation and
of its English original as they were built, and fails when

  a) code: the text of each <pre>, and of each <code> outside one, is not the
     same sequence, in the same order. A line inside a <pre> that says
     translate="yes" (the home's .out__note lines) is the site's prose, not
     digline's output, and is left out;
  b) links: the href of each <a>, resolved against its page, is not the same
     sequence. A link to a page that has a translation in the language — the
     translation's /it/why/, the original's /why/ — counts as that page with
     the language's prefix taken off, and without its #fragment (a heading's
     id is translated with the heading). A link off the site must be the same
     character for character. A heading's own permalink, and a link to a
     #fragment of the page itself, count only as being there;
  c) numbers: the numbers written in digits in the text outside code are not
     the same numbers, as many times each. 0.88 stays 0.88: a decimal comma is
     another number, and nothing is normalized;
  d) headings: the levels of h1–h6, in order, are not the same;
  h) structure: the blocks of the content — every p, li, blockquote, hr, pre,
     table and heading, in order — are not the same sequence: a paragraph
     merged into the next, or split, or written twice, or dropped;
  e) the glossary, tools/i18n/glossary.yml: a term to keep that the original
     shows is not in the translation, or the translation uses one of its
     language's forbidden words outside code (tools/translation.py);
  f) the translation does not hold together: its original is not one of the
     five, its lang is not its folder's, it has no description, or it does not
     record what it was made from — source (its original), source_sha,
     source_commit, model, and for the home its catalog's source_keys; or its page does not
     carry exactly one notice (DISCLAIMER_REQUIRED) that it was translated by
     a model — the fixed words of its language, the stale ones once the
     original has changed, and a link to the original, hreflang "en",
     named with the day of source_commit. The link's words are the page's
     language, so it carries no lang of its own;
  g) the fixed words themselves — every language's do_not_translate section —
     are not the ones FIXED_TEXTS_DIGEST pins. The translating agent never
     changes them; a person who means to changes the digest with them.

It also says, for every translation, whether its original has changed since it
was translated (tools/translation.py, status()), and that is never a failure:
the English site must stay free to change. The exit status is 0 then. A
translation whose original has changed is not compared with it (a–e, h): it was
checked against the English it was made from, and the English it would be held
to now is another text. It is reported, its notice must say it is behind, and
the agent translates it again.

    usage: tools/check-translations.py site [--root DIR]
           tools/check-translations.py --fixed-digest [--root DIR]
           tools/check-translations.py --selftest

--root is the repository the site was built from (docs/, i18n/, tools/i18n/):
this one by default.

--selftest needs docs/product/ synced (`make docs`). It builds the fake
translations of tools/testdata/translations in a copy of the site
(tools/hooks/translations.py) — each an English page as it is today,
pseudo-translated — and checks that they pass and that each check counted
something; then plants a failure for each of a) to f) and checks that each is
refused; then changes an original and a catalog value and checks that the
change is reported, with exit status 0.
"""

from __future__ import annotations

import datetime
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
import languages  # noqa: E402  tools/languages.py
import translation  # noqa: E402  tools/translation.py

# Every translation carries the notice that a model translated it: the element
# with this attribute, in the opening band (overrides/partials/opening.html) or
# the home's status line.
DISCLAIMER_REQUIRED = True
DISCLAIMER_ATTRIBUTE = "data-translation-notice"

# The fixed words, as approved: tools/translation.py's fixed_digest() of the
# do_not_translate section of i18n/it.yml, de.yml and es.yml. A change to any of
# them is refused until this changes too — the explicit step that says the
# change is meant, and that no translating agent takes. To make it:
#     uv run tools/check-translations.py --fixed-digest
# and set this to what it prints, in the same commit, saying why.
FIXED_TEXTS_DIGEST = "9b8530d40d1f"

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
BLOCK = {"p", "li", "ul", "ol", "dl", "dt", "dd", "div", "section", "header", "footer", "article", "aside",
         "figure", "figcaption", "blockquote", "table", "tr", "td", "th", "h1", "h2", "h3", "h4", "h5", "h6",
         "pre", "br", "nav", "main"}
HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
# The blocks h) compares, in the order the page has them.
STRUCTURE = {"p", "li", "blockquote", "hr", "pre", "table"} | HEADINGS
NUMBER = re.compile(r"\d+(?:\.\d+)*")


class Main(HTMLParser):
    """What the checks read out of a page's <main>."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.depth = 0          # open elements inside <main>; 0 outside it
        self.done = False
        self.stack: list[tuple[str, bool, bool]] = []   # (tag, says translate="yes", is the notice)
        self.pre = 0
        self.code = 0
        self.yes = 0
        self.skip = 0           # script, style
        self.buffer: list[str] | None = None
        self.buffer_kind = ""
        self.code_texts: list[tuple[str, str]] = []
        self.hrefs: list[str] = []
        self.headings: list[str] = []
        self.blocks: list[str] = []
        self.prose: list[str] = []
        self.everything: list[str] = []
        self.notice = False
        self.notices = 0
        self.in_notice = 0
        self.notice_class = ""
        self.notice_text: list[str] = []
        self.notice_links: list[tuple[str, str | None, str | None]] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.done:
            return
        if not self.depth:
            if tag == "main":
                self.depth = 1
            return
        # The notice is the site's, not the translation's: it is read on its
        # own, and none of it — its date, its link — counts in a) to e).
        is_notice = DISCLAIMER_ATTRIBUTE in attrs
        if is_notice:
            self.notice = True
            self.notices += 1
            self.notice_class = attrs.get("class") or ""
        if is_notice or self.in_notice:
            if tag == "a" and "href" in attrs:
                self.notice_links.append((attrs["href"], attrs.get("hreflang"), attrs.get("lang")))
            if tag not in VOID:
                self.stack.append((tag, False, is_notice))
                self.depth += 1
                self.in_notice += int(is_notice)
            return
        # Every tag separates words for the glossary and the numbers: two
        # spans side by side are two words, not one ("LangChain" beside the
        # question under it).
        self.prose.append(" ")
        self.everything.append(" ")
        if tag in BLOCK and self.buffer is not None:
            self.buffer.append("\n")
        if tag in HEADINGS:
            self.headings.append(tag)
        if tag in STRUCTURE and not self.pre:
            self.blocks.append(tag)
        if tag == "a" and "href" in attrs and "headerlink" not in (attrs.get("class") or "").split():
            self.hrefs.append(attrs["href"])
        elif tag == "a" and "href" in attrs:
            self.hrefs.append("#")
        if tag in VOID:
            return
        value = attrs.get("translate", "no")
        yes = value is None or value.strip().lower() in ("", "yes")
        self.stack.append((tag, yes, False))
        self.depth += 1
        if tag in ("script", "style"):
            self.skip += 1
        if tag == "pre":
            if not self.pre:
                self.buffer, self.buffer_kind = [], "pre"
            self.pre += 1
        elif tag == "code":
            if not self.pre and not self.code:
                self.buffer, self.buffer_kind = [], "code"
            self.code += 1
        if yes:
            self.yes += 1

    def handle_endtag(self, tag):
        if not self.depth or self.done or tag in VOID:
            return
        if tag != "main" and all(entry[0] != tag for entry in self.stack):
            return  # an end tag with no start: nothing to close
        while self.stack:
            open_tag, yes, notice = self.stack.pop()
            self.depth -= 1
            if self.in_notice:
                self.in_notice -= int(notice)
                if open_tag == tag:
                    break
                continue
            if yes:
                self.yes -= 1
            if open_tag in ("script", "style"):
                self.skip -= 1
            if open_tag == "pre":
                self.pre -= 1
                if not self.pre and self.buffer is not None:
                    self.code_texts.append(("pre", "".join(self.buffer)))
                    self.buffer = None
            elif open_tag == "code":
                self.code -= 1
                if not self.pre and not self.code and self.buffer is not None:
                    self.code_texts.append(("code", "".join(self.buffer)))
                    self.buffer = None
            if open_tag == tag:
                break
        self.prose.append(" ")
        self.everything.append(" ")
        if self.depth <= 1 and tag == "main":
            self.done = True
            self.depth = 0

    def handle_data(self, data):
        if not self.depth or self.done or self.skip:
            return
        if self.in_notice:
            self.notice_text.append(data)
            return
        self.everything.append(data)
        if (self.pre or self.code) and not self.yes:
            if self.buffer is not None:
                self.buffer.append(data)
        else:
            self.prose.append(data)


def read_main(path: str) -> Main:
    parser = Main()
    with open(path, encoding="utf-8") as fh:
        parser.feed(fh.read())
    parser.close()
    return parser


def site_path(src_uri: str) -> str:
    return languages.page_url(src_uri) + "index.html"


def normalized_hrefs(page: Main, src_uri: str, lang: str, site: str) -> list[str]:
    """Each href of a page, resolved, a translated destination as its original."""
    base = "https://site.invalid/" + languages.page_url(src_uri)
    out = []
    for href in page.hrefs:
        if href == "#" or href.startswith("#"):
            out.append("#")
            continue
        parts = urlsplit(href)
        if parts.scheme or parts.netloc:
            out.append(href)
            continue
        resolved = urlsplit(urljoin(base, href))
        path = resolved.path
        prefix = f"/{lang}/"
        translated = path.startswith(prefix) and os.path.isfile(os.path.join(site, path[1:], "index.html"))
        if translated:
            path = "/" + path[len(prefix):]
        elif os.path.isfile(os.path.join(site, lang, path[1:], "index.html")) and not path.startswith(prefix):
            translated = True
        out.append(path if translated or not resolved.fragment else f"{path}#{resolved.fragment}")
    return out


def _sequence_problem(where: str, what: str, original: list, translated: list) -> str | None:
    if original == translated:
        return None
    for i, (a, b) in enumerate(zip(original, translated)):
        if a != b:
            return f"{where}: {what} {i + 1} is {b!r}, and the original's is {a!r}"
    return (f"{where}: {len(translated)} {what}(s), and the original has {len(original)}; the first one "
            f"apart: {(translated if len(translated) > len(original) else original)[min(len(original), len(translated))]!r}")


FIXED = "do_not_translate"
NOTICE_KEYS = ("notice", "original", "stale")


def notice_problems(page: "Main", here: str, src_uri: str, meta: dict, lang: str, stale: bool, root: str) -> list[str]:
    """What is wrong with a translation's notice, if anything."""
    if not page.notice:
        return [f"{here}: no notice that the page was translated by a model ({DISCLAIMER_ATTRIBUTE})"]
    problems = []
    if page.notices != 1:
        problems.append(f"{here}: {page.notices} notices, and a page carries one")
    words = translation.fixed_texts(root).get(lang, {})
    date = translation.commit_date(root, meta.get("source_commit"))
    if date is None:
        problems.append(f"{here}: the notice has no date — source_commit {meta.get('source_commit')!r} is not a "
                        "commit this repository has")
    state = f"{FIXED}.stale" if stale else f"{FIXED}.notice"
    original_words = words.get(f"{FIXED}.original", "").replace("{date}", date or "?")
    wanted = f"{words.get(state, '?')} {original_words}"
    text = " ".join("".join(page.notice_text).split())
    if text != wanted:
        problems.append(f"{here}: the notice says {text!r}, and it should say {wanted!r}"
                        + (" (the original has changed since the translation)" if stale else ""))
    marked = any(c.endswith("--stale") for c in page.notice_class.split())
    if marked != stale:
        problems.append(f"{here}: the notice is {'' if marked else 'not '}marked stale, and the original has "
                        f"{'' if stale else 'not '}changed")
    original_url = "/" + languages.page_url(meta.get("translation_of") or "")
    links = page.notice_links
    if len(links) != 1:
        problems.append(f"{here}: the notice has {len(links)} links, and it has one, to the original")
    else:
        href, hreflang, _ = links[0]
        resolved = urlsplit(urljoin("https://site.invalid/" + languages.page_url(src_uri), href)).path
        if resolved != original_url:
            problems.append(f"{here}: the notice links to {resolved}, and the original is {original_url}")
        if hreflang != "en":
            problems.append(f"{here}: the notice's link is hreflang={hreflang!r}, not \"en\"")
    return problems


def check(site: str, root: str = ROOT) -> tuple[list[str], list[str], dict]:
    """(problems, changed originals, what was counted) for every translation."""
    problems: list[str] = []
    changed: list[str] = []
    counted = Counter()
    words = translation.glossary(root)
    kept = [(label, re.compile(pattern)) for label, pattern in translation.kept_terms(root)]
    docs = os.path.join(root, "docs")

    sources = []
    for lang in languages.LANGUAGES:
        folder = os.path.join(docs, lang)
        if os.path.isdir(folder):
            sources += [f"{lang}/{name}" for name in sorted(os.listdir(folder)) if name.endswith(".md")]
    built = []
    for lang in languages.LANGUAGES:
        for folder, dirs, names in os.walk(os.path.join(site, lang)):
            dirs.sort()
            built += [os.path.relpath(os.path.join(folder, n), site).replace(os.sep, "/") for n in names if n == "index.html"]
    for path in sorted(set(built) - {site_path(s) for s in sources}):
        problems.append(f"{path}: a page under a language's folder, with no translation in docs/ it was built from")

    # g) the fixed words
    fixed = translation.fixed_texts(root)
    for lang in languages.LANGUAGES:
        wanted = {f"{FIXED}.{key}" for key in NOTICE_KEYS}
        missing_keys = sorted(wanted - set(fixed.get(lang, {})))
        if missing_keys:
            problems.append(f"i18n/{lang}.yml: no fixed text for {', '.join(missing_keys)}")
    if translation.fixed_digest(root) != FIXED_TEXTS_DIGEST:
        problems.append("i18n/{" + ",".join(languages.LANGUAGES) + "}.yml: the fixed words (do_not_translate) are "
                        f"not the approved ones — digest {translation.fixed_digest(root)}, approved "
                        f"{FIXED_TEXTS_DIGEST}. A translation never changes them; if the change is meant, set "
                        "FIXED_TEXTS_DIGEST in tools/check-translations.py to the new digest, with a reason.")
    counted["fixed"] = sum(len(texts) for texts in fixed.values())

    for src_uri in sources:
        lang = languages.language_of(src_uri)
        where = f"docs/{src_uri}"
        meta, _ = translation.read_page(os.path.join(docs, src_uri))
        counted["translations"] += 1

        # f) holding together
        original = meta.get("translation_of")
        if original not in languages.PAGES or src_uri.split("/", 1)[1] != original:
            problems.append(f"{where}: translation_of {original!r} is not the presentation page at its path")
            continue
        if meta.get("lang") != lang:
            problems.append(f"{where}: lang {meta.get('lang')!r}, and it is in the {lang}/ folder")
        if not str(meta.get("description") or "").strip():
            problems.append(f"{where}: no description")
        missing = [field for field in translation.SOURCE_FIELDS if not str(meta.get(field) or "").strip()]
        if missing:
            problems.append(f"{where}: does not record what it was made from — no {', '.join(missing)}")
        if meta.get("source") and meta.get("source") != original:
            problems.append(f"{where}: source {meta.get('source')!r}, and it translates {original}")
        if meta.get("source_sha") and not translation.SHA.match(str(meta["source_sha"])):
            problems.append(f"{where}: source_sha {meta['source_sha']!r} is not twelve hex digits")
        if meta.get("source_commit") and not translation.COMMIT.match(str(meta["source_commit"])):
            problems.append(f"{where}: source_commit {meta['source_commit']!r} is not a commit")
        if original == translation.HOME:
            keys = translation.catalog_source_keys(root, lang)
            if not keys or not all(translation.SHA.match(str(v)) for v in keys.values()):
                problems.append(f"{where}: i18n/{lang}.yml records no source_keys, a digest per catalog key, "
                                "so the home cannot say whether its words are behind English")
        stale = False
        if not missing:
            for change in translation.status(meta, root):
                stale = True
                changed.append(f"{src_uri}: the original changed since it was translated — {change}")

        translated_path = os.path.join(site, site_path(src_uri))
        original_path = os.path.join(site, site_path(original))
        if not (os.path.isfile(translated_path) and os.path.isfile(original_path)):
            problems.append(f"{where}: {site_path(src_uri)} or {site_path(original)} is not in site/")
            continue
        page, english = read_main(translated_path), read_main(original_path)
        here = site_path(src_uri)
        if DISCLAIMER_REQUIRED:
            problems += notice_problems(page, here, src_uri, meta, lang, stale, root)
            counted["notices"] += page.notices
        if stale:
            counted["behind"] += 1
            continue

        # a) code
        problem = _sequence_problem(here, "code", english.code_texts, page.code_texts)
        if problem:
            problems.append(problem)
        counted["code"] += len(english.code_texts)

        # b) links
        problem = _sequence_problem(here, "link", normalized_hrefs(english, original, lang, site),
                                    normalized_hrefs(page, src_uri, lang, site))
        if problem:
            problems.append(problem)
        counted["links"] += len(english.hrefs)

        # c) numbers
        numbers = Counter(NUMBER.findall("".join(english.prose)))
        found = Counter(NUMBER.findall("".join(page.prose)))
        if numbers != found:
            lost, added = numbers - found, found - numbers
            problems.append(f"{here}: numbers differ from the original's — missing {sorted(lost.elements()) or 'none'}, "
                            f"not in the original {sorted(added.elements()) or 'none'}")
        counted["numbers"] += sum(numbers.values())

        # h) structure
        problem = _sequence_problem(here, "block", english.blocks, page.blocks)
        if problem:
            problems.append(problem.replace(": block ", ": structure — block ", 1).replace(" block(s)", " block(s) of structure"))
        counted["blocks"] += len(english.blocks)

        # d) headings
        problem = _sequence_problem(here, "heading", english.headings, page.headings)
        if problem:
            problems.append(problem)
        counted["headings"] += len(english.headings)

        # e) the glossary
        everything_en, everything = "".join(english.everything), "".join(page.everything)
        for label, pattern in kept:
            if pattern.search(everything_en):
                counted["kept"] += 1
                if not pattern.search(everything):
                    problems.append(f"{here}: the original has {label!r}, a term to keep, and the translation does not")
        prose = "".join(page.prose)
        for term in words["forbidden"].get(lang, []):
            hit = re.search(translation.term_pattern(term, True), prose)
            if hit:
                problems.append(f"{here}: {hit.group(0)!r} translates a term the glossary keeps (forbidden in {lang})")

    return problems, changed, counted


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    root = ROOT
    if "--root" in argv:
        i = argv.index("--root")
        root = argv[i + 1]
        argv = argv[:i] + argv[i + 2:]
    if argv == ["--fixed-digest"]:
        print(translation.fixed_digest(root))
        return 0
    if len(argv) != 1:
        print(__doc__.split("\n\n")[-3], file=sys.stderr)
        return 2
    problems, changed, counted = check(argv[0], root)
    for line in changed:
        print(f"translations: {line}")
    for problem in problems:
        print(f"translations: {problem}", file=sys.stderr)
    if problems:
        return 1
    if not counted["translations"]:
        print(f"translations: no translation in docs/, nothing to compare; the {counted['fixed']} fixed "
              "texts are the approved ones")
    else:
        print(f"translations: {counted['translations']} translation(s) against their originals — "
              f"{counted['code']} code, {counted['links']} links, {counted['numbers']} numbers, "
              f"{counted['headings']} headings, {counted['blocks']} blocks, {counted['kept']} kept terms, the same; "
              f"{counted['notices']} notice(s) right; {len(changed)} original(s) changed since translated, "
              f"{counted['behind']} translation(s) not compared with an original they were not made from")
    return 0


# ── the selftest ─────────────────────────────────────────────────────────────


def _hooks_translations():
    spec = importlib.util.spec_from_file_location("translations_hook", os.path.join(TOOLS, "hooks", "translations.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def selftest() -> int:
    failures: list[str] = []
    if not os.path.isfile(os.path.join(ROOT, "docs", "product", "guide.md")):
        print("translations selftest: docs/product/ is not synced; run `make docs` first.", file=sys.stderr)
        return 1
    hook = _hooks_translations()
    with tempfile.TemporaryDirectory() as root:
        hook._copy_site(root)
        built = hook._build(root)
        if built.returncode:
            print(built.stdout[-3000:] + built.stderr[-3000:], file=sys.stderr)
            print("translations selftest: the fixture did not build", file=sys.stderr)
            return 1
        site = os.path.join(root, "site")

        problems, changed, counted = check(site, root)
        if problems or changed:
            failures.append(f"the fixture's translations were refused or reported changed: {problems} {changed}")
        for what in ("translations", "code", "links", "numbers", "headings", "blocks", "kept"):
            if not counted[what]:
                failures.append(f"the fixture counted no {what}: a check that reads nothing passes anything")
        print(f"translations selftest: the fixture passes — {dict(counted)}")

        def edit(path, change):
            full = os.path.join(root, path)
            with open(full, encoding="utf-8") as fh:
                before = fh.read()
            after = change(before)
            if after == before:
                failures.append(f"a planted change to {path} changed nothing: {change}")
            with open(full, "w", encoding="utf-8") as fh:
                fh.write(after)
            return before

        def restore(path, before):
            with open(os.path.join(root, path), "w", encoding="utf-8") as fh:
                fh.write(before)

        def first_from(mark, pattern, replacement):
            def change(html):
                start = html.index(mark)
                head, rest = html[:start], html[start:]
                return head + re.sub(pattern, replacement, rest, count=1, flags=re.S)
            return change

        def first_in_main(pattern, replacement):
            return first_from("<main", pattern, replacement)

        # The page's text, after the opening band: the notice's date is the first
        # number in <main> and belongs to f), not to the checks a) to e).
        def first_in_article(pattern, replacement):
            return first_from('<article class="essay">', pattern, replacement)

        why = "site/it/why/index.html"
        planted = [
            ("a) a code span rewritten", why, first_in_main(r"(<code[^>]*>)pip install digline", r"\1pip installa digline"),
             "code "),
            ("a) a code span dropped", why, first_in_main(r"<code[^>]*>[^<]*</code>", ""), "code"),
            ("b) a link sent elsewhere", why, first_in_main(r'href="\.\./\.\./handbook/01-what-you-are-shipping/"',
                                                             'href="../../handbook/"'), "link "),
            ("b) an external link changed by a character", why,
             first_in_main(r'href="https://danluu\.com/exercise-7/"', 'href="https://danluu.com/exercise-8/"'), "link "),
            ("c) a decimal point made a comma", why, first_in_main(r"0\.91", "0,91"), "numbers differ"),
            # Neither plant names a number the page happens to carry: the page's
            # own numbers change as the page is written, and the check does not.
            # The first digits of the article's text — after a tag, so the 1 of
            # <h1> is not one — written out in words instead.
            ("c) a number dropped", why, first_in_article(r"(>[^<]*?)\b\d+\b", r"\1a number"), "numbers differ"),
            # A paragraph of the translation's own, with a number the original
            # has not got. c) reports it; h) reports the paragraph as well, since
            # a paragraph is a block — the needle below is c)'s message, so the
            # case passes on c) and not on h).
            ("c) a number the original has not got", why,
             first_in_article(r"</article>", "<p>42</p></article>"), "numbers differ"),
            ("d) a heading one level down", why, first_in_main(r"<h2([^>]*)>(.*?)</h2>", r"<h3\1>\2</h3>"), "heading "),
            ("h) two paragraphs merged into one", why,
             first_in_main(r"(<article class=\"essay\">.*?<p>(?:(?!</p>).)*)</p>\s*<p>", r"\1 "), "structure"),
            ("h) a paragraph written twice, further on", why,
             lambda html: (lambda m: html[:m.end()] + html[m.end():].replace("<hr", m.group(0) + "\n<hr", 1))(
                 re.search(r"<article class=\"essay\">\s*(<p>.*?</p>)", html, re.S)),
             "structure"),
            ("h) the last line written twice", why,
             lambda html: (lambda last: html.replace(last, last + "\n" + last, 1))(
                 re.findall(r"<p>[^\n]*?</p>(?=\s*</article>)", html, re.S)[-1]),
             "structure"),
            ("e) baseline translated wherever the home shows it", "site/it/index.html",
             lambda html: html[:html.index("<main")] + re.sub(r"(?i)(?<![\w-])baseline(?![\w-])",
                                                              "riferimento approvato", html[html.index("<main"):]),
             "'baseline', a term to keep"),
            ("e) a forbidden word, German", "site/de/why/index.html",
             first_in_main(r"(<p[^>]*>)", r"\1Die Basislinie "), "'Basislinie' translates a term"),
            ("e) a framework's name, read from the data, dropped from the home", "site/it/index.html",
             first_in_main(r'(<span class="stackrow__name">)LangChain(</span>)', r"\1Catena\2"),
             "'LangChain', a term to keep"),
            ("f) no description", "docs/it/about.md", lambda t: re.sub(r"\ndescription:[^\n]*(\n  [^\n]*)*", "", t, count=1),
             "docs/it/about.md: no description"),
            ("f) a lang that is not its folder's", "docs/it/about.md", lambda t: t.replace("lang: it", "lang: es", 1),
             "lang 'es', and it is in the it/ folder"),
            ("f) an original that is not one of the five", "docs/it/about.md",
             lambda t: t.replace("translation_of: about.md", "translation_of: agents.md", 1),
             "translation_of 'agents.md' is not the presentation page at its path"),
            ("f) no record of what it was made from", "docs/it/about.md",
             lambda t: re.sub(r"\nmodel:[^\n]*", "", t, count=1), "no model"),
            ("f) the home without its catalog digests", "i18n/it.yml",
             lambda t: re.sub(r"(?m)^source_keys:\n(?:[ ]+[^\n]*\n)*", "", t, count=1), "records no source_keys"),
        ]
        for label, path, change, needle in planted:
            before = edit(path, change)
            try:
                found, _, _ = check(site, root)
            finally:
                restore(path, before)
            if not any(needle in p for p in found):
                failures.append(f"{label}: not refused ({found})")
            else:
                print(f"translations selftest: refused, as it must — {label}")

        # b) the other half: a translation that links to a page translated into
        # its language — /it/why/ to the Italian home, /it/, where Why links to
        # /, with a #fragment the original does not have — passes. The hook
        # already writes ../../it/ there; the plant writes it as ../, with the
        # fragment.
        before = edit(why, first_in_main(r'<a href="\.\./\.\./it/"', '<a href="../#altrove"'))
        found, _, _ = check(site, root)
        restore(why, before)
        if found:
            failures.append(f"b) a link to the translation of the page the original links to was refused: {found}")
        else:
            print("translations selftest: passes, as it must — b) a link to the Italian home where Why links to the English one")

        # f) the notice: on every translation, once, dated by source_commit,
        # linking to its original in English.
        # The English site is committed on a day in the past (the hook's
        # ENGLISH_DATE), so a notice dated today is told apart from one dated
        # by its original's commit.
        git_day = hook.ENGLISH_DATE[:10]
        date = translation.commit_date(root, translation.read_page(os.path.join(root, "docs", "it", "why.md"))[0]["source_commit"])
        today = datetime.date.today().isoformat()
        if counted["notices"] != counted["translations"] or date != git_day or git_day == today:
            failures.append(f"f) the fixture's notices: {counted['notices']} for {counted['translations']} translations, "
                            f"dated {date}, the original's commit {git_day}, today {today}")
        it_why = read_main(os.path.join(site, "it", "why", "index.html"))
        expected = ("Tradotto dall'inglese con un modello AI. Originale in inglese del " + git_day,
                    [("../../why/", "en", None)])
        got = (" ".join("".join(it_why.notice_text).split()), it_why.notice_links)
        if got != expected:
            failures.append(f"f) the Italian Why's notice: {got}, wanted {expected}")
        home = read_main(os.path.join(site, "it", "index.html"))
        if home.notice_links != [("../", "en", None)] or "hero__notice" not in home.notice_class:
            failures.append(f"f) the Italian home's notice: {home.notice_class} {home.notice_links}")
        english = read_main(os.path.join(site, "why", "index.html"))
        if english.notice:
            failures.append("f) the English Why carries a notice")
        if not failures:
            print(f"translations selftest: a notice on each of the {counted['translations']} translations, dated "
                  f"{git_day} by the original's commit and not today, linking to its original with hreflang en; "
                  "none on English Why")

        notice_planted = [
            ("f) a translation without its notice", "site/it/about/index.html",
             first_in_main(r'<p class="opening__notice[^"]*" data-translation-notice>.*?</p>', ""), "no notice that the page"),
            ("f) a notice with another date", "site/it/about/index.html",
             first_in_main(r"(Originale in inglese del )\d{4}-\d{2}-\d{2}", r"\g<1>2020-01-01"), "the notice says"),
            ("f) a notice linking elsewhere", why,
             first_in_main(r'(data-translation-notice>.*?<a href=")\.\./\.\./why/', r"\1../../start/"), "the notice links to /start/"),
            ("f) a notice link with no hreflang", "site/de/why/index.html",
             first_in_main(r'(data-translation-notice>.*?<a [^>]*?) hreflang="en"', r"\1"), "hreflang=None"),
            ("f) a notice marked stale on an original that has not changed", "site/it/index.html",
             first_in_main(r'class="hero__notice"', 'class="hero__notice hero__notice--stale"'), "marked stale"),
            ("f) a notice in words that are not the fixed ones", "site/it/index.html",
             first_in_main(r"Tradotto dall'inglese con un modello AI\.", "Tradotto automaticamente."), "the notice says"),
            ("g) a fixed text changed in a catalog", "i18n/es.yml",
             lambda t: t.replace("con un modelo de IA.", "con inteligencia artificial.", 1), "the fixed words (do_not_translate) are not the approved ones"),
            ("g) a fixed text gone from a catalog", "i18n/de.yml",
             lambda t: re.sub(r"\n  stale:[^\n]*", "", t, count=1), "no fixed text for do_not_translate.stale"),
        ]
        for label, path, change, needle in notice_planted:
            before = edit(path, change)
            try:
                found, _, _ = check(site, root)
            finally:
                restore(path, before)
            if not any(needle in p for p in found):
                failures.append(f"{label}: not refused ({found})")
            else:
                print(f"translations selftest: refused, as it must — {label}")

        # The original changed, and the site built again: reported with exit
        # status 0, and the notices of its translations say so, marked.
        before_why = edit("docs/why.md", lambda t: t.replace("# Why\n", "# Why\n\nOne sentence more.\n", 1))
        before_catalog = edit("i18n/en.yml", lambda t: t.replace('lede: "The guide needs no key."',
                                                                  'lede: "The guide needs no API key."', 1))
        rebuilt = hook._build(root)
        run = subprocess.run([sys.executable, __file__, site, "--root", root], capture_output=True, text=True)
        stale_pages = {path: read_main(os.path.join(site, *path.split("/")))
                       for path in ("it/why/index.html", "de/why/index.html", "it/index.html", "it/about/index.html")}
        restore("docs/why.md", before_why)
        restore("i18n/en.yml", before_catalog)
        if rebuilt.returncode:
            failures.append(f"the site with a changed original did not build: {rebuilt.stdout[-1500:]}")
        if run.returncode != 0:
            failures.append(f"a changed original made the check fail: {run.returncode} {run.stderr[-1000:]}")
        for needle in ("it/why.md: the original changed since it was translated — why.md source_sha",
                       "de/why.md: the original changed since it was translated — why.md source_sha",
                       "it/index.md: the original changed since it was translated — 1 catalog key(s) changed: closing.lede"):
            if needle not in run.stdout:
                failures.append(f"a changed original was not reported: {needle!r} not in {run.stdout!r}")
        if "it/about.md: the original changed" in run.stdout:
            failures.append("an original that did not change was reported changed")
        stale_words = {"it/why/index.html": "L'originale inglese è cambiato dopo questa traduzione.",
                       "de/why/index.html": "Das englische Original wurde nach dieser Übersetzung geändert.",
                       "it/index.html": "L'originale inglese è cambiato dopo questa traduzione."}
        for path, parsed in stale_pages.items():
            text = " ".join("".join(parsed.notice_text).split())
            marked = any(c.endswith("--stale") for c in parsed.notice_class.split())
            if path in stale_words:
                if not (text.startswith(stale_words[path]) and marked and parsed.notice_links):
                    failures.append(f"{path}: the notice of a changed original is {text!r}, marked {marked}")
            elif marked or "cambiato" in text:
                failures.append(f"{path}: the notice of an unchanged original is {text!r}, marked {marked}")
        if not failures:
            print("translations selftest: a changed page and a changed catalog key reported, exit status 0; "
                  "the three notices say so, marked, with their links; About's does not")

    for failure in failures:
        print(f"translations selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print(f"translations selftest: the fixture's {counted['translations']} translations pass, each with its notice; "
          f"{len(planted) + len(notice_planted)} planted failures across a) to h) refused; a changed original "
          "reported, not refused, and shown stale on its translations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
