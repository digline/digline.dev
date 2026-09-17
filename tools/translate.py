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
the other way, a claim the English does not make, something left out — as
JSON, {ok, issues}. A page with issues is kept, and marked "needs attention".

── the model and the bill ───────────────────────────────────────────────────
claude-opus-5 for both calls, adaptive thinking, structured JSON output, and
server-side fallbacks ("default"): a request the model declines is run again
on the model Anthropic routes it to, and the report names the model that
answered. Every call's input and output tokens are recorded and priced from
PRICES, read from Anthropic's pricing page on PRICES_READ. The run stops before
the next call once --max-cost (USD) has been spent.

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
With --dry-run, nothing in docs/ or i18n/: everything goes to --out —
docs/<lang>/<page>.md and i18n/<lang>.yml for what was translated or carried
over unchanged, report.md, and calls.json. --existing DIR lays the
translations of an earlier dry run (its --out) over the repository first, so
a second run skips what the first translated.

    usage: tools/translate.py --langs it,de,es --pages index,start,why,about,contact
                              --out DIR --dry-run [--existing DIR] [--max-cost 5]
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

DEFAULT_MAX_COST = 5.0
REFRESH_MARGIN = 120
MAX_TOKENS = 64000

LANGUAGE_NAMES = {"it": "Italian", "de": "German", "es": "Spanish"}
ADDRESS = {"it": 'the informal "tu"', "de": 'the informal "du"', "es": 'the informal "tú"'}
WE = {"it": '"noi"', "de": '"wir"', "es": '"nosotros"'}
PAGE_FILES = {os.path.splitext(page)[0]: page for page in languages.PAGES}

# The front matter a translation translates; the rest is copied or stamped.
TRANSLATED_FIELDS = ("title", "seo_title", "description", "kicker", "accent")
FIXED_HEADING = "# ── DO NOT TRANSLATE"


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
- Leave these terms in English, exactly as written, wherever the English uses them: {", ".join(words["keep"])}.
- Leave these names exactly as written: the commands digline {", digline ".join(names["commands"])}; the checks {", ".join(names["checks"])}; the packages {", ".join(names["packages"])}; the frameworks {", ".join(names["frameworks"])}.
- Never use these words: {", ".join(words["forbidden"].get(lang, [])) or "(none)"}."""


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
            "properties": {"kind": {"type": "string", "enum": ["negation", "reversed", "added", "omitted", "other"]},
                           "english": {"type": "string"}, "translation": {"type": "string"},
                           "explanation": {"type": "string"}},
            "required": ["kind", "english", "translation", "explanation"],
            "additionalProperties": False,
        }},
    },
    "required": ["ok", "issues"],
    "additionalProperties": False,
}


def page_prompt(lang: str, meta: dict, body: str, previous: dict | None, diff: str | None,
                problems: list[str] | None, last: dict | None) -> str:
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

An error of meaning is: a negation added, dropped or turned round; a threshold, a comparison, a number's role or a behaviour described the other way round; a claim, a promise or a detail the English does not make; something the English says that the translation leaves out.

Not errors, and never to be reported: style, word choice, register, sentence order; English terms, commands, code and names left in English on purpose; the first person plural of the English rendered as the first person singular or impersonally (that is required); link targets with ../ in front.

Return JSON {{"ok": true, "issues": []}} when there is no error of meaning; otherwise "ok": false and one issue per error, quoting the English and the translation."""


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

    def __init__(self, repo: str, existing: str | None = None):
        self.dir = tempfile.mkdtemp(prefix="translate-")
        self.root = os.path.join(self.dir, "repo")
        subprocess.run(["git", "clone", "-q", "--local", repo, self.root], check=True)
        for name in ("mkdocs.yml", ".lastmod.tsv"):
            if os.path.isfile(os.path.join(repo, name)):
                shutil.copy(os.path.join(repo, name), self.root)
        ignore = shutil.ignore_patterns("__pycache__", ".DS_Store")
        for name in ("overrides", "tools", "i18n", "docs"):
            shutil.rmtree(os.path.join(self.root, name), ignore_errors=True)
            shutil.copytree(os.path.join(repo, name), os.path.join(self.root, name), ignore=ignore)
        if existing:
            for lang in languages.LANGUAGES:
                pages = os.path.join(existing, "docs", lang)
                if os.path.isdir(pages):
                    shutil.copytree(pages, os.path.join(self.root, "docs", lang), dirs_exist_ok=True)
                words = os.path.join(existing, "i18n", f"{lang}.yml")
                if os.path.isfile(words):
                    shutil.copy(words, os.path.join(self.root, "i18n", f"{lang}.yml"))
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


