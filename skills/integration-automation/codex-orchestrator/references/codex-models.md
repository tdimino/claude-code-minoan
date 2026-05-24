# Codex CLI Model Reference

Last updated: 2026-04-23

## Current Models

| Model | ID | Released | ChatGPT Auth | API Key | Description |
|-------|----|----------|:---:|:---:|-------------|
| **GPT-5.5** | `gpt-5.5` | Apr 23, 2026 | **Yes** | Yes | New flagship. 2M context, agentic workflows, more token-efficient than 5.4. Default for all profiles. |
| **GPT-5.5 Pro** | `gpt-5.5-pro` | Apr 23, 2026 | **No** | Yes | Iterative research partner variant. Deeper reasoning. Pro/Business/Enterprise + API key. |
| **GPT-5 Mini** | `gpt-5-mini` | Mar 2026 | **No** | Yes | Cost-optimized. Requires API key auth. |
| **GPT-5 Nano** | `gpt-5-nano` | Mar 2026 | **No** | Yes | High-throughput. Requires API key auth. |

> **ChatGPT account limitation:** Only `gpt-5.5` and legacy models (`gpt-5.4`, `gpt-5.3-codex`, `gpt-5.2`) work with ChatGPT-authenticated Codex sessions. All other models require `OPENAI_API_KEY` (API billing). This is by design—confirmed via [GitHub #2051](https://github.com/openai/codex/issues/2051) and OpenAI's Codex models page.

> **ChatGPT ecosystem models vs. Codex CLI models:** GPT-5.3 Instant and GPT-5.4 Thinking are ChatGPT-app models (available in the ChatGPT web/mobile app). They are **not** Codex CLI model IDs—you cannot pass them to `--model`. Codex CLI model IDs are listed in the table above.

> **API pricing:** GPT-5.5 is priced at approximately 2x GPT-5.4's per-token rate. GPT-5.5 Pro is higher still. However, GPT-5.5 uses significantly fewer tokens to complete equivalent tasks, partially offsetting the price increase.

## Previous Generation

These models still work but are superseded by the GPT-5.5 family.

| Model | ID | Released | Description |
|-------|----|----------|-------------|
| **GPT-5.4** | `gpt-5.4` | Mar 2026 | Previous flagship. 1M+ context, native compaction. |
| **GPT-5.4 Pro** | `gpt-5.4-pro` | Mar 2026 | Previous deeper reasoning variant. |
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

**Model compatibility:** Reasoning effort is supported on GPT-5.x and o-series models only. GPT-4.x models (gpt-4.1, gpt-4o, etc.) reject the parameter.

Source: [Codex Config Reference](https://developers.openai.com/codex/config-reference) — `model_reasoning_effort` key.

**Note:** GPT-5.5's base reasoning is deeper than GPT-5.4's. `high` remains the recommended default for most tasks.

### How to Set Reasoning Effort

In `~/.codex/config.toml`:

```toml
model = "gpt-5.5"
model_reasoning_effort = "high"
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
model = "gpt-5.5"
```

Override per-invocation with `--model` and `--reasoning`:

```bash
codex exec --model gpt-5-mini "Quick review of auth.ts"
codex exec --model gpt-5.5-pro "Design the caching architecture"
```

Both `codex-orchestrator` and `codex-cto` skills pass `--model` and `-c model_reasoning_effort` through to `codex exec`. Any model ID that Codex CLI accepts will work.

## Selection Guide

| Task | Model (ChatGPT auth) | Model (API key) | Reasoning | Why |
|------|---------------------|-----------------|-----------|-----|
| Coding subagents (builder, reviewer, debugger, etc.) | `gpt-5.5` | `gpt-5.5` | `high` | Agentic coding, 2M context, more token-efficient |
| Planning subagents (planner, architect) | `gpt-5.5` | `gpt-5.5-pro` | `high` | ChatGPT: best available; API: deepest reasoning |
| Research subagent (researcher) | `gpt-5.5` | `gpt-5.5` | `medium` | 2M context for codebase analysis |
| Quick reads, fast iteration | `gpt-5.4` | `gpt-5-mini` | `medium` | ChatGPT: previous flagship; API: cost-optimized |
| CTO planning (codex-cto) | `gpt-5.5` | `gpt-5.5-pro` | `high` | Architectural decomposition |
| CTO review (codex-cto) | `gpt-5.5` | `gpt-5.5` | `high` | Diff analysis and acceptance criteria |
