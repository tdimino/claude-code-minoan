#!/bin/bash
# Extract session name from Claude Code StatusLine JSON
# Priority: PID session file name → transcript slug → truncated session ID
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null)

if [ -z "$SESSION_ID" ]; then
  echo ""
  exit 0
fi

# Priority 1: Check active session PID files for a renamed name
SESSIONS_DIR="$HOME/.claude/sessions"
if [ -d "$SESSIONS_DIR" ]; then
  for f in "$SESSIONS_DIR"/*.json; do
    [ -f "$f" ] || continue
    NAME=$(python3 -c "
import json,sys
d=json.load(open('$f'))
if d.get('sessionId')=='$SESSION_ID' and d.get('name'):
    print(d['name'])
" 2>/dev/null)
    if [ -n "$NAME" ]; then
      echo "$NAME"
      exit 0
    fi
  done
fi

# Priority 2: Fall back to slug from transcript
TRANSCRIPT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('transcript_path',''))" 2>/dev/null)
if [ -n "$TRANSCRIPT" ] && [ -f "$TRANSCRIPT" ]; then
  SLUG=$(grep -o '"slug":"[^"]*"' "$TRANSCRIPT" 2>/dev/null | tail -1 | cut -d'"' -f4)
  if [ -n "$SLUG" ]; then
    echo "$SLUG"
    exit 0
  fi
fi

# Priority 3: Truncated session ID
echo "${SESSION_ID:0:8}"
