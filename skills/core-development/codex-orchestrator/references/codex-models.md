# Codex CLI Model Reference

Last updated: 2026-02-26

## Current Models

| Model | ID | Released | Description |
|-------|----|----------|-------------|
| **GPT-5.3-Codex** | `gpt-5.3-codex` | Feb 5, 2026 | Latest generation. 25% faster than 5.2. Self-bootstrapped (trained partly on its own output). SOTA on SWE-Bench Pro. Default for coding profiles. |
| **GPT-5.3-Codex Spark** | `gpt-5.3-codex-spark` | Feb 5, 2026 | Lightweight variant of 5.3. Near-instant responses. Pro subscribers only. Ideal for quick reads, small reviews, fast iteration. |
| **GPT-5.2-Codex** | `gpt-5.2-codex` | Dec 2025 | Deeper single-pass reasoning. Default for planning profiles. Community reports fewer cleanup iterations vs 5.3 on complex tasks. |

## Deprecated Models

These model IDs no longer work with Codex CLI. Use the current equivalents above.

| Deprecated ID | Era | Replaced By |
|---------------|-----|-------------|
| `o3` | Mid-2025 | `gpt-5.3-codex` |
| `o3-mini` | Mid-2025 | `gpt-5.3-codex-spark` |
| `o4-mini` | Late 2025 | `gpt-5.3-codex-spark` |
| `codex-mini` | Early 2025 | `gpt-5.3-codex-spark` |
| `codex-5.2` | Alias | `gpt-5.2-codex` |
| `gpt-5.1-codex-mini` | Oct 2025 | `gpt-5.3-codex-spark` |
| `gpt-5.1-codex-max` | Oct 2025 | `gpt-5.3-codex` |

## Reasoning Effort Levels

Reasoning effort controls how much "thinking" the model does before responding. Higher effort = deeper reasoning but slower and more expensive.

| Level | CLI Value | Use Case |
|-------|-----------|----------|
| Minimal | `minimal` | Trivial lookups, status checks |
| Low | `low` | Simple reads, formatting |
| Medium | `medium` | Default interactive coding (speed/quality balance) |
| High | `high` | Complex tasks needing deeper reasoning |
| Extra High | `xhigh` | Hardest tasks: architecture, multi-file refactors, security audits |

Source: [Codex Config Reference](https://developers.openai.com/codex/config-reference) — `model_reasoning_effort` key.

### How to Set Reasoning Effort

In `~/.codex/config.toml`:

```toml
model = "gpt-5.3-codex"
model_reasoning_effort = "xhigh"
```

Per-invocation via codex-orchestrator:

```bash
codex-exec.sh builder "task" --reasoning xhigh
codex-exec.sh planner "task" --reasoning high
```

Raw Codex CLI:

```bash
codex --config model_reasoning_effort='"xhigh"'
codex -c model_reasoning_effort='"xhigh"'
```

### Plan Mode Reasoning

Codex has a separate `plan_mode_reasoning_effort` config key. When unset, Plan mode defaults to `medium`. This is independent of `model_reasoning_effort`.

```toml
plan_mode_reasoning_effort = "high"
```

## Configuration

Default model is set in `~/.codex/config.toml`:

```toml
model = "gpt-5.3-codex"
```

Override per-invocation with `--model` and `--reasoning`:

```bash
codex exec --model gpt-5.3-codex-spark "Quick review of auth.ts"
codex exec --model gpt-5.2-codex "Compare against previous results"
```

Both `codex-orchestrator` and `codex-cto` skills pass `--model` and `-c model_reasoning_effort` through to `codex exec`. Any model ID that Codex CLI accepts will work.

## Selection Guide

| Task | Model | Reasoning | Why |
|------|-------|-----------|-----|
| Coding subagents (builder, reviewer, debugger, etc.) | `gpt-5.3-codex` | `xhigh` | Fast execution + maximum reasoning depth |
| Planning subagents (planner, architect, researcher) | `gpt-5.2-codex` | `xhigh` | Deeper single-pass reasoning, fewer cleanup iterations |
| Quick reads, fast iteration | `gpt-5.3-codex-spark` | `medium` | Near-instant, low cost |
| CTO planning (codex-cto) | `gpt-5.3-codex` | `xhigh` | Architectural reasoning at full capability |
| CTO review (codex-cto) | `gpt-5.3-codex` | `high` | Diff analysis needs strong but fast reasoning |
