---
name: codex-orchestrator
description: Orchestrate OpenAI Codex CLI with specialized subagents for code review, debugging, architecture analysis, security audits, refactoring, and documentation. This skill should be used when delegating focused development tasks to Codex subagents (codex-mini, o3, o4-mini) via AGENTS.md persona injection.
---

# Codex Orchestrator

Spawn specialized Codex CLI subagents for focused development tasks. Each profile injects a custom AGENTS.md persona that shapes the agent's behavior, focus areas, and output format.

## Architecture

```
Claude Code (orchestrator)
    ↓ invokes skill
codex-orchestrator scripts
    ↓ spawns via Bash
Codex CLI with AGENTS.md
    ↓ executes
Specialized subagent task
```

## Prerequisites

Verify Codex CLI is installed and configured:

```bash
~/.claude/skills/codex-orchestrator/scripts/codex-status.sh
```

Required:
- Codex CLI: `npm install -g @openai/codex`
- API Key: `export OPENAI_API_KEY=sk-...`

## Available Profiles

| Profile | Purpose | Use When |
|---------|---------|----------|
| `reviewer` | Code quality, bugs, performance | Pre-commit review, PR assessment |
| `debugger` | Root cause analysis, fixes | Investigating bugs, tracing issues |
| `architect` | System design, component boundaries | Planning changes, evaluating architecture |
| `security` | OWASP, vulnerabilities, secrets | Security audits, compliance checks |
| `refactor` | Code cleanup, modernization | Reducing tech debt, improving structure |
| `docs` | API docs, READMEs, comments | Documentation tasks |

## Quick Execution

Execute a one-shot task with a specific profile:

```bash
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh <profile> "<prompt>"
```

Examples:

```bash
# Code review
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh reviewer "Review src/auth.ts for security issues"

# Debug investigation
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh debugger "Debug the login timeout on slow networks"

# Architecture design
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh architect "Design a caching layer for the API"

# Security audit
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh security "Audit the payment module for vulnerabilities"

# Full-auto mode (no approval prompts)
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh reviewer "Fix all lint errors" --full-auto
```

## Session Management

For more control, use the Python session manager:

```bash
# List available profiles
python3 ~/.claude/skills/codex-orchestrator/scripts/codex-session.py list

# Start non-interactive session
python3 ~/.claude/skills/codex-orchestrator/scripts/codex-session.py start debugger "Trace the null pointer in UserService"

# Start interactive session
python3 ~/.claude/skills/codex-orchestrator/scripts/codex-session.py interactive architect

# Show profile details
python3 ~/.claude/skills/codex-orchestrator/scripts/codex-session.py info security
```

## Profile Selection Guide

### Review Tasks
- **reviewer** for general code quality and bugs
- **security** for vulnerability-focused review
- **refactor** for cleanup opportunities

### Investigation Tasks
- **debugger** for bug investigation
- **architect** for understanding system behavior

### Creation Tasks
- **architect** for design decisions
- **docs** for documentation
- **refactor** for implementation improvements

## Chaining Patterns

### Review → Debug → Fix
```bash
# 1. Identify issues
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh reviewer "Review src/api/ for bugs"

# 2. Investigate specific bug
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh debugger "Debug the race condition found in cache.ts"
```

### Architect → Review → Refactor
```bash
# 1. Design approach
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh architect "Design repository layer extraction"

# 2. Validate design
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh reviewer "Review the proposed repository pattern"

# 3. Implement
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh refactor "Extract repository pattern from services"
```

## Script Options

### codex-exec.sh Options

| Option | Description |
|--------|-------------|
| `--model <model>` | Override model (uses ~/.codex/config.toml default if not set) |
| `--sandbox <mode>` | read-only, workspace-write, danger-full-access |
| `--full-auto` | Skip approval prompts |

### Model Selection

| Task Type | Recommended Model |
|-----------|-------------------|
| Quick checks | codex-mini or gpt-5-codex |
| Detailed analysis | o4-mini |
| Complex architecture | o3 |

```bash
# Use default model from your Codex config
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh reviewer "Style check"

# Override with specific model
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh architect "Design distributed cache" --model o3
```

## Testing

Run the test suite to verify installation:

```bash
~/.claude/skills/codex-orchestrator/scripts/test-codex.sh         # Full tests
~/.claude/skills/codex-orchestrator/scripts/test-codex.sh --quick # Skip API test
```

## Reference Documentation

For detailed information:

- `references/codex-cli.md` - Complete CLI command reference
- `references/agents-md-format.md` - AGENTS.md syntax and best practices
- `references/subagent-patterns.md` - Delegation patterns and examples

## Troubleshooting

### "Codex CLI not found"
```bash
npm install -g @openai/codex
```

### "Authentication error"
```bash
export OPENAI_API_KEY=sk-...
# or
codex login
```

### "Model not supported with ChatGPT account"
Models like `codex-mini`, `o3`, `o4-mini` require an OpenAI API account, not a ChatGPT login.
Set an API key instead of using `codex login`:
```bash
export OPENAI_API_KEY=sk-...
```

### "Profile not found"
Available profiles: reviewer, debugger, architect, security, refactor, docs

Check profile exists:
```bash
ls ~/.claude/skills/codex-orchestrator/agents/
```

### Poor Results
- Narrow the task scope
- Provide more context in the prompt
- Try a different profile
- Use `--model o3` for complex tasks
