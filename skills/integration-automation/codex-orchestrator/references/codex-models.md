# Codex CLI Model Reference

Last updated: 2026-07-09

## Current Models

### GPT-5.6 Family

| Model | ID | Released | ChatGPT Auth | API Key | Description |
|-------|----|----------|:---:|:---:|-------------|
| **GPT-5.6 Sol** | `gpt-5.6-sol` | Jul 9, 2026 | **Yes** (Plus+) | Yes | New flagship. Complex reasoning, agentic workflows, coding, cybersecurity. Supports `max` reasoning effort and `ultra` mode (subagent-driven). Default for all coding/planning profiles. |
| **GPT-5.6 Terra** | `gpt-5.6-terra` | Jul 9, 2026 | **Yes** (all tiers) | Yes | Balanced everyday model. GPT-5.5-class performance at half the cost. Default for Free/Go ChatGPT users in Codex. |
| **GPT-5.6 Luna** | `gpt-5.6-luna` | Jul 9, 2026 | **Yes** (Plus+) | Yes | Fastest and most cost-efficient. Chatbots, classification, real-time responses, high-throughput pipelines. |

> **ChatGPT account tiers:** Free and Go users get **Terra only** in ChatGPT Work and Codex. Plus, Pro, Business, and Enterprise users can select Sol, Terra, or Luna. All models available with `OPENAI_API_KEY`.

> **API alias:** `gpt-5.6` routes to **Sol**, not Terra or Luna. Always use the full model ID (`gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna`) to avoid ambiguity.

> **New capabilities:** GPT-5.6 introduces `max` reasoning effort (above `high`) and `ultra` mode, which coordinates multiple subagents across parallel workstreams for complex tasks. Ultra is enabled via `--reasoning ultra` or `model_reasoning_effort = "ultra"` in config — Sol only.

> **Sol Fast pricing:** Sol Fast is the same model ID (`gpt-5.6-sol`) accessed at a higher throughput tier (up to 750 tokens/sec) with separate pricing ($12.50/$75.00 per M tokens). Availability depends on API plan tier.

#### GPT-5.6 Pricing

| Model | Input | Output | Cached Input |
|-------|-------|--------|-------------|
| Sol | $5.00/M | $30.00/M | $0.50/M |
| Sol Fast | $12.50/M | $75.00/M | — |
| Terra | $2.50/M | $15.00/M | $0.25/M |
| Luna | $1.00/M | $6.00/M | $0.10/M |

Long-context pricing (all tiers including Sol): 2x the short-context input/output rates.

### GPT-5.5 Family

| Model | ID | Released | ChatGPT Auth | API Key | Description |
|-------|----|----------|:---:|:---:|-------------|
| **GPT-5.5** | `gpt-5.5` | Apr 23, 2026 | **Yes** | Yes | Previous flagship. 2M context, agentic workflows, more token-efficient than 5.4. |
| **GPT-5.5 Pro** | `gpt-5.5-pro` | Apr 23, 2026 | **No** | Yes | Iterative research partner variant. Deeper reasoning. Pro/Business/Enterprise + API key. |
| **GPT-5 Mini** | `gpt-5-mini` | Mar 2026 | **No** | Yes | Cost-optimized. Requires API key auth. |
| **GPT-5 Nano** | `gpt-5-nano` | Mar 2026 | **No** | Yes | High-throughput. Requires API key auth. |

> **ChatGPT account limitation:** `gpt-5.5` and legacy models (`gpt-5.4`, `gpt-5.3-codex`, `gpt-5.2`) work with ChatGPT-authenticated Codex sessions. GPT-5.6 models are also available via ChatGPT auth (see above). `gpt-5.5-pro`, `gpt-5-mini`, and `gpt-5-nano` require `OPENAI_API_KEY` (API billing).

> **API pricing:** GPT-5.5 is priced at approximately 2x GPT-5.4's per-token rate. GPT-5.5 Pro is higher still. However, GPT-5.5 uses significantly fewer tokens to complete equivalent tasks, partially offsetting the price increase.

## Previous Generation

These models still work but are superseded by the GPT-5.5+ families.

