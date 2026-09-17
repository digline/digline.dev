"""The words the site writes itself, read out of i18n/<lang>.yml.

The presentation pages' templates and tools/hooks/home.py do not type the words
they show — a title, a label, a button, an aria-label. They name a key, and the
catalog holds the words: i18n/en.yml, the only catalog today and the original
every other will be translated from. The templates reach it through the `t`
filter tools/hooks/i18n.py registers, the hooks through ``t()`` below; both are
the same function.

── the catalog ──────────────────────────────────────────────────────────────
Nested mappings, grouped by where the words are shown (``bar``, ``footer``,
``home.verdict``, …); a key is the path to a value, dotted:
``home.hero.lede``. A value is one of

  * a string, printed as it is. Values are HTML, the way the templates had
    them: ``&rsquo;``, ``&nbsp;`` and ``&rarr;`` are written as entities, and
    a value that ran over several lines of a template keeps its line breaks
    and their indentation (a YAML ``|-`` block, continued two spaces further
    in), so the page is the same page byte for byte.
  * a plural: a mapping of exactly ``one`` and ``other``, chosen by ``count``
    — ``one`` when count is 1, ``other`` otherwise, the rule English, Italian,
    German and Spanish share for whole numbers.

A value may name placeholders, ``{name}``, filled from the arguments ``t`` is
given. With ``count`` three more are there to use: ``{count}`` in digits,
``{number}`` in words and ``{Number}`` the same with a capital, the words from
the ``numbers`` section (one to twenty; digits past it).

── what fails ───────────────────────────────────────────────────────────────
At the call: a key the catalog does not have; a plural without ``count``, or a
``count`` for a key that is not one; a placeholder nothing fills; an argument no
placeholder uses. Before the build: all of those that can be seen in the
source, plus a key the source never names — see ``scan()``, which
tools/hooks/i18n.py runs. The ``numbers`` section is named by no one: it is in
use while a plural in use writes ``{number}`` or ``{Number}``.
"""

from __future__ import annotations

import ast
import functools
import os
import re

import yaml
from mkdocs.exceptions import PluginError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOG = os.path.join(ROOT, "i18n", "en.yml")

# Where the keys are named: every template in overrides/ and every hook.
TEMPLATES = os.path.join(ROOT, "overrides")
PYTHON = (os.path.join(ROOT, "tools", "hooks"),)

PLURAL = ("one", "other")
AUTOMATIC = ("count", "number", "Number")
NUMBERS = "numbers"

_SEGMENT = re.compile(r"^[a-z0-9_]+$")
_PLACEHOLDER = re.compile(r"\{([A-Za-z_][A-Za-z0-9_]*)\}")


class CatalogError(PluginError):
    pass


class _UniqueKeys(yaml.SafeLoader):
    """PyYAML keeps the last of two equal keys without a word; this refuses."""


def _mapping(loader, node, deep=False):
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in seen:
            raise CatalogError(f"catalog: the key {key!r} is written twice (line {key_node.start_mark.line + 1}).")
        seen.add(key)
    return loader.construct_mapping(node, deep=deep)


_UniqueKeys.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _mapping)


def placeholders(value: str | dict) -> set[str]:
    forms = value.values() if isinstance(value, dict) else [value]
    return {name for form in forms for name in _PLACEHOLDER.findall(form)}


class Catalog:
    """One catalog file, flattened: dotted key → string or {one, other}."""

    def __init__(self, path: str = CATALOG):
        self.path = path
        try:
            with open(path, encoding="utf-8") as fh:
                data = yaml.load(fh, Loader=_UniqueKeys)
        except OSError as error:
            raise CatalogError(f"catalog: cannot read {path}: {error}") from None
        if not isinstance(data, dict) or not data:
            raise CatalogError(f"catalog: {path} is not a mapping of sections.")
        self.entries: dict[str, str | dict] = {}
        self._flatten(data, [])

    def _flatten(self, node: dict, path: list[str]) -> None:
        for raw, value in node.items():
            segment = str(raw)
            key = ".".join(path + [segment])
            if not _SEGMENT.match(segment):
                raise CatalogError(f"catalog: {key!r} — a key is lower-case letters, digits and _.")
            if isinstance(value, str):
                self.entries[key] = value
            elif isinstance(value, dict) and {str(k) for k in value} == set(PLURAL):
                forms = {str(k): v for k, v in value.items()}
                if not all(isinstance(v, str) for v in forms.values()):
                    raise CatalogError(f"catalog: {key} — `one` and `other` must both be strings.")
                self.entries[key] = forms
            elif isinstance(value, dict) and value and not ({str(k) for k in value} & set(PLURAL)):
                self._flatten(value, path + [segment])
            elif isinstance(value, dict) and value:
                raise CatalogError(f"catalog: {key} — a plural has exactly `one` and `other`, "
                                   f"and this has {sorted(str(k) for k in value)}.")
            else:
                raise CatalogError(f"catalog: {key} is {value!r}; a value is a string, a plural "
                                   "or a section. (Quote a word YAML reads as something else, "
                                   "like no or yes.)")

    def number_word(self, n: int) -> str:
        word = self.entries.get(f"{NUMBERS}.{n}")
        return word if isinstance(word, str) else str(n)

    def t(self, key: str, count: int | None = None, **values) -> str:
        if key not in self.entries:
            raise CatalogError(f"catalog: no key {key!r} in {self.path}.")
        entry = self.entries[key]
        if isinstance(entry, dict):
            if count is None:
                raise CatalogError(f"catalog: {key} is a plural and was given no count.")
            template = entry["one" if int(count) == 1 else "other"]
        elif count is not None:
            raise CatalogError(f"catalog: {key} is not a plural and was given a count.")
        else:
            template = entry
        wanted = placeholders(entry)
        unused = sorted(set(values) - wanted)
        if unused:
            raise CatalogError(f"catalog: {key} has no placeholder for {', '.join(unused)}.")
        filled = {name: str(value) for name, value in values.items()}
        if count is not None:
            word = self.number_word(int(count))
            filled.setdefault("count", str(count))
            filled.setdefault("number", word)
            filled.setdefault("Number", word[:1].upper() + word[1:])
        missing = sorted(set(_PLACEHOLDER.findall(template)) - set(filled))
        if missing:
            raise CatalogError(f"catalog: {key} needs {', '.join(missing)}, and was not given it.")
        return _PLACEHOLDER.sub(lambda m: filled[m.group(1)], template)


