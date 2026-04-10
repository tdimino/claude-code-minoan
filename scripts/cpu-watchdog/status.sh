#!/bin/bash
# Phroura CPU Watchdog — Quick Status Check
# Usage: ~/.claude/scripts/cpu-watchdog/status.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/cpu-watchdog.log"
STATE_FILE="$SCRIPT_DIR/data/state.json"

# Colors
G='\033[32m' Y='\033[33m' R='\033[31m' C='\033[36m' D='\033[90m' B='\033[1m' N='\033[0m'

echo -e "${B}Phroura CPU Watchdog${N}"
echo ""

# 1. Daemon status
launchd_info=$(launchctl list 2>/dev/null | grep "com.minoan.cpu-watchdog")
if [ -n "$launchd_info" ]; then
    pid=$(echo "$launchd_info" | awk '{print $1}')
    exit_code=$(echo "$launchd_info" | awk '{print $2}')
    if [ "$pid" != "-" ]; then
        echo -e "  ${G}RUNNING${N}  PID $pid"
    elif [ "$exit_code" = "0" ]; then
        echo -e "  ${G}IDLE${N}  (last exit: 0)"
    else
        echo -e "  ${Y}STOPPED${N}  (last exit code: $exit_code)"
    fi
else
    echo -e "  ${R}NOT LOADED${N}  — run: launchctl load ~/Library/LaunchAgents/com.minoan.cpu-watchdog.plist"
fi

# 2. Config (single python3 invocation)
if [ -f "$SCRIPT_DIR/config.json" ]; then
    read interval threshold checks < <(python3 - "$SCRIPT_DIR/config.json" <<'PYEOF'
import json, sys
c = json.load(open(sys.argv[1]))
print(c.get('poll_interval_sec',30), c.get('cpu_threshold_pct',90), c.get('consecutive_checks',3))
PYEOF
    )
    echo -e "  ${D}Config:${N} poll=${interval:-30}s, threshold=${threshold:-90}%, checks=${checks:-3}"
fi

# 3. Active Claude sessions
claude_count=$(ps aux | grep -E '\bclaude\b' | grep -v 'grep\|claude-peers\|claude-plugins' | wc -l | tr -d ' ')
echo -e "  ${D}Active Claude sessions:${N} $claude_count"

# 4. Tracked PIDs from state
if [ -f "$STATE_FILE" ]; then
    read tracked hot < <(python3 - "$STATE_FILE" "${checks:-3}" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
t = int(sys.argv[2])
print(len(d), sum(1 for s in d.values() if s.get('hot_count', 0) >= t))
PYEOF
    )
    echo -e "  ${D}Tracked PIDs:${N} ${tracked:-0} (${hot:-0} hot)"
fi

# 5. Last alert
if [ -f "$LOG_FILE" ]; then
    last_alert=$(grep "CPU WATCHDOG\|ORPHAN DETECTED" "$LOG_FILE" | tail -1)
    if [ -n "$last_alert" ]; then
        echo ""
        echo -e "  ${Y}Last alert:${N}"
        echo "    $last_alert"
    fi
fi

# 6. Recent errors
if [ -f "$LOG_FILE" ]; then
    recent_errors=$(tail -50 "$LOG_FILE" | grep -i "ERROR" | tail -3)
    if [ -n "$recent_errors" ]; then
        echo ""
        echo -e "  ${R}Recent errors:${N}"
        echo "$recent_errors" | while read -r line; do
            echo "    $line"
        done
    fi
fi

# 7. Recent log
if [ -f "$LOG_FILE" ]; then
    echo ""
    echo -e "  ${D}Recent log:${N}"
    tail -5 "$LOG_FILE" | while read -r line; do
        echo "    $line"
    done
fi

echo ""
