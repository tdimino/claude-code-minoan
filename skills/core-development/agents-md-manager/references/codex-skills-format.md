# Codex Skills Format

## Overview

Codex skills are reusable instruction packages that extend agent capabilities. They follow a different format from Claude skills (`.claude/skills/`) and are designed for the Codex CLI ecosystem.

## Locations

| Scope | Path | Notes |
|-------|------|-------|
| Project | `.agents/skills/<name>/` | Checked into the repo |
| User | `~/.agents/skills/<name>/` | Personal skills across projects |
| Admin | `/etc/codex/skills/<name>/` | System-wide, managed by admins |

## Directory Structure

```
my-skill/
├── SKILL.md              # Required: name + description in YAML frontmatter
├── agents/
│   └── openai.yaml       # Optional: UI metadata, policy, dependencies
├── scripts/              # Optional: executable code the skill can invoke
├── references/           # Optional: documentation loaded on demand
└── assets/               # Optional: templates, icons, static resources
```

## SKILL.md (Required)

The only required file. Must have YAML frontmatter with two fields:

```markdown
---
name: my-skill
description: >-
  One-paragraph description of what this skill does and when to use it.
---

# My Skill

Instructions for the agent when this skill is active.
```

**Required frontmatter fields:**
- `name` (string): Skill identifier, should match directory name
- `description` (string): When-to-use guidance for the agent

That's it. No other frontmatter fields are required or recognized by Codex.

## agents/openai.yaml (Optional)

Provides UI metadata, invocation policy, and tool dependencies for Codex-specific features.

```yaml
interface:
  display_name: "User-Facing Skill Name"
  short_description: "Brief one-line description"
  icon_small: "./assets/icon-small.svg"     # 24x24 recommended
  icon_large: "./assets/icon-large.png"     # 128x128 recommended
  brand_color: "#3B82F6"                    # Hex color for UI accents
  default_prompt: "Default surrounding prompt text"

policy:
  allow_implicit_invocation: false  # Default: true. If false, must be explicitly invoked.

dependencies:
  tools:
    - type: "mcp"
      value: "serverName"
      description: "What this MCP server provides"
      transport: "streamable_http"
      url: "https://example.com/mcp"
    - type: "mcp"
      value: "localTool"
      description: "Local MCP server"
      transport: "stdio"
      command: "npx"
      args: ["-y", "@example/mcp-server"]
```

### Interface Fields

| Field | Description |
|-------|-------------|
| `display_name` | Name shown in UI (can differ from `name` in SKILL.md) |
| `short_description` | One-line summary for skill browser |
| `icon_small` | Path to small icon (relative to skill root) |
| `icon_large` | Path to large icon (relative to skill root) |
| `brand_color` | Hex color for UI elements |
| `default_prompt` | Prompt text injected when skill is active |

### Policy Fields

| Field | Default | Description |
|-------|---------|-------------|
| `allow_implicit_invocation` | `true` | Whether the agent can activate this skill based on context |

### Dependency Fields

Declares MCP servers the skill requires. Codex will ensure these are available before activating the skill.

## Invocation

- **Explicit**: Type `$skill-name` in the prompt (e.g., `$my-skill do something`)
- **Implicit**: Agent activates the skill automatically based on the `description` field match, unless `allow_implicit_invocation: false`

## Enable/Disable in config.toml

```toml
[[skills.config]]
path = "/path/to/skill/SKILL.md"
enabled = false
```

## Built-In Skills

Codex ships with two built-in skills:
- `$skill-creator` -- Create new skills interactively
- `$skill-installer` -- Install skills from a URL or local path

## Differences from Claude Skills

| Aspect | Claude (`.claude/skills/`) | Codex (`.agents/skills/`) |
|--------|---------------------------|--------------------------|
| **Frontmatter** | Many optional fields: `context`, `agent`, `allowed-tools`, `disable-model-invocation`, `user-invocable`, etc. | Only `name` + `description` |
| **Invocation control** | `disable-model-invocation` and `user-invocable` flags in YAML frontmatter | `policy.allow_implicit_invocation` in `agents/openai.yaml` |
| **Subagent support** | `context: fork` spawns a subagent; `agent: Explore` for read-only | Not available in Codex |
| **UI metadata** | Not available (no icons, brand colors, display names) | Full UI config in `agents/openai.yaml` |
| **Tool dependencies** | Not declarable; skill instructions mention tools in prose | Formal `dependencies.tools` in `agents/openai.yaml` |
| **Dynamic context** | `!` backtick syntax runs shell commands at load time | Not available |
| **String substitution** | `$ARGUMENTS`, `$SESSION_ID`, `$USER` in SKILL.md body | Not documented |
| **Progressive disclosure** | `references/` directory loaded on demand | Same pattern -- `references/` loaded on demand |
| **Script execution** | `scripts/` directory with executable files | Same pattern -- `scripts/` directory |
| **Metadata file** | None | `agents/openai.yaml` |

## Conversion from Claude Skill to Codex Skill

1. Copy the directory structure, renaming from `.claude/skills/` to `.agents/skills/`
2. Strip all frontmatter fields except `name` and `description`
3. Remove `$ARGUMENTS`, `$SESSION_ID` substitution variables from SKILL.md body (rewrite as prose)
4. Remove `context: fork` and `agent: Explore` patterns (not supported)
5. Remove `!` backtick dynamic context (not supported)
6. Optionally create `agents/openai.yaml` for UI metadata
7. Declare any MCP tool dependencies in `agents/openai.yaml`
8. Move `allowed-tools` restrictions into prose instructions within SKILL.md

## Example: Minimal Codex Skill

```
exa-search/
├── SKILL.md
└── scripts/
    └── search.py
```

```markdown
---
name: exa-search
description: >-
  Search the web using Exa AI. Use when the user needs current information,
  code examples, or documentation that may be beyond the training cutoff.
---

# Exa Search

Run searches via the Exa API:

\`\`\`bash
python3 ~/.agents/skills/exa-search/scripts/search.py --query "search terms"
\`\`\`

Options: `--type code|research|news`, `--num-results N`, `--date-range 7d|30d|1y`
```
