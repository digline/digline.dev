"""The catalog of the site's words: the `t` filter, and the check before the build.

The templates in overrides/ and tools/hooks/home.py name the words they show
by key; i18n/en.yml holds them. tools/catalog.py reads the file and says how a
value is written. This hook does two things with it:

  * ``on_env`` gives the templates the filter, ``{{ "home.hero.lede" | t }}``,
    with its arguments by name: ``| t(count=n)`` for a plural,
    ``| t(version=home.version)`` for a placeholder. It is ``catalog.t`` in
    the language of the page being rendered (``catalog.page_language``).
  * ``on_config``, before anything renders, reads every template and every
    hook and fails the build on what the catalog and the source disagree about:

      - a key named in the source that the catalog does not have;
      - a key in the catalog that nothing names;
      - a key that is not a literal string, which no check can follow;
      - a plural named without ``count=``, or ``count=`` on a key that is not a
        plural;
      - a placeholder no argument fills, or an argument no placeholder uses,
        where the source shows its arguments;
      - a catalog that is not one: a key written twice, a plural that is not
        exactly ``one`` and ``other``, a value YAML read as something other
        than a string.

    Templates are read as Jinja's syntax tree, Python as its own, so a key in
    a comment or a docstring is not a use.

    usage: tools/hooks/i18n.py --selftest

--selftest needs no build: it writes a catalog, a template and a hook of its
own, checks that they agree and that ``t`` prints what it must — a plural
either way, a number in words and past them in digits, a placeholder, a value
over two lines — then plants each disagreement in turn and checks that each is
refused, before the build and at the call.
"""

from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import catalog  # noqa: E402  tools/catalog.py

from mkdocs.exceptions import PluginError  # noqa: E402


def on_config(config, **kwargs):
    catalog.default.cache_clear()
    problems, counted = catalog.scan(catalog.default(), catalog.sources(),
                                     translations=catalog.translation_catalogs())
    if problems:
        raise PluginError(
            f"i18n: {len(problems)} disagreement(s) between i18n/en.yml and the source that "
            "names its keys:\n  " + "\n  ".join(problems))
    return config


def on_env(env, config, files, **kwargs):
    env.filters["t"] = catalog.template_filter()
    return env


# ── the selftest ─────────────────────────────────────────────────────────────

CATALOG = '''\
numbers:
  1: "one"
  2: "two"
page:
  title: "Hello"
  lede: "It&rsquo;s {name}."
  count:
    one: "{Number} thing"
    other: "{Number} things"
  block: |-
    first
      second
'''

TEMPLATE = '''\
{#- "page.ghost" | t: a comment, not a use -#}
<h1>{{ "page.title" | t }}</h1>
<p>{{ 'page.lede' | t(name=who) }}</p>
'''

HOOK = '''\
"""t("page.ghost") in a docstring is not a use either."""
from catalog import t
HEADING = t("page.count", count=n)
BLOCK = t("page.block")
'''