@functools.lru_cache(maxsize=None)
def default() -> Catalog:
    return Catalog(CATALOG)


def t(key: str, count: int | None = None, **values) -> str:
    """The words for ``key`` in the site's catalog. See the module docstring."""
    return default().t(key, count=count, **values)


def number_word(n: int) -> str:
    """``n`` in words, from the catalog's numbers; in digits past them."""
    return default().number_word(n)


# ── the check ────────────────────────────────────────────────────────────────


class Use:
    """One place the source names a key."""

    def __init__(self, where: str, key: str | None, count: bool = False,
                 names: set[str] | None = None):
        self.where, self.key, self.count = where, key, count
        # None: arguments passed with ** or *, which the source does not show.
        self.names = names


def template_uses(path: str, source: str) -> list[Use]:
    """Every ``"key" | t(...)`` in a Jinja template, from its syntax tree."""
    from jinja2 import Environment, nodes

    uses: list[Use] = []
    tree = Environment().parse(source)
    for node in tree.find_all(nodes.Filter):
        if node.name != "t":
            continue
        where = f"{path}:{node.lineno}"
        if not (isinstance(node.node, nodes.Const) and isinstance(node.node.value, str)):
            uses.append(Use(where, None))
            continue
        names = None if (node.args or node.dyn_args or node.dyn_kwargs) else {k.key for k in node.kwargs}
        counted = any(k.key == "count" for k in node.kwargs)
        uses.append(Use(where, node.node.value, counted, None if names is None else names - {"count"}))
    return uses


def python_uses(path: str, source: str) -> list[Use]:
    """Every ``t("key", ...)`` in a Python file: a call of anything named t."""
    uses: list[Use] = []
    for node in ast.walk(ast.parse(source, filename=path)):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
        if name != "t":
            continue
        where = f"{path}:{node.lineno}"
        first = node.args[0] if node.args else None
        if not (isinstance(first, ast.Constant) and isinstance(first.value, str)):
            uses.append(Use(where, None))
            continue
        shown = len(node.args) == 1 and all(k.arg is not None for k in node.keywords)
        names = {k.arg for k in node.keywords if k.arg} if shown else None
        counted = any(k.arg == "count" for k in node.keywords)
        uses.append(Use(where, first.value, counted, None if names is None else names - {"count"}))
    return uses


def sources(templates: str = TEMPLATES, python=PYTHON) -> list[tuple[str, str]]:
    """(path, kind) of every file the check reads, in a stable order."""
    found: list[tuple[str, str]] = []
    for folder, dirs, names in os.walk(templates):
        dirs.sort()
        found += [(os.path.join(folder, n), "template") for n in sorted(names) if n.endswith(".html")]
    for entry in python:
        if os.path.isdir(entry):
            found += [(os.path.join(entry, n), "python") for n in sorted(os.listdir(entry)) if n.endswith(".py")]
        else:
            found.append((entry, "python"))
    return found


def scan(catalog: Catalog, files: list[tuple[str, str]], root: str = ROOT) -> tuple[list[str], dict]:
    """The problems between a catalog and the source that names its keys."""
    problems: list[str] = []
    uses: list[Use] = []
    for path, kind in files:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        rel = os.path.relpath(path, root)
        uses += template_uses(rel, text) if kind == "template" else python_uses(rel, text)

    used: set[str] = set()
    for use in uses:
        if use.key is None:
            problems.append(f"{use.where}: a key that is not written out — name it as a literal "
                            "string, so this check can see it")
            continue
        if use.key not in catalog.entries:
            problems.append(f"{use.where}: {use.key!r} is not in the catalog")
            continue
        used.add(use.key)
        entry = catalog.entries[use.key]
        plural = isinstance(entry, dict)
        if plural and not use.count:
            problems.append(f"{use.where}: {use.key} is a plural, and no count= is passed")
        if use.count and not plural:
            problems.append(f"{use.where}: {use.key} is not a plural, and count= is passed")
        if use.names is not None:
            wanted = placeholders(entry)
            given = use.names | (set(AUTOMATIC) if use.count else set())
            for name in sorted(wanted - given):
                problems.append(f"{use.where}: {use.key} needs {{{name}}}, and nothing passes it")
            for name in sorted(use.names - wanted):
                problems.append(f"{use.where}: {use.key} has no {{{name}}}, and {name}= is passed")

    if any(name in placeholders(catalog.entries[key]) for key in used for name in ("number", "Number")):
        used.update(k for k in catalog.entries if k.startswith(NUMBERS + "."))
    for key in sorted(set(catalog.entries) - used):
        problems.append(f"{os.path.relpath(catalog.path, root)}: {key} is in the catalog, and nothing uses it")
    return problems, {"keys": len(catalog.entries), "uses": len(uses), "files": len(files)}
