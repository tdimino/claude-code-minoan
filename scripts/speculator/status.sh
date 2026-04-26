#!/bin/bash
# Speculator — Ghostty Tab Discovery Daemon Status
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"
LOG_FILE="$SCRIPT_DIR/logs/speculator.log"
JSON_FILE="$DATA_DIR/ghostty-sessions.json"
LABEL="com.minoan.speculator"

G='\033[32m' Y='\033[33m' R='\033[31m' C='\033[36m' D='\033[90m' B='\033[1m' N='\033[0m'

echo -e "${B}Speculator — Ghostty Tab Discovery Daemon${N}"
echo ""

# Daemon status
LAUNCHCTL_OUT=$(launchctl list "$LABEL" 2>&1)
if echo "$LAUNCHCTL_OUT" | grep -q "PID"; then
    PID=$(echo "$LAUNCHCTL_OUT" | grep '"PID"' | awk '{print $NF}' | tr -d ';')
    echo -e "  Daemon:   ${G}running${N} (PID $PID)"
elif echo "$LAUNCHCTL_OUT" | grep -q "Could not find"; then
    echo -e "  Daemon:   ${R}not loaded${N}"
else
    EXIT_CODE=$(echo "$LAUNCHCTL_OUT" | grep '"LastExitStatus"' | awk '{print $NF}' | tr -d ';')
    echo -e "  Daemon:   ${Y}stopped${N} (exit: ${EXIT_CODE:-?})"
fi

# Last snapshot
if [ -f "$JSON_FILE" ]; then
    TIMESTAMP=$(python3 -c "import json; print(json.load(open('$JSON_FILE'))['timestamp'][:19])" 2>/dev/null)
    GHOSTTY=$(python3 -c "import json; d=json.load(open('$JSON_FILE')); print('running' if d['ghostty']['running'] else 'not running')" 2>/dev/null)
    SESSIONS=$(python3 -c "import json; d=json.load(open('$JSON_FILE')); print(d['stats']['ttys_with_claude'])" 2>/dev/null)
    TTYS=$(python3 -c "import json; d=json.load(open('$JSON_FILE')); print(d['stats']['total_ttys'])" 2>/dev/null)
    STATUSES=$(python3 -c "
import json
d=json.load(open('$JSON_FILE'))
parts = [f'{v} {k}' for k,v in sorted(d['stats']['sessions_by_status'].items())]
print(', '.join(parts) if parts else 'none')
" 2>/dev/null)

    # Snapshot age
    AGE_SEC=$(python3 -c "
from datetime import datetime, timezone
import json
ts = json.load(open('$JSON_FILE'))['timestamp']
dt = datetime.fromisoformat(ts)
age = (datetime.now(timezone.utc) - dt).total_seconds()
print(int(age))
" 2>/dev/null)

    if [ -n "$AGE_SEC" ] && [ "$AGE_SEC" -lt 360 ]; then
        AGE_COLOR="$G"
    elif [ -n "$AGE_SEC" ] && [ "$AGE_SEC" -lt 900 ]; then
        AGE_COLOR="$Y"
    else
        AGE_COLOR="$R"
    fi

    echo -e "  Snapshot: ${AGE_COLOR}${TIMESTAMP}${N} (${AGE_SEC}s ago)"
    echo -e "  Ghostty:  ${C}${GHOSTTY}${N}"
    echo -e "  Sessions: ${B}${SESSIONS}${N} Claude across ${TTYS} tabs (${STATUSES})"
else
    echo -e "  Snapshot: ${D}no data yet${N}"
fi

# Recent log
echo ""
if [ -f "$LOG_FILE" ]; then
    echo -e "${D}Recent log:${N}"
    tail -5 "$LOG_FILE" | sed 's/^/  /'
else
    echo -e "${D}No log file yet${N}"
fi
