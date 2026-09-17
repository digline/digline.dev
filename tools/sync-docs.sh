#!/usr/bin/env bash
# Copy the product documentation out of digline/digline into docs/product/.
#
# Nothing under docs/product/ is committed here: this script is the only thing
# that puts it there, and it runs before every build, locally and in CI. The
# rewrites at the bottom exist because the files are written to be read on
# GitHub, where they sit one directory deeper than they do on the site.
#
# Before it copies anything it checks that the checkout it is copying from is
# published — committed, and level with origin/main. See "the source has to be
# what everyone else can see" below for why, and for the one way out.
#
#   usage: tools/sync-docs.sh [path-to-digline-checkout]
#          SYNC_UNRELEASED=1 tools/sync-docs.sh [path]   # preview, never shipped
set -euo pipefail

src="${1:-../digline}"
here="$(cd "$(dirname "$0")/.." && pwd)"
out="$here/docs/product"

[ -d "$src/docs" ] || { echo "no docs/ in $src — is that a digline checkout?" >&2; exit 1; }

# ── the source has to be what everyone else can see ──────────────────────────
#
# Everything below copies files out of `$src` into a build that ships. A file
# that exists only in somebody's working tree — uncommitted, or committed and
# never pushed — builds green here and red for everyone else, and the way that
# gets found out is a nav entry whose page digline main does not have, stopping
# every release of the site including the ones digline dispatches itself.
#
# It happened. `docs/log.md` and `docs/register.md` were copied out of a
# checkout five commits ahead of `origin/main`; the three entries written
# against them were green locally and had to come back out of `main`.
#
# So, before a single file is copied, two questions about `$src`:
#
#   1. is everything this script reads committed?
#   2. is HEAD level with `origin/main`, freshly fetched?
#
# A checkout *behind* `origin/main` is refused as well — it would date and
# describe the pages by a history that has moved on — with one exception: a
# detached HEAD sitting exactly on the latest `v*` tag `origin/main` contains.
# That is the shape CI is in on a release dispatch, where `_digline` is checked
# out at the tag that was just published rather than at the tip of the branch.
# Not any tag, and not any commit main contains: an older release would put the
# documentation of a version nobody installs any more on the site, and a
# commit with no tag is documentation of nothing that was released at all.
# Ahead is refused in every shape there is: those are the commits nobody else
# has.
#
# SYNC_UNRELEASED=1 turns all of it off, for a local look at a page that is not
# released yet. It leaves a marker behind, and tools/check-source.sh — in
# `make build` and in the workflow — refuses to ship a build that has one.

marker="$here/.sync-preview"

# An argument may itself be several lines — a `git log`, a `git status` — so the
# indent is put on at the end, over the whole message, rather than by the loop.
# Otherwise only the first line of such an argument lines up with the rest.
refuse() {
  {
    echo
    echo "sync refused — $1"
    echo
    shift
    for line in "$@"; do echo "$line"; done
    echo
    echo "How to proceed:"
    echo
    echo "  · build against a clone pinned to what everyone else can see:"
    echo "      git clone https://github.com/digline/digline /tmp/digline"
    echo "      make build DIGLINE=/tmp/digline"
    echo
    echo "  · or, to look at a page that is not released yet — locally only:"
    echo "      make preview                  # or SYNC_UNRELEASED=1 make serve"
    echo "    That build carries a marker and the deploy gate refuses it."
    echo
  } | sed 's/^./  &/' >&2
  exit 1
}

