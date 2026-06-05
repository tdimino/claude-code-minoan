#!/usr/bin/env bash
# session-notify-hook.sh — Claude Code Stop hook that sends a macOS notification
#
# Add to ~/.claude/settings.json under hooks.Stop:
#   {"type": "command", "command": "~/.claude/hooks/session-notify-hook.sh", "async": true}
#
# Sends a macOS notification when Claude stops (waiting for input or done).
# Updates the Ghostty tab title with a status badge.

set -euo pipefail

NOTIFY_SCRIPT="$HOME/.claude/skills/claude-tracker-suite/scripts/session-notify.sh"

if [[ ! -f "$NOTIFY_SCRIPT" ]]; then
  exit 0
fi

PROJECT_NAME="$(basename "$PWD")"

"$NOTIFY_SCRIPT" --needs-input --project "$PROJECT_NAME"