def fixed_section(path: str) -> str:
    """The catalog's do_not_translate section, as written: from its heading to the end."""
    if not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    start = text.find(FIXED_HEADING)
    if start < 0:
        start = text.find(catalog.FIXED + ":")
    return text[start:] if start >= 0 else ""


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


_RELATIVE = re.compile(r"\]\((?![a-z]+:|/|#|\.\./)([^)\s]+)\)")


def one_folder_down(body: str) -> str:
    """Relative Markdown links, written from the English page's folder, as seen
    from the translation's, one folder down."""
    return _RELATIVE.sub(lambda m: f"](../{m.group(1)})", body)


def page_text(root: str, lang: str, page: str, answer: dict, model: str) -> str:
    english, _ = translation.read_page(os.path.join(root, "docs", page))
    meta = {"title": answer["title"] or english.get("title"), "template": english.get("template")}
    for field in ("seo_title", "kicker", "accent"):
        if english.get(field):
            meta[field] = answer[field]
    meta.update(lang=lang, translation_of=page, description=answer["description"], search={"exclude": True})
    stamped = translation.stamp(meta, root, model=model)
    front = yaml.safe_dump(stamped, allow_unicode=True, sort_keys=False, width=1000)
    return f"---\n{front}---\n\n{one_folder_down(answer['body']).strip()}\n"


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
                verdict = self.ask("meaning", lang, subject, 1, meaning_system(lang),
                                   meaning_prompt(english_body, answer["body"]), MEANING_SCHEMA).data
                outcome.meaning = verdict
                self.outcomes.append(outcome)
                return
        if before is None:
            os.remove(path)
        else:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(before)
        self.outcomes.append(Outcome(lang, subject, "failed", "not written", 2, problems))


# ── the report ───────────────────────────────────────────────────────────────


def report(translator: Translator, langs, pages, dry_run: bool, started: str) -> str:
    ledger = translator.ledger
    lines = [f"# Translation run, {started}", "",
             f"- Mode: {'dry run — nothing written to docs/ or i18n/' if dry_run else 'writing to docs/ and i18n/'}",
             f"- Languages: {', '.join(langs)}; pages: {', '.join(pages)}",
             f"- Model: {MODEL}; prices {', '.join(f'{m} ${p[0]:g}/${p[1]:g} per MTok in/out' for m, p in PRICES.items())} "
             f"(Anthropic's pricing page, read {PRICES_READ})",
             f"- Spent: **{ledger.spent:.4f} USD** of a {ledger.cap:.2f} USD limit, in {len(ledger.calls)} call(s); "
             f"{sum(c.input_tokens for c in ledger.calls)} input and {sum(c.output_tokens for c in ledger.calls)} output tokens",
             "", "## Outcomes", "", "| Language | What | Status | Attempts | Checks | Meaning |", "|---|---|---|---|---|---|"]
    attention = []
    for o in translator.outcomes:
        meaning = "—"
        if o.meaning is not None:
            meaning = "ok" if o.meaning.get("ok") and not o.meaning.get("issues") else "**needs attention**"
            if meaning != "ok":
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
    lines += ["", "## Calls", "", "| Kind | Language | What | Attempt | Model | Input tokens | Output tokens | Cost (USD) |",
              "|---|---|---|---|---|---|---|---|"]
    for c in ledger.calls:
        lines.append(f"| {c.kind} | {c.lang} | `{c.subject}` | {c.attempt} | {c.model} | {c.input_tokens} | "
                     f"{c.output_tokens} | {c.cost:.4f} |")
    texts = [o for o in translator.outcomes if o.status == "translated" and o.text]
    if texts:
        lines += ["", "## Texts", ""]
        for o in texts:
            lines += [f"<details><summary><code>{o.subject}</code></summary>", "", "````markdown" if o.subject.endswith(".md") else "````yaml",
                      o.text.rstrip("\n"), "````", "", "</details>", ""]
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


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--langs", default=",".join(languages.LANGUAGES))
    parser.add_argument("--pages", default=",".join(PAGE_FILES))
    parser.add_argument("--out", required=True)
    parser.add_argument("--existing")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-cost", type=float, default=DEFAULT_MAX_COST)
    args = parser.parse_args(argv)
    langs = [lang.strip() for lang in args.langs.split(",") if lang.strip()]
    pages = [page.strip() for page in args.pages.split(",") if page.strip()]
    wrong = [lang for lang in langs if lang not in languages.LANGUAGES] + [p for p in pages if p not in PAGE_FILES]
    if wrong:
        parser.error(f"not a language or a page: {', '.join(wrong)}")
    if not args.dry_run:
        parser.error("only --dry-run for now: the translations are not published yet")
    started = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    workspace = Workspace(ROOT, args.existing)
    translator = Translator(Claude(FederatedToken()), Ledger(args.max_cost), workspace)
    try:
        translator.run(langs, pages)
        os.makedirs(args.out, exist_ok=True)
        write_out(translator, args.out)
        text = report(translator, langs, pages, True, started)
        with open(os.path.join(args.out, "report.md"), "w", encoding="utf-8") as fh:
            fh.write(text)
        with open(os.path.join(args.out, "calls.json"), "w", encoding="utf-8") as fh:
            json.dump([dataclasses.asdict(c) for c in translator.ledger.calls], fh, indent=2)
        print(text)
    finally:
        workspace.close()
    failed = [o for o in translator.outcomes if o.status in ("failed", "stopped")]
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


