# Firecrawl

Cleaner web scraping than `WebFetch` — handles JavaScript-heavy pages, avoids content truncation, and exposes the full Firecrawl v2 API: scrape, crawl, map, search, LLM extraction, autonomous agents, and post-scrape browser interaction. Ships with a token-efficient filter pipeline and a DeepWiki helper for GitHub repo documentation.

**Last updated:** 2026-04-14

---

## Why This Skill Exists

`WebFetch` truncates long pages, mangles JS-rendered content, and pollutes the context with nav/footer noise. Firecrawl returns clean Markdown for >80% of real-world pages, lets you crawl whole sites with progress, and supports structured extraction and autonomous agents. This skill wraps the official CLI, the Python SDK, DeepWiki, and the Jina fallback (for Twitter/X) behind a consistent token-efficient workflow: **search → filter → scrape → filter → reason**.

---

## Prerequisites

```bash
npm install -g firecrawl-cli
firecrawl login --api-key $FIRECRAWL_API_KEY
pip install firecrawl-py requests   # only needed for firecrawl_api.py
```

`FIRECRAWL_API_KEY` lives in `~/.config/env/secrets.env`. Optional: `export FIRECRAWL_NO_TELEMETRY=1`.

---

## Structure

```
firecrawl/
  SKILL.md                                # Workflow patterns, when-to-use, comparisons
  README.md                               # This file
  references/
    cli-reference.md                      # Full CLI parameter reference
    python-api-reference.md               # firecrawl_api.py command reference + SDK examples
    firecrawl-api.md                      # Search API reference
    firecrawl-agent-api.md                # Agent API: spark models, parallel agents, webhooks
    actions-reference.md                  # Page actions for dynamic content (click/write/wait/scroll)
    interact-reference.md                 # Post-scrape browser interaction (prompt + code modes)
    branding-format.md                    # Brand identity extraction (colors, fonts, UI)
  scripts/
    firecrawl_api.py                      # Python SDK wrapper — search, scrape, crawl, extract, agent, interact
    filter_web_results.py                 # Token-efficient post-processor (sections, keywords, fields)
    deepwiki.sh                           # AI-generated wiki for any public GitHub repo
    test_firecrawl.py                     # Test suite (--quick for offline validation)
```

---

## Quick Start

### Single page → Markdown

```bash
firecrawl scrape https://docs.example.com/api --only-main-content
firecrawl scrape URL --only-main-content -o page.md
```

### Search the web

```bash
firecrawl search "claude code skill patterns" --limit 10
firecrawl search "query" --scrape --scrape-formats markdown
```

### Map then crawl

```bash
firecrawl map https://docs.example.com --search "API"
firecrawl crawl https://docs.example.com --include-paths /api,/guides --wait --progress --limit 50
```

### Token-efficient pipe

```bash
firecrawl scrape URL --only-main-content | \
  python3 scripts/filter_web_results.py --sections "API,Authentication" --max-chars 5000
```

`filter_web_results.py` flags: `--sections`, `--keywords`, `--max-chars`, `--max-lines`, `--fields` (JSON), `--strip-links`, `--strip-images`, `--compact`, `--stats`.

---

## Python API Script

`firecrawl_api.py` covers everything the CLI doesn't, plus the agent and interact APIs.

| Command | Purpose | Example |
|---------|---------|---------|
| `search` | Web search with optional scrape | `firecrawl_api.py search "query" -n 10` |
| `scrape` | Single URL with page actions | `firecrawl_api.py scrape URL --formats markdown summary` |
| `batch-scrape` | Multiple URLs concurrently | `firecrawl_api.py batch-scrape URL1 URL2 URL3` |
| `crawl` | Website crawling | `firecrawl_api.py crawl URL --limit 20` |
| `map` | URL discovery | `firecrawl_api.py map URL --search "query"` |
| `extract` | LLM-powered structured extraction | `firecrawl_api.py extract URL --prompt "Find pricing"` |
| `agent` | Autonomous extraction (no URLs needed) | `firecrawl_api.py agent "Find YC W24 AI startups"` |
| `parallel-agent` | Bulk agent queries | `firecrawl_api.py parallel-agent "Q1" "Q2" "Q3"` |
| `interact` | Post-scrape browser interaction | `firecrawl_api.py interact SCRAPE_ID --prompt "Click pricing"` |
| `interact-stop` | Stop an interact session | `firecrawl_api.py interact-stop SCRAPE_ID` |

