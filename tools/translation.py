"""What a translation was made from, and the words it must keep.

Shared by tools/check-translations.py, which compares every translation with
its original, and by tools/hooks/translations.py's selftest, which builds the
fake translations of tools/testdata/translations.

── what a translation was made from ─────────────────────────────────────────
A translation's front matter records the original it was made from:

    source: why.md                 the English page, as translation_of names it
    source_sha: 1a2b3c4d5e6f       source_sha() of that page when it was translated
    source_commit: 9545771         the commit of the original it was made from
    model: claude-opus-5           what translated it

``source_sha`` is ``assets.digest`` — twelve hex digits of SHA-256, the digest
tools/hooks/assets.py versions the stylesheets with — of the original's
Markdown after its front matter, exactly as written, then a newline, then its
``description:``. The home's words are not in its Markdown but in the catalog,
and the catalog records what it was translated from: i18n/<lang>.yml carries
``source_keys:``, the same digest of every key of i18n/en.yml when it was
translated (a plural's ``one``, a newline, its ``other``), nested the way the
keys are — ``source_keys: {home: {hero: {lede: 1a2b3c4d5e6f}}}``. The status
of a translation of index.md reads them there.

``status()`` compares those with the originals as they are now: an original
that changed since its translation is reported, and never refused — the
English site must stay free to change.

── the words a translation keeps ────────────────────────────────────────────
tools/i18n/glossary.yml's ``keep``, and, read from the site's own data rather
than written there (``data_terms()``): digline's command names, as
``digline <name>``; the names of its checks; the packages the home names; the
frameworks of the worked examples. ``forbidden``, per language, lists
translations of the glossary that a translation must not use.

── the fake translations ────────────────────────────────────────────────────
``pseudo_translate()`` turns an English page into a translation that keeps
everything the checks compare — code, links, numbers, headings, the kept
words — and changes every other word, so that the selftests can build a
translation of each presentation page as it is today, whatever it says.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

import yaml

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
sys.path.insert(0, os.path.join(TOOLS, "hooks"))
import catalog  # noqa: E402  tools/catalog.py
import languages  # noqa: E402  tools/languages.py
from assets import digest  # noqa: E402  tools/hooks/assets.py: the site's digest

GLOSSARY = os.path.join("tools", "i18n", "glossary.yml")
HOME_JSON = os.path.join("docs", "product", "assets", "home", "home.json")

SOURCE_FIELDS = ("source", "source_sha", "source_commit", "model")
KEYS_FIELD = "source_keys"
HOME = "index.md"

_FRONT_MATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---[ \t]*\r?\n", re.S)
SHA = re.compile(r"^[0-9a-f]{12}$")
COMMIT = re.compile(r"^[0-9a-f]{7,40}$")


def split_front_matter(text: str) -> tuple[dict, str]:
    match = _FRONT_MATTER.match(text)
    if not match:
        return {}, text
    data = yaml.safe_load(match.group(1))
    return (data if isinstance(data, dict) else {}), text[match.end():]


def read_page(path: str) -> tuple[dict, str]:
    with open(path, encoding="utf-8") as fh:
        return split_front_matter(fh.read())


def source_sha(root: str, page: str) -> str:
    """The digest of an English page as a translation records it."""
    meta, body = read_page(os.path.join(root, "docs", page))
    description = str(meta.get("description") or "").strip()
    return digest((body + "\n" + description).encode("utf-8"))


def catalog_hashes(root: str) -> dict[str, str]:
    """The digest of every key of the English catalog."""
    entries = catalog.Catalog(os.path.join(root, "i18n", f"{languages.ORIGINAL}.yml")).entries
    return {key: digest((value if isinstance(value, str) else value["one"] + "\n" + value["other"]).encode("utf-8"))
            for key, value in sorted(entries.items())}


def source_commit(root: str, page: str) -> str:
    """The last commit that touched an original: the page, or for the home the catalog."""
    path = os.path.join("i18n", "en.yml") if page == HOME else os.path.join("docs", page)
    out = subprocess.run(["git", "-C", root, "log", "-1", "--format=%h", "--", path],
                         capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else ""


def commit_date(root: str, commit) -> str | None:
    """The day a commit was made, YYYY-MM-DD; None when the repository does not have it.
    The date a translation's notice gives its original."""
    if not commit or not COMMIT.match(str(commit)):
        return None
    out = subprocess.run(["git", "-C", root, "show", "-s", "--format=%cs", f"{commit}^{{commit}}"],
                         capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 and out.stdout.strip() else None


def fixed_texts(root: str) -> dict[str, dict[str, str]]:
    """Each language's fixed section, key → text; a language with no catalog is absent."""
    texts = {}
    for lang in languages.LANGUAGES:
        path = os.path.join(root, "i18n", f"{lang}.yml")
        if os.path.isfile(path):
            entries = catalog.Catalog(path).entries
            texts[lang] = {key: value for key, value in sorted(entries.items())
                           if key.startswith(catalog.FIXED + ".") and isinstance(value, str)}
    return texts


def fixed_digest(root: str) -> str:
    """One digest of every language's fixed section: what check-translations pins."""
    lines = [f"{lang}\t{key}\t{text}" for lang, texts in sorted(fixed_texts(root).items())
             for key, text in texts.items()]
    return digest("\n".join(lines).encode("utf-8"))


def nested(flat: dict[str, str]) -> dict:
    """``{"home.hero.lede": x}`` as ``{"home": {"hero": {"lede": x}}}``."""
    tree: dict = {}
    for key, value in flat.items():
        *path, last = key.split(".")
        node = tree
        for segment in path:
            node = node.setdefault(segment, {})
        node[last] = value
    return tree


def catalog_source_keys(root: str, lang: str) -> dict[str, str]:
    """The digests a language's catalog records, by English key; {} when it has none."""
    path = os.path.join(root, "i18n", f"{lang}.yml")
    if not os.path.isfile(path):
        return {}
    prefix = KEYS_FIELD + "."
    return {key[len(prefix):]: value for key, value in catalog.Catalog(path).entries.items()
            if key.startswith(prefix) and isinstance(value, str)}


def stamp(meta: dict, root: str, model: str, commit: str | None = None) -> dict:
    """``meta`` with what its translation was made from, as the originals are now."""
    page = meta["translation_of"]
    return dict(meta, source=page, source_sha=source_sha(root, page),
                source_commit=commit or source_commit(root, page) or "0000000", model=model)


def status(meta: dict, root: str) -> list[str]:
    """What changed in the original since the translation was made; [] when nothing."""
    page = meta.get("source")
    if page not in languages.PAGES:
        return []
    changes = []
    now = source_sha(root, page)
    if meta.get("source_sha") != now:
        changes.append(f"{page} source_sha {meta.get('source_sha')} → {now}")
    if page == HOME:
        recorded = catalog_source_keys(root, str(meta.get("lang")))
        current = catalog_hashes(root)
        changed = sorted(k for k in current if k in recorded and recorded[k] != current[k])
        new = sorted(set(current) - set(recorded))
        gone = sorted(set(recorded) - set(current))
        for label, keys in (("changed", changed), ("new", new), ("removed", gone)):
            if keys:
                shown = ", ".join(keys[:5]) + (f", … {len(keys) - 5} more" if len(keys) > 5 else "")
                changes.append(f"{len(keys)} catalog key(s) {label}: {shown}")
    return changes


# ── the words a translation keeps ────────────────────────────────────────────


def glossary(root: str) -> dict:
    with open(os.path.join(root, GLOSSARY), encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    keep = [str(term) for term in data.get("keep") or []]
    forbidden = {str(lang): [str(term) for term in terms or []]
                 for lang, terms in (data.get("forbidden") or {}).items()}
    return {"keep": keep, "forbidden": forbidden}


def data_terms(root: str) -> dict[str, list[str]]:
    """The names the site's data gives: commands, checks, packages, frameworks."""
    import importlib.util

    with open(os.path.join(root, HOME_JSON), encoding="utf-8") as fh:
        data = json.load(fh)
    spec = importlib.util.spec_from_file_location("home_for_terms", os.path.join(root, "tools", "hooks", "home.py"))
    home = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(home)
    return {
        "commands": sorted(c["name"] for c in data["cli_commands"]["items"]),
        "checks": sorted(c["name"] for c in data["checks"]["items"]),
        "packages": sorted(set(data["runtime_dependencies"]["names"])
                           | {package for _, package, _ in home.STACK_PROVIDERS}),
        "frameworks": sorted(name for name, _ in home.STACK_EXAMPLES),
    }


def term_pattern(term: str, ignore_case: bool) -> str:
    """A term as a whole word or words: not inside a longer word, nor a hyphenated one."""
    body = r"\s+".join(re.escape(word) for word in term.split())
    return (r"(?i:" if ignore_case else r"(?:") + r"(?<![\w-])" + body + r"(?![\w-]))"


def kept_terms(root: str) -> list[tuple[str, str]]:
    """(what to report, pattern) of every term a translation keeps."""
    terms = [(term, term_pattern(term, True)) for term in glossary(root)["keep"]]
    names = data_terms(root)
    terms += [(f"digline {name}", r"(?<![\w-])digline\s+" + re.escape(name) + r"(?![\w-])") for name in names["commands"]]
    for kind in ("checks", "packages", "frameworks"):
        terms += [(name, term_pattern(name, False)) for name in names[kind]]
    return terms


# ── the fake translations ────────────────────────────────────────────────────

SUFFIX = {"it": "o", "de": "ẞ", "es": "ñ"}


def pseudo_translate(body: str, lang: str, root: str) -> str:
    """An English page's Markdown as a fake translation in ``lang``: every word
    outside what the checks compare gets a suffix (ẞ in German, so a German
    page draws it), and every relative link is made to reach the English page
    from one folder down."""
    protected = [
        r"```.*?```", r"<!--.*?-->", r"`[^`\n]+`", r"<[^>\n]+>", r"\]\([^)\n]*\)", r"&\w+;",
        r"https?://\S+", r"\d+(?:\.\d+)*",
    ]
    protected += [pattern for _, pattern in sorted(kept_terms(root), key=lambda t: -len(t[0]))]
    protected.append(r"(?<![\w-])digline(?![\w-])")
    splitter = re.compile("(" + "|".join(protected) + ")", re.S)
    link = re.compile(r"\]\(([^)\n]*)\)")
    out = []
    for i, part in enumerate(splitter.split(body)):
        if part is None or part == "":
            continue
        if splitter.fullmatch(part):
            match = link.fullmatch(part)
            if match and not re.match(r"^(?:[a-z]+:|/|#)", match.group(1)):
                part = f"](../{match.group(1)})"
            out.append(part)
        else:
            out.append(re.sub(r"[^\W\d_]+", lambda m: m.group(0) + SUFFIX[lang], part))
    return "".join(out)


def fake_translation(root: str, lang: str, meta: dict) -> str:
    """The text of a fake translation: ``meta`` stamped, over the pseudo-translated
    body of its original as the site has it now."""
    _, body = read_page(os.path.join(root, "docs", meta["translation_of"]))
    stamped = stamp(meta, root, model="selftest (tools/translation.py, pseudo_translate)")
    front = yaml.safe_dump(stamped, allow_unicode=True, sort_keys=False, width=1000)
    return f"---\n{front}---\n{pseudo_translate(body, lang, root)}"
