# Claude Usage

Ground-truth token usage and cost reporting for Claude Code sessions.

**Last updated:** 2026-02-21

**Reflects:** Empirical accuracy investigation of ccusage v18.0.5 (10.6k stars) conducted on 2026-02-20, which revealed the community standard tool undercounts output tokens by 77-94% for heavy Agent Teams users. This skill was built as a direct replacement, parsing every JSONL file—parent sessions and subagent sidechains—to produce correct numbers.

---

## Why This Was Needed

ccusage is the standard community tool for Claude Code usage tracking. On 2026-02-20, empirical testing against raw JSONL files exposed three compounding bugs:

| Source | Output Tokens | Notes |
|--------|-------------|-------|
| Raw JSONL (all files) | 1,076,691 | Ground truth |
| Raw JSONL (date-filtered) | 412,987 | Properly filtered |
| ccusage --timezone UTC | 93,960 | 77% undercount |
| ccusage default | 62,375 | 94% undercount |

**Three root causes:**

1. **Ignores subagent files.** Claude Code stores Agent Teams sidechains at `{session-uuid}/subagents/{agent-id}.jsonl`. ccusage only reads parent session files—132 sidechain files missed on a typical heavy day.

2. **Timezone confusion.** JSONL entry timestamps are UTC. ccusage applies `--since`/`--until` date filters in local time against UTC timestamps, silently dropping entries near midnight boundaries when UTC date differs from local date.

3. **Drops entries in parent files.** Even when forcing `--timezone UTC` to eliminate the boundary issue, ccusage reports only 94K of 413K actual output tokens from parent files alone—a 77% undercount with no explanation in the source.

These bugs compound. A user running Agent Teams with the default timezone sees 94% of their output tokens vanish from the report.

---

## Structure

```
claude-usage/
  SKILL.md                    # Skill definition (loaded by Claude Code)
  README.md                   # This file
  scripts/
    claude_usage.py           # Token usage CLI — Python 3.9+, stdlib only
    claude_usage_report.py    # PDF report generator — requires Playwright
```

---

## Usage

```bash
# Today's usage (default)
python3 ~/.claude/skills/claude-usage/scripts/claude_usage.py

# Last 7 days, broken down by day
python3 ~/.claude/skills/claude-usage/scripts/claude_usage.py --since 7d

# Weekly breakdown for the past month
python3 ~/.claude/skills/claude-usage/scripts/claude_usage.py --by week --since 30d

# Per-model breakdown
python3 ~/.claude/skills/claude-usage/scripts/claude_usage.py --by model --since 7d

# Per-session with human-readable summaries
python3 ~/.claude/skills/claude-usage/scripts/claude_usage.py --by session --since 1d

# Per-project breakdown
python3 ~/.claude/skills/claude-usage/scripts/claude_usage.py --by project --since 7d

# Filter to one project
python3 ~/.claude/skills/claude-usage/scripts/claude_usage.py --project Thera --since 30d

# Custom date range
python3 ~/.claude/skills/claude-usage/scripts/claude_usage.py --since 2026-02-01 --until 2026-02-28

# JSON output (pipe to jq)
python3 ~/.claude/skills/claude-usage/scripts/claude_usage.py --since 7d --json | jq '.grand_total'

# CSV output
python3 ~/.claude/skills/claude-usage/scripts/claude_usage.py --since 7d --csv

# Compare against ccusage (shows delta)
python3 ~/.claude/skills/claude-usage/scripts/claude_usage.py --compare
```

---

## How It Works

**JSONL discovery** — Walks `~/.claude/projects/` to find:
- Parent sessions: `{encoded-path}/{session-uuid}.jsonl`
- Subagent sidechains: `{encoded-path}/{session-uuid}/subagents/{agent-id}.jsonl`

Uses `Path.iterdir()` (not `rglob`) to avoid descending into unrelated `tool-results/` directories.

**Streaming parser** — Reads line-by-line with O(1) memory, handling files exceeding 300MB. Filters to `type == "assistant"` entries, skips synthetic models and all-zero billing errors.

