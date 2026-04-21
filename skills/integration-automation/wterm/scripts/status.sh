#!/bin/bash
# Check wterm-server daemon status

PORT="${WTERM_PORT:-3036}"
LABEL="com.minoan.wterm-server"

# Check launchd
LAUNCHD_STATUS=$(launchctl list "$LABEL" 2>/dev/null)
if [ $? -eq 0 ]; then
    PID=$(echo "$LAUNCHD_STATUS" | awk '{print $1}')
    echo "LaunchAgent: running (PID $PID)"
else
    echo "LaunchAgent: not loaded"
fi

# Check port — single request, capture output
HEALTH=$(curl -sf "http://localhost:$PORT/api/health" -H "Authorization: Bearer ${WTERM_AUTH_TOKEN:-}" 2>&1)
if [ $? -eq 0 ]; then
    SESSIONS=$(echo "$HEALTH" | python3 -c "import sys,json; print(json.load(sys.stdin).get('sessions', '?'))" 2>/dev/null)
    echo "Server: healthy on port $PORT"
    echo "Sessions: ${SESSIONS:-?} active"
else
    echo "Server: not responding on port $PORT"
    echo "Detail: $HEALTH"
fi
