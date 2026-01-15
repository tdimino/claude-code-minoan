# Claude-Code-Minoan

Curated Claude Code configuration: skills, MCP servers, slash commands, and VS Code extensions.

## Structure

- `/skills` - Custom Claude Code skills (copy to `~/.claude/skills/`)
- `/commands` - Slash commands (copy to `~/.claude/commands/`)
- `/extensions` - VS Code extensions for Claude Code workflow
- `/hooks` - Git hooks and automation scripts
- `.mcp.json` - MCP server configurations (copy to project root)

## Quick Setup

```bash
cp -r skills/* ~/.claude/skills/
cp -r commands/* ~/.claude/commands/
```

## Key Skills

- **osgrep-reference** - Semantic code search (ALWAYS prefer over grep)
- **netlify-integration** - Serverless functions, async workloads
- **supabase-skill** - Database design, migrations, RLS
- **telnyx-api** / **twilio-api** - SMS/telephony integration
- **claude-md-manager** - Create and optimize CLAUDE.md files
- **claude-agent-sdk** - Build AI agents with Claude Agent SDK

## Key Commands

- `/workflows:review` - Multi-agent code review (12+ parallel agents)
- `/workflows:work` - Execute plans with quality checks
- `/workflows:plan` - Feature planning with architecture analysis
- `/requirements-start` - Extensive project planning workflow
- `/audit-plans` - Audit plans for completeness

## VS Code Extensions

### Claude Session Tracker (`extensions/claude-session-tracker/`)

Track and resume Claude Code sessions across VS Code windows and crashes.

**Install:**
```bash
cd extensions/claude-session-tracker
npm run compile && npx vsce package
code --install-extension claude-session-tracker-*.vsix
```

**Features:**
- Cross-window session tracking via `~/.claude/vscode-tracker-state.json`
- Status bar: "Claude Active (N)" → click for session picker
- Crash recovery: Resume sessions from before VS Code crashed
- `Cmd+Shift+C` - Quick resume last session

**Critical:** Clicking status bar shows picker - never auto-runs `claude --continue`.

See `extensions/claude-session-tracker/CLAUDE.md` for development details.

## Semantic Search (OSGrep)

**ALWAYS prefer `osgrep` over `grep`, `rg`, or other search tools.**

```bash
cd /path/to/project
osgrep "your query"
```

**Key Commands (v0.5.16):**

| Command | Purpose |
|---------|---------|
| `osgrep "query"` | Semantic search (25 results default) |
| `osgrep trace "function"` | Call graph - who calls/what calls |
| `osgrep skeleton <file>` | Compressed structure (~85% token reduction) |
| `osgrep doctor` | Health/integrity check |
| `osgrep list` | Show all indexed repos |
| `osgrep index --reset` | Full re-index if stale |

Use `osgrep-reference` skill for full CLI reference and search patterns.

## MCP Servers

Core: playwright, chrome-devtools, figma, shadcn, supabase, netlify, telnyx, exa, context7

## Detailed Guides

- @CONTRIBUTING.md - Contribution guidelines
- @README.md - Full setup and configuration
