#!/bin/bash
# PreToolUse hook: intercept git commands in Bash calls.
# Matcher: "Bash" — only fires for Bash tool calls.
# Fast-path: ~7ms for non-git calls (jq parse + regex check).
# Appends event to ~/.claude/git-tracking.jsonl for git/gh commands.

set -euo pipefail

TRACKING_LOG="$HOME/.claude/git-tracking.jsonl"
MARKER_DIR="/tmp/claude-git-markers"

# Read all of stdin at once
INPUT=$(cat)

# Extract command — fast bail if empty or non-git
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
[[ -z "$CMD" ]] && exit 0

# Fast regex check: does the command contain git or gh?
# Matches: "git status", "cd foo && git push", "git -C /path log", "gh pr create"
if ! [[ "$CMD" =~ (^|[[:space:]\&\;\|])git[[:space:]] ]] && ! [[ "$CMD" =~ (^|[[:space:]\&\;\|])gh[[:space:]] ]]; then
  exit 0
fi

# --- Git command detected. Extract metadata. ---

SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
CWD=$(echo "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
TOOL_USE_ID=$(echo "$INPUT" | jq -r '.tool_use_id // empty' 2>/dev/null)

# Determine repo path from command patterns
REPO=""

# Pattern 1: git -C <path>
if [[ "$CMD" =~ git[[:space:]]+-C[[:space:]]+\"?([^[:space:]\"]+)\"? ]]; then
  REPO="${BASH_REMATCH[1]}"
  # Expand ~ if present
  REPO="${REPO/#\~/$HOME}"
# Pattern 2: cd <path> && git
elif [[ "$CMD" =~ ^cd[[:space:]]+\"?([^[:space:]\";\&]+)\"? ]]; then
  REPO="${BASH_REMATCH[1]}"
  REPO="${REPO/#\~/$HOME}"
# Pattern 3: bare git command — use cwd
else
  REPO="$CWD"
fi

# Resolve to git root (3ms, acceptable)
GIT_ROOT=$(git -C "$REPO" rev-parse --show-toplevel 2>/dev/null || echo "$REPO")

# Get branch and remote (fast, cached by git)
BRANCH=$(git -C "$GIT_ROOT" branch --show-current 2>/dev/null || echo "")
REMOTE=$(git -C "$GIT_ROOT" remote get-url origin 2>/dev/null || echo "")

# Parse git subcommand(s) from the command string
# Extract all git subcommands from compound commands (git add && git commit && git push)
OPS=""
while [[ "$CMD" =~ git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?([a-z-]+) ]]; do
  SUBCMD="${BASH_REMATCH[2]}"
  case "$SUBCMD" in
    commit|push|pull|clone|checkout|switch|merge|rebase|cherry-pick|revert|tag|reset|\
    status|diff|log|show|branch|fetch|add|rm|stash)
      if [[ -z "$OPS" ]]; then
        OPS="$SUBCMD"
      else
        OPS="$OPS,$SUBCMD"
      fi
      ;;
  esac
  # Remove matched portion to find next git command in compound expressions
  CMD="${CMD#*"${BASH_REMATCH[0]}"}"
done

# Handle gh commands
CMD_ORIG=$(echo "$INPUT" | jq -r '.tool_input.command // empty' 2>/dev/null)
if [[ "$CMD_ORIG" =~ (^|[[:space:]\&\;\|])gh[[:space:]]+([a-z-]+) ]]; then
  GH_SUB="${BASH_REMATCH[2]}"
  if [[ -z "$OPS" ]]; then
    OPS="gh-$GH_SUB"
  else
    OPS="$OPS,gh-$GH_SUB"
  fi
fi

# Extract commit message if present (for git commit -m "...")
MSG=""
if [[ "$CMD_ORIG" =~ -m[[:space:]]+[\"\']([^\"\']+)[\"\'] ]]; then
  MSG="${BASH_REMATCH[1]}"
elif [[ "$CMD_ORIG" =~ -m[[:space:]]+\"?\$\(cat ]]; then
  # HEREDOC commit message — extract first line after EOF marker
  MSG="(heredoc)"
fi

[[ -z "$OPS" ]] && exit 0

# Build JSON line and append atomically
TS=$(date -u +"%Y-%m-%dT%H:%M:%S")
SHORT="${SESSION_ID:0:8}"

# Truncate cmd to 200 chars for storage
CMD_TRUNC=$(echo "$CMD_ORIG" | head -c 200)

# Use printf for atomic append (under PIPE_BUF on macOS = 512 bytes)
printf '{"ts":"%s","sid":"%s","short":"%s","repo":"%s","remote":"%s","branch":"%s","ops":"%s","cmd":"%s","cwd":"%s","msg":"%s"}\n' \
  "$TS" "$SESSION_ID" "$SHORT" "$GIT_ROOT" "$REMOTE" "$BRANCH" "$OPS" \
  "$(echo "$CMD_TRUNC" | sed 's/"/\\"/g' | tr '\n' ' ')" \
  "$CWD" \
  "$(echo "$MSG" | sed 's/"/\\"/g')" \
  >> "$TRACKING_LOG"

# Write marker file for commit commands (consumed by PostToolUse)
if [[ "$OPS" == *"commit"* ]] && [[ -n "$TOOL_USE_ID" ]]; then
  mkdir -p "$MARKER_DIR"
  echo "$GIT_ROOT" > "$MARKER_DIR/$TOOL_USE_ID"
fi

exit 0
