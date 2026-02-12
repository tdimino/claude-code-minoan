# Sounds (`sounds/`)

Audio files used by hooks for notifications.

## `soft-ui.mp3`

Gentle notification sound played by `on-ready.sh` when Claude finishes a response. Designed to be non-intrusive in a multi-session workflow.

**Played by**: `terminal-title.sh` (via `afplay`) on the Stop hook
**Platform**: macOS only (`afplay` is a macOS command)

## Customization

Replace `soft-ui.mp3` with any audio file to change the notification sound. Keep it short (< 2 seconds) to avoid overlap with rapid Claude responses.

```bash
# Use a custom sound
cp your-notification.mp3 ~/.claude/sounds/soft-ui.mp3
```
