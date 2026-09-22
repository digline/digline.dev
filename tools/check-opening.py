#!/usr/bin/env -S uv run python
"""Every page opens on its lede, and the ones that do not say so by name.

`tools/hooks/opening.py` builds the opening band from the page's own Markdown:
the `# Title`, and the first paragraph under it as the lede. For the five
reading pages a missing paragraph already fails the build. For a documentation
page it does not — an ADR opens on its status list, and that is deliberate —
so a documentation page can lose its lede and the build stays green.

That is not hypothetical. The comparison index lost its band to an editorial
comment written under its `# H1`: invisible in the page, fatal to the pattern
that looks for the paragraph right after the title, and green through every
gate there was. `opening.py` skips comments in that seam now, so that
particular way is closed. This is the net under all the others — a paragraph
deleted, replaced by a list, turned into an image.

**The default is that a page has a lede**, and the exceptions are written
below with a reason each. The other direction — a list of the pages that must
have one — was considered and refused: a page added without a lede would
simply not be on it, so the gate would say nothing in the one case where
nobody has looked yet.

Five things it refuses, each next to the case it must let through:

  * a page with no lede that is not declared;
  * a declaration for a page that has one after all, which is a dead
    exception nobody can see is dead;
  * a declaration whose page is not in the build at all;
  * a build with no pages in it;
  * a build where nothing has a lede, which means the hook stopped running
    rather than that every page changed.

    usage: tools/check-opening.py site
           tools/check-opening.py --selftest

--selftest needs no build: it writes a small site by hand and plants each
failure in turn.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile

#: The pages that open without a lede, and why. A pattern for the ADR records,
#: which are one shape however many of them there are, and a line for each page
#: that is its own case. Removing a page from here is a diff a reviewer sees, which is the
#: whole point of writing it down rather than reading yesterday's build.
ALLOWED: dict[str, str] = {
    r"product/adr/\d{4}-[^/]+": (
        "a decision record opens on its status list — see tools/hooks/"
        "opening.py, which takes the title alone when no paragraph follows it"
    ),
    r"product/docker": (
        "the line under the title is `ghcr.io/digline/digline`, a lone <code> "
        "that labels the page rather than opening it"
    ),
    r"product/view": "the title is followed by a console block, not a paragraph",
    r"": "the home is overrides/home.html and has no Markdown at all",
    r"(it|de|es)": "a translated home, the same",
}

_ALLOWED = [(re.compile(rf"\A{pattern}\Z"), why) for pattern, why in ALLOWED.items()]

LEDE = re.compile(r'<p class="opening__lede">')

#: Built, but not a page of this site: Material's search stub and the 404.
SKIP = re.compile(r"\A(search|404)(/|\Z)")


def declared(url: str) -> str | None:
    """Why this page is allowed to have no lede, or None if it is not."""
    for pattern, why in _ALLOWED:
        if pattern.match(url):
            return why
    return None


def pages(site: str) -> list[tuple[str, str]]:
    """(url path, html) for every page in the build, deepest last."""
    found: list[tuple[str, str]] = []
    for dirpath, _, names in os.walk(site):
        if "index.html" not in names:
            continue
        url = os.path.relpath(dirpath, site).replace(os.sep, "/")
        url = "" if url == "." else url
        if SKIP.match(url):
            continue
        with open(os.path.join(dirpath, "index.html"), encoding="utf-8") as fh:
            found.append((url, fh.read()))
    return sorted(found)


def check(site: str) -> tuple[list[str], int, int]:
    """Problems, how many pages have a lede, how many are declared without."""
    problems: list[str] = []
    with_lede = 0
    seen_declared: set[str] = set()
    found = pages(site)
    if not found:
        problems.append(
            "the build has no pages in it, so this would hold nothing and pass"
        )
    for url, html in found:
        has = bool(LEDE.search(html))
        why = declared(url)
        if has:
            with_lede += 1
            if why is not None:
                problems.append(
                    f"/{url}/ has a lede and is declared as a page without one "
                    f"({why}). Take the declaration out: an exception nobody "
                    "can see is dead is one the next page inherits."
                )
            continue
        if why is None:
            problems.append(
                f"/{url}/ has no lede. A page opens on the first paragraph "
                "under its `# Title`; if one was removed, or a list, an image "
                "or a comment came between them, that is the regression. If "
                "the page is meant to open without one, add it to ALLOWED in "
                "this file with the reason."
            )
        else:
            seen_declared.add(url)
    if found and not with_lede:
        problems.append(
            "no page in the build has a lede, which is the hook having stopped "
            "rather than every page having changed on the same day"
        )
    for pattern, why in ALLOWED.items():
        if not any(re.match(rf"\A{pattern}\Z", url) for url in seen_declared):
            problems.append(
                f"nothing in the build matches the declaration {pattern!r} "
                f"({why}), so it holds nothing open and would let the next "
                "page that matches it through unread"
            )
    return problems, with_lede, len(seen_declared)


# ── the selftest ─────────────────────────────────────────────────────────────


def _site(root: str, pages_: dict[str, str]) -> str:
    """A site of `url -> html`, written under a fresh folder."""
    site = tempfile.mkdtemp(dir=root)
    for url, html in pages_.items():
        folder = os.path.join(site, *[p for p in url.split("/") if p])
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(html)
    return site


WITH = '<h1 class="opening__title">T</h1><p class="opening__lede">A line.</p>'
WITHOUT = '<h1 class="opening__title">T</h1><ul><li>Status: proposed</li></ul>'


def selftest() -> int:
    failures: list[str] = []

    def expect(label: str, actual: object, wanted: object) -> None:
        if actual != wanted:
            failures.append(f"{label}: {actual!r}, wanted {wanted!r}")

    def refused(label: str, problems: list[str], needle: str) -> None:
        if not problems:
            failures.append(f"{label}: accepted, which it exists to refuse")
        elif not any(needle in problem for problem in problems):
            failures.append(f"{label}: refused, but not for this: {problems}")
        else:
            print(f"opening-check selftest: refused, as it must — {label}")

    # Every declaration has to match something, so the whole set is present in
    # each of these sites; the case under test is the page added to them.
    base = {
        "product/adr/0001-verdict-not-score": WITHOUT,
        "product/docker": WITHOUT,
        "product/view": WITHOUT,
        "": WITHOUT,
        "it": WITHOUT,
        "de": WITHOUT,
        "es": WITHOUT,
    }

    with tempfile.TemporaryDirectory() as root:
        # 1. What must pass. A page with a lede, the declared pages without
        #    one, and a page that gains a lede it never had — nothing to
        #    declare, nothing to change.
        problems, with_lede, without = check(
            _site(root, {**base, "why": WITH, "handbook/01-what-you-are-shipping": WITH})
        )
        expect("a site where every undeclared page has a lede", problems, [])
        expect("pages counted with a lede", with_lede, 2)
        expect("pages declared without one", without, 7)

        # 2. A page that loses its lede. The ADR beside it is the control: the
        #    same absence, declared, and it passes in the same run.
        refused(
            "a page with no lede and no declaration",
            check(_site(root, {**base, "why": WITHOUT}))[0],
            "/why/ has no lede",
        )

        # 3. A declaration for a page that turned out to have one. The gate
        #    that only failed downwards would leave this behind for the next
        #    page to inherit.
        refused(
            "a declared page that has a lede after all",
            check(_site(root, {**base, "product/view": WITH, "why": WITH}))[0],
            "/product/view/ has a lede and is declared",
        )

        # 4. A declaration nothing in the build matches — the page renamed, the
        #    exception left behind.
        without_view = {k: v for k, v in base.items() if k != "product/view"}
        refused(
            "a declaration matching no page in the build",
            check(_site(root, {**without_view, "why": WITH}))[0],
            "product/view",
        )

        # 5. The two vacuous greens. A build with no pages, and a build where
        #    nothing has a lede — which is the hook having stopped rather than
        #    every page having changed on the same day.
        empty = check(_site(root, {}))[0]
        expect("an empty build is refused", bool(empty), True)
        allowed_only = check(_site(root, base))
        expect("a build where nothing has a lede is refused", bool(allowed_only[0]), True)

    for failure in failures:
        print(f"opening-check selftest: {failure}", file=sys.stderr)
    if failures:
        return 1
    print(
        "opening-check selftest: a page with a lede and the declared pages without one "
        "pass; a page that lost its lede, a declaration for a page that has one, a "
        "declaration matching no page, an empty build and a build with no lede anywhere "
        "are each refused"
    )
    return 0


def main(argv: list[str]) -> int:
    if argv == ["--selftest"]:
        return selftest()
    if len(argv) != 1:
        print(__doc__.split("usage:")[1].split("\n\n")[0], file=sys.stderr)
        return 2
    problems, with_lede, without = check(argv[0])
    for problem in problems:
        print(f"opening: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(
        f"opening: {with_lede + without} pages — {with_lede} open on their lede, "
        f"{without} declared to open without one"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
