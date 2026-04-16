#!/usr/bin/env bash
# Fetch all 68 DESIGN.md files from getdesign into a local reference library.
# Output: ~/.claude/skills/design-md/library/<brand>/DESIGN.md
#
# Usage:
#   bash fetch_all_design_md.sh           # Fetch all 68
#   bash fetch_all_design_md.sh --force   # Re-fetch even if already downloaded

set -euo pipefail

LIBRARY_DIR="$(dirname "$0")/../library"
FORCE=false
[[ "${1:-}" == "--force" ]] && FORCE=true

mkdir -p "$LIBRARY_DIR"

# Get the brand list from the CLI
BRANDS=$(npx getdesign@latest list 2>/dev/null | sed -n 's/^\([a-zA-Z][a-zA-Z0-9._-]*\) .*/\1/p' | head -80)

if [[ -z "$BRANDS" ]]; then
  echo "Error: could not fetch brand list from getdesign CLI" >&2
  exit 1
fi

TOTAL=$(echo "$BRANDS" | wc -l | tr -d ' ')
COUNT=0
SKIPPED=0

echo "Fetching $TOTAL DESIGN.md files into $LIBRARY_DIR/"

for brand in $BRANDS; do
  COUNT=$((COUNT + 1))
  TARGET="$LIBRARY_DIR/$brand/DESIGN.md"

  if [[ -f "$TARGET" && "$FORCE" != "true" ]]; then
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  mkdir -p "$LIBRARY_DIR/$brand"
  echo "  [$COUNT/$TOTAL] $brand..."

  # getdesign writes to ./DESIGN.md or ./<brand>/DESIGN.md if one already exists
  # Use a temp dir to avoid conflicts
  TMPDIR=$(mktemp -d)
  (cd "$TMPDIR" && npx getdesign@latest add "$brand" 2>/dev/null) || {
    echo "    WARN: failed to fetch $brand" >&2
    rm -rf "$TMPDIR"
    continue
  }

  # Find the DESIGN.md it created (could be at root or in a subdir)
  FOUND=$(find "$TMPDIR" -name "DESIGN.md" -type f | head -1)
  if [[ -n "$FOUND" ]]; then
    mv "$FOUND" "$TARGET"
  else
    echo "    WARN: no DESIGN.md produced for $brand" >&2
  fi

  rm -rf "$TMPDIR"
done

FETCHED=$((COUNT - SKIPPED))
echo ""
echo "Done: $FETCHED fetched, $SKIPPED already cached ($TOTAL total brands)"
echo "Library: $LIBRARY_DIR/"
