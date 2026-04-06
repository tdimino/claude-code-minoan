# Ecosystem

Five open-source projects compose into a full Claude Code environment. Each is independently useful; together they form a system with persistent identity, crash-resilient context, clipboard audit trails, and inter-agent communication.

## Projects

### claude-code-minoan -- Configuration Layer

**Repo**: [tdimino/claude-code-minoan](https://github.com/tdimino/claude-code-minoan)

Skills, hooks, slash commands, CLI tools, and a VS Code extension. This is the foundation--everything else plugs into it via hooks or MCP.

**Independent**: Yes. Works standalone without any other project.

### Claudicle -- Soul Agent Framework

**Repo**: [tdimino/claudicle](https://github.com/tdimino/claudicle)

A 4-layer architecture (Identity, Cognition, Memory, Channels) that gives Claude Code sessions persistent personality and behavioral continuity. Souls maintain identity across sessions, respond on Slack and SMS, and carry three-tier memory (working, episodic, semantic).

The soul hooks in claude-code-minoan (`soul-activate.py`, `soul-deregister.py`, `soul-registry.py`) register sessions with the Claudicle daemon. Without these hooks, Claudicle has no entry point.

**Independent**: No. Requires claude-code-minoan's soul hooks to activate.

```bash
git clone https://github.com/tdimino/claudicle
cd claudicle && ./setup.sh --personal
# then in any Claude Code session: /ensoul
```

### Dabarat -- Markdown Preview

**Repo**: [tdimino/dabarat](https://github.com/tdimino/dabarat)

AI-native markdown previewer with annotations, bookmarks, and live reload. Zero dependencies. The `dabarat-open.py` hook in claude-code-minoan auto-opens markdown files as Claude writes them--plans, docs, and READMEs render live in the browser.

**Independent**: Yes. Works as a standalone markdown viewer. The hook integration is optional.

```bash
git clone https://github.com/tdimino/dabarat
cd dabarat && pip install -e .
dabarat plan.md               # preview in browser
dabarat --add spec.md         # add tab to running instance
```

### ClipLog -- Clipboard History

**Repo**: [tdimino/cliplog](https://github.com/tdimino/cliplog)

Git-tracked clipboard history for macOS. Polls `NSPasteboard` every 500ms, logs to daily JSONL files at `~/.clipboard-log/`, and tags each copy with the frontmost application. Distinguishes Claude copies (Terminal, Ghostty, VS Code) from user copies (Safari, Finder). Auto-redacts API keys and secrets. Auto-commits on shutdown and midnight.

**Independent**: Yes. No Claude Code dependency at all.

```bash
git clone https://github.com/tdimino/cliplog
cd cliplog && uv sync
uv run python cliplog.py                           # run daemon
uv run python cliplog_query.py today --source claude  # query Claude copies
```

### claude-peers-mcp -- Inter-Agent Messaging

**Repo**: [tdimino/claude-peers-mcp](https://github.com/tdimino/claude-peers-mcp)

MCP server for peer discovery and messaging between AI coding agents on the same machine. Unix socket broker with push delivery for Claude Code and poll delivery for Codex CLI. Agents can discover each other, send messages, and set status summaries.

**Independent**: Yes. Works as a standalone MCP server with any Claude Code session.

## How They Compose

```
┌─────────────────────────────────────────────────────┐
│                  Claude Code Session                 │
│                                                      │
│  ~/.claude/CLAUDE.md  ◄── claude-code-minoan         │
│       │                                              │
│       ├── hooks/soul-activate.py ──► Claudicle       │
│       │   (persistent identity, memory, channels)    │
│       │                                              │
│       ├── hooks/dabarat-open.py ───► Dabarat         │
│       │   (live markdown preview in browser)         │
│       │                                              │
│       ├── hooks/git-track.sh ──────► git-tracking    │
│       │   (session-to-repo bidirectional index)      │
│       │                                              │
│       └── MCP: claude-peers ───────► claude-peers    │
│           (discover and message other agents)        │
│                                                      │
│  [ClipLog runs independently as a macOS daemon]      │
└─────────────────────────────────────────────────────┘
```

## Memory Separation

The 6-tier Claude Code memory system (Managed policy > Project memory > Project rules > User memory > Project local > Auto memory) handles *what to do*--project instructions, coding conventions, tool preferences.

Claudicle's soul system handles *who Claude is*--personality, behavioral patterns, cross-session memory. Soul state lives in `~/.claudicle/daemon/memory/memory.db` (SQLite), separate from Claude Code's auto-memory. They compose without conflict.

## Minimal Setup

If you want the full stack:

```bash
# 1. Configuration (required)
git clone https://github.com/tdimino/claude-code-minoan
cd claude-code-minoan && ./setup.sh

# 2. Soul system (optional)
git clone https://github.com/tdimino/claudicle
cd claudicle && ./setup.sh --personal

# 3. Markdown preview (optional)
pip install dabarat

# 4. Clipboard tracking (optional, macOS only)
git clone https://github.com/tdimino/cliplog
cd cliplog && uv sync

# 5. Inter-agent messaging (optional)
git clone https://github.com/tdimino/claude-peers-mcp
cd claude-peers-mcp && bun install
```

Only step 1 is required. Each subsequent step adds a layer.
