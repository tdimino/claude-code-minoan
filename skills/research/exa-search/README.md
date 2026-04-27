# Exa Search

Neural web search, content extraction, similar page discovery, AI-powered research, and async pro research via the [Exa API](https://exa.ai). Five specialized Python scripts covering all Exa endpoints with token-efficient search patterns. Synced to Exa API v1.2.0 (April 2026).

## Prerequisites

```bash
export EXA_API_KEY=your-key-here  # https://dashboard.exa.ai
```

## Scripts

| Script | Endpoint | Purpose |
|--------|----------|---------|
| `exa_search.py` | `/search` | Neural web search with 6 search types, 9 categories, structured output |
| `exa_contents.py` | `/contents` | Extract content from known URLs with summaries and highlights |
| `exa_similar.py` | `/findSimilar` | Find pages semantically similar to a given URL |
| `exa_research.py` | `/answer` | AI-powered research with citations |
| `exa_research_async.py` | `/research` | Async pro research with structured output |

## Quick Start

### Search

```bash
# Basic search
python3 scripts/exa_search.py "AI agent frameworks" -n 10

# Academic papers
python3 scripts/exa_search.py "transformer architecture" --category "research paper" -n 20

# Domain-filtered, recent content
python3 scripts/exa_search.py "React hooks" --domains react.dev --after 2025-01-01

# Titles only (cheapest)
python3 scripts/exa_search.py "query" -n 20 --no-text
```

### Exa Deep (Structured Search)

Deep and deep-reasoning searches support structured JSON output with field-level grounding citations.

```bash
# Quick factual answer
python3 scripts/exa_search.py "Who is the CEO of Stripe?" --deep --text-output "Short answer"

# Structured company research with preset schema
python3 scripts/exa_search.py "Top AI startups 2025" --deep-reasoning --schema-preset company

# Custom JSON schema
python3 scripts/exa_search.py "SEC filings Tesla" --deep-reasoning \
  --output-schema '{"filings": [{"date": "string", "type": "string", "key_findings": "string"}]}'

# Schema from file
python3 scripts/exa_search.py "Compare cloud providers" --deep --schema-file ~/schemas/comparison.json
```

**Preset schemas:** `company`, `paper-survey`, `competitor-analysis`, `person`, `news-digest`

**Grounding output** shows per-field citations with confidence: `[H]`igh, `[M]`edium, `[L]`ow.

### Content Extraction

```bash
# Extract with highlights
python3 scripts/exa_contents.py "https://arxiv.org/abs/2307.06435" --highlights --max-chars 3000

# Multiple URLs with summaries
python3 scripts/exa_contents.py URL1 URL2 --summary "Key findings"

# Fresh content (maxAgeHours preferred over deprecated livecrawl)
python3 scripts/exa_contents.py "https://news.ycombinator.com" --max-age-hours 0

# Verbosity and section filtering (requires --max-age-hours 0)
python3 scripts/exa_contents.py URL --max-age-hours 0 --verbosity compact --exclude-sections navigation footer

# Cost breakdown
python3 scripts/exa_contents.py URL --cost
```

### Similar Pages

```bash
# Find competitors
python3 scripts/exa_similar.py "https://stripe.com" --category company --exclude-source

# Related papers
python3 scripts/exa_similar.py "https://arxiv.org/abs/1706.03762" -n 15
```

### Research

```bash
# Quick research with citations
python3 scripts/exa_research.py "How does RAG work?" --sources --markdown

# Structured answer output
python3 scripts/exa_research.py "Compare top 3 JS frameworks" \
  --output-schema '{"frameworks": [{"name": "string", "pros": ["string"], "cons": ["string"]}]}'

# Async pro research (longer, deeper)
python3 scripts/exa_research_async.py "Compare AI agent frameworks" --pro --wait
```

## Search Types

| Flag | Latency | Cost/1k | Use Case |
|------|---------|---------|----------|
| `--instant` | <150ms | Cheapest | Real-time lookups |
| `--fast` | ~500ms | Low | Quick checks |
| (default) | auto | Medium | General search |
| `--deep` | 4-12s | $12 | Comprehensive research |
| `--deep-reasoning` | 12-50s | $15 | Maximum depth with LLM reasoning |

## Content Freshness & Filtering

Control content age, verbosity, and page sections across search, contents, and similar scripts.

```bash
# Always livecrawl (freshest content)
python3 scripts/exa_search.py "breaking news" --max-age-hours 0

# Compact text, body only
python3 scripts/exa_search.py "API docs" --max-age-hours 0 --verbosity compact --include-sections body

# Highlights by character count (preferred over deprecated numSentences)
python3 scripts/exa_search.py "query" --highlights --highlights-max-chars 500
```

**Valid sections:** header, navigation, banner, body, sidebar, footer, metadata

**Note:** `--verbosity` and `--include/exclude-sections` require `--max-age-hours 0` (livecrawl).

## Token-Efficient Search Pattern

Search cheaply, filter, extract selectively, then reason.

```bash
# 1. Titles only (cheapest)
python3 scripts/exa_search.py "query" -n 20 --no-text

# 2. Pick 3-5 best URLs from titles

# 3. Extract only those with bounded content
python3 scripts/exa_contents.py URL1 URL2 --highlights --max-chars 3000
```

### API-Level Filters (Free)

```bash
--must-include "term"          # Required string
--must-exclude "term"          # Excluded string
--domains site1.com site2.com  # Restrict to domains
--category "research paper"    # Filter by type
--after 2025-01-01             # Date range
```

## Directory Structure

```
exa-search/
├── README.md
├── SKILL.md                        # Claude Code skill definition
├── codex-agent-guide.md            # Codex CLI agent integration guide
├── references/
│   └── exa-scripts-reference.md    # Full parameter reference, costs, examples
└── scripts/
    ├── exa_search.py               # Neural search (6 types, structured output)
    ├── exa_contents.py             # URL content extraction
    ├── exa_similar.py              # Similar page discovery
    ├── exa_research.py             # AI research with citations
    ├── exa_research_async.py       # Async pro research
    └── test_exa.py                 # Test suite
```

## Testing

```bash
python3 scripts/test_exa.py --quick            # Offline validation (6 tests)
python3 scripts/test_exa.py                     # Full suite (API required)
python3 scripts/test_exa.py --endpoint search   # Test specific endpoint
```

## References

- [Exa API Documentation](https://docs.exa.ai)
- [Exa Deep Blog Post](https://exa.ai/blog/exa-deep)
- [Exa Dashboard](https://dashboard.exa.ai)
