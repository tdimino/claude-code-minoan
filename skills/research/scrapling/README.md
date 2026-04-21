# Scrapling

Scrape web pages locally with anti-bot bypass, TLS impersonation, and adaptive element tracking---no API keys, no cloud. Three fetcher tiers: fast HTTP, dynamic JS rendering, and stealth with Cloudflare solver. Includes CSS/XPath extraction, a Spider framework for concurrent crawling, and adaptive selectors that survive site redesigns.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

Firecrawl is excellent for clean markdown extraction but requires an API key and cloud access. Scrapling runs 100% locally with zero credentials, handles Cloudflare-protected sites, and provides element-level extraction with CSS/XPath selectors. Use Scrapling when you need anti-bot bypass, no API key, or targeted element extraction; use Firecrawl when you need clean LLM-ready markdown or batch cloud scraping.

---

## Structure

```
scrapling/
  SKILL.md                          # Full usage guide with Python API examples
  README.md                         # This file
  references/
    cli-reference.md                # Full CLI extract command reference
    python-api-reference.md         # Python API (Fetcher, DynamicFetcher, StealthyFetcher)
    adaptive-scraping.md            # Adaptive element tracking deep-dive
  scripts/
    scrapling_fetch.py              # Stdout wrapper (pipe-friendly)
    scrapling_install.sh            # One-time setup (install + Chromium + verify)
```

---

## Three Fetcher Tiers

| Tier | Engine | Stealth | JS | Speed |
|------|--------|---------|-----|-------|
| `get` | curl_cffi (HTTP) | TLS impersonation | No | Fast |
| `fetch` | Playwright/Chromium | Medium | Yes | Medium |
| `stealthy-fetch` | Patchright/Chrome | Maximum | Yes | Slower |

---

## Usage

```bash
# Basic HTTP fetch (fastest)
python3 scrapling_fetch.py https://example.com

# Stealth mode (anti-bot bypass)
python3 scrapling_fetch.py https://protected.site --stealth

# Stealth + Cloudflare solver
python3 scrapling_fetch.py https://cf-protected.site --stealth --solve-cloudflare

# Dynamic (Playwright, JS rendering)
python3 scrapling_fetch.py https://js-heavy.site --dynamic

# CSS selector extraction
python3 scrapling_fetch.py https://example.com --css ".product-list"

# CLI direct (file output)
scrapling extract get 'https://example.com' content.md
scrapling extract stealthy-fetch 'https://protected.site' content.md --solve-cloudflare
```

---

## Scrapling vs Firecrawl

| Need | Use |
|------|-----|
| Clean markdown from a URL | Firecrawl |
| Bypass Cloudflare/anti-bot | Scrapling (stealth) |
| Extract specific elements | Scrapling (CSS/XPath) |
| No API key available | Scrapling |
| Batch cloud scraping | Firecrawl |
| Site redesign resilience | Scrapling (adaptive mode) |
| Full-site concurrent crawl | Scrapling (Spider framework) |

---

## Key Features

- **Adaptive scraping** --- Elements fingerprinted to SQLite, relocated by similarity after redesigns
- **Spider framework** --- Scrapy-like concurrent crawling with pause/resume and session routing
- **3 fetcher tiers** --- Fast HTTP, dynamic JS, maximum stealth
- **Cloudflare solver** --- Built-in Turnstile bypass
- **CSS/XPath/text/regex** --- Multiple selector strategies
- **TLS impersonation** --- Mimics real browser TLS fingerprints

---

## Setup

### Prerequisites

```bash
# One-time setup (installs scrapling, Chromium, verifies fetchers)
bash scrapling_install.sh
```

- Python 3.9+
- `uv pip install "scrapling[all]"`
- Chromium (downloaded by install script)

---

## Related Skills

- **`firecrawl`**: Cloud-based scraping for clean markdown and batch operations.
- **`cloudflare`**: Browser Rendering for JS-rendered scraping on Cloudflare's edge.

---

## Requirements

- Python 3.9+
- `scrapling[all]`

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/research/scrapling ~/.claude/skills/
```
