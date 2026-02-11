# Claude Session Tracker

VS Code extension to track and resume Claude Code sessions after crashes or disconnections. Displays enriched session data — AI-generated titles, model name, turn count, and cost — from the `claude-tracker-suite` CLI.

## Features

- **Session Browser** — TreeView in Explorer sidebar showing recent sessions with AI-generated titles, model, turn count, and cost
- **Cross-Window Tracking** — See total Claude sessions across ALL VS Code windows (e.g., "Claude Active (7)")
- **Automatic Detection** — Recognizes terminals running Claude Code via name matching and process inspection
- **Enriched Display** — Consumes `sessions-index.json` and `session-summaries.json` for model, turns, cost, and AI-generated titles
- **Status Bar** — Shows active session count with cumulative cost
- **Crash Recovery** — Cross-window state tracking detects crashed sessions and offers one-click resume
- **Quick Resume** — `Cmd+Shift+C` to instantly resume your last session
- **Session Picker** — Browse and resume from recent sessions with enriched metadata
- **Auto-Refresh** — FileSystemWatchers on index and summary files update the TreeView automatically
- **Multi-Root Workspace Support** — Tracks sessions for all workspace folders
- **Sidechain Filtering** — Hides observer/memory sessions from the browser

## Commands

| Command | Keybinding | Description |
|---------|------------|-------------|
| Resume Last Claude Session | `Cmd+Shift+C` | Resume the most recent session for this workspace |
| Pick Claude Session | — | Browse recent sessions for current workspace |
| View Claude Sessions | — | Active terminals + recent resumable sessions |
| Browse All Claude Sessions | — | Browse sessions across ALL projects |
| Recover Claude Sessions from Crash | — | Pick which crashed sessions to recover |
| Resume All Crashed Sessions | — | One-click resume all crashed sessions |
| Refresh Claude Sessions | — | Manually refresh the session browser |

## How It Works

1. When you run `claude` in a VS Code terminal, the extension detects it
2. **Cross-window state** is shared via `~/.claude/vscode-tracker-state.json`
3. Status bar shows total Claude sessions across ALL VS Code windows
4. If VS Code closes or crashes, the session is marked as "recoverable"
5. When you reopen VS Code, a notification offers to resume crashed sessions
6. Press `Cmd+Shift+C` or click the status bar to resume where you left off

### Data Sources

The extension reads two pre-computed JSON files (produced by the `claude-tracker-suite` CLI) instead of parsing raw JSONL session logs:

- **`~/.claude/projects/<dir>/sessions-index.json`** — Session metadata per project (ID, title, first prompt, branch, timestamps, sidechain flag)
- **`~/.claude/session-summaries.json`** — Enriched data from tracker daemon (model, turns, cost, AI-generated title/summary)

These are merged to produce `EnrichedSession` objects displayed across TreeView, QuickPick, and status bar. Without the tracker-suite, the extension falls back to basic display (first prompt + branch).

### Cross-Window Tracking

Each VS Code window runs its own extension instance, but they communicate via a shared state file:

- **State File**: `~/.claude/vscode-tracker-state.json`
- **Heartbeat**: Every 10 seconds, each window updates its status
- **Stale Detection**: Windows that don't update for 30 seconds are considered crashed
- **Tooltip Info**: Hover over status bar to see distribution (e.g., "4 in this window, 3 in other window(s)")

Under the hood, this uses Claude Code's built-in flags:
- `claude --continue` — Resume most recent session for current directory
- `claude --resume <sessionId>` — Resume a specific session by ID

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `claudeTracker.autoResume` | `false` | Prompt to resume last session on workspace open |
| `claudeTracker.showStatusBar` | `true` | Show Claude session status in status bar |
| `claudeTracker.showCostInStatusBar` | `true` | Show session cost in status bar |
| `claudeTracker.showEnrichedData` | `true` | Show model, turns, and cost in session browser and quick picks |
| `claudeTracker.hideSidechainSessions` | `true` | Hide observer/sidechain sessions from session browser |

## Architecture

```
src/
├── extension.ts          # Activation, FileSystemWatchers, crash recovery flow
├── commands.ts           # Command handlers + session loading from index/cache
├── sessionBrowser.ts     # TreeView provider with enriched session display
├── statusBar.ts          # Status bar (active/resumable/recoverable states + cost)
├── terminalWatcher.ts    # Terminal lifecycle detection via process inspection
├── crossWindowState.ts   # Cross-window state via shared JSON + atomic writes
├── sessionStorage.ts     # VS Code globalState persistence for tracked sessions
├── types.ts              # EnrichedSession, SessionIndexEntry, SessionSummaryCache
├── utils.ts              # Path encoding, git branch, config getters, formatters
└── logger.ts             # Output channel logger
```

## Known Limitations

- **Windows Support**: Process detection uses WMIC which may be deprecated on newer Windows versions
- **Cost Lag**: Session cost appears after the tracker-suite daemon processes it, not in real-time
- **Enrichment Optional**: Without `claude-tracker-suite` installed, sessions display with basic metadata only

## Requirements

- VS Code 1.85.0+
- Claude Code CLI installed and in PATH
- Optional: `claude-tracker-suite` CLI skill for enriched session data

## Development

```bash
npm install
npm run compile   # or: npm run watch
```

Press `F5` in VS Code to launch the Extension Development Host.

## Version History

### 0.3.0

- Replace JSONL parsing with index + summary cache reads
- Enriched TreeView: AI-generated titles, model, turn count, cost in tooltips
- Enriched QuickPick items across all session commands
- Status bar cost display
- FileSystemWatchers for auto-refresh on data changes
- Sidechain session filtering
- New settings: `showCostInStatusBar`, `showEnrichedData`, `hideSidechainSessions`

### 0.2.1

- Cross-window session tracking via shared state file
- Crash recovery with resume-all
- Process inspection for Claude terminal detection
- Git branch detection with detached HEAD support
- Multi-root workspace support

### 0.1.0

- Initial release: terminal tracking, status bar, session resume

## License

MIT
