# Where the product documentation comes from when you build locally. In CI the
# workflow checks the repository out and passes its path instead.
DIGLINE ?= ../digline

.PHONY: docs preview serve css source home build check clean

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

source:          ## refuse a build made from an unreleased sync
	tools/check-source.sh

home:            ## the home's hook against its fixtures, refusals included — needs no build
	uv run tools/hooks/home.py --selftest

build: docs css source home  ## what CI does; a broken link, a wrong sitemap, a stylesheet a browser cannot read, an unreleased source or a home.json the home cannot stand behind fails it
	uv run mkdocs build --strict
	tools/check-sitemap.py site
	tools/check-llms.py site

check: css source  ## the stylesheets, the source, and the two generated indexes against an existing site/
	tools/check-sitemap.py site
	tools/check-llms.py site

clean:
	rm -rf site docs/product .sync-preview
