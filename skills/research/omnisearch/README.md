# Omnisearch

Unified web and social media search across 5 providers. Auto-routes queries to the best API, supports parallel multi-provider search with deduplication, AI-generated answers, and social media search.

## Providers

| Provider | Surface | Cost |
|----------|---------|------|
| **Brave** | Google SERP, news, freshness filtering, LLM Context API | $5/1k queries |
| **Tavily** | AI-synthesized answers with citations, content extraction | Free 1k/mo |
| **Xpoz** | Twitter/X, Reddit, Instagram search | Free 100k/mo |
| **Exa** | Neural/semantic search, research papers, similar pages | Per-query |
| **Firecrawl** | Search + scrape, site crawling | Per-page |

## Quick Start

```bash
# Auto-route to best provider
omnisearch.py "Iran oil sanctions"

# Force specific provider
omnisearch.py "query" --provider brave

# All web providers, merged + deduped
omnisearch.py "query" --parallel

# Twitter search
omnisearch.py "query" --social

# Reddit search
omnisearch.py "query" --social --platform reddit

# AI-generated answer
omnisearch.py "query" --answer

# News from all providers
omnisearch.py "query" --news --parallel
```

## Scripts

| Script | Purpose |
|--------|---------|
| `omnisearch.py` | Meta-router — auto-classifies and dispatches to best provider |
| `brave_search.py` | Brave web/news search with freshness filtering and LLM Context API |
| `tavily_search.py` | AI-optimized search with answers, topic modes, content extraction |
| `xpoz_search.py` | Social media search (Twitter, Reddit, Instagram) via Xpoz SDK |

## API Keys

Add to `~/.config/env/secrets.env` (or your preferred env file):

```bash
export BRAVE_API_KEY="..."      # https://api-dashboard.search.brave.com
export TAVILY_API_KEY="tvly-..."  # https://tavily.com (free tier)
export XPOZ_API_KEY="..."       # https://www.xpoz.ai
export EXA_API_KEY="..."        # https://dashboard.exa.ai (cross-skill)
export FIRECRAWL_API_KEY="..."  # https://firecrawl.dev (cross-skill)
```

All scripts gracefully error with a clear message when their key is missing. Any subset works.

## Dependencies

```bash
pip install requests xpoz  # xpoz requires Python 3.10+
```

Exa and Firecrawl scripts are optional cross-skill integrations — they call sibling skill scripts via subprocess.

## Token-Efficient Multi-Search

Search cheaply, filter, then extract selectively:

```bash
# Step 1: Titles/URLs only (cheapest)
omnisearch.py "query" --parallel --no-text

# Step 2: Evaluate titles, pick best URLs

# Step 3: Extract selected URLs
exa_contents.py URL1 URL2 --highlights --max-chars 3000
```

## Query Classification

The meta-router auto-detects query intent:

| Signal | Category | Provider |
|--------|----------|----------|
| @mentions, #hashtags, "tweet", "reddit" | Social Media | Xpoz |
| "latest", "breaking", "today" | News | Brave |
| "paper", "arxiv", "study" | Academic | Exa |
| "who is", "what is", short questions | Factual | Tavily |
| "company", "startup", "funding" | Company Research | Exa |
| Default | General Web | Brave |

## Test Suite

```bash
python3 scripts/test_omnisearch.py --quick     # Offline + one live per key
python3 scripts/test_omnisearch.py              # Full suite
python3 scripts/test_omnisearch.py --group router   # Classification tests only
python3 scripts/test_omnisearch.py --group dedup    # Dedup tests only
```

32 tests across 6 groups (router, dedup, format, brave, tavily, xpoz).

## Cross-Skill Integration

Omnisearch orchestrates with two sibling skills when available:

- **exa-search** — Neural/semantic search via `exa_search.py` subprocess
- **firecrawl** — Search + scrape via `firecrawl_api.py` subprocess

These are optional — omnisearch works with just Brave + Tavily + Xpoz.
