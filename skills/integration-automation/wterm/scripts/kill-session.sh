#!/bin/bash
# Kill a wterm session by ID
# Usage: kill-session.sh <session-id>

# Auto-load auth token from secrets.env if not already set
if [ -z "$WTERM_AUTH_TOKEN" ] && [ -f ~/.config/env/secrets.env ]; then
    WTERM_AUTH_TOKEN=$(grep '^WTERM_AUTH_TOKEN=' ~/.config/env/secrets.env | cut -d= -f2)
    export WTERM_AUTH_TOKEN
fi

PORT="${WTERM_PORT:-3036}"
TOKEN="${WTERM_AUTH_TOKEN:-}"

if [ -z "$1" ]; then
    echo "Usage: kill-session.sh <session-id>"
    echo "Get session IDs from: list-sessions.sh"
    exit 1
fi

RESPONSE=$(curl -sf "http://localhost:$PORT/api/sessions/$1" \
  -X DELETE \
  -H "Authorization: Bearer $TOKEN" 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "Error: failed to kill session $1 (not found or server not running)"
    exit 1
fi

echo "Killed session $1"
