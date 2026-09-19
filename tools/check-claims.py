#!/usr/bin/env python3
"""Refuse an absolute claim about where data goes that the site cannot stand
behind, in English or in a translation.

digline has the same gate on its own files (tools/claims.py there). This one
reads what is written here and nothing the sync brings in: docs/product/ is
digline's, and is checked in digline. So the gate needs no build and no
checkout of the other repository.

Three lists, and a non-zero exit on any hit:

  * TIER_1 is never admitted. Each phrase has been written somewhere and was
    false as written; it is rewritten, not registered.

  * TIER_2 is admitted only with an entry in tools/claims-register.toml, and
    an entry is admitted only when the claim is anchored: a file in this
    repository and the text in it that makes the sentence true. Being harmless
    is not a reason. Both ends are checked — the quote must still be in its
    file, the anchor must still hold the evidence — so a claim that outlives
    its reason fails here instead of drifting.

  * CALQUES are the translations of "Nothing leaves your machine", which was on
    /why/ and is gone. A translation run could put them back word for word, and
    nobody would read them again; each is refused in its own language, in
    docs/<lang>/ and in i18n/<lang>.yml.

What is read: every Markdown page under docs/ but docs/product/, and the
catalogs in i18n/. The text is compared lowercased, with runs of whitespace as
one space and Markdown's * dropped, so a phrase wrapped across two lines or set
in bold is the same phrase; a phrase matches on word boundaries.

    usage: tools/check-claims.py [root]
           tools/check-claims.py --selftest
"""

from __future__ import annotations

import re
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path

TIER_1 = (
    "payload never leaves",
    "the payload never leaves the perimeter",
    "nothing leaves your machine",
    "nothing leaves the machine",
    "nothing ever leaves",
    "no data ever leaves",
    "data never leaves",
)

TIER_2 = (
    "no data leaves",
    "never leaves the perimeter",
    "never leaves your repository",
    "nothing is sent",
)

CALQUES = {
    "it": ("niente esce dalla tua macchina",),
    "de": ("nichts verlässt deinen rechner",),
    "es": ("nada sale de tu máquina",),
}

REGISTER = "tools/claims-register.toml"

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Claim:
    file: str
    quote: str
    anchor_path: str
    anchor_contains: str
    why: str
    since: str


def normalise(raw: str) -> tuple[str, list[int]]:
    """The text as the gate reads it, and the source line of each character."""
    out: list[str] = []
    lines: list[int] = []
    line, space = 1, False
    for char in raw:
        if char == "\n":
            line += 1
        if char.isspace():
            space = bool(out)
            continue
        if char == "*":
            continue
        if space:
            out.append(" ")
            lines.append(line)
            space = False
        for lowered in char.lower():
            out.append(lowered)
            lines.append(line)
    return "".join(out), lines


def pattern(phrase: str) -> re.Pattern[str]:
    return re.compile(r"\b" + re.escape(normalise(phrase)[0]) + r"\b")


def language(path: str) -> str | None:
    """The language a file is written in, when it is a translation."""
    parts = path.split("/")
    if parts[0] == "docs" and len(parts) > 2 and parts[1] in CALQUES:
        return parts[1]
    if parts[0] == "i18n" and len(parts) == 2 and parts[1].removesuffix(".yml") in CALQUES:
        return parts[1].removesuffix(".yml")
    return None


def covered(path: str) -> bool:
    parts = path.split("/")
    if parts[0] == "docs":
        return path.endswith(".md") and parts[1:2] != ["product"]
    return parts[0] == "i18n" and len(parts) == 2 and path.endswith(".yml")


def files(root: Path) -> list[str]:
    """What the gate reads, from the file system rather than from git: the
    pages a build would publish, whether or not they are committed yet."""
    found = []
    for base in ("docs", "i18n"):
        for path in sorted((root / base).rglob("*")):
            relative = path.relative_to(root).as_posix()
            if path.is_file() and covered(relative):
                found.append(relative)
    return found


