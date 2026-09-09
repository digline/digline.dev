#!/usr/bin/env python3
"""Read the stylesheets in docs/assets/ and say whether a browser will get all
of them, or only the part before a mistake.

Nothing else in this repository looks at CSS. `mkdocs build --strict` fails on
a link that does not resolve, check-sitemap.py and check-llms.py read the two
generated indexes, and all three would pass a stylesheet that is entirely
comments: the files are copied byte for byte into site/ and never parsed. The
failure this exists to catch is the one that shows up only in a browser, on a
page nobody reloaded before deploying.

Two questions, and a non-zero exit on the first no:

  * does any rule have a } inside its selector? That is the whole signature of
    an unbalanced brace. A stray } at the top level is not an error to a CSS
    parser — it reads it as the start of a selector and swallows tokens up to
    the next {...}, so it produces one rule with a prelude no browser can match
    and silently drops whatever that rule was going to be. This is 60f655f: a
    second } after a media query cost .dg-foot its background and left the band
    at the foot of every page white, with light-grey links on it.

  * did the file keep at least the rules it had? FLOORS below is the count each
    file is known to reach, written down rather than derived, so a stylesheet
    that quietly collapses fails here. A real removal fails here too, and the
    number is lowered in the same commit that removes the rule — on purpose,
    where a reviewer sees it.

Neither question is about taste. Nothing here says a colour is wrong or a
selector is unused; it says the file a browser gets is the file that was
written.

    usage: tools/check-css.py [assets-dir]
           tools/check-css.py --selftest
"""

from __future__ import annotations

import os
import sys

import tinycss2

# What each file reaches today, counting every sound rule at every depth —
# media queries included. A file that drops below its number fails; lower the
# number in the commit that removes the rule.
FLOORS = {
    "chrome.css": 56,
    "pages.css": 32,
    "theme.css": 27,
    "tokens.css": 6,
}

# At-rules whose body is more rules rather than declarations, and so is worth
# descending into. @font-face and the like hold declarations and are counted as
# one rule each, which is what they are.
NESTING = {"media", "supports", "layer", "container"}


def walk(rules):
    """Every rule in a parsed stylesheet, flattened — the ones inside media
    queries included, because that is where a brace is easiest to lose."""
    for rule in rules:
        yield rule
        if rule.type == "at-rule" and rule.lower_at_keyword in NESTING and rule.content:
            yield from walk(
                tinycss2.parse_rule_list(
                    rule.content, skip_whitespace=True, skip_comments=True
                )
            )


def unmatched(rule):
    """The unmatched closing braces in this rule's selector, if any.

    tinycss2 hands a stray } inside a prelude back as a ParseError token —
    kind '}', message 'Unmatched }' — rather than as a literal, which is
    exactly the distinction wanted: a } written inside a string or an
    attribute selector, [data-x="}"], tokenises as part of that string and
    never appears here. So this asks the tokeniser rather than the text."""
    if rule.type != "qualified-rule":
        return []
    return [t for t in rule.prelude if t.type == "error"]


def check(path: str, require_floor: bool = True) -> list[str]:
    name = os.path.basename(path)
    errors: list[str] = []

    with open(path, encoding="utf-8") as f:
        source = f.read()
    rules = tinycss2.parse_stylesheet(source, skip_whitespace=True, skip_comments=True)

    sound = 0
    for rule in walk(rules):
        if rule.type == "error":
            errors.append(f"{name}:{rule.source_line}: {rule.message}")
            continue
        broken = unmatched(rule)
        if broken:
            selector = " ".join(tinycss2.serialize(rule.prelude).split())
            first = broken[0]
            errors.append(
                f"{name}:{first.source_line}: {first.message} in a selector — "
                f"an unbalanced brace at or above this line. The rule a browser "
                f"builds here is {selector!r}, which matches nothing, so every "
                f"declaration in it is dropped."
            )
            continue
        sound += 1

    floor = FLOORS.get(name)
    if floor is None:
        if require_floor:
            errors.append(
                f"{name}: no floor in FLOORS. Add one — the count today is {sound}."
            )
    elif sound < floor:
        errors.append(
            f"{name}: {sound} sound rules, floor is {floor}. Either a brace "
            f"swallowed some, or rules were removed on purpose and the floor "
            f"should come down in the same commit."
        )

    return errors


def main(assets: str) -> int:
    if not os.path.isdir(assets):
        print(f"no stylesheets at {assets}", file=sys.stderr)
        return 1

    files = sorted(
        os.path.join(assets, name)
        for name in os.listdir(assets)
        if name.endswith(".css")
    )
    if not files:
        print(f"no stylesheets in {assets}", file=sys.stderr)
        return 1

    errors: list[str] = []
    for path in files:
        errors.extend(check(path))

    for error in errors:
        print(f"error: {error}", file=sys.stderr)
    if errors:
        return 1

    print(f"css: {len(files)} stylesheets, every rule a browser can read")
    return 0


def selftest() -> int:
    """The check against the file that made it necessary. tools/testdata holds
    chrome.css exactly as 60f655f left it; if that no longer fails, this script
    has stopped doing the one thing it was written for."""
    here = os.path.dirname(os.path.abspath(__file__))
    broken = os.path.join(here, "testdata", "chrome-60f655f.css")

    errors = check(broken, require_floor=False)
    strays = [e for e in errors if "in a selector" in e]
    if not strays:
        print(
            "selftest: check-css.py passes the broken chrome.css from 60f655f, "
            "which it exists to fail",
            file=sys.stderr,
        )
        return 1

    print("selftest: the stylesheet from 60f655f fails, as it must —")
    for error in strays:
        print(f"  {error}")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--selftest":
        raise SystemExit(selftest())
    raise SystemExit(main(args[0] if args else "docs/assets"))
