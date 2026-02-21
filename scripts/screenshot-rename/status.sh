#!/bin/bash
# Screenshot Auto-Rename Daemon — Quick Status Check
# Usage: ~/.claude/scripts/screenshot-rename/status.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WATCH_DIR="$HOME/Desktop/Screencaps & Chats/Screenshots"
LOG_FILE="$SCRIPT_DIR/logs/screenshot-rename.log"
STDERR_LOG="$SCRIPT_DIR/logs/stderr.log"

# Colors
G='\033[32m' Y='\033[33m' R='\033[31m' C='\033[36m' D='\033[90m' B='\033[1m' N='\033[0m'

echo -e "${B}Screenshot Auto-Rename Daemon${N}"
echo ""

# 1. Daemon status
launchd_info=$(launchctl list 2>/dev/null | grep "com.minoan.screenshot-rename")
if [ -n "$launchd_info" ]; then
    pid=$(echo "$launchd_info" | awk '{print $1}')
    exit_code=$(echo "$launchd_info" | awk '{print $2}')
    if [ "$pid" != "-" ]; then
        echo -e "  ${G}RUNNING${N}  PID $pid"
    elif [ "$exit_code" = "0" ]; then
        echo -e "  ${G}IDLE${N}  (waiting for filesystem event, last exit: 0)"
    else
        echo -e "  ${Y}IDLE${N}  (last exit code: $exit_code)"
    fi
else
    echo -e "  ${R}NOT LOADED${N}  — run: launchctl load ~/Library/LaunchAgents/com.minoan.screenshot-rename.plist"
fi

# 2. Provider
provider=$(grep "^PROVIDER=" "$SCRIPT_DIR/.env" 2>/dev/null | cut -d= -f2)
echo -e "  ${D}Provider:${N} ${provider:-openrouter}"

# 3. Watch directory
if [ -d "$WATCH_DIR" ]; then
    total=$(ls -1 "$WATCH_DIR" 2>/dev/null | grep -v INDEX.md | wc -l | tr -d ' ')
    pending=$(ls -1 "$WATCH_DIR" 2>/dev/null | grep -E "^(CleanShot|Screenshot) " | wc -l | tr -d ' ')
    renamed=$(ls -1 "$WATCH_DIR" 2>/dev/null | grep -E "^20[0-9]{2}-" | wc -l | tr -d ' ')
    echo -e "  ${D}Watch dir:${N} $total files ($renamed renamed, ${pending} pending)"
else
    echo -e "  ${R}Watch dir not found:${N} $WATCH_DIR"
fi

# 4. Last rename
if [ -f "$LOG_FILE" ]; then
    last_rename=$(grep " -> " "$LOG_FILE" | grep -v "DRY RUN" | tail -1)
    if [ -n "$last_rename" ]; then
        echo ""
        echo -e "  ${C}Last rename:${N}"
        echo "    $last_rename"
    fi
fi

# 5. Recent errors
if [ -f "$LOG_FILE" ]; then
    recent_errors=$(tail -50 "$LOG_FILE" | grep -i "WARNING\|ERROR" | tail -3)
    if [ -n "$recent_errors" ]; then
        echo ""
        echo -e "  ${Y}Recent warnings:${N}"
        echo "$recent_errors" | while read -r line; do
            echo "    $line"
        done
    fi
fi

# 6. Recent activity (last 5 log lines)
if [ -f "$STDERR_LOG" ]; then
    echo ""
    echo -e "  ${D}Recent log:${N}"
    tail -5 "$STDERR_LOG" | while read -r line; do
        echo "    $line"
    done
fi

echo ""
