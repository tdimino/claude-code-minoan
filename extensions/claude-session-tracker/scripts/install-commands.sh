#!/bin/bash
# Install Claude Code slash commands for session tracking

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMMANDS_SRC="$SCRIPT_DIR/../.claude/commands"
COMMANDS_DST="$HOME/.claude/commands"

# Create destination if it doesn't exist
mkdir -p "$COMMANDS_DST"

# Copy commands
echo "Installing Claude Code commands..."
cp "$COMMANDS_SRC/claude-tracker.md" "$COMMANDS_DST/"
cp "$COMMANDS_SRC/claude-tracker-here.md" "$COMMANDS_DST/"
cp "$COMMANDS_SRC/claude-tracker-search.md" "$COMMANDS_DST/"

echo "✓ Installed commands:"
echo "  /claude-tracker        - List all recent sessions"
echo "  /claude-tracker-here   - List sessions for current dir"
echo "  /claude-tracker-search - Search sessions by keyword"
echo ""
echo "Commands are now available in Claude Code."
