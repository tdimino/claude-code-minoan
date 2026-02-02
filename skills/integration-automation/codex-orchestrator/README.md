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
| `builder` | Greenfield implementation | New features, incremental development |
| `syseng` | Infrastructure, DevOps, CI/CD | Deployment, containers, monitoring |

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

# Build new feature from spec
./scripts/codex-exec.sh builder "Implement user authentication with JWT"

# Continue from previous builder session
./scripts/codex-exec.sh builder "continue"

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

### Available Models (Jan 2026)

| Model | Description | Speed | Capability |
|-------|-------------|-------|------------|
| `gpt-5.2-codex` | Most advanced (recommended) | Medium | Highest |
| `gpt-5.1-codex-mini` | Cost-effective | Fast | Good |
| `gpt-5.1-codex-max` | Long-horizon tasks | Slow | Very High |
| `gpt-5.2` | General agentic | Medium | High |

### Configure Default Model

Edit `~/.codex/config.toml`:

```toml
model = "gpt-5.2-codex"
```

### Override Per-Task

```bash
./scripts/codex-exec.sh architect "Design distributed cache" --model gpt-5.1-codex-max
```

## Chaining Patterns

### Review → Debug → Fix

```bash
# 1. Identify issues
./scripts/codex-exec.sh reviewer "Review src/api/ for bugs"

# 2. Investigate specific bug
./scripts/codex-exec.sh debugger "Debug the race condition found in cache.ts"
```

### Planner → Architect → Builder

```bash
# 1. Create comprehensive ExecPlan
./scripts/codex-exec.sh planner "Create ExecPlan for new authentication system"

# 2. Validate architecture
./scripts/codex-exec.sh architect "Review the auth system ExecPlan for design issues"

# 3. Build (plan guides implementation)
./scripts/codex-exec.sh builder "Implement milestone 1 from the auth ExecPlan" --full-auto
```

### Architect → Builder → Reviewer

```bash
# 1. Design approach
./scripts/codex-exec.sh architect "Design a caching layer for the API"

# 2. Build the feature
./scripts/codex-exec.sh builder "Implement the caching layer from architect's design"

# 3. Review the implementation
./scripts/codex-exec.sh reviewer "Review the new caching implementation"
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

## The Builder Profile

The `builder` profile specializes in **greenfield implementation** - creating new features from scratch with incremental progress tracking. It maintains state via `progress.json` for session recovery.

### Builder Principles

1. **Atomic Units** - Build one feature/component at a time
2. **Verification-First** - Test each piece before moving on
3. **State Persistence** - Track progress in JSON for session recovery
4. **Clean Boundaries** - Create files in predictable locations
5. **Convention Following** - Match existing project patterns

### Task Types

- `build <requirement>` - Create new components/features from specification
- `continue` - Resume from progress.json file
- `verify` - Test current implementation state
- `status` - Show progress state summary

### Progress Tracking

Builder maintains `progress.json` at project root:

```json
{
  "task": "Implement user authentication",
  "status": "in_progress",
  "features": [
    {"name": "Login endpoint", "status": "completed"},
    {"name": "Session middleware", "status": "in_progress"},
    {"name": "Logout endpoint", "status": "pending"}
  ],
  "verification": {"build": true, "tests": true, "lint": true}
}
```

### When to Use Builder vs Refactor

| Use Builder | Use Refactor |
|-------------|--------------|
| Creating new files/components | Modifying existing code |
| Implementing new features | Behavior-preserving changes |
| Building from a spec | Improving structure |
| Greenfield development | Reducing tech debt |

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
│   ├── builder.md      # Greenfield implementation with progress tracking
│   ├── debugger.md
│   ├── docs.md
│   ├── planner.md      # ExecPlan methodology
│   ├── refactor.md
│   ├── reviewer.md
│   ├── security.md
│   └── syseng.md       # Infrastructure/DevOps
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

Some older model names (`codex-mini`, `o3`, `o4-mini`) have been deprecated. Use current models:

```bash
# Recommended
./scripts/codex-exec.sh reviewer "task" --model gpt-5.2-codex

# Fast/cheap
./scripts/codex-exec.sh reviewer "task" --model gpt-5.1-codex-mini
```

### "Authentication error"

```bash
# Re-authenticate with ChatGPT
codex login

# Or set API key
export OPENAI_API_KEY=sk-...
```

### "Profile not found"

Available profiles: `reviewer`, `debugger`, `architect`, `security`, `refactor`, `docs`, `planner`, `builder`, `syseng`

Check profiles exist:

```bash
ls ./agents/
```

### Poor Results

- Narrow the task scope
- Provide more context in the prompt
- Try a different profile
- Use `--model gpt-5.1-codex-max` for complex tasks

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