def selftest() -> int:
    failures: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        paths = {name: os.path.join(tmp, name) for name in ("en.yml", "page.html", "hook.py")}

        def write(catalog_text=CATALOG, template=TEMPLATE, hook=HOOK):
            for (name, path), text in zip(paths.items(), (catalog_text, template, hook)):
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(text)

        def files():
            return [(paths["page.html"], "template"), (paths["hook.py"], "python")]

        write()
        clean = catalog.Catalog(paths["en.yml"])
        problems, counted = catalog.scan(clean, files(), tmp)
        if problems:
            failures.append(f"a catalog and a source that agree were refused: {problems}")
        if counted != {"keys": 6, "uses": 4, "files": 2}:
            failures.append(f"the clean pair should count 6 keys, 4 uses in 2 files; counted {counted}")

        translate = clean.t
        printed = [
            ("a plural, one", lambda: translate("page.count", count=1), "One thing"),
            ("a plural, other, in words", lambda: translate("page.count", count=2), "Two things"),
            ("a plural past the words, in digits", lambda: translate("page.count", count=21), "21 things"),
            ("a placeholder, the entity as written", lambda: translate("page.lede", name="digline"), "It&rsquo;s digline."),
            ("a value over two lines", lambda: translate("page.block"), "first\n  second"),
        ]
        for label, call, wanted in printed:
            got = call()
            if got != wanted:
                failures.append(f"{label}: printed {got!r}, wanted {wanted!r}")

        before_build = [
            ("a key the template names and the catalog does not have",
             dict(template=TEMPLATE.replace("page.title", "page.subtitle")), "'page.subtitle' is not in the catalog"),
            ("a key a hook names and the catalog does not have",
             dict(hook=HOOK.replace("page.block", "page.blocks")), "'page.blocks' is not in the catalog"),
            ("a key in the catalog nothing names",
             dict(catalog_text=CATALOG + '  unused: "Nobody"\n'), "page.unused is in the catalog, and nothing uses it"),
            ("a key the template does not write out",
             dict(template=TEMPLATE.replace('"page.title" | t', "title_key | t")), "a key that is not written out"),
            ("a key a hook does not write out",
             dict(hook=HOOK.replace('t("page.block")', "t(key)")), "a key that is not written out"),
            ("a plural without count=",
             dict(hook=HOOK.replace('t("page.count", count=n)', 't("page.count")')), "is a plural, and no count= is passed"),
            ("count= on a key that is not a plural",
             dict(template=TEMPLATE.replace('"page.title" | t', '"page.title" | t(count=2)')), "is not a plural, and count= is passed"),
            ("a placeholder nothing fills",
             dict(template=TEMPLATE.replace("t(name=who)", "t")), "page.lede needs {name}"),
            ("an argument no placeholder uses",
             dict(template=TEMPLATE.replace("t(name=who)", "t(name=who, extra=1)")), "page.lede has no {extra}"),
            ("the numbers, once no plural writes {number}",
             dict(catalog_text=CATALOG.replace("{Number}", "{count}")), "numbers.1 is in the catalog, and nothing uses it"),
        ]
        for label, change, needle in before_build:
            write(**change)
            try:
                problems, _ = catalog.scan(catalog.Catalog(paths["en.yml"]), files(), tmp)
            except PluginError as error:
                problems = [str(error)]
            if not any(needle in p for p in problems):
                failures.append(f"{label}: not refused ({problems})")
            else:
                print(f"i18n selftest: refused, as it must — {label}")

        # The fixed section: in every language's catalog, not in en.yml.
        fixed_template = TEMPLATE + '<p>{{ "do_not_translate.notice" | t }}</p>\n'
        languages_dir = {}
        for lang, text in (("it", 'do_not_translate:\n  notice: "Tradotto."\n'),
                           ("de", 'do_not_translate:\n  notice: "Übersetzt."\n')):
            path = os.path.join(tmp, f"{lang}.yml")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            languages_dir[lang] = path
        write(template=fixed_template)
        found, _ = catalog.scan(catalog.Catalog(paths["en.yml"]), files(), tmp,
                                translations={lang: catalog.Catalog(path) for lang, path in languages_dir.items()})
        if found:
            failures.append(f"fixed text in every language's catalog, and used, was refused: {found}")
        fixed_cases = [
            ("fixed text one language's catalog lacks", fixed_template.replace("notice", "stale"),
             {"it": 'do_not_translate:\n  notice: "Tradotto."\n  stale: "Cambiato."\n', "de": 'do_not_translate:\n  notice: "Übersetzt."\n'},
             CATALOG, "'do_not_translate.stale' is not in i18n/de.yml"),
            ("fixed text a language's catalog holds and nothing uses", fixed_template,
             {"it": 'do_not_translate:\n  notice: "Tradotto."\n  stale: "Cambiato."\n', "de": 'do_not_translate:\n  notice: "Übersetzt."\n'},
             CATALOG, "i18n/it.yml: do_not_translate.stale is fixed text, and nothing uses it"),
            ("fixed text in en.yml", TEMPLATE,
             {}, CATALOG + 'do_not_translate:\n  notice: "Translated."\n', "do_not_translate.notice is fixed text, which the original"),
        ]
        for label, template, texts, catalog_text, needle in fixed_cases:
            write(catalog_text=catalog_text, template=template)
            others = {}
            for lang, text in texts.items():
                with open(languages_dir[lang], "w", encoding="utf-8") as fh:
                    fh.write(text)
                others[lang] = catalog.Catalog(languages_dir[lang])
            found, _ = catalog.scan(catalog.Catalog(paths["en.yml"]), files(), tmp, translations=others)
            if not any(needle in p for p in found):
                failures.append(f"{label}: not refused ({found})")
            else:
                print(f"i18n selftest: refused, as it must — {label}")

        not_a_catalog = [
            ("a key written twice", CATALOG + '  title: "Again"\n', "is written twice"),
            ("a plural that is not exactly one and other",
             CATALOG.replace('    one: "{Number} thing"\n', '    few: "{Number} things"\n'), "a plural has exactly"),
            ("a word YAML reads as a boolean", CATALOG.replace('"Hello"', "no"), "a value is a string"),
            ("a key with a capital", CATALOG.replace("  title:", "  Title:"), "a key is lower-case"),
        ]
        for label, text, needle in not_a_catalog:
            write(catalog_text=text)
            try:
                catalog.Catalog(paths["en.yml"])
                failures.append(f"{label}: read as a catalog")
            except PluginError as error:
                if needle in str(error):
                    print(f"i18n selftest: refused, as it must — {label}")
                else:
                    failures.append(f"{label}: refused, but not for this: {error}")

        at_the_call = [
            ("a key the catalog does not have", lambda: translate("page.subtitle"), "no key"),
            ("a plural without a count", lambda: translate("page.count"), "was given no count"),
            ("a count on a key that is not a plural", lambda: translate("page.title", count=1), "was given a count"),
            ("a placeholder not given", lambda: translate("page.lede"), "needs name"),
            ("an argument with no placeholder", lambda: translate("page.title", extra=1), "has no placeholder for extra"),
        ]
        for label, call, needle in at_the_call:
            try:
                call()
                failures.append(f"at the call, {label}: accepted")
            except PluginError as error:
                if needle in str(error):
                    print(f"i18n selftest: refused at the call, as it must — {label}")
                else:
                    failures.append(f"at the call, {label}: refused, but not for this: {error}")

    for failure in failures:
        print(f"i18n selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print("i18n selftest: a catalog and a source that agree pass, 6 keys and 4 uses counted, a key in a "
          "comment or a docstring not among them; t prints plurals, numbers, placeholders and a "
          "value over two lines as written; every disagreement refused")
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        raise SystemExit(selftest())
    print(__doc__.split("\n\n")[-2], file=sys.stderr)
    raise SystemExit(2)
