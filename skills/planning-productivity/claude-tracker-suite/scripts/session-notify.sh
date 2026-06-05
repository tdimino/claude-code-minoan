#!/usr/bin/env bash
# session-notify.sh — Send macOS notification for Claude session events
#
# Usage:
#   session-notify.sh --title "Title" --message "Body"         # Custom notification
#   session-notify.sh --session-done [--project <name>]        # Session completed
#   session-notify.sh --needs-input [--project <name>]         # Needs user attention
#   session-notify.sh --tab-badge <emoji> [--tab-title <t>]    # Update Ghostty tab with status badge
#
# Designed to be called from Claude Code hooks (PostToolUse, Stop) or
# from background monitoring scripts.

set -euo pipefail

TITLE=""
MESSAGE=""
SOUND="default"
PROJECT_NAME=""
TAB_BADGE=""
TAB_TITLE=""
SESSION_DONE=false
NEEDS_INPUT=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --title)
      TITLE="$2"
      shift 2
      ;;
    --message)
      MESSAGE="$2"
      shift 2
      ;;
    --sound)
      SOUND="$2"
      shift 2
      ;;
    --project)
      PROJECT_NAME="$2"
      shift 2
      ;;
    --session-done)
      SESSION_DONE=true
      shift
      ;;
    --needs-input)
      NEEDS_INPUT=true
      shift
      ;;
    --tab-badge)
      TAB_BADGE="$2"
      shift 2
      ;;
    --tab-title)
      TAB_TITLE="$2"
      shift 2
      ;;
    --no-sound)
      SOUND=""
      shift
      ;;
    --help|-h)
      echo "Usage: session-notify.sh [OPTIONS]"
      echo ""
      echo "Send macOS notifications for Claude session events."
      echo ""
      echo "Notification types:"
      echo "  --session-done              Session completed notification"
      echo "  --needs-input               Needs user attention notification"
      echo "  --title T --message M       Custom notification"
      echo ""
      echo "Options:"
      echo "  --project <name>            Project name for notification context"
      echo "  --tab-badge <emoji>         Update Ghostty tab title with emoji prefix"
      echo "  --tab-title <title>         Full tab title override"
      echo "  --sound <name>              macOS sound name (default: 'default')"
      echo "  --no-sound                  Silent notification"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

[[ "$(uname)" != "Darwin" ]] && { echo "session-notify: macOS only" >&2; exit 1; }

# Build notification for preset modes
if [[ "$SESSION_DONE" == "true" ]]; then
  TITLE="${PROJECT_NAME:+${PROJECT_NAME} — }Session Complete"
  MESSAGE="Claude Code session finished. Check results."
  TAB_BADGE="${TAB_BADGE:-✓}"
fi

if [[ "$NEEDS_INPUT" == "true" ]]; then
  TITLE="${PROJECT_NAME:+${PROJECT_NAME} — }Needs Input"
  MESSAGE="Claude Code is waiting for your response."
  TAB_BADGE="${TAB_BADGE:-⚡}"
  SOUND="Ping"
fi

# Send macOS notification (pass values as arguments to avoid injection)
if [[ -n "$TITLE" && -n "$MESSAGE" ]]; then
  if [[ -n "$SOUND" ]]; then
    osascript - "$TITLE" "$MESSAGE" "$SOUND" <<'APPLESCRIPT'
on run argv
    display notification (item 2 of argv) with title (item 1 of argv) sound name (item 3 of argv)
end run
APPLESCRIPT
  else
    osascript - "$TITLE" "$MESSAGE" <<'APPLESCRIPT'
on run argv
    display notification (item 2 of argv) with title (item 1 of argv)
end run
APPLESCRIPT
  fi
fi

# Update Ghostty tab title with badge
if [[ -n "$TAB_BADGE" ]]; then
  if [[ -n "$TAB_TITLE" ]]; then
    printf '\e]1;%s %s\a' "$TAB_BADGE" "$TAB_TITLE"
  else
    # Prepend badge to current project name
    local_project="${PROJECT_NAME:-$(basename "$PWD")}"
    printf '\e]1;%s %s\a' "$TAB_BADGE" "$local_project"
  fi
fi
