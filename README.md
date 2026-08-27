# digline.dev

The site behind <https://digline.dev>: MkDocs Material, with the presentation pages (home, why, about, contact) rendered by free-HTML templates in `overrides/`, and the product documentation copied in from [digline/digline](https://github.com/digline/digline) — never written here.

`make docs` copies that documentation from `../digline` into `docs/product/` (gitignored); `make serve` previews the site, `make build` runs the strict build CI runs.

Pushing to `main` publishes, and so does every digline release: `publish.yml` over there sends a `digline-release` dispatch once the version is on PyPI, and `.github/workflows/docs.yml` builds and deploys to GitHub Pages.
