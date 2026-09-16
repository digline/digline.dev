#!/usr/bin/env bash
# Refuse a build whose docs/product/ came from an unreleased sync.
#
# tools/sync-docs.sh writes .sync-preview when SYNC_UNRELEASED=1 told it to copy
# from a checkout without checking that digline main has any of it, and removes
# the file on every ordinary sync. So the marker describes the docs/product/
# that is on disk right now, not a mood somebody was in earlier.
#
# This is the gate on the way out: `make build` runs it, and so does the step
# before the artifact is uploaded in .github/workflows/docs.yml. A preview is a
# fine thing to look at and the one thing that must never be deployed — the
# pages in it are, by definition, pages the released digline does not have.
#
#     usage: tools/check-source.sh
set -euo pipefail

here="$(cd "$(dirname "$0")/.." && pwd)"
marker="$here/.sync-preview"

if [ -f "$marker" ]; then
  {
    echo
    echo "  error: this build came from an unreleased sync and cannot be shipped."
    echo
    sed 's/^/    /' "$marker"
    echo
    echo "  Re-sync from a published checkout and build again:"
    echo
    echo "      make build                      # ../digline, level with origin/main"
    echo "      make build DIGLINE=<path>       # or a clone pinned to origin/main"
    echo
  } >&2
  exit 1
fi

echo "source: docs/product/ came from a published digline checkout"
