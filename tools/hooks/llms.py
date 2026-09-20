"""llms.txt, and the Markdown behind every page it lists.

An agent that lands on this site gets HTML written for a person: a theme, a
sidebar, a palette switch, and the words somewhere inside it. llms.txt is the
other door — https://llmstxt.org — a single file at the root that says what the
site is and which page answers which question, in the order a reader should
meet them.

Two things are written here, both after the build, both derived and neither
committed:

  * ``site/llms.txt``   the index: an H1, a summary, and one section per group
    in the navigation, each link carrying a line about what the page answers.
  * ``site/<page>.md``  the source Markdown of every page, front matter off, at
    the path the page has in ``docs/``.

The second is what makes the first worth having: the links in llms.txt point at
Markdown, so an agent that follows one gets the page and not the chrome around
it. Mirroring the source path — ``docs/handbook/02-cases.md`` becomes
``/handbook/02-cases.md`` — is not only tidy: the relative links *inside* those
files then resolve against each other exactly as they do in the repository, so
the Markdown side of the site is navigable on its own.

Why a hook and not a plugin: there is a plugin for this, and taking it would put
a dependency in the build for two files this repository can write itself. The
descriptions are the only part that cannot be derived, and they live below.

── the gate ─────────────────────────────────────────────────────────────────
Every page in the nav needs a line in ``DESCRIPTIONS`` and the build fails
naming the ones that do not have it. That is the whole anti-rot mechanism, and
it leans on the one already there: a page that reaches ``docs/`` without a nav
entry fails ``--strict`` (``validation.omitted_files``), and a page that reaches
the nav without a description fails here. Neither can arrive quietly.

A description says what the page *answers*, not what it is called — the title is
already in the link. It is read by something deciding whether to spend a fetch.
"""

from __future__ import annotations

import os
import re
import sys

from mkdocs.exceptions import PluginError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import languages  # noqa: E402  tools/languages.py

# The pages that are not in any nav section: Home, Start here, Why, digline for
# agents, About and Contact. They need a heading of their own
# because llms.txt has no nesting — every section is an H2 — and "the ones that
# are not the documentation" is what they have in common.
#
# Not "Start here", which is what this said until one of those pages was given
# that name: a link titled "Start here" inside a section titled "Start here"
# reads, to something deciding what to fetch, as though the section were about
# the page. The label is only ever printed as that H2, so it names the group and
# leaves the name to the page.
ROOT_SECTION = "Overview"

# The summary under the H1. The landing's own words: the sentence under the
# wordmark, then the two paragraphs that say what you get and where it lives.
# Lifted rather than written, so there is one description of the product and
# not a second one that drifts from it — the same reason the SEO hook prefers a
# page's own first paragraph to anything it could compose.
TAGLINE = (
    "Regression testing for LLM applications, with the baseline in your "
    "repository, not on someone's server."
)

SUMMARY = """\
digline gives you an approved reference — the baseline — and on every change
tells you whether you are below it: which case, which check, by how much. The
baseline is a JSON file in your repository, so it goes through code review and
it rolls back with git. There is no hosted service that receives your payloads
and no usage data collection: the runs happen on your machines.

Every link below is the page's Markdown source. Drop the `.md` for the rendered
page — `/why.md` is `/why/`.\
"""

# ── what each page answers ───────────────────────────────────────────────────
# Keyed by the path under docs/, which for everything under product/ is the path
# tools/sync-docs.sh gives it. One line, no full stop needed at the end of a
# clause that is already a sentence, and never a restatement of the title: the
# title is in the link, this is the reason to open it.

