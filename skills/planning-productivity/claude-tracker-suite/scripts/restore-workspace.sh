#!/usr/bin/env bash
# restore-workspace.sh — Restore Claude sessions from workspace-state.json
#
# Usage:
#   restore-workspace.sh              # Restore all saved sessions in Ghostty tabs
#   restore-workspace.sh --dry-run    # Show what would be restored without acting
#   restore-workspace.sh --limit N    # Restore at most N sessions
#
# Reads ~/.claude/workspace-state.json (written by save-workspace.js) and
# opens each session in a new Ghostty tab via ghostty-resume.sh.

set -euo pipefail

STATE_FILE="$HOME/.claude/workspace-state.json"
RESUME_SCRIPT="$HOME/.claude/scripts/ghostty-resume.sh"
DRY_RUN=false
LIMIT=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --limit)
      LIMIT="$2"
      shift 2
      ;;
    --help|-h)
      echo "Usage: restore-workspace.sh [--dry-run] [--limit N]"
      echo ""
      echo "Restore Claude sessions from workspace-state.json into Ghostty tabs."
      echo "Each session opens in its own tab with the saved tab title."
      echo ""
      echo "Options:"
      echo "  --dry-run    Show what would be restored"
      echo "  --limit N    Restore at most N sessions"
      echo "  -h, --help   Show this help"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

if [[ ! -f "$STATE_FILE" ]]; then
  echo "No workspace state found at $STATE_FILE" >&2
  echo "Run 'node ~/.claude/skills/claude-tracker-suite/scripts/save-workspace.js' to save current state." >&2
  exit 1
fi

if [[ ! -f "$RESUME_SCRIPT" ]]; then
  echo "ghostty-resume.sh not found at $RESUME_SCRIPT" >&2
  exit 1
fi

# Parse workspace state with node
SESSIONS=$(node -e "
  const state = JSON.parse(require('fs').readFileSync('$STATE_FILE', 'utf8'));
  const limit = ${LIMIT};
  const sessions = limit > 0 ? state.sessions.slice(0, limit) : state.sessions;
  for (const s of sessions) {
    // Tab-separated: sessionId, projectDir, tabTitle
    console.log([s.sessionId, s.projectDir, s.tabTitle].join('\t'));
  }
  if (sessions.length === 0) process.exit(1);
" 2>/dev/null) || {
  echo "No sessions to restore (workspace state is empty or malformed)." >&2
  exit 1
}

SAVED_AT=$(node -e "
  const state = JSON.parse(require('fs').readFileSync('$STATE_FILE', 'utf8'));
  console.log(state.savedAt || 'unknown');
" 2>/dev/null)

COUNT=$(echo "$SESSIONS" | wc -l | tr -d ' ')
echo "Restoring $COUNT session(s) from workspace saved at $SAVED_AT"
echo ""

RESTORED=0
while IFS=$'\t' read -r session_id project_dir tab_title; do
  if [[ "$DRY_RUN" == "true" ]]; then
    echo "  [dry-run] $tab_title — $project_dir (session: ${session_id:0:8}…)"
  else
    echo "  Restoring: $tab_title"
    if [[ -n "$project_dir" && -d "$project_dir" ]]; then
      "$RESUME_SCRIPT" "$session_id" --project "$project_dir" --name "$tab_title"
    else
      "$RESUME_SCRIPT" "$session_id" --name "$tab_title"
    fi
    RESTORED=$((RESTORED + 1))
    # Stagger tab openings to avoid overwhelming Ghostty
    sleep 2
  fi
done <<< "$SESSIONS"

if [[ "$DRY_RUN" == "true" ]]; then
  echo ""
  echo "Dry run complete. $COUNT session(s) would be restored."
else
  echo ""
  echo "Restored $RESTORED session(s)."
fi
