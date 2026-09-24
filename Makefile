# Where the product documentation comes from when you build locally. In CI the
# workflow checks the repository out and passes its path instead.
DIGLINE ?= ../digline

.PHONY: docs preview serve css makefile claims actions source home opening agents operator indexes posts feed card glyphs assets bar translate i18n translations translation-checks agent build check clean

docs:            ## copy digline's docs/ and examples/*/README.md into docs/product/
	tools/sync-docs.sh $(DIGLINE)

preview:         ## build with pages that are not on digline main yet — never deployable
	SYNC_UNRELEASED=1 tools/sync-docs.sh $(DIGLINE)
	MKDOCS_OMITTED_FILES=info uv run mkdocs build --strict
	@echo
	@echo "  Built in site/, with the unreleased pages in it. \`make build\` and the"
	@echo "  workflow both refuse this build: tools/check-source.sh sees .sync-preview."
	@echo "  \`SYNC_UNRELEASED=1 make serve\` to read it in a browser."
	@echo

serve: docs      ## local preview on http://127.0.0.1:8000/
	uv run mkdocs serve

css:             ## parse docs/assets/*.css — needs no build, so run it first
	uv run tools/check-css.py docs/assets

makefile:        ## this Makefile: no target declared twice, every one in .PHONY, every prerequisite real — needs no build
	python3 tools/check-make.py --selftest
	python3 tools/check-make.py Makefile

claims:          ## absolute claims about where data goes, in English and in the three calques, against the register — needs no build
	uv run tools/check-claims.py --selftest
	uv run tools/check-claims.py

actions:         ## every action of .github/workflows at a full commit, with its version beside it — needs no build
	uv run tools/check-actions.py --selftest
	uv run tools/check-actions.py

source:          ## refuse a build made from an unreleased sync
	tools/check-source.sh

home:            ## the home's hook against its fixtures, refusals included — needs no build
	uv run tools/hooks/home.py --selftest

opening:         ## the opening band: the hook that builds it, and the check that every page has one — needs no build
	uv run tools/hooks/opening.py --selftest
	uv run tools/check-opening.py --selftest

agents:          ## /agents/: rule 1 read out of AGENTS.md, links led to the tag, the quotation held to the rule — needs no build
	python3 tools/agents_rule.py --selftest
	uv run tools/hooks/sources.py --selftest

operator:        ## /product/operator/: the example's facts read at the tag, and the page held to them — needs no build
	python3 tools/operator_facts.py --selftest
	python3 tools/hooks/operator_page.py --selftest

assets:          ## the asset-hash check against its own small site, refusals included — needs no build
	uv run tools/check-assets.py --selftest

indexes:         ## the Examples tiles and the Decisions table: every missing field refused, and no status in a record's description — needs no build
	uv run tools/hooks/indexes.py --selftest

posts:           ## a post's date read once: the list on /blog/, and a missing, unparseable or future date refused — needs no build
	uv run tools/hooks/blog.py --selftest

feed:            ## the RSS channel and its items, newest first, and a feed with no post refused — needs no build
	uv run tools/hooks/feed.py --selftest

card:            ## the card's image measured from its bytes, a default that is missing or unreadable and a built card that does not match it refused — needs no build
	uv run tools/hooks/seo.py --selftest

glyphs:          ## the glyph check against its own four-page site, refusals included — needs no build
	uv run tools/check-glyphs.py --selftest

bar:             ## the bar check against its own four-page site, refusals included — needs no build
	uv run tools/check-bar.py --selftest

translate:       ## the translate="no" and lang check against its own two-page site, refusals included — needs no build
	uv run tools/check-translate.py --selftest

i18n:            ## the catalog's check and t() against their own catalog, template and hook, refusals included — needs no build
	uv run tools/hooks/i18n.py --selftest

translations: docs  ## the fake translations in tools/testdata/translations built in a copy of the site, hreflang and refusals included
	uv run tools/hooks/translations.py --selftest

translation-checks: docs  ## every translation against its original: the fake ones pass, a failure planted for each check refused, a changed original reported
	uv run tools/check-translations.py --selftest

agent: docs      ## the translating agent with a fake model — prompts, skipping, the fixed section, retries, the spending limit, the report, a real build — no network
	uv run tools/translate.py --selftest

build: docs css makefile claims actions source home opening agents operator indexes posts feed card glyphs assets bar translate i18n translations translation-checks agent  ## what CI does; a broken link, a wrong sitemap, a stylesheet a browser cannot read, an action at a tag or a branch, an unreleased source, a home.json the home cannot stand behind, a post with no date or a date in the future, a card whose width and height are not the image's, a post missing from the feed or a page in it that is not one, a character with no Plex glyph, a search icon on a page without search or missing from one with it, code a translator may rewrite, a catalog key named and missing, or held and unused, or a translation that does not hold together, or strays from its original, fails it
	uv run mkdocs build --strict
	tools/check-sitemap.py site
	tools/check-llms.py site
	tools/check-feed.py site
	uv run tools/check-glyphs.py site
	uv run tools/check-assets.py site
	uv run tools/check-bar.py site
	uv run tools/check-opening.py site
	uv run tools/check-translate.py site
	uv run tools/check-translations.py site

check: css makefile claims actions source  ## the stylesheets, the source, the two generated indexes and the glyphs against an existing site/
	tools/check-sitemap.py site
	tools/check-llms.py site
	tools/check-feed.py site
	uv run tools/check-glyphs.py site
	uv run tools/check-assets.py site
	uv run tools/check-bar.py site
	uv run tools/check-opening.py site
	uv run tools/check-translate.py site
	uv run tools/check-translations.py site

clean:
	rm -rf site docs/product .sync-preview