def load_register(path: Path) -> list[Claim]:
    """Every field required: an entry without its anchor is the thing this
    gate exists to refuse."""
    with path.open("rb") as handle:
        document = tomllib.load(handle)
    claims = []
    for index, entry in enumerate(document.get("claim", []), start=1):
        where = f"{path.name}, claim {index}"
        anchor = entry.get("anchor")
        if not isinstance(anchor, dict):
            raise ValueError(f"{where}: `anchor` is missing")
        values = {}
        for key, table, name in (
            ("file", entry, "file"), ("quote", entry, "quote"),
            ("anchor_path", anchor, "path"), ("anchor_contains", anchor, "contains"),
            ("why", entry, "why"), ("since", entry, "since"),
        ):
            value = table.get(name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{where}: `{name}` is missing or empty")
            values[key] = value
        claims.append(Claim(**values))
    return claims


def read(root: Path, path: str) -> str | None:
    try:
        return (root / path).read_text(encoding="utf-8")
    except (FileNotFoundError, IsADirectoryError):
        return None


def check(root: Path, register: list[Claim]) -> list[str]:
    """Every problem, one line each, `path:line: what`. Empty is a pass."""
    problems = []
    for claim in register:
        where = f"{REGISTER}: {claim.file}"
        if not covered(claim.file):
            problems.append(f"{where}: this file is not read by the gate")
            continue
        raw = read(root, claim.file)
        if raw is None:
            problems.append(f"{where}: the file does not exist")
        elif normalise(claim.quote)[0] not in normalise(raw)[0]:
            problems.append(f"{where}: the quote is no longer there — {claim.quote!r}")
        evidence = read(root, claim.anchor_path)
        if evidence is None:
            problems.append(f"{where}: the anchor {claim.anchor_path} does not exist")
        elif claim.anchor_contains not in evidence:
            problems.append(f"{where}: the anchor {claim.anchor_path} no longer "
                            f"contains {claim.anchor_contains!r}")

    tier_1 = [(p, pattern(p)) for p in TIER_1]
    tier_2 = [(p, pattern(p)) for p in TIER_2]
    calques = {lang: [(p, pattern(p)) for p in phrases] for lang, phrases in CALQUES.items()}
    for path in files(root):
        text, lines = normalise(read(root, path) or "")
        for phrase, found in tier_1:
            for match in found.finditer(text):
                problems.append(f"{path}:{lines[match.start()]}: tier 1, {phrase!r} "
                                "is never admitted — rewrite it")
        lang = language(path)
        for phrase, found in calques.get(lang, []) if lang else []:
            for match in found.finditer(text):
                problems.append(f"{path}:{lines[match.start()]}: {phrase!r} is the "
                                "calque of 'nothing leaves your machine' — rewrite it")
        admitted = [
            (m.start(), m.end())
            for claim in register if claim.file == path
            for m in re.finditer(re.escape(normalise(claim.quote)[0]), text)
        ]
        for phrase, found in tier_2:
            for match in found.finditer(text):
                if not any(s <= match.start() and match.end() <= e for s, e in admitted):
                    problems.append(f"{path}:{lines[match.start()]}: tier 2, {phrase!r} "
                                    f"with no entry in {REGISTER} — rewrite it, or anchor it")
    return problems


def selftest() -> int:
    """Each refusal next to the case it must let through: a check that fails
    everything passes every "must fail", one that fails nothing passes every
    "must pass", and only the pair says it tells them apart."""
    evidence = ("overrides/partials/closing.html", "{% set nothing_sent = true %}\n")

    def claim(quote: str, file: str = "docs/why.md",
              contains: str = "{% set nothing_sent = true %}") -> Claim:
        return Claim(file, quote, evidence[0], contains, "the template", "selftest")

    cases: list[tuple[str, dict[str, str], list[Claim], bool]] = [
        ("tier 1 in a page fails",
         {"docs/why.md": "Nothing leaves\nyour **machine**.\n"}, [], False),
        ("the page without it passes",
         {"docs/why.md": "The CLI uploads nothing of its own.\n"}, [], True),
        ("tier 1 inside a registered quote still fails",
         {"docs/why.md": "The payload never leaves.\n"},
         [claim("The payload never leaves.")], False),
        ("a phrase inside a longer word does not match",
         {"docs/why.md": "Its metadata never leaves a trace.\n"}, [], True),
        ("tier 2 with no entry fails",
         {"docs/why.md": "Nothing is sent.\n"}, [], False),
        ("tier 2 with an anchored entry passes",
         {"docs/why.md": "- **Nothing is sent.** The page has no script.\n"},
         [claim("Nothing is sent. The page has no script.")], True),
        ("an entry covers its own file only",
         {"docs/why.md": "Nothing is sent.\n", "docs/about.md": "Nothing is sent.\n"},
         [claim("Nothing is sent.")], False),
        ("an entry whose quote is gone fails",
         {"docs/why.md": "The page has no script.\n"},
         [claim("Nothing is sent.")], False),
        ("an entry whose anchor lost its evidence fails",
         {"docs/why.md": "Nothing is sent.\n"},
         [claim("Nothing is sent.", contains="{% set nothing_sent = false %}")], False),
        ("an entry whose anchor file is gone fails",
         {"docs/why.md": "Nothing is sent.\n"},
         [Claim("docs/why.md", "Nothing is sent.", "overrides/gone.html", "x", "y", "z")],
         False),
        ("an entry for a file the gate does not read fails",
         {"docs/product/changelog.md": "Nothing is sent.\n"},
         [claim("Nothing is sent.", file="docs/product/changelog.md")], False),
        ("the synced changelog and ADRs are not read",
         {"docs/product/changelog.md": "The payload never leaves the perimeter.\n",
          "docs/product/adr/0002-the-three-worlds.md": "No data ever leaves.\n"}, [], True),
        ("the same sentence in a page of the site fails",
         {"docs/about.md": "The payload never leaves the perimeter.\n"}, [], False),
        ("the Italian calque in docs/it/ fails",
         {"docs/it/why.md": "- **Niente esce\n  dalla tua macchina.**\n"}, [], False),
        ("the German calque in docs/de/ fails",
         {"docs/de/why.md": "Nichts verlässt deinen Rechner.\n"}, [], False),
        ("the Spanish calque in i18n/es.yml fails",
         {"i18n/es.yml": "why:\n  lede: Nada sale de tu máquina.\n"}, [], False),
        ("an idiomatic translation passes",
         {"docs/it/why.md": "I dati restano nel tuo repository.\n",
          "docs/de/why.md": "Die Daten bleiben in deinem Repository.\n",
          "docs/es/why.md": "Los datos se quedan en tu repositorio.\n"}, [], True),
    ]

    failures = []
    for name, pages, register, passes in cases:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for path, text in {evidence[0]: evidence[1], **pages}.items():
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                (root / path).write_text(text, encoding="utf-8")
            (root / "docs").mkdir(exist_ok=True)
            (root / "i18n").mkdir(exist_ok=True)
            problems = check(root, register)
            if bool(problems) == passes:
                failures.append(f"{name}: got {problems or 'a pass'}")

    with tempfile.TemporaryDirectory() as tmp:
        broken = Path(tmp) / "register.toml"
        broken.write_text('[[claim]]\nfile = "docs/why.md"\nquote = "Nothing is sent."\n'
                          'why = "harmless"\nsince = "selftest"\n', encoding="utf-8")
        try:
            load_register(broken)
            failures.append("an entry with no anchor was loaded")
        except ValueError:
            pass

    if failures:
        for failure in failures:
            print(f"claims selftest: {failure}", file=sys.stderr)
        return 1
    print(f"claims selftest: {len(cases) + 1} cases, every refusal refused and every "
          "pass passed")
    return 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    if len(argv) > 1:
        print(__doc__, file=sys.stderr)
        return 2
    root = Path(argv[0]) if argv else ROOT
    problems = check(root, load_register(root / REGISTER))
    for problem in problems:
        print(problem, file=sys.stderr)
    if problems:
        return 1
    print(f"claims: {len(files(root))} files read, no claim the site cannot stand behind")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
