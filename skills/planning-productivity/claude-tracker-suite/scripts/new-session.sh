#!/usr/bin/env bash
# new-session.sh — Start a new Claude Code session in a Ghostty tab or headless
#
# Usage:
#   new-session.sh <project-path> [OPTIONS]
#
# Options:
#   --prompt <text>        Prompt for claude -p (tab: runs in the tab; headless: returns output)
#   --model <model>        Pass --model to claude (e.g. sonnet, opus, haiku)
#   --name <title>         Session display name (claude -n; shown in the /resume picker and tab title)
#   --headless             Run in the current terminal and print the result (requires --prompt)
#   --output-format <fmt>  Headless output format: json (default), text, stream-json
#   --cursor               Also open the project in Cursor
#   --ghostty              Accepted for compatibility (Ghostty is the only terminal target)
#   -h, --help             Show this help
#
# Tab mode delegates to ~/.claude/scripts/ghostty-resume.sh --exec, the suite's
# single terminal opener. Requires macOS.

set -uo pipefail

OPENER="$HOME/.claude/scripts/ghostty-resume.sh"
PROJECT_PATH=""
MODEL=""
PROMPT=""
HEADLESS=false
OUTPUT_FORMAT="json"
TAB_NAME=""
OPEN_CURSOR=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ghostty) shift ;;
    --vscode|--cmux) echo "Note: $1 is retired — opening in Ghostty" >&2; shift ;;
    --cursor) OPEN_CURSOR=true; shift ;;
    --headless) HEADLESS=true; shift ;;
    --prompt) PROMPT="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --name) TAB_NAME="$2"; shift 2 ;;
    --output-format) OUTPUT_FORMAT="$2"; shift 2 ;;
    --help|-h) sed -n '2,18p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; exit 1 ;;
    *)
      if [[ -z "$PROJECT_PATH" ]]; then PROJECT_PATH="$1"
      else echo "Error: unexpected argument '$1'" >&2; exit 1; fi
      shift ;;
  esac
done

[[ -n "$PROJECT_PATH" ]] || { echo "Error: project path required" >&2; exit 1; }
if [[ "$HEADLESS" == "true" && -z "$PROMPT" ]]; then
  echo "Error: --headless requires --prompt" >&2; exit 1
fi

PROJECT_PATH="$(cd "$PROJECT_PATH" 2>/dev/null && pwd)" || {
  echo "Error: directory does not exist: $PROJECT_PATH" >&2; exit 1
}

# --- Headless: run here, print the result ---
if [[ "$HEADLESS" == "true" ]]; then
  cd "$PROJECT_PATH"
  exec claude -p "$PROMPT" --output-format "$OUTPUT_FORMAT" ${MODEL:+--model "$MODEL"}
fi

# --- Tab: build the claude command, hand it to the opener ---
sq() { local q=\'; printf "'%s'" "${1//$q/$q\\$q$q}"; }   # 'it'\''s' — shell-safe single quoting
CLAUDE_CMD="claude"
[[ -n "$PROMPT" ]] && CLAUDE_CMD="claude -p $(sq "$PROMPT")"
[[ -n "$MODEL" ]] && CLAUDE_CMD="$CLAUDE_CMD --model $(sq "$MODEL")"
[[ -n "$TAB_NAME" ]] && CLAUDE_CMD="$CLAUDE_CMD -n $(sq "$TAB_NAME")"

if [[ "$OPEN_CURSOR" == "true" ]]; then
  if command -v cursor >/dev/null; then
    cursor "$PROJECT_PATH" >/dev/null 2>&1 &
    echo "Opened Cursor: $PROJECT_PATH"
  else
    echo "Warning: cursor CLI not found — skipping editor" >&2
  fi
fi

[[ -x "$OPENER" ]] || { echo "Error: opener not found at $OPENER" >&2; exit 1; }
exec "$OPENER" --exec "$CLAUDE_CMD" --project "$PROJECT_PATH" --name "${TAB_NAME:-$(basename "$PROJECT_PATH")}"
