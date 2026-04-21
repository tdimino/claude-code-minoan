# Cloudflare

Manage Cloudflare infrastructure from the terminal: Pages deploys, Workers, KV, R2, D1, Queues, Vectorize, Hyperdrive, Agents SDK with Code Mode, and budget web scraping via Browser Rendering. Two tools: Wrangler CLI for platform management, `cf_browser.py` for headless Chrome on the edge.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

Cloudflare's platform spans a dozen services with different CLI patterns and config formats. This skill consolidates the Wrangler CLI reference, Pages deployment workflows, Agents SDK patterns, and a Python script for Browser Rendering---the budget alternative to Firecrawl for scraping, screenshots, and PDFs.

---

## Structure

```
cloudflare/
  SKILL.md                                 # Full usage guide
  README.md                                # This file
  references/
    wrangler-commands.md                   # Full Wrangler CLI command reference
    pages-config.md                        # _headers, _redirects, build presets
    browser-rendering-api.md               # Browser Rendering REST API reference
    agents-sdk-codemode.md                 # Agents SDK & Code Mode API
  scripts/
    cf_browser.py                          # Browser Rendering CLI (scrape, crawl, screenshot, PDF)
```

---

## Quick Reference

### Platform Management (Wrangler)

```bash
wrangler pages deploy out --project-name mysite    # Deploy static site
wrangler deploy                                     # Deploy Worker
wrangler dev                                        # Local dev server
wrangler tail my-worker                             # Stream live logs
wrangler kv namespace list                          # List KV namespaces
wrangler r2 bucket list                             # List R2 buckets
wrangler d1 list                                    # List D1 databases
wrangler secret put API_KEY                         # Set encrypted secret
```

### Browser Rendering (cf_browser.py)

```bash
python3 cf_browser.py markdown https://example.com              # Page → markdown
python3 cf_browser.py markdown https://example.com --no-render  # Free static fetch
python3 cf_browser.py crawl https://docs.example.com --limit 50 # Multi-page crawl
python3 cf_browser.py screenshot https://example.com -o page.png
python3 cf_browser.py pdf https://example.com -o page.pdf
python3 cf_browser.py json https://example.com --prompt "Extract prices"
```

### Scraping Tool Comparison

| Need | Best Tool |
|------|-----------|
| Clean markdown, reliable | Firecrawl |
| Cheap/free JS-rendered scrape | `cf_browser.py` (free 10 min/day) |
| Free static fetch | `cf_browser.py --no-render` (free during beta) |
| Anti-bot bypass | Scrapling |
| Twitter/X | Jina |

---

## Setup

### Prerequisites

- `npm install -g wrangler` + `wrangler login` (platform management)
- Python 3.9+ and `requests` (Browser Rendering script)
- `CLOUDFLARE_ACCOUNT_ID` + `CLOUDFLARE_API_TOKEN` in `~/.config/env/secrets.env`

---

## Related Skills

- **`firecrawl`**: Higher-quality markdown extraction, web search + scrape.
- **`scrapling`**: Local anti-bot scraping without API keys.

---

## Requirements

- Node.js + Wrangler CLI (platform management)
- Python 3.9+ + `requests` (Browser Rendering)
- Cloudflare account with API token

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/cloudflare ~/.claude/skills/
```
