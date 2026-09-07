#!/usr/bin/env bash
# resume-session.sh — Open a Claude Code session in a new Ghostty tab
#
# Thin wrapper over ~/.claude/scripts/ghostty-resume.sh, the suite's single
# terminal opener (launcher script + keystroked path, no clipboard).
#
# Usage:
#   resume-session.sh <session-id> [--project <path>] [--name <title>] [--cursor]
#
# Options:
#   --project <path>   Project directory (auto-detected from the transcript when omitted)
#   --name <title>     Label in this script's output (Claude Code titles the tab itself)
#   --cursor           Also open the project in Cursor
#   --ghostty          Accepted for compatibility (Ghostty is the only target)
#   -h, --help         Show this help

set -uo pipefail

OPENER="$HOME/.claude/scripts/ghostty-resume.sh"
SESSION_ID=""
PROJECT_DIR=""
TAB_NAME=""
OPEN_CURSOR=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project) PROJECT_DIR="$2"; shift 2 ;;
    --name) TAB_NAME="$2"; shift 2 ;;
    --cursor) OPEN_CURSOR=true; shift ;;
    --ghostty) shift ;;
    --cmux|--vscode)
      echo "Note: $1 is retired — Ghostty is the only terminal target" >&2; shift ;;
    --help|-h) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "Unknown option: $1" >&2; exit 1 ;;
    *)
      if [[ -z "$SESSION_ID" ]]; then SESSION_ID="$1"
      else echo "Error: unexpected argument '$1'" >&2; exit 1; fi
      shift ;;
  esac
done

[[ -n "$SESSION_ID" ]] || { echo "Error: session ID required" >&2; exit 1; }
[[ -x "$OPENER" ]] || { echo "Error: opener not found at $OPENER" >&2; exit 1; }

if [[ "$OPEN_CURSOR" == "true" ]]; then
  if [[ -z "$PROJECT_DIR" ]]; then
    PROJECT_DIR=$(node -e '
      const os = require("os"), path = require("path"), fs = require("fs");
      const utils = require(path.join(os.homedir(), ".claude/lib/tracker-utils"));
      const projDir = path.join(os.homedir(), ".claude/projects");
      for (const d of fs.readdirSync(projDir, { withFileTypes: true })) {
        if (d.isDirectory() && fs.existsSync(path.join(projDir, d.name, process.argv[1] + ".jsonl"))) {
          console.log(utils.decodeProjectPath(d.name)); break;
        }
      }' "$SESSION_ID" 2>/dev/null || true)
  fi
  if [[ -n "$PROJECT_DIR" ]] && command -v cursor >/dev/null; then
    cursor "$PROJECT_DIR" >/dev/null 2>&1 &
    echo "Opened Cursor: $PROJECT_DIR"
  else
    echo "Warning: cursor CLI or project directory unavailable — skipping editor" >&2
  fi
fi

args=("$SESSION_ID")
[[ -n "$PROJECT_DIR" ]] && args+=(--project "$PROJECT_DIR")
[[ -n "$TAB_NAME" ]] && args+=(--name "$TAB_NAME")
exec "$OPENER" "${args[@]}"
