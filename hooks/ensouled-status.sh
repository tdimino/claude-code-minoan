#!/bin/bash
# Ensouled indicator for ccstatusline
# Checks: 1) soul marker file for this session, 2) CLAUDIUS_SOUL or CLAUDICLE_SOUL env var
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null)

# Glyph selection: Minoan theme uses Linear A AB001, default uses Eye of Horus
if [ "${STATUSLINE_THEME:-}" = "minoan" ]; then
  ENSOULED_GLYPH="𐘀 ensouled"
  MORTAL_GLYPH="○ mortal"
else
  ENSOULED_GLYPH="𓂀 ensouled"
  MORTAL_GLYPH="○ mortal"
fi

# Check per-session marker file
MARKER_DIR="$HOME/.claude/soul-sessions/active"
if [ -n "$SESSION_ID" ] && [ -f "$MARKER_DIR/$SESSION_ID" ]; then
  echo "$ENSOULED_GLYPH"
  exit 0
fi

# Check always-on env vars (both naming conventions)
if [ "${CLAUDIUS_SOUL:-0}" = "1" ] || [ "${CLAUDICLE_SOUL:-0}" = "1" ]; then
  echo "$ENSOULED_GLYPH"
  exit 0
fi

echo "$MORTAL_GLYPH"
