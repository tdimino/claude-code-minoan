#!/usr/bin/env bash
# Launch Recordly — detect install location and open
# Usage: bash launch_recordly.sh [recording-or-project-file]

set -euo pipefail

FILE_ARG="${1:-}"

# macOS: /Applications or built from source
if [ -d "/Applications/Recordly.app" ]; then
    echo "Launching Recordly from /Applications..."
    if [ -n "$FILE_ARG" ]; then
        open -a "/Applications/Recordly.app" "$FILE_ARG"
    else
        open -a "/Applications/Recordly.app"
    fi
elif APP=$(find "$HOME/tools/recordly/dist" -name "Recordly.app" -maxdepth 3 2>/dev/null | head -1) && [ -n "$APP" ]; then
    echo "Launching Recordly from $APP..."
    if [ -n "$FILE_ARG" ]; then
        open -a "$APP" "$FILE_ARG"
    else
        open -a "$APP"
    fi
# Linux: AppImage
elif APPIMAGE=$(find "$HOME/tools/recordly/dist" -name "*.AppImage" -maxdepth 3 2>/dev/null | head -1) && [ -n "$APPIMAGE" ]; then
    echo "Launching Recordly AppImage..."
    "$APPIMAGE" ${FILE_ARG:+"$FILE_ARG"} &
    PID=$!
    sleep 2
    if ! kill -0 "$PID" 2>/dev/null; then
        echo "ERROR: Recordly failed to start. Check output above."
        echo "Common fix on Linux: install FUSE (apt install libfuse2)"
        exit 1
    fi
    echo "Recordly running (PID: $PID)."
else
    echo "ERROR: Recordly not found."
    echo "Install it first: bash $(dirname "$0")/install_recordly.sh"
    exit 1
fi