**Agent models:** `spark-1-fast` (10 credits, simple), `spark-1-mini` (default), `spark-1-pro` (thorough).

**Interact modes:**
- AI prompt mode (7 credits/min): natural language instructions
- Code execution mode (2 credits/min): direct Playwright via `--code "..."` (`--language python` for Python)
- Persistent profiles via `--profile NAME` to reuse cookies across scrapes (logins)

Interact does **not** return page Markdown — extract specific elements in code mode, or follow up with another `scrape`.

---

## DeepWiki

AI-generated wikis for any public GitHub repo. No API key.

```bash
./scripts/deepwiki.sh karpathy/nanochat                            # Overview
./scripts/deepwiki.sh langchain-ai/langchain --toc                 # Browse sections
./scripts/deepwiki.sh karpathy/nanochat 4.1-gpt-transformer-impl   # Specific section
./scripts/deepwiki.sh openai/openai-python --all --save            # Full dump for RAG
```

---

## When to Use What

| Need | Tool |
|------|------|
| Single page → clean Markdown | `firecrawl scrape --only-main-content` |
| Search + scrape in one shot | `firecrawl search --scrape` |
| Crawl entire site with progress | `firecrawl crawl --wait --progress` |
| Autonomous data finding (no URLs) | `firecrawl_api.py agent` |
| Structured extraction by prompt | `firecrawl_api.py extract` |
| Interactive multi-step (forms, login) | `firecrawl_api.py interact` |
| Twitter/X content | `jina URL` (Firecrawl blocks Twitter) |
| GitHub repo docs | `deepwiki.sh owner/repo` |
| Anti-bot / Cloudflare bypass | `scrapling` skill |
| Budget JS-rendered scrape | `cloudflare:cf_browser.py` |
| Claude API agent building | Native `web_search_20260209` |
| Semantic / neural search | `exa-search` skill |

---

## Token-Efficient Workflow

Inspired by Anthropic's [dynamic filtering](https://claude.com/blog/improved-web-search-with-dynamic-filtering): **filter before reasoning**.

```
Search (titles/URLs only) → Evaluate → Scrape top hits → Filter sections → Reason
```

Practical levers:

- `firecrawl search "query" --limit 20` — titles/URLs only, cheap
- `firecrawl map URL --search "topic"` — discover relevant subpages first
- `firecrawl scrape URL --only-main-content` — strip nav/footer
- `--format links` — get URL list, scrape selectively
- Pipe to `filter_web_results.py` — sections, keywords, char/line caps

---

## Troubleshooting

```bash
firecrawl --status && firecrawl credit-usage    # Status + credits
firecrawl logout && firecrawl login --api-key $FIRECRAWL_API_KEY   # Re-auth
echo $FIRECRAWL_API_KEY                          # Check key is set
```

- **Scrape returns empty:** add `--wait-for 3000` for JS-heavy pages, or fall back to `jina URL`
- **Async job stuck:** `firecrawl crawl-status JOB_ID` / `batch-status`, cancel with `crawl-cancel` / `batch-cancel`
- **Twitter/X URL:** Firecrawl blocks Twitter — use `jina URL`
- **Cloudflare/anti-bot:** switch to the `scrapling` skill (local Turnstile solver)

---

## Testing

```bash
python3 scripts/test_firecrawl.py --quick          # Offline validation
python3 scripts/test_firecrawl.py                  # Full suite (API required)
python3 scripts/test_firecrawl.py --test scrape    # Specific test
```

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan) — curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/research/firecrawl ~/.claude/skills/
```
