# Claude Tracker Suite

Session management for Claude Code. Search, resume, spawn, and open sessions across projects---with full-text transcript search, title/nickname history, cmux/Ghostty terminal integration, named sessions, workspace save/restore, macOS notifications, crash recovery, git-aware tracking, and new machine bootstrapping.

**Last updated:** 2026-08-21

**Terminal targets:** cmux (preferred, deterministic CLI), Ghostty (OSC escape sequences + AppleScript), Cursor. VS Code integration is disabled---supplanted by Ghostty.

---

## Why This Skill Exists

Claude Code sessions accumulate fast. After a week of active development, you might have 50+ sessions across 10 projects, some crashed mid-task, some with critical context that wasn't committed. Finding the right session to resume---by topic, by project, by a phrase you remember typing three weeks ago---requires searching the conversations themselves, not just their metadata.

This skill provides 25+ scripts that handle session lifecycle: FTS5 full-text search over every user and assistant message, title/nickname history with rename timelines, an fzf picker, interactive session opening in cmux/Ghostty tabs, named sessions with automatic tab titles, workspace save/restore across reboots (Claude Code and Codex CLI), macOS notifications for session events, yazi file explorer integration, crash recovery with alive detection, automatic workflow phase detection, checkpoints, tagged phrase capture, headless spawning for automation, project discovery, a self-audit, a recall regression suite, and a bootstrap generator for new machines.

---

## Slash Commands

| Command | Description |
|---------|-------------|
| `/claude-tracker-search` | Search sessions by keyword or ID prefix |
| `/claude-tracker` | List recent sessions with status badges |
| `/claude-tracker-recent` | Last N sessions with full metadata (title, tags, summary, cost, model) |
| `/claude-tracker-here` | List top N sessions, open selected in cmux tabs |
| `/claude-tracker-resume` | Resume crashed/inactive sessions; `--workspace` restores all |
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
| **cmux** | `--cmux` | `cmux new-surface` + `cmux send` | Requires cmux running; known UI bugs |
| **Ghostty** | `--ghostty` | AppleScript clipboard-paste | Requires Accessibility permissions; timing-dependent; no native CLI on macOS |
| **VS Code** | `--vscode` | **Disabled** (supplanted by Ghostty)---flag warns and falls back to Ghostty | Code retained, inert |
| **Cursor** | `--cursor` | Opens project in editor + resumes in terminal | Editor-open only; terminal via cmux/Ghostty |

Auto-detect order: cmux (if `cmux ping` succeeds) > Ghostty > print resume command.

---

## Search

Every user and assistant message across every session, indexed in FTS5 and searchable in milliseconds. The query that motivated it---"the session where we worked on my twitter background with imagemagick"---went from unfindable to rank 3 in 75ms.

```bash
claude-tracker-search "subquadratic porthole imagemagick"
claude-tracker-search "twitter banner" --open   # resume top hit in Ghostty
claude-tracker-search "rare term" --deep        # raw JSONL scan, bypasses index
```

Default path: transcript FTS + metadata FTS, merged, with former-title fallback. Multi-word queries match per-term at the session level (terms may land in different messages), expand through synonym groups (`references/synonyms.json`), and fall back from AND to OR with a labeled notice. Ranking: IDF-weighted saturated match-density with a short-session damp. Results carry highlighted snippets.

The index lives in a sidecar `tracker-transcripts.db`, ATTACHed on demand---hooks that write one row per session event open an 11MB `tracker.db`, not a 300MB one.

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
| `--project <name>` | Filter by project |
| `--since <duration>` | Recent only: `7d`, `24h`, `30m` |
| `--json` | Machine-readable output |

---

## Transcript Indexing

```bash
node index-transcripts.js                    # incremental (skips unchanged files)
node index-transcripts.js --rebuild          # full rebuild
```

Incremental indexing skips files whose size, mtime, and extractor version (currently EXTRACTOR_VERSION 4) all match. Bumping the version constant forces a full reindex. Deleted transcripts are pruned on full runs. Read errors are never recorded as indexed---the session stays eligible for the next run.

Since v4, the indexer also extracts **title history events**: `/rename` custom-title lines (source `user`) and slug changes (source `slug`). Custom-title lines route by the line's own `sessionId`---a `/rename` issued after `/resume` targets the previous session, not the file it was written into. This corrects a known upstream behavior where Claude Code's metadata scanner assigns the rename to the wrong session.

Known lexical limit: a session can only be found by words that actually occur in it---the `[expected fail]` regression fixture documents this; a semantic (rlama) layer is the designated future fix.

---

## Title / Nickname History