DESCRIPTIONS: dict[str, str] = {
    # Overview
    "index.md": (
        "What digline is in one screen: the sentence, what `digline compare` "
        "prints, and the two things that will never be on the roadmap"
    ),
    "start.md": (
        "What a silent LLM regression is and why an ordinary test cannot see "
        "one, for a reader who has not met the problem yet — plus a short "
        "video of `digline compare` finding one"
    ),
    "why.md": (
        "Why an ordinary pass/fail test cannot see a quality regression — the "
        "same prompt scores 4 one morning and 3 the next, and the model moves "
        "under you — and what an approved baseline measures instead"
    ),
    "agents.md": (
        "What a coding agent can reach on each surface — MCP, the operator "
        "loop, pytest, the Action — and why none of them lets it promote a "
        "baseline"
    ),
    "comparison/index.md": (
        "Which question each family of tools answers — snapshot testing, "
        "observability, exploration, benchmarking, and regression testing "
        "against an approved baseline — and why the last one is digline's: "
        "did it get worse than what I approved? Links to a page per tool "
        "underneath"
    ),
    "comparison/promptfoo.md": (
        "What promptfoo does well — the prompt and provider matrix, its "
        "assertion library, `promptfoo redteam` — and where digline "
        "differs: a committed reference rather than a threshold, a noise floor "
        "measured per case, and a three-state verdict as the exit code"
    ),
    "comparison/deepeval.md": (
        "What DeepEval does well — its metric library, `assert_test` "
        "inside pytest, `Synthesizer`, DeepTeam — and where digline "
        "differs: the approved run is a committed file rather than an official "
        "run on Confident AI"
    ),
    "comparison/braintrust.md": (
        "What Braintrust does well — `Eval()`, experiments against a "
        "persistent baseline, Loop, hybrid self-hosting — and where "
        "digline differs: the same comparison, with the reference in git and "
        "no platform to run"
    ),
    "comparison/langsmith.md": (
        "What LangSmith does well — tracing, datasets and experiments, "
        "`evaluate()`, annotation queues, online evaluation — and where "
        "digline differs: one pre-deploy question, a committed reference and "
        "an exit code"
    ),
    "comparison/langfuse.md": (
        "What Langfuse does well — OpenTelemetry tracing, prompt "
        "management, batch evaluation over past traces, an MIT self-hosted "
        "core — and where digline differs: no platform at all, and the "
        "approval kept in git"
    ),
    "comparison/inspect-ai.md": (
        "What Inspect AI does well — `Task`, solvers and scorers, "
        "sandboxed execution, epochs and reducers — and where digline "
        "differs: an approved reference to regress against rather than a "
        "benchmark to score"
    ),
    "comparison/opik.md": (
        "What Opik does well — Apache-2.0 tracing, experiments, "
        "guardrails, the Agent Optimizer, a self-hostable platform — and "
        "where digline differs: a file in your repository instead of a backend "
        "to deploy"
    ),
    "about.md": "Who builds digline, under which licence, and where the code is",
    "contact.md": (
        "Where to write about digline: mail for questions, GitHub issues for "
        "bugs, the same address for security reports"
    ),
    # Handbook
    "handbook/index.md": (
        "What the eight chapters cover and the order to read them in — about "
        "evaluating an LLM feature, not about the tool: nothing here needs "
        "digline installed"
    ),
    "handbook/01-what-you-are-shipping.md": (
        "Why a model call looks like a function and is not one, and what that "
        "costs you once it is in front of users"
    ),
    "handbook/02-cases.md": (
        "What a case is, why almost every team has a prompt and no cases, and "
        "how to have twenty of them by this afternoon"
    ),
    "handbook/03-ground-truth.md": (
        "Where the expected answer comes from when nobody gives you one, and "
        "why whether it can be collected is decided when you write the feature"
    ),
    "handbook/04-checks.md": (
        "How to turn an output into a verdict, and the rule that saves the most "
        "time: use a model to judge only what nothing else can"
    ),
    "handbook/05-the-judge.md": (
        "How to measure how often your judge disagrees with itself, and why "
        "that number has to exist before any score it produces can be read"
    ),
    "handbook/06-the-reference.md": (
        "Why a threshold is not a reference, and how to choose the one number "
        "you agree to be measured against"
    ),
    "handbook/07-maintenance.md": (
        "When to run the suite, what should make you look, and what to do the "
        "morning it turns red and you changed nothing"
    ),
    "handbook/08-for-teams-building-for-others.md": (
        "The two extra jobs a suite does when the LLM feature belongs to a "
        "client, and the one rule about their data that cannot be bent"
    ),
    # Docs
    "product/guide.md": (
        "How to work with digline end to end, in the order the problems arrive: "
        "a first suite, a baseline, the judge's noise, sampling, thresholds, "
        "and the comparison in CI"
    ),
    "product/metrics.md": (
        "Which metric to reach for, per assertion and per aggregate: what each "
        "one takes, what it produces, and how it misleads you if you are not "
        "looking"
    ),
    "product/selection.md": (
        "How to test a system that selects items from its input: the offered "
        "set declared per case in a `suite.py`, and why an empty selection must "
        "never pass alone"
    ),
    "product/declarative.md": (
        "How to write a suite as data in a `suite.toml` rather than a "
        "`suite.py`, and which suites should stay Python"
    ),
    "product/roadmap.md": (
        "What is being built next, as tracks and gates rather than dates, and "
        "the two things that will never be built"
    ),
    "product/changelog.md": "What changed for you in each release of digline",
    # Reference
    "product/api.md": (
        "What to import when writing a suite: what `digline.core` and "
        "`digline.run` export, the Judge protocols, and what an assertion "
        "returns"
    ),
    "product/diff.md": (
        "How to choose between two runs neither of which is a baseline \u2014 "
        "prompt A or prompt B, one model or another \u2014 with a report that "
        "names no reference and gates nothing"
    ),
    "product/explain.md": (
        "How to read one run back at length \u2014 what moved, against which "
        "measured interval, what differed underneath \u2014 from a command "
        "that states the facts and gives no advice"
    ),
    "product/log.md": (
        "How to tell whether the model behind your alias changed, read down the "
        "runs you already stored \u2014 what each side sent, what the provider "
        "said answered, and why most of that history is absence"
    ),
    "product/register.md": (
        "How to write down what a person decided about a comparison \u2014 "
        "accepted, rejected or unsure \u2014 where the reason goes, and why no "
        "agent and no schedule may record one"
    ),
    "product/rejudge.md": (
        "How to see what the same answers score under a changed judge, rubric "
        "or threshold without paying the target again, why that is a replay "
        "that declares itself rather than a cache, and why it cannot be promoted"
    ),
    "product/view.md": (
        "How to read your runs, the baseline and a comparison in a local "
        "browser UI over `.digline/` — stdlib only, no JavaScript, no state of "
        "its own"
    ),
    "product/migrate.md": (
        "How to bring stored runs and a baseline up to the schema version this "
        "release reads, and what a scan does with a document it cannot read"
    ),
    "product/docker.md": (
        "What the official `ghcr.io/digline/digline` image contains and what it "
        "deliberately does not, which tag to pin in CI, and how to derive it "
        "for a suite with dependencies of its own"
    ),
    "product/mcp.md": (
        "How a coding agent reads a digline result and measures a new one over "
        "MCP, and why the server has no tool that promotes a baseline"
    ),
    "product/pytest.md": (
        "How to gate a pytest run on a digline comparison \u2014 one row per "
        "check, a suspension as a skip, and no provider call unless you ask "
        "for one \u2014 and what pytest's single exit code cannot tell apart"
    ),
    "product/operator.md": (
        "What an operator may decide alone \u2014 re-run, classify a draw from "
        "a drift, diff two candidates, all under a stopping rule declared "
        "before the first run \u2014 what it must escalate, why `promote` is "
        "absent from its surface rather than forbidden, and why the loop runs "
        "in your perimeter instead of as a service of ours"
    ),
    "product/security.md": (
        "digline's own threat model: the five surfaces an input can reach, "
        "why a suite file executing is a declared boundary rather than a "
        "gap, the six fixes of 0.7.1 and 0.7.2 and the four advisories, "
        "the delta-pass rule "
        "\u2014 and the attestations, pins and Scorecard run you can check"
    ),
    # Examples
    "product/examples/index.md": (
        "Every worked example by the question it answers, each a directory with "
        "its suite, its committed baseline and its CI job, and a whole product "
        "built on digline"
    ),
    "product/examples/prompt-first.md": (
        "How to tell whether an edit to a prompt made the answers better or "
        "only different, when there is no application around it yet"
    ),
    "product/examples/classifier.md": (
        "How to keep an LLM classifier under control: several samples per case "
        "and a majority, precision over the whole set as the gate, thresholds "
        "measured rather than chosen"
    ),
    "product/examples/rag.md": (
        "How to check that a RAG does not make things up, with the retrieved "
        "passages frozen into each case so the generator is what is measured"
    ),
    "product/examples/external-app.md": (
        "How to test an application digline cannot import — Java, Go, a shell "
        "script behind a socket: a body it can post and a field it can read back"
    ),
    "product/examples/langchain.md": (
        "How to tell what a LangChain upgrade changed, with digline importing "
        "the chain and calling it in process: no server, no HTTP, no port"
    ),
    "product/examples/langgraph.md": (
        "How to gate a LangGraph agent on what it did rather than what it "
        "said: which tools it called, in what order, and with which arguments, "
        "with the tools executing for real and the model scripted so CI needs "
        "no key"
    ),
    "product/examples/llamaindex.md": (
        "How to tell whether a LlamaIndex RAG still answers from the right "
        "page, with retrieval running on every run instead of frozen into "
        "the cases"
    ),
    "product/examples/langchain4j.md": (
        "What to put in the repository of a LangChain4j service — Spring Boot "
        "or Quarkus — when the endpoint and not the framework is the contract"
    ),
    "product/examples/quickstart-toml.md": (
        "How a team that writes no Python gates a prompt in CI: a `suite.toml`, "
        "a `cases.json`, and no code at all"
    ),
    "product/examples/operator.md": (
        "The operator loop assembled: a suite re-run on a schedule within a "
        "declared stopping rule, a draw told from a drift, a three-layer alert"
    ),
    # Decisions
    "product/adr/index.md": (
        "Every architecture decision behind digline, oldest first, each with "
        "its status and the date it was taken, and nothing deleted when a "
        "decision changes"
    ),
    "product/adr/0001-verdict-not-score.md": (
        "Why an assertion produces a three-state verdict rather than a bare "
        "score, and why the comparison against the baseline lives in the core"
    ),
    "product/adr/0002-three-worlds-and-where-the-data-lives.md": (
        "Where each kind of data lives across the developer's, the "
        "consultancy's and the customer's world, so that no customer's payload "
        "leaves its own"
    ),
    "product/adr/0003-artifacts-travel-only-when-the-suite-says-so.md": (
        "Why a run records the verdicts and the commit but not the prompt that "
        "produced them, and which files a suite can ask to store"
    ),
    "product/adr/0004-every-plugin-is-a-target-and-a-judge.md": (
        "Why every provider plugin ships both sides — the system under test and "
        "the judge that evaluates it — and the core implements neither"
    ),
    "product/adr/0005-the-configuration-of-the-system-under-test.md": (
        "Proposed, nothing implemented: how a run would record which model "
        "answered, at what temperature, under what token cap"
    ),
    "product/adr/0006-repeated-samples-and-the-noise-floor.md": (
        "Why a case is run more than once, and why a drop is a regression only "
        "when it clears the noise floor those samples measure — the fix for a "
        "tool that cries wolf on its own measurement error"
    ),
    "product/adr/0007-the-declarative-suite-format.md": (
        "What the TOML suite format can express, where it stops and Python "
        "takes over, and why both forms build the same objects and share one "
        "baseline"
    ),
    "product/adr/0008-the-two-run-report.md": (
        "Why \"should I switch?\" is a different question from \"did it get "
        "worse?\", and why the report that answers it names neither run the "
        "reference and never gates a pipeline"
    ),
    "product/adr/0009-boundary-semantics.md": (
        "One rule for every limit \u2014 compared at the precision the document "
        "stores, and inclusive \u2014 and why a threshold met exactly must pass "
        "while a delta must not be decided by a residue nobody can see"
    ),
    "product/adr/0010-per-group-aggregates.md": (
        "Why an aggregate over the whole run hides a class that is broken, and "
        "how a suite splits one by a variable its cases already carry without "
        "losing the noise floor"
    ),
    "product/adr/0011-the-mcp-server.md": (
        "Why the MCP server has no tool that promotes a baseline \u2014 an "
        "absence, not a refusal \u2014 and what a run projected for an agent "
        "may and may not carry"
    ),
    "product/adr/0012-the-reading.md": (
        "Why the command that reads a run back at length states no advice and "
        "quotes no judge, and why the facts it is built from are a type that "
        "cannot hold a payload rather than a filter that drops one"
    ),
    "product/adr/0013-the-pytest-plugin.md": (
        "Why a pytest row is one check and not one case, why comparing is the "
        "default and running is a flag that refuses under --collect-only, and "
        "why there is no way to promote a baseline from a green test run"
    ),
    "product/adr/0014-what-may-ride-a-schema-bump.md": (
        "Why a field may ride a schema bump only if it leaves `config_hash` "
        "alone, migrates without inventing a value and widens nothing that "
        "travels — and why a document now says which digline wrote it"
    ),
    "product/adr/0015-the-recorded-output-and-the-declared-re-judge.md": (
        "Why the model's answers are recorded only on opt-in and released by "
        "no `Disclosure`, why a re-judge is a replay that declares itself "
        "rather than a cache, and why a replay can never become the baseline"
    ),
    "product/adr/0016-the-canary-case.md": (
        "How a suite notices that the model behind an alias changed when the "
        "provider says nothing: a case kept out of every metric that stops "
        "the pipeline when it moves beyond its noise, in either direction"
    ),
    "product/adr/0017-the-journal-and-the-resumed-run.md": (
        "How a run killed mid-flight is finished rather than paid for again: a "
        "per-case journal that holds nothing the run file would not, a "
        "`--resume` refused unless every fact the run asserts is true of both "
        "halves, and why the resumed run carries no marker and no schema bump"
    ),
    "product/adr/0018-the-recorded-trajectory-and-the-agent-under-test.md": (
        "Why a suite that judged an agent's tool calls could never be "
        "re-judged, and what it cost to close that: the trajectory recorded "
        "beside the answer it belongs to, arguments that are payload and never "
        "travel, and a check for the right tool asked the wrong question"
    ),
    "product/adr/0019-the-reasoning-operator.md": (
        "How the operator loop exercises a judgment somebody wrote down: a "
        "`[policy]` in `operator.toml` the agent may not edit, a decision that "
        "names the clause it applied and the policy's digest, clauses that may "
        "hold a cycle but never wake one, three floors none may lower, and an "
        "append-only journal where every hold is written"
    ),
    "product/adr/0020-the-reading-across-runs.md": (
        "How `digline log` reads the story of an alias down a suite's stored "
        "runs: a roll is only the same sent model answering as a different "
        "recorded one, seven absences each with its own sentence, a replay that "
        "asked the target nothing, a row with no score by type, and the MCP "
        "surface growing once to eight tools with `explain` beside it"
    ),
    "product/adr/0021-the-register.md": (
        "How a person's decision about a comparison is kept: `digline register` "
        "with a mandatory accepted, rejected or unsure, one committed line of "
        "counts and keys per disposition, the reason in the commit message, "
        "absent from the MCP, and one retention rule for both ledgers"
    ),
    "product/adr/0022-the-declared-price.md": (
        "How a suite prices an OpenAI-compatible aggregator, a gateway or a "
        "self-hosted model: `[target.pricing]` with four per-million rates, a "
        "declared price that wins over the plugin's list and enters "
        "`config_hash`, rates withheld at a named endpoint as a declared latch, "
        "and `promote --target` so a multi-target suite names what it signs"
    ),
    "product/adr/0024-the-judge-as-an-instrument.md": (
        "How the judge is measured rather than trusted: read the rendered judge "
        "prompt before re-running anything, a calibration case with a written "
        "answer whose score outside its declared band exits 2 with no baseline, "
        "`judge_samples` never reported without that result, and two readings "
        "printed without thresholds until data sizes them \u2014 the share of "
        "judged scores at exactly 0 or 1, and the run-to-run range"
    ),
    "product/adr/0025-the-tokens-and-the-bill.md": (
        "What a run cost, recorded instead of thrown away: token counts had "
        "never reached any document and the judge's spending had never reached "
        "one at all, so run-level totals now stand on every run \u2014 target "
        "and judge kept apart, because one is the thing measured and the other "
        "the instrument \u2014 with per-call counts only where the suite "
        "already records answers, a `counted` that admits when a total covers "
        "part of the run, and the totals crossing a boundary while the per-call "
        "counts do not"
    ),
    "product/adr/0026-the-thinking-a-model-charged-for.md": (
        "The output tokens nobody reads, told apart from the ones they do: a "
        "model that reasons before it answers is billed for both, so a reply "
        "now records how many of its output tokens were thinking \u2014 a "
        "breakdown of a count already paid for, never added to it, which is "
        "the inverse of the cache-write case it will be mistaken for \u2014 "
        "with not-reported kept distinct from a measured zero, a reply "
        "claiming more thinking than output refused rather than clamped, and "
        "any unreported side making the total unreported"
    ),
    "product/adr/0027-the-run-reconciles.md": (
        "Whether a run recorded an answer to every question it asked: the "
        "driver reads its own dispatch back \u2014 a suspended case asked "
        "nothing, a calibration case its one check, every other case every "
        "assertion \u2014 and records each gap as an errored verdict naming "
        "the case and the check, so the run exits 2, cannot be promoted and "
        "says it is not a regression; with what no count can see, an exception "
        "the user's own code caught, stated rather than claimed"
    ),
    # Writing
    "blog/index.md": (
        "The posts, newest first, each with the runs behind it \u2014 written "
        "from the pipelines the author runs rather than about the library"
    ),
    "blog/denominator-trap.md": (
        "Why a case that errors, is suspended or carries no label leaves a "
        "run-level aggregate's denominator and raises the score exactly when "
        "it was the failing case; three questions to ask of your own eval "
        "code, and what digline's compare and explain now say when the two "
        "sides counted different cases"
    ),
    "blog/bad-evals-my-own.md": (
        "Five exercises on two LLM judges the author runs, artifacts first and "
        "explanations after: a noise floor that itself moves across sixteen "
        "identical runs, prompt edits a small judge misreads, a precision "
        "measured on a censored ground truth, a suite whose class balance "
        "decides the answer, a one-case threshold that stops holding as the "
        "suite grows, and five gaps the exercise found in the tool"
    ),
    "blog/my-llm-eval-cried-wolf.md": (
        "A worked example of a false alarm and the fix: why one reference "
        "score per case cannot tell a regression from a resample, how a "
        "min/max band over K=5 separates them on a public fixture, the three "
        "changes it judged the week after, and the three things it still "
        "cannot see"
    ),
}