**Timezone-correct filtering** — Converts UTC timestamps to local timezone (or `--tz` override) before applying date filters. Anchors `--since Nd` to midnight, not rolling 24h.

**Project path decoding** — Claude Code encodes `/Users/tom/Desktop/Thera-Knossos` as `-Users-tom-Desktop-Thera-Knossos`. Reversal is ambiguous when directories contain hyphens. The script uses greedy filesystem matching (longest segment first) to decode correctly.

---

## Output Columns

| Column | Description |
|--------|-------------|
| Input | Prompt tokens (charged at input rate) |
| Output | Response tokens (most expensive category) |
| CacheW | Cache write tokens (`cache_creation_input_tokens`) |
| CacheR | Cache read tokens (significantly cheaper than input) |
| Total | Sum of all four token types |
| Cost | Estimated USD from the hardcoded pricing table |

---

## Aggregation Modes (`--by`)

| Mode | Groups by | Example key |
|------|-----------|-------------|
| `day` (default) | Calendar date in local timezone | `2026-02-20` |
| `week` | ISO week number | `2026-W08` |
| `month` | Month | `2026-02` |
| `session` | Session UUID (resolved to summary) | `8a6c801a  Working on Claudicle...` |
| `model` | Model name | `claude-opus-4-6` |
| `project` | Project directory (decoded to path) | `~/Desktop/Programming` |

---

## Pricing Table

Hardcoded in the `PRICING` dict at the top of `claude_usage.py`. Update when Anthropic changes rates. Keys are model name substrings matched most-specific-first.

| Model | Input | Output | Cache Write | Cache Read |
|-------|-------|--------|-------------|------------|
| Opus 4 | $15.00 | $75.00 | $18.75 | $1.50 |
| Sonnet 4 | $3.00 | $15.00 | $3.75 | $0.30 |
| Haiku 4 | $0.80 | $4.00 | $1.00 | $0.08 |

Unknown models fall back to Sonnet rates with a stderr warning.

---

## PDF Reports

`claude_usage_report.py` generates a dark editorial PDF with:
- **Crimson Pro + JetBrains Mono + Inter** typography
- **Gold Minoan accent** system on dark background
- **5-metric header**: Total Tokens, Input, Output, Est. Cost, Files Scanned
- **Model distribution**: Color-coded stacked bar showing token share per model (Opus = gold, Sonnet = steel, Haiku = sage)
- **Daily cost chart**: Horizontal bar chart with per-day cost
- **Token composition**: Input/Output/CacheW/CacheR stacked bars
- **Detailed table**: Full breakdown with grand total row

```bash
# PDF report (default: last 30 days)
python3 ~/.claude/skills/claude-usage/scripts/claude_usage_report.py --since 30d

# Custom output path
python3 ~/.claude/skills/claude-usage/scripts/claude_usage_report.py --since 30d -o ~/Desktop/feb-usage.pdf

# HTML only (no Playwright needed)
python3 ~/.claude/skills/claude-usage/scripts/claude_usage_report.py --since 7d --html
```

Uses Playwright/Chromium for pixel-perfect CSS rendering—same engine as the Aldea Slide Deck skill. Migrated from weasyprint due to persistent `@page` margin bugs.

---

## Requirements

- Python 3.9+ (uses `zoneinfo` module)
- `claude_usage.py`: No external dependencies—stdlib only
- `claude_usage_report.py`: Requires Playwright (`uv pip install --system playwright && playwright install chromium`)

---

## Caveats

- Cost is estimated from the pricing table. Anthropic billing may differ due to batch discounts or promotional pricing.
- Cache write and cache read tokens are reported separately. Some accounting schemes treat cache writes differently.
- Synthetic entries (`model: "<synthetic>"`) and billing error entries (all-zero token counts) are automatically filtered.
- Session names resolve from `sessions-index.json`. Sessions not yet indexed show raw UUIDs.

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)—curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/claude-usage ~/.claude/skills/
```