Every name a session has borne---slug at birth, `/rename` events, slug changes, model-generated titles---recorded in `title_history` with source provenance and inferred timestamps.

```bash
node search-sessions.js titles dfb5613a
```

Default search checks former titles too: a session renamed away from a name you remember still surfaces, labeled with its old name and provenance. Rename events route by the line's own `sessionId`---a `/rename` after `/resume` targets another session, and Claude Code's own scanner titles the wrong one. This suite doesn't.

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

Shows per session: title (custom or auto), summary, all tags (color-coded by type), project name, age, model, cost, turn count, git branch, session ID, and resume command. First result's resume command is auto-copied to clipboard.

---

## Session Listing

```bash
claude-tracker                           # all recent sessions
claude-tracker vscode                    # VS Code sessions only
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
claude-tracker-alive --json              # machine-readable output
```

Cross-references running `claude` PIDs (via `pgrep` + `lsof`) against recent session files. Sessions >3 days without a process show an OLD badge.

---

## Auto-Summarize Daemon

Watch for new sessions and auto-populate summary cache:

```bash
claude-tracker-watch --status            # check if daemon is running
claude-tracker-watch --daemon            # start in background
claude-tracker-watch --stop              # stop running daemon
claude-tracker-watch --verbose           # foreground with debug output
```

The daemon watches `~/.claude/projects/*/sessions-index.json` for changes. When new sessions appear, it caches summaries from Claude Code metadata and regenerates `active-projects.md`. See `references/daemon-setup.md` for launchd plist and lifecycle details.

---

## fzf Session Picker

```bash
claude-tracker-pick                # fuzzy-find last 50, preview, Enter → Ghostty
claude-tracker-pick --here         # Enter resumes in current terminal instead of Ghostty
claude-tracker-pick --project thera --limit 100
```

Enter resumes in a Ghostty tab, Ctrl-O resumes in the current terminal, Ctrl-Y copies the resume command. Preview shows title, summary, and first prompt. Pair with `restore-workspace.sh` (bulk restore from the launchd snapshot)---the picker is for choosing, restore is for "give me back everything".

---

## Resume

### Resume in cmux tab

```bash
resume-session.sh <session-id>                         # auto-detects project directory
resume-session.sh <session-id> --cursor                # also open project in Cursor
resume-session.sh <session-id> --project ~/my-project  # explicit directory
resume-session.sh <session-id> --name "auth-fix"       # set tab title
```

cmux owns the terminal lifecycle. `--cursor` only opens the editor---the session always resumes in cmux. `--vscode` is disabled and falls back to Ghostty. Falls back to printing the resume command if cmux is not running.

### Resume in Ghostty tab

```bash
~/.claude/scripts/ghostty-resume.sh <session-id>
~/.claude/scripts/ghostty-resume.sh <session-id> --project ~/my-project
```

Uses the AppleScript clipboard-paste pattern for reliable command delivery. Launches Ghostty if not running. Search and recent-sessions output includes a `Ghostty:` line per result with the ready-to-run command.

### Resume crashed sessions

```bash
claude-tracker-resume                    # list crashed sessions with resume commands
claude-tracker-resume --tmux             # resume all in tmux windows
claude-tracker-resume --zsh              # resume all in Terminal.app tabs (macOS)
claude-tracker-resume --all              # include non-VS Code sessions
claude-tracker-resume --dry-run          # preview without acting
```

Smart fallback: if `--resume` fails on an expired session, starts a fresh session in that project directory. Sessions older than 7 days show a STALE badge.

---

## Workspace Save/Restore

Survive a logout or reboot with every agent session intact---Claude Code **and** OpenAI Codex CLI:

```bash
node save-workspace.js                        # snapshot to workspace-state.json
node save-workspace.js --dry-run              # preview without writing
claude-tracker-resume --workspace             # restore every session in Ghostty tabs, in order
claude-tracker-resume --workspace --dry-run   # preview
restore-workspace.sh --limit 3                # cap at 3 sessions
```

Claude sessions come from the authoritative `~/.claude/sessions/<pid>.json` PID files; Codex sessions are discovered via `lsof` on their open rollout files (the earliest-opened rollout is the main thread, its filename carries the resume UUID). The manifest is TTY-ordered so tabs restore in their original order, and restore skips sessions that are still running. Restore opens each session in a new Ghostty tab with a 2-second stagger between tab openings, warns when the stamp is >15 min old, and reports per-agent counts.