# ── the Markdown behind a page ───────────────────────────────────────────────

_FRONT_MATTER = re.compile(r"\A---\r?\n.*?\r?\n---[ \t]*\r?\n", re.S)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)


def _source(page) -> str | None:
    """The page's Markdown with the front matter off, or None if it has none.

    The Markdown the page was rendered from, as the hooks left it — which for
    every page but two is the file without its front matter. The two are the
    indexes tools/hooks/indexes.py fills, whose files hold a placeholder where
    the copy should hold the list.

    None happens once, and it is the landing: docs/index.md is a stub whose
    words live in overrides/home.html. Copying it out would publish a file with
    a comment in it and link an agent at nothing, so that one page is listed by
    its rendered URL instead.
    """
    if page.markdown is not None:
        text = page.markdown
    else:
        try:
            with open(page.file.abs_src_path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            return None
    body = _FRONT_MATTER.sub("", text).lstrip()
    if not _HTML_COMMENT.sub("", body).strip():
        return None
    return body


# ── the shape of the file ────────────────────────────────────────────────────


def _sections(items, title: str) -> list[tuple[str, list]]:
    """[(heading, pages)] for one level of the nav and each of its groups, in
    the nav's order.

    Every group inside a level becomes a heading of its own — which is how the
    Docs groups (Essentials, the three command groups, Running it, Reference,
    Examples, Decisions) reach llms.txt as H2s in a format that has no H3s to
    give them. The pages sitting directly in a level come out under that
    level's own heading, where the first of them stands among its groups: Docs
    lists its groups first and ends on Changelog and Roadmap, so "## Docs"
    comes after Decisions; the root opens on Home, so "## Overview" comes
    first. One heading per level: the root's About and Contact, which close the
    nav, stay under that first "## Overview" rather than open a second one. A
    group holding only groups, like Commands, has no pages of its own and no
    heading.

    Nav entries that are neither — the one external link, to digline/brief —
    fall through: this file is an index of this site, and every URL in it has
    to be a page that is in the build.

    Translations are left out by name, whatever the nav says: this is the
    index of the English site, the original, and a page under one of
    languages.LANGUAGES' folders (docs/it/why.md) is never in it, nor is its
    Markdown copied beside it.
    """
    out: list[tuple[str, list]] = []
    pages = [item for item in items
             if item.is_page and not languages.is_translation(item.file.src_uri)]
    for item in items:
        if item.is_page and item is pages[0]:
            out.append((title, pages))
        elif item.is_section:
            out.extend(_sections(item.children, item.title))
    return out


_nav = None


# ── the hooks mkdocs calls ───────────────────────────────────────────────────


def on_nav(nav, config, files, **kwargs):
    """Hold on to the nav, and refuse a page nobody has described.

    Here rather than at post-build because this is the earliest event that has
    the whole nav in hand: the build stops before rendering thirty pages to
    tell you about a line you have to add.
    """
    global _nav
    _nav = nav

    missing = [
        (item.file.src_uri, item.title)
        for _, pages in _sections(nav.items, ROOT_SECTION)
        for item in pages
        if item.file.src_uri not in DESCRIPTIONS
    ]
    if missing:
        lines = [
            f'    "{src}": "…",  # {title or "no title in the nav"}'
            for src, title in missing
        ]
        raise PluginError(
            "llms.txt: "
            + f"{len(missing)} page(s) in the nav with no description.\n"
            + "Add to DESCRIPTIONS in tools/hooks/llms.py — one line saying "
            + "what the page answers:\n"
            + "\n".join(lines)
        )
    return nav


def on_post_build(config, **kwargs):
    """Write the Markdown copies first, then the index that points at them."""
    assert _nav is not None
    site_dir = config["site_dir"]
    site_url = (config["site_url"] or "").rstrip("/") + "/"

    out = [f"# {config['site_name']}", "", f"> {TAGLINE}", "", SUMMARY, ""]

    for heading, pages in _sections(_nav.items, ROOT_SECTION):
        out += [f"## {heading}", ""]
        for page in pages:
            src_uri = page.file.src_uri
            body = _source(page)
            if body is None:
                url = site_url + page.url
            else:
                target = os.path.join(site_dir, *src_uri.split("/"))
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "w", encoding="utf-8") as fh:
                    fh.write(body if body.endswith("\n") else body + "\n")
                url = site_url + src_uri
            title = page.title or config["site_name"]
            out.append(f"- [{title}]({url}): {DESCRIPTIONS[src_uri]}")
        out.append("")

    with open(os.path.join(site_dir, "llms.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(out).rstrip("\n") + "\n")
