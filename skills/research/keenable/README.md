# Keenable

Web search and page fetch via [Keenable AI](https://keenable.ai) — a search API purpose-built for AI agents. Two scripts cover all use cases: search the web and fetch/extract page contents.

Differentiates from Exa and Firecrawl on three features no other tool offers: **point-in-time search** (query the index as it existed at a past date), **prompt-driven extraction** (LLM reads the page server-side and returns only what you asked for), and a **100K requests/month free tier** (100x Exa's).

## Prerequisites

```bash
export KEENABLE_API_KEY=keen_your-key-here  # https://app.keenable.ai
```

## Scripts

| Script | Endpoint | Purpose |
|--------|----------|---------|
| `keenable_search.py` | `POST /v1/search` | Web search with site, date, and point-in-time filters |
| `keenable_fetch.py` | `GET /v1/fetch` | Fetch page as markdown, with optional LLM extraction |
| `keenable_setup.py` | — | Validate API key and configure MCP server |

## Quick Start

### Search

```bash
# Basic search
python3 scripts/keenable_search.py "AI agent frameworks"

# Site-restricted
python3 scripts/keenable_search.py "authentication" --site docs.anthropic.com

# Recent only (last 7 days)
python3 scripts/keenable_search.py "Claude Code updates" --published-after 7d

# Point-in-time — search the index as of January 2026
python3 scripts/keenable_search.py "AI safety" --query-time 2026-01-01

# More results with longer snippets
python3 scripts/keenable_search.py "transformer optimization" --count 20 --snippet-length 5000
```

### Fetch

```bash
# Fetch page as markdown
python3 scripts/keenable_fetch.py "https://docs.keenable.ai/"

# Live fetch (bypass cache, works on any URL)
python3 scripts/keenable_fetch.py "https://example.com" --live

# Extract specific data — LLM reads page, returns only the answer
python3 scripts/keenable_fetch.py "https://example.com/pricing" \
  --prompt "List all pricing tiers with name, price, and features"

# Bounded output
python3 scripts/keenable_fetch.py "https://example.com" --max-chars 5000
```

### Token-Efficient Research

Search cheaply, pick the best results, extract selectively:

```bash
# 1. Search with short snippets to scan titles
python3 scripts/keenable_search.py "query" --count 10 --snippet-length 200

# 2. Pick the 2-3 most relevant URLs

# 3. Extract only what you need
python3 scripts/keenable_fetch.py URL --prompt "Extract the key findings"
```

## When to Use What

| Task | Best Tool | Why |
|------|-----------|-----|
| General web search | **Keenable** | 100K free/mo, fast |
| Point-in-time search | **Keenable** | Only tool with historical index queries |
| Extract data from URL | **Keenable** `--prompt` | Server-side LLM extraction |
| Semantic/neural search | **Exa** | AI-powered relevance ranking |
| Find similar pages | **Exa** | Semantic similarity |
| Deep site crawling | **Firecrawl** | Link following, JS rendering |
| High-volume research | **Keenable** | 100K vs Exa 1K vs Firecrawl 500 |

## MCP Alternative

For native tool access without scripts:

```bash
claude mcp add keenable \
  --transport http https://api.keenable.ai/mcp \
  --scope user \
  --header "X-API-Key: $KEENABLE_API_KEY"
```

## API Details

- **Base URL**: `https://api.keenable.ai`
- **Auth**: `X-API-Key: keen_...` header
- **Rate limits**: 10 req/s authenticated (per org), 1K/hr unauthenticated (per IP)
- **Credits**: 100K free/month, each search or fetch = 1 credit
- **Public endpoints**: `/v1/search/public`, `/v1/fetch/public` (keyless, shared limits)

Full parameter reference in `references/api-reference.md`. Comparison matrix in `references/selection-guide.md`.

## File Structure

```
keenable/
├── SKILL.md                          # Claude Code skill definition
├── README.md                         # This file
├── scripts/
│   ├── keenable_search.py            # Web search wrapper
│   ├── keenable_fetch.py             # Page fetch + LLM extraction wrapper
│   └── keenable_setup.py             # API key validation + MCP setup
├── references/
│   ├── api-reference.md              # Full API parameter docs
│   └── selection-guide.md            # Keenable vs Exa vs Firecrawl
└── evals/
    └── evals.json                    # Trigger/non-trigger test cases
```
