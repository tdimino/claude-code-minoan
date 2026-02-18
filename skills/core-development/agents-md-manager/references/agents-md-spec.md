# AGENTS.md Specification

## Overview

AGENTS.md is the open standard for AI coding agent instructions. It complements README.md (for humans) with agent-focused guidance: build steps, test commands, code conventions, and boundaries.

Stewarded by the Agentic AI Foundation under the Linux Foundation. Adopted by 20+ agents: Codex, Cursor, VS Code, Devin, GitHub Copilot, Jules (Google), Amp, Gemini CLI, Factory, Semgrep, Goose, Aider, Windsurf, Kilo Code, Warp, RooCode, Zed, opencode, and more.

## Format

- **Plain markdown**. No required fields, no YAML frontmatter, no special syntax.
- Any headings and structure work. The agent parses the raw text.
- No `@import` syntax (unlike CLAUDE.md).
- No file size enforcement by format—but Codex enforces `project_doc_max_bytes`.

## Discovery (Codex CLI)

Codex builds an instruction chain once per session:

1. **Global scope**: `~/.codex/AGENTS.override.md` (if exists), else `~/.codex/AGENTS.md`. At most one file at this level.
2. **Project scope**: Starting at project root (typically git root), walk down to CWD. At each directory, check `AGENTS.override.md`, then `AGENTS.md`, then `project_doc_fallback_filenames`. At most one file per directory.
3. **Merge**: Concatenate from root down, joined by blank lines. Later files (closer to CWD) override earlier guidance.

Codex skips empty files. Stops adding once combined size reaches `project_doc_max_bytes` (default 32 KiB).

## Override Mechanism

`AGENTS.override.md` takes precedence over `AGENTS.md` in the same directory. Use for temporary overrides without deleting the base file. Remove the override to restore shared guidance.

When both exist in a directory, only `AGENTS.override.md` is read. The base `AGENTS.md` is ignored for that directory level.

## Size Limits

| Setting | Default | Location |
|---------|---------|----------|
| `project_doc_max_bytes` | 32768 (32 KiB) | `~/.codex/config.toml` |

Raise the limit or split instructions across nested directories when you hit the cap.

## Fallback Filenames

Configure in `config.toml`:

```toml
project_doc_fallback_filenames = ["TEAM_GUIDE.md", ".agents.md"]
```

Check order per directory: `AGENTS.override.md` → `AGENTS.md` → fallback filenames in order.

## Global Personal Defaults

Create `~/.codex/AGENTS.md` for preferences that apply across all repositories:

```markdown
# Global Working Agreements
- Prefer pnpm when installing dependencies
- Ask before adding production dependencies
- Run tests after modifying code
```

Use `~/.codex/AGENTS.override.md` for temporary global overrides.

## Nested Hierarchies (Monorepos)

Place AGENTS.md at multiple directory levels. Each file is concatenated in order:

```
/AGENTS.md                    # Repo-wide (loaded first)
/services/payments/AGENTS.md  # Service-specific (loaded second, overrides)
```

Codex stops searching at CWD. Place overrides close to specialized work.

## Cross-Agent Compatibility

AGENTS.md works across all supporting agents without modification. Stick to:
- Standard markdown (no proprietary extensions)
- Imperative instructions ("Run X before Y")
- Explicit command examples with full syntax
- No agent-specific features (no Claude @imports, no Cursor metadata)

## Project Root Detection

Codex uses `.git` as the default project root marker. Customize:

```toml
project_root_markers = [".git", ".hg", ".sl"]
```

Set `project_root_markers = []` to use CWD as project root.

## Verification

```bash
# Confirm Codex loads instruction files
codex --ask-for-approval never "Summarize the current instructions."

# Confirm nested overrides
codex --cd services/payments --ask-for-approval never "Show which instruction files are active."

# Check session logs for loaded files
cat ~/.codex/log/codex-tui.log
```
