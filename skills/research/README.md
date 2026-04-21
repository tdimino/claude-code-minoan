# Research Skills

Web search, academic research, scraping, and computational analysis.

| Skill | Description |
|-------|-------------|
| `academic-research` | Paper search, literature reviews, and research synthesis via Exa and arXiv |
| `exa-search` | Neural web search with 5 specialized scripts (search, contents, similar, research, find) |
| `firecrawl` | Cloud web scraping to markdown — single pages, site crawls, search, agent extraction |
| `linear-a-decipherment` | Computational Linear A analysis using Gordon's Semitic hypothesis |
| `scrapling` | Local stealth web scraping — anti-bot bypass, Cloudflare solver, adaptive element tracking |

## Scraping Decision Table

| Need | Tool |
|------|------|
| Clean markdown from a URL | `firecrawl scrape --only-main-content` |
| Bypass Cloudflare / anti-bot | `scrapling --stealth` |
| Extract specific elements | `scrapling --css SELECTOR` |
| No API key available | `scrapling` (100% local) |
| Neural / semantic search | `exa-search` |
| Academic papers | `academic-research` (Exa + arXiv MCP) |

Both `firecrawl` and `scrapling` output can be piped through `firecrawl/scripts/filter_web_results.py` for token-efficient extraction.
