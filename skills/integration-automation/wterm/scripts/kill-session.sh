#!/bin/bash
# Kill a wterm session by ID
# Usage: kill-session.sh <session-id>

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
