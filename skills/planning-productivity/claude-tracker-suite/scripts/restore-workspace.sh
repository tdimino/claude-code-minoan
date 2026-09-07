#!/usr/bin/env bash
# restore-workspace.sh — Restore Claude + Codex sessions from workspace-state.json
#
# Usage:
#   restore-workspace.sh              # Restore all saved sessions in Ghostty tabs
#   restore-workspace.sh --dry-run    # Show what would be restored without acting
#   restore-workspace.sh --limit N    # Restore at most N sessions
#   restore-workspace.sh --stagger S  # Seconds between tabs (default 1; raise on a slow machine)
#
# Reads ~/.claude/workspace-state.json (written by save-workspace.js every
# 5 minutes via launchd) and opens each session in a new Ghostty tab via
# ghostty-resume.sh, in the saved TTY (tab) order. One session failing never
# aborts the rest; every outcome is printed and tallied.

set -uo pipefail

STATE_FILE="$HOME/.claude/workspace-state.json"
RESUME_SCRIPT="$HOME/.claude/scripts/ghostty-resume.sh"
PROJECTS_DIR="$HOME/.claude/projects"
DRY_RUN=false
LIMIT=0
STAGGER_SEC=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true; shift ;;
    --limit) LIMIT="$2"; shift 2 ;;
    --stagger) STAGGER_SEC="$2"; shift 2 ;;
    --help|-h)
      echo "Usage: restore-workspace.sh [--dry-run] [--limit N] [--stagger SEC]"
      echo ""
      echo "Restore Claude + Codex sessions from workspace-state.json into Ghostty tabs."
      echo ""
      echo "Options:"
      echo "  --dry-run    Show what would be restored"
      echo "  --limit N    Restore at most N sessions"
      echo "  -h, --help   Show this help"
      exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done

if [[ ! -f "$STATE_FILE" ]]; then
  echo "No workspace state found at $STATE_FILE" >&2
  echo "Run 'node ~/.claude/skills/claude-tracker-suite/scripts/save-workspace.js' to save current state." >&2
  exit 1
fi
[[ -x "$RESUME_SCRIPT" ]] || { echo "ghostty-resume.sh not found or not executable at $RESUME_SCRIPT" >&2; exit 1; }

# One node pass: session rows (tab-separated) + header line with savedAt, age,
# and the set of sessions that are live right now (by sessionId, from PID files)
PARSED=$(node -e '
  const os = require("os"), path = require("path"), fs = require("fs");
  const utils = require(path.join(os.homedir(), ".claude/lib/tracker-utils"));
  const state = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
  const limit = parseInt(process.argv[2], 10) || 0;
  const rows = limit > 0 ? state.sessions.slice(0, limit) : state.sessions;
  const live = utils.getLiveSessionIds({ allKinds: true });
  const ageMin = Math.round((Date.now() - new Date(state.savedAt)) / 60000);
  console.log(["#header", state.savedAt || "unknown", isNaN(ageMin) ? "" : ageMin].join("\t"));
  for (const s of rows) {
    // Tab-separated: agent, sessionId, projectDir, tabTitle, pid, live?, title
    console.log([s.agent || "claude", s.sessionId, s.projectDir || "", s.tabTitle || "",
      s.pid || "", live.has(s.sessionId) ? "1" : "0", (s.title || "").replace(/\t/g, " ")].join("\t"));
  }
' "$STATE_FILE" "$LIMIT" 2>/dev/null) || { echo "Workspace state is empty or malformed." >&2; exit 1; }

HEADER=$(printf '%s\n' "$PARSED" | head -n1)
SESSIONS=$(printf '%s\n' "$PARSED" | tail -n +2)
SAVED_AT=$(printf '%s' "$HEADER" | cut -f2)
STAMP_AGE_MIN=$(printf '%s' "$HEADER" | cut -f3)
COUNT=$(printf '%s\n' "$SESSIONS" | grep -c . || true)

[[ "$COUNT" -gt 0 ]] || { echo "No sessions to restore (workspace state is empty)." >&2; exit 1; }
echo "Restoring $COUNT session(s) from workspace saved at $SAVED_AT"
if [[ -n "$STAMP_AGE_MIN" && "$STAMP_AGE_MIN" -gt 15 ]]; then
  echo "WARNING: stamp is ${STAMP_AGE_MIN} minutes old — sessions started since then are not in it."
fi
echo ""

RESTORED=0; SKIPPED=0; FAILED=0; CLAUDE_N=0; CODEX_N=0
while IFS=$'\t' read -r agent session_id project_dir tab_title pid is_live title; do
  [[ -z "$session_id" ]] && continue
  label="${title:-$tab_title}"

  # Already running (double invoke, or a partial crash where some tabs survived)
  if [[ "$is_live" == "1" ]]; then
    echo "  Skipped:  ($agent) $label — already running"
    SKIPPED=$((SKIPPED + 1)); continue
  fi
  if [[ "$agent" == "codex" && -n "$pid" ]] && kill -0 "$pid" 2>/dev/null \
     && ps -p "$pid" -o command= 2>/dev/null | grep -q codex; then
    echo "  Skipped:  ($agent) $label — already running (PID $pid)"
    SKIPPED=$((SKIPPED + 1)); continue
  fi

  # Pre-checks: no tab for a session that cannot resume
  if [[ -n "$project_dir" && ! -d "$project_dir" ]]; then
    echo "  Skipped:  ($agent) $label — project directory missing: $project_dir"
    SKIPPED=$((SKIPPED + 1)); continue
  fi
  if [[ "$agent" == "codex" && -z "$project_dir" ]]; then
    echo "  Skipped:  (codex) $label — no saved project directory"
    SKIPPED=$((SKIPPED + 1)); continue
  fi
  if [[ "$agent" == "claude" ]] && ! ls "$PROJECTS_DIR"/*/"$session_id.jsonl" >/dev/null 2>&1; then
    echo "  Skipped:  (claude) $label — transcript not found for ${session_id:0:8}"
    SKIPPED=$((SKIPPED + 1)); continue
  fi

  if [[ "$DRY_RUN" == "true" ]]; then
    echo "  [dry-run] ($agent) $label — $project_dir (session ${session_id:0:8}…)"
    RESTORED=$((RESTORED + 1)); continue
  fi

  args=("$session_id" --agent "$agent" --name "$label")
  [[ -n "$project_dir" ]] && args+=(--project "$project_dir")
  if "$RESUME_SCRIPT" "${args[@]}" </dev/null; then
    echo "  Restored: ($agent) $label"
    RESTORED=$((RESTORED + 1))
    if [[ "$agent" == "codex" ]]; then CODEX_N=$((CODEX_N + 1)); else CLAUDE_N=$((CLAUDE_N + 1)); fi
    sleep "$STAGGER_SEC"
  else
    echo "  FAILED:   ($agent) $label — see message above" >&2
    FAILED=$((FAILED + 1))
  fi
done < <(printf '%s\n' "$SESSIONS")

echo ""
if [[ "$DRY_RUN" == "true" ]]; then
  echo "Dry run complete: $RESTORED would be restored, $SKIPPED skipped."
else
  echo "Restored $RESTORED session(s) ($CLAUDE_N claude, $CODEX_N codex), $SKIPPED skipped, $FAILED failed."
fi
[[ "$FAILED" -eq 0 ]]
