#!/usr/bin/env -S uv run python
"""No code on the site is offered to a translator, and every page says it is English.

tools/hooks/notranslate.py puts ``translate="no"`` on every <pre> and <code> of
the rendered Markdown, and the templates in overrides/ put it on theirs. This
reads the build and fails when that is not what was written:

  * a <pre> or a <code>, on any page, without ``translate="no"`` — a missing
    attribute, ``translate="yes"``, or a bare ``translate``, which the HTML
    standard reads as yes;
  * a page whose <html> does not carry ``lang="en"``, or that has no <html>;
  * a site with no page, no <pre> or no <code> at all, which cannot be right
    and would pass by counting nothing.

The page is parsed, not searched: a "<code>" inside a script is a string, not
a tag, and is not counted.

    usage: tools/check-translate.py site
           tools/check-translate.py --selftest

--selftest needs no build: it writes a two-page site — one page as a
template writes it, one run through the hook, with a code block in Pygments'
shape — and checks that it passes and counts its tags, then plants each
failure in turn and checks that each is refused.
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

LANG = "en"
CODE_TAGS = ("pre", "code")


class _Page(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.lang: str | None = None
        self.has_html = False
        self.counts = {tag: 0 for tag in CODE_TAGS}
        self.wrong: list[str] = []

    def handle_starttag(self, tag, attrs):
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

    handle_startendtag = handle_starttag


def check(site: str) -> tuple[list[str], dict[str, int]]:
    problems: list[str] = []
    counted = {"pages": 0, **{tag: 0 for tag in CODE_TAGS}}
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
            if not parser.has_html:
                problems.append(f"{rel}: no <html>")
            elif parser.lang != LANG:
                problems.append(f'{rel}: <html lang="{parser.lang}">, not lang="{LANG}"'
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
                '<pre translate="no" class="out"><span class="out__line">exit 1</span></pre>'
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
        expected = {"pages": 2, "pre": 2, "code": 4}
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
    print("translate selftest: a clean site passes with 2 pages, 2 <pre> and 4 <code> counted, "
          "a <script> string not among them; every planted failure refused")
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
          f"{counted['pre']} <pre> and {counted['code']} <code>, every one translate=\"no\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
