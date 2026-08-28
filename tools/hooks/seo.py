"""What search engines are given, for every page of the site.

Three things, in one place because they answer the same question — what is this
page, and when did it last change:

  * ``seo_title``   the whole of ``<title>``, built as "<topic> — digline"
  * ``description`` the ``<meta name="description">`` and the OG/Twitter one
  * ``page.update_date``  the ``<lastmod>`` mkdocs writes into sitemap.xml

The templates that consume them are ``overrides/partials/seo.html`` (Open Graph
and Twitter, included from both sides of the site) and the two title blocks in
``overrides/main.html`` and ``overrides/_shell.html``.

Where the copy comes from, first match wins:

  1. the page's own front matter — ``seo_title:`` and ``description:``. This is
     the normal place for the pages written in this repository.
  2. the ``PRODUCT`` table below, for the pages under ``product/``. Those files
     are copied out of digline/digline by tools/sync-docs.sh before every build
     and are never edited here, so their copy has to live somewhere that
     survives the copy. This is that somewhere.
  3. the first paragraph of the page, trimmed to a sentence boundary. Nothing
     is invented: a page digline/digline adds tomorrow still reaches the site
     with a description of its own, and it is the page's own opening line.

Everything is HTML-escaped once, here, because mkdocs renders templates with
autoescape off and Material's base.html prints ``page.meta.description`` raw.
The templates in overrides/ print these values raw for the same reason.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import subprocess

# The brand as it is written everywhere else: the wordmark, `pip install
# digline`, site_name, the repository. Lower case. One constant, so that a
# decision to capitalise it in titles is one edit and not thirty.
BRAND = "digline"

# The person behind it, for the JSON-LD below. The name that a query for
# "digline" has to be able to reach, and the one thing on the site that the
# Idaho utility company of the same name cannot also claim.
AUTHOR = "Alessandro Prandini"

REPO_URL = "https://github.com/digline/digline"
PYPI_URL = "https://pypi.org/project/digline/"
LICENSE_URL = "https://www.apache.org/licenses/LICENSE-2.0"

def _jsonld(description: str, config) -> str:
    """The one structured-data block on the site, on the home page only.

    It is data, not behaviour: nothing in it runs, nothing is fetched, and a
    reader with script blocked loses nothing — which is why it can be here at
    all. What it is for is the name: "digline" belongs to an unrelated company
    with a decade of links behind it, and the only way to be a second, distinct
    thing rather than a weaker copy of the first is to say plainly what this one
    is — a developer tool, at this URL, under this licence, by this person, with
    its source there and its package there.

    Everything below is stated somewhere else on the site already. No ratings,
    no offers, no counts: a field that cannot be checked against the rest of the
    site is a field that should not be here.
    """
    data = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": BRAND,
        "url": (config["site_url"] or "").rstrip("/"),
        "applicationCategory": "DeveloperApplication",
        "description": description,
        "license": LICENSE_URL,
        "author": {"@type": "Person", "name": AUTHOR},
        "sameAs": [REPO_URL, PYPI_URL],
    }
    # `</` cannot appear inside a <script> block whatever it is quoting, and
    # `\/` is a JSON escape for `/`, so this is a change of spelling and not of
    # value. Nothing in `data` contains it today; the day someone writes an
    # angle bracket into a description is not the day to find out.
    return json.dumps(data, ensure_ascii=False, indent=2).replace("</", "<\\/")


def _attr(value: str) -> str:
    """Escape for an HTML attribute, and only as far as that needs.

    `html.escape` also turns every apostrophe into `&#x27;`, which is correct
    and unreadable — these strings are half prose and they are read in view
    source. The values only ever land in double-quoted attributes and in
    `<title>`, so four characters is the whole of it.
    """
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

# The social image. It already exists in the repository (docs/assets/) and is
# the wordmark over the navy, with the product's own sentence under it.
OG_IMAGE = "assets/digline-wordmark.png"
OG_IMAGE_SIZE = (1800, 440)
OG_IMAGE_ALT = "digline — regression testing for LLM applications"

# The pages copied in from digline/digline. Keyed by the path under docs/.
PRODUCT: dict[str, tuple[str, str]] = {
    "product/guide.md": (
        "Guide",
        "Working with digline in eight chapters, in the order the problems "
        "arrive: a baseline, the judge's noise, sampling, thresholds, and the "
        "comparison in CI.",
    ),
    "product/metrics.md": (
        "Metrics",
        "One card per assertion and per aggregate: when to reach for it, what "
        "it takes, what it produces, and what it will do to you if you are not "
        "looking.",
    ),
    "product/api.md": (
        "Public API",
        "Reference for writing a digline suite: what digline.core and "
        "digline.run export, the Judge protocols, and the verdict an assertion "
        "returns.",
    ),
    "product/view.md": (
        "digline view",
        "The local browser UI over .digline/: four screens on your runs, the "
        "baseline and the comparison. Stdlib only, no JavaScript, no state of "
        "its own.",
    ),
    "product/migrate.md": (
        "digline migrate",
        "Bring the stored runs and the baseline of a suite up to the schema "
        "version this release reads, and what a scan does with a document it "
        "cannot read.",
    ),
    "product/roadmap.md": (
        "Roadmap",
        "Where digline goes next: tracks and gates rather than dates, and the "
        "two things that will never be on it — a hosted service that takes "
        "your payloads, and usage data.",
    ),
    "product/changelog.md": (
        "Changelog",
        "What changed for you in each release of digline, three lines a "
        "version. The reasoning behind the changes lives in the decision "
        "records.",
    ),
    "product/adr/index.md": (
        "Decisions",
        "Why digline is shaped the way it is: one architecture decision record "
        "per decision, in the order they were taken, superseded ones kept and "
        "marked.",
    ),
    "product/adr/0001-verdict-not-score.md": (
        "ADR 0001: Verdict, not score",
        "Why an assertion produces a three-state verdict rather than a bare "
        "score, and why the comparison against the baseline lives in the core.",
    ),
    "product/adr/0002-three-worlds-and-where-the-data-lives.md": (
        "ADR 0002: Three worlds, and where the data lives",
        "Developer, consultancy and customer want different things from the "
        "same runs. Where each kind of data lives, so that no customer's "
        "payload leaves its own world.",
    ),
    "product/adr/0003-artifacts-travel-only-when-the-suite-says-so.md": (
        "ADR 0003: Artifacts travel only when the suite says so",
        "A run records the verdicts and the commit, but not the prompt that "
        "produced them. Why digline stores the files under test, and only the "
        "ones the suite names.",
    ),
    "product/adr/0004-every-plugin-is-a-target-and-a-judge.md": (
        "ADR 0004: Every plugin is a target and a judge",
        "digline.core declares the Judge protocols and implements none. Why "
        "every provider plugin ships both sides: the system under test and the "
        "judge that evaluates it.",
    ),
    "product/adr/0005-the-configuration-of-the-system-under-test.md": (
        "ADR 0005: The configuration of the system under test",
        "Proposed, nothing implemented: a run records the fingerprint of its "
        "configuration but not which model answered, at what temperature, "
        "under what token cap.",
    ),
    "product/examples/prompt-first.md": (
        "Example: a prompt, no application yet",
        "A prompt, five cases and two checks: enough to tell whether an edit "
        "made the answers better or only different, before there is an "
        "application around it.",
    ),
    "product/examples/classifier.md": (
        "Example: a classifier",
        "Keeping an LLM classifier under control: five samples per case and a "
        "majority, precision over the whole set as the gate, thresholds "
        "measured rather than chosen.",
    ),
    "product/examples/rag.md": (
        "Example: a RAG",
        "Checking that a RAG does not make things up: the passages frozen into "
        "each case so the generator is what is measured, and faithfulness "
        "counted rather than scored.",
    ),
    "product/examples/external-app.md": (
        "Example: an application digline cannot import",
        "Your service is Java, Go or a shell script behind nc: digline needs a "
        "body it can post and a field it can read back, so what produced the "
        "answer is not its business.",
    ),
}


# ── the description of last resort ───────────────────────────────────────────
# The page's own first paragraph, which is the one sentence its author wrote to
# say what the page is. Nothing here rewrites it; it is cut at a sentence.

_FENCE = re.compile(r"^(```|~~~)")
_MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
# Backticks, asterisks and the marks that open a line. Not the underscore: it
# is emphasis far less often than it is part of a name, and `config_hash`
# arriving as "confighash" is worse than a stray one getting through.
_MD_MARK = re.compile(r"[*`>#]+")
_HTML_COMMENT = re.compile(r"<!--.*?-->", re.S)
_TAG = re.compile(r"<[^>]+>")
_SPACE = re.compile(r"\s+")

LIMIT = 165  # where Google stops reading, near enough


def _lead(markdown: str) -> str:
    text = _HTML_COMMENT.sub("", markdown)
    lines = text.splitlines()
    para: list[str] = []
    seen_heading = False
    fenced = False
    for line in lines:
        stripped = line.strip()
        if _FENCE.match(stripped):
            # A page can open with a console block — `digline view` does. Step
            # over it and keep looking for the prose, unless prose has already
            # been found, in which case the block is what ends it.
            if para:
                break
            fenced = not fenced
            continue
        if fenced:
            continue
        if stripped.startswith("#"):
            seen_heading = True
            continue
        if not stripped:
            if para:
                break
            continue
        # Front matter, tables, lists, admonitions and block quotes are not
        # prose; the first paragraph is what is wanted, not the first line.
        if stripped[0] in "-|!>:" or stripped.startswith("---"):
            if para:
                break
            continue
        if not seen_heading and not para:
            continue
        para.append(stripped)

    sentence = _SPACE.sub(" ", " ".join(para)).strip()
    sentence = _MD_LINK.sub(r"\1", sentence)
    sentence = _TAG.sub("", sentence)
    sentence = _MD_MARK.sub("", sentence)
    sentence = _SPACE.sub(" ", sentence).strip()

    if len(sentence) <= LIMIT:
        return sentence
    cut = sentence[:LIMIT]
    stop = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    if stop > 60:
        return cut[: stop + 1]
    return cut[: cut.rfind(" ")].rstrip(",;:—-") + "…"


# ── when the page last changed ───────────────────────────────────────────────
# <lastmod> is only worth writing if it is true. The date of the commit that
# last touched the file is the closest thing to the truth there is, and it is
# stable: rebuilding the site on Friday does not make every page Friday's.
#
#   * pages written here      → git log in this repository
#   * pages under product/    → git log in digline/digline, read out of the
#                               manifest tools/sync-docs.sh leaves behind
#   * anything else           → the file's own mtime
#
# Both lookups need real history. The workflow checks both repositories out
# with fetch-depth: 0 for this reason; a shallow clone would date every page
# the same day and the sitemap would be lying in a new way.

MANIFEST = ".lastmod.tsv"


def _git_dates(root: str, *paths: str) -> dict[str, str]:
    """{path relative to root: YYYY-MM-DD of the commit that last touched it}."""
    try:
        out = subprocess.run(
            ["git", "-C", root, "log", "--format=%x01%cs", "--name-only", "--", *paths],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    if out.returncode != 0:
        return {}

    dates: dict[str, str] = {}
    date = ""
    for line in out.stdout.splitlines():
        if line.startswith("\x01"):
            date = line[1:].strip()
        elif line.strip() and date:
            # git log walks newest first, so the first time a path appears is
            # the last time it was touched.
            dates.setdefault(line.strip(), date)
    return dates


class _Dates:
    def __init__(self, config) -> None:
        self.repo = os.path.dirname(os.path.abspath(config["config_file_path"]))
        self.docs_dir = config["docs_dir"]
        rel = os.path.relpath(self.docs_dir, self.repo)
        # docs/ for the pages, overrides/ because a presentation page is its
        # template — see `of()`.
        self.git = _git_dates(self.repo, rel, "overrides")
        self.prefix = rel.replace(os.sep, "/").rstrip("/") + "/"
        self.product = self._manifest()

    def _manifest(self) -> dict[str, str]:
        path = os.path.join(self.repo, MANIFEST)
        out: dict[str, str] = {}
        try:
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    src, _, date = line.rstrip("\n").partition("\t")
                    if src and date:
                        out[src] = date
        except OSError:
            pass
        return out

    def of(self, page) -> str:
        src_uri = page.file.src_uri
        best = self.product.get(src_uri) or self.git.get(self.prefix + src_uri)

        # A presentation page is its template: docs/index.md is a stub, and the
        # words on the landing live in overrides/home.html. Whichever of the two
        # moved last is when the page changed.
        template = (page.meta or {}).get("template")
        if template:
            for d in self._template_dirs():
                cand = os.path.join(d, template)
                rel = os.path.relpath(cand, self.repo).replace(os.sep, "/")
                if rel in self.git:
                    best = max(best or "", self.git[rel])
                    break

        if best:
            return best
        try:
            mtime = os.path.getmtime(page.file.abs_src_path)
        except OSError:
            return datetime.date.today().isoformat()
        return datetime.date.fromtimestamp(mtime).isoformat()

    def _template_dirs(self) -> list[str]:
        return [os.path.join(self.repo, "overrides")]


_dates: _Dates | None = None
_leads: dict[str, str] = {}


# ── the hooks mkdocs calls ───────────────────────────────────────────────────


def on_config(config, **kwargs):
    global _dates, _leads
    _dates = _Dates(config)
    _leads = {}
    # The git log for the whole tree is one subprocess, run once. If it came
    # back empty the history is shallow or absent and every date will fall back
    # to an mtime — worth saying out loud rather than shipping a flat sitemap.
    if not _dates.git and not _dates.product:
        import logging

        logging.getLogger("mkdocs.hooks.seo").warning(
            "seo: no git history and no %s — <lastmod> will fall back to file "
            "mtimes",
            MANIFEST,
        )
    return config


def on_page_markdown(markdown, page, config, files, **kwargs):
    # Kept for on_page_content, which runs once page.title exists but no longer
    # has the source in hand.
    _leads[page.file.src_uri] = markdown
    return markdown


def on_page_content(html_content, page, config, files, **kwargs):
    """Everything is decided here, and here rather than in on_page_context.

    mkdocs writes sitemap.xml before it renders a single page, so a
    `page.update_date` set at page-context time would arrive after the sitemap
    was already on disk. This event is the last one in the read-everything
    phase, which is also the first point at which `page.title` — the h1 of the
    page, for the pages that do not declare one — exists.
    """
    meta = page.meta if page.meta is not None else {}
    src_uri = page.file.src_uri
    topic, described = PRODUCT.get(src_uri, (None, None))

    description = (
        meta.get("description")
        or described
        or _lead(_leads.get(src_uri, ""))
        or config["site_description"]
    )
    description = _SPACE.sub(" ", str(description)).strip()

    title = meta.get("seo_title") or topic or page.title or config["site_name"]
    title = _SPACE.sub(" ", str(title)).strip()

    # "<topic> — digline", except where the topic already opens with the name:
    # the landing ("digline — catch LLM quality regressions…") and the two
    # command pages ("digline view", "digline migrate"), which would otherwise
    # come out saying it twice.
    lead_word = title.split(" ", 1)[0].strip(":—,").lower()
    full = title if lead_word == BRAND else f"{title} — {BRAND}"

    site_url = (config["site_url"] or "").rstrip("/") + "/"
    meta["seo_title"] = _attr(full)
    meta["description"] = _attr(description)
    meta["og_image"] = site_url + OG_IMAGE
    meta["og_image_width"] = str(OG_IMAGE_SIZE[0])
    meta["og_image_height"] = str(OG_IMAGE_SIZE[1])
    meta["og_image_alt"] = _attr(OG_IMAGE_ALT)
    meta["og_type"] = "website" if page.is_homepage else "article"

    # One page carries it, and it is the page the name is about. Repeating the
    # same node on all twenty-nine says nothing the first one did not.
    if page.is_homepage:
        meta["jsonld"] = _jsonld(description, config)
    page.meta = meta

    assert _dates is not None
    page.update_date = _dates.of(page)
    return html_content
