#!/bin/bash
# wterm-server LaunchAgent installer
# Usage: install.sh [install|uninstall]

LABEL="com.minoan.wterm-server"
PLIST_SRC="$(dirname "$0")/com.minoan.wterm-server.plist"
PLIST_DST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_DIR="$HOME/.claude/logs"
GUI_DOMAIN="gui/$(id -u)"
NODE_BIN=$(which node 2>/dev/null || echo "/opt/homebrew/bin/node")

case "${1:-}" in
    install)
        if [ ! -d "$HOME/daimones/wterm-server" ]; then
            echo "Error: wterm-server not found at ~/daimones/wterm-server/"
            echo "Deploy the daemon first (see scripts/wterm-server/README.md)"
            exit 1
        fi

        mkdir -p "$LOG_DIR"

        sed -e "s|__HOME__|$HOME|g" -e "s|__NODE__|$NODE_BIN|g" "$PLIST_SRC" > "$PLIST_DST"

        if ! launchctl bootstrap "$GUI_DOMAIN" "$PLIST_DST"; then
            echo "Error: Failed to bootstrap $LABEL"
            exit 1
        fi
        echo "Installed and started $LABEL"
        echo "  Node: $NODE_BIN"
        echo "  Daemon: $HOME/daimones/wterm-server/"
        echo "  Logs: $LOG_DIR/wterm-server.{out,err}.log"
        sleep 2
        bash "$(dirname "$0")/../scripts/status.sh"
        ;;
    uninstall)
        launchctl bootout "$GUI_DOMAIN" "$PLIST_DST" 2>/dev/null
        rm -f "$PLIST_DST"
        echo "Uninstalled $LABEL"
        ;;
    *)
        echo "Usage: $0 [install|uninstall]"
        echo ""
        echo "Other commands:"
        echo "  Status:  bash ~/.claude/skills/wterm/scripts/status.sh"
        echo "  Restart: bash ~/.claude/skills/wterm/scripts/restart.sh"
        echo "  Logs:    tail -50 ~/.claude/logs/wterm-server.{out,err}.log"
        exit 1
        ;;
esac
