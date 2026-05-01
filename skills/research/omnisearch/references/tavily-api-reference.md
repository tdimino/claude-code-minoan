# Tavily API Reference

## Overview

- **Base URL**: `https://api.tavily.com`
- **Auth**: `Authorization: Bearer tvly-...` header
- **Method**: POST (all endpoints)
- **Cost**: Free 1,000 credits/month, then $0.008/query (basic) or $0.016/query (advanced)
- **Key**: `TAVILY_API_KEY` env var. Get at https://tavily.com

## Endpoints

### POST /search

AI-optimized web search with optional grounded answer.

**Request Body:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | required | Natural language query |
| `search_depth` | string | `"basic"` | `"basic"` (~1s) or `"advanced"` (~3-5s, deeper) |
| `topic` | string | `"general"` | `"general"`, `"news"`, `"finance"` |
| `max_results` | int | 5 | Results to return (1–20) |
| `include_answer` | bool | false | Generate AI-synthesized answer with citations |
| `include_raw_content` | bool | false | Include full page content per result |
| `include_domains` | string[] | — | Restrict to these domains |
| `exclude_domains` | string[] | — | Exclude these domains |
| `days` | int | — | Results from last N days only |
| `include_images` | bool | false | Include image results |
| `chunks_per_source` | int | 3 | Content chunks per source (1–10) |

**Response Shape:**
```json
{
  "query": "...",
  "answer": "AI-generated answer with citations...",
  "results": [
    {
      "title": "...",
      "url": "...",
      "content": "Relevant excerpt...",
      "raw_content": "Full page (if requested)...",
      "score": 0.95,
      "published_date": "2026-04-28"
    }
  ],
  "images": [{"url": "..."}]
}
```

### POST /extract

Extract full content from URLs.

**Request Body:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `urls` | string[] | required | URLs to extract |
| `include_images` | bool | false | Include images from pages |

**Response Shape:**
```json
{
  "results": [
    {
      "url": "...",
      "raw_content": "Full extracted content..."
    }
  ],
  "failed_results": [
    {"url": "...", "error": "..."}
  ]
}
```

## Script Mapping

| Script Function | Endpoint | Key Params |
|----------------|----------|------------|
| `search()` | `/search` | All search params |
| `extract()` | `/extract` | urls, include_images |
| `format_answer()` | — | Renders answer + source citations |

## Topic Modes

| Topic | Behavior |
|-------|----------|
| `general` | Default web search across all content |
| `news` | Prioritizes news sources, recent content |
| `finance` | Prioritizes financial data, market sources |

## Search Depth

| Depth | Latency | Cost | Use When |
|-------|---------|------|----------|
| `basic` | ~1s | 1 credit | Quick lookups, confirmations |
| `advanced` | ~3-5s | 2 credits | Comprehensive research, complex queries |

## Credit System

- 1 basic search = 1 credit
- 1 advanced search = 2 credits
- 1 extract = 1 credit per URL
- Free tier: 1,000 credits/month
- No per-second rate limit documented