if [ -n "${SYNC_UNRELEASED:-}" ]; then
  head_sha="$(git -C "$src" rev-parse --short HEAD 2>/dev/null || echo 'not a git checkout')"
  {
    echo
    echo "  ############################################################"
    echo "  ##  UNRELEASED SYNC — THIS BUILD MUST NOT BE DEPLOYED      ##"
    echo "  ############################################################"
    echo
    echo "  SYNC_UNRELEASED=1: docs/product/ is being copied out of"
    echo "    $src (at $head_sha)"
    echo "  without checking that digline main has any of it."
    echo
    echo "  Pages that are not on digline main may appear. tools/check-source.sh"
    echo "  refuses this build, so \`make build\` and the workflow will not ship it."
    echo
  } >&2
  {
    echo "This build is an unreleased preview and must not be deployed."
    echo "source: $src"
    echo "head:   $head_sha"
    echo "made:   $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  } > "$marker"
else
  rm -f "$marker"

  git -C "$src" rev-parse --git-dir >/dev/null 2>&1 ||
    refuse "$src is not a git checkout" \
           "There is no history to check it against, so nothing here can tell" \
           "whether what it holds is published."

  # 1. Everything this script reads, committed. Only those paths: digline is a
  #    workspace and its src/ changes constantly, which is none of our business.
  dirty="$(git -C "$src" status --porcelain -- docs examples docker CHANGELOG.md ROADMAP.md)"
  if [ -n "$dirty" ]; then
    refuse "uncommitted changes in $src, under what this script copies" \
           "$(echo "$dirty" | sed 's/^/    /')" \
           "" \
           "Those files would reach the site from a working tree and nowhere else."
  fi

  # 2. Level with origin/main, and fetched rather than remembered.
  #
  #    `fetch origin main` rather than `fetch origin`: it sets FETCH_HEAD even
  #    where refs/remotes/origin/main is not how the checkout is arranged, which
  #    is the case in more CI checkouts than one would like to bet on. The
  #    remote-tracking ref is used when it is there and FETCH_HEAD when it is
  #    not; both are the same commit.
  git -C "$src" fetch --quiet origin main 2>/dev/null ||
    refuse "cannot fetch origin/main in $src" \
           "The check needs origin/main as it is now, not as it was last" \
           "fetched. Check the network, or the remote named origin."

  main_sha="$(git -C "$src" rev-parse --verify --quiet origin/main ||
              git -C "$src" rev-parse --verify --quiet FETCH_HEAD || true)"
  [ -n "$main_sha" ] ||
    refuse "no origin/main in $src" \
           "Nothing to compare HEAD with."

  ahead="$(git -C "$src" rev-list --count "$main_sha..HEAD")"
  behind="$(git -C "$src" rev-list --count "HEAD..$main_sha")"
  head_sha="$(git -C "$src" rev-parse --short HEAD)"
  main_sha="$(git -C "$src" rev-parse --short "$main_sha")"

  if [ "$ahead" -gt 0 ]; then
    refuse "$src is $ahead commit(s) ahead of origin/main" \
           "HEAD        $head_sha" \
           "origin/main $main_sha" \
           "" \
           "$(git -C "$src" log --oneline "$main_sha..HEAD" | sed 's/^/    /')" \
           "" \
           "Those commits are on nobody else's clock. A page that arrives with" \
           "them builds green here and is missing from every other build."
  fi

  if [ "$behind" -gt 0 ]; then
    if git -C "$src" symbolic-ref -q HEAD >/dev/null; then
      refuse "$src is $behind commit(s) behind origin/main" \
             "HEAD        $head_sha  ($(git -C "$src" rev-parse --abbrev-ref HEAD))" \
             "origin/main $main_sha" \
             "" \
             "Pull it. The pages would otherwise be dated and described by a" \
             "history that has moved on."
    fi

    # Detached and behind: only the release that is current. The tags are
    # fetched here and not earlier because this is the only case that reads
    # them, and a clone made before the release has not got the tag yet.
    git -C "$src" fetch --quiet --tags origin 2>/dev/null ||
      refuse "cannot fetch the tags of origin in $src" \
             "A detached HEAD passes only on the latest release tag, and the" \
             "tags have to be the ones origin has now to say which that is."

    tag="$(git -C "$src" describe --exact-match --tags --match 'v*' HEAD 2>/dev/null || true)"
    latest="$(git -C "$src" tag --merged "$main_sha" --list 'v*' --sort=-v:refname | head -1)"
    if [ -n "$latest" ]; then
      latest_sha="$(git -C "$src" rev-parse --short "$latest^{commit}")"
      latest_desc="$latest ($latest_sha)"
    else
      latest_sha=""
      latest_desc="none — origin/main contains no v* tag"
    fi

    if [ -z "$tag" ]; then
      refuse "$src is detached at $head_sha, $behind commit(s) behind origin/main, on no release tag" \
             "HEAD                 $head_sha  (no v* tag on this commit)" \
             "origin/main          $main_sha" \
             "latest release tag   $latest_desc" \
             "" \
             "A detached checkout passes only on the latest release. A commit" \
             "that was never tagged is documentation of nothing anyone installed."
    fi

    if [ "$(git -C "$src" rev-parse --short HEAD)" != "$latest_sha" ]; then
      refuse "$src is detached at $tag, which is not the latest release" \
             "HEAD                 $head_sha  ($tag)" \
             "origin/main          $main_sha" \
             "latest release tag   $latest_desc" \
             "" \
             "The site documents the version people install. Check out $latest," \
             "or origin/main, and sync again."
    fi

    echo "sync: $src is the latest release, $tag ($head_sha), $behind commit(s) behind origin/main ($main_sha)" >&2
  else
    echo "sync: $src is level with origin/main, $head_sha" >&2
  fi
