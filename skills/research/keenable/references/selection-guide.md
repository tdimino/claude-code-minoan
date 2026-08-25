# Search Tool Selection Guide

## Decision Matrix

### By Feature

| Feature | Keenable | Exa | Firecrawl |
|---------|----------|-----|-----------|
| Web search | Yes | Yes (neural) | Limited (search + scrape) |
| Page fetch/read | Yes | Yes (contents) | Yes (scrape) |
| Point-in-time search | Yes | No | No |
| Prompt-driven extraction | Yes (on fetch) | No | No |
| Semantic similarity search | No | Yes | No |
| Deep site crawling | No | No | Yes |
| JS rendering | No | No | Yes |
| Structured scraping | No | No | Yes (CSS selectors) |
| Research synthesis | No | Yes (exa_research) | No |
| MCP native | Yes | Yes (MCP server) | No |
| Date filtering | Yes | Yes | No |
| Site restriction | Yes | Yes | N/A |
| Category filtering | No | Yes (8 categories) | No |

### By Free Tier

| Tool | Free Requests/Month | Burst Limit |
|------|---------------------|-------------|
| Keenable | 100,000 | Per-org (authenticated) |
| Exa | 1,000 | Per-key |
| Firecrawl | 500 credits | Per-key |

### By Task

| Task | Best Tool | Runner-up |
|------|-----------|-----------|
| General web search | Keenable | Exa |
| Find recent news | Keenable (`--published-after`) | Exa (`--after`) |
| Historical search (past index) | Keenable (`--query-time`) | — |
| Extract data from URL | Keenable (`--prompt`) | Firecrawl (scrape + parse) |
| Read a known URL | Keenable (fetch) | Firecrawl (scrape) |
| Find similar pages | Exa (exa_similar.py) | — |
| Academic paper search | Exa (`--category "research paper"`) | Keenable |
| Company research | Exa (`--category company`) | Keenable |
| Crawl entire site | Firecrawl (crawl) | — |
| Scrape JS-rendered pages | Firecrawl | — |
| Quick factual answer | Exa (exa_research.py) | Keenable (search + fetch) |
| High-volume research | Keenable (100K/mo) | — |

## When to Combine Tools

**Keenable search → Firecrawl scrape**: When you need to find pages via web search but the target pages require JS rendering or structured CSS extraction.

**Keenable search → Exa contents**: When you find URLs via Keenable but want Exa's AI-powered content summarization.

**Exa search → Keenable fetch**: When you need Exa's semantic ranking to find the right pages, then Keenable's prompt-driven extraction to pull specific data.
