# CLI Tools (`bin/`)

Terminal commands for managing Claude Code and Codex sessions. Copy to `~/.local/bin/` (or anywhere on your `$PATH`).

## Installation

```bash
cp bin/* ~/.local/bin/
mkdir -p ~/.claude/lib ~/.claude/scripts && cp lib/* ~/.claude/lib/
cp scripts/ghostty-resume.sh ~/.claude/scripts/ && chmod +x ~/.claude/scripts/ghostty-resume.sh
```

Requires macOS, Node ≥ 22.13 (the DB layer uses the built-in `node:sqlite`—there is no `npm install`), Ghostty (≥ 1.3.0 for the native tab/split path), fzf for the picker, and the `sqlite3` CLI. The `claude-tracker*` commands are thin wrappers over the scripts in `skills/planning-productivity/claude-tracker-suite/scripts/`, so install that skill too.

## Session Management

### `claude-tracker` — List Recent Sessions

Browse recent Claude Code sessions with summaries and a LIVE badge (with TTY) taken from Claude Code's own PID files in `~/.claude/sessions/`, matched by session ID.

```bash
claude-tracker              # List recent sessions
claude-tracker --here       # Only this directory's sessions
claude-tracker --limit 5
```

### `claude-tracker-recent` — Fast Listing from tracker.db

```bash
claude-tracker-recent --limit 20 --project knossot
claude-tracker-recent --since 24h --model opus --json
claude-tracker-recent --copy          # copy the first resume command (opt-in)
```

### `claude-tracker-alive` — Live vs. Stale

```bash
claude-tracker-alive                  # running sessions + newest stale transcript per project
claude-tracker-alive --json
claude-tracker-alive --stale
```

### `codex-tracker` — Search and Inspect Codex Sessions

Use Codex's native App Server APIs to search transcript text, browse recent work, inspect one session, and print a safe native resume command.

```bash
codex-tracker search "permission profile"
codex-tracker recent --limit 10
codex-tracker show <session-id>
codex-tracker occurrences <session-id> "search phrase"
codex-tracker resume <session-id>
```

The launcher resolves `codex-tracker-suite` from either `~/.claude/skills/` or `~/.codex/skills/`. Install the skill before using it. Full-text search requires a Codex build exposing the experimental App Server search methods.

See [`skills/planning-productivity/codex-tracker-suite/README.md`](../skills/planning-productivity/codex-tracker-suite/README.md) for setup, compatibility, privacy, and operational notes.

### `claude-tracker-search` — Search Sessions

Find past sessions by topic, content, name, or ID. Searches the FTS5 transcript index in `~/.claude/tracker-transcripts.db`; the index is refreshed in-process before every search (1.5 s budget) and by Stop/SessionEnd hooks, so a session from a minute ago is findable. Sub-100 ms on a 6 GB corpus.

```bash
claude-tracker-search "kothar mac mini"           # Full-text search
claude-tracker-search "twitter banner" --open     # Resume the top hit in a Ghostty tab
claude-tracker-search --id 1da2b718               # Lookup by session ID prefix
claude-tracker-search --name knossot              # Match names/slugs/titles only
claude-tracker-search "rare term" --deep          # Streaming JSONL scan, bypasses the index
claude-tracker-search "query" --copy              # Copy the first resume command (opt-in)
```

### `claude-tracker-resume` — Crash Recovery

A crashed session is the newest transcript of a project with no live Claude process. Reopens them in Ghostty tabs through `ghostty-resume.sh`.

```bash
claude-tracker-resume              # List crashed sessions with resume commands
claude-tracker-resume --open       # Reopen each in a new Ghostty tab
claude-tracker-resume --dry-run    # Preview without acting
claude-tracker-resume --days 14    # Widen the window (default 7)
claude-tracker-resume --workspace  # Restore every claude + codex tab from the last workspace stamp
```

### `ghostty-resume.sh` — The Terminal Opener

Installed at `~/.claude/scripts/ghostty-resume.sh`. Writes a short launcher to `~/.claude/run/launch/r-<id>.sh` (checks the project dir and transcript, falls back to a fresh session with a printed reason, then `exec claude --resume <id>`) and has Ghostty run it.

```bash
ghostty-resume.sh <session-id>                       # New Ghostty tab
ghostty-resume.sh <session-id> --split               # Split the focused terminal (right; also left/down/up)
ghostty-resume.sh <session-id> --project ~/myproject # Override project dir
ghostty-resume.sh --exec "claude -n 'auth'" --project ~/p   # Any command
ghostty-resume.sh <session-id> --print               # Only write the launcher, print its path
```

On Ghostty ≥ 1.3.0 it uses the AppleScript dictionary (`new tab … with configuration`, `split … direction`), which needs no keystrokes, clipboard or focus. Older builds fall back to Cmd-T + one paste of the launcher path, with the clipboard saved and restored.

**Requires**: macOS, Ghostty

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

### `ccnew` — New Session in a Ghostty Tab

```bash
ccnew ~/Desktop/my-project                                # Interactive session
ccnew ~/Desktop/my-project --model sonnet --name "auth"   # Model override + name (resume picker / tab title)
ccnew ~/Desktop/my-project --prompt "fix the tests"       # Prompt-driven, in the tab
ccnew ~/Desktop/my-project --headless --prompt "summarize" --output-format text
ccnew ~/Desktop/my-project --cursor                       # Also open the project in Cursor
```

Wrapper for `skills/planning-productivity/claude-tracker-suite/scripts/new-session.sh`, which delegates to `ghostty-resume.sh --exec`. `ccresume` and `resume-in-vscode.sh` are retired—use `ghostty-resume.sh <session-id>` or `claude-tracker-search "…" --open`.

**Requires**: macOS, Ghostty

### `cckill` — Kill Sessions

Kill Claude Code processes by name or PID.

### `claude-tmux-status` — Tmux Statusline

Claude Code status integration for tmux status bar.

## Shared Library (`lib/tracker-utils.js`)

All tracker CLIs share `tracker-utils.js` for consistent session parsing:

- `getLiveSessions()` / `getStaleSessions()` — live sessions from `~/.claude/sessions/*.json` PID files, verified against `ps`; crash candidates per project
- `decodeProjectPath()` — encoded dir name → real path (tracker.db → transcript `cwd` → filesystem heuristic; `sessions-index.json` is no longer read)
- `buildSessionStatus()` — per-session `isRunning`, `pid`, `tty`, `liveName`, VS Code workspace membership
- `loadSessionsIndex()` — every transcript with titles/summaries from tracker.db
- `parseSession()` — Parse individual JSONL session files
- `formatAge()` — Human-readable time formatting

`tracker-db.js` wraps Node's built-in `node:sqlite` (`DatabaseSync`) with a small compatibility layer (`prepare/run/get/all/exec/pragma/transaction`), so nothing native has to be rebuilt when Node upgrades.

## Credits & Inspiration

- **Claude Code** by [Anthropic](https://github.com/anthropics/claude-code) — the CLI that makes all of this possible
- **fzf** by [Junegunn Choi](https://github.com/junegunn/fzf) — interactive fuzzy finder used by `ccpick`
- **tmux** — terminal multiplexer that enables multi-session workflows
