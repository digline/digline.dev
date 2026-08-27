# Where the product documentation comes from when you build locally. In CI the
# workflow checks the repository out and passes its path instead.
DIGLINE ?= ../digline

.PHONY: docs serve build clean

docs:            ## copy digline's docs/ and examples/*/README.md into docs/product/
	tools/sync-docs.sh $(DIGLINE)

serve: docs      ## local preview on http://127.0.0.1:8000/
	uv run mkdocs serve

build: docs      ## what CI does: a broken link fails the build
	uv run mkdocs build --strict

clean:
	rm -rf site docs/product