def _fake_answer(root: str, lang: str, meaning_ok: bool = True):
    """A fake model that translates the way the fixtures do: the catalog as it
    is, a page pseudo-translated, and a meaning check that says what it is told."""
    def answer(system, prompt, schema):
        if schema is CATALOG_SCHEMA:
            return {"entries": [{"key": e["key"], "text": e.get("text", ""), "one": e.get("one", ""),
                                 "other": e.get("other", "")} for e in _english_entries(prompt)]}
        if schema is PAGE_SCHEMA:
            body = re.search(r"<english>\n(.*?)\n</english>", prompt, re.S).group(1)
            meta = dict(re.findall(r"^(title|seo_title|description|kicker|accent): (.*)$",
                                   prompt.split("<english>")[0], re.M))
            return {field: meta.get(field, "") for field in TRANSLATED_FIELDS} | {
                "body": translation.pseudo_translate(body, lang, root).replace("](../", "](")}
        return {"ok": meaning_ok, "issues": [] if meaning_ok else [
            {"kind": "negation", "english": "does not", "translation": "does", "explanation": "a negation dropped"}]}
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
    workspace = Workspace(ROOT)
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
        text = report(translator, ["it"], ["contact"], True, "2026-09-17 12:00 UTC")
        wanted = ("| it | `docs/it/contact.md` | translated (new) | 1 | passed | **needs attention** |",
                  "## Needs attention", "a negation dropped",
                  "| page | it | `docs/it/contact.md` | 1 | claude-opus-5 | 1000 | 500 | 0.0175 |",
                  "Spent: **0.0350 USD**", "## Texts", "<code>docs/it/contact.md</code>")
        expect("the report: outcome, needs attention, calls, cost, the text",
               [w for w in wanted if w not in text], [])
    finally:
        workspace.close()

    # 7. The real thing, without the network: the Italian catalog and Why, built and checked.
    workspace = Workspace(ROOT)
    try:
        fake = FakeModel(_fake_answer(workspace.root, "it"))
        translator = Translator(fake, Ledger(5.0), workspace)
        translator.run(["it"], ["why"])
        expect("built and checked for real: the catalog and Why translated at the first attempt",
               [(o.subject, o.status, o.attempts) for o in translator.outcomes],
               [("i18n/it.yml", "translated", 1), ("docs/it/why.md", "translated", 1)])
        # The same checks refuse what they must: a decimal point made a comma, twice.
        comma = _fake_answer(workspace.root, "it")
        wrong = FakeModel(lambda system, prompt, schema: (
            {**comma(system, prompt, schema), "body": comma(system, prompt, schema)["body"].replace("0.88", "0,88")}
            if schema is PAGE_SCHEMA else comma(system, prompt, schema)))
        refused = Translator(wrong, Ledger(5.0), workspace)
        refused.page("it", "start")
        outcome = refused.outcomes[-1]
        expect("built and checked for real: 0,88 for 0.88 refused twice, the page not written",
               (outcome.status, outcome.attempts, any("numbers differ" in p for p in outcome.problems),
                "numbers differ" in wrong.prompts[1][1],
                os.path.exists(os.path.join(workspace.root, "docs", "it", "start.md"))),
               ("failed", 2, True, True, False))
        with tempfile.TemporaryDirectory() as out:
            write_out(translator, out)
            expect("written out: the catalog and the page", sorted(
                os.path.relpath(os.path.join(d, n), out) for d, _, ns in os.walk(out) for n in ns),
                ["docs/it/why.md", "i18n/it.yml"])
            second = Workspace(ROOT, out)
            try:
                again = FakeModel(_fake_answer(second.root, "it"))
                rerun = Translator(again, Ledger(5.0), second)
                rerun.run(["it"], ["why"])
                expect("a second run over the first one's output: nothing to translate, no call",
                       ([(o.subject, o.status) for o in rerun.outcomes], len(again.prompts)),
                       ([("i18n/it.yml", "unchanged"), ("docs/it/why.md", "unchanged")], 0))
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
