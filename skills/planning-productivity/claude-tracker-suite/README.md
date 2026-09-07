# Claude Tracker Suite

Session management for Claude Code. Search, resume, spawn, and open sessions across projects—with full-text transcript search, title/nickname history, Ghostty terminal integration, named sessions, workspace save/restore, crash recovery, git-aware tracking, and new machine bootstrapping.

**Last updated:** 2026-09-07

**Terminal target:** Ghostty (the only target). cmux, tmux, Terminal.app, and VS Code are retired. Cursor is supported as an editor-only sidebar (`--cursor` opens the project in the editor; the session always resumes in Ghostty).

---

## Why This Skill Exists

Claude Code sessions accumulate fast. After a week of active development, you might have 50+ sessions across 10 projects, some crashed mid-task, some with critical context that wasn't committed. Finding the right session to resume—by topic, by project, by a phrase you remember typing three weeks ago—requires searching the conversations themselves, not just their metadata.

This skill provides 25+ scripts that handle session lifecycle: FTS5 full-text search over every user and assistant message, title/nickname history with rename timelines, an fzf picker, interactive session opening in Ghostty tabs, named sessions with automatic tab titles, workspace save/restore across reboots (Claude Code and Codex CLI), crash recovery with alive detection, automatic workflow phase detection, checkpoints, tagged phrase capture, headless spawning for automation, project discovery, a self-audit, a recall regression suite, and a bootstrap generator for new machines.

---

## Slash Commands

| Command | Description |
|---------|-------------|
| `/claude-tracker-search` | Search sessions by keyword or ID prefix |
| `/claude-tracker` | List recent sessions with status badges |
| `/claude-tracker-recent` | Last N sessions with full metadata (title, tags, summary, cost, model) |
| `/claude-tracker-here` | List sessions for the current working directory |
| `/claude-tracker-resume` | Resume a session by its number from `/claude-tracker` output |
| `/spawn` | Start new interactive, prompt-driven, or headless session |
| `/checkpoint` | Create a named bookmark at the current point |
| `/checkpoint-list` | Query checkpoints by phase, label, or limit |
| `/quote` | Capture a tagged phrase from the session |
| `/quote-search` | Search tagged phrases via FTS5 |
| `/tag` | Manually tag the current session |
| `/session-report` | Generate a Markdown dashboard (separate skill, references tracker data) |

---

## Structure

```
claude-tracker-suite/
  SKILL.md                                 # CLI reference and workflows
  README.md                                # This file
  references/
    daemon-setup.md                        # Watcher daemon lifecycle and launchd plist
    data-schemas.md                        # tracker.db schema, title_history, JSONL formats
    search-mechanics.md                    # Indexing, ranking, synonym expansion, fallbacks
    synonyms.json                          # Token groups for query expansion
  scripts/
    search-sessions.js                     # FTS search, --id lookup, titles timeline
    index-transcripts.js                   # Incremental transcript FTS indexer (module + CLI)
    backfill-summaries.js                  # LLM summary backfill (disabled by default)
    claude-tracker-pick                    # fzf picker with preview
    db-maintain.js                         # Weekly FTS optimize + WAL checkpoint
    audit-suite.js                         # Self-audit → AUDIT.md
    search-regression.js                   # Recall regression fixtures
    open-sessions.js                       # List top N sessions, open in Ghostty tabs
    resume-session.sh                      # Thin wrapper over ghostty-resume.sh (+Cursor)
    list-sessions.js                       # List recent sessions with status badges
    recent-sessions.js                     # Last N sessions with full metadata
    new-session.sh                         # Start new interactive/prompt-driven/headless session
    claude-wrapper.sh                      # Shell function `cc` for named sessions with tab titles
    save-workspace.js                      # Snapshot alive sessions to workspace-state.json
    restore-workspace.sh                   # Restore sessions from workspace-state.json
    open-file-explorer.sh                  # Open yazi in Ghostty split pane
    checkpoint-session.js                  # Named bookmarks within sessions
    quote-session.js                       # Tagged phrase capture + FTS search
    tag-session.js                         # Manual session tagging
    com.claude.workspace-snapshot.plist    # launchd plist for periodic workspace snapshots
    com.claude.transcript-index.plist      # launchd plist for hourly transcript indexing
    com.claude.db-maintain.plist           # launchd plist for weekly DB maintenance
    bootstrap-claude-setup.js              # Generate complete ~/.claude/ structure
    detect-projects.js                     # Project discovery and CLAUDE.md scaffolding
```

