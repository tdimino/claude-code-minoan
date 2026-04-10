# Claude Tracker Suite

Session management for Claude Code. Search, resume, spawn, and open sessions across projects---with cmux/Ghostty terminal integration, crash recovery, git-aware tracking, weighted search ranking, and new machine bootstrapping.

**Last updated:** 2026-04-10

**Terminal targets:** cmux (preferred, deterministic CLI), Ghostty (AppleScript fallback), VS Code, Cursor

---

## Why This Skill Exists

Claude Code sessions accumulate fast. After a week of active development, you might have 50+ sessions across 10 projects, some crashed mid-task, some with critical context that wasn't committed. Finding the right session to resume---by topic, by project, by what you were working on---requires searching across summaries, first prompts, branches, and project paths.

This skill provides 8 scripts that handle session lifecycle: interactive session opening in cmux/Ghostty tabs, search with weighted ranking and ID prefix lookup, crash recovery with alive detection, headless spawning for automation, project discovery, and a bootstrap generator for new machines.

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
    resume-session.sh                      # Open single session in cmux/Ghostty (replaces resume-in-vscode.sh)
    search-sessions.js                     # Keyword search + --id prefix lookup
    list-sessions.js                       # List recent sessions with status badges
    bootstrap-claude-setup.js              # Generate complete ~/.claude/ structure
    detect-projects.js                     # Project discovery and CLAUDE.md scaffolding
    new-session.sh                         # Start new interactive/prompt-driven/headless session
    resume-in-vscode.sh                    # Legacy: AppleScript-based terminal launch
    tag-session.js                         # Manual session metatags (add/remove/list/clear)
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

## What's New (2026-04-10)

### Manual session metatags --- `/tag` and `tag-session.js`

Sessions now support user-authored keyword tags that supplement the auto-generated Qwen tags. Three layers are merged and searchable:

1. **`display_tags`** (3) --- Qwen's top picks, shown in statusline
2. **`tags`** (up to 10) --- Qwen's full pool
3. **`user_tags`** (unlimited) --- yours, via `/tag` or `tag-session.js`

```bash
# Tag the current live session (breadcrumb, applies on next Stop event)
/tag codex-skill-detection

# Tag a closed session directly (writes to registry)
node tag-session.js add codex-skill-detection --session 664a8e7c

# Remove a tag
/tag -off-topic-tag

# List all tags on a session
node tag-session.js list
node tag-session.js list --session 664a8e7c
```

### Default-mode metadata pre-pass in search

`search-sessions.js` default mode (no `--name` flag) now runs a registry metadata pre-pass before body-scanning JSONLs. Sessions matching on tags, title, or summary surface even when the literal search term never appeared in the transcript. Metadata-only hits display with labeled indicators:

```
[1] Programming (1d ago)
    Dir: /Users/you/Desktop/Programming
    › Tags: SubQ Code Update, ..., codex-skill-detection
```

### Tag merge in `--name` mode

`--name` mode now merges all three tag arrays (`display_tags` + `tags` + `user_tags`) with case-insensitive deduplication, instead of the previous fallback behavior that only checked `display_tags`.

---

## What's New (2026-03-26)

### open-sessions.js --- Interactive session launcher

Lists top N sessions and opens selected ones in cmux tabs, Ghostty tabs, or splits:

```bash
node open-sessions.js                        # List top 10, prompt to open
node open-sessions.js --limit 5 --split right  # Vertical splits, top 5
node open-sessions.js --ghostty              # Force Ghostty instead of cmux
node open-sessions.js --yes                  # Skip confirmation, open all
node open-sessions.js --json                 # Machine-readable output
```

### resume-session.sh --- Single session resume

Replaces `resume-in-vscode.sh`. cmux-first with Ghostty fallback:

```bash
resume-session.sh <session-id>               # Auto-detect best terminal
resume-session.sh <session-id> --ghostty     # Force Ghostty
resume-session.sh <session-id> --vscode      # Open project in VS Code + resume
```

### search-sessions.js --id --- ID prefix lookup

```bash
node search-sessions.js --id d7b8f4dd       # Find session by ID prefix
```

Returns the correct project directory from JSONL ground truth, not stale `active-projects.md`.

### cmux-commands.md --- Reference

Complete cmux CLI reference: hierarchy, splits, tabs, input, browser, sidebar, notifications, keyboard shortcuts. See `references/cmux-commands.md`.

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
| `resume-session.sh` | `bash resume-session.sh <session-id> [--cmux\|--ghostty\|--vscode\|--cursor]` |
| `search-sessions.js` | `node search-sessions.js "query" [--id <prefix>] [--name]` |
| `list-sessions.js` | `node list-sessions.js [--limit 20]` |
| `new-session.sh` | `bash new-session.sh [dir] [-p "prompt"] [--headless]` |
| `detect-projects.js` | `node detect-projects.js [--suggest\|--scaffold]` |
| `tag-session.js` | `node tag-session.js add\|remove\|list\|clear <tags> [--session ID]` |
| `bootstrap-claude-setup.js` | `node bootstrap-claude-setup.js --user "Name"` |

---

## Requirements

- Node.js 18+
- Claude Code CLI installed
- macOS (for Ghostty AppleScript fallback)
- cmux (optional but preferred for deterministic terminal control)
- No external npm dependencies (uses built-in `fs`, `path`, `child_process`)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/planning-productivity/claude-tracker-suite ~/.claude/skills/
```
