#!/usr/bin/env bash
# resume-session.sh — Open a Claude Code session in a new terminal
#
# Usage:
#   resume-session.sh <session-id> [--project <path>] [--cmux|--ghostty|--vscode|--cursor]
#
# Targets:
#   --cmux      Open in cmux tab (default when CMUX_WORKSPACE_ID is set)
#   --ghostty   Open in Ghostty tab via AppleScript (default when cmux unavailable)
#   --vscode    Open project in VS Code + resume in terminal
#   --cursor    Open project in Cursor + resume in terminal
#
# Auto-detects: cmux if running, otherwise Ghostty.

set -euo pipefail

# --- Parse arguments ---
SESSION_ID=""
PROJECT_DIR=""
TARGET="auto"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)
      PROJECT_DIR="$2"
      shift 2
      ;;
    --cmux)
      TARGET="cmux"
      shift
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
      echo "Usage: resume-session.sh <session-id> [OPTIONS]"
      echo ""
      echo "Opens a new terminal tab and resumes the given Claude Code session."
      echo "Auto-detects cmux (preferred) or Ghostty as terminal target."
      echo ""
      echo "Targets (pick one, or let auto-detect choose):"
      echo "  --cmux             cmux terminal tab"
      echo "  --ghostty          Ghostty tab via AppleScript"
      echo "  --vscode           Open project in VS Code + resume in terminal"
      echo "  --cursor           Open project in Cursor + resume in terminal"
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
  echo "Usage: resume-session.sh <session-id> [--cmux|--ghostty|--vscode|--cursor] [--project <path>]" >&2
  exit 1
fi

# --- Auto-detect project directory from session ID ---
# Claude Code stores sessions at ~/.claude/projects/<encoded-path>/<session-id>.jsonl
# Uses tracker-utils.js decodeProjectPath() for correct path resolution.
if [[ -z "$PROJECT_DIR" ]]; then
  DETECTED=$(SESSION_ID="$SESSION_ID" node -e "
    const fs = require('fs'), path = require('path');
    const projDir = path.join(require('os').homedir(), '.claude/projects');
    const sid = process.env.SESSION_ID;
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

# Validate SESSION_ID is alphanumeric/hyphens only (UUID format)
if [[ ! "$SESSION_ID" =~ ^[a-zA-Z0-9-]+$ ]]; then
  echo "Error: invalid session ID (must be alphanumeric/hyphens)" >&2
  exit 1
fi

RESUME_CMD="claude --resume ${SESSION_ID}"

# --- Build full command with cd ---
build_cmd() {
  local cmd="$RESUME_CMD"
  if [[ -n "$PROJECT_DIR" ]]; then
    cmd="cd $(printf '%q' "$PROJECT_DIR") && $cmd"
  fi
  echo "$cmd"
}

# --- Check if cmux is available ---
cmux_available() {
  cmux ping &>/dev/null 2>&1
}

# --- cmux ---
open_in_cmux() {
  local cmd
  cmd=$(build_cmd)

  if ! cmux_available; then
    echo "cmux not running — falling back to Ghostty" >&2
    open_in_ghostty
    return
  fi

  local output
  output=$(cmux new-surface --type terminal 2>&1)
  local surface_id
  surface_id=$(echo "$output" | grep -o 'surface:[0-9]*' | head -1)

  if [[ -z "$surface_id" ]]; then
    echo "Error: failed to create cmux surface. Output: $output" >&2
    echo "Falling back to Ghostty" >&2
    open_in_ghostty
    return
  fi

  sleep 0.3

  cmux send --surface "$surface_id" "$cmd" &>/dev/null
  cmux send-key --surface "$surface_id" enter &>/dev/null

  local tab_label="${SESSION_ID:0:8}"
  if [[ -n "$PROJECT_DIR" ]]; then
    tab_label="$(basename "$PROJECT_DIR"):${SESSION_ID:0:8}"
  fi
  cmux rename-tab --surface "$surface_id" "$tab_label" &>/dev/null

  echo "Opened cmux $surface_id with: $cmd"
}

# --- Ghostty (AppleScript, macOS only) ---
# Uses clipboard-paste to avoid AppleScript keystroke capitalization bugs.
open_in_ghostty() {
  local cmd
  cmd=$(build_cmd)

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
        keystroke "t" using command down
    end tell
end tell

delay 1.0

tell application "System Events"
    tell process "Ghostty"
        keystroke "v" using command down
        delay 0.2
        keystroke return
    end tell
end tell
APPLESCRIPT

  # Restore clipboard
  sleep 0.5
  printf '%s' "$old_clipboard" | pbcopy

  echo "Opened Ghostty tab with: $cmd"
}

# --- Editor + terminal ---
# Opens the project in VS Code/Cursor, then resumes in best available terminal.
open_in_editor_and_terminal() {
  local cli_cmd="$1"

  if ! command -v "$cli_cmd" &>/dev/null; then
    echo "Warning: '$cli_cmd' command not found — skipping editor open" >&2
  else
    if [[ -n "$PROJECT_DIR" ]]; then
      "$cli_cmd" "$PROJECT_DIR" &>/dev/null &
      echo "Opened $cli_cmd $PROJECT_DIR"
    fi
  fi

  # Resume in best available terminal
  open_in_best_terminal
}

# --- Auto-detect best terminal ---
open_in_best_terminal() {
  if cmux_available; then
    open_in_cmux
  else
    open_in_ghostty
  fi
}

# --- Dispatch ---
case "$TARGET" in
  auto)
    open_in_best_terminal
    ;;
  cmux)
    open_in_cmux
    ;;
  ghostty)
    open_in_ghostty
    ;;
  vscode)
    open_in_editor_and_terminal "code"
    ;;
  cursor)
    open_in_editor_and_terminal "cursor"
    ;;
esac
