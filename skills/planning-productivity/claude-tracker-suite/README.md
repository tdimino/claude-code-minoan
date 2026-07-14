# Claude Tracker Suite

Session management for Claude Code. Search, resume, spawn, and open sessions across projects---with full-text transcript search, title/nickname history, cmux/Ghostty terminal integration, named sessions, workspace save/restore, macOS notifications, crash recovery, git-aware tracking, and new machine bootstrapping.

**Last updated:** 2026-07-13

**Terminal targets:** cmux (preferred, deterministic CLI), Ghostty (OSC escape sequences + AppleScript), VS Code, Cursor

---

## Why This Skill Exists

Claude Code sessions accumulate fast. After a week of active development, you might have 50+ sessions across 10 projects, some crashed mid-task, some with critical context that wasn't committed. Finding the right session to resume---by topic, by project, by a phrase you remember typing three weeks ago---requires searching the conversations themselves, not just their metadata.

This skill provides 20+ scripts that handle session lifecycle: FTS5 full-text search over every user and assistant message, title/nickname history with rename timelines, an fzf picker, interactive session opening in cmux/Ghostty tabs, named sessions with automatic tab titles, workspace save/restore across Ghostty restarts, macOS notifications for session events, yazi file explorer integration, crash recovery with alive detection, headless spawning for automation, project discovery, a self-audit, a recall regression suite, and a bootstrap generator for new machines.

---

## Structure

```
claude-tracker-suite/
  SKILL.md                                 # CLI reference and workflows
  README.md                                # This file
  references/
    cmux-commands.md                       # Complete cmux CLI reference
    daemon-setup.md                        # Watcher daemon lifecycle and launchd plist
    data-schemas.md                        # tracker.db schema, title_history, JSONL formats
    search-mechanics.md                    # Indexing, ranking, synonym expansion, fallbacks
    synonyms.json                          # Token groups for query expansion
  scripts/
    search-sessions.js                     # FTS search, --id lookup, titles timeline
    index-transcripts.js                   # Incremental transcript FTS indexer
    backfill-summaries.js                  # LLM summary backfill (disabled by default)
    claude-tracker-pick                    # fzf picker with preview
    db-maintain.js                         # Weekly FTS optimize + WAL checkpoint
    audit-suite.js                         # Self-audit → AUDIT.md
    search-regression.js                   # Recall regression fixtures
    open-sessions.js                       # List top N sessions, open in cmux/Ghostty tabs
    resume-session.sh                      # Open single session in cmux/Ghostty
    list-sessions.js                       # List recent sessions with status badges
    recent-sessions.js                     # Last N sessions with full metadata
    new-session.sh                         # Start new interactive/prompt-driven/headless session
    claude-wrapper.sh                      # Shell function `cc` for named sessions with tab titles
    save-workspace.js                      # Snapshot alive sessions to workspace-state.json
    restore-workspace.sh                   # Restore sessions from workspace-state.json
    session-notify.sh                      # macOS notifications + Ghostty tab badges
    open-file-explorer.sh                  # Open yazi in Ghostty split pane
    checkpoint-session.js                  # Named bookmarks within sessions
    quote-session.js                       # Tagged phrase capture + FTS search
    tag-session.js                         # Manual session tagging
    com.claude.workspace-snapshot.plist    # launchd plist for periodic workspace snapshots
    com.claude.db-maintain.plist           # launchd plist for weekly DB maintenance
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

## What's New (2026-07-13)

### Transcript Full-Text Search

Every user and assistant message across every session, indexed in FTS5 and searchable in milliseconds. The query that motivated it---"the session where we worked on my twitter background with imagemagick"---went from unfindable to rank 3 in 75ms.

```bash
node index-transcripts.js                    # incremental (skips unchanged files)
node index-transcripts.js --rebuild          # full rebuild
claude-tracker-search "subquadratic porthole imagemagick"
claude-tracker-search "twitter banner" --open   # resume top hit in Ghostty
claude-tracker-search "rare term" --deep        # raw JSONL scan, bypasses index
```

Multi-word queries match per-term at the session level (terms may land in different messages), expand through synonym groups (`references/synonyms.json`), and fall back from AND to OR with a labeled notice. Ranking: IDF-weighted saturated match-density with a short-session damp. Results carry highlighted snippets.

The index lives in a sidecar `tracker-transcripts.db`, ATTACHed on demand---hooks that write one row per session event open an 11MB `tracker.db`, not a 300MB one.

### Title / Nickname History

Every name a session has borne---slug at birth, `/rename` events, slug changes, model-generated titles---recorded in `title_history` with source provenance and inferred timestamps.

```bash
node search-sessions.js titles dfb5613a
#   2026-05-01 20:59  slug   let-s-scope-out-a-peppy-nest
#   2026-05-01 21:18  user   btw: Can you succinctly explain what we added…
#   2026-05-13 17:04  user   utility plugin
```

Default search checks former titles too: a session renamed away from a name you remember still surfaces, labeled with its old name and provenance. Rename events route by the line's own `sessionId`---a `/rename` issued after `/resume` lands in the active file but targets another session, and Claude Code's own scanner titles the wrong one. This suite doesn't. Live renames also drop an auto-checkpoint.

### fzf Session Picker

```bash
claude-tracker-pick                # fuzzy-find last 50, preview, Enter → Ghostty
claude-tracker-pick --here         # current project only
```

Enter resumes in a Ghostty tab, Ctrl-O resumes in the current terminal, Ctrl-Y copies the resume command.

### Summary Backfill (disabled by default)

LLM-generated summaries for sessions Claude Code never summarized natively (native generation stopped around v2.1.31, February 2026). Requires explicit opt-in, runs hermetically---no hooks fire, no synthetic sessions persist---and supports two providers:

```bash
node backfill-summaries.js --dry-run                       # preview, no LLM calls
node backfill-summaries.js --enable                        # claude CLI, haiku
node backfill-summaries.js --enable --provider openrouter  # OpenRouter, kimi-k2
```

### Weekly DB Maintenance

`db-maintain.js` merges FTS segments and truncates WALs on both databases, skipping when an indexer is mid-run. Scheduled Sundays 04:30 via `com.claude.db-maintain.plist`.

### Self-Audit and Regression Suite

```bash
node audit-suite.js          # inventory, portability, daemons, DB coverage → AUDIT.md
node search-regression.js    # recall fixtures; exit 1 on regression
```

The regression suite includes an expected-fail fixture documenting the semantic-recall gap (a session findable only by words actually typed in it)---if it ever passes, a semantic layer landed.

---

## Earlier Updates (2026-06-05)

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
restore-workspace.sh                          # restore all in Ghostty tabs
restore-workspace.sh --limit 3                # cap at 3 sessions
```

