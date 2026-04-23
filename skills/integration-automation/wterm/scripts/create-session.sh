#!/bin/bash
# Create a new wterm session
# Usage: create-session.sh [command] [name]

# Auto-load auth token from secrets.env if not already set
if [ -z "$WTERM_AUTH_TOKEN" ] && [ -f ~/.config/env/secrets.env ]; then
    WTERM_AUTH_TOKEN=$(grep '^WTERM_AUTH_TOKEN=' ~/.config/env/secrets.env | cut -d= -f2)
    export WTERM_AUTH_TOKEN
fi

PORT="${WTERM_PORT:-3036}"
TOKEN="${WTERM_AUTH_TOKEN:-}"
COMMAND="${1:-/bin/zsh}"
NAME="${2:-}"

BODY=$(python3 -c "
import json, sys
d = {'command': sys.argv[1]}
if sys.argv[2]:
    d['name'] = sys.argv[2]
print(json.dumps(d))
" "$COMMAND" "$NAME")

RESPONSE=$(curl -sf "http://localhost:$PORT/api/sessions" \
  -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$BODY" 2>&1)

if [ $? -ne 0 ]; then
    echo "Error: failed to create session (is wterm-server running?)"
    echo "Detail: $RESPONSE"
    exit 1
fi

echo "$RESPONSE" | python3 -c "
import sys, json
s = json.load(sys.stdin)
if 'error' in s:
    print(f'Error: {s[\"error\"]}')
    sys.exit(1)
print(f'Created session {s[\"id\"]} ({s[\"name\"]})')
print(f'  Command: {s[\"command\"]}')
print(f'  PID: {s[\"pid\"]}')
import socket
print(f'  Open in browser: http://{socket.gethostname()}:{$PORT}')
"