Periodic snapshots via launchd plist (`com.claude.workspace-snapshot.plist`, every 300s) never overwrite a good snapshot with an empty one---after a crash or logout with zero live sessions, the previous snapshot is preserved. Install the plist:

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
```

Headless and prompt-driven modes use `claude -p` (the Agent SDK CLI). Terminal modes use the clipboard-paste AppleScript pattern for reliable command delivery (handles special characters in prompts).

---

## Named Sessions (`cc` wrapper)

Shell function that wraps `claude` with automatic Ghostty tab naming and tracker tagging:

```bash
source ~/.claude/skills/claude-tracker-suite/scripts/claude-wrapper.sh

cc                            # tab titled to cwd basename
cc --name "kothar-refactor"   # explicit tab title
cc --resume abc123 --name "fix"  # resume with name
```

Sets the Ghostty tab title via OSC 1 escape sequence, tags the session in `tracker.db` on exit. All `new-session.sh`, `resume-session.sh`, and `ghostty-resume.sh` also accept `--name`. When no name is given, the default format is `{project-basename}---{session-id-prefix}`.

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

Phases: `exploring`, `planning`, `implementing`, `testing`, `reviewing`, `debugging`, `committing`, `deploying`.

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

## Session Notifications

macOS notifications when sessions need attention, with Ghostty tab title badges:

```bash
session-notify.sh --needs-input --project "my-app"    # ⚡ badge + notification
session-notify.sh --session-done --project "my-app"   # ✓ badge + notification
session-notify.sh --title "Done" --message "Build complete"  # custom
session-notify.sh --tab-badge "✓" --tab-title "my-app"      # tab badge only
session-notify.sh --needs-input --no-sound                   # silent
```

A Stop hook at `~/.claude/hooks/session-notify-hook.sh` automatically sends a "needs input" notification whenever Claude stops. Registered in `settings.json` as async; opt-in only.

---

## Yazi File Explorer

```bash
open-file-explorer.sh                  # left split (sidebar-style)
open-file-explorer.sh ~/my-project     # specific directory
open-file-explorer.sh --right          # right split
```

Uses System Events clipboard-paste pattern (Cmd+D for split). Requires yazi: `brew install yazi`.

---

## Summary Backfill (disabled by default)

LLM-generated summaries for sessions Claude Code never summarized natively (native generation stopped around v2.1.31, February 2026). Requires explicit opt-in, runs hermetically---no hooks fire, no synthetic sessions persist---and supports two providers:

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

The generated table includes Model, Turns, and Cost columns from enriched session data (extracted from JSONL transcripts). Git worktree sessions show a tree emoji badge. The auto-name path (one-shot `claude --model haiku` call for sessions without summaries) is disabled by default---set `TRACKER_AUTO_NAME=1` to re-enable it.

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

## Workflows

### Find and Resume

1. `claude-tracker-search "topic"` --- find matching sessions
2. `claude-tracker-recent` --- browse last 10 sessions with full metadata
3. `claude --resume <session-id>` --- resume in current terminal
4. `~/.claude/scripts/ghostty-resume.sh <session-id>` --- resume in a new Ghostty tab
5. `open-sessions.js` --- list top sessions, open selected in cmux tabs
6. Or `claude-tracker-resume --tmux` --- auto-resume all crashed sessions

### Open Sessions in cmux

```bash
node open-sessions.js                          # list top 10, prompt for selection
node open-sessions.js --split right            # open as vertical splits
node open-sessions.js --yes                    # open all without confirmation
node open-sessions.js --json                   # JSON output for scripting
```

Session directories are resolved from JSONL ground truth (`decodeProjectPath`), not from `active-projects.md`. Falls back to printing resume commands when cmux is unavailable. See `references/cmux-commands.md` for the full cmux CLI reference.

### Monitor Active Work

1. `claude-tracker-alive` --- see what's running vs stale
2. `claude-tracker-watch --daemon` --- keep summaries auto-updated
3. Read `~/.claude/agent_docs/active-projects.md` --- curated project overview

---

## Database

Single SQLite database at `~/.claude/tracker.db` consolidates all session metadata, git tracking, tags, checkpoints, phase tracking, and tagged phrases. Transcript FTS lives in a sidecar `tracker-transcripts.db` (ATTACHed on demand).

**API module**: `~/.claude/lib/tracker-db.js` --- synchronous better-sqlite3, WAL mode, singleton lazy-open.
**Shared utils**: `~/.claude/lib/tracker-utils.js` --- path decoding, session parsing, git remote detection.
**Migration** (idempotent): `node ~/.claude/scripts/migrate-to-sqlite.js`

Tables: `sessions`, `sessions_fts`, `title_history`, `checkpoints`, `phases`, `tagged_phrases`, `tagged_phrase_tags`, `transcript_index_state`.

### DB Maintenance

`db-maintain.js` merges FTS segments and truncates WALs on both databases, skipping when an indexer is mid-run. Scheduled Sundays 04:30 via `com.claude.db-maintain.plist`.

### Self-Audit and Regression

```bash
node audit-suite.js          # inventory, portability, daemons, DB coverage → AUDIT.md
node search-regression.js    # recall fixtures; exit 1 on regression
```

The regression suite includes an expected-fail fixture documenting the semantic-recall gap---if it ever passes, a semantic layer landed.

---

## Related Systems

- **Git Tracking** --- PreToolUse/PostToolUse hooks intercept git commands, tag sessions with repos they touch. Query via `tracker-utils.js` functions (`getSessionsForRepo`, `getReposForSession`, `getRecentCommits`). See `references/data-schemas.md` for hook files and index format.
- **Speculator** --- Daemon at `~/.claude/scripts/speculator/` maps Ghostty tabs to sessions every 5 minutes. `list-sessions.js` uses `loadSpeculatorData()` and `getSessionTTY()` for TTY badges. Health check: `bash ~/.claude/scripts/speculator/status.sh`
- **Soul Registry** --- Live session tracking with heartbeats and Slack bindings at `~/.claude/soul-sessions/registry.json`. View: `python3 ~/.claude/hooks/soul-registry.py list --md`. Activate: `/ensoul`. Bind to Slack: `/slack-sync #channel`.
- **Session Report** --- `/session-report` generates a Markdown dashboard combining session status with git activity.

