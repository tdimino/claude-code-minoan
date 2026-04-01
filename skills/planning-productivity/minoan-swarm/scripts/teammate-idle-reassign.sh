#!/bin/bash
# teammate-idle-reassign.sh — TeammateIdle hook for Minoan Swarm
#
# When a teammate goes idle, check the shared task list for unclaimed tasks.
# If any exist, return exit code 2 with feedback telling the teammate to
# claim the next one. If no unclaimed tasks remain, exit 0 (let them stop).
#
# Hook event: TeammateIdle
# Input: JSON on stdin with { teammate_name, team_name, ... }
# Exit 0: allow idle (teammate stops)
# Exit 2: send feedback (teammate continues working)
#
# Install in settings.json:
#   "hooks": {
#     "TeammateIdle": [{
#       "type": "command",
#       "command": "bash ~/.claude/skills/minoan-swarm/scripts/teammate-idle-reassign.sh"
#     }]
#   }

set -euo pipefail

# Read hook input from stdin
INPUT=$(cat)

# Extract team name from input
TEAM_NAME=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('team_name',''))" 2>/dev/null || echo "")

if [ -z "$TEAM_NAME" ]; then
  # No team context — can't check tasks, let them idle
  exit 0
fi

TASKS_DIR="$HOME/.claude/tasks/$TEAM_NAME"

if [ ! -d "$TASKS_DIR" ]; then
  # No task directory — let them idle
  exit 0
fi

# Count unclaimed pending tasks (status=pending, no owner or empty owner)
UNCLAIMED=0
NEXT_SUBJECT=""

for task_file in "$TASKS_DIR"/*.json; do
  [ -f "$task_file" ] || continue

  # Parse task: check status is pending and owner is empty/missing
  TASK_INFO=$(python3 -c "
import json, sys
with open('$task_file') as f:
    t = json.load(f)
status = t.get('status', '')
owner = t.get('owner', '')
blocked = t.get('blockedBy', [])
subject = t.get('subject', '')
task_id = t.get('id', '')
# Task is claimable if: pending, no owner, not blocked
if status == 'pending' and not owner and not blocked:
    print(f'CLAIMABLE|{task_id}|{subject}')
else:
    print('SKIP')
" 2>/dev/null || echo "SKIP")

  if [[ "$TASK_INFO" == CLAIMABLE* ]]; then
    UNCLAIMED=$((UNCLAIMED + 1))
    if [ -z "$NEXT_SUBJECT" ]; then
      NEXT_SUBJECT="${TASK_INFO#CLAIMABLE|}"
    fi
  fi
done

if [ "$UNCLAIMED" -gt 0 ]; then
  TASK_ID="${NEXT_SUBJECT%%|*}"
  TASK_SUBJ="${NEXT_SUBJECT#*|}"
  # Return exit code 2 with feedback to keep the teammate working
  echo "There are $UNCLAIMED unclaimed tasks remaining. Claim task #$TASK_ID (\"$TASK_SUBJ\") from the task list and continue working. Check TaskList for the full list."
  exit 2
else
  # All tasks claimed or completed — teammate can rest
  exit 0
fi
