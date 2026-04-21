# OpenRouter Usage

Query OpenRouter API costs, credits, and usage breakdown by model, provider, and date. Single script, no dependencies beyond `requests`.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

OpenRouter's dashboard shows aggregate spend, but doesn't make it easy to break down costs by model, provider, or date from the command line. This skill queries the analytics API and produces human-readable reports, CSV exports, or raw JSON for accounting and cost auditing.

---

## Structure

```
openrouter-usage/
  SKILL.md                          # Full usage guide
  README.md                         # This file
  scripts/
    openrouter_usage.py             # Usage report generator
```

---

## Usage

```bash
# Full 30-day summary with credits balance
python3 openrouter_usage.py

# Filter to a single date
python3 openrouter_usage.py --date 2026-02-01

# Export as CSV
python3 openrouter_usage.py --csv

# Raw JSON (for piping to jq)
python3 openrouter_usage.py --json

# Skip credits lookup (activity only)
python3 openrouter_usage.py --no-credits
```

Default output includes credits balance, spend by model (with token counts), spend by provider, and daily spend with a visual bar chart.

---

## Setup

### Prerequisites

- Python 3.9+
- `pip install requests`
- `OPENROUTER_API_KEY` in environment or `.env` file
- **Must be a Management key** (create at https://openrouter.ai/settings/management-keys)---regular provisioning keys return 401/403 on analytics endpoints

---

## Related Skills

- **`claude-usage`**: Similar cost tracking for Anthropic API usage.

---

## Requirements

- Python 3.9+
- `requests`
- OpenRouter Management API key

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/core-development/openrouter-usage ~/.claude/skills/
```
