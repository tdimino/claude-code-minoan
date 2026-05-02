# Codex Orchestrator

> Last updated: 2026-04-23 | Codex CLI v0.122.0 | Models: GPT-5.5 family

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
# or
brew install --cask codex
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
| `builder` | Greenfield implementation | New features from specs |
| `researcher` | Read-only Q&A and analysis | Questions, comparisons (no file changes) |

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

## Model & Reasoning Configuration

### Profile Defaults

Each profile has a default model and reasoning effort. User flags override these.

| Profile Type | Profiles | Model | Reasoning |
|-------------|----------|-------|-----------|
| **Coding** | builder, reviewer, debugger, refactor, syseng, security, docs | `gpt-5.5` | `high` |
| **Planning** | planner, architect | `gpt-5.5` | `high` |
| **Research** | researcher | `gpt-5.5` | `medium` |

### Available Models (Apr 2026)

| Model | ID | ChatGPT Auth | API Key | Notes |
|-------|----|:---:|:---:|-------|
| **GPT-5.5** | `gpt-5.5` | Yes | Yes | New flagship. Agentic workflows, 2M context. Default for all profiles. |
| **GPT-5.5 Pro** | `gpt-5.5-pro` | No | Yes | Iterative research partner. Use `--model gpt-5.5-pro` to override. |
| **GPT-5 Mini** | `gpt-5-mini` | No | Yes | Cost-optimized. Fast iteration. |
| **GPT-5 Nano** | `gpt-5-nano` | No | Yes | High-throughput. Cheapest option. |

> **Note:** `gpt-5.5-pro`, `gpt-5-mini`, and `gpt-5-nano` require `OPENAI_API_KEY` (API billing). ChatGPT auth (`codex login`) supports `gpt-5.5` and legacy models (`gpt-5.4`, `gpt-5.3-codex`, `gpt-5.2`). GPT-5.3 Instant and GPT-5.4 Thinking are ChatGPT-app models, not Codex CLI model IDs.

### Reasoning Effort Levels

`none` < `minimal` < `low` < `medium` < `high` < `xhigh`

See `references/codex-models.md` for full model history, capabilities, and reasoning reference.

### Override Per-Task

```bash
# Override model for quick tasks
./scripts/codex-exec.sh architect "Design distributed cache" --model gpt-5-mini

# Override reasoning effort
./scripts/codex-exec.sh builder "Quick lint fix" --reasoning medium

# Override both
./scripts/codex-exec.sh planner "Complex design" --model gpt-5.5 --reasoning high
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
| `--model <model>` | Override model (default: per-profile) |
| `--reasoning <level>` | Override reasoning effort: `minimal`, `low`, `medium`, `high`, `xhigh` |
| `--sandbox <mode>` | `read-only`, `workspace-write`, `danger-full-access` |
| `--full-auto` | Skip approval prompts |
| `--no-auto` | Disable auto `--full-auto` (require manual approval) |
| `--web-search` | Enable Exa web search (injects guide into AGENTS.md) |
| `--search` | Enable native Codex web search (works in all sandboxes) |
| `--json` | Output JSONL event stream (pipe to jq, logs, etc.) |
| `--image <file>` | Attach image to prompt (vision input) |
| `--resume` | Resume previous exec session (builder "continue" workflow) |
| `--with-mcp` | Keep global MCP servers enabled (no-op, kept for compatibility) |

## Notable Recent CLI Features (v0.110–v0.122)

- **Plugin system** (v0.110) — `codex plugins` / `codex plugin install <name>`
- **`/fast` toggle** (v0.110) — Switch to faster output mid-session
- **Smart Approvals** (v0.115) — Guardian subagent evaluates command safety before prompting
- **Full-resolution `view_image`** (v0.115) — Vision input at native resolution
- **`userpromptsubmit` hook** (v0.116) — Fires when user submits a prompt
- **Sub-agent addressing** (v0.117) — Send messages to specific sub-agents by name
- **`/side` conversations** (v0.122) — Parallel side conversations without losing main context
- **Plan Mode improvements** (v0.122) — Better plan editing, approval, and execution tracking
- **Deny-read glob policies** (v0.122) — `deny_file_read_patterns` blocks reads of sensitive paths

See `references/codex-cli.md` for full feature details.

## Directory Structure

```
codex-orchestrator/
├── README.md              # This file
├── SKILL.md               # Claude Code skill definition
├── agents/                # AGENTS.md persona profiles
│   ├── architect.md
│   ├── builder.md
│   ├── debugger.md
│   ├── docs.md
│   ├── planner.md         # ExecPlan methodology
│   ├── refactor.md
│   ├── researcher.md
│   ├── reviewer.md
│   ├── security.md
│   └── syseng.md
├── references/            # Documentation
│   ├── agents-md-format.md
│   ├── codex-cli.md
│   ├── codex-models.md
│   └── subagent-patterns.md
└── scripts/               # Execution scripts
    ├── codex-exec.sh      # One-shot execution
    ├── codex-session.py   # Session management
    ├── codex-status.sh    # Installation check
    ├── codex-version-check.sh  # Version check + auto-update
    └── test-codex.sh      # Test suite
```

## Troubleshooting

### "Codex CLI not found"

```bash
npm install -g @openai/codex
```

### "Model not supported with ChatGPT account"

Older model names (`codex-mini`, `o3`, `o4-mini`, `gpt-5.3-codex`) have been superseded. Use current models:

```bash
# Recommended
./scripts/codex-exec.sh reviewer "task" --model gpt-5.5

# Fast/cheap
./scripts/codex-exec.sh reviewer "task" --model gpt-5-mini
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
- Use `--model gpt-5.5-pro` for complex tasks

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
