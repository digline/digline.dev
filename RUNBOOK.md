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
2. Build against the digline branch or worktree that has the file: `make preview DIGLINE=<path>` — `make build` refuses a checkout ahead of `origin/main`, which that branch is. It must be green, with one URL more than `main`.
3. Commit, saying which digline branch and commit it was built against, the URL count, and that the branch waits for the record. Do not merge.
4. When the record is on digline main: update `../digline`, rebase or merge the branch, `make build` green, merge, push, check live.

## The gates, before any merge into `main`

- `make css` whenever `docs/assets/*.css` changed. It needs no build.
- `make build` against `../digline` level with `origin/main`: sync, the CSS check, `mkdocs build --strict`, then `check-sitemap.py` and `check-llms.py`. All green.
- The sync checks the first half of that itself: it refuses a digline checkout with uncommitted changes under what it copies (`docs/`, `examples/`, `docker/`, the changelog and roadmap), or one ahead of `origin/main`, or behind it — except a detached HEAD exactly on the latest `v*` tag `origin/main` contains, the release tag CI builds a dispatch from; an older tag, or an untagged commit, is refused. To look at a page that is not on digline main yet, `make preview` (`SYNC_UNRELEASED=1`): it builds with a banner and leaves `.sync-preview`, and `tools/check-source.sh`, in `make build` and in the workflow, refuses to ship that build.
- The commit message names the digline commit it was built against and the URL count.

Not a gate, a tool: when a page's look changed, `uv run tools/screenshots.py --out <dir> --page <path> --widths 1280,390 --themes light,dark` photographs it from `site/` (or `--base https://digline.dev`) and fails if a `<pre>` scrolls sideways; its docstring has the rest.

A red build caused by something outside the change (a nav entry whose file is not on digline main, for instance) is fixed on `main` first, in its own commit, and the change is verified against the fixed `main`, never committed on top of a red one.

## After the push

1. The `docs` workflow run for the pushed commit: Build and Deploy both succeed (`gh run watch <id> --exit-status`).
2. On the live site, with a cache-busting query, every check in two halves: the positive one, and a negative one built to fail — a check that cannot fail has verified nothing. A 200 from a server that answers 200 to anything, or a string search on a page that was never going to contain the string, passes whether the change is live or not. The report gives both halves, each with what it got.
   - every new or changed page answers 200, with the expected `<title>` and `<meta name="description">` — and a path next to it that does not exist (`/no-such-page-<random>/`) answers 404;
   - the text the change added is on the page — and the text it replaced, or a string that must not be there (an old version, a removed figure), is found 0 times;
   - its internal links answer 200, and its external links too — and one of them with a character changed answers 404;
   - a new nav, bar or footer entry is present on a presentation page and on a documentation page — and absent from a page that should not carry it;
   - `llms.txt` lists the new page and `sitemap.xml` has the expected URL count — and a page that should not be there yet (an ADR still on its branch) answers 404 and is in neither;
   - a version on a package index answers 200 — and a version that does not exist answers 404. Ask the JSON API for this, not the project page: `https://pypi.org/project/<pkg>/<version>/` answers 200 for any version, real or not, while `https://pypi.org/pypi/<pkg>/<version>/json` answers 200 for a released version and 404 for any other.
