# Where the product documentation comes from when you build locally. In CI the
# workflow checks the repository out and passes its path instead.
DIGLINE ?= ../digline

.PHONY: docs serve build check clean

docs:            ## copy digline's docs/ and examples/*/README.md into docs/product/
	tools/sync-docs.sh $(DIGLINE)

serve: docs      ## local preview on http://127.0.0.1:8000/
	uv run mkdocs serve

build: docs      ## what CI does; a broken link or a wrong sitemap fails it
	uv run mkdocs build --strict
	tools/check-sitemap.py site
	tools/check-llms.py site

check:           ## the two generated indexes against an existing site/, on their own
	tools/check-sitemap.py site
	tools/check-llms.py site

clean:
	rm -rf site docs/product
