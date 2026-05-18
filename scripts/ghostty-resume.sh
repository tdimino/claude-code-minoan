#!/usr/bin/env bash
# ghostty-resume.sh — open a Claude Code session in a new Ghostty tab
#
# Usage:
#   ghostty-resume.sh <session-id> [--project <path>]
#   ghostty-resume.sh --help
#
# Arguments:
#   <session-id>         Required. The Claude Code session ID to resume.
#   --project <path>     Optional. Explicit project directory (skips auto-detection).
#   --help / -h          Print this usage message and exit.

set -euo pipefail

usage() {
  sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'
  exit 0
}

SESSION_ID=""
PROJECT_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h)
      usage
      ;;
    --project)
      [[ $# -lt 2 ]] && { echo "ghostty-resume: --project requires a path" >&2; exit 1; }
      PROJECT_DIR="$2"
      shift 2
      ;;
    -*)
      echo "ghostty-resume: unknown option: $1" >&2
      exit 1
      ;;
    *)
      if [[ -z "$SESSION_ID" ]]; then
        SESSION_ID="$1"
      else
        echo "ghostty-resume: unexpected argument: $1" >&2
        exit 1
      fi
      shift
      ;;
  esac
done

[[ -z "$SESSION_ID" ]] && { echo "ghostty-resume: session ID is required" >&2; exit 1; }

if [[ ! "$SESSION_ID" =~ ^[a-zA-Z0-9-]+$ ]]; then
  echo "ghostty-resume: invalid session ID: $SESSION_ID" >&2
  exit 1
fi

if [[ "$(uname)" != "Darwin" ]]; then
  echo "ghostty-resume: macOS only" >&2
  exit 1
fi

if [[ ! -d "/Applications/Ghostty.app" ]]; then
  echo "ghostty-resume: Ghostty.app not found in /Applications" >&2
  exit 1
fi

if [[ -z "$PROJECT_DIR" ]]; then
  DETECTED=$(node -e "
    const sid = process.argv[1];
    const os = require('os');
    const path = require('path');
    const fs = require('fs');
    const utils = require(path.join(os.homedir(), '.claude/lib/tracker-utils'));
    try {
      const db = require(path.join(os.homedir(), '.claude/lib/tracker-db'));
      if (db.isAvailable()) {
        db.initSchema();
        const s = db.getSessionById(sid);
        if (s) {
          const p = s.project_path && !s.project_path.startsWith('-') ? s.project_path : utils.decodeProjectPath(s.project_dir || s.project_path);
          console.log(p);
          process.exit(0);
        }
      }
    } catch(e) {}
    const projDir = path.join(os.homedir(), '.claude/projects');
    try {
      const dirs = fs.readdirSync(projDir, { withFileTypes: true }).filter(d => d.isDirectory());
      for (const d of dirs) {
        if (fs.existsSync(path.join(projDir, d.name, sid + '.jsonl'))) {
          console.log(utils.decodeProjectPath(d.name));
          process.exit(0);
        }
      }
    } catch(e) {}
    process.exit(1);
  " "$SESSION_ID" 2>/dev/null) || true

  if [[ -z "$DETECTED" ]]; then
    echo "ghostty-resume: could not resolve project directory for session $SESSION_ID" >&2
    echo "ghostty-resume: use --project <path> to specify it explicitly" >&2
    exit 1
  fi

  PROJECT_DIR="$DETECTED"
fi

if [[ ! -d "$PROJECT_DIR" ]]; then
  echo "ghostty-resume: project directory does not exist: $PROJECT_DIR" >&2
  exit 1
fi

if ! pgrep -x Ghostty &>/dev/null; then
  open -a Ghostty
  sleep 2
fi

escaped_dir="${PROJECT_DIR//\'/\'\\\'\'}"
cmd="cd '${escaped_dir}' && claude --resume ${SESSION_ID}"

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

sleep 0.5
printf '%s' "$old_clipboard" | pbcopy

echo "Opened Ghostty tab: cd ${PROJECT_DIR} && claude --resume ${SESSION_ID}"
