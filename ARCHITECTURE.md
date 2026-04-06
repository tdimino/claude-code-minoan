# Architecture

This document describes the layout of `claude-code-minoan` and the reasoning behind its structure. It follows [matklad's ARCHITECTURE.md guidelines](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html): it tells you where to look, not what the code does.

## Big Picture

`claude-code-minoan` is a curated configuration layer for Claude Code--the Anthropic CLI. Claude Code reads a fixed set of discovery paths at startup: `~/.claude/skills/*/SKILL.md`, `~/.claude/commands/*.md`, and `~/.claude/settings.json`. This repo is structured so that its contents install cleanly into those paths.

The repo does not extend Claude Code programmatically. It works entirely through Claude Code's documented extension points: skills loaded as context, slash commands invoked by the user, hooks wired to lifecycle events, and MCP servers registered in `settings.json`.

## Directory Layout

```
claude-code-minoan/
├── skills/                    # Skills, organized into category subdirs
│   ├── core-development/
│   ├── design-media/
│   ├── integration-automation/
│   ├── planning-productivity/
│   ├── research/
│   └── _archive/
├── hooks/                     # Lifecycle event scripts
├── commands/                  # Slash command markdown files
├── agents/                    # Custom subagent role definitions
├── bin/                       # CLI tools (cc, ccls, claude-tracker, etc.)
├── lib/                       # Shared JS libraries
├── scripts/                   # Utility and maintenance scripts
├── extensions/                # VS Code extension source + .vsix
├── docs/                      # Guides and references
├── ghostty/                   # Terminal emulator config
├── sounds/                    # Notification audio
├── CLAUDE.md                  # Repo-local config for working ON this repo
├── CLAUDE.template.md         # Starting point for users' global CLAUDE.md
├── setup.sh                   # Interactive installer
└── tmux.conf.example          # Optimized tmux config for Claude Code sessions
```

## Key Concepts

### Flat-Install Mapping

Skills in the repo are categorized for maintainability but install flat. The canonical path Claude Code discovers is `~/.claude/skills/{skill-name}/SKILL.md`. When installing:

```
skills/research/firecrawl/  →  ~/.claude/skills/firecrawl/
skills/core-development/react-best-practices/  →  ~/.claude/skills/react-best-practices/
```

Category subdirs (`core-development/`, `design-media/`, etc.) exist only in the repo. Once installed, the category is invisible to Claude Code. Do not rely on subdirectory structure in any hook, command, or skill that references another skill by path.

### Skill Anatomy

A skill is a directory with exactly one required file: `SKILL.md`. Claude Code injects the full content of `SKILL.md` into its system context when the skill is active.

```
firecrawl/
├── SKILL.md          # Entry point -- YAML frontmatter + instructional prose
├── scripts/          # Executable scripts called by instructions in SKILL.md
└── references/       # Additional markdown docs loaded on demand
```

`SKILL.md` frontmatter fields:
- `name`: skill identifier
- `description`: loaded by Claude Code to decide when to surface the skill

The `scripts/` directory contains the actual executables. The `SKILL.md` instructs Claude Code to call them. The `references/` directory contains docs that the instructions in `SKILL.md` tell Claude Code to read when needed--they are not auto-injected.

**Invariant**: skills must be self-contained. A skill must not import from or depend on another skill's scripts or references directory. Cross-skill orchestration belongs in commands or hooks.

### Hook Wiring

Hooks are scripts executed by Claude Code at lifecycle event boundaries. They are not discovered automatically--each hook must be registered in `~/.claude/settings.json` under the `hooks` key with an event name, command path, optional `tool_name` matcher, and `async` flag.

The repo ships the hook scripts; `settings.json` is not included (it contains user-specific paths and API keys). The setup guide in `docs/global-setup/` explains how to wire them.

Hooks communicate with Claude Code via stdout JSON:
- `{"continue": true}` -- allow the action
- `{"continue": false, "reason": "..."}` -- block with explanation
- `{"additionalContext": "..."}` -- inject context into the next turn (PostToolUse)

**Invariant**: every hook that parses JSON input must wrap `json.load` in `try/except`. Claude Code feeds hooks JSON on stdin; malformed input must not crash the hook process. A hook crash surfaces as an error in the Claude Code session.

### Triple-Handoff System

Three hooks coordinate to preserve session context across three failure modes:

| Event | Hook | Purpose |
|-------|------|---------|
| `PreCompact` | `precompact-handoff.py` | Context window is about to be compacted--write handoff before history is truncated |
| `SessionEnd` | `precompact-handoff.py` | Graceful session close--same handoff generation |
| `Stop` | `stop-handoff.py` | Claude Code stops between turns--throttled heartbeat with 3-min cooldown (10-min idle gate) |

All three write YAML to `~/.claude/handoffs/{session_id}.yaml`. On session resume, the most recent handoff is read and injected into the system prompt.

The handoff YAML is generated by calling an LLM via OpenRouter to summarize the session transcript. This happens outside the Claude Code model so it does not consume the user's context window.

### Config Layers

There are two `CLAUDE.md` files with distinct roles:

- **`CLAUDE.template.md`**: The starting point for a new user's global `~/.claude/CLAUDE.md`. Contains placeholders and commented-out sections. Users copy it, fill in their identity section, and point `@` references at their own `agent_docs/`. This file is never read by Claude Code when working on this repo.

- **`CLAUDE.md`** (repo-local): Read by Claude Code when the working directory is inside `claude-code-minoan/`. Contains instructions for contributors working on the repo itself--skill structure conventions, hook testing procedures, install path rules.

`settings.json` (user-local, not in repo) is the third layer. It binds hooks to lifecycle events, registers MCP servers, and lists enabled plugins. Its absence from the repo is intentional: it contains absolute paths and API configuration that cannot be shared.

### CLI Tools (`bin/`)

`bin/` contains tools for session management:

| Binary | Purpose |
|--------|---------|
| `cc` | Launch Claude Code with common flags |
| `ccls` | List active sessions |
| `ccpick` | Interactive session picker |
| `cckill` | Kill a session by ID |
| `ccnew` | Start a new session with common flags |
| `ccresume` | Resume a session by ID |
| `claude-tracker` | Full session browser (recent sessions, cost, model) |
| `claude-tracker-search` | Keyword search across session transcripts |
| `claude-tracker-resume` | Search then resume in one step |
| `claude-tmux-status` | Emit session info for tmux statusline |

All tools that read session data share `lib/tracker-utils.js`. This library parses Claude Code's `~/.claude/projects/` directory and reads `sessions-index.json` and JSONL transcript files. The library is copied to `~/.claude/lib/tracker-utils.js` at install time and required via absolute path by the bin tools.

## Data Flow

```
User types in Claude Code
        │
        ▼
UserPromptSubmit hooks run
        │
        ▼
Claude Code reasons and calls tools
        │
        ├── PreToolUse hooks (git-track.sh, block-websearch.sh)
        ├── PermissionRequest hooks (smart-auto-approve.py)
        │
        ├── Tool executes
        │
        └── PostToolUse hooks (lint-on-write.py → additionalContext, git-track-post.sh)
                │
                ▼
        Agent self-corrects from additionalContext if lint violations found

Session ends or compacts
        │
        ├── PreCompact / SessionEnd → precompact-handoff.py → ~/.claude/handoffs/{id}.yaml
        │
        └── Stop → stop-handoff.py (throttled), session-tags-infer.py (async)

Session resumes
        │
        └── SessionStart (resume) → injects handoff YAML into prompt
```

## Invariants

1. **No API keys in the repo.** All secrets use placeholder comments. The setup guide directs users to their shell environment.

2. **Skills are self-contained.** A skill directory must work in isolation after flat installation. No script in `skills/A/scripts/` may import from `skills/B/scripts/`.

3. **Hooks fail gracefully.** Every hook that parses stdin must handle malformed JSON without exiting nonzero in a way that blocks the user action. Log to stderr, return `{"continue": true}` when in doubt.

4. **Async hooks for slow work.** Hooks that call external APIs (session tag inference, handoff generation) run with `async: true` so they do not block the Claude Code session.

5. **Commands are markdown.** Slash commands in `commands/` are plain markdown files. They contain instructions Claude Code follows when the command is invoked. They do not execute shell code directly--if they need to run something, they instruct Claude Code to use the Bash tool.

6. **Flat install is authoritative.** The category subdirectory inside the repo is a source-of-truth organizational artifact. The installed flat path is what Claude Code and all users interact with. Any documentation, hook, or command that references a skill uses the flat name (`firecrawl`, not `research/firecrawl`).

## Where to Start

- Understanding what a skill does: read `skills/{category}/{name}/SKILL.md`
- Understanding how hooks run: read `hooks/INDEX.md` for the full event map
- Understanding session handoff: read `hooks/precompact-handoff.py` and `hooks/stop-handoff.py`
- Understanding the install: run `setup.sh --help` or read `docs/global-setup/README.md`
- Adding a new skill: copy an existing skill directory, update `SKILL.md` frontmatter, place executables in `scripts/`
- Wiring a new hook: add the script to `hooks/`, document it in `hooks/INDEX.md`, register it in your local `settings.json`
