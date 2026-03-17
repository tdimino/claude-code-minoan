# Cloudflare Browser Rendering REST API Reference

**Base URL**: `https://api.cloudflare.com/client/v4/accounts/{account_id}/browser-rendering`

**Auth**: `Authorization: Bearer {api_token}` or `X-Auth-Key: {global_key}` + `X-Auth-Email: {email}`

**Status**: `/crawl` is open beta (March 10, 2026). All other endpoints are GA.

## Endpoints

### Single-Page (Synchronous)

| Endpoint | Method | Returns | Description |
|----------|--------|---------|-------------|
| `/markdown` | POST | text/markdown | Convert page to markdown |
| `/content` | POST | text/html | Rendered HTML (includes page title) |
| `/screenshot` | POST | image/png | Page screenshot (1920x1080 default) |
| `/pdf` | POST | application/pdf | Page as PDF |
| `/scrape` | POST | application/json | Extract elements via CSS selectors |
| `/links` | POST | application/json | All links from a page |
| `/json` | POST | application/json | AI-structured extraction (Workers AI) |
| `/snapshot` | POST | application/json | HTML + metadata snapshot |

All single-page endpoints accept:
- `url` (string, required) — Target URL
- `render` (boolean, default: true) — `true` = headless Chrome, `false` = static HTML fetch

### `/crawl` (Async, Beta)

**POST** — Start a crawl job (returns job ID immediately)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `url` | string | required | Starting URL |
| `limit` | number | 10 | Max pages (max 100,000 paid, 100 free) |
| `depth` | number | 100,000 | Max link depth |
| `source` | string | `all` | URL discovery: `all`, `sitemaps`, `links` |
| `formats` | array | `["html"]` | Output: `html`, `markdown`, `json` |
| `render` | boolean | true | JS rendering (false = static, free in beta) |
| `maxAge` | number | 86,400 | Cache TTL in seconds (max 604,800) |
| `modifiedSince` | number | — | Unix timestamp, skip unmodified pages |
| `jsonOptions.prompt` | string | — | AI extraction prompt (requires `json` format) |
| `jsonOptions.response_format` | object | — | JSON schema for structured extraction |
| `options.includePatterns` | array | — | Wildcard URL include filters (`*`, `**`) |
| `options.excludePatterns` | array | — | Wildcard URL exclude filters (higher priority) |
| `options.includeSubdomains` | boolean | false | Follow subdomain links |
| `options.includeExternalLinks` | boolean | false | Follow external domain links |

**GET** `/crawl/{id}` — Poll job status

| Parameter | Type | Description |
|-----------|------|-------------|
| `cursor` | string | Pagination cursor (response capped at 10 MB) |
| `status` | string | Filter results by page status |

**DELETE** `/crawl/{id}` — Cancel a running job

**Job statuses**: `running`, `completed`, `errored`, `cancelled_by_user`, `cancelled_due_to_timeout`, `cancelled_due_to_limits`

**Limits**: Max run time 7 days. Results available 14 days after completion.

### `/json` (AI Extraction)

Three modes:
1. **Prompt + schema** — Most precise
2. **Prompt only** — AI determines structure
3. **Schema only** — AI infers what to extract

Additional params:
- `jsonOptions.custom_ai` — BYO model (OpenAI, Anthropic, etc.)
- Response includes `rawAiResponse` on parse errors for debugging

## Pricing

| Tier | Browser Hours | Concurrent Browsers |
|------|---------------|---------------------|
| **Free** | 10 min/day | 3 per account |
| **Paid** | 10 hr/month included, then $0.09/hr | 10 (monthly avg), then $2.00/each |

- `render: false` (static fetch): **FREE during beta**, will be billed under Workers pricing post-beta
- `/json` format: incurs Workers AI usage
- Failed API calls (e.g. timeout errors) are NOT charged

## Rate Limits

| | Free | Paid |
|---|---|---|
| REST API | 6/min (1 per 10s) | 600/min (10/s) |
| New instances/min | 3 | 30 |
| Concurrent browsers | 3 | 30 (requestable increase) |
| Browser timeout | 60s (keep_alive up to 10 min) | Same |

### Crawl-Specific (Free Plan)
- 5 crawl jobs/day
- 100 pages max per crawl

## Bot Identity

- Self-identifies as bot (signed agent)
- Respects `robots.txt` including `crawl-delay`
- Cannot bypass Cloudflare bot detection or CAPTCHAs
- Bot detection ID: `128292352` (for WAF rules)
- Headers: `cf-brapi-request-id`, `Signature-agent`

## Links

- Docs: https://developers.cloudflare.com/browser-rendering/rest-api/
- Crawl endpoint: https://developers.cloudflare.com/browser-rendering/rest-api/crawl-endpoint/
- Pricing: https://developers.cloudflare.com/browser-rendering/pricing/
- LLM docs: https://developers.cloudflare.com/browser-rendering/llms-full.txt
- MCP server: https://github.com/cloudflare/mcp-server-cloudflare
