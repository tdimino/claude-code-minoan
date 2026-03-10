# Handoff Model Evaluation

Rigorous comparison of LLM models for `precompact-handoff.py`—the hook that summarizes session transcripts into structured YAML handoffs via OpenRouter.

**Date**: 2026-03-09
**Framework**: `scripts/eval-handoff-models.py` (worldwarwatcher repo)
**Judge**: Claude Sonnet 4 (`anthropic/claude-sonnet-4`) via OpenRouter

## Current Production Config

```python
model = "qwen/qwen3-235b-a22b-2507"  # switched from gemini-2.5-flash-lite on 2026-03-09
prompt = "generic"  # lines 49-61 of precompact-handoff.py
timeout = 180  # seconds (Qwen needs up to 132s on heavy sessions)
```

Cost: ~$0.008/call. Fires on PreCompact + SessionEnd.

## Why This Evaluation

Gemini Flash Lite ($0.075/$0.40 per 1M input/output) works but may be 4-10x more expensive than alternatives that produce equivalent quality. Before switching models, we needed rigorous comparison—not just "does it parse?" but "does it preserve the soul of the session?"

## Test Matrix

**4 candidate models** (1 eliminated early):

| Model | Input $/M | Output $/M | Context | Status |
|-------|-----------|------------|---------|--------|
| `google/gemini-2.5-flash-lite` | $0.075 | $0.40 | 1M | **Winner** |
| `qwen/qwen3-235b-a22b-2507` | $0.07 | $0.10 | 262K | Runner-up |
| `google/gemma-3-27b-it` | $0.05 | $0.11 | 128K | Eliminated (unreliable) |
| `mistralai/mistral-nemo` | $0.018 | $0.04 | 131K | Eliminated (0% YAML) |

**3 prompt variants** per model:
- **Generic**: Production prompt (same for all models)
- **Optimized**: Per-model instruction format tuning (`/no_think` for Qwen, `<start_of_turn>` for Gemma, etc.)
- **JSON-then-Convert**: Ask for JSON output, convert to YAML downstream

**5 real sessions** spanning trivial to heavy complexity:

| Session | Project | Complexity | Transcript Lines |
|---------|---------|------------|-----------------|
| `a467b8a5` | Programming | Trivial | 37 |
| `529a0eea` | Desktop | Simple | 77 |
| `73e757ab` | Programming | Medium | 1,178 |
| `2ed9fa81` | worldwarwatcher | Complex | 6,940 |
| `685a1d77` | worldwarwatcher | Heavy | 14,974 |

**Total**: 3 models × 3 prompts × 5 sessions = **45 generation calls** + **136 judge calls** (4 dimensions × 34 valid entries).

## Scoring System

### Mechanical (4 dimensions, code-based)

| Dimension | How |
|-----------|-----|
| YAML Validity | `yaml.safe_load()` succeeds AND result is dict |
| Field Completeness | `len(fields_present) / 5` — objective, completed, decisions, blockers, next_steps |
| Latency | Wall-clock seconds |
| Cost | `(prompt_tokens × input_rate + completion_tokens × output_rate) / 1M` |

### Craft (4 dimensions, LLM-as-Judge via Claude Sonnet 4)

Each scored 1-5 with chain-of-thought critique. Judge sees candidate output, reference handoff, and transcript tail.

| Dimension | Score 5 | Score 1 |
|-----------|---------|---------|
| **Signal Density** | Every sentence carries unique, non-obvious technical detail | Mostly meta-commentary and filler |
| **Narrative Coherence** | Cold-start reader understands the session arc | Fields contradict or are self-referential |
| **Actionability** | next_steps have file paths and commands | "Continue with planned tasks" |
| **Voice Preservation** | Uses project vocabulary (daimon, PHOSPHOR VIGIL, Mazkir) | Completely generic |

### Composite (0-100)

| Component | Weight |
|-----------|--------|
| YAML validity | 15% |
| Field completeness | 10% |
| Signal density | 20% |
| Narrative coherence | 20% |
| Actionability | 20% |
| Voice preservation | 15% |

## Results

