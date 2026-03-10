#!/usr/bin/env bash
# Check all installed shadcn components for upstream changes.
# Usage: bash scripts/diff-all.sh [project-dir]
#
# Outputs: List of components with upstream differences.

set -euo pipefail

PROJECT_DIR="${1:-.}"
cd "$PROJECT_DIR"

if [ ! -f "components.json" ]; then
  echo "ERROR: No components.json found in $PROJECT_DIR"
  exit 1
fi

# Find UI component directory
UI_DIR=$(python3 -c "
import json
with open('components.json') as f:
    cfg = json.load(f)
ui = cfg.get('aliases', {}).get('ui', '@/components/ui')
# Strip @/ alias — works whether src/ exists or not
print(ui.lstrip('@/'))
" 2>/dev/null || echo "components/ui")

if [ ! -d "$UI_DIR" ]; then
  echo "ERROR: UI directory $UI_DIR not found"
  exit 1
fi

echo "Checking for upstream changes..."
echo "================================"

CHANGED=0
CHECKED=0

for file in "$UI_DIR"/*.tsx; do
  [ -f "$file" ] || continue
  component=$(basename "$file" .tsx)
  CHECKED=$((CHECKED + 1))

  # Run diff, capture output
  diff_output=$(npx shadcn@latest diff "$component" 2>/dev/null || true)

  if [ -n "$diff_output" ] && [ "$diff_output" != "No changes." ]; then
    echo "  CHANGED: $component"
    CHANGED=$((CHANGED + 1))
  fi
done

echo ""
echo "$CHECKED components checked, $CHANGED with upstream changes."

if [ "$CHANGED" -gt 0 ]; then
  echo ""
  echo "Run 'npx shadcn@latest diff <component>' for details."
  echo "Commit local changes before running 'npx shadcn@latest add --overwrite <component>'."
fi
