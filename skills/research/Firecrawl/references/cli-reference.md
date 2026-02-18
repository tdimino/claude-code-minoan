# Firecrawl CLI Reference

Complete parameter reference for the official Firecrawl CLI (`firecrawl`).

## scrape — Single Page Extraction

```bash
firecrawl scrape URL [options]
```

| Option | Description |
|--------|-------------|
| `--only-main-content` | Extract only main content, skip nav/footer (recommended) |
| `--format <formats>` | Output formats: markdown, html, rawHtml, links, screenshot, json |
| `--html` | Shortcut for `--format html` |
| `--wait-for <ms>` | Wait for JS rendering (milliseconds) |
| `--screenshot` | Take screenshot |
| `--include-tags <tags>` | HTML tags to include |
| `--exclude-tags <tags>` | HTML tags to exclude |
| `-o, --output <path>` | Save to file |
| `--pretty` | Pretty print JSON |

**Examples:**

```bash
# Recommended: clean output
firecrawl scrape https://example.com --only-main-content

# Save to file
firecrawl scrape https://example.com --only-main-content -o output.md

# Get HTML
firecrawl scrape https://example.com --html

# Multiple formats (returns JSON)
firecrawl scrape https://example.com --format markdown,links --pretty

# Wait for JS rendering
firecrawl scrape https://example.com --wait-for 3000

# Take screenshot
firecrawl scrape https://example.com --screenshot
```

---

## crawl — Website Crawling

```bash
firecrawl crawl URL [options]
```

| Option | Description |
|--------|-------------|
| `--wait` | Wait for crawl completion (recommended) |
| `--progress` | Show progress indicator |
| `--limit <n>` | Maximum pages to crawl |
| `--max-depth <n>` | Maximum crawl depth |
| `--include-paths <paths>` | Paths to include (comma-separated) |
| `--exclude-paths <paths>` | Paths to exclude |
| `--allow-subdomains` | Include subdomains |
| `--delay <ms>` | Delay between requests |
| `--max-concurrency <n>` | Max concurrent requests |
| `-o, --output <path>` | Save results to file |

**Examples:**

```bash
# Crawl with progress
firecrawl crawl https://docs.example.com --wait --progress

# Limit pages and depth
firecrawl crawl https://example.com --limit 50 --max-depth 3 --wait

# Filter by paths
firecrawl crawl https://example.com --include-paths /blog,/docs --wait

# Save results
firecrawl crawl https://example.com --wait --progress -o results.json

# Check status of existing crawl
firecrawl crawl <job-id>
```

---

## map — URL Discovery

```bash
firecrawl map URL [options]
```

| Option | Description |
|--------|-------------|
| `--limit <n>` | Maximum URLs to discover |
| `--search <query>` | Filter URLs by search query |
| `--sitemap <mode>` | Sitemap handling: include, skip, only |
| `--include-subdomains` | Include subdomains |
| `--json` | Output as JSON |
| `-o, --output <path>` | Save to file |

**Examples:**

```bash
# Discover all URLs
firecrawl map https://example.com

# Filter by search query
firecrawl map https://example.com --search "API"

# Limit results
firecrawl map https://example.com --limit 100

# Include subdomains
firecrawl map https://example.com --include-subdomains

# Output as JSON
firecrawl map https://example.com --json --pretty -o urls.json
```

---

## search — Web Search

```bash
firecrawl search "query" [options]
```

| Option | Description |
|--------|-------------|
| `--limit <n>` | Maximum results (default: 5, max: 100) |
| `--sources <sources>` | Sources: web, images, news |
| `--categories <cats>` | Filter: github, research, pdf |
| `--tbs <value>` | Time filter: qdr:h (hour), qdr:d (day), qdr:w (week), qdr:m (month) |
| `--location <loc>` | Geo-targeting |
| `--scrape` | Scrape search results |
| `--scrape-formats <formats>` | Formats for scraped content |

**Examples:**

```bash
# Basic search
firecrawl search "web scraping tutorials" --limit 10

# Time-filtered
firecrawl search "AI news" --tbs qdr:d   # Last day
firecrawl search "AI news" --tbs qdr:w   # Last week

# Category-filtered
firecrawl search "react hooks" --categories github
firecrawl search "machine learning" --categories research,pdf

# Search AND scrape results
firecrawl search "documentation" --scrape --scrape-formats markdown

# Location-based
firecrawl search "restaurants" --location "Berlin,Germany" --country DE
```

---

## Utility Commands

```bash
# Check status, credits, and concurrency
firecrawl --status

# View credit usage
firecrawl credit-usage

# View config
firecrawl config

# Authenticate
firecrawl login --api-key $FIRECRAWL_API_KEY

# Logout
firecrawl logout
```

---

## fc-save — Auto-Save Alias

```bash
fc-save URL
```

Scrapes a webpage and saves to `~/Desktop/Screencaps & Chats/Web-Scrapes/`. Filename derived from URL (e.g., `docs-example-com-api.md`).

---

## Jina Reader — Fallback

```bash
jina URL
```

Alternative scraper. Use when Firecrawl fails or for Twitter/X URLs (Firecrawl blocks Twitter, Jina works).

---

## DeepWiki — GitHub Repo Documentation

```bash
~/.claude/skills/Firecrawl/scripts/deepwiki.sh <owner/repo> [section] [options]
```

AI-generated wiki for any public GitHub repo via [DeepWiki](https://deepwiki.com).

| Option | Description |
|--------|-------------|
| `--toc` | List all available wiki pages |
| `--all` | Fetch and concatenate all pages |
| `--save` | Auto-save to Web-Scrapes directory |
| `-o FILE` | Save to specific file |

```bash
# Overview
~/.claude/skills/Firecrawl/scripts/deepwiki.sh karpathy/nanochat

# Browse sections
~/.claude/skills/Firecrawl/scripts/deepwiki.sh langchain-ai/langchain --toc

# Specific section
~/.claude/skills/Firecrawl/scripts/deepwiki.sh karpathy/nanochat 4.1-gpt-transformer-implementation

# Full dump
~/.claude/skills/Firecrawl/scripts/deepwiki.sh openai/openai-python --all --save
```
