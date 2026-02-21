# Codex Orchestrator

Spawn specialized OpenAI Codex CLI subagents for focused development tasks. Each profile injects a custom AGENTS.md persona that shapes the agent's behavior, focus areas, and output format.

## Architecture

```
Claude Code (orchestrator)
    ↓ invokes skill
codex-orchestrator scripts
    ↓ spawns via Bash
Codex CLI with AGENTS.md persona
    ↓ executes
Specialized subagent task
```

## Prerequisites

### 1. Install Codex CLI

```bash
npm install -g @openai/codex
```

### 2. Authentication

Codex CLI supports two authentication methods:

**Option A: ChatGPT Login** (subscription-based)
```bash
codex login
```
Uses your ChatGPT Plus/Pro subscription credits.

**Option B: API Key** (usage-based)
```bash
export OPENAI_API_KEY=sk-...
```
Billed at standard API rates.

### 3. Verify Installation

```bash
./scripts/codex-status.sh
```

## Available Profiles

| Profile | Purpose | Best For |
|---------|---------|----------|
| `reviewer` | Code quality, bugs, performance | Pre-commit review, PR assessment |
| `debugger` | Root cause analysis, fixes | Investigating bugs, tracing issues |
| `architect` | System design, component boundaries | Planning changes, evaluating architecture |
| `security` | OWASP, vulnerabilities, secrets | Security audits, compliance checks |
| `refactor` | Code cleanup, modernization | Reducing tech debt, improving structure |
| `docs` | API docs, READMEs, comments | Documentation tasks |
| `planner` | ExecPlan design documents | Multi-hour tasks, complex features |
| `syseng` | Infrastructure, DevOps, CI/CD | Deployment, containers, observability |
| `builder` | Greenfield implementation | Creating new code from specs |
| `researcher` | Read-only Q&A, analysis | Questions, comparisons (no file changes) |

## Quick Start

### One-Shot Execution

```bash
./scripts/codex-exec.sh <profile> "<prompt>"
```

**Examples:**

```bash
# Code review
./scripts/codex-exec.sh reviewer "Review src/auth.ts for security issues"

# Debug investigation
./scripts/codex-exec.sh debugger "Debug the login timeout on slow networks"

# Architecture design
./scripts/codex-exec.sh architect "Design a caching layer for the API"

# Security audit
./scripts/codex-exec.sh security "Audit the payment module for vulnerabilities"

# Create execution plan (ExecPlan)
./scripts/codex-exec.sh planner "Create an ExecPlan for adding WebSocket support"

# Full-auto mode (no approval prompts)
./scripts/codex-exec.sh reviewer "Fix all lint errors" --full-auto
```

### Session Management

For interactive sessions with more control:

```bash
# List available profiles
python3 ./scripts/codex-session.py list

# Start non-interactive session
python3 ./scripts/codex-session.py start debugger "Trace the null pointer in UserService"

# Start interactive session
python3 ./scripts/codex-session.py interactive architect

# Show profile details
python3 ./scripts/codex-session.py info security
```

## Model Selection

### Available Models (Feb 2026)

| Model | Description | Speed | Capability |
|-------|-------------|-------|------------|
| `gpt-5.3-codex` | Most advanced (recommended) | Medium | Highest |
| `gpt-5.3-codex-spark` | Quick checks / fast iteration | Fast | Good |
| `gpt-5.2-codex` | Previous generation | Medium | High |

### Configure Default Model

Edit `~/.codex/config.toml`:

```toml
model = "gpt-5.3-codex"
```

### Override Per-Task

```bash
./scripts/codex-exec.sh architect "Design distributed cache" --model gpt-5.3-codex
```

## Chaining Patterns

### Review → Debug → Fix

```bash
# 1. Identify issues
./scripts/codex-exec.sh reviewer "Review src/api/ for bugs"

# 2. Investigate specific bug
./scripts/codex-exec.sh debugger "Debug the race condition found in cache.ts"
```

### Planner → Architect → Implement

```bash
# 1. Create comprehensive ExecPlan
./scripts/codex-exec.sh planner "Create ExecPlan for new authentication system"

# 2. Validate architecture
./scripts/codex-exec.sh architect "Review the auth system ExecPlan for design issues"

# 3. Implement (plan guides execution)
./scripts/codex-exec.sh refactor "Implement milestone 1 from the auth ExecPlan" --full-auto
```

