# Clean Browser Screenshot

Take browser screenshots with no toolbar, tabs, or UI chrome. Enters fullscreen, triggers CleanShot X capture with auto-save, then exits fullscreen.

## How It Works

1. Sends `Cmd+Shift+F` to enter browser fullscreen (universal across Chrome, Arc, Safari)
2. Waits 1.5s for the macOS fullscreen animation to complete
3. Triggers `cleanshot://capture-fullscreen?action=save` (auto-saves, no annotation overlay)
4. Waits 2s for capture + save
5. Sends `Cmd+Shift+F` again to exit fullscreen

## Requirements

- **CleanShot X** (running)
- **Accessibility permission** for Terminal or Shortcuts app (System Settings > Privacy & Security > Accessibility)
- Browser must be frontmost and not already in fullscreen

## Setup

```bash
# Copy to scripts directory
cp clean-browser-screenshot.sh ~/.claude/scripts/
chmod +x ~/.claude/scripts/clean-browser-screenshot.sh
```

### Bind to keyboard shortcut (macOS Shortcuts app)

1. Open **Shortcuts** app
2. Click **+** → name it "Clean Browser Screenshot"
3. Add action: **Run Shell Script**
4. Paste: `~/.claude/scripts/clean-browser-screenshot.sh`
5. Click shortcut name → **Add Keyboard Shortcut** → press your combo (e.g. `Ctrl+Opt+Cmd+S`)

## Usage

```bash
# Run directly
~/.claude/scripts/clean-browser-screenshot.sh

# Or trigger via keyboard shortcut (after Shortcuts app setup)
```

Screenshots land in your CleanShot save directory (default: `~/Desktop/Screencaps & Chats/Screenshots/`). If the [screenshot-rename](../screenshot-rename/) daemon is running, files are auto-renamed via vision AI within ~5 seconds.

## Edge Cases

- **Already in fullscreen**: The first `Cmd+Shift+F` will *exit* fullscreen, capturing the wrong state. Ensure the browser is in windowed mode before triggering.
- **Non-browser focused**: The keystroke goes to whatever app has focus. If invoked from a global shortcut while another app is frontmost, uncomment the browser activation line in the script.
- **Multi-monitor**: CleanShot captures the screen containing the cursor. Ensure the cursor is on the same screen as the browser.

## Files

| File | Purpose |
|------|---------|
| `clean-browser-screenshot.sh` | Main script: fullscreen → capture → exit fullscreen |
