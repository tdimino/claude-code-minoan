# Claude Tracker Suite

Session management for Claude Code. Search, resume, spawn, and open sessions across projects---with cmux/Ghostty terminal integration, named sessions, workspace save/restore, macOS notifications, crash recovery, git-aware tracking, weighted search ranking, and new machine bootstrapping.

**Last updated:** 2026-06-05

**Terminal targets:** cmux (preferred, deterministic CLI), Ghostty (OSC escape sequences + AppleScript), VS Code, Cursor

---

## Why This Skill Exists

Claude Code sessions accumulate fast. After a week of active development, you might have 50+ sessions across 10 projects, some crashed mid-task, some with critical context that wasn't committed. Finding the right session to resume---by topic, by project, by what you were working on---requires searching across summaries, first prompts, branches, and project paths.

This skill provides 13+ scripts that handle session lifecycle: interactive session opening in cmux/Ghostty tabs, named sessions with automatic tab titles, workspace save/restore across Ghostty restarts, macOS notifications for session events, yazi file explorer integration, search with weighted ranking and ID prefix lookup, crash recovery with alive detection, headless spawning for automation, project discovery, and a bootstrap generator for new machines.

---

## Structure

```
claude-tracker-suite/
  SKILL.md                                 # CLI reference and workflows
  README.md                                # This file
  references/
    cmux-commands.md                       # Complete cmux CLI reference
    daemon-setup.md                        # Watcher daemon lifecycle and launchd plist
    data-schemas.md                        # Session index, summary cache, JSONL schemas
  scripts/
    open-sessions.js                       # List top N sessions, open in cmux/Ghostty tabs
    resume-session.sh                      # Open single session in cmux/Ghostty
    search-sessions.js                     # Keyword search + --id prefix lookup
    list-sessions.js                       # List recent sessions with status badges
    new-session.sh                         # Start new interactive/prompt-driven/headless session
    claude-wrapper.sh                      # Shell function `cc` for named sessions with tab titles
    save-workspace.js                      # Snapshot alive sessions to workspace-state.json
    restore-workspace.sh                   # Restore sessions from workspace-state.json
    session-notify.sh                      # macOS notifications + Ghostty tab badges
    open-file-explorer.sh                  # Open yazi in Ghostty split pane
    com.claude.workspace-snapshot.plist    # launchd plist for periodic workspace snapshots
    bootstrap-claude-setup.js              # Generate complete ~/.claude/ structure
    detect-projects.js                     # Project discovery and CLAUDE.md scaffolding
```

---

## Terminal Targets

Both `open-sessions.js` and `resume-session.sh` support multiple terminal backends. Auto-detection picks the best available.