### Architect → Review → Refactor

```bash
# 1. Design approach
./scripts/codex-exec.sh architect "Design repository layer extraction"

# 2. Validate design
./scripts/codex-exec.sh reviewer "Review the proposed repository pattern"

# 3. Implement
./scripts/codex-exec.sh refactor "Extract repository pattern from services"
```

## The Planner Profile

The `planner` profile creates **ExecPlans** - self-contained, living design documents for multi-hour implementation tasks. Based on [OpenAI's ExecPlan methodology](https://developers.openai.com/cookbook/articles/codex_exec_plans/).

### ExecPlan Principles

1. **Self-Contained** - Plan has ALL context; no external knowledge required
2. **Living Document** - Updated as progress/discoveries occur
3. **Novice-Enabling** - A complete beginner can execute end-to-end
4. **Outcome-Focused** - Produces demonstrably working behavior
5. **Plain Language** - Defines every term of art immediately

### Required Sections

Every ExecPlan includes:

- **Purpose / Big Picture** - User-visible value
- **Progress** - Checkbox list with timestamps
- **Surprises & Discoveries** - Unexpected findings with evidence
- **Decision Log** - Every decision with rationale
- **Outcomes & Retrospective** - Summary at completion
- **Context and Orientation** - Current state, key files by full path
- **Plan of Work** - Prose describing sequence of changes
- **Concrete Steps** - Exact commands with expected output
- **Validation and Acceptance** - How to verify success
- **Idempotence and Recovery** - Safe retry and rollback paths
- **Interfaces and Dependencies** - Required types, signatures, libraries

## Script Options

### codex-exec.sh

| Option | Description |
|--------|-------------|
| `--model <model>` | Override model for this task |
| `--sandbox <mode>` | `read-only`, `workspace-write`, `danger-full-access` |
| `--full-auto` | Skip approval prompts |

## Directory Structure

```
codex-orchestrator/
├── README.md           # This file
├── SKILL.md            # Claude Code skill definition
├── agents/             # AGENTS.md persona profiles
│   ├── architect.md
│   ├── debugger.md
│   ├── docs.md
│   ├── planner.md      # ExecPlan methodology
│   ├── refactor.md
│   ├── reviewer.md
│   └── security.md
├── references/         # Documentation
│   ├── agents-md-format.md
│   ├── codex-cli.md
│   └── subagent-patterns.md
└── scripts/            # Execution scripts
    ├── codex-exec.sh   # One-shot execution
    ├── codex-session.py # Session management
    ├── codex-status.sh # Installation check
    └── test-codex.sh   # Test suite
```

## Troubleshooting

### "Codex CLI not found"

```bash
npm install -g @openai/codex
```

### "Model not supported with ChatGPT account"

Older model names (`codex-mini`, `o3`, `o4-mini`) have been deprecated. Current models: `gpt-5.3-codex`, `gpt-5.3-codex-spark`, `gpt-5.2-codex`.

```bash
# Recommended
./scripts/codex-exec.sh reviewer "task" --model gpt-5.3-codex

# Fast/cheap
./scripts/codex-exec.sh reviewer "task" --model gpt-5.3-codex-spark
```

### "Authentication error"

```bash
# Re-authenticate with ChatGPT
codex login

# Or set API key
export OPENAI_API_KEY=sk-...
```

### "Profile not found"

Available profiles: `reviewer`, `debugger`, `architect`, `security`, `refactor`, `docs`, `planner`, `syseng`, `builder`, `researcher`

Check profiles exist:

```bash
ls ./agents/
```

### Poor Results

- Narrow the task scope
- Provide more context in the prompt
- Try a different profile
- Use `--model gpt-5.3-codex` for complex tasks

## Testing

Run the test suite to verify installation:

```bash
./scripts/test-codex.sh         # Full tests
./scripts/test-codex.sh --quick # Skip API test
```

## References

- [Codex CLI Documentation](https://developers.openai.com/codex/cli)
- [Codex Models](https://developers.openai.com/codex/models)
- [AGENTS.md Format](https://developers.openai.com/codex/guides/agents-md)
- [ExecPlan Methodology](https://developers.openai.com/cookbook/articles/codex_exec_plans/)