---

## Search

Every user and assistant message across every session, indexed in FTS5 and searchable in milliseconds. The query that motivated it—"the session where we worked on my twitter background with imagemagick"—went from unfindable to rank 3 in 75ms.

```bash
claude-tracker-search "subquadratic porthole imagemagick"
claude-tracker-search "twitter banner" --open   # resume top hit in Ghostty
claude-tracker-search "rare term" --deep        # raw JSONL scan, bypasses index
```

Default path: transcript FTS + metadata FTS, merged, with former-title fallback. Before every body search, `search-sessions.js` runs an in-process index refresh (1.5s budget) so sessions from today are searchable within seconds of their last turn. Multi-word queries match per-term at the session level (terms may land in different messages), expand through synonym groups (`references/synonyms.json`), and fall back from AND to OR with a labeled notice. Ranking: IDF-weighted saturated match-density with a short-session damp. Results carry highlighted snippets.

The index lives in a sidecar `tracker-transcripts.db`, ATTACHed on demand—hooks that write one row per session event open an 11MB `tracker.db`, not a 300MB one.

### Metadata bm25 column weights

| Field | Weight | Why |
|-------|--------|-----|
| Custom title | 3x | You named it that for a reason |
| Auto title / Summary | 2x | Most descriptive of what happened |
| First prompt | 1.5x | Captures intent |
| Slug | 1x | Auto-nickname |

### Flags

| Flag | Description |
|------|-------------|
| `--limit <n>` | Max results (default: 15) |
| `--id <prefix>` | Lookup by session ID prefix (8+ chars) |
| `titles <prefix>` | Title/nickname history timeline |
| `--name` | Metadata FTS only (fastest) |
| `--deep` | Raw JSONL scan, bypasses index |
| `--open` | Resume top hit in a new Ghostty tab |
| `--copy` | Copy top hit's resume command to clipboard (opt-in; nothing writes clipboard by default) |
| `--no-refresh` | Skip the on-demand index catch-up before searching |
| `--project <name>` | Filter by project |
| `--since <duration>` | Recent only: `7d`, `24h`, `30m` |
| `--json` | Machine-readable output |

---

## Transcript Indexing

```bash
node index-transcripts.js                    # incremental (skips unchanged files)
node index-transcripts.js --rebuild          # full rebuild
node index-transcripts.js --session <id>     # single session (what hooks call)
node index-transcripts.js --budget 1500      # budget-limited (what search calls in-process)
```

The indexer runs automatically through three channels:

1. **Hooks**: Stop hook (async, `--stdin --quiet --debounce 120`) and SessionEnd hook (sync, `--stdin --quiet --debounce 10`) so every session is searchable within seconds of its last turn.
2. **In-process**: `search-sessions.js` calls `refreshTranscriptIndex()` before every body search with a 1.5s budget, printing `Index refreshed: N session(s) in Xms — M still pending`.
3. **Hourly launchd**: `com.claude.transcript-index` agent (plist in `scripts/`, installed in `~/Library/LaunchAgents/`, logs in `~/.claude/logs/transcript-index.{log,err}`, uses `/opt/homebrew/bin/node`).

As a module it exports `indexOne`, `refreshTranscriptIndex`, `indexSession`, and `findTranscript`. CLI flags: `--rebuild --limit N --budget MS --quiet --session ID --file PATH --stdin --debounce SEC`.

Incremental indexing skips files whose size, mtime, and extractor version (currently EXTRACTOR_VERSION 4) all match. Bumping the version constant forces a full reindex. Deleted transcripts are pruned on full runs. Read errors are never recorded as indexed—the session stays eligible for the next run.

