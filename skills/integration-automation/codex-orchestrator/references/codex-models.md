# Codex CLI Model Reference

Last updated: 2026-02-21

## Current Models

| Model | ID | Released | Description |
|-------|----|----------|-------------|
| **GPT-5.3-Codex** | `gpt-5.3-codex` | Feb 5, 2026 | Latest generation. 25% faster than 5.2. Self-bootstrapped (trained partly on its own output). SOTA on SWE-Bench Pro. Default model in `~/.codex/config.toml`. |
| **GPT-5.3-Codex Spark** | `gpt-5.3-codex-spark` | Feb 5, 2026 | Lightweight variant of 5.3. Near-instant responses. Pro subscribers only. Ideal for quick reads, small reviews, fast iteration. |
| **GPT-5.2-Codex** | `gpt-5.2-codex` | Dec 2025 | Previous generation. Still fully supported. Use when 5.3 exhibits regressions on specific tasks or when reproducibility with older results matters. |

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

## Configuration

Default model is set in `~/.codex/config.toml`:

```toml
model = "gpt-5.3-codex"
```

Override per-invocation with `--model`:

```bash
codex exec --model gpt-5.3-codex-spark "Quick review of auth.ts"
codex exec --model gpt-5.2-codex "Compare against previous results"
```

Both `codex-orchestrator` and `codex-cto` skills pass `--model` through to `codex exec`. Any model ID that Codex CLI accepts will work.

## Selection Guide

| Task | Recommended Model | Why |
|------|-------------------|-----|
| Default for all tasks | `gpt-5.3-codex` | Best balance of speed and capability |
| Quick reads, fast iteration | `gpt-5.3-codex-spark` | Near-instant, low cost |
| Reproducing older results | `gpt-5.2-codex` | Same model that produced original output |
| CTO planning (codex-cto) | `gpt-5.3-codex` | Architectural reasoning benefits from full capability |
| CTO review (codex-cto) | `gpt-5.3-codex` | Diff analysis needs full capability |
| One-shot subagent (codex-orchestrator) | `gpt-5.3-codex` | Default |
| Quick researcher query | `gpt-5.3-codex-spark` | Read-only, speed matters |
