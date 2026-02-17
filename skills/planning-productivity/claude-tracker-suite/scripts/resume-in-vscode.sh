#!/usr/bin/env bash
# resume-in-vscode.sh — Open a Claude Code session in a new terminal
#
# Usage:
#   resume-in-vscode.sh <session-id> [--project <path>] [--ghostty|--cursor|--vscode]
#
# Targets:
#   --ghostty   Open in Ghostty (default — new tab via AppleScript)
#   --vscode    Open in VS Code integrated terminal
#   --cursor    Open in Cursor integrated terminal
#
# Opens the selected app, creates a new terminal/tab, and runs:
#   claude --resume <session-id>
#
# Requires macOS (uses osascript for automation).

set -euo pipefail

# --- Parse arguments ---
SESSION_ID=""
PROJECT_DIR=""
TARGET="ghostty"  # default

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      PROJECT_DIR="$2"
      shift 2
      ;;
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
    --help|-h)
      echo "Usage: resume-in-vscode.sh <session-id> [OPTIONS]"
      echo ""
      echo "Opens a new terminal and resumes the given Claude Code session."
      echo ""
      echo "Targets (pick one):"
      echo "  --ghostty          Ghostty terminal — new tab (default)"
      echo "  --vscode           VS Code integrated terminal"
      echo "  --cursor           Cursor integrated terminal"
      echo ""
      echo "Options:"
      echo "  --project <path>   cd to this directory before resuming"
      echo "  -h, --help         Show this help"
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
    *)
      if [[ -z "$SESSION_ID" ]]; then
        SESSION_ID="$1"
      else
        echo "Error: unexpected argument '$1'" >&2
        exit 1
      fi
      shift
      ;;
  esac
done

if [[ -z "$SESSION_ID" ]]; then
  echo "Error: session ID required" >&2
  echo "Usage: resume-in-vscode.sh <session-id> [--ghostty|--vscode|--cursor] [--project <path>]" >&2
  exit 1
fi

# --- Auto-detect project directory from session ID ---
# Claude Code stores sessions at ~/.claude/projects/<encoded-path>/<session-id>.jsonl
# Uses tracker-utils.js decodeProjectPath() which handles dashes-in-folder-names correctly.
if [[ -z "$PROJECT_DIR" ]]; then
  DETECTED=$(node -e "
    const fs = require('fs'), path = require('path');
    const projDir = path.join(require('os').homedir(), '.claude/projects');
    const sid = '${SESSION_ID}';
    try {
      const utils = require(require('os').homedir() + '/.claude/lib/tracker-utils.js');
      const dirs = fs.readdirSync(projDir, { withFileTypes: true }).filter(d => d.isDirectory());
      for (const d of dirs) {
        const jsonl = path.join(projDir, d.name, sid + '.jsonl');
        if (fs.existsSync(jsonl)) {
          console.log(utils.decodeProjectPath(d.name));
          break;
        }
      }
    } catch(e) {}
  " 2>/dev/null)
  if [[ -n "$DETECTED" && -d "$DETECTED" ]]; then
    PROJECT_DIR="$DETECTED"
    echo "Auto-detected project: $PROJECT_DIR"
  fi
fi

RESUME_CMD="claude --resume ${SESSION_ID}"

# --- Ghostty ---
# Uses clipboard-paste (Cmd+V) instead of keystroke to avoid AppleScript
# capitalization bugs. Pattern from zeitlings/alfred-ghostty-script.
open_in_ghostty() {
  local cmd="$RESUME_CMD"
  if [[ -n "$PROJECT_DIR" ]]; then
    cmd="cd $(printf '%q' "$PROJECT_DIR") && $cmd"
  fi

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

  echo "Opened Ghostty tab with: $cmd"
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

  # Open project if specified
  if [[ -n "$PROJECT_DIR" ]]; then
    "$cli_cmd" "$PROJECT_DIR" &>/dev/null &
    sleep 1
  fi

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
        keystroke "$RESUME_CMD"
        delay 0.2
        keystroke return
    end tell
end tell
EOF
  echo "Opened $app_name terminal with: $RESUME_CMD"
}

# --- Dispatch ---
case "$TARGET" in
  ghostty)
    open_in_ghostty
    ;;
  vscode)
    open_in_editor "Visual Studio Code" "vscode"
    ;;
  cursor)
    open_in_editor "Cursor" "cursor"
    ;;
esac
