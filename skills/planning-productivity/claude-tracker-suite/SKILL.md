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
| `claude-tracker-search` | Search sessions by keyword or ID prefix (standalone script) |
| `claude-tracker-pick` | Interactive fzf picker: fuzzy-find recent sessions, preview, Enter resumes in Ghostty |
| `index-transcripts.js` | Build/refresh the transcript full-text index (FTS5 over user+assistant text) and extract title history events |
| `backfill-summaries.js` | Generate missing session summaries (claude CLI or OpenRouter; disabled by default, `--enable` to run) |
| `audit-suite.js` | Self-audit: inventory, portability, daemons, DB coverage, search recall → AUDIT.md |
| `search-regression.js` | Recall regression fixtures for the search stack (exit 1 on regression) |
| `open-sessions.js` | List top N sessions, open selected in cmux tabs/splits |
| `claude-tracker-resume` | Find and resume crashed/inactive sessions |
| `claude-tracker-alive` | Check which sessions have running processes |
| `claude-tracker-watch` | Daemon: auto-summarize new sessions, update active-projects.md |
| `claude-tracker` | List recent sessions with status badges (standalone script) |
| `new-session.sh` | Start a new session in Ghostty/VSCode/Cursor, with optional prompt or headless mode |
| `resume-session.sh` | Open a session in a cmux tab (optionally open project in VS Code/Cursor) |
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
| `session-notify.sh` | macOS notifications for session events + Ghostty tab badges |
| `open-file-explorer.sh` | Open yazi file explorer in a Ghostty split pane |

## Standalone Scripts

Commands delegate to standalone Node.js scripts (avoids shell escaping issues with inline `node -e`):

| Script | Called By | Purpose |
|--------|-----------|---------|
| `scripts/search-sessions.js` | `/claude-tracker-search` | Keyword search or `--id` prefix lookup across all sessions |
| `scripts/open-sessions.js` | Direct invocation | List top N sessions, open in cmux tabs/splits with confirmation |
| `scripts/list-sessions.js` | `/claude-tracker` | List recent sessions with status badges |
| `scripts/new-session.sh` | `/spawn` | Start new interactive or prompt-driven session in Ghostty/VSCode/Cursor or headless |
| `scripts/resume-session.sh` | Direct invocation | Open session in cmux tab, optionally open project in VS Code/Cursor |
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
| `scripts/index-transcripts.js` | Direct / after heavy sessions | Incremental transcript FTS indexer (EXTRACTOR_VERSION 4; prunes deleted; extracts title history events) |
| `scripts/backfill-summaries.js` | Direct invocation | Hermetic summary backfill, claude or OpenRouter provider (disabled by default) |
| `scripts/audit-suite.js` | Direct invocation | Suite self-audit → AUDIT.md |
| `scripts/search-regression.js` | After search changes | Recall fixtures incl. expected-fail semantic-gap marker |
| `scripts/session-notify.sh` | Direct / hooks | macOS notifications + Ghostty tab badges for session events |
| `scripts/open-file-explorer.sh` | Direct invocation | Open yazi in a Ghostty split pane |
| `~/.claude/scripts/ghostty-resume.sh` | Direct invocation | Open session in a new Ghostty tab |

All scripts use `~/.claude/lib/tracker-utils.js` for shared utilities (path decoding, session parsing, git remote detection) and `~/.claude/lib/tracker-db.js` for SQLite access (better-sqlite3, WAL mode).

## Quick Start

```bash
# Search by topic
claude-tracker-search "kothar mac mini"

# Lookup by session ID prefix (exact directory from JSONL ground truth)
node ~/.claude/skills/claude-tracker-suite/scripts/search-sessions.js --id d7b8f4dd

# Search by session name/slug only (fast — no JSONL body scan)
claude-tracker-search "thera" --name

# List top 10 sessions, open selected in cmux tabs
node ~/.claude/skills/claude-tracker-suite/scripts/open-sessions.js

# Open top 5 as vertical splits
node ~/.claude/skills/claude-tracker-suite/scripts/open-sessions.js --limit 5 --split right

# Check what's alive
claude-tracker-alive

# Resume crashed sessions in tmux
claude-tracker-resume --tmux

# Start auto-summarize daemon
claude-tracker-watch --daemon
```

## Search

```bash
claude-tracker-search "$ARGUMENTS"
```