| Model | ID | Released | Description |
|-------|----|----------|-------------|
| **GPT-5.4** | `gpt-5.4` | Mar 2026 | Previous flagship. 1M+ context, native compaction. |
| **GPT-5.4 Pro** | `gpt-5.4-pro` | Mar 2026 | Previous deeper reasoning variant. |
| **GPT-5.3-Codex** | `gpt-5.3-codex` | Feb 5, 2026 | Previous coding SOTA. 25% faster than 5.2. SWE-Bench Pro 56.8%. |
| **GPT-5.3-Codex Spark** | `gpt-5.3-codex-spark` | Feb 5, 2026 | Lightweight variant of 5.3. Near-instant responses. Pro subscribers only. |
| **GPT-5.2** | `gpt-5.2` | Dec 2025 | Deeper single-pass reasoning. |

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
| Max | `max` | Deepest reasoning. GPT-5.6 Sol only. Use for the hardest problems. |

> **Legacy level:** `xhigh` from the GPT-5.3-Codex era still works but `high` on GPT-5.5+ achieves equivalent depth.

**Model compatibility:** Reasoning effort is supported on GPT-5.x+ and o-series models only. GPT-4.x models (gpt-4.1, gpt-4o, etc.) reject the parameter.

Source: [Codex Config Reference](https://developers.openai.com/codex/config-reference) — `model_reasoning_effort` key.

### How to Set Reasoning Effort

In `~/.codex/config.toml`:

```toml
model = "gpt-5.6-sol"
model_reasoning_effort = "high"
```

Per-invocation via codex-orchestrator:

```bash
codex-exec.sh builder "task" --reasoning max
codex-exec.sh planner "task" --reasoning high
```

Raw Codex CLI:

```bash
codex --config model_reasoning_effort='"max"'
codex -c model_reasoning_effort='"max"'
```

### Plan Mode Reasoning

Codex has a separate `plan_mode_reasoning_effort` config key. When unset, Plan mode defaults to `medium`. This is independent of `model_reasoning_effort`.

```toml
plan_mode_reasoning_effort = "high"
```

## Configuration

Default model is set in `~/.codex/config.toml`:

```toml
model = "gpt-5.6-sol"
```

Override per-invocation with `--model` and `--reasoning`:

```bash
codex exec --model gpt-5.6-luna "Quick review of auth.ts"
codex exec --model gpt-5.6-sol "Design the caching architecture" --reasoning max
codex exec --model gpt-5.5 "Use previous flagship for comparison"
```

Both `codex-orchestrator` and `codex-cto` skills pass `--model` and `-c model_reasoning_effort` through to `codex exec`. Any model ID that Codex CLI accepts will work.

## Selection Guide

| Task | Model (ChatGPT auth) | Model (API key) | Reasoning | Why |
|------|---------------------|-----------------|-----------|-----|
| Coding subagents (builder, reviewer, debugger, etc.) | `gpt-5.6-sol` | `gpt-5.6-sol` | `high` | Flagship agentic coding, strongest single-agent performance |
| Planning subagents (planner, architect) | `gpt-5.6-sol` | `gpt-5.6-sol` | `high` | Complex reasoning, long-horizon planning |
| Research subagent (researcher) | `gpt-5.6-sol` | `gpt-5.6-sol` | `medium` | Large context analysis, speed/quality balance |
| Adjudication subagent (adjudicator) | `gpt-5.6-sol` | `gpt-5.6-sol` | `high` | Rival-hypothesis weighing, evidence ranking |
| Quick reads, fast iteration | `gpt-5.6-terra` | `gpt-5.6-luna` | `medium` | ChatGPT: balanced tier; API: cheapest option |
| Chat (open-ended) | `gpt-5.6-terra` | `gpt-5.6-terra` | `medium` | Everyday conversation, cost-efficient |
| CTO planning (codex-cto) | `gpt-5.6-sol` | `gpt-5.6-sol` | `high` | Architectural decomposition |
| CTO review (codex-cto) | `gpt-5.6-sol` | `gpt-5.6-sol` | `high` | Diff analysis and acceptance criteria |
| Hardest problems (complex bugs, architecture) | `gpt-5.6-sol` | `gpt-5.6-sol` | `max` | Maximum reasoning depth |
