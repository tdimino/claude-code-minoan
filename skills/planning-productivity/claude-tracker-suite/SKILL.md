---
name: claude-tracker-suite
description: "Manage Claude Code sessions — search by topic or ID, browse recent sessions with full metadata (tags, summaries, titles, cost), view title/nickname history timelines, resume in Ghostty tabs, spawn interactive or headless sessions, monitor live sessions, and bootstrap new setups. Triggers on resume session, find session, list sessions, recent sessions, spawn session, session history, what was I working on, open in ghostty, title history, session nicknames."
argument-hint: [query or --id <prefix>]
allowed-tools: Bash(claude-tracker*), Bash(node ~/.claude/skills/claude-tracker-suite/scripts/*), Bash(~/.claude/skills/claude-tracker-suite/scripts/*.sh), Bash(python3 ~/.claude/scripts/*), Read, Grep, Glob, Edit, Write, Skill
---

# Claude Session Management Suite

Search, browse, monitor, and manage Claude Code session history across all projects.

## Tools

Commands on PATH (`~/.local/bin`) are thin wrappers around scripts in `scripts/`; scripts run directly with `node` or `bash` from `~/.claude/skills/claude-tracker-suite/scripts/`.

**Everyday use**

| Tool | Invoked by | Purpose |
|------|-----------|---------|
| `claude-tracker-search` → `search-sessions.js` | `/claude-tracker-search` | Keyword search, `--id` prefix lookup, `titles <id>` timeline |
| `claude-tracker-recent` → `recent-sessions.js` | `/claude-tracker-recent` | Last N sessions with title, tags, summary, model, cost (headless sdk-cli sessions only with `--all`) |
| `claude-tracker` → `list-sessions.js` | `/claude-tracker` | Recent sessions with status badges |
| `claude-tracker-alive` | Direct | Which sessions have running processes |
| `claude-tracker-resume` | `/claude-tracker-resume` | Find and reopen crashed sessions; `--workspace` restores the last stamp |
| `scripts/claude-tracker-pick` | Direct | fzf picker with preview; Enter→Ghostty, Ctrl-O→current terminal, Ctrl-Y→copy |
| `scripts/open-sessions.js` | Direct | List top N sessions, open the selected ones in Ghostty tabs |
| `scripts/new-session.sh` | `/spawn` | New interactive, prompt-driven, or headless session |
| `scripts/resume-session.sh` | Direct | Open a session in a Ghostty tab, optionally the project in Cursor |
| `~/.claude/scripts/ghostty-resume.sh` | Direct | The suite's single terminal opener (tabs and splits) |
| `scripts/checkpoint-session.js` | `/checkpoint`, `/checkpoint-list` | Named bookmarks within sessions |
| `scripts/quote-session.js` | `/quote`, `/quote-search` | Capture and search tagged phrases (FTS5) |
| `scripts/tag-session.js` | `/tag` | Manual session tags with provenance |

**Index, maintenance, and setup** (details in `references/operations.md`)

| Tool | Invoked by | Purpose |
|------|-----------|---------|
| `scripts/index-transcripts.js` | Hooks / launchd / in-process | Incremental transcript FTS indexer; session metadata and title history |
| `scripts/db-maintain.js` | Weekly launchd | FTS optimize, WAL truncate, VACUUM when a quarter of pages are free |
| `scripts/search-regression.js` | After search changes | Recall fixtures (exit 1 on regression) |
| `scripts/audit-suite.js` | Direct | Self-audit → AUDIT.md |
| `scripts/backfill-summaries.js` | Direct | Hermetic summary backfill (disabled by default, `--enable`) |
| `scripts/save-workspace.js`, `scripts/restore-workspace.sh` | launchd / direct | Snapshot live sessions; restore them into Ghostty tabs |
| `scripts/claude-wrapper.sh` | Source in `.zshrc` | `cc` shell function for named sessions |
| `scripts/open-file-explorer.sh` | Direct | yazi in a Ghostty split |
| `scripts/detect-projects.js`, `~/.claude/scripts/update-active-projects.py` | Direct | Project discovery; regenerate active-projects.md |
| `scripts/bootstrap-claude-setup.js` | Direct | Generate a `~/.claude/` setup for a new machine |
| `claude-tracker-watch` | — | Dormant summarize daemon (Claude Code no longer writes the file it watches) |

All scripts use `~/.claude/lib/tracker-utils.js` for shared utilities (path decoding, session parsing, live-session detection, git remote detection) and `~/.claude/lib/tracker-db.js` for SQLite access (node:sqlite `DatabaseSync`, WAL mode, singleton lazy-open). No npm dependencies—the DB module uses Node's built-in `node:sqlite` (Node >= 22.13).

## Quick Start

```bash
# Search by topic
claude-tracker-search "kothar soul"

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
2. `claude-tracker-recent --since 1d` — today's sessions with titles, summaries, and cost
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

## Operations and Database

Load these only when the task needs them:

- **Indexing and maintenance** — how the transcript index stays current (hooks, hourly launchd, in-process refresh), byte-offset increments, the `Sanity:` line, rebuilds, summary backfill, the regression suite and self-audit: `references/operations.md`.
- **Workspace snapshots, `cc` wrapper, tab naming, yazi, project detection, bootstrap, performance**: `references/operations.md`.
- **`tracker.db` directly** — schema-level queries, title history, checkpoints, phase tracking, tagged phrases: `references/database.md`.

## Related Systems

- **Git Tracking** — PreToolUse/PostToolUse hooks intercept git commands, tag sessions with repos they touch. Query via `tracker-utils.js` functions (`getSessionsForRepo`, `getReposForSession`, `getRecentCommits`). See `references/data-schemas.md` for hook files and index format.
- **Speculator** — Daemon at `~/.claude/scripts/speculator/` maps Ghostty tabs to sessions every 5 minutes. `list-sessions.js` uses `loadSpeculatorData()` and `getSessionTTY()` for TTY badges. Health check: `bash ~/.claude/scripts/speculator/status.sh`
- **Soul Registry** — Live session tracking with heartbeats and Slack bindings at `~/.claude/soul-sessions/registry.json`. View: `python3 ~/.claude/hooks/soul-registry.py list --md`. Activate: `/ensoul`. Bind to Slack: `/slack-sync #channel`.
- **Session Report** — `/session-report` generates a Markdown dashboard combining session status with git activity.

## References

For detailed schemas and infrastructure:

- `references/operations.md` — Indexing pipeline and schedule, summary backfill, workspace stamp/restore, `cc` wrapper, yazi, project tools, bootstrap, performance
- `references/database.md` — `tracker.db` API module, direct queries, title history, checkpoints, phases, tagged phrases
- `references/data-schemas.md` — Session index, summary cache, JSONL transcript schemas, title_history schema; data source locations; shared library API
- `references/search-mechanics.md` — Transcript FTS indexing pipeline, search query resolution, synonym expansion, AND-to-OR fallback, former-title fallback, ranking algorithm
- `references/daemon-setup.md` — Watcher daemon lifecycle and launchd plist template
- `references/synonyms.json` — Bidirectional synonym groups for search query expansion (Porter stemming handles inflections; groups list distinct vocabulary)
