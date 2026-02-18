# CLAUDE.md to AGENTS.md Conversion Mapping

## Overview

This reference provides a field-by-field mapping from CLAUDE.md (Claude Code) to AGENTS.md (cross-agent standard). Use it when converting existing Claude Code projects to the agent-agnostic format, or when maintaining both files in parallel.

## Field-by-Field Mapping

| CLAUDE.md Feature | AGENTS.md Equivalent | Automation | Notes |
|---|---|---|---|
| `@path/to/file.md` imports | Inline content (<50 lines) or create nested AGENTS.md | `convert_claude_to_agents.py` detects | Review: large imports may exceed 32 KiB |
| `@~/.claude/personal.md` | Move to `~/.codex/AGENTS.md` | Manual | Personal preferences stay global |
| `@agent_docs/building.md` etc. | Inline key sections or create nested AGENTS.md per subdir | Script generates stubs | Must respect one-per-dir rule |
| `.claude/hooks/` references | Suggest `.rules` file equivalents | Script suggests | Different paradigm: hooks = shell events, rules = command approval |
| `/skill-name` invocations | Prose: "Use tool X for task Y" or scaffold `.agents/skills/` | Manual | Codex skills use different format (see `codex-skills-format.md`) |
| `settings.json` permissions | `.codex/config.toml` | `generate_config_toml.py` | JSON to TOML format change |
| MCP servers in settings.json | `[mcp_servers]` in config.toml | Script extracts | Same concept, TOML syntax |
| Progressive disclosure (`agent_docs/`) | Nested AGENTS.md hierarchy | Script scaffolds | One file per directory |
| Claude-specific commands (`/init`, `/context`, `/compact`) | Remove entirely | Script strips | Not applicable to Codex |
| `file:line` references | Same pattern works | Pass-through | Both support code references |
| Hierarchical merge (parent to child) | Root-to-CWD concatenation | Similar but different | Codex: one per dir, `AGENTS.override.md` |
| Anti-patterns (linting via LLM) | Same anti-patterns apply | Pass-through | Same guidance |
| Code blocks and examples | Same format | Pass-through | Standard markdown |
| `$ARGUMENTS` / `$SESSION_ID` | Not available | Strip or rewrite | Codex has no skill string substitution |
| `context: fork` subagents | Not available | Rewrite as prose | Codex does not support subagent forking |
| `!` backtick dynamic context | Not available | Inline the output or remove | Codex has no dynamic context injection |
| `allowed-tools` restrictions | Prose instructions | Rewrite | "Only use tool X" in AGENTS.md body |
| `disable-model-invocation` | `allow_implicit_invocation: false` | Move to `agents/openai.yaml` | Different mechanism, similar intent |
| YAML frontmatter in CLAUDE.md | Remove entirely | Script strips | AGENTS.md uses no frontmatter |
| Memory files (`.claude/memory/`) | Not applicable | Exclude | Agent memory is implementation-specific |
| Custom commands (`.claude/commands/`) | No direct equivalent | Rewrite as scripts in `.agents/skills/` | Or document as shell commands in AGENTS.md |

## Conversion Workflow

### Step 1: Analyze

```bash
python3 ~/.claude/skills/agents-md-manager/scripts/analyze_project.py [project_path]
```

Detects: CLAUDE.md location, `@import` targets, hooks, skills, settings.json, existing AGENTS.md.

### Step 2: Convert

```bash
python3 ~/.claude/skills/agents-md-manager/scripts/convert_claude_to_agents.py <claude_md_path> [output_path]
```

Produces:
- `AGENTS.md` with converted content
- `conversion_report.json` listing all transformations and manual review items

### Step 3: Review the Report

The `conversion_report.json` contains:

```json
{
  "auto_converted": [
    {"type": "auto", "action": "Inlined @agent_docs/building.md (32 lines)"},
    {"type": "auto", "action": "Stripped YAML frontmatter"},
    {"type": "auto", "action": "Removed Claude command: - `/compact`"}
  ],
  "manual_review": [
    {"type": "manual", "action": "Hooks reference on line 45", "suggestion": "Convert to .rules file (Starlark). See references/starlark-rules-spec.md"},
    {"type": "manual", "action": "Removed @agent_docs/architecture.md", "suggestion": "Create nested AGENTS.md in agent_docs/ (280 lines)"}
  ],
  "warnings": [
    "Output is 28,500 bytes, exceeds 32 KiB limit. Split into nested files."
  ]
}
```

### Step 4: Validate

```bash
python3 ~/.claude/skills/agents-md-manager/scripts/validate_agents_md.py [project_path]
```

Checks: size limits, no `@import` syntax, no YAML frontmatter, command accuracy, directory references.

### Step 5: Generate Config

```bash
python3 ~/.claude/skills/agents-md-manager/scripts/generate_config_toml.py --project <path>
```

Converts `settings.json` entries to `.codex/config.toml`: MCP servers, permissions, model settings.

### Step 6: Create Rules (if applicable)

If the project uses `.claude/hooks/`, review each hook and determine if the behavior maps to a `.rules` file. See `starlark-rules-spec.md`.

## Things That Cannot Be Auto-Converted

### Hook Logic

Claude hooks are shell scripts triggered by lifecycle events (pre-commit, post-tool-use, etc.). Codex `.rules` files only handle command approval (allow/prompt/forbidden). Hooks that:
- Run linters or formatters
- Modify files before commit
- Send notifications
- Perform conditional logic based on file content

...must be reimplemented as CI steps, git hooks, or manual agent instructions.

### Skill Behavior

Claude skills support:
- `context: fork` for subagent isolation -- no Codex equivalent
- `agent: Explore` for read-only subagents -- no Codex equivalent
- Dynamic context via `!` backtick syntax -- no Codex equivalent
- `$ARGUMENTS` string substitution -- no Codex equivalent

Rewrite skill instructions as prose in AGENTS.md or scaffold new `.agents/skills/` with the Codex format.

### Agent Subagent Patterns

Claude's `context: fork` creates an isolated subagent with its own context window. Codex has no subagent mechanism. Rewrite as:
- Sequential instructions in AGENTS.md
- Separate scripts the agent can invoke
- Human-in-the-loop steps

### Dynamic Context Injection

Claude's `!` backtick syntax runs shell commands at SKILL.md load time and injects the output. Codex loads static markdown only. Options:
- Pre-generate the content and inline it
- Have the agent run the command explicitly during the session
- Move dynamic content to a script in `scripts/`

## Maintaining Both Files

If the project needs both CLAUDE.md and AGENTS.md:

1. Keep CLAUDE.md as the source of truth for Claude-specific features (hooks, skills, @imports)
2. Keep AGENTS.md as the cross-agent baseline (commands, structure, conventions, boundaries)
3. Do not duplicate content -- CLAUDE.md can `@import` AGENTS.md if needed
4. Run `validate_agents_md.py` in CI to catch drift

## Import Resolution Strategy

When converting `@import` statements:

| Import Size | Strategy |
|-------------|----------|
| < 50 lines | Inline directly into AGENTS.md |
| 50-200 lines | Create a nested AGENTS.md in the imported file's directory |
| > 200 lines | Split into multiple nested AGENTS.md files by topic |
| Global (`@~/.claude/...`) | Move to `~/.codex/AGENTS.md` |

Always check that the total concatenated size stays under `project_doc_max_bytes` (32 KiB default).