| Target | Flag | Method | Limitations |
|--------|------|--------|-------------|
| **cmux** | `--cmux` | `cmux new-surface` + `cmux send` | Requires cmux running; known UI bugs ([#616](https://github.com/manaflow-ai/cmux/issues/616), [#2132](https://github.com/manaflow-ai/cmux/issues/2132)) |
| **Ghostty** | `--ghostty` | AppleScript clipboard-paste | Requires Accessibility permissions; timing-dependent; no native CLI on macOS |
| **VS Code** | `--vscode` | Opens project in editor + resumes in terminal | Editor-open only; terminal via cmux/Ghostty |
| **Cursor** | `--cursor` | Opens project in editor + resumes in terminal | Editor-open only; terminal via cmux/Ghostty |

Auto-detect order: cmux (if `cmux ping` succeeds) > Ghostty > print resume command.

---

## What's New (2026-06-05)

### Named Sessions (`cc` wrapper)

Shell function that wraps `claude` with automatic Ghostty tab naming and tracker tagging:

```bash
source ~/.claude/skills/claude-tracker-suite/scripts/claude-wrapper.sh

cc                            # tab titled to cwd basename
cc --name "kothar-refactor"   # explicit tab title
cc --resume abc123 --name "fix"  # resume with name
```

Sets the Ghostty tab title via OSC 1 escape sequence, tags the session in `tracker.db` on exit. All `new-session.sh`, `resume-session.sh`, and `ghostty-resume.sh` also accept `--name`.

### Workspace Save/Restore

Snapshot running sessions and restore them after a Ghostty restart:

```bash
node save-workspace.js                        # snapshot to workspace-state.json
node save-workspace.js --dry-run              # preview
restore-workspace.sh                          # restore all in Ghostty tabs
restore-workspace.sh --dry-run                # preview
restore-workspace.sh --limit 3               # cap at 3 sessions
```

Periodic snapshots via launchd plist (`com.claude.workspace-snapshot.plist`, every 300s).

### Session Notifications

macOS notifications when sessions need attention, with Ghostty tab title badges:

```bash
session-notify.sh --needs-input --project "my-app"   # ⚡ badge + notification
session-notify.sh --session-done --project "my-app"   # ✓ badge + notification
session-notify.sh --tab-badge "🔥" --tab-title "hot"  # badge only
```

A Stop hook (`session-notify-hook.sh`) auto-fires "needs input" on every Claude stop.

### Yazi File Explorer

Open a yazi file manager in a Ghostty split pane:

```bash
open-file-explorer.sh                  # left split (sidebar-style)
open-file-explorer.sh ~/project        # at specific directory
open-file-explorer.sh --right          # right split
```

Requires `brew install yazi`. Uses System Events clipboard-paste pattern (Cmd+D for split).

---

## Earlier Updates (2026-03-26)

### open-sessions.js --- Interactive session launcher

```bash
node open-sessions.js                        # List top 10, prompt to open
node open-sessions.js --limit 5 --split right  # Vertical splits, top 5
node open-sessions.js --ghostty              # Force Ghostty instead of cmux
```

### resume-session.sh --- Single session resume

```bash
resume-session.sh <session-id>               # Auto-detect best terminal
resume-session.sh <session-id> --ghostty     # Force Ghostty
resume-session.sh <session-id> --vscode      # Open project in VS Code + resume
```

### search-sessions.js --id --- ID prefix lookup

```bash
node search-sessions.js --id d7b8f4dd       # Find session by ID prefix
```

---

## Search

`search-sessions.js` searches across all sessions with weighted ranking:

| Field | Weight | Why |
|-------|--------|-----|
| Summary | 3x | Most descriptive of what happened |
| First prompt | 2x | Captures user intent |
| Project path | 1x | Directory context |
| Branch name | 1x | Feature context |

| Flag | Description |
|------|-------------|
| `--limit <n>` | Max results (default: 20) |
| `--id <prefix>` | Lookup by session ID prefix |
| `--name` | Search names/slugs only (fast, no body scan) |
| `--project <name>` | Filter by project |
| `--since <duration>` | Recent only: `7d`, `24h`, `30m` |
| `--json` | Machine-readable output |

---

## Session Status

| Badge | Meaning |
|-------|---------|
| ACTIVE | Process running, recent heartbeat |
| STALE | Process exists but no recent activity |
| OLD | Older than 24 hours |
| CRASHED | Process not found, no clean exit |

---

## Scripts

| Script | Usage |
|--------|-------|
| `open-sessions.js` | `node open-sessions.js [--limit N] [--cmux\|--ghostty] [--split <dir>]` |
| `resume-session.sh` | `bash resume-session.sh <session-id> [--cmux\|--ghostty\|--vscode\|--cursor] [--name <title>]` |
| `search-sessions.js` | `node search-sessions.js "query" [--id <prefix>] [--name]` |
| `list-sessions.js` | `node list-sessions.js [--limit 20]` |
| `new-session.sh` | `bash new-session.sh [dir] [--prompt "text"] [--headless] [--name <title>]` |
| `claude-wrapper.sh` | `source claude-wrapper.sh` then `cc [--name <title>] [--resume <id>]` |
| `save-workspace.js` | `node save-workspace.js [--dry-run\|--json]` |
| `restore-workspace.sh` | `bash restore-workspace.sh [--dry-run] [--limit N]` |
| `session-notify.sh` | `bash session-notify.sh [--needs-input\|--session-done] [--project <name>]` |
| `open-file-explorer.sh` | `bash open-file-explorer.sh [<dir>] [--left\|--right]` |
| `detect-projects.js` | `node detect-projects.js [--suggest\|--scaffold]` |
| `bootstrap-claude-setup.js` | `node bootstrap-claude-setup.js --user "Name"` |

---

## Requirements

- Node.js 18+
- Claude Code CLI installed
- macOS (for Ghostty/System Events automation)
- cmux (optional for deterministic terminal control)
- yazi (optional, for file explorer: `brew install yazi`)
- No external npm dependencies (uses built-in `fs`, `path`, `child_process`)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/planning-productivity/claude-tracker-suite ~/.claude/skills/
```
