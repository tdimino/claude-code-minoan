# Brave Search API Reference

## Overview

- **Base URL**: `https://api.search.brave.com/res/v1`
- **Auth**: `X-Subscription-Token` header with API key
- **Method**: GET (all endpoints)
- **Cost**: $5 per 1,000 requests (free tier: 2,000/month with 1 req/sec)
- **Key**: `BRAVE_API_KEY` env var. Get at https://api-dashboard.search.brave.com

## Endpoints

### GET /web/search

Web search with optional news, images, videos, and AI summary.

**Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `q` | string | required | Search query |
| `count` | int | 10 | Results to return (max 20) |
| `offset` | int | 0 | Pagination offset |
| `freshness` | string | — | `pd` (day), `pw` (week), `pm` (month), `py` (year), or `YYYY-MM-DDtoYYYY-MM-DD` |
| `country` | string | — | Two-letter country code (e.g. `US`, `GB`, `IL`) |
| `search_lang` | string | — | Language code (e.g. `en`, `ar`, `he`) |
| `safesearch` | string | moderate | `off`, `moderate`, `strict` |
| `result_filter` | string | — | Comma-separated: `web`, `news`, `images`, `videos` |
| `goggles_id` | string | — | Custom reranking goggles ID |
| `extra_snippets` | bool | false | Include up to 5 additional snippets per result |
| `text_decorations` | bool | true | Include HTML bold/italic in snippets |
| `spellcheck` | bool | true | Enable query spellcheck |
| `summary` | bool | false | Enable LLM Context API (AI summary) |

**Response Shape:**
```json
{
  "query": {"original": "...", "altered": "..."},
  "web": {
    "results": [
      {
        "title": "...",
        "url": "...",
        "description": "...",
        "page_age": "2026-04-28T...",
        "extra_snippets": ["...", "..."]
      }
    ]
  },
  "news": {"results": [...]},
  "images": {"results": [...]},
  "videos": {"results": [...]},
  "summarizer": {"key": "..."}
}
```

### GET /news/search

Dedicated news search endpoint.

**Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `q` | string | required | Search query |
| `count` | int | 20 | Results (max 20) |
| `freshness` | string | — | Same as web search |
| `country` | string | — | Two-letter country code |

**Response Shape:**
```json
{
  "query": {"original": "..."},
  "results": [
    {
      "title": "...",
      "url": "...",
      "description": "...",
      "age": "3 hours ago",
      "meta_url": {"hostname": "reuters.com"}
    }
  ]
}
```

### LLM Context API

Not a separate endpoint — enabled via `summary=true` + `extra_snippets=true` on `/web/search`.

Returns pre-processed content optimized for LLM consumption: AI-generated summary alongside supporting results with extra snippets for richer grounding context.

## Script Mapping

| Script Function | Endpoint | Key Params |
|----------------|----------|------------|
| `web_search()` | `/web/search` | All web params |
| `news_search()` | `/news/search` | q, count, freshness, country |
| `summarize_search()` | `/web/search` | summary=true, extra_snippets=true |

## Rate Limits

- Free tier: 1 request/second, 2,000/month
- Paid: varies by plan, no published per-second limit
- Handle 429 with exponential backoff

## Goggles

Custom result reranking rules. Community-created or self-authored. Pass `goggles_id` URL to apply.
Documentation: https://brave.com/goggles/
