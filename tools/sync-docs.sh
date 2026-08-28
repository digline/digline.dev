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

echo "docs/product/ ← $src ($(find "$out" -name '*.md' | wc -l | tr -d ' ') pages)"
