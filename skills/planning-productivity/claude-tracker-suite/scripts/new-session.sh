#!/usr/bin/env bash
# new-session.sh — Start a new Claude Code session in a terminal
#
# Usage:
#   new-session.sh <project-path> [--ghostty|--vscode|--cursor] [--model <model>]
#
# Targets:
#   --ghostty   Open in Ghostty (default — new tab via AppleScript)
#   --vscode    Open in VS Code integrated terminal
#   --cursor    Open in Cursor integrated terminal
#
# Opens the selected app, creates a new terminal/tab, cd's to the project
# directory, and runs `claude` (optionally with --model).
#
# Requires macOS (uses osascript for automation).

set -euo pipefail

# --- Parse arguments ---
PROJECT_PATH=""
TARGET="ghostty"  # default
MODEL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ghostty)
      TARGET="ghostty"
      shift
      ;;
    --vscode)
      TARGET="vscode"
      shift
      ;;
    --cursor)
      TARGET="cursor"
      shift
      ;;
    --model)
      MODEL="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: new-session.sh <project-path> [OPTIONS]"
      echo ""
      echo "Opens a new terminal tab and starts a fresh Claude Code session"
      echo "in the given project directory."
      echo ""
      echo "Targets (pick one):"
      echo "  --ghostty          Ghostty terminal — new tab (default)"
      echo "  --vscode           VS Code integrated terminal"
      echo "  --cursor           Cursor integrated terminal"
      echo ""
      echo "Options:"
      echo "  --model <model>    Pass --model to claude (e.g. sonnet, opus, haiku)"
      echo "  -h, --help         Show this help"
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
    *)
      if [[ -z "$PROJECT_PATH" ]]; then
        PROJECT_PATH="$1"
      else
        echo "Error: unexpected argument '$1'" >&2
        exit 1
      fi
      shift
      ;;
  esac
done

if [[ -z "$PROJECT_PATH" ]]; then
  echo "Error: project path required" >&2
  echo "Usage: new-session.sh <project-path> [--ghostty|--vscode|--cursor] [--model <model>]" >&2
  exit 1
fi

# Resolve to absolute path
PROJECT_PATH="$(cd "$PROJECT_PATH" 2>/dev/null && pwd)" || {
  echo "Error: directory does not exist: $PROJECT_PATH" >&2
  exit 1
}

# Build the claude command
CLAUDE_CMD="claude"
if [[ -n "$MODEL" ]]; then
  CLAUDE_CMD="claude --model $MODEL"
fi

# --- Ghostty ---
# Uses clipboard-paste (Cmd+V) instead of keystroke to avoid AppleScript
# capitalization bugs. Pattern from zeitlings/alfred-ghostty-script.
open_in_ghostty() {
  local cmd="cd $(printf '%q' "$PROJECT_PATH") && $CLAUDE_CMD"

  # Save clipboard, write command to it
  local old_clipboard
  old_clipboard="$(pbpaste 2>/dev/null || true)"
  printf '%s' "$cmd" | pbcopy

  osascript <<'APPLESCRIPT'
tell application "Ghostty"
    activate
end tell

delay 0.5

tell application "System Events"
    tell process "Ghostty"
        -- Cmd+T for new tab
        keystroke "t" using command down
    end tell
end tell

delay 1.0

tell application "System Events"
    tell process "Ghostty"
        -- Paste command from clipboard (avoids keystroke capitalization bugs)
        keystroke "v" using command down
        delay 0.2
        keystroke return
    end tell
end tell
APPLESCRIPT

  # Restore clipboard after a brief delay
  sleep 0.5
  printf '%s' "$old_clipboard" | pbcopy

  echo "Opened Ghostty tab: $cmd"
}

# --- VS Code / Cursor ---
open_in_editor() {
  local app_name="$1"
  local cli_cmd="$2"

  # Verify CLI exists
  if ! command -v "$cli_cmd" &>/dev/null; then
    echo "Error: '$cli_cmd' command not found." >&2
    exit 1
  fi

  # Open project directory
  "$cli_cmd" "$PROJECT_PATH" &>/dev/null &
  sleep 1

  local full_cmd="$CLAUDE_CMD"

  osascript <<EOF
tell application "$app_name"
    activate
end tell

delay 0.5

tell application "System Events"
    tell process "$app_name"
        -- Ctrl+Shift+\` to open new terminal
        key code 50 using {control down, shift down}
    end tell
end tell

delay 0.8

tell application "System Events"
    tell process "$app_name"
        keystroke "$full_cmd"
        delay 0.2
        keystroke return
    end tell
end tell
EOF
  echo "Opened $app_name terminal in $PROJECT_PATH with: $full_cmd"
}

# --- Dispatch ---
case "$TARGET" in
  ghostty)
    open_in_ghostty
    ;;
  vscode)
    open_in_editor "Visual Studio Code" "code"
    ;;
  cursor)
    open_in_editor "Cursor" "cursor"
    ;;
esac
