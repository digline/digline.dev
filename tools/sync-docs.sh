#!/usr/bin/env bash
# Copy the product documentation out of digline/digline into docs/product/.
#
# Nothing under docs/product/ is committed here: this script is the only thing
# that puts it there, and it runs before every build, locally and in CI. The
# rewrites at the bottom exist because the files are written to be read on
# GitHub, where they sit one directory deeper than they do on the site.
#
#   usage: tools/sync-docs.sh [path-to-digline-checkout]
set -euo pipefail

src="${1:-../digline}"
here="$(cd "$(dirname "$0")/.." && pwd)"
out="$here/docs/product"

[ -d "$src/docs" ] || { echo "no docs/ in $src — is that a digline checkout?" >&2; exit 1; }

rm -rf "$out"
mkdir -p "$out/examples"

cp -R "$src/docs/." "$out/"

# Two files live at the root of the repository rather than in its docs/, because
# that is where a reader arriving on GitHub looks for them. They are pages here.
cp "$src/CHANGELOG.md" "$out/changelog.md"
cp "$src/ROADMAP.md"   "$out/roadmap.md"

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
  echo "order they were taken; superseded ones stay, marked."
  echo
  for adr in "$out"/adr/[0-9]*.md; do
    title="$(sed -n 's/^# //p' "$adr" | head -1)"
    echo "- [$title]($(basename "$adr"))"
  done
} > "$out/adr/index.md"

# Links that are correct in the repository and wrong on the site.
perl -pi -e 's{\]\(\.\./README\.md\)}{](https://github.com/digline/digline#readme)}g' "$out"/*.md "$out"/adr/*.md
perl -pi -e 's{\]\(adr/\)}{](adr/index.md)}g'                                        "$out"/*.md
perl -pi -e 's{\]\(docs/adr/\)}{](adr/index.md)}g'                                   "$out/changelog.md"

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

echo "docs/product/ ← $src ($(find "$out" -name '*.md' | wc -l | tr -d ' ') pages, $(wc -l < "$manifest" | tr -d ' ') dated)"