fi

rm -rf "$out"
mkdir -p "$out/examples"

cp -R "$src/docs/." "$out/"

# A README that accompanies an asset is not a page. `docs/assets/` holds images
# and the note that explains how one was made — read in a checkout by whoever
# edits the SVG, never by anyone on the site — and `cp -R` cannot tell the two
# apart. mkdocs can: a file that lands in the tree with no entry in `nav` is a
# warning, and `--strict` makes it a failed build. In `publish.yml` that build
# runs *after* PyPI, so the first sighting would be a version already spent.
#
# By pattern and not by name. The one that arrived was `assets/flow/README.md`;
# the next asset with a note beside it would fail the same build for the same
# reason, and a rule naming one file closes only the instance it met.
find "$out/assets" -name 'README.md' -type f -delete 2>/dev/null || true

# Two files live at the root of the repository rather than in its docs/, because
# that is where a reader arriving on GitHub looks for them. They are pages here.
cp "$src/CHANGELOG.md" "$out/changelog.md"
cp "$src/ROADMAP.md"   "$out/roadmap.md"

# The image's own page, which lives beside the Dockerfile it documents rather
# than in docs/: it is read on GitHub by whoever is editing the image, and it
# is the reference page for whoever is only running it.
cp "$src/docker/README.md" "$out/docker.md"

