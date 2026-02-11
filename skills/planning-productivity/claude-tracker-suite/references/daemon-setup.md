# Daemon Setup

## claude-tracker-watch

Auto-summarize new sessions and regenerate `active-projects.md`.

See SKILL.md "Auto-Summarize Daemon" section for CLI usage (`--daemon`, `--status`, `--stop`, `--verbose`).

### Auto-Start with launchd (macOS)

Create `~/Library/LaunchAgents/com.claude.tracker-watch.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.claude.tracker-watch</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/node</string>
        <string>/Users/USERNAME/.local/bin/claude-tracker-watch</string>
        <string>--verbose</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/USERNAME/.claude/logs/tracker-watch.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/USERNAME/.claude/logs/tracker-watch.log</string>
</dict>
</plist>
```

Replace `USERNAME` with your actual username, then:

```bash
launchctl load ~/Library/LaunchAgents/com.claude.tracker-watch.plist
```

### How It Works

1. Watches `~/.claude/projects/*/sessions-index.json` for changes
2. On change (5s debounce): reads new entries, populates summary cache
3. Runs `update-active-projects.py` to regenerate `active-projects.md`
4. Re-scans for new project directories every 60 seconds
5. PID file at `~/.claude/.tracker-watch.pid` for daemon management