Since v4, the indexer also extracts **title history events**: `/rename` custom-title lines (source `user`) and slug changes (source `slug`). Custom-title lines route by the line's own `sessionId`—a `/rename` issued after `/resume` targets the previous session, not the file it was written into. This corrects a known upstream behavior where Claude Code's metadata scanner assigns the rename to the wrong session.

Known lexical limit: a session can only be found by words that actually occur in it—the `[expected fail]` regression fixture documents this; a semantic (rlama) layer is the designated future fix.

---

## Title / Nickname History

Every name a session has borne—slug at birth, `/rename` events, slug changes, model-generated titles—recorded in `title_history` with source provenance and inferred timestamps.

```bash
node search-sessions.js titles dfb5613a
```

Default search checks former titles too: a session renamed away from a name you remember still surfaces, labeled with its old name and provenance. Rename events route by the line's own `sessionId`—a `/rename` after `/resume` targets another session, and Claude Code's own scanner titles the wrong one. This suite doesn't.

Sources: `user` (custom titles), `slug` (auto-nicknames), `cache` (May 2026 metadata import), `summarizer` (from `backfill-summaries.js`).

---

## Recent Sessions

Full metadata view of the last N sessions:

```bash
claude-tracker-recent                          # last 10 with full metadata
claude-tracker-recent --limit 20               # last 20
claude-tracker-recent --json                   # machine-readable
claude-tracker-recent --project myapp          # filter by project
claude-tracker-recent --model opus             # filter by model
claude-tracker-recent --since 7d               # last 7 days only
```

Shows per session: title (custom or auto), summary, all tags (color-coded by type), project name, age, model, cost, turn count, git branch, session ID, and resume command. Add `--copy` to put the first resume command on the clipboard (never done by default).

---

## Session Listing

```bash
claude-tracker                           # all recent sessions
```

Status badges: ACTIVE (process running, recent heartbeat), STALE (process exists but no recent activity), OLD (older than 24 hours), CRASHED (process not found, no clean exit).

When speculator is running, the listing includes Ghostty tab count and window count in the header, plus TTY badges per session showing which Ghostty tab it occupies.

---

## Alive Detection

Check which sessions have running Claude processes:

```bash
claude-tracker-alive                     # running + stale sessions overview
claude-tracker-alive --running           # only sessions with active processes
claude-tracker-alive --stale             # only sessions with no process
claude-tracker-alive --all-kinds         # include headless/background sessions
claude-tracker-alive --json              # machine-readable output
```

Source of truth is Claude Code's PID files (`~/.claude/sessions/<pid>.json`), verified against one `ps` pass. Matching is by sessionId—a crashed session next to a live sibling in the same directory is no longer reported RUNNING. Sessions >3 days without a process show an OLD badge.

---

## Auto-Summarize Daemon

Watch for new sessions and auto-populate summary cache:

```bash
claude-tracker-watch --status            # check if daemon is running
claude-tracker-watch --daemon            # start in background
claude-tracker-watch --stop              # stop running daemon
claude-tracker-watch --verbose           # foreground with debug output
```

Dormant: it watches `sessions-index.json`, which Claude Code no longer writes, so it never fires on current versions. Kept for reference; see `references/daemon-setup.md` for the launchd agents that do run (workspace-snapshot, transcript-index, db-maintain).

---

## fzf Session Picker

```bash
claude-tracker-pick                # fuzzy-find last 50, preview, Enter → Ghostty
claude-tracker-pick --here         # Enter resumes in current terminal instead of Ghostty
claude-tracker-pick --project thera --limit 100
```

Enter resumes in a Ghostty tab, Ctrl-O resumes in the current terminal, Ctrl-Y copies the resume command. Preview shows title, summary, and first prompt. Pair with `restore-workspace.sh` (bulk restore from the launchd snapshot)—the picker is for choosing, restore is for "give me back everything".

---

## Resume

### Resume in Ghostty tab

The single terminal opener for the suite is `~/.claude/scripts/ghostty-resume.sh`. It writes a tiny launcher to `~/.claude/run/launch/` and opens it in a new Ghostty tab or split.