### YAML Reliability

The most critical metric—a failed parse means lost session context.

| Model | Generic | Optimized | JSON | Total |
|-------|---------|-----------|------|-------|
| **Gemini Flash Lite** | **5/5** | 4/5 | **5/5** | 14/15 (93%) |
| **Qwen 3 235B** | **5/5** | **5/5** | **5/5** | **15/15 (100%)** |
| Gemma 3 27B | 2/5 | 1/5 | 2/5 | 5/15 (33%) |
| Mistral Nemo | 0/1 | 0/1 | 0/1 | 0/3 (0%) |

Gemma fails on all sessions beyond simple (medium, complex, heavy). Context overflow on heavy (128K limit hit at 138K tokens). Mistral Nemo can't produce valid YAML at all.

### Composite Scores (Generic Prompt—Production Config)

| Model | Trivial | Simple | Medium | Complex | Heavy | **Avg** |
|-------|---------|--------|--------|---------|-------|---------|
| **Gemini Flash Lite** | 92 | 100 | 100 | 100 | 80 | **94.4** |
| **Qwen 3 235B** | 96 | 100 | 96 | 92 | 100 | **96.8** |
| Gemma 3 27B | 70 | 96 | FAIL | FAIL | FAIL | 83.0* |

*Gemma average based on 2 valid entries only.

### Craft Dimension Breakdown (Generic Prompt)

| Model | Session | Signal | Narrative | Action | Voice | Composite |
|-------|---------|--------|-----------|--------|-------|-----------|
| Gemini | trivial | 4 | 5 | 4 | 5 | 92 |
| Gemini | simple | 5 | 5 | 5 | 5 | 100 |
| Gemini | medium | 5 | 5 | 5 | 5 | 100 |
| Gemini | complex | 5 | 5 | 5 | 5 | 100 |
| Gemini | heavy | 3 | 5 | 2 | 5 | 80 |
| Qwen | trivial | 5 | 5 | 4 | 5 | 96 |
| Qwen | simple | 5 | 5 | 5 | 5 | 100 |
| Qwen | medium | 5 | 5 | 4 | 5 | 96 |
| Qwen | complex | 4 | 5 | 4 | 5 | 92 |
| Qwen | heavy | 5 | 5 | 5 | 5 | 100 |

Key finding: Qwen outperforms on **heavy sessions** (100 vs 80)—the sessions that matter most for handoff quality. Gemini's heavy-session weakness is in signal density (3/5) and actionability (2/5).

### Latency

| Model | Trivial | Simple | Medium | Complex | Heavy | **Avg** |
|-------|---------|--------|--------|---------|-------|---------|
| **Gemini Flash Lite** | 2.2s | 2.9s | 9.6s | 9.7s | 10.5s | **7.0s** |
| Qwen 3 235B | 10.9s | 47.8s | 78.7s | 20.1s | 132.5s | 58.0s |

Gemini is **8x faster**. This matters because the handoff hook runs during PreCompact, adding to user wait time.

### Cost

| Model | Avg Cost/Call | Cost per 1,000 Calls |
|-------|--------------|---------------------|
| Gemma 3 27B | $0.00264 | $2.64 |
| Qwen 3 235B | $0.00776 | $7.76 |
| Gemini Flash Lite | $0.00875 | $8.75 |

Qwen is slightly cheaper than Gemini per call, but the difference is negligible (~$1/1000 calls).

### All Prompt Variants (Top 20 by Composite)

