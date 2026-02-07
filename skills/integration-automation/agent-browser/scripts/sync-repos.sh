#!/bin/bash
# sync-repos.sh — Sync agent-browser skill to Claude-Code-Minoan and Claude-Code-Aldea
#
# Copies bin/, scripts/, and SKILL.md from the canonical skill location
# to the two downstream repos.

set -euo pipefail

SRC="/Users/tomdimino/.claude/skills/agent-browser"
MINOAN="/Users/tomdimino/Desktop/claude-code-minoan/skills/integration-automation/agent-browser"
ALDEA="/Users/tomdimino/Desktop/Aldea/Prompt development/Claude-Code-Aldea/skills/integration-automation/agent-browser"

sync_to() {
  local dest="$1"
  local name="$2"

  mkdir -p "$dest/bin" "$dest/scripts"

  # Sync binaries
  cp "$SRC/bin/agent-browser" "$dest/bin/"
  cp "$SRC/bin/agent-browser-darwin-arm64" "$dest/bin/" 2>/dev/null || true
  chmod +x "$dest/bin/"*

  # Sync scripts
  cp "$SRC/scripts/"*.sh "$dest/scripts/" 2>/dev/null || true
  chmod +x "$dest/scripts/"*.sh 2>/dev/null || true

  # Sync SKILL.md if it exists in the nested structure
  if [ -f "$SRC/skills/agent-browser/SKILL.md" ]; then
    cp "$SRC/skills/agent-browser/SKILL.md" "$dest/" 2>/dev/null || true
  fi

  local version=$("$dest/bin/agent-browser" --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
  echo "  $name: v${version}"
}

echo "Syncing agent-browser from canonical source..."
echo "  Source: $SRC"
echo ""

sync_to "$MINOAN" "Claude-Code-Minoan"
sync_to "$ALDEA" "Claude-Code-Aldea"

echo ""
echo "Done."
