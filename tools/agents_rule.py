#!/usr/bin/env python3
"""Rule 1 of digline's AGENTS.md, as the latest release has it.

/agents/ closes on a quotation of the first rule of AGENTS.md, written in
overrides/agents.html and not in the page's Markdown, so a translation never
touches it. The words are digline's, and they change there: so tools/sync-docs.sh
runs this against the checkout it copies from, and writes what it finds to
.agents-rule.json beside .lastmod.tsv — the release tag it read (the latest v*
tag the checkout's HEAD contains, not main), that tag's commit, and the rule's
text as AGENTS.md writes it. tools/hooks/sources.py reads the file back: it
points the page's links to AGENTS.md and to the skill at that tag, and fails
the build when the quotation on the page is not that text.

Standard library only: sync-docs.sh runs it with the system's python3, before
any environment exists.

A rule is a numbered level-2 heading, ``## 1. …`` — the shape digline's own
tests/test_agents.py reads — and rule 1's quotation is the blockquote that
opens it.

    usage: tools/agents_rule.py <digline checkout>      # JSON on stdout
           tools/agents_rule.py --selftest
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

RULE = re.compile(r"^## 1\. .*?$\n+((?:^>.*\n?)+)", re.M)


def extract(agents_md: str) -> str | None:
    """The blockquote under ``## 1.``, its lines joined, the ``>`` taken off; None when there is none."""
    found = RULE.search(agents_md)
    if not found:
        return None
    lines = [re.sub(r"^>\s?", "", line).strip() for line in found.group(1).splitlines()]
    text = " ".join(line for line in lines if line)
    return text or None


def git(src: str, *args: str) -> str:
    return subprocess.run(["git", "-C", src, *args], check=True, capture_output=True, text=True).stdout.strip()


def released(src: str) -> list[str]:
    return git(src, "tag", "--merged", "HEAD", "--list", "v*", "--sort=-v:refname").splitlines()


def deepen(src: str) -> bool:
    """Give a shallow checkout the history its tags have to be tested against.

    `--merged HEAD` walks from HEAD, and in a shallow clone that walk stops at
    the graft one commit down: the tags are all there and none of them is an
    ancestor of anything, so the checkout reads as a repository that never
    released. digline's CI checks itself out shallow for the docs job on
    purpose, so this is the ordinary shape here and not a broken clone.

    Deepening is the honest answer and not widening the refusal, because the
    question — which release does HEAD contain — has an answer that a shallow
    clone is merely unable to reach. Returns whether anything was deepened, so
    a checkout that was never shallow is not fetched twice.
    """
    if git(src, "rev-parse", "--is-shallow-repository") != "true":
        return False
    subprocess.run(["git", "-C", src, "fetch", "--quiet", "--tags", "--unshallow", "origin"],
                   check=False, capture_output=True, text=True)
    return True


def read(src: str) -> dict:
    tags = released(src)
    if not tags and deepen(src):
        # The clone was shallow, so the first reading was about the graft and
        # not about the history. This one is about the history.
        tags = released(src)
    if not tags:
        raise SystemExit(f"agents_rule: {src} contains no v* release tag: nothing released to quote")
    tag = tags[0]
    rule = extract(git(src, "show", f"{tag}:AGENTS.md") + "\n")
    if rule is None:
        raise SystemExit(f"agents_rule: AGENTS.md at {tag} has no `## 1.` rule opening on a blockquote")
    return {"source": "AGENTS.md", "tag": tag, "commit": git(src, "rev-parse", f"{tag}^{{commit}}"), "rule": rule}


def selftest() -> int:
    failures = []
    text = ("# Agents\n\nIntro.\n\n## 1. The prime rule: propose\n\n> **Never run `x`.** Assemble\n"
            "> the evidence — and recommend.\n\nMore.\n\n## 2. Another\n\n> Not this.\n")
    if extract(text) != "**Never run `x`.** Assemble the evidence — and recommend.":
        failures.append(f"rule 1: {extract(text)!r}")
    if extract(text.replace("## 1. ", "## One. ")) is not None:
        failures.append("no numbered rule 1: something extracted")
    if extract(text.replace("> **Never", "**Never").replace("> the evidence", "the evidence")) is not None:
        failures.append("rule 1 with no blockquote: something extracted")
    with tempfile.TemporaryDirectory() as tmp:
        # The shape digline's CI is in: checked out shallow on purpose, with the
        # tags fetched afterwards. Read from the graft alone it looks like a
        # repository that never released, which is the defect this covers.
        origin, clone = f"{tmp}/origin", f"{tmp}/clone"
        subprocess.run(["git", "init", "--quiet", "-b", "main", origin], check=True)
        Path(origin, "AGENTS.md").write_text(text, encoding="utf-8")
        for args in (["add", "AGENTS.md"], ["-c", "user.email=s@t", "-c", "user.name=s", "commit", "--quiet", "-m", "one"],
                     ["tag", "v0.1.0"], ["-c", "user.email=s@t", "-c", "user.name=s", "commit", "--quiet", "--allow-empty", "-m", "two"]):
            subprocess.run(["git", "-C", origin, *args], check=True, capture_output=True)
        subprocess.run(["git", "clone", "--quiet", "--depth", "1", "--no-tags", f"file://{origin}", clone], check=True)
        subprocess.run(["git", "-C", clone, "fetch", "--quiet", "--tags", "origin"], check=True)
        if git(clone, "rev-parse", "--is-shallow-repository") != "true":
            failures.append("the selftest's own clone is not shallow: it proves nothing")
        else:
            try:
                found = read(clone)["tag"]
            except SystemExit as refusal:
                found = f"refused: {refusal}"
            if found != "v0.1.0":
                failures.append(f"shallow clone: {found!r}, not the tag HEAD contains")

    for failure in failures:
        print(f"agents_rule selftest: FAILED — {failure}", file=sys.stderr)
    if not failures:
        print("agents_rule selftest: rule 1's blockquote read, nothing read without a rule 1 or its blockquote, "
              "and the release tag found in a shallow clone")
    return 1 if failures else 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        raise SystemExit(selftest())
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    print(json.dumps(read(sys.argv[1]), ensure_ascii=False, indent=2))
