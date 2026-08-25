# Keenable API Reference

Base URL: `https://api.keenable.ai`

## Authentication

Pass API key via either header:
- `X-API-Key: keen_<key>` (preferred)
- `Authorization: Bearer keen_<key>` (alternative; `X-API-Key` wins if both present)

Keys are scoped to your workspace, never expire, can be rotated at any time.

### Public/keyless endpoints

Each endpoint has a `/public` twin (`/v1/search/public`, `/v1/fetch/public`) — no API key needed, but requires `X-Keenable-Title` header naming your application. Max 256 chars.

### Error responses

| Status | Meaning |
|--------|---------|
| `400` | Malformed API key or invalid request parameters |
| `401` | Missing or invalid API key |
| `402` | No credits available (monthly allowance spent) |
| `403` | API key disabled or revoked |
| `404` | Page not found (fetch only) |
| `422` | Content could not be extracted (fetch only) |
| `429` | Rate limit exceeded |
| `500` | Internal server error |

Error body: `{"error": "category", "message": "detail", "details": {...}}`

## Rate Limits

| Auth status | Rate limit |
|-------------|------------|
| Authenticated | 10 requests/second (per organization) |
| Unauthenticated | 1,000 requests/hour + 10 requests/second (per IP) |

Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`. `429` adds `Retry-After`.

## Credits

- **100,000 requests/month free** (resets monthly, recurring)
- Each search or fetch = 1 credit
- SKUs: `search.realtime`, `search.pro`, `fetch`, `fetch.live`
- Unauthenticated requests are NOT metered
- When exhausted: `402` error

## POST /v1/search

Search the web and return ranked results.

### Request Body (JSON)

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | **yes** | — | Search query |
| `site` | string | no | — | Restrict to a specific domain (e.g. `"techcrunch.com"`) |
| `acquired_after` | string | no | — | Pages indexed at or after this point |
| `acquired_before` | string | no | — | Pages indexed at or before this point |
| `published_after` | string | no | — | Pages published at or after this point |
| `published_before` | string | no | — | Pages published at or before this point |
| `query_time` | string | no | — | Point-in-time search: index as it stood at this moment. Re-bases relative deltas |
| `snippet_max_length` | integer | no | — | Max chars per snippet (180–10000) |
| `max_results` | integer | no | 10 | Max number of results (1–50) |

### Date/Time Filter Formats

Each filter accepts ONE of:
- **Date**: `YYYY-MM-DD` — `_after` resolves to `00:00:00Z`, `_before` to `23:59:59.999Z`
- **Timestamp**: `YYYY-MM-DDTHH:MM:SS[.sss][±HH:MM]` — no offset = UTC
- **Relative delta**: `<number><unit>` — resolves to request time (or `query_time`) minus delta
  - Units: `min` (minutes), `h` (hours), `d` (days), `mo` (months), `y` (years)
  - Examples: `7d`, `30min`, `6mo`, `1y`

### Response

```json
{
  "query": "typescript best practices",
  "results": [
    {
      "title": "TypeScript Best Practices 2026",
      "url": "https://example.com/ts-best-practices",
      "description": "A comprehensive guide to modern TypeScript patterns.",
      "snippet": "TypeScript Best Practices 2026 Use strict mode...",
      "published_at": "2026-01-15T10:30:00Z",
      "acquired_at": "2026-01-16T08:12:34Z"
    }
  ]
}
```

Fields per result: `title` (required), `url` (required), `description` (required), `snippet` (optional), `published_at` (optional, ISO 8601), `acquired_at` (optional, ISO 8601).

## GET /v1/fetch

Fetch webpage contents as markdown.

### Query Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `url` | string (URI) | **yes** | — | URL to fetch |
| `max_chars` | integer | no | 50000 | Max characters of content (min: 1). Longer content truncated with notice |
| `live` | boolean | no | false | Fetch live from source instead of indexed copy. Required for non-indexed URLs |
| `prompt` | string | no | — | Extraction instruction (max 2000 chars). LLM reads page and returns only extracted answer |

**Non-indexed URLs return an error by default.** Pass `live=true` for any URL not in Keenable's index.

### Response

```json
{
  "url": "https://example.com/page",
  "title": "Page Title",
  "description": "Meta description",
  "author": "Jane Doe",
  "published_at": "2026-01-15T10:30:00Z",
  "content": "# Page Title\n\nMarkdown content..."
}
```

Fields: `url` (required), `content` (required), `title` (optional), `description` (optional), `author` (optional), `published_at` (optional).

When `prompt` is set, `content` contains the extracted answer, not the full page.

## MCP Server

Remote: `https://api.keenable.ai/mcp`
npm: `@keenable/mcp-server` (stdio bridge)

### Claude Code setup

```bash
claude mcp add keenable \
  --transport http https://api.keenable.ai/mcp \
  --scope user \
  --header "X-API-Key: keen_<your_key>"
```

### MCP Tools

1. **`search_web_pages`** — same params as POST /v1/search
2. **`fetch_page_content`** — same params as GET /v1/fetch

Authenticated calls include `_meta["keenable/usage"]` with SKU, amount, credits, and paid status.

## CLI

Install: `brew install keenableai/tap/keenable-cli`

Commands:
- `keenable login` — device-code auth flow
- `keenable search "query"` — search from terminal
- `keenable configure-mcp --all` — auto-configure MCP for Claude Code, Cursor, Windsurf, Codex, OpenCode
