#!/bin/bash
# PostToolUse hook: enrich git tracking with command results.
# Matcher: "Bash" — only fires for Bash tool calls.
# Checks for marker file from PreToolUse git-track.sh.
# Parses tool_response for commit hashes, branch switches, push results.
# Appends enrichment line to ~/.claude/git-tracking.jsonl.

set -uo pipefail
# Note: intentionally no -e — bash regex =~ returns exit 1 on no match,
# which would kill the script under set -e.

TRACKING_LOG="$HOME/.claude/git-tracking.jsonl"
MARKER_DIR="/tmp/claude-git-markers"

# Read all of stdin at once
INPUT=$(cat)

# Extract tool_use_id — check for marker file
TOOL_USE_ID=$(echo "$INPUT" | jq -r '.tool_use_id // empty' 2>/dev/null)
[[ -z "$TOOL_USE_ID" ]] && exit 0

MARKER_FILE="$MARKER_DIR/$TOOL_USE_ID"
[[ ! -f "$MARKER_FILE" ]] && exit 0

# --- Marker found. This was a git command we want to enrich. ---

GIT_ROOT=$(cat "$MARKER_FILE")
rm -f "$MARKER_FILE"

SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
RESPONSE=$(echo "$INPUT" | jq -r '.tool_response // empty' 2>/dev/null)

[[ -z "$RESPONSE" ]] && exit 0

# Parse commit hash from git commit output: [main a1b2c3d] message
HASH=""
COMMIT_MSG=""
if [[ "$RESPONSE" =~ \[([^][:space:]]+)[[:space:]]+([a-f0-9]{7,40})\][[:space:]]+(.*) ]]; then
  BRANCH_REF="${BASH_REMATCH[1]}"
  HASH="${BASH_REMATCH[2]}"
  COMMIT_MSG="${BASH_REMATCH[3]}"
  # Truncate message
  COMMIT_MSG=$(echo "$COMMIT_MSG" | head -c 120)
fi

# Parse branch switch from git checkout/switch output
SWITCHED_BRANCH=""
if [[ "$RESPONSE" =~ Switched\ to\ (a\ new\ )?branch\ \'([^\']+)\' ]]; then
  SWITCHED_BRANCH="${BASH_REMATCH[2]}"
elif [[ "$RESPONSE" =~ Already\ on\ \'([^\']+)\' ]]; then
  SWITCHED_BRANCH="${BASH_REMATCH[1]}"
fi

# Parse push result: old_hash..new_hash local -> remote
PUSH_REF=""
if [[ "$RESPONSE" =~ ([a-f0-9]+)\.\.([a-f0-9]+)[[:space:]]+([^[:space:]]+)[[:space:]]*-\>[[:space:]]*([^[:space:]]+) ]]; then
  PUSH_REF="${BASH_REMATCH[3]}->${BASH_REMATCH[4]}"
fi

# Only append if we found something useful
if [[ -n "$HASH" ]] || [[ -n "$SWITCHED_BRANCH" ]] || [[ -n "$PUSH_REF" ]]; then
  TS=$(date -u +"%Y-%m-%dT%H:%M:%S")

  printf '{"ts":"%s","sid":"%s","type":"result","tool_use_id":"%s","repo":"%s","hash":"%s","commit_msg":"%s","switched_branch":"%s","push_ref":"%s"}\n' \
    "$TS" "$SESSION_ID" "$TOOL_USE_ID" "$GIT_ROOT" \
    "$HASH" \
    "$(echo "$COMMIT_MSG" | sed 's/"/\\"/g' | tr '\n' ' ')" \
    "$SWITCHED_BRANCH" \
    "$PUSH_REF" \
    >> "$TRACKING_LOG"
fi

exit 0
