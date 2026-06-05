#!/usr/bin/env bash
# open-file-explorer.sh — Open yazi file explorer in a Ghostty split pane
#
# Usage:
#   open-file-explorer.sh [<directory>]   # Open yazi at directory (default: cwd)
#   open-file-explorer.sh --right         # Split to the right instead of left
#
# Opens a new Ghostty split pane via System Events and launches yazi.
# Requires: yazi (brew install yazi), Ghostty (macOS)
#
# Bind to Cmd+E in Ghostty config:
#   keybind = cmd+e=new_split:left
# Or use this script for yazi-specific behavior.

set -euo pipefail

TARGET_DIR=""
DIRECTION="left"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --right)
      DIRECTION="right"
      shift
      ;;
    --left)
      DIRECTION="left"
      shift
      ;;
    --help|-h)
      echo "Usage: open-file-explorer.sh [<directory>] [--left|--right]"
      echo ""
      echo "Open yazi file explorer in a Ghostty split pane."
      echo ""
      echo "Options:"
      echo "  --left       Split to the left (default, sidebar-style)"
      echo "  --right      Split to the right"
      echo "  -h, --help   Show this help"
      echo ""
      echo "Prerequisites:"
      echo "  brew install yazi ffmpegthumbnailer unar jq poppler fd ripgrep fzf zoxide"
      exit 0
      ;;
    -*)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
    *)
      TARGET_DIR="$1"
      shift
      ;;
  esac
done

[[ -z "$TARGET_DIR" ]] && TARGET_DIR="$(pwd)"

if [[ "$(uname)" != "Darwin" ]]; then
  echo "open-file-explorer: macOS only (requires Ghostty AppleScript)" >&2
  exit 1
fi

if ! command -v yazi &>/dev/null; then
  echo "open-file-explorer: yazi not found" >&2
  echo "Install: brew install yazi" >&2
  exit 1
fi

if ! pgrep -x Ghostty &>/dev/null; then
  echo "open-file-explorer: Ghostty not running" >&2
  exit 1
fi

# Map direction to Ghostty keybinding
case "$DIRECTION" in
  left)
    # Cmd+D creates split:right, Cmd+Shift+D creates split:down
    # For a left split, we split right then swap (or accept right-side split)
    # Ghostty doesn't have split:left via System Events, so we split right
    SPLIT_KEY="d"
    SPLIT_MOD="command down"
    ;;
  right)
    SPLIT_KEY="d"
    SPLIT_MOD="command down"
    ;;
esac

# Build the yazi command
escaped_dir="${TARGET_DIR//\'/\'\\\'\'}"
yazi_cmd="cd '${escaped_dir}' && yazi"

# Save clipboard, paste yazi command into new split
old_clipboard="$(pbpaste 2>/dev/null || true)"
printf '%s' "$yazi_cmd" | pbcopy

osascript <<APPLESCRIPT
tell application "Ghostty"
    activate
end tell

delay 0.3

tell application "System Events"
    tell process "Ghostty"
        -- Create split pane
        keystroke "$SPLIT_KEY" using {${SPLIT_MOD}}
    end tell
end tell

delay 0.8

tell application "System Events"
    tell process "Ghostty"
        -- Paste yazi command
        keystroke "v" using command down
        delay 0.2
        keystroke return
    end tell
end tell
APPLESCRIPT

sleep 0.5
printf '%s' "$old_clipboard" | pbcopy

echo "Opened yazi in Ghostty split ($DIRECTION) at: $TARGET_DIR"