**How search works**: the default path queries the **transcript full-text index** (FTS5 over all user+assistant conversation text, built by `index-transcripts.js`), merged with metadata FTS over titles/slug/summary/first-prompt (bm25 column weights: custom_title 3x, auto_title 2x, summary 2x, first_prompt 1.5x, slug 1x). Multi-word queries match per-term at the *session* level (terms may appear in different messages), expand through synonym groups in `references/synonyms.json`, and fall back from AND to OR with a labeled partial-match notice. Ranking: IDF-weighted saturated match-density with a short-session damp. Results include highlighted snippet excerpts.

**Former-title fallback**: default search also checks `title_history` for sessions whose past titles match the query but whose current title does not. A session renamed away from a name the user remembers still surfaces under a "former-title matches" heading, capped to avoid crowding body results. Each former-title hit prints its old name, provenance, date, and a link to the full timeline via the `titles` subcommand.

| Flag / Subcommand | Description |
|------|-------------|
| `--limit <n>` | Max results (default: 15) |
| `--id <prefix>` | Lookup by session ID prefix (8+ chars) |
| `--name` | Titles/slugs/summaries only via metadata FTS (fastest) |
| `--deep` | Bypass the index: streaming raw JSONL scan (new/unindexed sessions; whole-phrase matching) |
| `--open` | Resume the top hit in a new Ghostty tab immediately |
| `titles <id-prefix>` | Print the chronological title/nickname timeline for a session (all rename, slug, cache, and summarizer events) |

## Transcript Index & Summary Backfill

