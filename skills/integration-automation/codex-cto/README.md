# Codex CTO

Inverted orchestration: GPT-5.4-Pro plans and GPT-5.4 reviews (read-only sandbox, JSON schema enforcement), Claude Code executes with native tools.

Sister skill to [`codex-orchestrator`](../codex-orchestrator/README.md). The orchestrator delegates one-shot specialist tasks to Codex. This skill inverts it — Codex directs, Claude Code builds.

## Architecture

```
User: /codex-cto "Add WebSocket auth"
        │
        ▼
┌─ Claude Code (the loop) ──────────────────────────┐
│                                                     │
│  1. cto-invoke.sh plan "objective"                  │
│     └─ codex exec --sandbox read-only               │
│        --output-schema plan-schema.json             │
│     └─ Returns structured plan JSON                 │
│                                                     │
│  2. Claude Code executes tasks with NATIVE TOOLS    │
│     (Read, Edit, Write, Bash, Glob, Grep)           │
│                                                     │
│  3. cto-invoke.sh review "objective + results"      │
│     └─ codex exec --sandbox read-only               │
│        --output-schema review-schema.json           │
│     └─ Returns verdict: approve / revise / abort    │
│                                                     │
│  4. If revise → fix and repeat review               │
│     If approve → done                               │
│     Max 5 iterations                                │
└─────────────────────────────────────────────────────┘
```

## Prerequisites

Same as codex-orchestrator:

```bash
npm install -g @openai/codex
export OPENAI_API_KEY=sk-...
```

Verify with: `~/.claude/skills/codex-orchestrator/scripts/codex-status.sh`

## Usage

Invoke from any Claude Code session:

```
/codex-cto Add a health check endpoint to the Express API
```

### Direct script usage

```bash
# Plan phase (uses gpt-5.4-pro by default)
~/.claude/skills/codex-cto/scripts/cto-invoke.sh plan \
  "Add a health check endpoint"

# Review phase (uses gpt-5.4 by default)
~/.claude/skills/codex-cto/scripts/cto-invoke.sh review \
  "Health check added at /health returning {status: ok}. Tests pass."

# Override model
~/.claude/skills/codex-cto/scripts/cto-invoke.sh plan \
  "Quick fix" --model gpt-5-mini
```

### Options

| Option | Description |
|--------|-------------|
| `--model <model>` | Override model (default: phase-specific) |
| `--dry-run` | Show what would be sent without calling Codex |
| `--max-iterations N` | Set iteration limit (default: 5) |

## How It Works

1. **Plan**: Codex analyzes the codebase (read-only) and returns a structured JSON plan with tasks, acceptance criteria, and dependencies
2. **Execute**: Claude Code works through each task using its native tools — no subprocess, no `claude -p`
3. **Review**: Codex reviews the results (read-only) and returns approve/revise/abort
4. **Iterate**: On "revise", Claude Code fixes issues and requests re-review

Key insight: Claude Code IS the loop. SKILL.md instructions are the orchestrator. No Python loop manager needed.

## Model Defaults

| Phase | Model | Reasoning | Rationale |
|-------|-------|-----------|-----------|
| **Plan** | `gpt-5.4-pro` | `high` | Deepest reasoning for architectural decomposition |
| **Review** | `gpt-5.4` | `high` | Strong reasoning for diff analysis and criteria evaluation |

### Override Per-Task

```bash
# Use Mini for fast iteration
cto-invoke.sh plan "Quick fix" --model gpt-5-mini

# Dry run to inspect the command
cto-invoke.sh plan "Add caching" --dry-run
```

### All Available Models

| Model | ID | Notes |
|-------|----|-------|
| GPT-5.4 Pro | `gpt-5.4-pro` | Default for plan. Deepest reasoning. |
| GPT-5.4 | `gpt-5.4` | Default for review. Unified coding + reasoning. |
| GPT-5 Mini | `gpt-5-mini` | Cost-optimized, fast iteration. |

### Previous Generation (still functional)

| Model | ID |
|-------|----|
| GPT-5.3-Codex | `gpt-5.3-codex` |
| GPT-5.2 | `gpt-5.2` |

## Directory Structure

```
codex-cto/
├── README.md                   # This file
├── SKILL.md                    # Claude Code skill definition + protocol
├── agents/
│   └── cto.md                  # CTO persona AGENTS.md (read-only)
├── scripts/
│   └── cto-invoke.sh           # Thin wrapper: AGENTS.md inject → codex exec → stdout
└── templates/
    ├── plan-schema.json        # JSON Schema for plan phase
    └── review-schema.json      # JSON Schema for review phase
```

## Artifacts

Session artifacts are saved to `.codex-cto/` in the working directory, PID-namespaced for concurrent sessions:

```
.codex-cto/$$/plan-001.json
.codex-cto/$$/review-001.json
```

## Comparison with codex-orchestrator

| Aspect | codex-orchestrator | codex-cto |
|--------|-------------------|-----------|
| Direction | Claude Code → Codex | Codex → Claude Code |
| Codex role | Specialist (one-shot) | Director (plan + review) |
| Claude role | Orchestrator | Worker (executes with native tools) |
| Flow | Single invocation | Multi-round loop |
| Sandbox | Per-profile | Always read-only |
| Output | Free-form or structured | JSON schema enforced |
