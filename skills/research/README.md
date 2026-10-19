# Research Skills

Web search, academic research, scraping, and computational analysis.

| Skill | Description |
|-------|-------------|
| `academic-research` | Paper search, literature reviews, and research synthesis via Exa and arXiv |
| `ancient-near-east-research` | Biblical Hebrew, Semitic linguistics, cuneiform, Minoan/Aegean archaeology --- Sefaria, CDLI/ORACC APIs + web discovery |
| `exa-search` | Exa 3.0 search (lite/auto/deep), URL contents, cited answers, and the async Agent API — 6 scripts |
| `firecrawl` | Cloud web scraping to markdown — single pages, site crawls, search, agent extraction |
| `keenable` | Web search + page fetch via Keenable AI — point-in-time search, prompt-driven extraction, 100K free/mo |
| `omnisearch` | Unified meta-router across 5 providers (Brave, Tavily, Xpoz, Exa, Firecrawl) — auto-routes, parallel search, dedup, social media |
| `openplanter` | Dataset investigation, entity resolution, evidence chains with confidence tiers (Admiralty/ACH) |
| `reverse-trace` | Reverse image/video source identification — chains Vision, Picarta, Gemini to trace TV shows, movies, locations |
| `scrapling` | Local stealth web scraping — anti-bot bypass, Cloudflare solver, adaptive element tracking |

## Scraping Decision Table

| Need | Tool |
|------|------|
| Clean markdown from a URL | `firecrawl scrape --only-main-content` |
| Bypass Cloudflare / anti-bot | `scrapling --stealth` |
| Extract specific elements | `scrapling --css SELECTOR` |
| No API key available | `scrapling` (100% local) |
| General web search (high volume) | `keenable` |
| Point-in-time search | `keenable --query-time` |
| Extract data from URL (LLM) | `keenable --prompt "extract X"` |
| Neural / semantic search | `exa-search` |
| Researched lists, enrichment, multi-hop | `exa-search` (`exa_agent.py`) |
| Academic papers | `academic-research` (Exa + arXiv MCP) |
| ANE primary sources (Hebrew, cuneiform) | `ancient-near-east-research` (Sefaria + CDLI/ORACC) |
| Multi-provider parallel search | `omnisearch --parallel` |
| Twitter / Reddit / Instagram | `omnisearch --social` or `xpoz_search.py` |
| AI-synthesized answer | `omnisearch --answer` |
| Identify image/video source | `reverse-trace` (rt_trace.py) |
| Geolocate a photo | `reverse-trace` (rt_geospy.py) |

Both `firecrawl` and `scrapling` output can be piped through `firecrawl/scripts/filter_web_results.py` for token-efficient extraction.
