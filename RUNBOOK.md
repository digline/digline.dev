# Runbook

How changes reach <https://digline.dev>. Pushing to `main` publishes, so everything below happens before the push, except the last section, which happens right after it.

## A change is a branch

One branch per change, merged into `main` with `--no-ff` (`Merge branch '<name>'`), deleted once it is merged and pushed. A fix that `main` needs on its own (a broken build, say) is a commit of its own on `main`, with a message that says why.

The diff is read before the commit, not after.

`gh pr merge` is a call of its own: never chained with `gh run watch`, a poll or a sleep. Stopping a chained call during the wait leaves the merge done. That is how #72 reached `main` on 19 September at a commit older than the one under review.

**And never chained with `cd` either.** A merge is addressed by number, and the number alone says nothing about which repository it is in: `gh` reads that from the working directory. So the call before it is `gh repo view --json nameWithOwner --jq .nameWithOwner`, and the number is merged only against the name that comes back.

Why: on 22 September a session merged five pull requests across both repositories, and one call began `cd ../digline-lock-glob && gh pr merge 67`. Another session had already removed that worktree, the `cd` failed, and the shell was left in `digline.dev` — where `gh pr merge 67` addressed digline.dev#67, a pull request about the Handbook that had merged three days earlier. Nothing happened, because a merged pull request cannot be merged again. That is the only reason nothing happened: had digline.dev#67 been open, an unrelated change would have landed on `main` and deployed, from a command whose author believed it was in the other repository. `cd` failing is not the unusual part — a shared checkout is shared, and worktrees come and go under it.

## One session, one worktree

Several sessions — people, agents — may work on this repository at once, and they share one checkout. So a session does not change branch in that checkout. It works in a worktree of its own, on a branch from `origin/main`:

    git fetch
    git worktree add ../digline.dev-<branch> -b <branch> origin/main

and removes it when its work is merged or abandoned: `git worktree remove ../digline.dev-<branch>`.

Why: on 16 September a branch change made outside the session moved the shared checkout back to `main` mid-task, and the next commit landed on local `main` instead of on the branch it was written for.

On 24 September it was broken by the session writing this RUNBOOK's own entry on translations. That session switched branches in both shared checkouts and left `../digline` on a branch it had already merged. It put the checkout back and said so. The rule does not hold because people know it: the session that broke it was reading this file at the time.

At the end of the session, after the merge, the local `main` of both shared checkouts — this repository's, `../digline.dev`, and digline's, `../digline`, which `make build` syncs from — is brought level with `origin/main`: by fast-forward only, and only when the checkout is on `main`, has nothing uncommitted, and its `main` is an ancestor of `origin/main`. Otherwise it is left as it is, and the session says which checkout, and which of the three conditions failed. A checkout that is not on `main` is reported with the branch it is on and whether that branch has work not pushed: commits ahead of its upstream (`git -C "$repo" rev-list --count @{u}..HEAD`), or no upstream at all.

    for repo in ../digline.dev ../digline; do
      git -C "$repo" fetch
      test "$(git -C "$repo" branch --show-current)" = main \
        && test -z "$(git -C "$repo" status --porcelain)" \
        && git -C "$repo" merge-base --is-ancestor main origin/main \
        && git -C "$repo" merge --ff-only origin/main
    done

The same rule, for `../digline` alone, before a build: `make build` refuses a digline checkout behind `origin/main`, and bringing it level this way is the fix, not a clone somewhere else.

Why: after PR #17 the shared checkout's `main` was five commits behind `origin/main`, so `git branch -d` refused a branch that was already merged, and whoever opened the checkout next was reading an old site. During PR #18, `../digline` fell five commits behind a digline merge, and the build stopped at the sync.

## A claim that cannot be sourced

It says so in the place it is made — never in a footnote, and never nowhere.