```bash
# Incremental index refresh (skips unchanged files; run after heavy sessions)
node ~/.claude/skills/claude-tracker-suite/scripts/index-transcripts.js

# Full rebuild (also forced automatically when EXTRACTOR_VERSION bumps)
node ~/.claude/skills/claude-tracker-suite/scripts/index-transcripts.js --rebuild

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

Incremental indexing skips files whose size, mtime, and extractor version (currently EXTRACTOR_VERSION 4) all match `transcript_index_state`. Bumping the version constant forces a full reindex under new extraction rules. Read errors are never recorded as indexed—the session stays eligible for the next run, preventing a partial read from permanently masking content from search. Deleted transcripts are pruned on full (unlimited) runs.

Since v4, the indexer also extracts **title history events** from each transcript: `/rename` custom-title lines (source `user`), slug changes (source `slug`). Custom-title lines route by the line's own `sessionId` field, not the containing file—a `/rename` after `/resume` writes into the active transcript but targets the previous session. Claude Code's own metadata scanner gets this wrong, overwriting the active session's title with the rename target's title. Consecutive duplicate title values within a file collapse to a single event.

Known lexical limit: a session can only be found by words that actually occur in it—the `[expected fail]` regression fixture documents this; a semantic (rlama) layer is the designated future fix.

## Interactive Picker (restart recovery)

```bash
~/.claude/skills/claude-tracker-suite/scripts/claude-tracker-pick              # fuzzy-find recent 50
~/.claude/skills/claude-tracker-suite/scripts/claude-tracker-pick --here      # resume in current terminal
~/.claude/skills/claude-tracker-suite/scripts/claude-tracker-pick --project thera --limit 100
```

Enter opens the session in a Ghostty tab, Ctrl-O resumes in the current terminal, Ctrl-Y copies the resume command. Preview shows title, summary, and first prompt. Pair with `restore-workspace.sh` (bulk restore from the launchd snapshot) — the picker is for choosing, restore is for "give me back everything".

## Resume Crashed Sessions

```bash
claude-tracker-resume                    # List crashed sessions with resume commands
claude-tracker-resume --tmux             # Resume all in tmux windows
claude-tracker-resume --zsh              # Resume all in Terminal.app tabs (macOS)
claude-tracker-resume --all              # Include non-VS Code sessions
claude-tracker-resume --dry-run          # Preview without acting
```

Smart fallback: if `--resume` fails on an expired session, automatically starts a fresh session in that project directory. Sessions older than 7 days show a STALE badge.

## Alive Detection

Check which sessions have running Claude processes:

```bash
claude-tracker-alive                     # Running + stale sessions overview
claude-tracker-alive --running           # Only sessions with active processes
claude-tracker-alive --stale             # Only sessions with no process
claude-tracker-alive --json              # Machine-readable output
```

Cross-references running `claude` PIDs (via `pgrep` + `lsof`) against recent session files. Sessions >3 days without a process show an OLD badge.

## Auto-Summarize Daemon

Watch for new sessions and auto-populate summary cache:

```bash
claude-tracker-watch --status            # Check if daemon is running
claude-tracker-watch --daemon            # Start in background
claude-tracker-watch --stop              # Stop running daemon
claude-tracker-watch --verbose           # Foreground with debug output
```

The daemon watches `~/.claude/projects/*/sessions-index.json` for changes. When new sessions appear, it caches summaries from Claude Code metadata and regenerates `active-projects.md`. See `references/daemon-setup.md` for launchd plist and lifecycle details.

## Recent Sessions (Full Metadata)

```bash
claude-tracker-recent                          # Last 10 sessions with full metadata
claude-tracker-recent --limit 20               # Last 20 sessions
claude-tracker-recent --json                   # Machine-readable JSON output
claude-tracker-recent --project myapp          # Filter by project
claude-tracker-recent --model opus             # Filter by model
claude-tracker-recent --since 7d               # Last 7 days only
```

Shows per session: title (custom or auto), summary, all tags (color-coded by type), project name, age, model, cost, turn count, git branch, session ID, and resume command. First result's resume command is auto-copied to clipboard.

## Session Listing

```bash
claude-tracker                           # All recent sessions
claude-tracker vscode                    # VS Code sessions only
```

When speculator is running, the session listing includes:
- **Header**: Ghostty tab count and window count alongside running/inactive/VS Code counts
- **TTY badges**: Purple `s000`–`s010` badge per session showing which Ghostty tab it occupies

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

## Resume in New Terminal

Open a session in a new cmux tab, optionally opening the project in an editor:

```bash
# Resume in cmux tab (default — auto-detects project directory)
~/.claude/skills/claude-tracker-suite/scripts/resume-session.sh <session-id>

# Resume in cmux + open project in VS Code
~/.claude/skills/claude-tracker-suite/scripts/resume-session.sh <session-id> --vscode

# Resume in cmux + open project in Cursor
~/.claude/skills/claude-tracker-suite/scripts/resume-session.sh <session-id> --cursor

# Explicit project directory
~/.claude/skills/claude-tracker-suite/scripts/resume-session.sh <session-id> --project ~/Desktop/Programming
```

cmux owns the terminal lifecycle. Editor flags (`--vscode`, `--cursor`) only open the project in the editor — the session always resumes in cmux. Falls back to printing the resume command if cmux is not running.

## Resume in Ghostty Tab

Open a session in a new Ghostty tab (auto-detects project directory from SQLite or JSONL):

```bash
~/.claude/scripts/ghostty-resume.sh <session-id>
~/.claude/scripts/ghostty-resume.sh <session-id> --project ~/my-project
```

Uses the AppleScript clipboard-paste pattern for reliable command delivery. Launches Ghostty if not running. Search and recent-sessions output includes a `Ghostty:` line per result with the ready-to-run command.

## New Session / Spawn

Start a new Claude Code session in a terminal tab or headless:

```bash
# Interactive session in Ghostty (default)
~/.claude/skills/claude-tracker-suite/scripts/new-session.sh ~/my-project

# With a specific model
~/.claude/skills/claude-tracker-suite/scripts/new-session.sh ~/my-project --model opus

# Prompt-driven session in Ghostty tab
~/.claude/skills/claude-tracker-suite/scripts/new-session.sh ~/my-project --prompt "fix the login bug"

# Prompt-driven in VS Code terminal
~/.claude/skills/claude-tracker-suite/scripts/new-session.sh ~/my-project --vscode --prompt "fix the login bug"

# Headless — runs in current terminal, returns JSON
~/.claude/skills/claude-tracker-suite/scripts/new-session.sh ~/my-project --headless --prompt "summarize the README"

# Headless with specific model and output format
~/.claude/skills/claude-tracker-suite/scripts/new-session.sh ~/my-project --headless --prompt "fix tests" --model haiku --output-format text
```

Headless and prompt-driven modes use `claude -p` (the Agent SDK CLI). Note: `-p` is now officially part of the Claude Agent SDK—it uses SDK billing, not interactive session billing. Terminal modes use the clipboard-paste AppleScript pattern for reliable command delivery (handles special characters in prompts).

## Workflow: Find and Resume

1. `claude-tracker-search "topic"` — find matching sessions
2. `claude-tracker-recent` — browse last 10 sessions with full metadata
3. `claude --resume <session-id>` — resume in current terminal
4. `~/.claude/scripts/ghostty-resume.sh <session-id>` — resume in a new Ghostty tab
5. `open-sessions.js` — list top sessions, open selected in cmux tabs
6. Or `claude-tracker-resume --tmux` — auto-resume all crashed sessions

## Workflow: Open Sessions in cmux

List recent sessions and open them in cmux tabs or splits:

```bash
# List top 10, prompt for selection
node ~/.claude/skills/claude-tracker-suite/scripts/open-sessions.js

# Open as vertical splits
node ~/.claude/skills/claude-tracker-suite/scripts/open-sessions.js --split right

# Open all without confirmation
node ~/.claude/skills/claude-tracker-suite/scripts/open-sessions.js --yes

# JSON output for scripting
node ~/.claude/skills/claude-tracker-suite/scripts/open-sessions.js --json
```

Session directories are resolved from JSONL ground truth (`decodeProjectPath`), not from `active-projects.md`. Falls back to printing resume commands when cmux is unavailable.

For the full cmux CLI reference, see `references/cmux-commands.md`.

## Workflow: Monitor Active Work

1. `claude-tracker-alive` — see what's running vs stale
2. `claude-tracker-watch --daemon` — keep summaries auto-updated
3. Read `~/.claude/agent_docs/active-projects.md` — curated project overview

## SQLite Database (`tracker.db`)

Single SQLite database at `~/.claude/tracker.db` consolidates all session metadata, git tracking, tags, and three new capabilities: checkpoints, phase tracking, and tagged phrases.

**API module**: `~/.claude/lib/tracker-db.js` — synchronous better-sqlite3, WAL mode, singleton lazy-open.

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

Phases: `exploring`, `planning`, `implementing`, `testing`, `reviewing`, `debugging`, `committing`, `deploying`.

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

`new-session.sh`, `resume-session.sh`, and `ghostty-resume.sh` all accept `--name` to set the Ghostty tab title on launch. When no name is given, the default format is `{project-basename}—{session-id-prefix}`.

```bash
# Named new session
~/.claude/skills/claude-tracker-suite/scripts/new-session.sh ~/my-project --name "auth-rewrite"

# Named resume
~/.claude/scripts/ghostty-resume.sh abc12345 --project ~/my-project --name "auth-rewrite"
```

Tab titles use VT escape sequences (`\e]1;Title\a`) which persist while `claude` is interactive—no shell prompt resets them.

## Workspace Save/Restore

Snapshot running Claude sessions and restore them after a Ghostty restart.

### Save

```bash
# Snapshot current sessions
node ~/.claude/skills/claude-tracker-suite/scripts/save-workspace.js

# Preview without writing
node ~/.claude/skills/claude-tracker-suite/scripts/save-workspace.js --dry-run
```

Detects alive sessions via `pgrep`/`lsof` (same logic as `claude-tracker-alive`), matches them to tracker DB entries, and writes `~/.claude/workspace-state.json` with session IDs, project directories, and tab titles. Deduplicates by sessionId (multiple PIDs from forks and MCP children resolve to one entry). Never overwrites a good snapshot with an empty one—after a crash or logout with zero live sessions, the previous snapshot is preserved for `restore-workspace.sh`.

### Restore

```bash
# Restore all saved sessions into Ghostty tabs
~/.claude/skills/claude-tracker-suite/scripts/restore-workspace.sh

# Preview what would be restored
~/.claude/skills/claude-tracker-suite/scripts/restore-workspace.sh --dry-run

# Restore at most 3 sessions
~/.claude/skills/claude-tracker-suite/scripts/restore-workspace.sh --limit 3
```

Opens each session in a new Ghostty tab via `ghostty-resume.sh` with saved tab titles. 2-second stagger between tab openings.

### Automatic Snapshots (launchd)

A launchd plist at `scripts/com.claude.workspace-snapshot.plist` runs `save-workspace.js` every 300 seconds. Install:

```bash
cp ~/.claude/skills/claude-tracker-suite/scripts/com.claude.workspace-snapshot.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.claude.workspace-snapshot.plist
```

## Session Notifications

macOS notifications when Claude sessions need attention, with Ghostty tab title badges.

```bash
# Custom notification
~/.claude/skills/claude-tracker-suite/scripts/session-notify.sh --title "Done" --message "Build complete"

# Preset: session completed
~/.claude/skills/claude-tracker-suite/scripts/session-notify.sh --session-done --project "my-app"

# Preset: needs user input
~/.claude/skills/claude-tracker-suite/scripts/session-notify.sh --needs-input --project "my-app"

# Tab badge only (no notification)
~/.claude/skills/claude-tracker-suite/scripts/session-notify.sh --tab-badge "✓" --tab-title "my-app"

# Silent notification (no sound)
~/.claude/skills/claude-tracker-suite/scripts/session-notify.sh --needs-input --no-sound
```

A Stop hook at `~/.claude/hooks/session-notify-hook.sh` automatically sends a "needs input" notification whenever Claude stops. Registered in `settings.json` as async.

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
- `references/cmux-commands.md` — Complete cmux CLI reference: hierarchy, splits, tabs, input, browser, sidebar, notifications, keyboard shortcuts
