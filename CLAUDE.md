# Claude-Code-Minoan

Curated Claude Code configuration: skills, MCP servers, slash commands, CLI tools, and VS Code extensions.

## Structure

- `/skills` - Custom skills organized by category (copy to `~/.claude/skills/`)
- `/commands` - Slash commands (copy to `~/.claude/commands/`)
- `/bin` - CLI tools: `cc`, `ccls`, `ccpick`, `cckill`, `claude-tracker`, `claude-tracker-search`, `claude-tracker-resume`
- `/lib` - Shared libraries (`tracker-utils.js`)
- `/extensions` - VS Code extensions (`claude-session-tracker`)
- `/hooks` - Terminal title, session handoff, automation scripts
- `/sounds` - Notification audio
- `.mcp.json` - MCP server configurations
- `tmux.conf.example` - Optimized tmux config for Claude Code

## Setup

```bash
cp -r skills/* ~/.claude/skills/
cp -r commands/* ~/.claude/commands/
cp bin/* ~/.local/bin/
mkdir -p ~/.claude/lib && cp lib/* ~/.claude/lib/
```

## Key Skills

- **minoan-swarm** - Agent Teams orchestration with Minoan-Semitic naming. 5 team templates, 30+ named teammates, auto-discovers project context. Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- **osgrep-reference** - Semantic code search. ALWAYS prefer `osgrep` over grep/rg
- **claude-agent-sdk** - Build AI agents with Claude Agent SDK
- **codex-orchestrator** - Delegate to specialized Codex CLI subagents (reviewer, debugger, architect, security)
- **super-ralph-wiggum** - Autonomous iteration loops (HITL/AFK modes)
- **llama-cpp** / **rlama** / **parakeet** / **smolvlm** / **speak-response** - Local ML stack (inference, RAG, STT, vision, TTS)
  - **RLAMA default**: Always use retrieve-only mode (`rlama_retrieve.py`)—Claude synthesizes from raw chunks. Never route through Qwen when Claude is in the loop. `rlama run` is fallback only.
- **Firecrawl** / **exa-search** - Web scraping and search
- **claude-md-manager** - Create and optimize CLAUDE.md files

## Key Commands

- `/workflows:review` - Multi-agent code review (12+ parallel agents)
- `/workflows:work` - Execute plans with quality checks
- `/workflows:plan` - Feature planning with architecture analysis
- `/requirements-start` - Extensive project planning workflow
- `/audit-plans` - Audit plans for completeness

## OSGrep Quick Reference

```bash
osgrep "query"              # Semantic search (25 results)
osgrep trace "function"     # Call graph
osgrep skeleton <file>      # Compressed structure (~85% token reduction)
osgrep index --reset        # Full re-index if stale
```

## VS Code Extension

**Claude Session Tracker** — Track and resume sessions across VS Code windows and crashes.

```bash
cd extensions/claude-session-tracker
npm run compile && npx vsce package
code --install-extension claude-session-tracker-*.vsix
```

`Cmd+Shift+C` to quick-resume last session.

## tmux + Claude

```bash
cp bin/cc bin/ccls bin/ccpick bin/cckill bin/claude-tmux-status ~/.local/bin/
```

| Command | Description |
|---------|-------------|
| `cc [name]` | Create/attach tmux session with Claude |
| `ccls` | List sessions with Claude status |
| `ccpick` | fzf picker with tmux + Claude history |
| `cckill` | Kill idle sessions (preserves running Claude) |

Prefix: `Ctrl+A`. See `docs/tmux-claude-workflow.md` for keybindings.

## MCP Servers

Core: playwright, chrome-devtools, figma, shadcn, supabase, context7, arxiv, perplexity

## Guides

- `docs/tmux-claude-workflow.md` - tmux session management
- `CONTRIBUTING.md` - Contribution guidelines
- `README.md` - Full setup, all skills, all commands
