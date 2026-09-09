# digline.dev

The site behind <https://digline.dev>: MkDocs Material, with the presentation pages (home, start, why, about, contact) rendered by free-HTML templates in `overrides/`, and the product documentation copied in from [digline/digline](https://github.com/digline/digline) — never written here.

`make docs` copies that documentation from `../digline` into `docs/product/` (gitignored); `make serve` previews the site, `make build` runs the strict build CI runs.

Before pushing anything that touches `docs/assets/*.css`, run `make css`. It parses the stylesheets and fails on a rule a browser would silently drop — an unbalanced brace does not stop the build, it just costs you whichever rule follows it, which is how the footer went white in 60f655f. It needs no build, so it is the quick one.

Pushing to `main` publishes, and so does every digline release: `publish.yml` over there sends a `digline-release` dispatch once the version is on PyPI, and `.github/workflows/docs.yml` builds and deploys to GitHub Pages.
