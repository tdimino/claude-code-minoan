# Codex CLI Model Reference

Last updated: 2026-03-05

## Current Models

| Model | ID | Released | Description |
|-------|----|----------|-------------|
| **GPT-5.4** | `gpt-5.4` | Mar 2026 | Unified flagship. Absorbs GPT-5.3-Codex coding into general model. 1M+ token context, built-in computer use, native compaction, deferred tool loading. Default for coding and research profiles. |
| **GPT-5.4 Pro** | `gpt-5.4-pro` | Mar 2026 | Deeper reasoning variant with more compute. For hardest problems: architecture, multi-step planning, complex decomposition. Default for planning profiles and CTO plan phase. |
| **GPT-5 Mini** | `gpt-5-mini` | Mar 2026 | Cost-optimized reasoning and chat. Replaces GPT-5.3-Codex-Spark for fast iteration, lint fixes, quick reads. |
| **GPT-5 Nano** | `gpt-5-nano` | Mar 2026 | High-throughput, simple tasks. Classification, straightforward instruction-following. |

## Previous Generation

These models still work but are superseded by the GPT-5.4 family.

| Model | ID | Released | Description |
|-------|----|----------|-------------|
| **GPT-5.3-Codex** | `gpt-5.3-codex` | Feb 5, 2026 | Previous coding SOTA. 25% faster than 5.2. SWE-Bench Pro 56.8%. |
| **GPT-5.3-Codex Spark** | `gpt-5.3-codex-spark` | Feb 5, 2026 | Lightweight variant of 5.3. Near-instant responses. Pro subscribers only. |
| **GPT-5.2** | `gpt-5.2` | Dec 2025 | Deeper single-pass reasoning. Previously default for planning profiles. |

## Deprecated Models

These model IDs no longer work with Codex CLI. Use the current equivalents above.

| Deprecated ID | Era | Replaced By |
|---------------|-----|-------------|
| `o3` | Mid-2025 | `gpt-5.4` |
| `o3-mini` | Mid-2025 | `gpt-5-mini` |
| `o4-mini` | Late 2025 | `gpt-5-mini` |
| `codex-mini` | Early 2025 | `gpt-5-mini` |
| `codex-5.2` | Alias | `gpt-5.2` |
| `gpt-5.1-codex-mini` | Oct 2025 | `gpt-5-mini` |
| `gpt-5.1-codex-max` | Oct 2025 | `gpt-5.4` |

## Reasoning Effort Levels

Reasoning effort controls how much "thinking" the model does before responding. Higher effort = deeper reasoning but slower and more expensive.

| Level | CLI Value | Use Case |
|-------|-----------|----------|
| None | `none` | Lowest latency, no chain-of-thought (GPT-5.2+ only) |
| Minimal | `minimal` | Trivial lookups, status checks |
| Low | `low` | Simple reads, formatting |
| Medium | `medium` | Research, read-only Q&A (speed/quality balance) |
| High | `high` | Default for most coding and planning tasks |
| Extra High | `xhigh` | Legacy level from GPT-5.3-Codex era. Still works but `high` on GPT-5.4 achieves equivalent depth. |

Source: [Codex Config Reference](https://developers.openai.com/codex/config-reference) — `model_reasoning_effort` key.

**Note:** GPT-5.4's base reasoning is deeper than GPT-5.3's xhigh. `high` is now the recommended default for most tasks.

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
model = "gpt-5.4"
```

Override per-invocation with `--model` and `--reasoning`:

```bash
codex exec --model gpt-5-mini "Quick review of auth.ts"
codex exec --model gpt-5.4-pro "Design the caching architecture"
```

Both `codex-orchestrator` and `codex-cto` skills pass `--model` and `-c model_reasoning_effort` through to `codex exec`. Any model ID that Codex CLI accepts will work.

## Selection Guide

| Task | Model | Reasoning | Why |
|------|-------|-----------|-----|
| Coding subagents (builder, reviewer, debugger, etc.) | `gpt-5.4` | `high` | Unified coding + reasoning, native compaction for longer trajectories |
| Planning subagents (planner, architect) | `gpt-5.4-pro` | `high` | Deepest reasoning for architecture and multi-step planning |
| Research subagent (researcher) | `gpt-5.4` | `medium` | 1M context window for codebase analysis, read-only doesn't need deep reasoning |
| Quick reads, fast iteration | `gpt-5-mini` | `medium` | Cost-optimized, replaces Spark |
| CTO planning (codex-cto) | `gpt-5.4-pro` | `high` | Architectural decomposition at maximum depth |
| CTO review (codex-cto) | `gpt-5.4` | `high` | Strong reasoning for diff analysis and acceptance criteria |