```bash
~/.claude/scripts/ghostty-resume.sh <session-id>
~/.claude/scripts/ghostty-resume.sh <session-id> --project ~/my-project --name "auth-fix"
~/.claude/scripts/ghostty-resume.sh <session-id> --split right       # split focused terminal
~/.claude/scripts/ghostty-resume.sh <session-id> --print             # write launcher, print path
```

On Ghostty >= 1.3.0: AppleScript dictionary—no keystrokes, no clipboard, no focus dependency. On older builds: activate + Cmd-T + one Cmd-V paste (clipboard saved/restored). `--split` requires >= 1.3.0.

`resume-session.sh` is a thin wrapper that delegates to the opener. `--cursor` also opens the project in Cursor. `--cmux` and `--vscode` print retirement notes.

### Resume crashed sessions

```bash
claude-tracker-resume                    # list crashed sessions with resume commands
claude-tracker-resume --open             # reopen each in a new Ghostty tab
claude-tracker-resume --open --limit 3   # reopen at most 3
claude-tracker-resume --dry-run          # preview without acting
claude-tracker-resume --days 14          # widen look-back window (default 7)
```

A crashed session is the newest transcript per project (within the look-back window) that has no live process, for projects with no live tab at all. Sessions older than 3 days show an OLD badge. `--tmux` and `--zsh` are retired—they print a note and map to `--open`.

---

## Workspace Save/Restore

Survive a logout or reboot with every agent session intact—Claude Code **and** OpenAI Codex CLI:

```bash
node save-workspace.js                        # snapshot to workspace-state.json
node save-workspace.js --dry-run              # preview without writing
claude-tracker-resume --workspace             # restore every session in Ghostty tabs, in order
claude-tracker-resume --workspace --dry-run   # preview
restore-workspace.sh --limit 3                # cap at 3 sessions
restore-workspace.sh --stagger 3              # seconds between tabs (default 1)
```

Claude sessions come from the authoritative `~/.claude/sessions/<pid>.json` PID files; Codex sessions are discovered via `lsof` on their open rollout files (the earliest-opened rollout is the main thread, its filename carries the resume UUID). The manifest is TTY-ordered so tabs restore in their original order, and restore skips sessions that are still running, missing directories, and missing transcripts—each with a reason, never aborting on one failure. Restore reports per-agent counts and warns when the stamp is >15 min old.

Periodic snapshots via launchd plist (`com.claude.workspace-snapshot.plist`, every 300s) never overwrite a good snapshot with an empty one—after a crash or logout with zero live sessions, the previous snapshot is preserved. Install the plist:

```bash
cp ~/.claude/skills/claude-tracker-suite/scripts/com.claude.workspace-snapshot.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.claude.workspace-snapshot.plist
```

---

## New Session / Spawn

```bash
new-session.sh ~/my-project                                    # interactive in Ghostty
new-session.sh ~/my-project --model opus                       # specific model
new-session.sh ~/my-project --prompt "fix the login bug"       # prompt-driven in Ghostty tab
new-session.sh ~/my-project --headless --prompt "summarize"    # headless, returns JSON
new-session.sh ~/my-project --headless --prompt "fix tests" --output-format text  # plain text output
new-session.sh ~/my-project --name "auth-rewrite"              # named tab
new-session.sh ~/my-project --cursor                           # also open in Cursor
```

Headless and prompt-driven modes use `claude -p` (the Agent SDK CLI). Terminal modes delegate to `ghostty-resume.sh --exec`. `--cmux` and `--vscode` print retirement notes.

---

## Named Sessions (`cc` wrapper)

Shell function that wraps `claude` with automatic Ghostty tab naming and tracker tagging:

```bash
source ~/.claude/skills/claude-tracker-suite/scripts/claude-wrapper.sh

cc                            # tab titled to cwd basename
cc --name "kothar-refactor"   # explicit tab title
cc --resume abc123 --name "fix"  # resume with name
```

Sets the Ghostty tab title via OSC 1 escape sequence, tags the session in `tracker.db` on exit.

