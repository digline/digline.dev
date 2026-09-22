#!/usr/bin/env -S uv run python
"""The translating agent: the presentation pages and the catalog, into it, de, es.

For each language asked for, and in this order:

  1. the catalog, i18n/<lang>.yml: every key of i18n/en.yml whose English has
     changed since it was translated (its digest against the catalog's
     source_keys), or that the catalog does not have yet. The
     do_not_translate section is never sent and never written: it is read from
     the file as it is and put back as it was;
  2. each page asked for, docs/<lang>/<page>.md: translated when it does not
     exist, or when its source_sha is not the English page's digest now. A
     page translated before is sent with its previous translation and the
     diff of the English since source_commit, and the model is asked for the
     smallest change. A page whose original has not moved is skipped, and
     costs nothing.

Every translation is checked before it is kept. It is written into a copy of
the repository (a local clone, so that source_commit and the notice's date
resolve, with the working tree laid over it), the site is built there with
--strict, and tools/check-translations.py compares it with its original. When
the build or the check fails, the model is asked once more, with the problems;
when it fails again, that page, or that language's catalog, is not written,
and the report says why. A language whose catalog cannot be written has none
of its pages translated either: a page cannot be built without it.

A page that passes is read once more by a second call, which reports errors of
meaning only — a negation turned round, a threshold or a behaviour described
the other way, a claim the English does not make, something left out, a term
in a sense it does not have ("deprecate" as "abschreiben") — as JSON, {ok,
issues, notes}; notes are the evident calques. A page with issues or notes is
corrected once, with both as its context, then checked and read again: it is
marked "needs attention" only when an error of meaning is still there, and the
notes still there are reported, never blocking (a correction that fails the
checks is not kept).

The instructions ask for idiomatic Italian, German and Spanish, not calques of
the English, with the calques and wrong senses these pages have had written as
concepts, each with its wording in every language (CONCEPTS), and for
quantified statements kept at their strength ("most" is not "almost all").

--plan prints what a run would translate, as JSON, and calls nothing:
translate.yml starts no run when there is nothing.

--summary prints, for the Handbook, which is translated by hand and never on
a push, one line per language: how many of its pages are translated, and how
many of those are behind the English. docs.yml writes it into every build's
summary, so a Handbook that has fallen behind is seen without a run.

── the model and the bill ───────────────────────────────────────────────────
claude-opus-5 for both calls, adaptive thinking, structured JSON output, and
server-side fallbacks ("default"): a request the model declines is run again
on the model Anthropic routes it to, and the report names the model that
answered. Every call's input and output tokens are recorded and priced from
PRICES, read from Anthropic's pricing page on PRICES_READ. Before the first call
the run prints what it expects to cost, and the most it could (estimate()); it
stops before the next call once --max-cost (USD) has been spent.

── the credentials ──────────────────────────────────────────────────────────
No API key. In GitHub Actions the job asks GitHub for an OIDC token and
exchanges it at https://api.anthropic.com/v1/oauth/token (Workload Identity
Federation) for a short-lived token, passed to the SDK as auth_token — sent as
Authorization: Bearer. A token is exchanged again when less than
REFRESH_MARGIN seconds of it are left, so a long run never calls with an
expired one. The identifiers are the environment's ANTHROPIC_FEDERATION_RULE_ID,
ANTHROPIC_ORGANIZATION_ID, ANTHROPIC_SERVICE_ACCOUNT_ID and
ANTHROPIC_WORKSPACE_ID; the GitHub side, ACTIONS_ID_TOKEN_REQUEST_URL and
ACTIONS_ID_TOKEN_REQUEST_TOKEN, which a job with id-token: write has.

── what it writes ───────────────────────────────────────────────────────────
Without --dry-run the translations are also written into docs/ and i18n/ of
the repository, for translate.yml to commit and open a pull request with, and
--out gets pr-body.md, the report without the texts, and summary.json.

With --dry-run, nothing in docs/ or i18n/: everything goes to --out —
docs/<lang>/<page>.md and i18n/<lang>.yml for what was translated or carried
over unchanged, report.md, and calls.json. --existing DIR lays the
translations of an earlier dry run (its --out) over the repository first, so
a second run skips what the first translated.

    usage: tools/translate.py --langs it,de,es          # --pages defaults to
                                                        # the presentation pages
           tools/translate.py --langs it --pages handbook      # the Handbook's ten
           tools/translate.py --langs it --pages handbook/02-cases
                              --out DIR [--dry-run] [--existing DIR] [--max-cost 12]
           tools/translate.py --langs it,de,es --pages ... --plan
           tools/translate.py --summary
           tools/translate.py --selftest

--selftest makes no network call: a fake model and, where it needs one, a fake
check, to test the prompts, the skipping of what has not changed, the fixed
section, the second attempt, the spending limit, the token's renewal and the
report; and one real build, of a page and a catalog the fake model translates.
"""

from __future__ import annotations

import argparse
import dataclasses
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from typing import Callable

import yaml

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
import catalog  # noqa: E402  tools/catalog.py
import languages  # noqa: E402  tools/languages.py
import translation  # noqa: E402  tools/translation.py

MODEL = "claude-opus-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"

# USD per million tokens (input, output), from
# https://platform.claude.com/docs/en/about-claude/pricing, read on PRICES_READ.
# claude-opus-4-8 is where a declined request may be served. Thinking is billed
# as output; the price is the same across the whole context window.
PRICES = {"claude-opus-5": (5.0, 25.0), "claude-opus-4-8": (5.0, 25.0)}
PRICES_READ = "2026-09-17"

DEFAULT_MAX_COST = 12.0
REFRESH_MARGIN = 120
MAX_TOKENS = 64000

LANGUAGE_NAMES = {"it": "Italian", "de": "German", "es": "Spanish"}
ADDRESS = {"it": 'the informal "tu"', "de": 'the informal "du"', "es": 'the informal "tú"'}
WE = {"it": '"noi"', "de": '"wir"', "es": '"nosotros"'}
# A page by its path under docs/ without .md: "why", "handbook/02-cases". The
# presentation pages keep the names they always had, and "index" is the home,
# never the Handbook's index, which is "handbook/index".
PAGE_FILES = {os.path.splitext(page)[0]: page for page in languages.PAGES}
# Names that stand for several pages, in the nav's order.
PAGE_GROUPS = {"handbook": [os.path.splitext(page)[0] for page in languages.HANDBOOK_PAGES]}
# What a run translates when it is not told: the presentation pages. The
# Handbook is asked for by name (RUNBOOK.md, Translations).
DEFAULT_PAGES = [os.path.splitext(page)[0] for page in languages.PRESENTATION_PAGES]

# The front matter a translation translates; the rest is copied or stamped.
TRANSLATED_FIELDS = ("title", "seo_title", "description", "kicker", "accent")


class BudgetExceeded(Exception):
    pass


class ModelError(Exception):
    pass


# ── the bill ─────────────────────────────────────────────────────────────────


@dataclasses.dataclass
class Call:
    kind: str
    lang: str
    subject: str
    attempt: int
    model: str
    input_tokens: int
    output_tokens: int
    cost: float


class Ledger:
    def __init__(self, cap: float):
        self.cap = cap
        self.calls: list[Call] = []

    @property
    def spent(self) -> float:
        return sum(call.cost for call in self.calls)

    def check(self) -> None:
        if self.spent >= self.cap:
            raise BudgetExceeded(f"{self.spent:.4f} USD spent, the limit is {self.cap:.2f}")

    def record(self, kind, lang, subject, attempt, reply: "Reply") -> Call:
        price_in, price_out = PRICES.get(reply.model, PRICES[MODEL])
        cost = reply.input_tokens * price_in / 1e6 + reply.output_tokens * price_out / 1e6
        call = Call(kind, lang, subject, attempt, reply.model, reply.input_tokens, reply.output_tokens, cost)
        self.calls.append(call)
        return call


# ── the credentials ──────────────────────────────────────────────────────────


