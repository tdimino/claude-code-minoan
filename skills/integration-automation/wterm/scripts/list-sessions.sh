#!/bin/bash
# List active wterm sessions

PORT="${WTERM_PORT:-3036}"
TOKEN="${WTERM_AUTH_TOKEN:-}"

RESPONSE=$(curl -sf "http://localhost:$PORT/api/sessions" \
  -H "Authorization: Bearer $TOKEN" 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "Error: wterm-server not responding on port $PORT"
    exit 1
fi

echo "$RESPONSE" | python3 -c "
import sys, json
sessions = json.load(sys.stdin)
if not sessions:
    print('No active sessions')
    sys.exit(0)
print(f'{'ID':<14} {'Name':<20} {'Command':<12} {'PID':<8} {'Clients':<9} Last Activity')
print('-' * 85)
for s in sessions:
    last = s['lastActivity'][:19].replace('T', ' ')
    print(f'{s[\"id\"]:<14} {s[\"name\"]:<20} {s[\"command\"]:<12} {s[\"pid\"]:<8} {s[\"clientCount\"]:<9} {last}')
"