---

## Checkpoints

Named bookmarks within sessions capturing label, git state, workflow phase, and modified files:

```bash
node checkpoint-session.js create "finished auth module"
node checkpoint-session.js create "pre-deploy" --summary "about to push"
node checkpoint-session.js list
node checkpoint-session.js list --phase implementing
node checkpoint-session.js list --limit 10
```

Auto-checkpoints are created on git commits (`git-track-post.sh`) and phase transitions (`phase-detect.py`). Live renames also drop an auto-checkpoint.

---

## Phase Tracking

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

---

## Tagged Phrases / Quotes

Notable excerpts captured from sessions with tags, searchable via FTS5:

```bash
node quote-session.js capture "assumptions are the enemy" --tags principle,design
node quote-session.js search "assumptions"
node quote-session.js tag principle
node quote-session.js list --limit 20
```

Phrases are also auto-extracted by the `session-tags-infer.py` Stop hook during LLM inference.

---

## Manual Tagging

```bash
node tag-session.js <session-id> "tag-name"
```

Manual session tagging with provenance tracking. Tags appear color-coded in `claude-tracker-recent` output.

---

## Summary Backfill (disabled by default)

LLM-generated summaries for sessions Claude Code never summarized natively (native generation stopped around v2.1.31, February 2026). Requires explicit opt-in, runs hermetically—no hooks fire, no synthetic sessions persist—and supports two providers:

```bash
node backfill-summaries.js --dry-run                       # preview, no LLM calls
node backfill-summaries.js --enable                        # claude CLI, haiku
node backfill-summaries.js --enable --provider openrouter  # OpenRouter, kimi-k2
node backfill-summaries.js --enable --session <id-prefix>  # force one session
```

---

## Update Active Projects

```bash
python3 ~/.claude/scripts/update-active-projects.py              # regenerate active-projects.md
python3 ~/.claude/scripts/update-active-projects.py --summarize  # show sessions needing summaries
```

The generated table includes Model, Turns, and Cost columns from enriched session data (extracted from JSONL transcripts). Git worktree sessions show a tree emoji badge. The auto-name path (one-shot `claude --model haiku` call for sessions without summaries) is disabled by default—set `TRACKER_AUTO_NAME=1` to re-enable it.

---

## Project Detection

```bash
node detect-projects.js                # list all discovered projects
node detect-projects.js --suggest      # suggest additions
node detect-projects.js --scaffold     # create CLAUDE.md stubs
node detect-projects.js --since 30d    # recent only
```

Scans sessions to find all projects, checks CLAUDE.md coverage, suggests missing scaffolds.

---

## Bootstrap New Setup

Generate a complete `~/.claude/` configuration for a new machine:

```bash
node bootstrap-claude-setup.js --user "Name" --dry-run    # preview
node bootstrap-claude-setup.js --user "Name"              # create everything
```

Creates directory structure, global CLAUDE.md, userModel template, agent_docs stubs, and project CLAUDE.md scaffolds. Follow up with `/claude-md-manager` to enrich generated files.

---

## Yazi File Explorer

```bash
open-file-explorer.sh                  # left split (sidebar-style)
open-file-explorer.sh ~/my-project     # specific directory
open-file-explorer.sh --right          # right split
```

Uses System Events clipboard-paste pattern (Cmd+D for split). Requires yazi: `brew install yazi`.

---

## Native Claude Code Features

Claude Code 2.1.263+ provides session management primitives that overlap with parts of this suite. Where native is sufficient, use it directly:

- `claude -r|--resume [id|name|search-term]` — built-in picker with search across all projects
- `-n/--name` — name a session at launch
- `/rename` — rename the current session
- `--fork-session` — fork a session for exploratory work
- `--from-pr` — start a session seeded with a PR's context
- `--bg` + `claude attach` — background sessions with attach/detach
- `-w/--worktree` — worktree isolation

This suite's `cleanupPeriodDays` is 99999 so transcripts never expire.

---

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

---

## Workflows

### Find and Resume

