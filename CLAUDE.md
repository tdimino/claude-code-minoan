# Claude-Code-Minoan

Curated Claude Code configuration: skills, MCP servers, and slash commands.

## Structure

- `/skills` - Custom Claude Code skills (copy to `~/.claude/skills/`)
- `/commands` - Slash commands (copy to `~/.claude/commands/`)
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
