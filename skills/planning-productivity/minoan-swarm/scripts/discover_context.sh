#!/usr/bin/env bash
# discover_context.sh — Auto-discover project context for team planning
# Usage: bash discover_context.sh [project-root]
#
# Scans a repo for planning artifacts: CLAUDE.md, roadmaps, plans,
# issues, and documentation. Outputs a structured summary for the
# Minoan Swarm skill to consume when designing agent teams.

set -euo pipefail

ROOT="${1:-.}"
ROOT="$(cd "$ROOT" && pwd)"

echo "=== MINOAN SWARM: PROJECT CONTEXT DISCOVERY ==="
echo "Root: $ROOT"
echo ""

# 1. Identity files
echo "--- Identity ---"
for f in CLAUDE.md .claude/CLAUDE.md README.md SPEC.md; do
  path="$ROOT/$f"
  if [[ -f "$path" ]]; then
    lines=$(wc -l < "$path" | tr -d ' ')
    echo "  [found] $f ($lines lines)"
  fi
done

# Also check for project-level CLAUDE.md in .claude/
if [[ -f "$ROOT/.claude/settings.json" ]]; then
  echo "  [found] .claude/settings.json"
fi

echo ""

# 2. Planning artifacts
echo "--- Planning ---"
for f in ROADMAP.md roadmap.md CHANGELOG.md; do
  path="$ROOT/$f"
  if [[ -f "$path" ]]; then
    lines=$(wc -l < "$path" | tr -d ' ')
    echo "  [found] $f ($lines lines)"
  fi
done

for d in plans/ .beads/ docs/ design/; do
  path="$ROOT/$d"
  if [[ -d "$path" ]]; then
    count=$(find "$path" -maxdepth 3 -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
    echo "  [found] $d ($count markdown files)"
  fi
done

echo ""

# 3. Codebase structure
echo "--- Codebase ---"
if [[ -f "$ROOT/package.json" ]]; then
  name=$(grep -o '"name":\s*"[^"]*"' "$ROOT/package.json" | head -1 | cut -d'"' -f4)
  echo "  [node] $name"
fi
if [[ -f "$ROOT/Gemfile" ]]; then
  echo "  [ruby] Gemfile present"
fi
if [[ -f "$ROOT/pyproject.toml" ]] || [[ -f "$ROOT/setup.py" ]]; then
  echo "  [python] Python project"
fi
if [[ -f "$ROOT/Cargo.toml" ]]; then
  echo "  [rust] Cargo project"
fi

# Count source files by type (only search directories that exist)
src_dirs=()
for d in src app lib; do
  [[ -d "$ROOT/$d" ]] && src_dirs+=("$ROOT/$d")
done
if [[ ${#src_dirs[@]} -gt 0 ]]; then
  for ext in ts tsx js jsx rb py rs go; do
    count=$(find "${src_dirs[@]}" -name "*.$ext" 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$count" -gt 0 ]]; then
      echo "  .$ext files: $count"
    fi
  done
fi

echo ""

# 4. Test infrastructure
echo "--- Tests ---"
for d in __tests__/ tests/ test/ spec/ e2e/; do
  path="$ROOT/$d"
  if [[ -d "$path" ]]; then
    count=$(find "$path" -maxdepth 3 -type f 2>/dev/null | wc -l | tr -d ' ')
    echo "  [found] $d ($count files)"
  fi
done

if [[ -f "$ROOT/vitest.config.ts" ]] || [[ -f "$ROOT/vitest.config.js" ]]; then
  echo "  [framework] Vitest"
fi
if [[ -f "$ROOT/jest.config.ts" ]] || [[ -f "$ROOT/jest.config.js" ]]; then
  echo "  [framework] Jest"
fi
if [[ -f "$ROOT/playwright.config.ts" ]]; then
  echo "  [framework] Playwright"
fi

echo ""

# 5. GitHub issues (if gh CLI available)
echo "--- Issues ---"
if command -v gh &>/dev/null; then
  if gh auth status &>/dev/null 2>&1; then
    issue_count=$(gh issue list --limit 1000 --state open --json number 2>/dev/null | grep -c "number" || echo "0")
    echo "  Open issues: $issue_count"

    # Show labels if any
    labels=$(gh label list --limit 50 --json name 2>/dev/null | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | tr '\n' ', ' | sed 's/,$//')
    if [[ -n "$labels" ]]; then
      echo "  Labels: $labels"
    fi
  else
    echo "  [skip] gh not authenticated"
  fi
else
  echo "  [skip] gh CLI not installed"
fi

echo ""

# 6. Git state
echo "--- Git ---"
if git -C "$ROOT" rev-parse --is-inside-work-tree &>/dev/null; then
  branch=$(git -C "$ROOT" branch --show-current 2>/dev/null || echo "detached")
  echo "  Branch: $branch"
  commit_count=$(git -C "$ROOT" rev-list --count HEAD 2>/dev/null || echo "?")
  echo "  Commits: $commit_count"
  dirty=$(git -C "$ROOT" status --porcelain 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$dirty" -gt 0 ]]; then
    echo "  Uncommitted changes: $dirty files"
  else
    echo "  Working tree: clean"
  fi
fi

echo ""
echo "=== DISCOVERY COMPLETE ==="