1. `claude-tracker-search "topic"` — find matching sessions
2. `claude-tracker-recent` — browse last 10 sessions with full metadata
3. `claude --resume <session-id>` — resume in current terminal
4. `~/.claude/scripts/ghostty-resume.sh <session-id>` — resume in a new Ghostty tab
5. `claude-tracker-resume --open` — auto-resume all crashed sessions in Ghostty

### Monitor Active Work

1. `claude-tracker-alive` — see what's running vs stale
2. `claude-tracker-watch --daemon` — keep summaries auto-updated
3. Read `~/.claude/agent_docs/active-projects.md` — curated project overview

---

## Database

Single SQLite database at `~/.claude/tracker.db` consolidates all session metadata, git tracking, tags, checkpoints, phase tracking, and tagged phrases. Transcript FTS lives in a sidecar `tracker-transcripts.db` (ATTACHed on demand).

**API module**: `~/.claude/lib/tracker-db.js` — synchronous node:sqlite `DatabaseSync` (built into Node >= 22.13, no native module to rebuild), WAL mode, singleton lazy-open. The compat shim keeps the `prepare/run/get/all/exec/pragma/transaction` surface and throws on a missing named parameter. `isAvailable()` is a real open probe; `tryDb()` prints `tracker-db unavailable: <reason> — falling back to JSONL scan` to stderr once per process.

**Shared utils**: `~/.claude/lib/tracker-utils.js` — path decoding, session parsing, live-session detection (`getLiveSessions`, `getLiveSessionIds`, `getStaleSessions`), git remote detection.

**Migration** (idempotent): `node ~/.claude/scripts/migrate-to-sqlite.js`

Tables: `sessions`, `sessions_fts`, `title_history`, `checkpoints`, `phases`, `tagged_phrases`, `tagged_phrase_tags`, `transcript_index_state` (in sidecar).

### DB Maintenance

`db-maintain.js` merges FTS segments and truncates WALs on both databases, skipping when an indexer is mid-run. Scheduled Sundays 04:30 via `com.claude.db-maintain.plist`.

### Self-Audit and Regression

```bash
node audit-suite.js          # inventory, portability, daemons, DB coverage → AUDIT.md
node search-regression.js    # recall fixtures; exit 1 on regression
```

The regression suite includes an expected-fail fixture documenting the semantic-recall gap—if it ever passes, a semantic layer landed.

---

## Related Systems

- **Git Tracking** — PreToolUse/PostToolUse hooks intercept git commands, tag sessions with repos they touch. Query via `tracker-utils.js` functions (`getSessionsForRepo`, `getReposForSession`, `getRecentCommits`). See `references/data-schemas.md` for hook files and index format.
- **Speculator** — Daemon at `~/.claude/scripts/speculator/` maps Ghostty tabs to sessions every 5 minutes. `list-sessions.js` uses `loadSpeculatorData()` and `getSessionTTY()` for TTY badges. Health check: `bash ~/.claude/scripts/speculator/status.sh`
- **Soul Registry** — Live session tracking with heartbeats and Slack bindings at `~/.claude/soul-sessions/registry.json`. View: `python3 ~/.claude/hooks/soul-registry.py list --md`. Activate: `/ensoul`. Bind to Slack: `/slack-sync #channel`.
- **Session Report** — `/session-report` generates a Markdown dashboard combining session status with git activity.

---

## References

- `references/data-schemas.md` — Session index, summary cache, JSONL transcript schemas, title_history schema; data source locations; shared library API
- `references/search-mechanics.md` — Transcript FTS indexing pipeline, search query resolution, synonym expansion, AND-to-OR fallback, former-title fallback, ranking algorithm
- `references/daemon-setup.md` — Watcher daemon lifecycle and launchd plist template
- `references/synonyms.json` — Bidirectional synonym groups for search query expansion

---

## Scripts

