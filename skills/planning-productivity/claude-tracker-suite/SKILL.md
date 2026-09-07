---
name: claude-tracker-suite
description: "Manage Claude Code sessions — search by topic or ID, browse recent sessions with full metadata (tags, summaries, titles, cost), view title/nickname history timelines, resume in Ghostty tabs, spawn interactive or headless sessions, monitor live sessions, and bootstrap new setups. Triggers on resume session, find session, list sessions, recent sessions, spawn session, session history, what was I working on, open in ghostty, title history, session nicknames."
argument-hint: [query or --id <prefix>]
allowed-tools: Bash(claude-tracker*), Bash(node ~/.claude/skills/claude-tracker-suite/scripts/*), Bash(~/.claude/skills/claude-tracker-suite/scripts/*.sh), Bash(python3 ~/.claude/scripts/*), Read, Grep, Glob, Edit, Write, Skill
---

# Claude Session Management Suite

Search, browse, monitor, and manage Claude Code session history across all projects.

## Tools Overview

| Tool | Purpose |
|------|---------|
| `claude-tracker-search` | Search sessions by keyword or ID prefix |
| `claude-tracker-pick` | Interactive fzf picker: fuzzy-find recent sessions, preview, Enter resumes in Ghostty |
| `index-transcripts.js` | Build/refresh the transcript full-text index (FTS5 over user+assistant text) and extract title history events |
| `backfill-summaries.js` | Generate missing session summaries (claude CLI or OpenRouter; disabled by default, `--enable` to run) |
| `audit-suite.js` | Self-audit: inventory, portability, daemons, DB coverage, search recall → AUDIT.md |
| `search-regression.js` | Recall regression fixtures for the search stack (exit 1 on regression) |
| `open-sessions.js` | List top N sessions, open selected in Ghostty tabs |
| `claude-tracker-resume` | Find and resume crashed/inactive sessions |
| `claude-tracker-alive` | Check which sessions have running processes |
| `claude-tracker-watch` | Daemon: auto-summarize new sessions, update active-projects.md |
| `claude-tracker` | List recent sessions with status badges |
| `new-session.sh` | Start a new session in Ghostty or headless, with optional prompt |
| `resume-session.sh` | Open a session in a Ghostty tab (optionally open project in Cursor) |
| `detect-projects.js` | Scan sessions to find all projects, check CLAUDE.md coverage |
| `bootstrap-claude-setup.js` | Generate complete ~/.claude/ config for new machine |
| `update-active-projects.py` | Regenerate active-projects.md with enriched session data |
| `checkpoint-session.js` | Create/query named bookmarks within sessions |
| `quote-session.js` | Capture/search notable phrases with FTS5 |
| `tag-session.js` | Manual session tagging with provenance |
| `claude-tracker-recent` | Show last N sessions with full metadata (title, tags, summary, cost, model) |
| `claude-wrapper.sh` | Shell function `cc` for named Claude sessions with auto tab titles |
| `save-workspace.js` | Snapshot alive sessions to `~/.claude/workspace-state.json` |
| `restore-workspace.sh` | Restore saved sessions into Ghostty tabs |
| `open-file-explorer.sh` | Open yazi file explorer in a Ghostty split pane |

## Standalone Scripts

Commands delegate to standalone Node.js scripts (avoids shell escaping issues with inline `node -e`):

| Script | Called By | Purpose |
|--------|-----------|---------|
| `scripts/search-sessions.js` | `/claude-tracker-search` | Keyword search or `--id` prefix lookup across all sessions |
| `scripts/open-sessions.js` | Direct invocation | List top N sessions, open selected in Ghostty tabs |
| `scripts/list-sessions.js` | `/claude-tracker` | List recent sessions with status badges |
| `scripts/new-session.sh` | `/spawn` | Start new interactive or prompt-driven session in Ghostty or headless |
| `scripts/resume-session.sh` | Direct invocation | Open session in Ghostty tab, optionally open project in Cursor |
| `scripts/detect-projects.js` | Direct invocation | Project discovery and CLAUDE.md scaffolding |
| `scripts/bootstrap-claude-setup.js` | Direct invocation | New machine setup generator |
| `scripts/checkpoint-session.js` | `/checkpoint`, `/checkpoint-list` | Create and query session checkpoints |
| `scripts/quote-session.js` | `/quote`, `/quote-search` | Capture and search tagged phrases via FTS5 |
| `scripts/tag-session.js` | `/tag` | Manual session tagging with provenance |
| `scripts/recent-sessions.js` | `/claude-tracker-recent` | Last N sessions with title, tags, summary, model, cost |
| `scripts/claude-wrapper.sh` | Source in `.zshrc` | Shell function `cc` for named sessions with tab titles |
| `scripts/save-workspace.js` | Direct / launchd | Snapshot alive sessions to workspace-state.json (deduped; never overwrites a good snapshot with an empty one) |
| `scripts/restore-workspace.sh` | Direct invocation | Restore sessions from workspace-state.json into Ghostty tabs |
| `scripts/claude-tracker-pick` | Direct invocation | fzf session picker with preview; Enter→Ghostty, Ctrl-O→current terminal, Ctrl-Y→copy |
| `scripts/index-transcripts.js` | Hooks / launchd / in-process | Incremental transcript FTS indexer (EXTRACTOR_VERSION 4; prunes deleted; extracts title history events) |
| `scripts/backfill-summaries.js` | Direct invocation | Hermetic summary backfill, claude or OpenRouter provider (disabled by default) |
| `scripts/audit-suite.js` | Direct invocation | Suite self-audit → AUDIT.md |
| `scripts/search-regression.js` | After search changes | Recall fixtures incl. expected-fail semantic-gap marker |
| `scripts/open-file-explorer.sh` | Direct invocation | Open yazi in a Ghostty split pane |
| `~/.claude/scripts/ghostty-resume.sh` | Direct invocation | The single terminal opener for the suite—opens sessions in Ghostty tabs or splits |

All scripts use `~/.claude/lib/tracker-utils.js` for shared utilities (path decoding, session parsing, live-session detection, git remote detection) and `~/.claude/lib/tracker-db.js` for SQLite access (node:sqlite `DatabaseSync`, WAL mode, singleton lazy-open). No npm dependencies—the DB module uses Node's built-in `node:sqlite` (Node >= 22.13).

## Quick Start

```bash
# Search by topic
claude-tracker-search "kothar mac mini"

# Lookup by session ID prefix (exact directory from JSONL ground truth)
node ~/.claude/skills/claude-tracker-suite/scripts/search-sessions.js --id d7b8f4dd

# Search by session name/slug only (fast — no body scan)
claude-tracker-search "thera" --name

# List top 10 sessions, open selected in Ghostty tabs
node ~/.claude/skills/claude-tracker-suite/scripts/open-sessions.js

# Check what's alive
claude-tracker-alive

# Resume crashed sessions in Ghostty
claude-tracker-resume --open

# Start auto-summarize daemon
claude-tracker-watch --daemon
```

## Search

```bash
claude-tracker-search "$ARGUMENTS"
```

**How search works**: the default path queries the **transcript full-text index** (FTS5 over all user+assistant conversation text, built by `index-transcripts.js`), merged with metadata FTS over titles/slug/summary/first-prompt (bm25 column weights: custom_title 3x, auto_title 2x, summary 2x, first_prompt 1.5x, slug 1x). Multi-word queries match per-term at the *session* level (terms may appear in different messages), expand through synonym groups in `references/synonyms.json`, and fall back from AND to OR with a labeled partial-match notice. Ranking: IDF-weighted saturated match-density with a short-session damp. Results include highlighted snippet excerpts.

Before every body search, `search-sessions.js` runs an in-process index refresh (1.5s budget) so sessions from today are searchable within seconds of their last turn. The refresh line reads `Index refreshed: N session(s) in Xms — M still pending`. Pass `--no-refresh` to skip it.

**Former-title fallback**: default search also checks `title_history` for sessions whose past titles match the query but whose current title does not. A session renamed away from a name the user remembers still surfaces under a "former-title matches" heading, capped to avoid crowding body results. Each former-title hit prints its old name, provenance, date, and a link to the full timeline via the `titles` subcommand.

| Flag / Subcommand | Description |
|------|-------------|
| `--limit <n>` | Max results (default: 15) |
| `--id <prefix>` | Lookup by session ID prefix (8+ chars) |
| `--name` | Titles/slugs/summaries only via metadata FTS (fastest) |
| `--deep` | Bypass the index: streaming raw JSONL scan (new/unindexed sessions; whole-phrase matching) |
| `--open` | Resume the top hit in a new Ghostty tab immediately |
| `--copy` | Copy the top hit's resume command to the clipboard (opt-in; nothing writes clipboard by default) |
| `--no-refresh` | Skip the on-demand index catch-up before searching |
| `titles <id-prefix>` | Print the chronological title/nickname timeline for a session (all rename, slug, cache, and summarizer events) |

## Transcript Index & Summary Backfill

```bash
# Incremental index refresh (skips unchanged files; runs automatically via hooks and launchd)
node ~/.claude/skills/claude-tracker-suite/scripts/index-transcripts.js

# Full rebuild (also forced automatically when EXTRACTOR_VERSION bumps)
node ~/.claude/skills/claude-tracker-suite/scripts/index-transcripts.js --rebuild

# Single session (what the hooks call)
node ~/.claude/skills/claude-tracker-suite/scripts/index-transcripts.js --session <id>
node ~/.claude/skills/claude-tracker-suite/scripts/index-transcripts.js --stdin --quiet --debounce 120

# Budget-limited refresh (what search-sessions.js calls in-process)
node ~/.claude/skills/claude-tracker-suite/scripts/index-transcripts.js --budget 1500

# Backfill missing summaries — DISABLED BY DEFAULT, requires --enable
# (or TRACKER_SUMMARIZER=1). Hermetic when run: --safe-mode
# --no-session-persistence, no hooks fire, no synthetic sessions persist.
node ~/.claude/skills/claude-tracker-suite/scripts/backfill-summaries.js --enable
node ~/.claude/skills/claude-tracker-suite/scripts/backfill-summaries.js --enable --session <id-prefix>  # force one

# OpenRouter backend instead of claude CLI (default model moonshotai/kimi-k2;
# key from OPENROUTER_API_KEY or ~/.config/env/secrets.env)
node ~/.claude/skills/claude-tracker-suite/scripts/backfill-summaries.js --enable --provider openrouter

# Preview excerpts without any LLM calls (no gate needed)
node ~/.claude/skills/claude-tracker-suite/scripts/backfill-summaries.js --dry-run

# NOTE: the watcher-daemon auto-name path (update-active-projects.py) is also
# gated off by default; set TRACKER_AUTO_NAME=1 to re-enable it.

# Recall regression suite — run after touching search code or synonyms
node ~/.claude/skills/claude-tracker-suite/scripts/search-regression.js

# Suite self-audit → AUDIT.md (P0-P3 findings)
node ~/.claude/skills/claude-tracker-suite/scripts/audit-suite.js
```

The indexer runs automatically through three channels: Stop and SessionEnd hooks (`--stdin --quiet --debounce 120` async on Stop, `--stdin --quiet --debounce 10` sync on SessionEnd), the hourly `com.claude.transcript-index` launchd agent (plist in `scripts/`, installed in `~/Library/LaunchAgents/`, logs in `~/.claude/logs/transcript-index.{log,err}`), and in-process from `search-sessions.js` before every body search (1.5s budget). Sessions are searchable within seconds of their last turn.

Incremental indexing skips files whose size, mtime, and extractor version (currently EXTRACTOR_VERSION 4) all match `transcript_index_state`. Bumping the version constant forces a full reindex under new extraction rules. Read errors are never recorded as indexed—the session stays eligible for the next run, preventing a partial read from permanently masking content from search. Deleted transcripts are pruned on full (unlimited) runs.

Since v4, the indexer also extracts **title history events** from each transcript: `/rename` custom-title lines (source `user`), slug changes (source `slug`). Custom-title lines route by the line's own `sessionId` field, not the containing file—a `/rename` after `/resume` writes into the active transcript but targets the previous session. Claude Code's own metadata scanner gets this wrong, overwriting the active session's title with the rename target's title. Consecutive duplicate title values within a file collapse to a single event.

Known lexical limit: a session can only be found by words that actually occur in it—the `[expected fail]` regression fixture documents this; a semantic (rlama) layer is the designated future fix.

## Interactive Picker (restart recovery)

```bash
~/.claude/skills/claude-tracker-suite/scripts/claude-tracker-pick              # fuzzy-find recent 50
~/.claude/skills/claude-tracker-suite/scripts/claude-tracker-pick --here      # resume in current terminal
~/.claude/skills/claude-tracker-suite/scripts/claude-tracker-pick --project thera --limit 100
```

Enter opens the session in a Ghostty tab, Ctrl-O resumes in the current terminal, Ctrl-Y copies the resume command. Preview shows title, summary, and first prompt. Pair with `restore-workspace.sh` (bulk restore from the launchd snapshot)—the picker is for choosing, restore is for "give me back everything".

## Resume Crashed Sessions

```bash
claude-tracker-resume                    # List crashed sessions with resume commands
claude-tracker-resume --open             # Reopen each in a new Ghostty tab
claude-tracker-resume --open --limit 3   # Reopen at most 3
claude-tracker-resume --dry-run          # Preview without acting
claude-tracker-resume --days 14          # Widen the look-back window (default 7)
```

A crashed session is the newest transcript per project (within the look-back window) that has no live Claude process, for projects with no live tab at all. Liveness comes from `~/.claude/sessions/<pid>.json` PID files via `tracker-utils.getLiveSessions()`. Sessions older than 3 days show an OLD badge.

## Workspace Stamp & Restore (claude + codex)

Survive a logout/reboot with every agent session intact:

```bash
node ~/.claude/skills/claude-tracker-suite/scripts/save-workspace.js   # Stamp now (also runs every 5 min via launchd)
claude-tracker-resume --workspace --dry-run                            # Preview the restore
claude-tracker-resume --workspace                                      # Reopen every session in Ghostty tabs, in order
```

The stamp (`~/.claude/workspace-state.json`) captures all live **Claude Code** sessions (from the authoritative `~/.claude/sessions/<pid>.json` PID files) and **Codex CLI** sessions (native binary PIDs joined to their open rollout files via `lsof`; the earliest-opened rollout is the main thread, its filename carries the UUID). Entries are TTY-ordered so tabs restore in their original order. Empty-protection means a post-logout stamp never clobbers the last good one. Restore warns when the stamp is >15 min old and reports per-agent counts.

## Alive Detection

Check which sessions have running Claude processes:

```bash
claude-tracker-alive                     # Running + stale sessions overview
claude-tracker-alive --running           # Only sessions with active processes
claude-tracker-alive --stale             # Only sessions with no process
claude-tracker-alive --all-kinds         # Include headless/background sessions
claude-tracker-alive --json              # Machine-readable output
```

Source of truth is Claude Code's PID files (`~/.claude/sessions/<pid>.json`), verified against one `ps` pass via `getLiveSessions()`. Matching is by sessionId—a crashed session next to a live sibling in the same directory is no longer reported RUNNING. Sessions >3 days without a process show an OLD badge.

## Auto-Summarize Daemon

Watch for new sessions and auto-populate summary cache:

```bash
claude-tracker-watch --status            # Check if daemon is running
claude-tracker-watch --daemon            # Start in background
claude-tracker-watch --stop              # Stop running daemon
claude-tracker-watch --verbose           # Foreground with debug output
```

Dormant: it watches `sessions-index.json`, which Claude Code no longer writes, so it never fires on current versions. Kept for reference; see `references/daemon-setup.md` for the launchd agents that do run (workspace-snapshot, transcript-index, db-maintain).

## Recent Sessions (Full Metadata)

```bash
claude-tracker-recent                          # Last 10 sessions with full metadata
claude-tracker-recent --limit 20               # Last 20 sessions
claude-tracker-recent --json                   # Machine-readable JSON output
claude-tracker-recent --project myapp          # Filter by project
claude-tracker-recent --model opus             # Filter by model
claude-tracker-recent --since 7d               # Last 7 days only
```

Shows per session: title (custom or auto), summary, all tags (color-coded by type), project name, age, model, cost, turn count, git branch, session ID, and resume command. Add `--copy` to put the first resume command on the clipboard (never done by default).

## Session Listing

```bash
claude-tracker                           # All recent sessions
```

Status badges: ACTIVE (process running, recent heartbeat), STALE (process exists but no recent activity), OLD (older than 24 hours), CRASHED (process not found, no clean exit).

When speculator is running, the session listing includes Ghostty tab count and window count in the header, plus TTY badges per session showing which Ghostty tab it occupies.

## Detect Projects

```bash
node ~/.claude/skills/claude-tracker-suite/scripts/detect-projects.js                # List all
node ~/.claude/skills/claude-tracker-suite/scripts/detect-projects.js --suggest      # Suggest additions
node ~/.claude/skills/claude-tracker-suite/scripts/detect-projects.js --scaffold     # Create CLAUDE.md stubs
node ~/.claude/skills/claude-tracker-suite/scripts/detect-projects.js --since 30d    # Recent only
```

## Update Active Projects

```bash
python3 ~/.claude/scripts/update-active-projects.py              # Regenerate active-projects.md
python3 ~/.claude/scripts/update-active-projects.py --summarize  # Show sessions needing summaries
```

The generated table includes Model, Turns, and Cost columns from enriched session data (extracted from JSONL transcripts). Git worktree sessions show a tree emoji badge. The auto-name path (one-shot `claude --model haiku` call for sessions without summaries) is disabled by default—set `TRACKER_AUTO_NAME=1` to re-enable it. Native Claude Code session summaries stopped generating around v2.1.31 (February 2026), so `sessions-index.json` summary fields are stale for newer sessions; use `backfill-summaries.js` or the transcript index instead.

## Bootstrap New Setup

Generate a complete `~/.claude/` configuration for a new machine:

```bash
node ~/.claude/skills/claude-tracker-suite/scripts/bootstrap-claude-setup.js --user "Name" --dry-run
node ~/.claude/skills/claude-tracker-suite/scripts/bootstrap-claude-setup.js --user "Name"
```

Creates directory structure, global CLAUDE.md, userModel template, agent_docs stubs, and project CLAUDE.md scaffolds. Follow up with `/claude-md-manager` to enrich generated files.

## Resume in Ghostty Tab

The single terminal opener for the suite is `~/.claude/scripts/ghostty-resume.sh`. It writes a tiny launcher script to `~/.claude/run/launch/` and has Ghostty run it in a new tab or split.

```bash
~/.claude/scripts/ghostty-resume.sh <session-id>
~/.claude/scripts/ghostty-resume.sh <session-id> --project ~/my-project --name "auth-fix"
~/.claude/scripts/ghostty-resume.sh <session-id> --split right       # split the current tab
~/.claude/scripts/ghostty-resume.sh <session-id> --print             # write launcher, print its path
~/.claude/scripts/ghostty-resume.sh --exec "claude -n foo" --project ~/my-project  # arbitrary command
```

On Ghostty >= 1.3.0, the opener uses the AppleScript dictionary (`new surface configuration` with `initial working directory` + `initial input`, then `new tab` or `split`)—no keystrokes, no clipboard, no focus dependency. On older builds it falls back to activate + Cmd-T + one Cmd-V paste of the launcher path (clipboard saved/restored). `--split` requires the scripting dictionary (>= 1.3.0); without it, the flag is ignored and a tab opens instead.

The launcher itself checks the project directory and transcript before running `exec claude --resume <id>`, falling back to a fresh session with a reason when either is missing. Launchers are pruned after a day; `~/.claude/run/` is gitignored. Claude Code sets tab titles itself (`-n` / derived name)—nothing is injected.

Exit codes: 0 opened, 1 bad arguments or unresolvable session, 2 Ghostty or Accessibility unavailable.

`resume-session.sh` is a thin wrapper that delegates to the opener, with `--cursor` to also open the project in Cursor.

## New Session / Spawn

Start a new Claude Code session in a terminal tab or headless:

```bash
# Interactive session in Ghostty (default)
~/.claude/skills/claude-tracker-suite/scripts/new-session.sh ~/my-project

# With a specific model
~/.claude/skills/claude-tracker-suite/scripts/new-session.sh ~/my-project --model opus

# Prompt-driven session in Ghostty tab
~/.claude/skills/claude-tracker-suite/scripts/new-session.sh ~/my-project --prompt "fix the login bug"

# Headless — runs in current terminal, returns JSON
~/.claude/skills/claude-tracker-suite/scripts/new-session.sh ~/my-project --headless --prompt "summarize the README"

# Headless with specific model and output format
~/.claude/skills/claude-tracker-suite/scripts/new-session.sh ~/my-project --headless --prompt "fix tests" --model haiku --output-format text
```

Headless and prompt-driven modes use `claude -p` (the Agent SDK CLI). Terminal modes delegate to `ghostty-resume.sh --exec`.

## Workflow: Find and Resume

1. `claude-tracker-search "topic"` — find matching sessions
2. `claude-tracker-recent` — browse last 10 sessions with full metadata
3. `claude --resume <session-id>` — resume in current terminal
4. `~/.claude/scripts/ghostty-resume.sh <session-id>` — resume in a new Ghostty tab
5. `claude-tracker-resume --open` — auto-resume all crashed sessions in Ghostty

## Workflow: Monitor Active Work

1. `claude-tracker-alive` — see what's running vs stale
2. `claude-tracker-watch --daemon` — keep summaries auto-updated
3. Read `~/.claude/agent_docs/active-projects.md` — curated project overview

## Native Claude Code Features

Claude Code 2.1.263+ provides session management primitives that overlap with parts of this suite. Where native is sufficient, use it directly:

- `claude -r|--resume [id|name|search-term]` — built-in picker with search across all projects
- `-n/--name` — name a session at launch (shown in `/resume` picker and tab title)
- `/rename` — rename the current session
- `--fork-session` — fork a session for exploratory work
- `--from-pr` — start a session seeded with a PR's context
- `--bg` + `claude attach` — background sessions with attach/detach
- `-w/--worktree` — worktree isolation

This suite's `cleanupPeriodDays` is 99999 so transcripts never expire.

## SQLite Database (`tracker.db`)

Single SQLite database at `~/.claude/tracker.db` consolidates all session metadata, git tracking, tags, and three capabilities: checkpoints, phase tracking, and tagged phrases.

**API module**: `~/.claude/lib/tracker-db.js` — synchronous node:sqlite `DatabaseSync` (built into Node >= 22.13, no native module to rebuild), WAL mode, singleton lazy-open. The compat shim keeps the `prepare/run/get/all/exec/pragma/transaction` surface the call sites were written against and throws on a missing named parameter. `isAvailable()` is a real open probe (attempts a read-only open); `tryDb()` in `tracker-utils.js` prints `tracker-db unavailable: <reason> — falling back to JSONL scan` to stderr once per process instead of failing silently.

```bash
# Query directly
sqlite3 ~/.claude/tracker.db "SELECT COUNT(*) FROM sessions;"
sqlite3 ~/.claude/tracker.db "SELECT phase, COUNT(*) FROM phases GROUP BY phase;"
sqlite3 ~/.claude/tracker.db "SELECT phrase, GROUP_CONCAT(tag) FROM tagged_phrases tp LEFT JOIN tagged_phrase_tags tpt ON tpt.phrase_id = tp.id GROUP BY tp.id ORDER BY tp.timestamp DESC LIMIT 10;"
```

**Migration** (idempotent): `node ~/.claude/scripts/migrate-to-sqlite.js`

### Title / Nickname History

The `title_history` table records every name a session has ever had, with provenance. Sources: `user` (from `/rename` custom-title lines), `slug` (auto-nickname from Claude Code), `cache` (May 2026 metadata import from `session-summaries.json`), `summarizer` (from `backfill-summaries.js`).

```bash
# Print the title timeline for a session
node ~/.claude/skills/claude-tracker-suite/scripts/search-sessions.js titles <id-prefix>

# Query raw history
sqlite3 ~/.claude/tracker.db "SELECT title, source, observed_at FROM title_history WHERE session_id LIKE 'abc%' ORDER BY observed_at;"
```

Title events are extracted during transcript indexing (`index-transcripts.js` v4+). `/rename` entries route by the line's own `sessionId`—a rename issued after `/resume` targets the previous session, not the file it was written into. This corrects a known upstream behavior where Claude Code's metadata scanner assigns the rename to the wrong session.

Default search automatically surfaces sessions findable only by a former title under a "former-title matches" heading. The `titles` subcommand prints the full chronological timeline: timestamp, source, title value, and cross-session rename provenance.

### Checkpoints

Named bookmarks within sessions capturing label, git state, workflow phase, and modified files.

```bash
# Manual checkpoint
node ~/.claude/skills/claude-tracker-suite/scripts/checkpoint-session.js create "finished auth module"
node ~/.claude/skills/claude-tracker-suite/scripts/checkpoint-session.js create "pre-deploy" --summary "about to push"

# List checkpoints
node ~/.claude/skills/claude-tracker-suite/scripts/checkpoint-session.js list
node ~/.claude/skills/claude-tracker-suite/scripts/checkpoint-session.js list --phase implementing
node ~/.claude/skills/claude-tracker-suite/scripts/checkpoint-session.js list --limit 10
```

Auto-checkpoints are created on git commits (`git-track-post.sh`) and phase transitions (`phase-detect.py`).

### Phase Tracking

Automatic workflow phase detection via PostToolUse hook (`phase-detect.py`). Rolling window of last 10 tool calls, hysteresis to prevent flickering.

Phases: `exploring`, `planning`, `deepening`, `implementing`, `testing`, `reviewing`, `debugging`, `committing`, `deploying`, `discussing`.

```bash
# Query current phase for a session
sqlite3 ~/.claude/tracker.db "SELECT phase, started_at FROM phases WHERE session_id = 'abc...' AND ended_at IS NULL;"

# Phase history
sqlite3 ~/.claude/tracker.db "SELECT phase, started_at, ended_at, duration_ms FROM phases WHERE session_id = 'abc...' ORDER BY started_at;"

# Phase analytics
sqlite3 ~/.claude/tracker.db "SELECT phase, COUNT(*) as transitions, AVG(duration_ms)/1000 as avg_seconds FROM phases GROUP BY phase;"
```

### Tagged Phrases

Notable excerpts captured from sessions with tags, searchable via FTS5.

```bash
# Capture a phrase
node ~/.claude/skills/claude-tracker-suite/scripts/quote-session.js capture "assumptions are the enemy" --tags principle,design

# Search phrases (FTS5)
node ~/.claude/skills/claude-tracker-suite/scripts/quote-session.js search "assumptions"

# List by tag
node ~/.claude/skills/claude-tracker-suite/scripts/quote-session.js tag principle

# List recent phrases
node ~/.claude/skills/claude-tracker-suite/scripts/quote-session.js list --limit 20
```

Phrases are also auto-extracted by the `session-tags-infer.py` Stop hook during LLM inference.

## Named Sessions (`cc` Wrapper)

Shell function that wraps `claude` with automatic Ghostty tab naming and tracker tagging.

```bash
# Source in .zshrc (one-time setup)
source ~/.claude/skills/claude-tracker-suite/scripts/claude-wrapper.sh

# Start a named session
cc --name "kothar-refactor"

# Resume with a name
cc --resume abc12345 --name "auth-fix"

# Default: tab title = basename of cwd
cc
```

The `cc` function sets the Ghostty tab title via OSC 1 escape sequence before launching `claude`, then tags the session with the name in `tracker.db` on exit. Tab title resets to the directory basename when the session ends.

## Tab Auto-Naming

`new-session.sh`, `resume-session.sh`, and `ghostty-resume.sh` all accept `--name` to label the session. Claude Code sets the Ghostty tab title itself (`-n` / derived name)—no OSC injection is needed.

## Workspace Save/Restore

Snapshot running Claude sessions and restore them after a Ghostty restart.

### Save

```bash
# Snapshot current sessions
node ~/.claude/skills/claude-tracker-suite/scripts/save-workspace.js

# Preview without writing
node ~/.claude/skills/claude-tracker-suite/scripts/save-workspace.js --dry-run
```

Detects alive sessions via PID files (`~/.claude/sessions/<pid>.json`) verified against `ps`, matches them to tracker DB entries, and writes `~/.claude/workspace-state.json` with session IDs, project directories, and tab titles. Title precedence: custom_title → auto_title → slug → summary. Deduplicates by sessionId (multiple PIDs from forks and MCP children resolve to one entry). Never overwrites a good snapshot with an empty one—after a crash or logout with zero live sessions, the previous snapshot is preserved.

### Restore

```bash
# Restore all saved sessions into Ghostty tabs
~/.claude/skills/claude-tracker-suite/scripts/restore-workspace.sh

# Preview what would be restored
~/.claude/skills/claude-tracker-suite/scripts/restore-workspace.sh --dry-run

# Restore at most 3 sessions
~/.claude/skills/claude-tracker-suite/scripts/restore-workspace.sh --limit 3

# Slow stagger for a loaded machine
~/.claude/skills/claude-tracker-suite/scripts/restore-workspace.sh --stagger 3
```

Opens each session in a new Ghostty tab via `ghostty-resume.sh`. Default stagger is 1 second between tabs. Skips sessions that are still running, missing project directories, and missing transcripts—each with a reason, never aborting on one failure. Reports per-agent counts.

### Automatic Snapshots (launchd)

A launchd plist at `scripts/com.claude.workspace-snapshot.plist` runs `save-workspace.js` every 300 seconds. Install:

```bash
cp ~/.claude/skills/claude-tracker-suite/scripts/com.claude.workspace-snapshot.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.claude.workspace-snapshot.plist
```

## Yazi File Explorer

Open a yazi file manager in a Ghostty split pane for project browsing.

```bash
# Open yazi in a left split (default, sidebar-style)
~/.claude/skills/claude-tracker-suite/scripts/open-file-explorer.sh

# Open at a specific directory
~/.claude/skills/claude-tracker-suite/scripts/open-file-explorer.sh ~/my-project

# Split to the right instead
~/.claude/skills/claude-tracker-suite/scripts/open-file-explorer.sh --right
```

Uses System Events clipboard-paste pattern (Cmd+D for split, then paste yazi command). Requires yazi: `brew install yazi ffmpegthumbnailer unar jq poppler fd ripgrep fzf zoxide`.

## Performance

| Operation | Before | After |
|-----------|--------|-------|
| Search ("kothar mac mini") | 11.1s (JSONL scan) | 0.06s (FTS5) |
| List sessions | 1.4s | 0.44s |
| Recent sessions | crash | 0.13s |
| `claude-tracker-alive` | — | 0.25s |
| Live detection | 881ms | ~100ms |
| Index backlog (85 files) | — | 1.3s |
| Opener (per tab) | — | ~1–2s |

## Related Systems

- **Git Tracking** — PreToolUse/PostToolUse hooks intercept git commands, tag sessions with repos they touch. Query via `tracker-utils.js` functions (`getSessionsForRepo`, `getReposForSession`, `getRecentCommits`). See `references/data-schemas.md` for hook files and index format.
- **Speculator** — Daemon at `~/.claude/scripts/speculator/` maps Ghostty tabs to sessions every 5 minutes. `list-sessions.js` uses `loadSpeculatorData()` and `getSessionTTY()` for TTY badges. Health check: `bash ~/.claude/scripts/speculator/status.sh`
- **Soul Registry** — Live session tracking with heartbeats and Slack bindings at `~/.claude/soul-sessions/registry.json`. View: `python3 ~/.claude/hooks/soul-registry.py list --md`. Activate: `/ensoul`. Bind to Slack: `/slack-sync #channel`.
- **Session Report** — `/session-report` generates a Markdown dashboard combining session status with git activity.

## References

For detailed schemas and infrastructure:

- `references/data-schemas.md` — Session index, summary cache, JSONL transcript schemas, title_history schema; data source locations; shared library API
- `references/search-mechanics.md` — Transcript FTS indexing pipeline, search query resolution, synonym expansion, AND-to-OR fallback, former-title fallback, ranking algorithm
- `references/daemon-setup.md` — Watcher daemon lifecycle and launchd plist template
- `references/synonyms.json` — Bidirectional synonym groups for search query expansion (Porter stemming handles inflections; groups list distinct vocabulary)