# One page per example, named after the directory it came from. quickstart has
# no README — it is the guide's first chapter, not a case of its own.
for readme in "$src"/examples/*/README.md; do
  name="$(basename "$(dirname "$readme")")"
  cp "$readme" "$out/examples/$name.md"
done

# A landing page for the decisions, built from what is actually there, so that
# the section has a page and `](adr/)` in the guide has somewhere to land.
{
  echo "# Decisions"
  echo
  echo "Why digline is shaped the way it is. One record per decision, in the"
  echo "order they were numbered; superseded ones stay, marked."
  echo
  # The table — number, title, status, date — is filled at build time by
  # tools/hooks/indexes.py, which reads each record and fails the build on one
  # that does not say all four.
  echo "<!-- decisions: the table is filled by tools/hooks/indexes.py, from the records. -->"
} > "$out/adr/index.md"

# Links that are correct in the repository and wrong on the site.
perl -pi -e 's{\]\(\.\./README\.md\)}{](https://github.com/digline/digline#readme)}g' "$out"/*.md "$out"/adr/*.md
perl -pi -e 's{\]\(adr/\)}{](adr/index.md)}g'                                        "$out"/*.md
perl -pi -e 's{\]\(docs/adr/\)}{](adr/index.md)}g'                                   "$out/changelog.md"

# AGENTS.md is at the root of the other repository and is not a page here: it is
# a file an agent reads in a checkout, not documentation about the product. It
# is linked from docs/ and from an ADR, so from two depths.
perl -pi -e 's{\]\((?:\.\./)+AGENTS\.md\)}{](https://github.com/digline/digline/blob/main/AGENTS.md)}g' \
  "$out"/*.md "$out"/adr/*.md

# The two files that live at the root of the repository reach the documentation
# by path — `](docs/mcp.md)`, `](docs/adr/0011-....md)` — which is right where
# they are read on GitHub. Here they are siblings of what they link to. Must
# come after the `](docs/adr/)` line above, which would otherwise be left
# pointing at a directory.
perl -pi -e 's{\]\(docs/}{](}g'                                                       "$out/changelog.md" "$out/roadmap.md"

# The pages under product/ that are written here rather than copied in.
#
# A page about how digline is *used* rather than about what it does — the
# operator loop is the first — has no home in the other repository's docs/, but
# its URL belongs under product/, beside everything it links to. So the source
# is committed in pages/product/ and installed here.
#
# After the rewrites above, deliberately: those correct links that are right in
# a repository and wrong on the site, and a page written here is already
# written for the site. It has nothing to correct.
#
# This is also what keeps docs/product/ entirely generated, which is the whole
# reason the `rm -rf` above and `make clean` can be as blunt as they are.
native="$here/pages/product"
#
# Folders are kept: pages/product/examples/index.md becomes product/examples/,
# the index of the pages copied in above.
find "$native" -name '*.md' -type f | while read -r page; do
  rel="${page#"$native"/}"
  mkdir -p "$out/$(dirname "$rel")"
  cp "$page" "$out/$rel"
done

# The dates the sitemap needs.
#
# `cp` gives every file the time it was copied, which would make <lastmod> say
# "today" for the whole of product/ on every build. The dates that are true are
# in the other repository's history, and this is the only moment both are in
# reach — so they are written down here, keyed by the page path they will have
# on the site, and tools/hooks/seo.py reads them back at build time.
#
# Needs real history: `actions/checkout` with fetch-depth: 0. Under a shallow
# clone git reports the same commit for every file, which the hook detects; it
# then falls back to mtimes rather than writing a date it cannot stand behind.
manifest="$here/.lastmod.tsv"
: > "$manifest"

if git -C "$src" rev-parse --git-dir >/dev/null 2>&1; then
  git -C "$src" log --format='%x01%cs' --name-only |
  awk -v OFS='\t' '
    /^\001/ { date = substr($0, 2); next }
    !NF || !date { next }
    seen[$0]++ { next }            # newest first: the first sighting is the last change
    {
      p = $0
      if (p == "CHANGELOG.md")                    page = "product/changelog.md"
      else if (p == "ROADMAP.md")                 page = "product/roadmap.md"
      else if (p == "docker/README.md")           page = "product/docker.md"
      else if (p ~ /^docs\//)                     { page = "product/" substr(p, 6) }
      else if (p ~ /^examples\/[^\/]+\/README\.md$/) {
        split(p, a, "/"); page = "product/examples/" a[2] ".md"
      }
      else next
      if (!(page in out)) { out[page] = date; print page, date }
    }
  ' >> "$manifest"

  # adr/index.md is written by this script, not by anyone: it is as old as the
  # newest record it lists.
  newest="$(awk -F'\t' '$1 ~ /^product\/adr\/[0-9]/ { print $2 }' "$manifest" | sort | tail -1)"
  if [ -n "$newest" ]; then
    printf 'product/adr/index.md\t%s\n' "$newest" >> "$manifest"
  fi
else
  echo "note: $src is not a git checkout — product/ pages will be dated by mtime" >&2
fi

# The native pages are dated from *this* repository's history. seo.py looks for
# anything under product/ in the manifest and nowhere else — it scans docs/ and
# overrides/ for the pages written here, and pages/ is neither — so their dates
# have to arrive the same way the copied ones do.
if git -C "$here" rev-parse --git-dir >/dev/null 2>&1; then
  find "$native" -name '*.md' -type f | while read -r page; do
    rel="${page#"$native"/}"
    date="$(git -C "$here" log -1 --format=%cs -- "pages/product/$rel")"
    if [ -n "$date" ]; then
      printf 'product/%s\t%s\n' "$rel" "$date" >> "$manifest"
    fi
  done
fi

echo "docs/product/ ← $src ($(find "$out" -name '*.md' | wc -l | tr -d ' ') pages, $(wc -l < "$manifest" | tr -d ' ') dated)"