| # | Model | Prompt | Session | S | N | A | V | Composite | Latency | Cost |
|---|-------|--------|---------|---|---|---|---|-----------|---------|------|
| 1 | Gemma 27B | optimized | simple | 5 | 5 | 5 | 5 | 100.0 | 27.7s | $0.003 |
| 2 | Gemma 27B | json | simple | 5 | 5 | 5 | 5 | 100.0 | 33.3s | $0.004 |
| 3 | Qwen 235B | generic | simple | 5 | 5 | 5 | 5 | 100.0 | 47.8s | $0.005 |
| 4 | Qwen 235B | optimized | simple | 5 | 5 | 5 | 5 | 100.0 | 20.5s | $0.005 |
| 5 | Qwen 235B | json | simple | 5 | 5 | 5 | 5 | 100.0 | 90.7s | $0.005 |
| 6 | Gemini FL | all 3 | simple | 5 | 5 | 5 | 5 | 100.0 | 2.9-4.1s | $0.005 |
| 7 | Qwen 235B | json | medium | 5 | 5 | 5 | 5 | 100.0 | 88.5s | $0.009 |
| 8 | Qwen 235B | json | complex | 5 | 5 | 5 | 5 | 100.0 | 21.8s | $0.010 |
| 9 | Gemini FL | all 3 | medium | 5 | 5 | 4-5 | 5 | 96-100 | 9.5-11s | $0.011 |
| 10 | Gemini FL | all 3 | complex | 5 | 5 | 5 | 5 | 100.0 | 9.0-14.8s | $0.011 |
| 11 | Qwen 235B | generic | heavy | 5 | 5 | 5 | 5 | 100.0 | 132.5s | $0.014 |

## Failure Modes

| Model | Failure Type | Sessions Affected |
|-------|-------------|-------------------|
| Gemma 27B | `YAML parsed as NoneType` | medium, complex (all prompts) |
| Gemma 27B | Context overflow (130K limit) | heavy (all prompts) |
| Gemma 27B | Backtick in YAML value | trivial (optimized prompt) |
| Gemini FL | Backtick in YAML value | heavy (optimized prompt only) |
| Mistral Nemo | Empty YAML / parse errors | all sessions tested |

The backtick failures (`` ` `` inside YAML values) affect both Gemma and Gemini when using model-specific optimized prompts. The generic prompt avoids this.

## Recommendation

**Switched to `qwen/qwen3-235b-a22b-2507` with the generic prompt** (2026-03-09).

| Factor | Qwen 3 235B (chosen) | Gemini Flash Lite (previous) |
|--------|---------------------|------------------------------|
| Reliability (generic) | 5/5 (100%) | 5/5 (100%) |
| Avg composite | **96.8/100** | 94.4/100 |
| Avg latency | 58.0s | 7.0s |
| Avg cost/call | **$0.008** | $0.009 |
| Heavy session score | **100/100** | 80/100 |

**Why Qwen wins:**
1. **Heavy sessions are the ones that matter** — PreCompact fires when context is full, which means heavy transcripts. Qwen scores 100/100 vs Gemini's 80/100 on heavy sessions, with perfect actionability (5/5 vs 2/5).
2. **Latency is tolerable** — the 5-minute cooldown on `stop-handoff.py` means handoffs fire at most once every 5 minutes. 132s fits comfortably within that window.
3. **100% reliability across all prompt variants** — Gemini had one format failure (optimized prompt, heavy session). Qwen: zero failures.
4. **Slightly cheaper** — $0.008 vs $0.009 per call.
5. **Timeout bumped to 180s** — accommodates Qwen's worst-case latency (205s on JSON variant, 132s on generic).

## Reproduction

```bash
cd ~/Desktop/Programming/worldwarwatcher

# Full eval with craft scoring (~45 min, ~$2 in API costs)
uv run scripts/eval-handoff-models.py

# Mechanical only (fast, ~$0.50)
uv run scripts/eval-handoff-models.py --skip-judge

# Single model
uv run scripts/eval-handoff-models.py --models google/gemini-2.5-flash-lite

# Resume from cache
uv run scripts/eval-handoff-models.py --resume
```

Results cached to `scripts/eval-results/results-{timestamp}.json` and reports to `scripts/eval-results/handoff-eval-{timestamp}.md`.

## Files

| File | Location | Role |
|------|----------|------|
| `precompact-handoff.py` | `~/.claude/hooks/` | Production handoff hook |
| `stop-handoff.py` | `~/.claude/hooks/` | Throttled stop-event wrapper |
| `eval-handoff-models.py` | `worldwarwatcher/scripts/` | Evaluation framework |
| `eval-results/` | `worldwarwatcher/scripts/` | Cached results + reports |
