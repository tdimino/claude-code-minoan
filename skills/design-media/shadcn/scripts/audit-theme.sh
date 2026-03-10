#!/usr/bin/env bash
# Audit shadcn theme CSS variables for completeness and consistency.
# Usage: bash scripts/audit-theme.sh [globals.css-path]
#
# Checks:
#   1. All standard shadcn CSS variables defined
#   2. Every --foo has a matching --foo-foreground
#   3. Dark mode variants exist
#   4. OKLCH syntax validation (Tailwind v4)
#   5. @theme inline mappings present

set -euo pipefail

CSS_FILE="${1:-}"

# Auto-detect from components.json if not provided
if [ -z "$CSS_FILE" ]; then
  if [ -f "components.json" ]; then
    CSS_FILE=$(python3 -c "
import json
with open('components.json') as f:
    cfg = json.load(f)
print(cfg.get('tailwind', {}).get('css', 'app/globals.css'))
" 2>/dev/null)
  fi
  CSS_FILE="${CSS_FILE:-app/globals.css}"
fi

if [ ! -f "$CSS_FILE" ]; then
  echo "ERROR: CSS file not found: $CSS_FILE"
  exit 1
fi

echo "Theme Audit: $CSS_FILE"
echo "========================="

# Standard shadcn CSS variables that should exist
REQUIRED_VARS=(
  "background" "foreground"
  "card" "card-foreground"
  "popover" "popover-foreground"
  "primary" "primary-foreground"
  "secondary" "secondary-foreground"
  "muted" "muted-foreground"
  "accent" "accent-foreground"
  "destructive" "destructive-foreground"
  "border" "input" "ring"
  "radius"
)

echo ""
echo "1. Required Variables"
echo "---------------------"
MISSING=0
for var in "${REQUIRED_VARS[@]}"; do
  if grep -q "\-\-${var}:" "$CSS_FILE"; then
    echo "  OK  --${var}"
  else
    echo "  MISSING  --${var}"
    MISSING=$((MISSING + 1))
  fi
done

echo ""
echo "2. Foreground Pairs"
echo "-------------------"
# Find all --foo variables and check for --foo-foreground
UNPAIRED=0
grep -oP '(?<=--)\w[\w-]*(?=:)' "$CSS_FILE" 2>/dev/null | sort -u | while read -r var; do
  # Skip variables that ARE foreground vars, or special vars
  case "$var" in
    *-foreground|border|input|ring|radius|chart-*|sidebar-*) continue ;;
  esac
  # Check if this var has a foreground partner
  if ! grep -q "\-\-${var}-foreground:" "$CSS_FILE"; then
    echo "  UNPAIRED  --${var} (no --${var}-foreground)"
    UNPAIRED=$((UNPAIRED + 1))
  fi
done

echo ""
echo "3. Dark Mode"
echo "------------"
if grep -q '\.dark' "$CSS_FILE"; then
  DARK_VARS=$(grep -c '\-\-.*:' <(sed -n '/\.dark/,/}/p' "$CSS_FILE") 2>/dev/null || echo 0)
  echo "  OK  .dark scope found ($DARK_VARS variables)"
else
  echo "  MISSING  No .dark scope found"
fi

echo ""
echo "4. Color Format"
echo "---------------"
HSL_COUNT=$(grep -c 'hsl(' "$CSS_FILE" 2>/dev/null || echo 0)
OKLCH_COUNT=$(grep -c 'oklch(' "$CSS_FILE" 2>/dev/null || echo 0)
RAW_COUNT=$(grep -cP '^\s+--\w.*:\s*\d' "$CSS_FILE" 2>/dev/null || echo 0)

echo "  oklch(): $OKLCH_COUNT"
echo "  hsl(): $HSL_COUNT"
echo "  raw values: $RAW_COUNT"

if [ "$HSL_COUNT" -gt 0 ] && [ "$OKLCH_COUNT" -gt 0 ]; then
  echo "  WARNING: Mixed color formats (hsl + oklch). Tailwind v4 prefers OKLCH."
fi

echo ""
echo "5. @theme inline"
echo "----------------"
if grep -q '@theme inline' "$CSS_FILE"; then
  THEME_VARS=$(grep -c '\-\-color-' "$CSS_FILE" 2>/dev/null || echo 0)
  echo "  OK  @theme inline found ($THEME_VARS color mappings)"
else
  echo "  MISSING  No @theme inline block — Tailwind v4 needs this for utility classes"
fi

echo ""
if [ "$MISSING" -eq 0 ]; then
  echo "Theme audit passed."
else
  echo "$MISSING required variables missing."
fi
