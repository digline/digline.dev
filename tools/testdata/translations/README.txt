Fake translations, for tools/hooks/translations.py --selftest only.

docs/it/ and docs/de/ are copied over a copy of the site's docs/ in a
temporary directory, each language given a catalog that is a copy of
i18n/en.yml, and the site is built there. Nothing here is a translation to
publish: the words are placeholders in the right language, and none of these
files is ever in docs/.

  it: index.md, why.md, about.md
  de: why.md
  es: none

so Why has two translations, the home and About one each, and Start here and
Contact none.
