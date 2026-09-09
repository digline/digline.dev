# Where the product documentation comes from when you build locally. In CI the
# workflow checks the repository out and passes its path instead.
DIGLINE ?= ../digline

.PHONY: docs serve css build check clean

docs:            ## copy digline's docs/ and examples/*/README.md into docs/product/
	tools/sync-docs.sh $(DIGLINE)

serve: docs      ## local preview on http://127.0.0.1:8000/
	uv run mkdocs serve

css:             ## parse docs/assets/*.css — needs no build, so run it first
	uv run tools/check-css.py docs/assets

build: docs css  ## what CI does; a broken link, a wrong sitemap or a stylesheet a browser cannot read fails it
	uv run mkdocs build --strict
	tools/check-sitemap.py site
	tools/check-llms.py site

check: css       ## the stylesheets, and the two generated indexes against an existing site/
	tools/check-sitemap.py site
	tools/check-llms.py site

clean:
	rm -rf site docs/product
