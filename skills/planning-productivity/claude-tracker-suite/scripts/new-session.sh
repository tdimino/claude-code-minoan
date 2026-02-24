#!/usr/bin/env bash
# new-session.sh — Start a new Claude Code session in a terminal or headless
#
# Usage:
#   new-session.sh <project-path> [OPTIONS]
#
# Targets (pick one):
#   --ghostty          Ghostty terminal — new tab (default)
#   --vscode           VS Code integrated terminal
#   --cursor           Cursor integrated terminal
#   --headless         Run in current terminal, return JSON (requires --prompt)
#
# Options:
#   --prompt <text>    Pass a prompt to claude -p (terminal: runs in tab; headless: returns JSON)
#   --model <model>    Pass --model to claude (e.g. sonnet, opus, haiku)
#   --output-format <fmt>  Output format for headless mode: json (default), text, stream-json
#   -h, --help         Show this help
#
# Opens the selected app, creates a new terminal/tab, cd's to the project
# directory, and runs `claude` (optionally with --model and --prompt).
#
# Requires macOS (uses osascript for terminal automation).

set -euo pipefail

# --- Parse arguments ---
PROJECT_PATH=""
TARGET="ghostty"  # default
MODEL=""
PROMPT=""
HEADLESS=false
OUTPUT_FORMAT="json"

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
    --headless)
      HEADLESS=true
      shift
      ;;
    --prompt)
      PROMPT="$2"
      shift 2
      ;;
    --model)
      MODEL="$2"
      shift 2
      ;;
    --output-format)
      OUTPUT_FORMAT="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: new-session.sh <project-path> [OPTIONS]"
      echo ""
      echo "Start a new Claude Code session in a terminal tab or headless."
      echo ""
      echo "Targets (pick one):"
      echo "  --ghostty              Ghostty terminal — new tab (default)"
      echo "  --vscode               VS Code integrated terminal"
      echo "  --cursor               Cursor integrated terminal"
      echo "  --headless             Run in current terminal, return output (requires --prompt)"
      echo ""
      echo "Options:"
      echo "  --prompt <text>        Pass a prompt to claude -p"
      echo "  --model <model>        Pass --model to claude (e.g. sonnet, opus, haiku)"
      echo "  --output-format <fmt>  Headless output format: json (default), text, stream-json"
      echo "  -h, --help             Show this help"
      echo ""
      echo "Examples:"
      echo "  new-session.sh ~/project                              # interactive in Ghostty"
      echo "  new-session.sh ~/project --prompt 'fix the bug'       # prompt-driven in Ghostty"
      echo "  new-session.sh ~/project --headless --prompt 'hello'  # headless JSON output"
      echo "  new-session.sh ~/project --vscode --model opus        # interactive in VS Code"
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
  echo "Usage: new-session.sh <project-path> [--ghostty|--vscode|--cursor|--headless] [--prompt <text>] [--model <model>]" >&2
  exit 1
fi

# --- Validate flag combinations ---
if [[ "$HEADLESS" == "true" && -z "$PROMPT" ]]; then
  echo "Error: --headless requires --prompt" >&2
  exit 1
fi

if [[ "$HEADLESS" == "true" && "$TARGET" != "ghostty" ]]; then
  echo "Error: --headless runs in current terminal, cannot combine with --$TARGET" >&2
  exit 1
fi

# Resolve to absolute path
PROJECT_PATH="$(cd "$PROJECT_PATH" 2>/dev/null && pwd)" || {
  echo "Error: directory does not exist: $PROJECT_PATH" >&2
  exit 1
}

# --- Headless mode: run in current terminal, return output ---
if [[ "$HEADLESS" == "true" ]]; then
  cd "$PROJECT_PATH"
  # shellcheck disable=SC2086
  exec claude -p "$PROMPT" --output-format "$OUTPUT_FORMAT" ${MODEL:+--model "$MODEL"}
fi

# --- Build the command string for terminal modes ---
CLAUDE_CMD="claude"
if [[ -n "$PROMPT" ]]; then
  CLAUDE_CMD="claude -p $(printf '%q' "$PROMPT")"
fi
if [[ -n "$MODEL" ]]; then
  CLAUDE_CMD="$CLAUDE_CMD --model $MODEL"
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
# Uses clipboard-paste (same as Ghostty) to avoid AppleScript quoting issues
# with prompts containing special characters.
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

  local cmd="$CLAUDE_CMD"

  # Save clipboard, write command to it
  local old_clipboard
  old_clipboard="$(pbpaste 2>/dev/null || true)"
  printf '%s' "$cmd" | pbcopy

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
        -- Paste command from clipboard (avoids keystroke quoting issues)
        keystroke "v" using command down
        delay 0.2
        keystroke return
    end tell
end tell
EOF

  # Restore clipboard after a brief delay
  sleep 0.5
  printf '%s' "$old_clipboard" | pbcopy

  echo "Opened $app_name terminal in $PROJECT_PATH with: $cmd"
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