class FederatedToken:
    """An Anthropic token exchanged for a GitHub OIDC token, exchanged again when
    less than REFRESH_MARGIN seconds of it are left."""

    AUDIENCE = "https://api.anthropic.com"
    EXCHANGE = "https://api.anthropic.com/v1/oauth/token"

    def __init__(self, env=os.environ, clock: Callable[[], float] = time.time, http=None):
        self.env = env
        self.clock = clock
        self.http = http or self._http
        self.value: str | None = None
        self.expires_at = 0.0
        self.exchanges = 0

    @staticmethod
    def _http(method: str, url: str, headers: dict, body: bytes | None = None) -> dict:
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)

    def token(self) -> str:
        if self.value and self.clock() < self.expires_at - REFRESH_MARGIN:
            return self.value
        jwt = self.http("GET", self.env["ACTIONS_ID_TOKEN_REQUEST_URL"] + "&audience=" + self.AUDIENCE,
                        {"Authorization": "bearer " + self.env["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]})["value"]
        body = {"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": jwt,
                "federation_rule_id": self.env["ANTHROPIC_FEDERATION_RULE_ID"],
                "organization_id": self.env["ANTHROPIC_ORGANIZATION_ID"],
                "service_account_id": self.env["ANTHROPIC_SERVICE_ACCOUNT_ID"]}
        if self.env.get("ANTHROPIC_WORKSPACE_ID"):
            body["workspace_id"] = self.env["ANTHROPIC_WORKSPACE_ID"]
        started = self.clock()
        reply = self.http("POST", self.EXCHANGE, {"content-type": "application/json"},
                          json.dumps(body).encode("utf-8"))
        self.value = reply["access_token"]
        self.expires_at = started + float(reply["expires_in"])
        self.exchanges += 1
        return self.value


# ── the model ────────────────────────────────────────────────────────────────


@dataclasses.dataclass
class Reply:
    data: dict
    model: str
    input_tokens: int
    output_tokens: int


class Claude:
    """claude-opus-5 over the SDK, with a federated bearer token."""

    def __init__(self, tokens: FederatedToken):
        self.tokens = tokens
        self.fallbacks = True

    def ask(self, system: str, prompt: str, schema: dict) -> Reply:
        import anthropic

        client = anthropic.Anthropic(auth_token=self.tokens.token(), max_retries=3)
        params = dict(model=MODEL, max_tokens=MAX_TOKENS, system=system,
                      messages=[{"role": "user", "content": prompt}],
                      thinking={"type": "adaptive"},
                      output_config={"format": {"type": "json_schema", "schema": schema}})
        if self.fallbacks:
            params.update(extra_headers={"anthropic-beta": FALLBACK_BETA}, extra_body={"fallbacks": "default"})
        try:
            with client.messages.stream(**params) as stream:
                message = stream.get_final_message()
        except anthropic.BadRequestError as error:
            if self.fallbacks and "fallback" in str(error).lower():
                self.fallbacks = False
                return self.ask(system, prompt, schema)
            raise
        if message.stop_reason == "refusal":
            raise ModelError(f"declined ({getattr(message, 'stop_details', None)})")
        if message.stop_reason == "max_tokens":
            raise ModelError("the answer reached max_tokens")
        text = "".join(block.text for block in message.content if block.type == "text")
        usage = message.usage
        iterations = getattr(usage, "iterations", None) or []
        tokens_in = sum(getattr(i, "input_tokens", 0) or 0 for i in iterations) or usage.input_tokens
        tokens_out = sum(getattr(i, "output_tokens", 0) or 0 for i in iterations) or usage.output_tokens
        tokens_in += (usage.cache_read_input_tokens or 0) + (usage.cache_creation_input_tokens or 0)
        return Reply(json.loads(text), message.model, tokens_in, tokens_out)


# ── the prompts ──────────────────────────────────────────────────────────────


def rules(lang: str, root: str) -> str:
    words = translation.glossary(root)
    names = translation.data_terms(root)
    return f"""You translate the website of digline — an open-source tool for regression testing of LLM applications — from English into {LANGUAGE_NAMES[lang]}.

Write as a careful technical writer whose first language is {LANGUAGE_NAMES[lang]}: natural, precise and plain. No marketing tone, no embellishment; add nothing and leave nothing out.

- Never write in the first person plural ({WE[lang]}). Where the English says "I", keep the first person singular. Where it says "we" or "our", use the first person singular or an impersonal form. Everywhere else stay as impersonal as the English is.
- Address the reader with {ADDRESS[lang]}.
- Leave exactly as written: code spans and code blocks, commands, program output, URLs and link targets, HTML tags and attributes, HTML entities' meaning, Markdown structure, numbers (a decimal point stays a point: 0.88, never 0,88), and headings with their level — translate a heading's words, keep its number of # signs and its place.
- **Everything inside a fenced block stays byte for byte, whether or not it looks like code.** A fence may hold a diagram, a tree, a worked example, a transcript, or plain English sentences — that is still a fenced block and it is still left alone. It is the fence that decides, never what is written between the fences: a block that reads as prose you would otherwise translate is exactly the case this rule is for. The one exception is a line the page has already marked `translate="yes"`; translate that line and nothing else in the block.
- These terms name concepts of digline: {", ".join(words["keep"])}. Where the English uses one as a noun for that concept — a check, a run, the baseline, a gate, the noise floor — leave it in English, exactly as written. Where the same word is an ordinary verb or an everyday word — "check your inputs", "run the suite three times" — translate it, as a native writer would.
- Leave these names exactly as written: the commands digline {", digline ".join(names["commands"])}; the checks {", ".join(names["checks"])}; the packages {", ".join(names["packages"])}; the frameworks {", ".join(names["frameworks"])}.
- Never use these words: {", ".join(words["forbidden"].get(lang, [])) or "(none)"}.
- Write idiomatic {LANGUAGE_NAMES[lang]}, never a calque: do not carry English syntax, idioms or collocations across word for word. Say what a native technical writer would say in their place.
- Keep the strength of every quantified or hedged statement: "most" is the majority, not "almost all"; "some", "often", "rarely", "about", "may" keep exactly their force.{calques(lang)}"""


# Calques and wrong senses seen in translations of these pages, by concept: the
# English, what it means, and in each language the wording to use, with the
# calques actually met there (none is made up). Every concept has every language: the rule is the
# same in all of them, only the words differ.
CONCEPTS = [
    {"english": "catches below the line", "sense": "a threshold catches what falls under it",
     "it": ("sotto soglia", ["intercetta sotto la linea"]),
     "de": ("unter dem Schwellenwert", ["unter der Linie"]),
     "es": ("por debajo del umbral", [])},
    {"english": "it is not yours to show", "sense": "you are not the one able to show it",
     "it": ("non puoi mostrarlo tu", ["non è tuo da mostrare"]),
     "de": ("kannst du nicht vorzeigen", []),
     "es": ("no puedes mostrarlo", ["no es tuyo para mostrarlo"])},
    {"english": "worth reading", "sense": "deserving to be read",
     "it": ("vale la pena leggere", ["valgono la lettura"]),
     "de": ("lesenswert", []),
     "es": ("vale la pena leer", [])},
    {"english": "it is what a judge is", "sense": "that is simply how a judge works",
     "it": ("è così che funziona un giudice", []),
     "de": ("so funktioniert ein Richter", []),
     "es": ("así funciona un juez", ["es lo que un juez es"])},
    {"english": "you are sampling from it", "sense": "each answer is a sample drawn from a distribution",
     "it": ("stai estraendo dei campioni", ["ne stai campionando"]),
     "de": ("du ziehst Stichproben daraus", []),
     "es": ("estás extrayendo muestras", [])},
    {"english": "it happened to it", "sense": "said of a thing, a project: it occurred in it",
     "it": ("è successo in questo progetto", ["è successo a lui"]),
     "de": ("ist in diesem Projekt passiert", []),
     "es": ("pasó en este proyecto", [])},
    {"english": "most teams", "sense": "the majority of teams, not almost all of them",
     "it": ("la maggior parte dei team", ["quasi tutti i team"]),
     "de": ("die meisten Teams", []),
     "es": ("la mayoría de los equipos", [])},
    {"english": "they deprecate versions", "sense": "they mark versions as outdated, to be withdrawn — not an accounting write-off",
     "it": ("dichiarano obsolete delle versioni", []),
     "de": ("markieren Versionen als veraltet", ["Sie schreiben Versionen ab"]),
     "es": ("marcan versiones como obsoletas", [])},
    {"english": "ToolsCalled holds which tools were called",
     "sense": "an assertion holds the data — it records what happened; it does not check or verify it",
     "it": ("contiene quali strumenti sono stati chiamati", []),
     "de": ("hält fest, welche Tools aufgerufen wurden", ["prüft, welche Tools aufgerufen wurden"]),
     "es": ("contiene qué herramientas se llamaron", [])},
]


def calques(lang: str) -> str:
    """The concepts, in the words of one language."""
    lines = []
    for concept in CONCEPTS:
        right, wrong = concept[lang]
        avoid = "; not " + ", not ".join(f'"{w}"' for w in wrong) if wrong else ""
        lines.append(f'  - "{concept["english"]}" ({concept["sense"]}): "{right}"{avoid}')
    return (f"\n- The same concepts, in every language, have been carried across word for word before. "
            f"In {LANGUAGE_NAMES[lang]}, write them as follows — examples of the rule, not a glossary:\n"
            + "\n".join(lines))


PAGE_SCHEMA = {
    "type": "object",
    "properties": {field: {"type": "string"} for field in ("title", "seo_title", "description", "kicker", "accent", "body")},
    "required": ["title", "seo_title", "description", "kicker", "accent", "body"],
    "additionalProperties": False,
}

CATALOG_SCHEMA = {
    "type": "object",
    "properties": {"entries": {"type": "array", "items": {
        "type": "object",
        "properties": {"key": {"type": "string"}, "text": {"type": "string"},
                       "one": {"type": "string"}, "other": {"type": "string"}},
        "required": ["key", "text", "one", "other"],
        "additionalProperties": False,
    }}},
    "required": ["entries"],
    "additionalProperties": False,
}

MEANING_SCHEMA = {
    "type": "object",
    "properties": {
        "ok": {"type": "boolean"},
        "issues": {"type": "array", "items": {
            "type": "object",
            "properties": {"kind": {"type": "string", "enum": ["negation", "reversed", "added", "omitted", "sense", "other"]},
                           "english": {"type": "string"}, "translation": {"type": "string"},
                           "explanation": {"type": "string"}},
            "required": ["kind", "english", "translation", "explanation"],
            "additionalProperties": False,
        }},
        "notes": {"type": "array", "items": {
            "type": "object",
            "properties": {"english": {"type": "string"}, "translation": {"type": "string"},
                           "suggestion": {"type": "string"}},
            "required": ["english", "translation", "suggestion"],
            "additionalProperties": False,
        }},
    },
    "required": ["ok", "issues", "notes"],
    "additionalProperties": False,
}


def page_prompt(lang: str, meta: dict, body: str, previous: dict | None, diff: str | None,
                problems: list[str] | None, last: dict | None, review: list[dict] | None = None,
                notes: list[dict] | None = None) -> str:
    fields = "\n".join(f"{field}: {meta[field]}" for field in TRANSLATED_FIELDS if meta.get(field))
    parts = [f"""Translate this page into {LANGUAGE_NAMES[lang]}.

Return JSON: "title", "seo_title", "description", "kicker" and "accent" are the front matter values translated — an empty string for any the English does not have; "body" is the Markdown after the front matter, translated. When the English has an "accent", it is a part of the title, and the translated accent must be written exactly as it appears in the translated title.

The English front matter:
{fields}

The English Markdown:
<english>
{body}
</english>"""]
    if previous is not None:
        parts.append(f"""This page was translated before, from an earlier version of the English. Here is that translation, and the diff of the English since then. Change the translation as little as the diff requires: keep every sentence the diff does not touch exactly as it is.

<previous_translation>
{json.dumps(previous, ensure_ascii=False, indent=2)}
</previous_translation>

<english_diff>
{diff or "(no difference in the Markdown: only the description changed)"}
</english_diff>""")
    if review or notes:
        found = []
        if review:
            found.append(f"""These errors of meaning. Correct each so that it says what the English says:
{json.dumps(review, ensure_ascii=False, indent=2)}""")
        if notes:
            found.append(f"""These calques. Rewrite each in idiomatic {LANGUAGE_NAMES[lang]}, keeping its meaning; the suggestion is one way, not the only one:
{json.dumps(notes, ensure_ascii=False, indent=2)}""")
        parts.append(f"""A reviewer read your translation, below, against the English and found what follows. Correct exactly these, and change nothing else.

{chr(10).join(found)}

<last_answer>
{json.dumps(last, ensure_ascii=False, indent=2)}
</last_answer>""")
    if problems:
        parts.append(f"""Your last answer, below, did not pass the site's checks. Correct exactly these problems and change nothing else:
{chr(10).join("- " + p for p in problems)}

<last_answer>
{json.dumps(last, ensure_ascii=False, indent=2)}
</last_answer>""")
    return "\n\n".join(parts)


def catalog_prompt(lang: str, wanted: dict[str, str | dict], known: dict[str, str | dict],
                   problems: list[str] | None, last: dict | None) -> str:
    entries = [{"key": key, **({"one": value["one"], "other": value["other"]} if isinstance(value, dict) else {"text": value})}
               for key, value in wanted.items()]
    parts = [f"""Translate these entries of the site's catalog — the words its templates show — into {LANGUAGE_NAMES[lang]}.

Return JSON {{"entries": [...]}}: one entry for each key below, in the same order, with the same "key". An entry that has "text" in English gets its translation in "text", and "one" and "other" empty; a plural, "one" and "other" in English, gets both forms in {LANGUAGE_NAMES[lang]} ("one" is used when the count is 1), and "text" empty.

- Values are HTML. Keep every placeholder in braces exactly as written — {{count}}, {{Number}}, {{version}} — and every HTML tag. An entity (&rsquo;, &rarr;, &nbsp;) may stay an entity or become its character.
- A line break inside an English value, and the spaces after it, only laid out the template's source: they may be kept or dropped.
- Keys under "numbers" are numbers in words, lower case.

<english_entries>
{json.dumps(entries, ensure_ascii=False, indent=2)}
</english_entries>"""]
    if known:
        parts.append(f"""The entries already translated, for consistency — use the same words for the same things:
<translated_entries>
{json.dumps(known, ensure_ascii=False, indent=2)}
</translated_entries>""")
    if problems:
        parts.append(f"""Your last answer, below, did not pass the checks. Correct exactly these problems and change nothing else:
{chr(10).join("- " + p for p in problems)}

<last_answer>
{json.dumps(last, ensure_ascii=False, indent=2)}
</last_answer>""")
    return "\n\n".join(parts)


def meaning_system(lang: str) -> str:
    return f"""You check a translation of a page of digline.dev from English into {LANGUAGE_NAMES[lang]} for errors of meaning, and nothing else.

An error of meaning is: a negation added, dropped or turned round; a threshold, a comparison, a number's role or a behaviour described the other way round; a claim, a promise or a detail the English does not make; something the English says that the translation leaves out; a word or term translated with a sense it does not have in the English — "deprecate" rendered in German as "abschreiben", which means to write off — is an error of meaning too (kind "sense"), never a note.

Not errors, and never to be reported: style, word choice, register, sentence order; English terms, commands, code and names left in English on purpose; the first person plural of the English rendered as the first person singular or impersonally (that is required); link targets with ../ in front.

Return JSON {{"ok": true, "issues": [], "notes": []}} when there is no error of meaning; otherwise "ok": false and one issue per error, quoting the English and the translation.

Separately, in "notes", list the evident calques: a phrase carried across from English word for word, which a native writer would not write, but whose meaning is right, quoting the translation and suggesting the idiomatic wording. Notes never make "ok" false."""


def meaning_prompt(english: str, translated: str) -> str:
    return f"""<english>
{english}
</english>

<translation>
{translated}
</translation>"""


# ── the repository, and the copy it is checked in ────────────────────────────


def _load(path: str):
    spec = importlib.util.spec_from_file_location(os.path.basename(path).replace("-", "_")[:-3], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Workspace:
    """A local clone of the repository, for its history, with the working tree
    laid over it — and over that the translations of an earlier run."""

    def __init__(self, repo: str, existing: str | None = None, english_only: bool = False):
        self.dir = tempfile.mkdtemp(prefix="translate-")
        self.root = os.path.join(self.dir, "repo")
        subprocess.run(["git", "clone", "-q", "--local", repo, self.root], check=True)
        for name in ("mkdocs.yml", ".lastmod.tsv", ".agents-rule.json", ".operator-facts.json"):
            if os.path.isfile(os.path.join(repo, name)):
                shutil.copy(os.path.join(repo, name), self.root)
        ignore = shutil.ignore_patterns("__pycache__", ".DS_Store")
        for name in ("overrides", "tools", "i18n", "docs"):
            shutil.rmtree(os.path.join(self.root, name), ignore_errors=True)
            shutil.copytree(os.path.join(repo, name), os.path.join(self.root, name), ignore=ignore)
        if english_only:
            # The selftest's copy: as if nothing were translated yet, whatever
            # the repository holds.
            translation.english_only(self.root)
        if existing:
            # Only what the repository does not have: a translation on main (a
            # merged one, perhaps corrected by hand) is never replaced by a run's.
            for lang in languages.LANGUAGES:
                pages = os.path.join(existing, "docs", lang)
                # Every folder down: the Handbook's translations are in handbook/.
                for folder, _, names in os.walk(pages):
                    for name in names:
                        source = os.path.join(folder, name)
                        target = os.path.join(self.root, "docs", lang, os.path.relpath(source, pages))
                        if not os.path.exists(target):
                            os.makedirs(os.path.dirname(target), exist_ok=True)
                            shutil.copy(source, target)
                words = os.path.join(existing, "i18n", f"{lang}.yml")
                target = os.path.join(self.root, "i18n", f"{lang}.yml")
                if os.path.isfile(words) and not catalog_entries(target):
                    shutil.copy(words, target)
        self.checks = _load(os.path.join(self.root, "tools", "check-translations.py"))

    def path(self, *parts: str) -> str:
        return os.path.join(self.root, *parts)

    def build(self) -> list[str]:
        site = self.path("site")
        run = subprocess.run([sys.executable, "-m", "mkdocs", "build", "--strict", "-q", "-f", self.path("mkdocs.yml"),
                              "-d", site], cwd=self.root, capture_output=True, text=True,
                             env=dict(os.environ, MKDOCS_OMITTED_FILES="warn"))
        if run.returncode:
            lines = [line for line in (run.stdout + run.stderr).splitlines() if line.strip() and "│" not in line]
            return ["the site does not build: " + " / ".join(lines[-8:])]
        return []

    def check(self, lang: str, page: str | None) -> list[str]:
        """The build's problems, then check-translations' problems that are
        about this page, or about the language's catalog when page is None."""
        problems = self.build()
        if problems:
            return problems
        found, _, _ = self.checks.check(self.path("site"), self.root)
        mine = []
        for problem in found:
            if page is not None:
                here = (f"docs/{lang}/{page}", languages.page_url(f"{lang}/{page}") + "index.html")
                if problem.startswith(here):
                    mine.append(problem)
            if problem.startswith(f"i18n/{lang}.yml") or problem.startswith("i18n/{"):
                mine.append(problem)
        return mine

    def close(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)


# ── the catalog ──────────────────────────────────────────────────────────────


fixed_section = translation.fixed_section


def catalog_entries(path: str) -> dict[str, str | dict]:
    """A catalog's own words: every entry but the fixed section and source_keys."""
    if not os.path.isfile(path):
        return {}
    return {key: value for key, value in catalog.Catalog(path).entries.items()
            if not key.startswith((catalog.FIXED + ".", translation.KEYS_FIELD + "."))}


def catalog_plan(root: str, lang: str) -> tuple[dict, dict]:
    """(the English entries to translate, the translated entries to keep)."""
    english = catalog_entries(os.path.join(root, "i18n", "en.yml"))
    translated = catalog_entries(os.path.join(root, "i18n", f"{lang}.yml"))
    recorded = translation.catalog_source_keys(root, lang)
    current = translation.catalog_hashes(root)
    wanted = {key: value for key, value in english.items()
              if key not in translated or recorded.get(key) != current[key]}
    kept = {key: value for key, value in translated.items() if key in english and key not in wanted}
    return wanted, kept


def catalog_problems(wanted: dict, data: dict) -> tuple[list[str], dict]:
    """The structural problems of a catalog answer, and its entries."""
    problems, got = [], {}
    for entry in data.get("entries", []):
        key = entry.get("key")
        if key not in wanted:
            problems.append(f"{key!r} was not asked for")
            continue
        english = wanted[key]
        if isinstance(english, dict):
            value = {"one": entry.get("one", ""), "other": entry.get("other", "")}
            forms = [("one", english["one"], value["one"]), ("other", english["other"], value["other"])]
        else:
            value = entry.get("text", "")
            forms = [("text", english, value)]
        for form, source, text in forms:
            if not text.strip():
                problems.append(f"{key}: {form} is empty")
            elif set(re.findall(r"\{[A-Za-z_]+\}", source)) != set(re.findall(r"\{[A-Za-z_]+\}", text)):
                problems.append(f"{key}: {form} has placeholders {sorted(set(re.findall(r'{[A-Za-z_]+}', text)))}, "
                                f"and the English {sorted(set(re.findall(r'{[A-Za-z_]+}', source)))}")
            elif sorted(re.findall(r"</?[a-z][^>]*>", source)) != sorted(re.findall(r"</?[a-z][^>]*>", text)):
                problems.append(f"{key}: {form} does not keep the English HTML tags")
        got[key] = value
    for key in wanted:
        if key not in got:
            problems.append(f"{key}: no translation")
    return problems, got


def write_catalog(root: str, lang: str, entries: dict[str, str | dict], fixed: str) -> str:
    """i18n/<lang>.yml: the words in en.yml's order, source_keys, and the fixed
    section exactly as it was."""
    order = list(catalog_entries(os.path.join(root, "i18n", "en.yml")))
    words = translation.nested({key: entries[key] for key in order if key in entries})
    keys = translation.nested({key: sha for key, sha in translation.catalog_hashes(root).items() if key in entries})
    text = (f"# The words the site writes itself, in {LANGUAGE_NAMES[lang]}.\n#\n"
            "# Translated from i18n/en.yml by tools/translate.py. source_keys records the English\n"
            "# each key was translated from; the format is described at the top of tools/catalog.py.\n\n"
            + yaml.safe_dump(words, allow_unicode=True, sort_keys=False, width=1000)
            + "\n" + yaml.safe_dump({translation.KEYS_FIELD: keys}, sort_keys=False, width=1000)
            + ("\n" + fixed if fixed else ""))
    path = os.path.join(root, "i18n", f"{lang}.yml")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    catalog.Catalog(path)  # a file the site can read, or an error now
    return text


# ── the pages ────────────────────────────────────────────────────────────────


def page_plan(root: str, lang: str, page: str) -> str:
    """"new", "changed" or "unchanged"."""
    path = os.path.join(root, "docs", lang, page)
    if not os.path.isfile(path):
        return "new"
    meta, _ = translation.read_page(path)
    return "unchanged" if meta.get("source_sha") == translation.source_sha(root, page) else "changed"


def english_diff(root: str, page: str, commit: str | None) -> str:
    if not commit:
        return ""
    out = subprocess.run(["git", "-C", root, "diff", "--no-color", "-U2", str(commit), "--", f"docs/{page}"],
                         capture_output=True, text=True)
    return out.stdout if out.returncode == 0 else ""


def page_text(root: str, lang: str, page: str, answer: dict, model: str) -> str:
    english, _ = translation.read_page(os.path.join(root, "docs", page))
    # Only what the English has: a Handbook chapter has no title: (its <h1> is
    # its title) and no template:, and a null one would be written as one.
    meta = {"title": answer["title"] or english.get("title"), "template": english.get("template")}
    meta = {field: value for field, value in meta.items() if value}
    for field in ("seo_title", "kicker", "accent"):
        if english.get(field):
            meta[field] = answer[field]
    meta.update(lang=lang, translation_of=page, description=answer["description"], search={"exclude": True})
    stamped = translation.stamp(meta, root, model=model)
    front = yaml.safe_dump(stamped, allow_unicode=True, sort_keys=False, width=1000)
    return f"---\n{front}---\n\n{translation.relink(answer['body'], page, lang).strip()}\n"


# ── the run ──────────────────────────────────────────────────────────────────


@dataclasses.dataclass
class Outcome:
    lang: str
    subject: str
    status: str                  # translated, unchanged, carried, failed, skipped, stopped
    detail: str = ""
    attempts: int = 0
    problems: list = dataclasses.field(default_factory=list)
    meaning: dict | None = None
    text: str = ""


class Translator:
    def __init__(self, model, ledger: Ledger, workspace: Workspace, check=None):
        self.model = model
        self.ledger = ledger
        self.ws = workspace
        self.check = check or workspace.check
        self.outcomes: list[Outcome] = []

    def ask(self, kind, lang, subject, attempt, system, prompt, schema) -> Reply:
        self.ledger.check()
        reply = self.model.ask(system, prompt, schema)
        self.ledger.record(kind, lang, subject, attempt, reply)
        return reply

    def run(self, langs: list[str], pages: list[str]) -> None:
        for lang in langs:
            try:
                if not self.catalog(lang):
                    for page in pages:
                        self.outcomes.append(Outcome(lang, page, "skipped", "the language's catalog was not written"))
                    continue
                for page in pages:
                    self.page(lang, page)
            except BudgetExceeded as error:
                self.outcomes.append(Outcome(lang, "—", "stopped", f"spending limit: {error}"))
                return

    def catalog(self, lang: str) -> bool:
        root = self.ws.root
        path = os.path.join(root, "i18n", f"{lang}.yml")
        fixed = fixed_section(path)
        wanted, kept = catalog_plan(root, lang)
        subject = f"i18n/{lang}.yml"
        if not wanted:
            self.outcomes.append(Outcome(lang, subject, "unchanged", f"{len(kept)} keys, none behind English"))
            return True
        before = open(path, encoding="utf-8").read() if os.path.isfile(path) else None
        problems, answer = None, None
        system = rules(lang, root)
        for attempt in (1, 2):
            reply = self.ask("catalog", lang, subject, attempt, system,
                             catalog_prompt(lang, wanted, kept, problems, answer), CATALOG_SCHEMA)
            answer = reply.data
            problems, got = catalog_problems(wanted, answer)
            if not problems:
                try:
                    write_catalog(root, lang, {**kept, **got}, fixed)
                    problems = self.check(lang, None)
                except catalog.CatalogError as error:
                    problems = [str(error)]
            if not problems:
                with open(path, encoding="utf-8") as fh:
                    text = fh.read()
                self.outcomes.append(Outcome(lang, subject, "translated",
                                             f"{len(wanted)} keys translated, {len(kept)} kept", attempt, text=text))
                return True
        if before is None:
            os.remove(path) if os.path.exists(path) else None
        else:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(before)
        self.outcomes.append(Outcome(lang, subject, "failed", "not written", 2, problems))
        return before is not None and not catalog_plan(root, lang)[0]

    def meaning(self, lang, subject, english_body, answer) -> dict:
        verdict = self.ask("meaning", lang, subject, 1, meaning_system(lang),
                           meaning_prompt(english_body, answer["body"]), MEANING_SCHEMA).data
        verdict.setdefault("issues", [])
        verdict.setdefault("notes", [])
        return verdict

    def page(self, lang: str, name: str) -> None:
        root = self.ws.root
        page = PAGE_FILES[name]
        path = os.path.join(root, "docs", lang, page)
        state = page_plan(root, lang, page)
        subject = f"docs/{lang}/{page}"
        if state == "unchanged":
            self.outcomes.append(Outcome(lang, subject, "unchanged", "its original has not changed since"))
            return
        english_meta, english_body = translation.read_page(os.path.join(root, "docs", page))
        previous, diff, before = None, None, None
        if state == "changed":
            with open(path, encoding="utf-8") as fh:
                before = fh.read()
            old_meta, old_body = translation.read_page(path)
            previous = {field: str(old_meta.get(field) or "") for field in TRANSLATED_FIELDS}
            previous["body"] = old_body
            diff = english_diff(root, page, old_meta.get("source_commit"))
        system = rules(lang, root)
        problems, answer = None, None
        os.makedirs(os.path.dirname(path), exist_ok=True)
        for attempt in (1, 2):
            reply = self.ask("page", lang, subject, attempt, system,
                             page_prompt(lang, english_meta, english_body, previous, diff, problems, answer),
                             PAGE_SCHEMA)
            answer = reply.data
            text = page_text(root, lang, page, answer, reply.model)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
            problems = self.check(lang, page)
            if not problems:
                outcome = Outcome(lang, subject, "translated", state, attempt, text=text)
                verdict = self.meaning(lang, subject, english_body, answer)
                if not _meaning_ok(verdict) or verdict.get("notes"):
                    # One round of correction, with the errors and the calques;
                    # checked and read again. What fails the checks is not kept.
                    reply = self.ask("correction", lang, subject, 1, system,
                                     page_prompt(lang, english_meta, english_body, previous, diff, None, answer,
                                                 review=verdict.get("issues"), notes=verdict.get("notes")),
                                     PAGE_SCHEMA)
                    corrected = page_text(root, lang, page, reply.data, reply.model)
                    with open(path, "w", encoding="utf-8") as fh:
                        fh.write(corrected)
                    after = self.check(lang, page)
                    if after:
                        with open(path, "w", encoding="utf-8") as fh:
                            fh.write(text)
                        outcome.detail += "; its correction failed the checks and was not kept: " + "; ".join(after)[:300]
                    else:
                        outcome.text = corrected
                        # What the second reading finds is what stays: the notes
                        # of the first were corrected.
                        verdict = self.meaning(lang, subject, english_body, reply.data)
                        outcome.detail += "; corrected once"
                outcome.meaning = verdict
                self.outcomes.append(outcome)
                return
        if before is None:
            os.remove(path)
        else:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(before)
        self.outcomes.append(Outcome(lang, subject, "failed", "not written", 2, problems))


def _meaning_ok(verdict: dict) -> bool:
    return bool(verdict.get("ok")) and not verdict.get("issues")


# ── the estimate ─────────────────────────────────────────────────────────────

# Tokens per character, and output per input, from the first run on
CHARS_PER_TOKEN = 3.2

# What a page costs, per call, in tokens, as a line in the tokens of its English
# (after the front matter, CHARS_PER_TOKEN characters each), and how many of
# each call a page takes. Measured on ESTIMATE_MEASURED from ESTIMATE_SOURCE, by
# least squares over every call of the run; the reading's output is the mean,
# since its slope was noise. tools/testdata/estimate/ keeps the pages and what
# each cost, and the selftest holds these constants to them.
#
# Two things they do not know. They were fitted on Handbook pages, where the
# reading found a calque on nearly every page and so nearly every page was
# corrected once (CORRECTIONS_PER_PAGE); the presentation pages have been
# corrected less, so on them this expects more than a run spends. And the
# catalog is estimated as before, from 2026-09-17 (the Italian catalog):
# 1.65 output tokens per token of English, twice that at most.
ESTIMATE_MEASURED = "2026-09-19"
ESTIMATE_SOURCE = ("run 35451029899, the Handbook's nine pages in it, de and es — 27 pages, 58,928 English "
                   "tokens, 101 calls, 14.77 USD")
TRANSLATION_IN = (1.67, 944)       # (per token of English, and a constant)
TRANSLATION_OUT = (3.41, 1906)     # thinking included
CORRECTION_IN = (2.64, 2149)       # the English, the last answer and the reviewer's notes
CORRECTION_OUT = (1.58, 154)
READING_IN = (2.54, 997)
READING_OUT = (0.0, 1855)
TRANSLATIONS_PER_PAGE = 1.15       # a second attempt after failed checks, on 15 pages in 100
READINGS_PER_PAGE = 1.70           # one, and one more after each correction
CORRECTIONS_PER_PAGE = 0.81
# The most a single call cost against its line, per kind, rounded up: a
# reading's thinking varies most. The most a page can cost takes each call at
# that.
TRANSLATION_MOST, CORRECTION_MOST, READING_MOST = 1.3, 1.2, 1.7
CATALOG_OUT_PER_TOKEN = 1.65


def _call(tokens: float, into: tuple[float, float], out: tuple[float, float]) -> float:
    """What one call costs in USD, for a page of `tokens` English tokens."""
    price_in, price_out = PRICES[MODEL]
    return ((into[0] * tokens + into[1]) * price_in + (out[0] * tokens + out[1]) * price_out) / 1e6


def page_estimate(tokens: float) -> tuple[float, float]:
    """(expected, most) for one page: expected, each call as often as a page
    took it on ESTIMATE_MEASURED; most, the longest path the run can take — two
    translations (the second after failed checks), one correction and a reading
    after each — every call at the most one of its kind cost."""
    translation_ = _call(tokens, TRANSLATION_IN, TRANSLATION_OUT)
    correction = _call(tokens, CORRECTION_IN, CORRECTION_OUT)
    reading = _call(tokens, READING_IN, READING_OUT)
    expected = (TRANSLATIONS_PER_PAGE * translation_ + CORRECTIONS_PER_PAGE * correction
                + READINGS_PER_PAGE * reading)
    most = (2 * TRANSLATION_MOST * translation_ + CORRECTION_MOST * correction
            + 2 * READING_MOST * reading)
    return expected, most


def estimate(root: str, langs: list[str], pages: list[str]) -> tuple[float, float]:
    """(the expected cost in USD, the most it could cost on the longest path),
    from what the plan would translate."""
    price_in, price_out = PRICES[MODEL]
    expected = worst = 0.0
    for lang in langs:
        wanted, _ = catalog_plan(root, lang)
        if wanted:
            tokens = len(json.dumps(wanted, ensure_ascii=False)) / CHARS_PER_TOKEN
            cost = ((tokens + 1500) * price_in + CATALOG_OUT_PER_TOKEN * tokens * price_out) / 1e6
            expected += cost
            worst += 2 * cost
        for name in pages:
            page = PAGE_FILES[name]
            if page_plan(root, lang, page) == "unchanged":
                continue
            _, body = translation.read_page(os.path.join(root, "docs", page))
            one, most = page_estimate(len(body) / CHARS_PER_TOKEN)
            expected += one
            worst += most
    return expected, worst


# ── the report ───────────────────────────────────────────────────────────────


def needs_attention(outcome: "Outcome") -> bool:
    return outcome.meaning is not None and not _meaning_ok(outcome.meaning)


def report(translator: Translator, langs, pages, dry_run: bool, started: str,
           estimated: tuple[float, float] | None = None, texts: bool = True) -> str:
    """The run in Markdown; without the texts, it is the bot's pull request body."""
    ledger = translator.ledger
    lines = [f"# Translation run, {started}", "",
             f"- Mode: {'dry run — nothing written to docs/ or i18n/' if dry_run else 'writing to docs/ and i18n/'}",
             f"- Languages: {', '.join(langs)}; pages: {', '.join(pages)}",
             f"- Model: {MODEL}; prices {', '.join(f'{m} ${p[0]:g}/${p[1]:g} per MTok in/out' for m, p in PRICES.items())} "
             f"(Anthropic's pricing page, read {PRICES_READ})",
             f"- Spent: **{ledger.spent:.4f} USD** of a {ledger.cap:.2f} USD limit, in {len(ledger.calls)} call(s); "
             f"{sum(c.input_tokens for c in ledger.calls)} input and {sum(c.output_tokens for c in ledger.calls)} output tokens"]
    if estimated:
        lines.append(f"- Estimated before the run: {estimated[0]:.2f} USD, at most {estimated[1]:.2f} on the longest path")
    lines += ["", "## Outcomes", "", "| Language | What | Status | Attempts | Checks | Meaning |", "|---|---|---|---|---|---|"]
    attention = []
    for o in translator.outcomes:
        meaning = "—"
        if o.meaning is not None:
            meaning = "**needs attention**" if needs_attention(o) else (
                "ok after a correction" if "corrected once" in o.detail else "ok")
            if needs_attention(o):
                attention.append(o)
        checks = "passed" if o.status == "translated" else ("failed: " + "; ".join(o.problems)[:300] if o.problems else "—")
        detail = f"{o.status}" + (f" ({o.detail})" if o.detail else "")
        lines.append(f"| {o.lang} | `{o.subject}` | {detail} | {o.attempts or '—'} | {checks} | {meaning} |")
    if attention:
        lines += ["", "## Needs attention", ""]
        for o in attention:
            lines.append(f"### `{o.subject}`")
            for issue in o.meaning.get("issues", []):
                lines.append(f"- **{issue['kind']}**: {issue['explanation']}\n  - English: {issue['english']}\n"
                             f"  - Translation: {issue['translation']}")
    noted = [o for o in translator.outcomes if o.meaning and o.meaning.get("notes")]
    if noted:
        lines += ["", "## Calques noted (not blocking)", ""]
        for o in noted:
            lines.append(f"### `{o.subject}`")
            for note in o.meaning["notes"]:
                lines.append(f"- {note['translation']} → {note['suggestion']}  \n  English: {note['english']}")
    lines += ["", "## Calls", "", "| Kind | Language | What | Attempt | Model | Input tokens | Output tokens | Cost (USD) |",
              "|---|---|---|---|---|---|---|---|"]
    for c in ledger.calls:
        lines.append(f"| {c.kind} | {c.lang} | `{c.subject}` | {c.attempt} | {c.model} | {c.input_tokens} | "
                     f"{c.output_tokens} | {c.cost:.4f} |")
    written = [o for o in translator.outcomes if o.status == "translated" and o.text] if texts else []
    if written:
        lines += ["", "## Texts", ""]
        for o in written:
            lines += [f"<details><summary><code>{o.subject}</code></summary>", "", "````markdown" if o.subject.endswith(".md") else "````yaml",
                      o.text.rstrip("\n"), "````", "", "</details>", ""]
    return "\n".join(lines) + "\n"


def plan(root: str, langs: list[str], pages: list[str]) -> dict:
    """What a run would translate, without a call: each language's catalog keys
    behind English, and its pages new or changed. "work" is false when there is
    nothing, and translate.yml then starts no run."""
    catalogs, changed = {}, {}
    for lang in langs:
        wanted, _ = catalog_plan(root, lang)
        if wanted:
            catalogs[lang] = len(wanted)
        todo = [name for name in pages if page_plan(root, lang, PAGE_FILES[name]) != "unchanged"]
        if todo:
            changed[lang] = todo
    return {"work": bool(catalogs or changed), "catalogs": catalogs, "pages": changed}


def summary(root: str, langs: list[str] = list(languages.LANGUAGES)) -> str:
    """The Handbook's translations, one Markdown line per language: how many of
    its pages are translated, and how many of those are behind the English."""
    names = PAGE_GROUPS["handbook"]
    lines = []
    for lang in langs:
        states = [page_plan(root, lang, PAGE_FILES[name]) for name in names]
        translated = sum(state != "new" for state in states)
        behind = [name for name, state in zip(names, states) if state == "changed"]
        line = f"- Handbook, {lang}: {translated} of {len(names)} page(s) translated"
        if translated:
            line += f", {len(behind)} behind the English" + (f" ({', '.join(behind)})" if behind else "")
        lines.append(line)
    return "\n".join(lines) + "\n"


def write_out(translator: Translator, out: str) -> None:
    """Every translation the copy now holds, for the languages run: what this
    run translated and what it carried over unchanged."""
    root = translator.ws.root
    for lang in {o.lang for o in translator.outcomes}:
        folder = os.path.join(root, "docs", lang)
        if os.path.isdir(folder):
            shutil.copytree(folder, os.path.join(out, "docs", lang), dirs_exist_ok=True)
        words = os.path.join(root, "i18n", f"{lang}.yml")
        if os.path.isfile(words) and catalog_entries(words):
            os.makedirs(os.path.join(out, "i18n"), exist_ok=True)
            shutil.copy(words, os.path.join(out, "i18n", f"{lang}.yml"))


def expand_pages(text: str) -> list[str]:
    """--pages as the page names it stands for: each name, and each group's
    pages in its place, once each, in the order asked."""
    out: list[str] = []
    for name in (part.strip() for part in text.split(",")):
        for page in PAGE_GROUPS.get(name, [name] if name else []):
            if page not in out:
                out.append(page)
    return out


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--langs", default=",".join(languages.LANGUAGES))
    parser.add_argument("--pages", default=",".join(DEFAULT_PAGES))
    parser.add_argument("--out")
    parser.add_argument("--plan", action="store_true",
                        help="print what would be translated, as JSON, and call nothing")
    parser.add_argument("--summary", action="store_true",
                        help="print the Handbook's translations and how many are behind the English, and call nothing")
    parser.add_argument("--existing")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-cost", type=float, default=DEFAULT_MAX_COST)
    args = parser.parse_args(argv)
    langs = [lang.strip() for lang in args.langs.split(",") if lang.strip()]
    pages = expand_pages(args.pages)
    wrong = [lang for lang in langs if lang not in languages.LANGUAGES] + [p for p in pages if p not in PAGE_FILES]
    if wrong:
        parser.error(f"not a language or a page: {', '.join(wrong)}")
    if args.plan:
        print(json.dumps(plan(ROOT, langs, pages)))
        return 0
    if args.summary:
        print(summary(ROOT, langs), end="")
        return 0
    if not args.out:
        parser.error("--out is required, except with --plan")
    started = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    workspace = Workspace(ROOT, args.existing)
    estimated = estimate(workspace.root, langs, pages)
    print(f"translate: estimated cost {estimated[0]:.2f} USD, at most {estimated[1]:.2f} on the longest path "
          f"(ESTIMATE_MEASURED {ESTIMATE_MEASURED}); the limit is {args.max_cost:.2f} USD", flush=True)
    translator = Translator(Claude(FederatedToken()), Ledger(args.max_cost), workspace)
    try:
        translator.run(langs, pages)
        os.makedirs(args.out, exist_ok=True)
        write_out(translator, args.out)
        if not args.dry_run:
            # The translations into the repository, for the bot's pull request.
            write_out(translator, ROOT)
        text = report(translator, langs, pages, args.dry_run, started, estimated)
        with open(os.path.join(args.out, "report.md"), "w", encoding="utf-8") as fh:
            fh.write(text)
        with open(os.path.join(args.out, "pr-body.md"), "w", encoding="utf-8") as fh:
            fh.write(report(translator, langs, pages, args.dry_run, started, estimated, texts=False)
                     + "\n🤖 Opened by tools/translate.py (.github/workflows/translate.yml).\n")
        with open(os.path.join(args.out, "calls.json"), "w", encoding="utf-8") as fh:
            json.dump([dataclasses.asdict(c) for c in translator.ledger.calls], fh, indent=2)
        print(text)
    finally:
        workspace.close()
    failed = [o for o in translator.outcomes if o.status in ("failed", "stopped")]
    with open(os.path.join(args.out, "summary.json"), "w", encoding="utf-8") as fh:
        json.dump({"failed": len(failed), "needs_attention": sum(needs_attention(o) for o in translator.outcomes),
                   "translated": sum(o.status == "translated" for o in translator.outcomes),
                   "spent": round(translator.ledger.spent, 4)}, fh)
    return 1 if failed else 0


# ── the selftest ─────────────────────────────────────────────────────────────


class FakeModel:
    """Answers from a function of (system, prompt, schema), with the usage it is given."""

    def __init__(self, answer, input_tokens=1000, output_tokens=500, model=MODEL):
        self.answer = answer
        self.usage = (input_tokens, output_tokens)
        self.model = model
        self.prompts: list[tuple[str, str]] = []

    def ask(self, system, prompt, schema):
        self.prompts.append((system, prompt))
        return Reply(self.answer(system, prompt, schema), self.model, *self.usage)


def _english_entries(prompt: str) -> list[dict]:
    block = re.search(r"<english_entries>\n(.*?)\n</english_entries>", prompt, re.S).group(1)
    return json.loads(block)


def _fake_answer(root: str, lang: str, meaning_ok=True):
    """A fake model that translates the way the fixtures do: the catalog as it
    is, a page pseudo-translated, and a meaning check that says what it is told
    — True (ok), False (an error and a calque) or "notes" (ok, with a calque),
    or a list of those, one reading after another."""
    readings = list(meaning_ok) if isinstance(meaning_ok, (list, tuple)) else None

    def answer(system, prompt, schema):
        if schema is CATALOG_SCHEMA:
            return {"entries": [{"key": e["key"], "text": e.get("text", ""), "one": e.get("one", ""),
                                 "other": e.get("other", "")} for e in _english_entries(prompt)]}
        if schema is PAGE_SCHEMA:
            body = re.search(r"<english>\n(.*?)\n</english>", prompt, re.S).group(1)
            meta = dict(re.findall(r"^(title|seo_title|description|kicker|accent): (.*)$",
                                   prompt.split("<english>")[0], re.M))
            corrected = "\n\nCorrected." if "A reviewer read your translation" in prompt else ""
            return {field: meta.get(field, "") for field in TRANSLATED_FIELDS} | {
                "body": translation.pseudo_translate(body, lang, root) + corrected}
        said = readings.pop(0) if readings is not None else meaning_ok
        ok = said is not False
        return {"ok": ok, "issues": [] if ok else [
            {"kind": "negation", "english": "does not", "translation": "does", "explanation": "a negation dropped"}],
                "notes": [] if said is True else [{"english": "is not yours to show", "translation": "non è tuo da mostrare",
                                                   "suggestion": "non puoi mostrarlo tu"}]}
    return answer


def selftest() -> int:
    failures: list[str] = []

    def expect(label, actual, wanted):
        if actual != wanted:
            failures.append(f"{label}: got {actual!r}, wanted {wanted!r}")
        else:
            print(f"translate selftest: {label}")

    if not os.path.isfile(os.path.join(ROOT, "docs", "product", "guide.md")):
        print("translate selftest: docs/product/ is not synced; run `make docs` first.", file=sys.stderr)
        return 1

    # 1. The prompts.
    system = rules("de", ROOT)
    expect("the rules: the address, the voice, the decimal point, the glossary, the names, the forbidden words",
           all(s in system for s in ('the informal "du"', '"wir"', "0.88, never 0,88", "noise floor", "digline compare",
                                     "LangChain", "digline-openai", "Basislinie")), True)
    expect("the rules: idiomatic, no calques, quantifiers at their strength, Italian examples",
           ("never a calque" in rules("es", ROOT), '"most" is the majority' in rules("de", ROOT),
            "non puoi mostrarlo tu" in rules("it", ROOT), "non puoi mostrarlo tu" in rules("de", ROOT)),
           (True, True, True, False))
    expect("the concepts: every one in every language, the English and its wording",
           [(c["english"], lang) for c in CONCEPTS for lang in languages.LANGUAGES
            if not (isinstance(c.get(lang), tuple) and c[lang][0] and f'"{c[lang][0]}"' in rules(lang, ROOT)
                    and f'"{c["english"]}"' in rules(lang, ROOT) and c["sense"] in rules(lang, ROOT))], [])
    expect("holds is not checks: the assertion records, in each language's words",
           ('"contiene quali strumenti sono stati chiamati"' in rules("it", ROOT),
            '"hält fest, welche Tools aufgerufen wurden"' in rules("de", ROOT),
            '"prüft, welche Tools aufgerufen wurden"' in rules("de", ROOT),
            '"contiene qué herramientas se llamaron"' in rules("es", ROOT),
            "hält fest" in rules("es", ROOT)), (True, True, True, True, False))
    expect("the concepts in each language's words: below the line, not yours to show, worth reading, what a judge is",
           ([w in rules("it", ROOT) for w in ('"sotto soglia"', '"non puoi mostrarlo tu"', '"vale la pena leggere"',
                                               '"è così che funziona un giudice"')],
            [w in rules("de", ROOT) for w in ('"unter dem Schwellenwert"', '"kannst du nicht vorzeigen"', '"lesenswert"',
                                               '"so funktioniert ein Richter"', '"Sie schreiben Versionen ab"')],
            [w in rules("es", ROOT) for w in ('"por debajo del umbral"', '"no puedes mostrarlo"', '"vale la pena leer"',
                                               '"así funciona un juez"', '"no es tuyo para mostrarlo"')]),
           ([True] * 4, [True] * 5, [True] * 5))
    expect("each language gets its own words only",
           ("no es tuyo" in rules("it", ROOT), "sotto soglia" in rules("de", ROOT), "lesenswert" in rules("es", ROOT)),
           (False, False, False))
    expect("the reading of meaning: a term in another sense is an error, never a note",
           ('"abschreiben"' in meaning_system("de"), 'kind "sense"' in meaning_system("it"),
            "sense" in MEANING_SCHEMA["properties"]["issues"]["items"]["properties"]["kind"]["enum"]), (True, True, True))
    expect("the rules: a kept term stays English as digline's noun, and is translated as a verb or an everyday word",
           ("as a noun for that concept" in system, '"check your inputs"' in system, "translate it" in system,
            "wherever the English uses them" in system), (True, True, True, False))
    expect("the page names: the six by their old names, the Handbook by path, a group expanded once, in order",
           (DEFAULT_PAGES, PAGE_FILES["index"], PAGE_FILES["handbook/index"],
            expand_pages("why, handbook,handbook/02-cases,why"), expand_pages("")),
           (["index", "start", "why", "about", "contact", "agents"], "index.md", "handbook/index.md",
            ["why"] + PAGE_GROUPS["handbook"], []))
    expect("the page names: no bare folder, no page the site does not translate",
           [name in PAGE_FILES for name in ("handbook", "handbook/", "handbook/99-x", "product/guide")],
           [False, False, False, False])
    expect("the rules in Italian address the reader with tu, and never noi",
           ('the informal "tu"' in rules("it", ROOT), '"noi"' in rules("it", ROOT)), (True, True))
    english_meta, english_body = translation.read_page(os.path.join(ROOT, "docs", "why.md"))
    first = page_prompt("it", english_meta, english_body, None, None, None, None)
    update = page_prompt("it", english_meta, english_body, {"title": "Perché", "body": "Vecchio."}, "-old\n+new", None, None)
    retry = page_prompt("it", english_meta, english_body, None, None, ["code 3 is 'x'"], {"body": "B"})
    expect("a new page's prompt: the English front matter and body, and no previous translation",
           (english_body in first, "title: Why" in first, "<previous_translation>" in first), (True, True, False))
    expect("a changed page's prompt: the previous translation, the English diff, the smallest change",
           ("Vecchio." in update, "-old\n+new" in update, "as little as the diff requires" in update), (True, True, True))
    expect("a second attempt's prompt: the problems and the last answer", ("- code 3 is 'x'" in retry, '"body": "B"' in retry),
           (True, True))

    # 2. The token: one exchange while it is fresh, another near its end.
    clock = [1000.0]
    calls = []

    def http(method, url, headers, body=None):
        calls.append(url)
        if method == "GET":
            return {"value": f"jwt-{len(calls)}"}
        return {"access_token": f"sk-ant-oat01-{len(calls)}", "expires_in": 600}

    env = {"ACTIONS_ID_TOKEN_REQUEST_URL": "https://gh.invalid/token?x=1", "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "t",
           "ANTHROPIC_FEDERATION_RULE_ID": "fdrl_x", "ANTHROPIC_ORGANIZATION_ID": "o", "ANTHROPIC_SERVICE_ACCOUNT_ID": "svac_x"}
    tokens = FederatedToken(env, clock=lambda: clock[0], http=http)
    a = tokens.token(); clock[0] += 400; b = tokens.token(); clock[0] += 100; c = tokens.token()
    expect("the token: kept while more than two minutes are left, exchanged again after",
           (a == b, b != c, tokens.exchanges), (True, True, 2))

    # 3. The catalog's plan and file: the fixed section is never asked for, and comes back as it was.
    workspace = Workspace(ROOT, english_only=True)
    try:
        root = workspace.root
        fixed_before = fixed_section(os.path.join(root, "i18n", "it.yml"))
        wanted, kept = catalog_plan(root, "it")
        expect("a catalog with no words yet: every English key asked for, no fixed key, no source key",
               (len(wanted) == len(catalog_entries(os.path.join(root, "i18n", "en.yml"))), kept,
                any(k.startswith(("do_not_translate", "source_keys")) for k in wanted)), (True, {}, False))
        fake = FakeModel(_fake_answer(root, "it"))
        translator = Translator(fake, Ledger(5.0), workspace, check=lambda lang, page: [])
        expect("the catalog written", translator.catalog("it"), True)
        expect("the catalog's prompt never carries the fixed words",
               "Tradotto dall'inglese" in fake.prompts[0][1] or "do_not_translate" in fake.prompts[0][1], False)
        expect("the fixed section comes back exactly as it was", fixed_section(os.path.join(root, "i18n", "it.yml")),
               fixed_before)
        expect("the fixed words still the approved ones",
               translation.fixed_digest(root) == workspace.checks.FIXED_TEXTS_DIGEST, True)
        expect("a catalog up to date asks for nothing", catalog_plan(root, "it")[0], {})
        with open(os.path.join(root, "i18n", "en.yml"), encoding="utf-8") as fh:
            en = fh.read()
        with open(os.path.join(root, "i18n", "en.yml"), "w", encoding="utf-8") as fh:
            fh.write(en.replace('lede: "The guide needs no key."', 'lede: "The guide needs no API key."'))
        expect("one English value changed: that key alone asked for", list(catalog_plan(root, "it")[0]), ["closing.lede"])
        with open(os.path.join(root, "i18n", "en.yml"), "w", encoding="utf-8") as fh:
            fh.write(en)
        bad = FakeModel(lambda s, p, sc: {"entries": [{"key": "closing.lede", "text": "senza {placeholder}", "one": "", "other": ""}]})
        expect("a catalog answer with a placeholder the English lacks is refused",
               catalog_problems({"closing.lede": "The guide needs no key."}, bad.answer("", "", CATALOG_SCHEMA))[0][0],
               "closing.lede: text has placeholders ['{placeholder}'], and the English []")

        # 4. The second attempt, and the page left unwritten after two failures.
        attempts = []

        def check_twice(lang, page):
            attempts.append(page)
            return ["code 1 is 'x', and the original's is 'y'"] if len(attempts) == 1 else []

        fake = FakeModel(_fake_answer(root, "it"))
        translator = Translator(fake, Ledger(5.0), workspace, check=check_twice)
        translator.page("it", "about")
        outcome = translator.outcomes[-1]
        expect("a page failing its checks once: asked again with the problem, then kept",
               (outcome.status, outcome.attempts, "code 1 is 'x'" in fake.prompts[1][1], outcome.meaning["ok"]),
               ("translated", 2, True, True))
        expect("a page translated and unchanged since: skipped, no call",
               (page_plan(root, "it", "about.md"), len(fake.prompts)), ("unchanged", 3))
        translator.page("it", "about")
        expect("the skip costs nothing", (translator.outcomes[-1].status, len(fake.prompts)), ("unchanged", 3))
        fake = FakeModel(_fake_answer(root, "it"))
        translator = Translator(fake, Ledger(5.0), workspace, check=lambda lang, page: ["heading 2 is 'h3'"])
        translator.page("it", "contact")
        expect("a page failing its checks twice: not written, and said",
               (translator.outcomes[-1].status, translator.outcomes[-1].attempts,
                os.path.exists(os.path.join(root, "docs", "it", "contact.md"))), ("failed", 2, False))

        # 5. The spending limit.
        fake = FakeModel(_fake_answer(root, "it"), input_tokens=400_000, output_tokens=200_000)
        ledger = Ledger(5.0)
        translator = Translator(fake, ledger, workspace, check=lambda lang, page: [])
        translator.run(["it"], ["start", "why"])
        statuses = [(o.subject, o.status) for o in translator.outcomes]
        expect("the spending limit: the call past it is not made, and the run stops",
               (statuses[-1][1], len(ledger.calls), round(ledger.spent, 2)), ("stopped", 1, 7.0))

        # 6. The report.
        fake = FakeModel(_fake_answer(root, "it", meaning_ok=False))
        translator = Translator(fake, Ledger(5.0), workspace, check=lambda lang, page: [])
        translator.page("it", "contact")
        expect("an error of meaning that stays: corrected once, read again, still needs attention",
               ([c.kind for c in translator.ledger.calls], needs_attention(translator.outcomes[-1]),
                "a negation dropped" in fake.prompts[2][1]),
               (["page", "meaning", "correction", "meaning"], True, True))
        text = report(translator, ["it"], ["contact"], True, "2026-09-17 12:00 UTC", (0.5, 1.2))
        wanted = ("| it | `docs/it/contact.md` | translated (new; corrected once) | 1 | passed | **needs attention** |",
                  "## Needs attention", "a negation dropped", "## Calques noted (not blocking)",
                  "non è tuo da mostrare → non puoi mostrarlo tu",
                  "| page | it | `docs/it/contact.md` | 1 | claude-opus-5 | 1000 | 500 | 0.0175 |",
                  "| correction | it | `docs/it/contact.md` | 1 |", "Spent: **0.0700 USD**",
                  "Estimated before the run: 0.50 USD, at most 1.20", "## Texts", "<code>docs/it/contact.md</code>")
        expect("the report: outcome, needs attention, calques, calls, cost, estimate, the text",
               [w for w in wanted if w not in text], [])
        body = report(translator, ["it"], ["contact"], False, "2026-09-17 12:00 UTC", (0.5, 1.2), texts=False)
        expect("the pull request's body: the same report without the texts",
               ("## Texts" in body, "## Needs attention" in body, "writing to docs/ and i18n/" in body), (False, True, True))

        # The correction that works: an error of meaning found, corrected, read again, ok.
        os.remove(os.path.join(root, "docs", "it", "contact.md"))
        fake = FakeModel(_fake_answer(root, "it", meaning_ok=[False, True]))
        translator = Translator(fake, Ledger(5.0), workspace, check=lambda lang, page: [])
        translator.page("it", "contact")
        text = report(translator, ["it"], ["contact"], True, "2026-09-17 12:00 UTC")
        expect("an error of meaning corrected: ok after a correction, not needing attention",
               (needs_attention(translator.outcomes[-1]), "ok after a correction" in text), (False, True))

        # Calques alone start a correction too, with the notes as its context.
        os.remove(os.path.join(root, "docs", "it", "contact.md"))
        fake = FakeModel(_fake_answer(root, "it", meaning_ok=["notes", True]))
        translator = Translator(fake, Ledger(5.0), workspace, check=lambda lang, page: [])
        translator.page("it", "contact")
        text = report(translator, ["it"], ["contact"], True, "2026-09-17 12:00 UTC")
        expect("calques alone: corrected once with the notes, read again, nothing left to note",
               ([c.kind for c in translator.ledger.calls], "non puoi mostrarlo tu" in fake.prompts[2][1],
                "These errors of meaning" in fake.prompts[2][1], needs_attention(translator.outcomes[-1]),
                "## Calques noted" in text), (["page", "meaning", "correction", "meaning"], True, False, False, False))

        os.remove(os.path.join(root, "docs", "it", "contact.md"))
        fake = FakeModel(_fake_answer(root, "it", meaning_ok=["notes", "notes"]))
        translator = Translator(fake, Ledger(5.0), workspace, check=lambda lang, page: [])
        translator.page("it", "contact")
        text = report(translator, ["it"], ["contact"], True, "2026-09-17 12:00 UTC")
        expect("calques that stay after the correction: noted, never needing attention",
               (needs_attention(translator.outcomes[-1]), "## Calques noted (not blocking)" in text,
                "## Needs attention" in text), (False, True, False))

        os.remove(os.path.join(root, "docs", "it", "contact.md"))
        fake = FakeModel(_fake_answer(root, "it", meaning_ok=True))
        translator = Translator(fake, Ledger(5.0), workspace, check=lambda lang, page: [])
        translator.page("it", "contact")
        expect("nothing found: no correction", [c.kind for c in translator.ledger.calls], ["page", "meaning"])

        # The correction that fails the checks is not kept.
        os.remove(os.path.join(root, "docs", "it", "contact.md"))
        checks = iter([[], ["structure — block 3 is 'p', and the original's is 'li'"]])
        fake = FakeModel(_fake_answer(root, "it", meaning_ok=False))
        translator = Translator(fake, Ledger(5.0), workspace, check=lambda lang, page: next(checks))
        translator.page("it", "contact")
        first_text = translator.outcomes[-1].text
        with open(os.path.join(root, "docs", "it", "contact.md"), encoding="utf-8") as fh:
            on_disk = fh.read()
        expect("a correction failing the checks: not kept, the checked translation stays, needs attention",
               (on_disk == first_text and "Corrected." not in on_disk, needs_attention(translator.outcomes[-1]),
                "its correction failed the checks" in translator.outcomes[-1].detail), (True, True, True))

        # The estimate, and a run's output never replacing what the repository has.
        expected, worst = estimate(root, ["it"], ["start", "why"])
        expect("the estimate: something to pay for pages to translate, more at most", (0 < expected < worst), True)
        expect("the estimate: nothing for what is up to date", estimate(root, ["it"], ["about"]), (0.0, 0.0))
        # The constants against what they were measured on: the pages of
        # ESTIMATE_SOURCE, each with its English tokens and what it cost.
        with open(os.path.join(TOOLS, "testdata", "estimate", "handbook-2026-09-19.json"), encoding="utf-8") as fh:
            measured = json.load(fh)
        spent = sum(p["cost"] for p in measured["pages"])
        foreseen = sum(page_estimate(p["tokens"])[0] for p in measured["pages"])
        most = [(p["page"], p["lang"]) for p in measured["pages"] if p["cost"] > page_estimate(p["tokens"])[1]]
        per_lang = {lang: (sum(p["cost"] for p in measured["pages"] if p["lang"] == lang),
                           sum(page_estimate(p["tokens"])[0] for p in measured["pages"] if p["lang"] == lang))
                    for lang in ("it", "de", "es")}
        expect("the estimate against the run it was measured on: within 10% in all, and in each language",
               (len(measured["pages"]), abs(foreseen - spent) / spent < 0.10,
                all(abs(f - s) / s < 0.15 for s, f in per_lang.values())), (27, True, True))
        expect("no page of that run cost more than its most", most, [])
        # The other half: the same test, on an estimate that counts no
        # correction — one translation and one reading a page, as it did until
        # ESTIMATE_MEASURED — refuses it.
        uncorrected = sum(_call(p["tokens"], TRANSLATION_IN, TRANSLATION_OUT) + _call(p["tokens"], READING_IN, READING_OUT)
                          for p in measured["pages"])
        expect("an estimate with no correction in it is not within 10% of that run",
               abs(uncorrected - spent) / spent < 0.10, False)
    finally:
        workspace.close()

    # 7. The real thing, without the network: the Italian catalog and Why, built and checked.
    workspace = Workspace(ROOT, english_only=True)
    try:
        first = plan(workspace.root, ["it"], ["why"])
        expect("the plan before any translation: every catalog key, and Why",
               (first["work"], first["catalogs"].get("it") == len(catalog_entries(workspace.path("i18n", "en.yml"))),
                first["pages"]), (True, True, {"it": ["why"]}))
        fake = FakeModel(_fake_answer(workspace.root, "it"))
        translator = Translator(fake, Ledger(5.0), workspace)
        translator.run(["it"], ["why", "handbook/03-ground-truth"])
        expect("built and checked for real: the catalog, Why and a Handbook chapter translated at the first attempt",
               [(o.subject, o.status, o.attempts) for o in translator.outcomes],
               [("i18n/it.yml", "translated", 1), ("docs/it/why.md", "translated", 1),
                ("docs/it/handbook/03-ground-truth.md", "translated", 1)])
        chapter_meta, chapter = translation.read_page(workspace.path("docs", "it", "handbook", "03-ground-truth.md"))
        expect("the chapter as written: its links from one folder deeper, no title: or template: it has not got",
               ("](../../blog/bad-evals-my-own.md)" in chapter, "](../blog/" in chapter.replace("](../../", ""),
                "title" in chapter_meta, "template" in chapter_meta, chapter_meta["translation_of"]),
               (True, False, False, False, "handbook/03-ground-truth.md"))
        # The same checks refuse what they must: a number changed, twice.
        comma = _fake_answer(workspace.root, "it")
        wrong = FakeModel(lambda system, prompt, schema: (
            {**comma(system, prompt, schema), "body": comma(system, prompt, schema)["body"].replace("0.88", "0.89")}
            if schema is PAGE_SCHEMA else comma(system, prompt, schema)))
        refused = Translator(wrong, Ledger(5.0), workspace)
        refused.page("it", "start")
        outcome = refused.outcomes[-1]
        expect("built and checked for real: 0.89 for 0.88 refused twice, the page not written",
               (outcome.status, outcome.attempts, any("numbers differ" in p for p in outcome.problems),
                "numbers differ" in wrong.prompts[1][1],
                os.path.exists(os.path.join(workspace.root, "docs", "it", "start.md"))),
               ("failed", 2, True, True, False))
        with tempfile.TemporaryDirectory() as out:
            write_out(translator, out)
            expect("written out: the catalog and the pages, the chapter in its folder", sorted(
                os.path.relpath(os.path.join(d, n), out) for d, _, ns in os.walk(out) for n in ns),
                ["docs/it/handbook/03-ground-truth.md", "docs/it/why.md", "i18n/it.yml"])
            with open(os.path.join(out, "docs", "it", "why.md"), "a", encoding="utf-8") as fh:
                fh.write("\nA line only the run's output has.\n")
            second = Workspace(ROOT, out, english_only=True)
            try:
                expect("the plan over the first run's output: nothing for Why or the chapter, Start still to translate",
                       (plan(second.root, ["it"], ["why", "handbook/03-ground-truth"]),
                        plan(second.root, ["it"], ["why", "start"])),
                       ({"work": False, "catalogs": {}, "pages": {}},
                        {"work": True, "catalogs": {}, "pages": {"it": ["start"]}}))
                again = FakeModel(_fake_answer(second.root, "it"))
                rerun = Translator(again, Ledger(5.0), second)
                rerun.run(["it"], ["why"])
                expect("a second run over the first one's output: nothing to translate, no call",
                       ([(o.subject, o.status) for o in rerun.outcomes], len(again.prompts)),
                       ([("i18n/it.yml", "unchanged"), ("docs/it/why.md", "unchanged")], 0))
                expect("the summary over the first run's output: the chapter translated and up to date",
                       summary(second.root, ["it", "de"]).splitlines(),
                       ["- Handbook, it: 1 of 10 page(s) translated, 0 behind the English",
                        "- Handbook, de: 0 of 10 page(s) translated"])
                with open(second.path("docs", "handbook", "03-ground-truth.md"), "a", encoding="utf-8") as fh:
                    fh.write("\nOne more sentence in English.\n")
                expect("the summary after the English chapter changed: behind, and named",
                       summary(second.root, ["it"]),
                       "- Handbook, it: 1 of 10 page(s) translated, 1 behind the English (handbook/03-ground-truth)\n")
                # One English sentence changed: the plan has that page, in that language, and nothing else.
                with open(second.path("docs", "why.md"), "a", encoding="utf-8") as fh:
                    fh.write("\nOne more sentence.\n")
                expect("the plan after an English edit: that page, no catalog key",
                       plan(second.root, ["it"], ["why"]), {"work": True, "catalogs": {}, "pages": {"it": ["why"]}})
            finally:
                second.close()
    finally:
        workspace.close()

    for failure in failures:
        print(f"translate selftest: FAILED — {failure}", file=sys.stderr)
    if failures:
        return 1
    print("translate selftest: prompts, token renewal, the catalog and its fixed section, the second attempt, "
          "the skip, the spending limit and the report, with a fake model; a real build of a fake Italian "
          "catalog and Why that passes the checks; a second run over the first that makes no call")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
