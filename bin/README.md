# CLI Tools (`bin/`)

Terminal commands for managing Claude Code sessions. Copy to `~/.local/bin/` (or anywhere on your `$PATH`).

## Installation

```bash
cp bin/* ~/.local/bin/
mkdir -p ~/.claude/lib && cp lib/* ~/.claude/lib/
```

## Session Management

### `claude-tracker` — List Recent Sessions

Browse recent Claude Code sessions with summaries, running status, and VS Code detection.

```bash
claude-tracker              # List recent sessions
claude-tracker --json       # JSON output for scripting
```

### `claude-tracker-search` — Search Sessions

Find past sessions by topic, content, project, or date range.

```bash
claude-tracker-search "kothar mac mini"           # Full-text search
claude-tracker-search --id 1da2b718               # Lookup by session ID prefix
claude-tracker-search --project Aldea --limit 5   # Filter by project
claude-tracker-search --since 7d --json           # Last 7 days, JSON output
```

### `claude-tracker-resume` — Crash Recovery

Find crashed sessions and resume them in tmux or Terminal.app.

```bash
claude-tracker-resume              # List crashed sessions with resume commands
claude-tracker-resume --tmux       # Auto-resume in tmux windows
claude-tracker-resume --zsh        # Auto-resume in Terminal.app tabs
claude-tracker-resume --dry-run    # Preview without acting
```

## Quick Launchers

### `cc` — Session Launcher

Quick launcher for Claude Code sessions. Attaches to existing session or creates a new one.

```bash
cc                    # Launch in current directory
cc project-name       # Launch in named project
```

### `ccls` — List Running Sessions

Show all currently running Claude Code sessions.

### `ccpick` — Interactive Picker

Browse and select from running sessions with [fzf](https://github.com/junegunn/fzf).

**Requires**: `brew install fzf`

### `cckill` — Kill Sessions

Kill Claude Code processes by name or PID.

### `claude-tmux-status` — Tmux Statusline

Claude Code status integration for tmux status bar.

## Shared Library (`lib/tracker-utils.js`)

All tracker CLIs share `tracker-utils.js` for consistent session parsing:

- `loadSessionsIndex()` — Load all `sessions-index.json` into flat array
- `decodeProjectPath()` — Resolve encoded dir names to real paths
- `buildSessionStatus()` — Detect running sessions, VS Code workspace membership
- `parseSession()` — Parse individual JSONL session files
- `formatAge()` — Human-readable time formatting

## Credits & Inspiration

- **Claude Code** by [Anthropic](https://github.com/anthropics/claude-code) — the CLI that makes all of this possible
- **fzf** by [Junegunn Choi](https://github.com/junegunn/fzf) — interactive fuzzy finder used by `ccpick`
- **tmux** — terminal multiplexer that enables multi-session workflows
