# Runbook

How changes reach <https://digline.dev>. Pushing to `main` publishes, so everything below happens before the push, except the last section, which happens right after it.

## A change is a branch

One branch per change, merged into `main` with `--no-ff` (`Merge branch '<name>'`), deleted once it is merged and pushed. A fix that `main` needs on its own (a broken build, say) is a commit of its own on `main`, with a message that says why.

The diff is read before the commit, not after.

## A page the site did not have

Every page in the nav needs a description, or the build fails:

- **Written here** (`docs/*.md`, `docs/handbook/`, `docs/blog/`): `description:` in the page's front matter, and a line in `DESCRIPTIONS` in `tools/hooks/llms.py`. `image:` and `image_alt:` come as a pair, PNG or JPEG only; with neither, the card is the wordmark.
- **Under `product/`**, copied in from digline/digline: the page carries no front matter, so its title and description go in `PRODUCT` in `tools/hooks/seo.py`, plus its line in `DESCRIPTIONS`.

A new entry in the bar (`overrides/partials/header.html`) is measured, not estimated: the breakpoints in `docs/assets/chrome.css` (presentation pages) and `docs/assets/theme.css` (documentation pages) state the widths they were calibrated on. An entry that yields on a narrow screen needs somewhere else to live, which is the footer.

## An ADR

The rule:

> The three entries of an ADR — the nav line in `mkdocs.yml`, `PRODUCT` in `tools/hooks/seo.py`, `DESCRIPTIONS` in `tools/hooks/llms.py` — go on a branch `adr-NNNN-site`. It merges only when the record is on digline main, after a green build with `sync-docs` from main. Never on `main` before.

Why: `tools/sync-docs.sh` copies from digline's main, and `--strict` refuses a nav entry whose file is not there. An entry that lands early stops every release of the site, including the ones dispatched by digline itself.

The procedure, the one ADR 0009 and ADR 0022 followed:

1. Branch `adr-NNNN-site` from `main`. Write all three entries; the descriptions are written from the record's content, not copied from it.
2. Build against the digline branch or worktree that has the file: `make build DIGLINE=<path>`. It must be green, with one URL more than `main`.
3. Commit, saying which digline branch and commit it was built against, the URL count, and that the branch waits for the record. Do not merge.
4. When the record is on digline main: update `../digline`, rebase or merge the branch, `make build` green, merge, push, check live.

## The gates, before any merge into `main`

- `make css` whenever `docs/assets/*.css` changed. It needs no build.
- `make build` against `../digline` level with `origin/main`: sync, the CSS check, `mkdocs build --strict`, then `check-sitemap.py` and `check-llms.py`. All green.
- The commit message names the digline commit it was built against and the URL count.

A red build caused by something outside the change (a nav entry whose file is not on digline main, for instance) is fixed on `main` first, in its own commit, and the change is verified against the fixed `main`, never committed on top of a red one.

## After the push

1. The `docs` workflow run for the pushed commit: Build and Deploy both succeed (`gh run watch <id> --exit-status`).
2. On the live site, with a cache-busting query:
   - every new or changed page answers 200, with the expected `<title>` and `<meta name="description">`;
   - its internal links answer 200, and its external links too;
   - a new nav, bar or footer entry is present on a presentation page and on a documentation page;
   - `llms.txt` lists the new page, and a page that should not be there yet (an ADR still on its branch) answers 404.
