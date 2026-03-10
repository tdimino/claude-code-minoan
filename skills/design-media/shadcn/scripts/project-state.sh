#!/usr/bin/env bash
# Reads shadcn project state for context injection.
# Usage: bash scripts/project-state.sh [project-dir]
#
# Outputs: JSON with framework, installed components, aliases, theme config.
# Falls back to components.json direct read if CLI unavailable.

set -euo pipefail

PROJECT_DIR="${1:-.}"
cd "$PROJECT_DIR"

# Try CLI first (most complete)
if command -v npx &>/dev/null && [ -f "components.json" ]; then
  echo "=== shadcn info ==="
  npx shadcn@latest info 2>/dev/null || true
  echo ""
fi

# Always dump components.json for full config
if [ -f "components.json" ]; then
  echo "=== components.json ==="
  cat components.json
  echo ""
fi

# List installed UI components
UI_DIR=$(python3 -c "
import json, sys
try:
    with open('components.json') as f:
        cfg = json.load(f)
    aliases = cfg.get('aliases', {})
    ui = aliases.get('ui', '@/components/ui')
    # Convert @/ alias to relative path
    print(ui.lstrip('@/'))
except:
    print('components/ui')
" 2>/dev/null)

if [ -d "$UI_DIR" ]; then
  echo "=== Installed Components ==="
  ls -1 "$UI_DIR"/*.tsx 2>/dev/null | sed 's|.*/||; s|\.tsx$||' | sort
  COMPONENT_COUNT=$(ls -1 "$UI_DIR"/*.tsx 2>/dev/null | wc -l | tr -d ' ')
  echo ""
  echo "$COMPONENT_COUNT components installed in $UI_DIR/"
fi

# Check Tailwind version
if [ -f "package.json" ]; then
  echo ""
  echo "=== Tailwind Version ==="
  python3 -c "
import json
with open('package.json') as f:
    pkg = json.load(f)
deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
tw = deps.get('tailwindcss', 'not installed')
print(f'tailwindcss: {tw}')
animate = deps.get('tw-animate-css', deps.get('tailwindcss-animate', 'not installed'))
print(f'animation: {animate}')
" 2>/dev/null || true
fi
