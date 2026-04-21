# AGENTS.md Manager

Create, audit, and maintain AGENTS.md files and Codex CLI configuration for any project. Supports cross-agent compatibility (Codex, Cursor, Copilot, Devin, Jules, Amp, Gemini CLI), CLAUDE.md-to-AGENTS.md conversion, config.toml generation, .rules authoring, and .agents/skills/ scaffolding.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

Most AI coding agents now read an AGENTS.md file for project context, but the format constraints differ from CLAUDE.md (no `@import`, no YAML frontmatter, 32 KiB limit, plain markdown only). This skill handles the full lifecycle: analyze a project, generate AGENTS.md from scratch, convert from CLAUDE.md, generate Codex config.toml, scaffold Codex skills, and audit existing files for bloat and staleness.

Complementary to `codex-orchestrator`, which executes subagents---this skill creates the config files they consume.

---

## Structure

```
agents-md-manager/
  SKILL.md                                   # Full usage guide and reference
  README.md                                  # This file
  assets/                                    # Skill assets
  references/
    agents-md-spec.md                        # AGENTS.md discovery, concatenation, override rules
    config-toml-reference.md                 # Complete config.toml field reference
    starlark-rules-spec.md                   # .rules file syntax and examples
    codex-skills-format.md                   # .agents/skills/ format vs Claude skills
    conversion-mapping.md                    # CLAUDE.md → AGENTS.md field-by-field mapping
    templates.md                             # AGENTS.md templates by project type
  scripts/
    analyze_project.py                       # Detect stack, existing config, and gaps
    convert_claude_to_agents.py              # Convert CLAUDE.md to AGENTS.md
    generate_config_toml.py                  # Generate config.toml (global or project)
    scaffold_codex_skill.py                  # Scaffold .agents/skills/<name>/
    validate_agents_md.py                    # Audit existing AGENTS.md for issues
```

---

## Modes

| Mode | When | Script |
|------|------|--------|
| **Create** | New project needs AGENTS.md | `analyze_project.py` → write |
| **Refresh** | Existing AGENTS.md needs audit | `validate_agents_md.py` |
| **Convert** | Migrate from CLAUDE.md | `convert_claude_to_agents.py` |
| **Config** | Generate config.toml | `generate_config_toml.py` |
| **Skills** | Scaffold .agents/skills/ | `scaffold_codex_skill.py` |
| **Rules** | Create .rules files | Manual, see `references/starlark-rules-spec.md` |

---

## Scripts

| Script | Purpose | Example |
|--------|---------|---------|
| `analyze_project.py` | Detect stack, commands, and Codex artifact inventory | `python3 analyze_project.py /path/to/project` |
| `convert_claude_to_agents.py` | Convert CLAUDE.md to AGENTS.md with transformation report | `python3 convert_claude_to_agents.py CLAUDE.md` |
| `generate_config_toml.py` | Generate global or project-scoped config.toml | `python3 generate_config_toml.py --project .` |
| `scaffold_codex_skill.py` | Create .agents/skills/ with SKILL.md and openai.yaml | `python3 scaffold_codex_skill.py my-skill` |
| `validate_agents_md.py` | Audit for size, syntax, stale references, secrets | `python3 validate_agents_md.py /path/to/project` |

---

## Key Constraints

- **32 KiB** max per AGENTS.md (`project_doc_max_bytes`)
- **Plain markdown only**---no `@import`, no YAML frontmatter
- Target **under 200 lines** per file (warn >200, error >400)
- Include a **Boundaries** section (Always/Ask/Never) for agent guardrails
- Nested files (monorepos) should stay under 100 lines each

---

## Setup

### Prerequisites

- Python 3.9+
- No external dependencies (scripts use stdlib only)

### Usage

```bash
# Analyze a project
python3 ~/.claude/skills/agents-md-manager/scripts/analyze_project.py /path/to/project

# Convert CLAUDE.md to AGENTS.md
python3 ~/.claude/skills/agents-md-manager/scripts/convert_claude_to_agents.py CLAUDE.md output/AGENTS.md

# Audit existing AGENTS.md
python3 ~/.claude/skills/agents-md-manager/scripts/validate_agents_md.py /path/to/project
```

---

## Related Skills

- **`codex-orchestrator`**: Executes Codex subagents using the config files this skill creates.
- **`claude-md-manager`**: Sister skill for Claude Code's CLAUDE.md format.

---

## Requirements

- Python 3.9+
- No external dependencies

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/core-development/agents-md-manager ~/.claude/skills/
```
