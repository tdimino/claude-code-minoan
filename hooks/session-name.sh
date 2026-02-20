#!/bin/bash
# Extract session name (slug) from Claude Code StatusLine JSON
# Reads transcript_path from stdin → greps for "slug" in first few lines
INPUT=$(cat)
TRANSCRIPT=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('transcript_path',''))" 2>/dev/null)

if [ -z "$TRANSCRIPT" ] || [ ! -f "$TRANSCRIPT" ]; then
  echo ""
  exit 0
fi

# slug is in transcript lines; grab the first match
SLUG=$(grep -m1 -o '"slug":"[^"]*"' "$TRANSCRIPT" 2>/dev/null | cut -d'"' -f4)

if [ -n "$SLUG" ]; then
  echo "$SLUG"
else
  # Fallback: short session ID
  SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null)
  echo "${SESSION_ID:0:8}"
fi
