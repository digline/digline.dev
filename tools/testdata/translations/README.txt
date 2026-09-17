Fake translations, for the selftests of tools/hooks/translations.py and
tools/check-translations.py only.

Each file here is a translation's front matter and nothing else. A selftest
copies the site into a temporary directory and writes each translation there
with tools/translation.py, fake_translation(): this front matter, stamped with
what the translation was made from (source, source_sha, source_commit, model,
and for the home source_keys), over the text of the English page as it is at
that moment, pseudo-translated — code, links, numbers, headings and the terms
to keep left as they are, every other word given a suffix (ẞ in German). Each
language gets a catalog that is a copy of i18n/en.yml, and the site is built
there.

So the fake translations follow the English pages wherever they go, and
nothing here is a translation to publish. None of these files is ever in docs/.

  it: index.md, why.md, about.md
  de: why.md
  es: none

so Why has two translations, the home and About one each, and Start here and
Contact none.
