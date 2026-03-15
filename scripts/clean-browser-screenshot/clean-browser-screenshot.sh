#!/bin/bash
# Clean Browser Screenshot
# Enters browser fullscreen, captures via CleanShot (auto-save), exits fullscreen.
# Result: a screenshot with no browser toolbar or UI chrome.
#
# Assumes: browser is frontmost and not already in fullscreen.
# Requires: CleanShot X running, Accessibility permission for Shortcuts/Terminal.
#
# Usage: ./clean-browser-screenshot.sh
# Bind to a keyboard shortcut via macOS Shortcuts app.

# Enter fullscreen (Cmd+Shift+F — universal across Chrome/Arc/Safari)
osascript -e 'tell application "System Events" to keystroke "f" using {command down, shift down}'

# Wait for macOS fullscreen animation (1.5s is safer than 1.0s under load)
sleep 1.5

# Trigger CleanShot fullscreen capture with auto-save
# ?action=save bypasses annotation overlay, preventing focus from landing
# in CleanShot before the exit-fullscreen keystroke fires
open "cleanshot://capture-fullscreen?action=save"

# Wait for capture + save to complete
sleep 2

# Exit fullscreen
osascript -e 'tell application "System Events" to keystroke "f" using {command down, shift down}'
