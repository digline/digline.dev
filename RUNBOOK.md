# Runbook

How changes reach <https://digline.dev>. Pushing to `main` publishes, so everything below happens before the push, except the last section, which happens right after it.

## A change is a branch

One branch per change, merged into `main` with `--no-ff` (`Merge branch '<name>'`), deleted once it is merged and pushed. A fix that `main` needs on its own (a broken build, say) is a commit of its own on `main`, with a message that says why.

The diff is read before the commit, not after.

## One session, one worktree

Several sessions — people, agents — may work on this repository at once, and they share one checkout. So a session does not change branch in that checkout. It works in a worktree of its own, on a branch from `origin/main`:

    git fetch
    git worktree add ../digline.dev-<branch> -b <branch> origin/main

and removes it when its work is merged or abandoned: `git worktree remove ../digline.dev-<branch>`.

Why: on 16 September a branch change made outside the session moved the shared checkout back to `main` mid-task, and the next commit landed on local `main` instead of on the branch it was written for.

At the end of the session, after the merge, the local `main` of both shared checkouts — this repository's, `../digline.dev`, and digline's, `../digline`, which `make build` syncs from — is brought level with `origin/main`: by fast-forward only, and only when the checkout is on `main`, has nothing uncommitted, and its `main` is an ancestor of `origin/main`. Otherwise it is left as it is, and the session says which checkout, and which of the three conditions failed.

    for repo in ../digline.dev ../digline; do
      git -C "$repo" fetch
      test "$(git -C "$repo" branch --show-current)" = main \
        && test -z "$(git -C "$repo" status --porcelain)" \
        && git -C "$repo" merge-base --is-ancestor main origin/main \
        && git -C "$repo" merge --ff-only origin/main
    done

The same rule, for `../digline` alone, before a build: `make build` refuses a digline checkout behind `origin/main`, and bringing it level this way is the fix, not a clone somewhere else.

Why: after PR #17 the shared checkout's `main` was five commits behind `origin/main`, so `git branch -d` refused a branch that was already merged, and whoever opened the checkout next was reading an old site. During PR #18, `../digline` fell five commits behind a digline merge, and the build stopped at the sync.

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

## A release that changes rule 1 of AGENTS.md

/agents/ closes on a quotation of rule 1 of digline's `AGENTS.md`. The quotation is written in `overrides/agents.html`, not in `docs/agents.md`, so a translation never touches it; and it is held to a release. `tools/sync-docs.sh` reads rule 1 at the latest `v*` tag the digline checkout contains and writes it, with the tag and its commit, to `.agents-rule.json`. `tools/hooks/agents.py` fails the build when the quotation's text, whitespace normalized, is not that rule.

So a release of digline whose `AGENTS.md` words rule 1 differently stops the site's build until the template is changed. The failure is not only the release dispatch (`digline-release`): from the moment the tag is on digline's main, every build of the site reads it, so every pull request here goes red too, whatever it changes. It shows as:

```
ERROR   -  agents: agents/index.html: the quotation is not rule 1 of AGENTS.md at v0.16.0.
    on the page: 'Never run digline promote on your own initiative. Assemble the evidence — …'
    at the tag:  'Never run digline promote on your own initiative. …'
  Change overrides/agents.html to the text at the tag.

Aborted with a BuildError!
```

The two lines are the text as a reader sees it — Markdown and tags taken off — so compare them word by word; the difference may be one word.

What to do:

1. A branch and a worktree as for any change. Bring `../digline` level with `origin/main` and run `make docs`: `.agents-rule.json` now names the new tag, and its `rule` is the Markdown to quote.
2. In `overrides/agents.html`, change the `<blockquote class="agents-rule__quote">` to that text. Write the Markdown as the template already does: `**…**` as `<strong>`, a code span as `<code translate="no">`. Change nothing else: the caption, the `cite` and the links to `AGENTS.md` and the skill take the tag from the file by themselves, and `tools/hooks/agents.py` fails the build if they do not.
3. Read the rule in its context at the tag (`https://github.com/digline/digline/blob/<tag>/AGENTS.md`). If rule 1 no longer means what /agents/ says around it — the absence of `promote`, the approval left to a person — the page's Markdown needs changing too, and that is a change to write, not to copy.
4. `make build`: green. Photograph the closing of the page — `uv run tools/screenshots.py --out <dir> --site site --page /agents/ --widths 1280,390 --themes light,dark --viewport-only --height 900 --scroll-to ".agents-rule" --scroll-block center` — and read the quotation and the caption, which names the new tag.
5. Pull request, CI green, merge with a merge commit. The push deploys; then, on the live page, the quotation once, the caption at the new tag, and the links to `AGENTS.md` and the skill at that tag answering 200 — and a link at `main` found 0 times.