---

## References

- `references/data-schemas.md` --- Session index, summary cache, JSONL transcript schemas, title_history schema; data source locations; shared library API
- `references/search-mechanics.md` --- Transcript FTS indexing pipeline, search query resolution, synonym expansion, AND-to-OR fallback, former-title fallback, ranking algorithm
- `references/daemon-setup.md` --- Watcher daemon lifecycle and launchd plist template
- `references/synonyms.json` --- Bidirectional synonym groups for search query expansion
- `references/cmux-commands.md` --- Complete cmux CLI reference

---

## Scripts

| Script | Usage |
|--------|-------|
| `search-sessions.js` | `node search-sessions.js "query" [--id <prefix>] [titles <prefix>] [--open] [--deep]` |
| `index-transcripts.js` | `node index-transcripts.js [--rebuild] [--limit N] [--quiet]` |
| `backfill-summaries.js` | `node backfill-summaries.js --enable [--provider claude\|openrouter] [--dry-run] [--session <id>]` |
| `claude-tracker-pick` | `claude-tracker-pick [--here] [--project <name>] [--limit N]` |
| `db-maintain.js` | `node db-maintain.js [--quiet]` |
| `audit-suite.js` | `node audit-suite.js` |
| `search-regression.js` | `node search-regression.js [--json]` |
| `open-sessions.js` | `node open-sessions.js [--limit N] [--cmux\|--ghostty] [--split <dir>] [--yes] [--json]` |
| `resume-session.sh` | `bash resume-session.sh <session-id> [--cmux\|--ghostty\|--cursor] [--name <title>]` |
| `list-sessions.js` | `node list-sessions.js [--limit 20]` |
| `recent-sessions.js` | `node recent-sessions.js [--limit N] [--project <name>] [--model <name>] [--since <dur>] [--json]` |
| `new-session.sh` | `bash new-session.sh [dir] [--prompt "text"] [--headless] [--model <name>] [--name <title>] [--output-format text]` |
| `claude-wrapper.sh` | `source claude-wrapper.sh` then `cc [--name <title>] [--resume <id>]` |
| `save-workspace.js` | `node save-workspace.js [--dry-run\|--json]` |
| `restore-workspace.sh` | `bash restore-workspace.sh [--dry-run] [--limit N]` |
| `session-notify.sh` | `bash session-notify.sh [--needs-input\|--session-done] [--title X --message Y] [--no-sound]` |
| `open-file-explorer.sh` | `bash open-file-explorer.sh [<dir>] [--left\|--right]` |
| `checkpoint-session.js` | `node checkpoint-session.js create "label" [--summary "text"] \| list [--phase X] [--limit N]` |
| `quote-session.js` | `node quote-session.js capture "phrase" --tags a,b \| search "term" \| tag <name> \| list` |
| `tag-session.js` | `node tag-session.js <session-id> "tag-name"` |
| `detect-projects.js` | `node detect-projects.js [--suggest\|--scaffold] [--since <dur>]` |
| `bootstrap-claude-setup.js` | `node bootstrap-claude-setup.js --user "Name" [--dry-run]` |

The two launchd plists hardcode absolute paths (launchd does not expand `$HOME`)---edit the `/Users/<you>/...` strings before copying them to `~/Library/LaunchAgents/`.

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
