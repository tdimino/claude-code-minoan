# Example agent_docs

Starter templates for `~/.claude/agent_docs/`--the progressive disclosure layer that keeps your global `CLAUDE.md` small while giving Claude deep reference material on demand.

## How It Works

Files here are **not** auto-loaded. They become available through two mechanisms in your `CLAUDE.md`:

**Always Loaded** (inlined every session via `@`):
```markdown
@agent_docs/active-projects.md
@agent_docs/skills.md
```

**On-Demand** (read only when relevant):
```markdown
## On-Demand References
- `~/.claude/agent_docs/tools.md` -- Scraping, search, ML, image tools
- `~/.claude/agent_docs/mcp-servers.md` -- MCP server setup & config
```

## Files in This Example

| File | Load Pattern | Purpose |
|------|-------------|---------|
| `active-projects.md` | Always Loaded | Current projects, recent sessions, active plans |
| `skills.md` | Always Loaded | Skill inventory with descriptions |
| `tools.md` | On-Demand | Tool preferences, CLI references, API key locations |
| `mcp-servers.md` | On-Demand | MCP server documentation and troubleshooting |

## Setup

```bash
mkdir -p ~/.claude/agent_docs
cp docs/global-setup/agent_docs/*.md ~/.claude/agent_docs/
```

Then edit each file to match your actual setup. Add `@` references in your `CLAUDE.md` for the ones you want always loaded.

## Guidelines

- **One file per concern.** Don't combine ML setup with MCP configuration.
- **Keep Always Loaded files small.** Under 50 lines each. They cost tokens every session.
- **On-Demand files can be large.** They only load when relevant.
- **Maintain an INDEX.md.** Once you have more than 5 files, add an index so you can audit what exists.
- **Let frequency guide placement.** If you read an on-demand doc most sessions, promote it.

See `docs/guides/progressive-disclosure.md` for the full pattern and decision matrix.
