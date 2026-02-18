#!/bin/bash
# sync-repos.sh — Sync minoan-swarm skill to Claude-Code-Minoan and Claude-Code-Aldea
#
# Copies SKILL.md and references/ from the canonical skill location
# to the two downstream repos.

set -euo pipefail

SRC="/Users/tomdimino/.claude/skills/minoan-swarm"
MINOAN="/Users/tomdimino/Desktop/claude-code-minoan/skills/planning-productivity/minoan-swarm"
ALDEA="/Users/tomdimino/Desktop/Aldea/Prompt development/Claude-Code-Aldea/skills/planning-productivity/minoan-swarm"

sync_to() {
  local dest="$1"
  local name="$2"

  mkdir -p "$dest/references" "$dest/scripts"

  # Sync SKILL.md
  cp "$SRC/SKILL.md" "$dest/"

  # Sync references
  if [ -d "$SRC/references" ]; then
    cp "$SRC/references/"* "$dest/references/" 2>/dev/null || true
  fi

  # Sync scripts (including this sync script)
  if [ -d "$SRC/scripts" ]; then
    cp "$SRC/scripts/"*.sh "$dest/scripts/" 2>/dev/null || true
    chmod +x "$dest/scripts/"*.sh 2>/dev/null || true
  fi

  echo "  ✓ $name"
}

echo "Syncing minoan-swarm from canonical source..."
echo "  Source: $SRC"
echo ""

sync_to "$MINOAN" "Claude-Code-Minoan"
sync_to "$ALDEA" "Claude-Code-Aldea"

echo ""
echo "Done."
