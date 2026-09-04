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

from mkdocs.exceptions import PluginError

# The pages that are not in any nav section: Home, Why, the comparison, About
# and Contact. They need a heading of their own because llms.txt has no nesting
# — every section is an H2 — and "the ones that are not the documentation" is
# what they have in common.
ROOT_SECTION = "Start here"

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
    # Start here
    "index.md": (
        "What digline is in one screen: the sentence, what `digline compare` "
        "prints, and the two things that will never be on the roadmap"
    ),
    "why.md": (
        "Why an ordinary pass/fail test cannot see a quality regression — the "
        "same prompt scores 4 one morning and 3 the next, and the model moves "
        "under you — and what an approved baseline measures instead"
    ),
    "comparison.md": (
        "Which question each family of tools answers — snapshot testing, "
        "observability, exploration frameworks, Opik — and which one digline "
        "answers: did it get worse than what I approved?"
    ),
    "about.md": "Who builds digline, under which licence, and where the code is",
    "contact.md": (
        "Where to write about digline: mail for questions, GitHub issues for "
        "bugs, the same address for security reports"
    ),
    # Handbook
    "handbook/index.md": (
        "What the seven chapters cover and the order to read them in — about "
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
    "handbook/03-checks.md": (
        "How to turn an output into a verdict, and the rule that saves the most "
        "time: use a model to judge only what nothing else can"
    ),
    "handbook/04-the-judge.md": (
        "How to measure how often your judge disagrees with itself, and why "
        "that number has to exist before any score it produces can be read"
    ),
    "handbook/05-the-reference.md": (
        "Why a threshold is not a reference, and how to choose the one number "
        "you agree to be measured against"
    ),
    "handbook/06-maintenance.md": (
        "When to run the suite, what should make you look, and what to do the "
        "morning it turns red and you changed nothing"
    ),
    "handbook/07-for-teams-building-for-others.md": (
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
    "product/view.md": (
        "How to read your runs, the baseline and a comparison in a local "
        "browser UI over `.digline/` — stdlib only, no JavaScript, no state of "
        "its own"
    ),
    "product/migrate.md": (
        "How to bring stored runs and a baseline up to the schema version this "
        "release reads, and what a scan does with a document it cannot read"
    ),
    # Examples
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
    "product/examples/langchain4j.md": (
        "What to put in the repository of a LangChain4j service — Spring Boot "
        "or Quarkus — when the endpoint and not the framework is the contract"
    ),
    "product/examples/quickstart-toml.md": (
        "How a team that writes no Python gates a prompt in CI: a `suite.toml`, "
        "a `cases.json`, and no code at all"
    ),
    # Decisions
    "product/adr/index.md": (
        "Every architecture decision behind digline, in the order it was taken, "
        "superseded ones kept and marked"
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
}


# ── the Markdown behind a page ───────────────────────────────────────────────

_FRONT_MATTER = re.compile(r"\A---\r?\n.*?\r?\n---[ \t]*\r?\n", re.S)
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)


def _source(path: str) -> str | None:
    """The page's Markdown with the front matter off, or None if it has none.

    None happens once, and it is the landing: docs/index.md is a stub whose
    words live in overrides/home.html. Copying it out would publish a file with
    a comment in it and link an agent at nothing, so that one page is listed by
    its rendered URL instead.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    body = _FRONT_MATTER.sub("", text).lstrip()
    if not _HTML_COMMENT.sub("", body).strip():
        return None
    return body


# ── the shape of the file ────────────────────────────────────────────────────


def _sections(items, title: str) -> list[tuple[str, list]]:
    """[(heading, pages)] for one level of the nav, then for each of its groups.

    The pages sitting directly in a level come out under that level's own
    heading, and every group inside it becomes a heading of its own after it —
    which is how the four Docs sub-sections (Reference, Examples, Decisions)
    reach llms.txt as H2s in a format that has no H3s to give them.

    Nav entries that are neither — the one external link, to digline/brief —
    fall through: this file is an index of this site, and every URL in it has
    to be a page that is in the build.
    """
    out: list[tuple[str, list]] = []
    pages = [item for item in items if item.is_page]
    if pages:
        out.append((title, pages))
    for item in items:
        if item.is_section:
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
            body = _source(page.file.abs_src_path)
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