Periodic snapshots via launchd plist (`com.claude.workspace-snapshot.plist`, every 300s). Snapshots dedupe by session ID and never overwrite a good snapshot with an empty one.

### Session Notifications

macOS notifications when sessions need attention, with Ghostty tab title badges:

```bash
session-notify.sh --needs-input --project "my-app"    # ⚡ badge + notification
session-notify.sh --session-done --project "my-app"   # ✓ badge + notification
```

The Stop-hook auto-fire is opt-in---wired into settings.json only when you want per-stop notifications.

### Yazi File Explorer

```bash
open-file-explorer.sh                  # left split (sidebar-style)
open-file-explorer.sh --right          # right split
```

Requires `brew install yazi`. Uses System Events clipboard-paste pattern (Cmd+D for split).

---

## Search

Default path: transcript FTS + metadata FTS, merged, with former-title fallback. Metadata bm25 column weights:

| Field | Weight | Why |
|-------|--------|-----|
| Custom title | 3x | You named it that for a reason |
| Auto title / Summary | 2x | Most descriptive of what happened |
| First prompt | 1.5x | Captures intent |
| Slug | 1x | Auto-nickname |

| Flag | Description |
|------|-------------|
| `--limit <n>` | Max results (default: 15) |
| `--id <prefix>` | Lookup by session ID prefix |
| `titles <prefix>` | Title/nickname history timeline |
| `--name` | Metadata FTS only (fastest) |
| `--deep` | Raw JSONL scan, bypasses index |
| `--open` | Resume top hit in a new Ghostty tab |
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
| `search-sessions.js` | `node search-sessions.js "query" [--id <prefix>] [titles <prefix>] [--open] [--deep]` |
| `index-transcripts.js` | `node index-transcripts.js [--rebuild] [--limit N] [--quiet]` |
| `backfill-summaries.js` | `node backfill-summaries.js --enable [--provider claude\|openrouter] [--dry-run]` |
| `claude-tracker-pick` | `claude-tracker-pick [--here] [--project <name>] [--limit N]` |
| `db-maintain.js` | `node db-maintain.js [--quiet]` |
| `audit-suite.js` | `node audit-suite.js` |
| `search-regression.js` | `node search-regression.js [--json]` |
| `open-sessions.js` | `node open-sessions.js [--limit N] [--cmux\|--ghostty] [--split <dir>]` |
| `resume-session.sh` | `bash resume-session.sh <session-id> [--cmux\|--ghostty\|--vscode\|--cursor] [--name <title>]` |
| `list-sessions.js` | `node list-sessions.js [--limit 20]` |
| `recent-sessions.js` | `node recent-sessions.js [--limit N] [--project <name>] [--json]` |
| `new-session.sh` | `bash new-session.sh [dir] [--prompt "text"] [--headless] [--name <title>]` |
| `claude-wrapper.sh` | `source claude-wrapper.sh` then `cc [--name <title>] [--resume <id>]` |
| `save-workspace.js` | `node save-workspace.js [--dry-run\|--json]` |
| `restore-workspace.sh` | `bash restore-workspace.sh [--dry-run] [--limit N]` |
| `session-notify.sh` | `bash session-notify.sh [--needs-input\|--session-done] [--project <name>]` |
| `open-file-explorer.sh` | `bash open-file-explorer.sh [<dir>] [--left\|--right]` |
| `checkpoint-session.js` | `node checkpoint-session.js create "label" \| list` |
| `quote-session.js` | `node quote-session.js capture "phrase" --tags a,b \| search "term"` |
| `detect-projects.js` | `node detect-projects.js [--suggest\|--scaffold]` |
| `bootstrap-claude-setup.js` | `node bootstrap-claude-setup.js --user "Name"` |

---

## Requirements

- Node.js 18+
- Claude Code CLI installed
- `better-sqlite3` (for `tracker.db` / transcript index; the only npm dependency)
- macOS (for Ghostty/System Events automation)
- fzf (optional, for `claude-tracker-pick`)
- cmux (optional for deterministic terminal control)
- yazi (optional, for file explorer: `brew install yazi`)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/planning-productivity/claude-tracker-suite ~/.claude/skills/
```
