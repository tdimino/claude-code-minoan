#!/usr/bin/env bash
#
# Manage the Slack daemon LaunchAgent.
#
# Usage:
#   install.sh install    — Load and start the daemon
#   install.sh uninstall  — Stop and unload the daemon
#   install.sh status     — Check if running
#   install.sh logs       — Tail daemon logs
#   install.sh restart    — Unload + load

set -euo pipefail

PLIST_NAME="com.minoan.slack-daemon"
PLIST_SRC="$(cd "$(dirname "$0")" && pwd)/${PLIST_NAME}.plist"
PLIST_DST="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
LOG_DIR="$(cd "$(dirname "$0")/../logs" && pwd)"

case "${1:-help}" in
    install)
        if [[ ! -f "$PLIST_SRC" ]]; then
            echo "Error: $PLIST_SRC not found"
            exit 1
        fi
        # Check tokens are set in plist (not placeholder)
        if grep -q "YOUR-BOT-TOKEN\|YOUR-APP-TOKEN" "$PLIST_SRC"; then
            echo "Error: Update tokens in $PLIST_SRC before installing"
            echo "  SLACK_BOT_TOKEN and SLACK_APP_TOKEN must be real values"
            exit 1
        fi
        cp "$PLIST_SRC" "$PLIST_DST"
        launchctl load "$PLIST_DST"
        echo "Loaded $PLIST_NAME"
        sleep 1
        "$0" status
        ;;

    uninstall)
        if launchctl list | grep -q "$PLIST_NAME"; then
            launchctl unload "$PLIST_DST"
            echo "Unloaded $PLIST_NAME"
        else
            echo "$PLIST_NAME not loaded"
        fi
        rm -f "$PLIST_DST"
        ;;

    status)
        if launchctl list | grep -q "$PLIST_NAME"; then
            PID=$(launchctl list | grep "$PLIST_NAME" | awk '{print $1}')
            echo "$PLIST_NAME is running (PID: $PID)"
        else
            echo "$PLIST_NAME is not running"
        fi
        ;;

    logs)
        echo "=== stdout ==="
        tail -f "$LOG_DIR/stdout.log" "$LOG_DIR/stderr.log" "$LOG_DIR/daemon.log" 2>/dev/null
        ;;

    restart)
        "$0" uninstall
        sleep 2
        "$0" install
        ;;

    *)
        echo "Usage: $0 {install|uninstall|status|logs|restart}"
        exit 1
        ;;
esac
