#!/usr/bin/env -S uv run python
"""No code on the site is offered to a translator, and every page says it is English.

tools/hooks/notranslate.py puts ``translate="no"`` on every <pre> and <code> of
the rendered Markdown, and the templates in overrides/ put it on theirs. This
reads the build and fails when that is not what was written:

  * a <pre> or a <code>, on any page, without ``translate="no"`` — a missing
    attribute, ``translate="yes"``, or a bare ``translate``, which the HTML
    standard reads as yes;
  * a ``translate="yes"`` (or a bare ``translate``) on anything inside a <pre>
    or a <code>, except one: an element of class ``out__note`` inside a <pre>
    — a line the site writes among lines digline printed, like the two
    questions under the scores on the home. A .out__note that says yes outside
    a <pre>, or inside a <code> alone, is refused too;
  * a page whose <html> does not carry its language — ``lang="en"``, or on a
    translation under docs/<lang>/ that ``lang`` (tools/languages.py) — or
    that has no <html>;
  * a site with no page, no <pre> or no <code> at all, which cannot be right
    and would pass by counting nothing.

The page is parsed, not searched: a "<code>" inside a script is a string, not
a tag, and is not counted.

    usage: tools/check-translate.py site
           tools/check-translate.py --selftest

--selftest needs no build: it writes a two-page site — one page as a
template writes it, one run through the hook, with a code block in Pygments'
shape, and a .out__note saying yes inside an output <pre> — and checks that
it passes and counts its tags and its note, then plants each failure in turn
and checks that each is refused.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools", "hooks"))

import notranslate  # noqa: E402  the hook, for the selftest's second page

sys.path.insert(0, os.path.join(ROOT, "tools"))
import languages  # noqa: E402  tools/languages.py

LANG = "en"
CODE_TAGS = ("pre", "code")

# The one element a translator is let back into, inside a <pre>.
NOTE = "out__note"


def _says_yes(value: str | None) -> bool:
    """translate="yes", or a bare translate, which the standard reads as yes."""
    return (value or "").strip().lower() in ("", "yes")


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang: str | None = None
        self.has_html = False
        self.counts = {tag: 0 for tag in CODE_TAGS}
        self.notes = 0
        self.wrong: list[str] = []
        # How many of each are open where the parser is: a <code> in a <pre>.
        self.open = {tag: 0 for tag in CODE_TAGS}

    def handle_starttag(self, tag, attrs, void=False):
        attrs = dict(attrs)
        if tag == "html" and not self.has_html:
            self.has_html = True
            self.lang = attrs.get("lang")
        elif tag in CODE_TAGS:
            self.counts[tag] += 1
            if "translate" not in attrs:
                self.wrong.append(f"<{tag}> without translate")
            elif (attrs["translate"] or "").strip().lower() != "no":
                self.wrong.append(f'<{tag} translate="{attrs["translate"] or ""}">')
        elif "translate" in attrs and _says_yes(attrs["translate"]):
            note = NOTE in (attrs.get("class") or "").split()
            if note and self.open["pre"]:
                self.notes += 1
            elif note:
                self.wrong.append(f'<{tag} class="{NOTE}" translate="yes"> outside a <pre>')
            elif any(self.open.values()):
                inside = "pre" if self.open["pre"] else "code"
                self.wrong.append(f'<{tag} translate="yes"> inside a <{inside}>, not a .{NOTE}')
        if tag in CODE_TAGS and not void:
            self.open[tag] += 1

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs, void=True)

    def handle_endtag(self, tag):
        if tag in CODE_TAGS and self.open[tag]:
            self.open[tag] -= 1


def check(site: str) -> tuple[list[str], dict[str, int]]:
    problems: list[str] = []
    counted = {"pages": 0, **{tag: 0 for tag in CODE_TAGS}, "notes": 0}
    for folder, dirs, names in os.walk(site):
        dirs.sort()
        for name in sorted(names):
            if not name.endswith(".html"):
                continue
            path = os.path.join(folder, name)
            rel = os.path.relpath(path, site).replace(os.sep, "/")
            parser = _Page()
            with open(path, encoding="utf-8") as fh:
                parser.feed(fh.read())
            parser.close()
            counted["pages"] += 1
            for tag in CODE_TAGS:
                counted[tag] += parser.counts[tag]
            counted["notes"] += parser.notes
            if not parser.has_html:
                problems.append(f"{rel}: no <html>")
            elif parser.lang != (languages.language_of(rel) or LANG):
                expected = languages.language_of(rel) or LANG
                problems.append(f'{rel}: <html lang="{parser.lang}">, not lang="{expected}"'
                                if parser.lang is not None else f"{rel}: <html> without lang")
            if parser.wrong:
                shown = sorted(set(parser.wrong))
                problems.append(f"{rel}: {len(parser.wrong)} tag(s) a translator may rewrite — "
                                + ", ".join(shown))
    if not counted["pages"]:
        problems.append(f"{site}: no page at all")
    for tag in CODE_TAGS:
        if counted["pages"] and not counted[tag]:
            problems.append(f"{site}: no <{tag}> on any page, which cannot be right")
    return problems, counted


def selftest() -> int:
    failures: list[str] = []
    template = ('<!doctype html><html lang="en"><body><main class="dg-page">'
                '<code translate="no" class="install__cmd">pip install digline</code>'
                '<pre translate="no" class="out"><span class="out__line">exit 1</span>'
                '<span class="out__line quiet out__note" translate="yes">Nothing here says.</span></pre>'
                "<script>var s = '<code>not a tag</code>';</script></main></body></html>")
    rendered = notranslate.no_translate(
        '<p>Run <code>digline run</code>.</p>'
        '<div class="highlight"><pre><span></span><code><span class="gp">$ </span>digline compare</code></pre></div>'
        '<p>Already said: <code translate="no">x</code>, and &lt;code&gt; as text.</p>')
    docs = f'<!doctype html><html lang="en" class="no-js"><body><article>{rendered}</article></body></html>'
    if '&lt;code translate' in rendered or rendered.count('translate="no"') != 4:
        failures.append(f"the hook did not mark exactly the three untagged tags: {rendered}")

    with tempfile.TemporaryDirectory() as site:
        os.makedirs(os.path.join(site, "product", "guide"))
        home = os.path.join(site, "index.html")
        guide = os.path.join(site, "product", "guide", "index.html")

        def write(home_html: str = template, guide_html: str = docs) -> None:
            for path, html in ((home, home_html), (guide, guide_html)):
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(html)

        write()
        problems, counted = check(site)
        if problems:
            failures.append(f"a clean site was refused: {problems}")
        expected = {"pages": 2, "pre": 2, "code": 4, "notes": 1}
        if counted != expected:
            failures.append(f"the clean site should count {expected}, counted {counted}")

        planted = [
            ("a <pre> without translate",
             lambda: write(template.replace('<pre translate="no"', "<pre")), "<pre> without translate"),
            ("a <code> without translate, on a page Material renders",
             lambda: write(guide_html=docs.replace('<code translate="no"><span class="gp">', '<code><span class="gp">')),
             "<code> without translate"),
            ('translate="yes"',
             lambda: write(template.replace('<code translate="no"', '<code translate="yes"')), '<code translate="yes">'),
            ("a bare translate attribute",
             lambda: write(template.replace('<code translate="no"', "<code translate")), '<code translate="">'),
            ("an upper-case tag without translate",
             lambda: write(template.replace('<pre translate="no"', "<PRE")), "<pre> without translate"),
            ("a page in another language",
             lambda: write(template.replace('lang="en"', 'lang="it"')), 'lang="it"'),
            ("a page without lang",
             lambda: write(guide_html=docs.replace(' lang="en"', "")), "<html> without lang"),
            ("a page without <html>",
             lambda: write(template.replace('<html lang="en">', "")), "no <html>"),
            ('translate="yes" inside a <pre>, on a line that is not a .out__note',
             lambda: write(template.replace("quiet out__note", "quiet")),
             'translate="yes"> inside a <pre>, not a .out__note'),
            ('translate="yes" inside a <code> in a code block, on a Pygments span',
             lambda: write(guide_html=docs.replace('<span class="gp">', '<span class="gp" translate="yes">')),
             'translate="yes"> inside a <pre>, not a .out__note'),
            ('a .out__note saying yes inside an inline <code>, with no <pre> round it',
             lambda: write(guide_html=docs.replace("digline run</code>",
                                                   '<span class="out__note" translate="yes">digline run</span></code>')),
             'class="out__note" translate="yes"> outside a <pre>'),
            ('a .out__note saying yes outside any <pre> or <code>',
             lambda: write(template.replace("</main>", '<p class="out__note" translate>x</p></main>')),
             'class="out__note" translate="yes"> outside a <pre>'),
            ("a site without any <pre>",
             lambda: write(template.replace("<pre", "<div").replace("</pre>", "</div>"),
                           docs.replace("<pre", "<div").replace("</pre>", "</div>")),
             "no <pre> on any page"),
        ]
        for label, plant, needle in planted:
            plant()
            problems, _ = check(site)
            if not any(needle in p for p in problems):
                failures.append(f"{label}: not refused ({problems})")
            else:
                print(f"translate selftest: refused, as it must — {label}")

        # A translation, under a language's folder (tools/languages.py): its own
        # language passes, English there is refused, and so is an English page
        # that says it is Italian beside it.
        write()
        italian = os.path.join(site, "it")
        os.makedirs(italian)
        for label, home_html, translated_html, needle in (
            ("a translation in its own language", template, template.replace('lang="en"', 'lang="it"'), None),
            ("a translation that says it is English", template, template, 'it/index.html: <html lang="en">, not lang="it"'),
            ("an English page that says it is Italian", template.replace('lang="en"', 'lang="it"'),
             template.replace('lang="en"', 'lang="it"'), 'index.html: <html lang="it">, not lang="en"'),
        ):
            write(home_html)
            with open(os.path.join(italian, "index.html"), "w", encoding="utf-8") as fh:
                fh.write(translated_html)
            problems, _ = check(site)
            if needle is None and problems:
                failures.append(f"{label}: refused ({problems})")
            elif needle is not None and not any(p.startswith(needle) for p in problems):
                failures.append(f"{label}: not refused ({problems})")
            elif needle is not None:
                print(f"translate selftest: refused, as it must — {label}")
        shutil.rmtree(italian)
        write()

        shutil.rmtree(os.path.join(site, "product"))
        os.remove(home)
        problems, _ = check(site)
        if not any("no page at all" in p for p in problems):
            failures.append(f"an empty site: not refused ({problems})")
        else:
            print("translate selftest: refused, as it must — an empty site")

    for failure in failures:
        print(f"translate selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("translate selftest: a clean site passes with 2 pages, 2 <pre>, 4 <code> and 1 .out__note "
          "counted, a <script> string not among them; every planted failure refused")
    return 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    if len(argv) != 1:
        print(__doc__.split("\n\n")[-2], file=sys.stderr)
        return 2
    problems, counted = check(argv[0])
    for problem in problems:
        print(f"translate: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"translate: {counted['pages']} pages, every one lang=\"{LANG}\"; "
          f"{counted['pre']} <pre> and {counted['code']} <code>, every one translate=\"no\"; "
          f"{counted['notes']} .{NOTE} translate=\"yes\" inside a <pre>, and no other yes inside one")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
