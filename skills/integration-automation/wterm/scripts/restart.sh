#!/bin/bash
# Restart the wterm-server LaunchAgent

LABEL="com.minoan.wterm-server"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

if [ ! -f "$PLIST" ]; then
    echo "Error: LaunchAgent not installed at $PLIST"
    echo "Install with: bash ~/.claude/skills/wterm/launchd/install.sh install"
    exit 1
fi

echo "Stopping $LABEL..."
launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null

sleep 1

echo "Starting $LABEL..."
if ! launchctl bootstrap "gui/$(id -u)" "$PLIST"; then
    echo "Error: Failed to start $LABEL"
    echo "Check: launchctl print gui/$(id -u)/$LABEL"
    exit 1
fi

sleep 2
bash "$(dirname "$0")/status.sh"
