#!/bin/bash
# syspeek — Quick Status Check

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="$SCRIPT_DIR/data"
LOG_FILE="$SCRIPT_DIR/logs/syspeek.log"

G='\033[32m' Y='\033[33m' R='\033[31m' C='\033[36m' D='\033[90m' B='\033[1m' N='\033[0m'

echo -e "${B}syspeek System Monitor${N}"
echo ""

# 1. Daemon status
launchd_info=$(launchctl list 2>/dev/null | grep "com.minoan.syspeek")
if [ -n "$launchd_info" ]; then
    pid=$(echo "$launchd_info" | awk '{print $1}')
    if [ "$pid" != "-" ] && [ "$pid" != "0" ]; then
        echo -e "  Daemon:   ${G}RUNNING${N}  PID $pid"
    else
        echo -e "  Daemon:   ${Y}IDLE${N}  (loaded but not running)"
    fi
else
    echo -e "  Daemon:   ${D}NOT LOADED${N}"
fi

# 2. Data directory
if [ -d "$DATA_DIR" ]; then
    today=$(date +%Y-%m-%d)
    today_file="$DATA_DIR/$today.jsonl"
    if [ -f "$today_file" ]; then
        count=$(wc -l < "$today_file" | tr -d ' ')
        echo -e "  Today:    ${C}$count snapshots${N}"
    else
        echo -e "  Today:    ${D}0 snapshots${N}"
    fi
    total_files=$(ls -1 "$DATA_DIR"/*.jsonl 2>/dev/null | wc -l | tr -d ' ')
    gz_files=$(ls -1 "$DATA_DIR"/*.gz 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  Data:     ${D}$total_files active, $gz_files archived${N}"
else
    echo -e "  Data:     ${D}no data directory${N}"
fi

# 3. Ensouled status
if [ -f "$HOME/.claudicle/soul/soul.md" ]; then
    echo -e "  Ensouled: ${C}yes${N} (writing to memory.db)"
else
    echo -e "  Ensouled: ${D}no${N} (JSONL only)"
fi

# 4. Last snapshot
if [ -f "$LOG_FILE" ]; then
    last=$(grep "Snapshot\|Recorded" "$LOG_FILE" | tail -1)
    if [ -n "$last" ]; then
        echo ""
        echo -e "  Last:     ${D}$last${N}"
    fi
fi

echo ""