Two neighbours of the same failure:

- AGENTS.md at the tag has no `## 1.` heading opening on a blockquote (the rules renumbered, or rule 1 no longer quoted): the sync stops before anything is copied — ``agents_rule: AGENTS.md at <tag> has no `## 1.` rule opening on a blockquote``. The fix is the same decision as step 3, and `tools/agents_rule.py` may need to learn the new shape.
- `.agents-rule.json` missing, or with no rule or no tag: `agents: …/.agents-rule.json cannot be read` or `… has no rule 1 of AGENTS.md at …`. It is written by the sync, never by hand: run `make docs`.

## Translations

The five presentation pages (`docs/index.md`, `start`, `why`, `about`, `contact`) and the catalog (`i18n/en.yml`) are translated into Italian, German and Spanish by `.github/workflows/translate.yml`, which runs `tools/translate.py`. Its docstring has how a translation is made and checked; this is what happens around it.

**What starts a run.** A push to `main` that touches one of those pages, `i18n/en.yml`, or a template that writes catalog words (`overrides/home.html`, `404.html`, `partials/header.html`, `footer.html`, `opening.html`, `closing.html`). The Plan job asks `tools/translate.py --plan` what is behind English on `main` as it is: nothing, and the run stops there — no call, no pull request opened or touched. Otherwise only what changed is translated: an English sentence changed in `about.md` costs three pages, not fifteen. One run at a time; a newer push replaces a pending run, never the one in progress. The bot's own merges touch only `docs/<lang>/` and `i18n/<lang>.yml`, which start nothing.

**What it produces.** A commit by `digline-translation-bot[bot]` on `i18n/auto`, rewritten on top of `main` at every run, and a pull request into `main` (opened, or updated if one is open) whose description is the run's report: what was translated or skipped, the checks, the reading of meaning, the calques noted, tokens and cost. docs.yml runs on it like on any other.

- **No page needs attention**: the run enables auto-merge with a merge commit. The ruleset on `main` requires the Build check, so the pull request merges itself when Build is green, and the push deploys.
- **A page needs attention** (an error of meaning still there after the correction round): no auto-merge, the label `translation: needs attention`, and the report in the description says which page, the English, the translation and why. A person reads it and either pushes a fix onto `i18n/auto` and merges by hand once Build is green (before any other run, which would rewrite the branch), or closes the pull request and corrects on `main` as below.

A page whose translation failed the checks twice is not written, and the job fails; what passed is still proposed.

**Correcting a translation by hand.** A branch and a pull request like any change: edit `docs/<lang>/<page>.md` (the text; leave `source`, `source_sha`, `source_commit` and `model` as they are), or a key of `i18n/<lang>.yml` (never the `do_not_translate` section: `FIXED_TEXTS_DIGEST` in `tools/check-translations.py` refuses it). `make build` checks it against the original like any translation. It does not start a run. It lasts as long as its original does not change: a page until its English `source_sha` moves, a catalog key until that English key does. Then the agent translates again, starting from the corrected text and the English diff, asked to change as little as the diff requires — the correction usually survives, but read the next pull request's diff for that page.

**A run by hand.** From `main` only — the federation rule refuses any other ref:

    gh workflow run translate.yml --ref main -f langs=it,de,es -f pages=index,start,why,about,contact -f dry_run=false -f max_cost=12

`dry_run` defaults to true: the translations, the report and the bill go to the run's artifact, nothing to `docs/` or a pull request.

**The spending limit.** Per run. By hand, the `max_cost` input (12 USD by default); after a push, 12 USD, set by `MAX_COST` in the Translate step of `translate.yml`; locally, `DEFAULT_MAX_COST` in `tools/translate.py`. The log has the estimate before the first call, and the run stops before the call that would pass the limit.

**The credentials.** No Anthropic key: the job's GitHub OIDC token is exchanged at Anthropic (Workload Identity Federation). The federation rule is in the Anthropic Console of the organization whose id is the repository variable `ANTHROPIC_ORG_ID`; its own id is `ANTHROPIC_FEDERATION_RULE_ID`, with `ANTHROPIC_SERVICE_ACCOUNT_ID` and `ANTHROPIC_WORKSPACE_ID` next to it (Settings → Secrets and variables → Actions → Variables). It accepts this repository's `refs/heads/main` in the immutable subject form, `repo:digline@321413575/digline.dev@1348500446:ref:refs/heads/main`, and a job with no environment. The pull request is opened with the GitHub App's token, secrets `TRANSLATION_APP_ID` and `TRANSLATION_APP_PRIVATE_KEY`, because what `GITHUB_TOKEN` opens starts no workflow. Auto-merge needs "Allow auto-merge" on in the repository settings and the ruleset on `main` (pull request required, Build required, no force push).

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
