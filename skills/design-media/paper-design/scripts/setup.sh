#!/usr/bin/env bash
# Purpose: Register Paper Design MCP server with Claude Code
# Usage: bash ~/.claude/skills/paper-design/scripts/setup.sh
# Outputs: Registration status, next steps

set -euo pipefail

echo "=== Paper Design MCP Setup ==="
echo ""

# Check if already registered
if claude mcp list 2>/dev/null | grep -q "paper"; then
    echo "[OK] Paper MCP already registered."
    claude mcp get paper 2>/dev/null || true
else
    echo "[ADDING] Registering Paper MCP server (HTTP transport, user scope)..."
    claude mcp add --transport http --scope user paper http://127.0.0.1:29979/mcp
    echo "[OK] Paper MCP registered."
fi

echo ""
echo "=== Next Steps ==="
echo "1. Add 'mcp__paper' to permissions.allow in ~/.claude/settings.json"
echo "2. Restart Claude Code for the new MCP server to take effect"
echo "3. Open Paper Desktop before starting a Claude Code session"
echo "4. Verify: run python3 ~/.claude/skills/paper-design/scripts/health-check.py"