A footnote is a place a reader arrives after having already believed the claim,
and a reader who goes looking for evidence and finds none draws a worse
conclusion than the one we could have handed them. So the qualification travels
with the sentence: in the paragraph that makes the claim, in the section that
prints the figure.

The instance in this repository is the Handbook's chapter 0, which describes a
system "read off one system's code" and then says, in that same paragraph, that
the reading has no dated artefact behind it — no note, no captured repository,
nothing to cite. It is offered as a shape that recurs, not as evidence.

The rule is the same one digline's `CLAUDE.md` carries under Conventions, and it
is written in both places on purpose: chapter 0 is the instance that lives here,
and a convention cited in one repository about a claim made in another is one
lookup too far. The other instance is a measurement rather than prose —
`docs/adr/0024` §5.6 states the bound on what a replay can measure beside the
figure it qualifies — and the shape does not change between the two.

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

## A page here about something that lives in digline

Three pages under `product/` are written in this repository rather than copied from digline: `pages/product/operator.md`, `pages/product/security.md` and `pages/product/examples/index.md`. `tools/sync-docs.sh` installs them into `docs/product/` after the copy. They exist because a page about how digline is *used* has no home in the other repository's `docs/` — but what they describe does live there, and changes there.

The rule:

> A page written here may name a **public API name**, linked to its own page — `HttpTarget`, `Disclosure`. It may not state a **count**, a **command**, an **internal file** or a **decision rule** that belongs to digline. Those are the other repository's to state, and they move when it moves: name the thing the reader needs and link the example, which states its own.

Why: `pages/product/operator.md` was written on 9 September as a copy of `examples/operator/DESIGN.md`, minus one section. DESIGN.md was amended twice on 11 September; the copy was not. For twelve days the page said *two* alerts shipped where three did, named `compare` and `diff` for a layer the loop renders from `explain`, and described an escalation rule the shipped loop contradicts — while every link resolved and every gate was green. The distinction the rule draws is the one that failed: an API name is stable and has a page of its own that the sync brings in, so a reader can check it; a count, a command, a file name and a decision rule are mechanism, and a copy of mechanism goes stale silently.

The gate, for the countable half: `tools/sync-docs.sh` writes `.operator-facts.json` (`tools/operator_facts.py`) — the alerts that ship, the files of `examples/operator/`, and digline's command list as `home.json` has it, all read at the latest `v*` tag the checkout contains. `tools/hooks/operator_page.py` fails the build when `/product/operator/` states a number of alerts that is not the number that ship, or names a command or one of those files as code. `promote` is the one command the page may name, because its *absence* from the operator's surface is the page's argument.

A decision rule is not gated and cannot be: it is a sentence, not a number. The answer there is not to write one — say what the operator is for, and let the example say what it decides.

## A release that changes rule 1 of AGENTS.md

/agents/ closes on a quotation of rule 1 of digline's `AGENTS.md`. The quotation is written in `overrides/agents.html`, not in `docs/agents.md`, so a translation never touches it; and it is held to a release. `tools/sync-docs.sh` reads rule 1 at the latest `v*` tag the digline checkout contains and writes it, with the tag and its commit, to `.agents-rule.json`. `tools/hooks/sources.py` fails the build when the quotation's text, whitespace normalized, is not that rule.

So a release of digline whose `AGENTS.md` words rule 1 differently stops the site's build until the template is changed. The failure is not only the release dispatch (`digline-release`): from the moment the tag is on digline's main, every build of the site reads it, so every pull request here goes red too, whatever it changes. It shows as:

```
ERROR   -  sources: agents/index.html: the quotation is not rule 1 of AGENTS.md at v0.16.0.
    on the page: 'Never run digline promote on your own initiative. Assemble the evidence — …'
    at the tag:  'Never run digline promote on your own initiative. …'
  Change overrides/agents.html to the text at the tag.

Aborted with a BuildError!
```

The two lines are the text as a reader sees it — Markdown and tags taken off — so compare them word by word; the difference may be one word.

