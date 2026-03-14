# Claude Tracker Suite

The session management skill. Search, resume, spawn, and monitor Claude Code sessions across projects---with crash recovery, git-aware tracking, weighted search ranking, and a bootstrap script for new machine setup.

**Last updated:** 2026-03-10

**Reflects:** Claude Code session internals (`sessions-index.json`, JSONL transcripts), git tracking hooks, and macOS process detection patterns.

---

## Why This Skill Exists

Claude Code sessions accumulate fast. After a week of active development, you might have 50+ sessions across 10 projects, some crashed mid-task, some with critical context that wasn't committed. Finding the right session to resume---by topic, by project, by what you were working on---requires searching across summaries, first prompts, branches, and project paths. And recovering from a crash means finding the session, checking if it's actually dead, and resuming in the right directory.

This skill provides 6 scripts that handle session lifecycle: search with weighted ranking, crash recovery with alive detection, headless spawning for automation, project discovery, and a bootstrap generator for setting up a new machine.

---

## Structure

```
claude-tracker-suite/
  SKILL.md                                 # CLI reference and workflows
  README.md                                # This file
  references/
    daemon-setup.md                        # Watcher daemon lifecycle and launchd plist
    data-schemas.md                        # Session index, summary cache, JSONL schemas
  scripts/
    search-sessions.js                     # Keyword search across all sessions
    list-sessions.js                       # List recent sessions with status badges
    bootstrap-claude-setup.js              # Generate complete ~/.claude/ structure
    detect-projects.js                     # Project discovery and CLAUDE.md scaffolding
    new-session.sh                         # Start new interactive/prompt-driven/headless session
    resume-in-vscode.sh                    # Open session in new terminal (macOS AppleScript)
```

---

## What It Covers

### Search

`search-sessions.js` searches across all sessions with weighted ranking:

| Field | Weight | Why |
|-------|--------|-----|
| Summary | 3x | Most descriptive of what happened |
| First prompt | 2x | Captures user intent |
| Project path | 1x | Directory context |
| Branch name | 1x | Feature context |

Results show session ID, project, branch, date, model, and summary. Filter by project path or date range.

### Session Status

| Badge | Meaning |
|-------|---------|
| ACTIVE | Process running, recent heartbeat |
| STALE | Process exists but no recent activity |
| OLD | Older than 24 hours |
| CRASHED | Process not found, no clean exit |

Alive detection uses `ps` to check for the Claude Code process by session ID.

### Crash Recovery

```
1. search-sessions.js finds candidate sessions
2. list-sessions.js shows status badges
3. If CRASHED: resume with `claude --resume <session-id>`
4. resume-in-vscode.sh opens in a new terminal (macOS AppleScript)
```

### Spawning

`new-session.sh` supports three modes:

| Mode | Command | Use Case |
|------|---------|----------|
| Interactive | `new-session.sh` | Normal development |
| Prompt-driven | `new-session.sh -p "Fix the auth bug"` | Directed task |
| Headless | `new-session.sh -p "Run tests" --headless` | Automation, CI |

Prompt-driven and headless modes use `claude -p` (Agent SDK CLI).

### Bootstrap

`bootstrap-claude-setup.js` generates a complete `~/.claude/` directory structure for a new machine: CLAUDE.md template, agent_docs/, skills/, hooks/, plans/, and handoffs/ directories with starter files.

### Daemon

An optional watcher daemon auto-summarizes new sessions via Claude Haiku. See `references/daemon-setup.md` for launchd plist configuration.

---

## Scripts

| Script | Usage |
|--------|-------|
| `search-sessions.js` | `node search-sessions.js "auth bug" [--project ~/myapp]` |
| `list-sessions.js` | `node list-sessions.js [--limit 20]` |
| `bootstrap-claude-setup.js` | `node bootstrap-claude-setup.js` |
| `detect-projects.js` | `node detect-projects.js [~/code]` |
| `new-session.sh` | `bash new-session.sh [-p "prompt"] [--headless]` |
| `resume-in-vscode.sh` | `bash resume-in-vscode.sh <session-id>` |

---

## Requirements

- Node.js 18+
- Claude Code CLI installed
- macOS (for AppleScript-based terminal launch in `resume-in-vscode.sh`)
- No external npm dependencies (uses built-in `fs`, `path`, `child_process`)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/planning-productivity/claude-tracker-suite ~/.claude/skills/
```
