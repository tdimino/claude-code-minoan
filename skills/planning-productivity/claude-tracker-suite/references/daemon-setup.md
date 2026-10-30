# Daemon Setup

Three launchd agents ship in `scripts/` and are the ones that matter today (copy to `~/Library/LaunchAgents/`, then `launchctl load`):

| Agent | Runs | Cadence | Logs |
|-------|------|---------|------|
| `com.claude.workspace-snapshot` | `save-workspace.js` | every 300 s | `/tmp/claude-workspace-snapshot.{log,err}` |
| `com.claude.transcript-index` | `index-transcripts.js --quiet` | hourly + at load | `~/.claude/logs/transcript-index.{log,err}` |
| `com.claude.db-maintain` | `db-maintain.js` | Sunday 04:30 | `/tmp/claude-db-maintain.{log,err}` |

All use `/opt/homebrew/bin/node` (Homebrew). The transcript indexer also runs from the Stop hook (async) and the SessionEnd hook (`--detach`, so indexing never holds up exit), so the hourly agent is a safety net for sessions that die without a hook, for pruning deleted transcripts, and for closing phases those sessions left open.

## claude-tracker-watch (dormant)

Watches `sessions-index.json`, which Claude Code stopped writing—the watcher never fires on current versions. Kept for reference only.

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
        <string>/opt/homebrew/bin/node</string>
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

1. Watches `~/.claude/projects/*/sessions-index.json` for changes (dormant: Claude Code no longer writes this file, so the watcher never fires)
2. On change (5s debounce): reads new entries, populates summary cache
3. Runs `update-active-projects.py` to regenerate `active-projects.md`
4. Re-scans for new project directories every 60 seconds
5. PID file at `~/.claude/.tracker-watch.pid` for daemon management

## Hook timeouts

The hook `timeout` field is in **seconds**. Tracker hooks: `session-sync-db.py` 10, Stop indexer 120 (async, so not enforced), `phase-detect.py` 5, `plan-rename.py` 10, SessionEnd indexer 5. SessionEnd hooks share a 1.5 s budget that rises to the largest per-hook `timeout` (60 s cap), so keep SessionEnd work detached rather than raising timeouts. A SessionEnd hook with no `timeout` of its own still gets only 1.5 s. Any tracker hook `timeout` above 600 is a units bug (an `audit-suite.js` check for it is planned, not built).