What to do:

1. A branch and a worktree as for any change. Bring `../digline` level with `origin/main` and run `make docs`: `.agents-rule.json` now names the new tag, and its `rule` is the Markdown to quote.
2. In `overrides/agents.html`, change the `<blockquote class="agents-rule__quote">` to that text. Write the Markdown as the template already does: `**…**` as `<strong>`, a code span as `<code translate="no">`. Change nothing else: the caption, the `cite` and the links to `AGENTS.md` and the skill take the tag from the file by themselves, and `tools/hooks/sources.py` fails the build if they do not.
3. Read the rule in its context at the tag (`https://github.com/digline/digline/blob/<tag>/AGENTS.md`). If rule 1 no longer means what /agents/ says around it — the absence of `promote`, the approval left to a person — the page's Markdown needs changing too, and that is a change to write, not to copy.
4. `make build`: green. Photograph the closing of the page — `uv run tools/screenshots.py --out <dir> --site site --page /agents/ --widths 1280,390 --themes light,dark --viewport-only --height 900 --scroll-to ".agents-rule" --scroll-block center` — and read the quotation and the caption, which names the new tag.
5. Pull request, CI green, merge with a merge commit. The push deploys; then, on the live page, the quotation once, the caption at the new tag, and the links to `AGENTS.md` and the skill at that tag answering 200 — and a link at `main` found 0 times.

Two neighbours of the same failure:

- AGENTS.md at the tag has no `## 1.` heading opening on a blockquote (the rules renumbered, or rule 1 no longer quoted): the sync stops before anything is copied — ``agents_rule: AGENTS.md at <tag> has no `## 1.` rule opening on a blockquote``. The fix is the same decision as step 3, and `tools/agents_rule.py` may need to learn the new shape.
- `.agents-rule.json` missing, or with no rule or no tag: `sources: …/.agents-rule.json cannot be read` or `… has no rule 1 of AGENTS.md at …`. It is written by the sync, never by hand: run `make docs`.

## Translations

The presentation pages and the Handbook's chapters — `tools/languages.py`, `PRESENTATION_PAGES` and `HANDBOOK_PAGES`, which is where both lists live and the only place they are written — and the catalog (`i18n/en.yml`) are translated into Italian, German and Spanish by `.github/workflows/translate.yml`, which runs `tools/translate.py`. Its docstring has how a translation is made and checked; this is what happens around it. The presentation pages and the catalog follow every push; the Handbook is translated by hand (below).

**What starts a run.** A push to `main` that touches one of those pages, `i18n/en.yml`, or a template that writes catalog words (`overrides/home.html`, `404.html`, `partials/header.html`, `footer.html`, `opening.html`, `closing.html`). The Plan job asks `tools/translate.py --plan` what is behind English on `main` as it is: nothing, and the run stops there — no call, no pull request opened or touched. Otherwise only what changed is translated: an English sentence changed in `about.md` costs that page in each language of `tools/languages.py`, not every page. One run at a time; a newer push replaces a pending run, never the one in progress. The bot's own merges touch only `docs/<lang>/` and `i18n/<lang>.yml`, which start nothing. `docs/handbook/` is not among the paths either: a change to the Handbook's English starts nothing and costs nothing.

**What it produces.** A commit by `digline-translation-bot[bot]` on `i18n/auto` — on `i18n/auto-<lang>` for a run of one language, so that one run per language is one pull request per language, and a later run never rewrites an earlier one's branch before it is merged — rewritten on top of `main` at every run, and a pull request into `main` (opened, or updated if one is open) whose description is the run's report: what was translated or skipped, the checks, the reading of meaning, the calques noted, tokens and cost. docs.yml runs on it like on any other.