| Script | Usage |
|--------|-------|
| `search-sessions.js` | `node search-sessions.js "query" [--id <prefix>] [titles <prefix>] [--open] [--copy] [--deep] [--no-refresh]` |
| `index-transcripts.js` | `node index-transcripts.js [--rebuild] [--limit N] [--budget MS] [--quiet] [--session ID] [--file PATH] [--stdin] [--debounce SEC]` |
| `backfill-summaries.js` | `node backfill-summaries.js --enable [--provider claude\|openrouter] [--dry-run] [--session <id>]` |
| `claude-tracker-pick` | `claude-tracker-pick [--here] [--project <name>] [--limit N]` |
| `db-maintain.js` | `node db-maintain.js [--quiet]` |
| `audit-suite.js` | `node audit-suite.js` |
| `search-regression.js` | `node search-regression.js [--json]` |
| `open-sessions.js` | `node open-sessions.js [--limit N] [--yes] [--json] [--list]` |
| `resume-session.sh` | `bash resume-session.sh <session-id> [--project <path>] [--name <title>] [--cursor]` |
| `list-sessions.js` | `node list-sessions.js [--limit 20]` |
| `recent-sessions.js` | `node recent-sessions.js [--limit N] [--project <name>] [--model <name>] [--since <dur>] [--json]` |
| `new-session.sh` | `bash new-session.sh [dir] [--prompt "text"] [--headless] [--model <name>] [--name <title>] [--output-format text] [--cursor]` |
| `claude-wrapper.sh` | `source claude-wrapper.sh` then `cc [--name <title>] [--resume <id>]` |
| `save-workspace.js` | `node save-workspace.js [--dry-run\|--json]` |
| `restore-workspace.sh` | `bash restore-workspace.sh [--dry-run] [--limit N] [--stagger SEC]` |
| `open-file-explorer.sh` | `bash open-file-explorer.sh [<dir>] [--left\|--right]` |
| `checkpoint-session.js` | `node checkpoint-session.js create "label" [--summary "text"] \| list [--phase X] [--limit N]` |
| `quote-session.js` | `node quote-session.js capture "phrase" --tags a,b \| search "term" \| tag <name> \| list` |
| `tag-session.js` | `node tag-session.js <session-id> "tag-name"` |
| `detect-projects.js` | `node detect-projects.js [--suggest\|--scaffold] [--since <dur>]` |
| `bootstrap-claude-setup.js` | `node bootstrap-claude-setup.js --user "Name" [--dry-run]` |
| `ghostty-resume.sh` | `bash ghostty-resume.sh <id> [--agent claude\|codex] [--project <path>] [--name <title>] [--split [dir]] [--print] [--exec "<cmd>"]` |

CLI wrappers in `~/.local/bin/` (thin `exec node` / `exec bash` wrappers):

| Wrapper | Delegates to |
|---------|-------------|
| `claude-tracker` | `scripts/list-sessions.js` |
| `claude-tracker-search` | `scripts/search-sessions.js` |
| `claude-tracker-recent` | `scripts/recent-sessions.js` |
| `ccnew` | `scripts/new-session.sh` |

Standalone scripts (not wrappers):

| Script | Location |
|--------|----------|
| `claude-tracker-alive` | `~/.local/bin/claude-tracker-alive` |
| `claude-tracker-resume` | `~/.local/bin/claude-tracker-resume` |

The launchd plists hardcode absolute paths (launchd does not expand `$HOME`)—edit the `/Users/<you>/...` strings before copying them to `~/Library/LaunchAgents/`.

---

## Requirements

- Node.js >= 22.13 (Homebrew at `/opt/homebrew/bin/node`; Node 26.8.1 with SQLite 3.53.4 + FTS5/porter)
- Claude Code CLI installed
- macOS (for Ghostty/System Events automation)
- Ghostty (>= 1.3.0 for native AppleScript dictionary and splits; older builds use the Cmd-T + paste fallback)
- fzf (for `claude-tracker-pick`)
- sqlite3 CLI (for the pick script and ad-hoc queries)
- Python 3 (for hooks: session-sync-db.py, phase-detect.py, session-tags-infer.py)
- No npm install—the DB module uses Node's built-in `node:sqlite`

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)—curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/planning-productivity/claude-tracker-suite ~/.claude/skills/
```
