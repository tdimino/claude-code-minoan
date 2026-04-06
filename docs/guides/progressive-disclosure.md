# Progressive Disclosure with agent_docs

## The Problem

`~/.claude/CLAUDE.md` is loaded into every Claude Code session. A 2000-line CLAUDE.md wastes ~4000 tokens on information that's relevant 5% of the time. Context tokens are finite--every token spent on tool references you don't need today is a token unavailable for the actual work.

## The Solution

Keep `CLAUDE.md` small (~75-100 lines). Move detailed references into `~/.claude/agent_docs/` files. Use `@` references to control what loads automatically versus on demand.

### Always Loaded

Files referenced with `@agent_docs/file.md` in CLAUDE.md are inlined into every session:

```markdown
## Always Loaded
@agent_docs/active-projects.md
@agent_docs/skills.md
```

These should be small and high-frequency--information Claude needs in nearly every session.

### On-Demand References

Files listed (but not `@`-referenced) in CLAUDE.md are read only when Claude determines they're relevant:

```markdown
## On-Demand References
- `~/.claude/agent_docs/local-ml.md` -- Ollama, HuggingFace, MLX, llama.cpp
- `~/.claude/agent_docs/local-rag.md` -- rlama usage & RAG collections
- `~/.claude/agent_docs/mcp-servers.md` -- MCP server setup & config
```

Claude reads these when the conversation touches their domain. They can be large without wasting base context.

## Decision Matrix

| Used every session? | Small (<50 lines)? | Action |
|---------------------|---------------------|--------|
| Yes | Yes | Put in CLAUDE.md directly |
| Yes | No | Always Loaded `@reference` |
| No | Any | On-Demand reference (listed, not `@`'d) |

## Recommended agent_docs

### `tools.md` -- Tool preferences and CLI references
What scraping tool to use (Firecrawl for general, Jina for Twitter). What Python runner to prefer (uv). What image tools are available. API key locations. This changes rarely and applies to most sessions.

### `active-projects.md` -- Current projects and sessions
Which repos are active, recent sessions per project, current branches. Auto-updated by `scripts/update-active-projects.py`. Small enough to always load.

### `skills.md` -- Skill inventory
Table of all installed skills with one-line descriptions. Helps Claude discover capabilities without scanning the filesystem. Always load this.

### `local-ml.md` -- Local ML setup
Ollama models, HuggingFace cache location, llama.cpp paths, STT/TTS configuration. Only relevant when doing ML work. On-demand.

### `local-rag.md` -- RAG configuration
RLAMA collections, retrieve-only default, query patterns. On-demand.

### `mcp-servers.md` -- MCP server documentation
Which MCP servers are configured, how to troubleshoot them, setup procedures. On-demand.

## Directory Structure

```
~/.claude/
├── CLAUDE.md                    # ~75-100 lines, @references for Always Loaded
└── agent_docs/
    ├── INDEX.md                 # Master list of all agent docs
    ├── active-projects.md       # Always Loaded
    ├── skills.md                # Always Loaded
    ├── tools.md                 # Always Loaded
    ├── directories.md           # Always Loaded (from active-projects)
    ├── local-ml.md              # On-Demand
    ├── local-rag.md             # On-Demand
    ├── mcp-servers.md           # On-Demand
    ├── image-editing.md         # On-Demand
    └── references/              # Deep reference material
```

## The 6-Tier Memory Hierarchy

Progressive disclosure via agent_docs operates within Claude Code's broader memory system:

| Tier | Location | Scope | Shared |
|------|----------|-------|--------|
| Managed policy | OS-specific managed policy path | Organization | All org users |
| Project memory | `./CLAUDE.md` | Project | Team (via git) |
| Project rules | `.claude/rules/*.md` | Path-scoped | Team (via git) |
| User memory | `~/.claude/CLAUDE.md` | All projects | Personal |
| Project local | `./CLAUDE.local.md` | This project | Personal |
| Auto memory | `~/.claude/projects/<project>/memory/` | Per-project | Personal |

`agent_docs/` files are part of Tier 4 (User memory)--they extend `~/.claude/CLAUDE.md` through references. More specific tiers take precedence.

## Design Principles

1. **One file per concern.** Each agent_doc covers exactly one domain. Don't combine ML setup with MCP configuration.
2. **Titles are discovery.** The On-Demand list in CLAUDE.md acts as a table of contents. Clear titles (`local-ml.md -- Ollama, HuggingFace, MLX, llama.cpp`) help Claude decide when to read them.
3. **Maintain an INDEX.md.** Keep a master list in `agent_docs/INDEX.md` so you can audit what exists.
4. **Let frequency guide placement.** If you're reading an on-demand doc in most sessions, promote it to Always Loaded. If an Always Loaded doc is rarely relevant, demote it.

See `docs/global-setup/README.md` for the full `~/.claude/` directory reference.