- **No page needs attention**: the run enables auto-merge with a merge commit. The ruleset on `main` requires the Build check, so the pull request merges itself when Build is green, and the push deploys.
- **A page needs attention** (an error of meaning still there after the correction round): no auto-merge, the label `translation: needs attention`, and the report in the description says which page, the English, the translation and why. A person reads it and either pushes a fix onto its branch and merges by hand once Build is green (before any other run, which would rewrite the branch), or closes the pull request and corrects on `main` as below.

A page whose translation failed the checks twice is not written, and the job fails; what passed is still proposed.

**Correcting a translation by hand.** A branch and a pull request like any change: edit `docs/<lang>/<page>.md` (the text; leave `source`, `source_sha`, `source_commit` and `model` as they are), or a key of `i18n/<lang>.yml` (never the `do_not_translate` section: `FIXED_TEXTS_DIGEST` in `tools/check-translations.py` refuses it). `make build` checks it against the original like any translation. It does not start a run. It lasts as long as its original does not change: a page until its English `source_sha` moves, a catalog key until that English key does. Then the agent translates again, starting from the corrected text and the English diff, asked to change as little as the diff requires — the correction usually survives, but read the next pull request's diff for that page.

**"Keep every sentence the diff does not touch" is not obeyed, and nothing checks it.** A page translated before goes to the model with its previous translation and the English diff, and the prompt says to change only what the diff requires. On 23 September the English of chapter 0 added one paragraph and changed nothing else (49fbb1a). Each of the three translations added that paragraph and also rewrote text the English had not touched. Spanish relabelled "Dónde se resiste" as "Dónde no encaja", which misnames a caveat about cost. Italian reworded a sentence without changing what it says. German turned "jede Zählung" (every count) into "jede Auswertung" (every evaluation), twice, in a chapter about telling a count from a judgement. All three passed the checks and the reading of meaning, and a person caught the rewrites by reading the diffs (#124, #127, #128). This is about the job, not these pages: making `relink()` idempotent changed where the model strayed, not whether it did.

The check that is missing compares shapes, not meaning. The diff of a translation should have the shape of the diff of its source. One paragraph added in English means one paragraph added in each language, at the same place, with every other paragraph byte for byte what it was; anything else is a finding. That comparison is mechanical and cheap. It needs no model and no reader of Spanish, Italian or German, and it would have caught all three. It has to run after every attempt, not only the first. All three pages passed "ok after a correction", and the correction prompt also says to change nothing else, so the rewrites may have come from that round rather than the first translation. A check only on the first attempt would stop the translation and let the correction through, and the correction may be the half that did the damage. Which round it was is an open question, and what the job keeps cannot answer it. The `translation-<lang>` artifacts of the two runs (35842922036 for es, 35850295635 for it and de) and their logs hold each page's final text, the non-blocking calques and the list of calls. The calls show every page corrected once, and es also written twice, because its first answer failed the checks. Neither the text of any earlier attempt nor what the meaning review asked the correction to fix is stored. Answering it next time means the job keeping each attempt's text, and the shape check would then say which attempt strayed. Until the check exists, a translation of a changed page is reviewed rather than verified: read its pull request's diff paragraph by paragraph against the English diff, and put back what the English did not move.

**That review has four minutes, and nobody is standing in them.** A pull request whose pages pass the checks and the reading of meaning merges itself when Build is green (above), about four minutes after it opens, and the push deploys. No person is asked, and nothing waits for one. A rewrite found after the merge is found on a live page. So the shape check is neither optional nor a convenience. It is the only reviewer that can be present, and until it exists a translation of a changed page reaches the site unread.

On 24 September it happened a fourth time in two days. #136 changed one URL in the English of /agents/, and the translations already carried the new URL. The German run rewrote three passages the English had not touched. The sharpest was "Die Oberflächen, die ein Agent erreicht", which became "Die Berührungspunkte, …" while the page's own description still says "keine Oberfläche erreichen": two words for one term, which is what "Zählung" to "Auswertung" did the day before. It passed the checks and the reading of meaning ("ok after a correction"), and so did "Auswertung", because in both cases the meaning did not change. The term did. A reading of meaning cannot see a term of art being paraphrased. That is why the check that compares shapes is the one that matters: one URL changed in English and three paragraphs changed in German is a finding without reading a word of German. It was caught only because a fix happened to be pushed to `i18n/auto` (6c45569) before Build finished. The bot then merged the fixed head (#137).

That run adds one data point to the open question above. German was the only page of the three sent to a correction round, and the only one that strayed. Italian and Spanish were written once, and changed nothing but their `source_sha` and `source_commit`. That fits the correction round being the half that strays, but one run does not show it.

**The count over the history, 24 September: strays live in corrected pages, and "German" was never the variable.** The data point above read German and the correction round as one thing because in #137 they were the same page. They are not the same thing. Corrections happen in all three languages, and strays follow the correction, not the language.

How it was counted: every merged translation pull request (25, `i18n/auto*`), measuring only the bot's commit against its parent, so a hand fix cannot count as a stray the job made. The hand fixes left out are 6c45569 (#137), 0827a78 (#128), bb987c3 (#127), 503d858 (#124), 1af4f74 (#108), d65605c (#109), 6515c61 (#105), 54f7f4d (#78), 8b7530a (#79), 0603a65 and 2d1d0c2 (#77), and dd610ca (#50), plus the merges of `main`. Only pages the report marks *changed* count (40). The 48 *new* pages have no English diff to stray from. A page strayed when its translation changed more paragraphs than its English did between the two `source_commit`s, front matter excluded. That is the shape check, run backwards, at paragraph level. It agrees with every case a person had already ruled on: German /agents/ in #137 and chapter 0 in #124, #127 and #128 come out as strays, and the Italian and Spanish /agents/ in #137 come out clean.

| | strayed |
|---|---|
| corrected once | 17 of 18 |
| not corrected | 1 of 22 |
| German | 7 of 7 corrected, 0 of 6 not |
| Spanish | 7 of 7 corrected, 0 of 6 not |
| Italian | 3 of 4 corrected, 1 of 10 not |

Its limit is part of the result. 40 pages are not 40 observations: the three languages of one English change share that change. The unit is the English change. There are 13, and 9 of them hold both a corrected and an uncorrected page. In 8 only the corrected page strayed. In one, /start/ in #54, both did. In none did only the uncorrected page stray. Eight in one direction against a coin is p ≈ 0.004, and five would already have been under 0.05. *Corrected the same day:* this paragraph first said all 9 and p ≈ 0.002. The /start/ change had been seen as mixed and was still counted, and re-running the count from `private/` caught it. That is enough to say strays live in corrected pages. It is not enough to put a rate on it, and not enough to say which step strayed.

What it cannot say, and why. There are three explanations and the history cannot choose between them. The correction rewrites what it was not asked to. Or the first attempt strays, the reader flags the rewritten prose, and that is why the page was corrected at all. Or the reader, which reads the whole page, notes a calque in prose the English did not touch, and the correction does exactly what it was told. The third is not a stray in the model. It is an instruction. Telling them apart needs what the job does not keep: each attempt's text, and the first reading's issues and notes, which the second reading replaces. The rendered prompt is not needed, because it is a pure function of those and the commit.

None of this changes what the shape check has to be. It must run after the correction, and this count says that is where the strays are. Wired into the job's checks, it also answers most of "which step" for free. A correction that fails the checks is already put back to the text before it, and the report says "its correction failed the checks and was not kept". Keeping the attempts is worth building only for a stray the shape check cannot see: inside the paragraphs the English changed, or on a new page.

**The third explanation is a constraint on the shape check, not only a diagnosis.** The reader reads the whole page, so it can legitimately note a calque in a paragraph the English did not touch. The correction is told to fix exactly what the reader named, so changing that paragraph is an instruction being followed. A check that refuses any diff wider than the English's would refuse it, and a calque outside the diff would then be something no run could correct. So the check cannot be "same shape as the English". It has to tell a change the reader asked for from one nobody asked for. That makes the first reading's issues and notes an **input** to the check, not a diagnostic. Today the second reading overwrites them before anything stores them. Being asked is not the same as being right, though. If the reader asked for #137's "Berührungspunkte", an allowance for asked-for changes would have let a term-of-art paraphrase through. A change outside the English's diff that the reader named can make a change legitimate to propose. It cannot make it safe to merge unread.

**Ruled the same day: two modes, and the reader scoped to the English's diff. This supersedes the paragraph above's conclusion.** That paragraph stays because it is how the decision was reached. Letting the reader's notes reach outside the diff and sending those pages to "needs attention" would take auto-merge from about four pull requests in five. 18 of the 40 changed pages were corrected, and one such page is enough to hold its whole pull request: 14 of the 18 translation pull requests that carried a changed page had at least one. *Corrected the same day:* this first said "one run in two", counting pages where the unit that loses auto-merge is the pull request. That does not protect anything. It puts a person back in the four-minute window nobody can stand in, it builds a queue nobody clears, and then the check gets switched off. So there are two modes with two contracts:

- **Incremental** (a changed page, the ordinary push): the reader notes errors and calques only in the paragraphs the English changed. The check refuses any change outside those paragraphs. The run is mechanical and merges itself.
- **Whole page** (a run someone chose): the whole page may move, and the check says so rather than pretending to a shape. This is the only place it can be relaxed truthfully, and it is how a calque outside the diff gets corrected.

**The consequence, which removes machinery, and why the two questions are one.** Scoping the reader and storing its notes look like separate decisions. They are not. With the reader scoped, what it may ask for is a subset of what the English changed. So "anything changed outside the English's diff was asked for by nobody" is the entire check, and the first reading's notes stop being an input to it. That reverses what was ruled this morning and what the paragraph above says. Storing the notes goes back to being a diagnostic, wanted only if a stray turns up that this check cannot see.

One thing the scoping does not do: it is an instruction to a model, not a wall. The check is what enforces it. A reader that notes outside the diff anyway gets a correction the check refuses. Today's fallback then keeps the text from before the correction, which also drops any fix inside the diff that the same correction made. That failure is visible and safe, and it needs no notes to detect. What the job does need is to hand the reader the paragraphs the English changed, which it already computes (`english_diff`).

**The two comparisons on /start/.** They are not written on the page: `tools/hooks/home.py` puts the headline of two captured runs — the `steady` scenario and `prompt_regression` in digline's `home.json` — where the page keeps two comments, and holds the built page to them. The sentence around them counts what those runs report, in words: three checks moved, one case set aside, six checks worse. Those counts are checked against the capture too (`claim_problems`), so a recapture that moves one of them stops the build here rather than leaving the page saying what no run said. When that happens: read the new sentence, change the words around it, and let the translations follow — `docs/start.md` is a page the agent translates.

**A second run on a language destroys the first one's unmerged work.** Every run rewrites `i18n/auto-<lang>` on top of `main`, so its pull request holds that run's pages and only those. A page the previous run translated, and nobody merged, is gone from the branch — not conflicted, not flagged: absent, with the pull request still open and looking complete.

So: merge a language's pull request before running that language again, or ask one run for every page you need. On 22 September a run for chapter 0 alone, dispatched while the German and Spanish chapter 8 sat unmerged in #108 and #109, took both with it.

Recovering costs nothing if you notice in time. The run that produced the lost page uploaded it: `gh api repos/digline/digline.dev/actions/runs/<id>/artifacts` names `translation-<lang>`, and its zip holds `docs/<lang>/…` exactly as the run wrote it, checked and corrected. Copy the file back onto the branch and push. The artifacts keep for **90 days** — the repository's retention, which `translate.yml` does not override — so the window is long, and the reason to hurry is that nobody will look for a page they do not know is missing.

**A run by hand.** From `main` only — the federation rule refuses any other ref:

    gh workflow run translate.yml --ref main -f langs=it,de,es -f pages=index,start,why,about,contact,agents -f dry_run=false -f max_cost=12

`dry_run` defaults to true: the translations, the report and the bill go to the run's artifact, nothing to `docs/` or a pull request.

**The Handbook, by hand.** One language per job — ten pages fit a job's time and its 12 USD, three languages in one job do not — and a pull request per language on `i18n/auto-<lang>`. One language:

    gh workflow run translate.yml --ref main -f langs=it -f pages=handbook -f dry_run=false -f max_cost=12

All three in one dispatch, one job after the other, each with its own branch, pull request and artifact (`translation-<lang>`), a language that fails leaving the others running, and every pull request left open for a person to read (`auto_merge=false`) even when no page needs attention:

    gh workflow run translate.yml --ref main -f langs=it,de,es -f pages=handbook -f one_pr_per_language=true -f auto_merge=false -f dry_run=false -f max_cost=12

`max_cost` is then per language.

`pages=handbook` is every chapter and the index; a single page is `handbook/02-cases`. `uv run tools/translate.py --plan --langs it --pages handbook` says first what the run would translate, and `--summary` says, per language, how many of the Handbook's pages are translated and how many of those are behind the English. docs.yml writes that summary into every build's run summary ("The Handbook's translations"), so a Handbook fallen behind is seen without a run: its pages keep the stale notice meanwhile, and `tools/check-translations.py` reports them and does not compare them, never fails on them.

**A plan is never stored.** `--plan`, and the estimate a run prints before its first call, are worked out from `main` as it is at that moment. No file keeps them, and a run asks again when it starts, so there is no plan that can go on covering English it was not measured against. The cost is that a figure quoted in a message, an issue or a pull request only holds for the English it was read from. Once a page moves, ask `--plan` again rather than reusing the figure. On 22 September a five-page figure of 8.19 USD was quoted. By the next day it had expired: chapter 0 had changed again, and the plan was one page in three languages, at 1.96 USD.

**Renumbering or renaming a Handbook chapter.** A translation stands at its original's path and its links reach the English pages by path (`tools/translation.py`, `relink()`), so a `git mv` of `docs/handbook/<chapter>.md` is also a `git mv` of `docs/<lang>/handbook/<chapter>.md` in every language that has it — with its `translation_of` and `source` set to the new path — and the relative links to it in every translation change with it, in the same pull request. Otherwise the build stops — a translation whose `translation_of` names a page the build does not have, or a link to a file that is not there — which is the point: nothing reaches `main` half-renamed. A renumbering changes the English text too (the `# 4.` of its title, the "chapter 4" of its neighbours), so the translations are then behind their originals, and the next run by hand brings them up to date.

**The spending limit.** Per run. By hand, the `max_cost` input (12 USD by default); after a push, 12 USD, set by `MAX_COST` in the Translate step of `translate.yml`; locally, `DEFAULT_MAX_COST` in `tools/translate.py`. The log has the estimate before the first call, and the run stops before the call that would pass the limit.

**The credentials.** No Anthropic key: the job's GitHub OIDC token is exchanged at Anthropic (Workload Identity Federation). The federation rule is in the Anthropic Console of the organization whose id is the repository variable `ANTHROPIC_ORG_ID`; its own id is `ANTHROPIC_FEDERATION_RULE_ID`, with `ANTHROPIC_SERVICE_ACCOUNT_ID` and `ANTHROPIC_WORKSPACE_ID` next to it (Settings → Secrets and variables → Actions → Variables). It accepts this repository's `refs/heads/main` in the immutable subject form, `repo:digline@321413575/digline.dev@1348500446:ref:refs/heads/main`, and a job with no environment. The pull request is opened with the GitHub App's token, secrets `TRANSLATION_APP_ID` and `TRANSLATION_APP_PRIVATE_KEY`, because what `GITHUB_TOKEN` opens starts no workflow. Auto-merge needs "Allow auto-merge" on in the repository settings and the ruleset on `main` (pull request required, Build required, no force push).

## Updating an action

Every `uses:` in `.github/workflows/` is a full commit with the version it is at written after it, and `tools/check-actions.py` (in `make build` and in CI) refuses a tag, a branch, a short sha, or a pin whose version is not written:

    uses: actions/checkout@fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09 # v5.1.0

To move one to a newer version, read the sha from the action's own repository, never from a list — a tag is whatever that repository says it is today:

    git ls-remote --tags https://github.com/actions/checkout | grep -E 'refs/tags/v5(\.|$)'

An annotated tag prints twice: `refs/tags/v5.1.0` is the tag object and `refs/tags/v5.1.0^{}` the commit it points at. **The commit is the one with `^{}`**, and it is what goes in the workflow; when a tag prints only once, that line is the commit. The same commit usually carries the moving major (`v5`) and the exact version (`v5.1.0`): the comment names the exact one, so that a reader knows what they are on and the next update has something to compare with.

The comment names the exact version — `# v5.1.0`, never `# v5`: a major is a tag that moves, so beside a fixed commit it says nothing, and `tools/check-actions.py` refuses it. The sha and the comment move together, in the same commit here: a comment left on an older version is worse than none, and nothing can catch it — the gate reads that an exact version is written, not that it is this commit's. Two things it is worth checking by hand when you update: that the version you wrote is the one the sha belongs to, and that the same action is at the same version in every workflow that uses it.

## The gates, before any merge into `main`

- `make css` whenever `docs/assets/*.css` changed, and `make actions` whenever a workflow changed. Neither needs a build.
- `make build` against `../digline` level with `origin/main`: sync, the CSS check, `mkdocs build --strict`, then `check-sitemap.py` and `check-llms.py`. All green.
- The sync checks the first half of that itself: it refuses a digline checkout with uncommitted changes under what it copies (`docs/`, `examples/`, `docker/`, the changelog and roadmap), or one ahead of `origin/main`, or behind it — except a detached HEAD exactly on the latest `v*` tag `origin/main` contains, the release tag CI builds a dispatch from; an older tag, or an untagged commit, is refused. To look at a page that is not on digline main yet, `make preview` (`SYNC_UNRELEASED=1`): it builds with a banner and leaves `.sync-preview`, and `tools/check-source.sh`, in `make build` and in the workflow, refuses to ship that build.
- The commit message names the digline commit it was built against and the URL count.

**`make preview` is not this gate, even when it is green.** A preview syncs whatever checkout it is pointed at. `make build` and the pull request's `Build` sync digline's `main`, or the latest tag on a release dispatch, which is what `main` here will use. On 2026-09-23, #133 was verified locally with `make preview` against a digline follow-up branch. Everything it needed was already on digline `main` by then, so `make build` was possible, and it was the gate. The pull request's own `Build` covered the difference, because it clones the default branch, so nothing shipped unverified. But the local green that was reported described a different source than the one `main` used. When the page is on digline `main`, run `make build`. Keep `make preview` for the case it exists for: a page that is not there yet.

**The cross-repository freshness gap is left open, on purpose.** `Build` is required with `strict` on, so a pull request must be up to date with this repository's `main`, but not with digline's. digline's `main` can move between a pull request's green `Build` and its merge, and nothing re-runs the check when it does. The push build after the merge syncs again, and if it goes red it does not deploy: the live site keeps what it had. So the cost of the gap is a red `main`, not a bad page, and that is why leaving it open is a decision rather than an oversight. Closing it would take a cross-repository trigger, such as a digline push to `main` re-running `Build` on open pull requests here, or a merge queue.

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
