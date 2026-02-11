---
name: Firecrawl
description: Use Firecrawl and Jina for fetching web content. ALWAYS prefer Firecrawl over WebFetch for all web fetching tasks—it produces cleaner output, handles JavaScript-heavy pages, and has no content truncation. This skill should be used when fetching URLs, scraping web pages, converting URLs to markdown, extracting web content, searching the web, crawling sites, mapping URLs, LLM-powered extraction, autonomous data gathering with the Agent API, or fetching AI-generated documentation for GitHub repos via DeepWiki. Provides complete coverage of Firecrawl v2.8.0 API endpoints including parallel agents, spark-1-fast model, and sitemap-only crawling.
---

# Firecrawl & Jina Web Scraping

This skill provides comprehensive guidance for web scraping and content extraction using the official Firecrawl CLI, Python API script, and Jina Reader.

## CRITICAL: Always Use Firecrawl Over WebFetch

**ALWAYS prefer `firecrawl scrape URL --only-main-content` over the WebFetch tool for fetching web content.**

Why Firecrawl is better:
- Produces cleaner markdown output
- Better handling of JavaScript-heavy pages
- No token limits or content truncation
- Handles complex page structures better
- Industry-leading >80% coverage on benchmark evaluations

```bash
# ALWAYS DO THIS for fetching URLs:
firecrawl scrape https://docs.example.com/api --only-main-content

# Or for quick auto-save scraping:
fc-save https://docs.example.com/api

# NEVER use WebFetch when Firecrawl is available
```

## When to Use This Skill

Use this skill when:
- Converting web pages to markdown or clean text
- Scraping structured data from websites
- Performing web searches with automatic content extraction
- Analyzing documentation, articles, or web content
- Extracting data for AI/LLM processing
- Research tasks requiring web content retrieval
- **Crawling entire websites** with progress tracking
- **Mapping site structure** to discover all URLs
- **Autonomous data gathering** - describe what you want, let the agent find/extract it
- **Lead generation, competitive research, or dataset curation** across multiple sites
- **LLM-powered extraction** with structured schemas

## Available Tools

### 1. Official Firecrawl CLI (Primary Tool)

**Installation**: `npm install -g firecrawl-cli`
**Authentication**: `firecrawl login --api-key $FIRECRAWL_API_KEY`
**Status Check**: `firecrawl --status`

The official CLI provides the most feature-rich interface for web scraping.

#### Scrape - Single Page Extraction

```bash
# Basic scrape (outputs to stdout)
firecrawl scrape https://example.com

# Recommended: clean output without nav/footer
firecrawl scrape https://example.com --only-main-content

# Save to file
firecrawl scrape https://example.com --only-main-content -o output.md

# Get HTML instead of markdown
firecrawl scrape https://example.com --html

# Multiple formats (returns JSON)
firecrawl scrape https://example.com --format markdown,links --pretty

# Wait for JavaScript rendering
firecrawl scrape https://example.com --wait-for 3000

# Take screenshot
firecrawl scrape https://example.com --screenshot
```

**Scrape Options**:
- `--only-main-content` - Extract only main content (recommended)
- `--format <formats>` - Output formats: markdown, html, rawHtml, links, screenshot, json
- `--html` - Shortcut for `--format html`
- `--wait-for <ms>` - Wait for JS rendering
- `--screenshot` - Take screenshot
- `--include-tags <tags>` - HTML tags to include
- `--exclude-tags <tags>` - HTML tags to exclude
- `-o, --output <path>` - Save to file
- `--pretty` - Pretty print JSON

#### Crawl - Website Crawling

```bash
# Start crawl and wait for completion with progress
firecrawl crawl https://docs.example.com --wait --progress

# Limit pages and depth
firecrawl crawl https://example.com --limit 50 --max-depth 3 --wait

# Filter by paths
firecrawl crawl https://example.com --include-paths /blog,/docs --wait
firecrawl crawl https://example.com --exclude-paths /admin,/login --wait

# Save results
firecrawl crawl https://example.com --wait --progress -o results.json

# Check status of existing crawl job
firecrawl crawl <job-id>
```

**Crawl Options**:
- `--wait` - Wait for crawl completion (recommended)
- `--progress` - Show progress indicator
- `--limit <n>` - Maximum pages to crawl
- `--max-depth <n>` - Maximum crawl depth
- `--include-paths <paths>` - Paths to include (comma-separated)
- `--exclude-paths <paths>` - Paths to exclude
- `--allow-subdomains` - Include subdomains
- `--delay <ms>` - Delay between requests
- `--max-concurrency <n>` - Max concurrent requests

#### Map - URL Discovery

```bash
# Discover all URLs on a site
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

**Map Options**:
- `--limit <n>` - Maximum URLs to discover
- `--search <query>` - Filter URLs by search query
- `--sitemap <mode>` - Sitemap handling: include, skip, only
- `--include-subdomains` - Include subdomains
- `--json` - Output as JSON

#### Search - Web Search

```bash
# Basic search
firecrawl search "web scraping tutorials" --limit 10

# Search with time filter
firecrawl search "AI news" --tbs qdr:d   # Last day
firecrawl search "AI news" --tbs qdr:w   # Last week

# Search specific categories
firecrawl search "react hooks" --categories github
firecrawl search "machine learning" --categories research,pdf

# Search AND scrape results
firecrawl search "documentation" --scrape --scrape-formats markdown

# Location-based search
firecrawl search "restaurants" --location "Berlin,Germany" --country DE
```

**Search Options**:
- `--limit <n>` - Maximum results (default: 5, max: 100)
- `--sources <sources>` - Sources: web, images, news
- `--categories <cats>` - Filter: github, research, pdf
- `--tbs <value>` - Time filter: qdr:h/d/w/m/y
- `--location <loc>` - Geo-targeting
- `--scrape` - Scrape search results
- `--scrape-formats <formats>` - Formats for scraped content

#### Utility Commands

```bash
# Check status, credits, and concurrency
firecrawl --status

# View credit usage
firecrawl credit-usage

# View config
firecrawl config

# Logout
firecrawl logout
```

---

### 2. Auto-Save Alias (`fc-save`)

**Command**: `fc-save URL`

Custom wrapper that scrapes a webpage and **automatically saves** to `~/Desktop/Screencaps & Chats/Web-Scrapes/`

**When to use**:
- Quick single page scraping when you want automatic file saving
- When you don't want to specify an output filename

**Example**:
```bash
fc-save https://docs.anthropic.com/api/introduction
# → Saves to ~/Desktop/Screencaps & Chats/Web-Scrapes/docs-anthropic-com-api-introduction.md
```

**Output location**: Files saved to `~/Desktop/Screencaps & Chats/Web-Scrapes/`

---

### 3. Jina Reader CLI (Fallback)

**Command**: `jina URL`

Alternative to Firecrawl - scrapes webpage and converts to markdown with different parsing approach.

**When to use**:
- When Firecrawl fails or produces suboptimal results
- Alternative parsing for complex pages
- Twitter/X URLs (Firecrawl blocks Twitter, Jina works)

**Example**:
```bash
jina https://example.com/article
jina https://x.com/username/status/123456  # Twitter works with Jina
```

---

### 4. DeepWiki - GitHub Repo Documentation (`deepwiki`)

**Command**: `~/.claude/skills/Firecrawl/scripts/deepwiki.sh <owner/repo> [section] [options]`

AI-generated wiki documentation for any public GitHub repository, powered by [DeepWiki](https://deepwiki.com) (Cognition/Devin). Converts any GitHub repo into structured, navigable documentation with architecture diagrams, component breakdowns, and cross-referenced source links — no API key required.

**URL pattern**: `https://deepwiki.com/{owner}/{repo}` (overview), `https://deepwiki.com/{owner}/{repo}/{section-slug}` (subpage)

**When to use**:
- Understanding an unfamiliar GitHub repo's architecture quickly
- Getting structured documentation for a library/framework before using it
- Researching how open-source projects implement specific patterns
- Alternative to reading raw README + source when you need a high-level map

```bash
# Fetch overview (architecture summary + table of contents)
~/.claude/skills/Firecrawl/scripts/deepwiki.sh karpathy/nanochat

# List all available wiki sections
~/.claude/skills/Firecrawl/scripts/deepwiki.sh langchain-ai/langchain --toc

# Fetch a specific section
~/.claude/skills/Firecrawl/scripts/deepwiki.sh karpathy/nanochat 4.1-gpt-transformer-implementation

# Fetch entire wiki (all pages concatenated)
~/.claude/skills/Firecrawl/scripts/deepwiki.sh anthropics/anthropic-sdk-python --all

# Save to file
~/.claude/skills/Firecrawl/scripts/deepwiki.sh openai/openai-python --save
~/.claude/skills/Firecrawl/scripts/deepwiki.sh openai/openai-python -o docs.md

# Also accepts full GitHub URLs (strips automatically)
~/.claude/skills/Firecrawl/scripts/deepwiki.sh https://github.com/karpathy/nanochat
```

**Options**:
- `--toc` - List all available wiki pages (fetches overview, displays titles only)
- `--all` - Fetch and concatenate all wiki pages (full dump)
- `--save` - Auto-save to `~/Desktop/Screencaps & Chats/Web-Scrapes/deepwiki-{repo}.md`
- `-o FILE` - Save to specific file

**Notes**:
- Works on any public GitHub repo — DeepWiki indexes on demand
- Pages include architecture diagrams (as ASCII), source file references, and cross-links
- For private repos or repos not yet indexed, DeepWiki may not have content
- Scraping uses Firecrawl under the hood (consumes credits like any scrape)

---

### 5. Firecrawl API Script (Advanced Features)

**Command**: `python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py <command>`

Complete access to ALL Firecrawl v2 API endpoints.

**Requires**: `FIRECRAWL_API_KEY` environment variable
**Install**: `pip install firecrawl-py requests`

**Available Commands**:

| Command | Description |
|---------|-------------|
| `search` | Web search with optional content scraping |
| `scrape` | Extract content from a single URL |
| `batch-scrape` | Scrape multiple URLs concurrently |
| `crawl` | Crawl entire websites, following links |
| `map` | Discover all URLs on a website |
| `extract` | LLM-powered structured data extraction |
| `agent` | Autonomous multi-page extraction (no URLs required!) |
| `parallel-agent` | Run multiple agent queries in parallel (v2.8.0+) |
| `crawl-status` | Check async crawl job status |
| `crawl-cancel` | Cancel a running crawl job |
| `crawl-errors` | Get errors from a crawl job |
| `crawl-active` | List all active crawl jobs |
| `batch-status` | Check batch scrape job status |
| `batch-cancel` | Cancel a running batch scrape job |
| `batch-errors` | Get errors from a batch scrape job |
| `extract-status` | Check extract job status |
| `status` | Check agent job status |
| `agent-cancel` | Cancel a running agent job |

---

## Command Reference

### search - Web Search

Search the web with optional content scraping.

```bash
# Basic search
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py search "web scraping best practices" -n 10

# Search GitHub repos only
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py search "python web scraping" --categories github

# Search research papers
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py search "transformer architecture" --categories research

# Search with content scraping
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py search "firecrawl examples" --scrape

# Time-filtered search (recent content)
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py search "AI news" --time qdr:d  # last day

# Location-based search
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py search "tech startups" --location "San Francisco"
```

**Parameters**:
- `-n, --limit`: Number of results (default: 10)
- `--categories`: Filter by github, research, pdf
- `--sources`: Result types: web, news, images
- `--time`: Time filter: qdr:h (hour), qdr:d (day), qdr:w (week), qdr:m (month)
- `--location`: Geotarget results
- `--scrape`: Also scrape content from results
- `--json`: Output raw JSON

---

### scrape - Single URL Extraction

Extract content from a single URL with optional page actions, geo-targeting, and caching.

```bash
# Basic scrape
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py scrape "https://docs.firecrawl.dev/"

# With specific formats (including new: summary, images, branding)
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py scrape "https://example.com" --formats markdown html links summary

# Extract brand identity (colors, fonts, typography)
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py scrape "https://example.com" --formats branding

# Include navigation/footer
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py scrape "https://example.com" --full

# With page actions (click, wait, scroll) for dynamic content
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py scrape "https://example.com" \
  --actions '[{"type": "click", "selector": "#load-more"}, {"type": "wait", "milliseconds": 2000}]'

# Geo-targeted scraping (e.g., for localized content)
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py scrape "https://example.com" \
  --country US --languages en-US es

# Use cached result if fresher than 1 hour
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py scrape "https://example.com" --max-age 3600

# Don't cache this scrape
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py scrape "https://example.com" --no-cache
```

**Parameters**:
- `--formats`: Output formats: markdown, html, links, screenshot, **summary**, **images**, **branding**
- `--full`: Include navigation and footer (default: main content only)
- `--actions`: JSON array of page actions (click, write, wait, scroll, screenshot)
- `--country`: Country code for geo-targeting (e.g., US, GB, DE)
- `--languages`: Language codes for geo-targeting (e.g., en-US es)
- `--max-age`: Use cached result if fresher than N seconds
- `--no-cache`: Don't cache this scrape result
- `--json`: Output raw JSON

**Page Actions** (for dynamic content):
- `{"type": "click", "selector": "#button"}` - Click an element
- `{"type": "write", "selector": "#input", "text": "hello"}` - Type into input
- `{"type": "wait", "milliseconds": 2000}` - Wait for time
- `{"type": "scroll", "direction": "down", "amount": 500}` - Scroll page
- `{"type": "screenshot"}` - Take screenshot during action sequence

---

### batch-scrape - Multiple URL Scraping

Scrape multiple URLs concurrently. Returns a job ID for status polling.

```bash
# Batch scrape multiple URLs
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py batch-scrape https://example.com/page1 https://example.com/page2 https://example.com/page3

# Check status
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py batch-status <job_id>

# Cancel if needed
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py batch-cancel <job_id>
```

**Parameters**:
- `urls`: One or more URLs to scrape
- `--formats`: Output formats: markdown, html, links, screenshot
- `--full`: Include navigation and footer
- `--json`: Output raw JSON

**Job Management**:
```bash
# Check batch status
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py batch-status <job_id>

# Cancel a batch
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py batch-cancel <job_id>

# Get batch errors
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py batch-errors <job_id>
```

---

### crawl - Website Crawling

Crawl entire websites, following links.

```bash
# Basic crawl (50 pages max)
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py crawl "https://docs.example.com"

# Limit pages
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py crawl "https://docs.example.com" --limit 20

# Limit depth
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py crawl "https://docs.example.com" --depth 2

# Filter paths
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py crawl "https://docs.example.com" --include "/api" "/guides"

# Sitemap-only crawl (v2.8.0+) - only follow URLs in the sitemap
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py crawl "https://docs.example.com" --sitemap-only

# Async crawl for large sites
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py crawl "https://docs.example.com" --async
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py crawl-status <job_id>
```

**Parameters**:
- `-n, --limit`: Maximum pages to crawl (default: 50)
- `--depth`: Maximum link depth to follow
- `--include`: Only crawl URLs matching these paths (regex)
- `--exclude`: Skip URLs matching these paths (regex)
- `--sitemap-only`: Only crawl URLs found in the sitemap (v2.8.0+)
- `--async`: Return job ID for polling (use crawl-status)
- `--json`: Output raw JSON

**Job Management**:
```bash
# Check crawl status
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py crawl-status <job_id>

# Cancel a crawl
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py crawl-cancel <job_id>

# Get crawl errors
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py crawl-errors <job_id>

# List all active crawl jobs
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py crawl-active
```

---

### map - URL Discovery

Discover all URLs on a website. Fast way to get a site's structure.

```bash
# Map a website (up to 5000 URLs)
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py map "https://example.com"

# Limit results
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py map "https://example.com" -n 100

# Search to order by relevance
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py map "https://docs.example.com" --search "API authentication"

# Exclude subdomains
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py map "https://example.com" --no-subdomains

# Sitemap only mode
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py map "https://example.com" --sitemap only
```

**Parameters**:
- `-n, --limit`: Max URLs to return (default: 5000, max: 100000)
- `--search`: Search query to order results by relevance
- `--no-subdomains`: Exclude subdomains
- `--sitemap`: Sitemap handling: include (default), skip, or only
- `--json`: Output raw JSON

---

### extract - LLM-Powered Extraction

Extract structured data from pages using LLM. Supports wildcards for crawling.

```bash
# Extract with prompt
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py extract "https://example.com/*" --prompt "Find all pricing information"

# Extract with JSON schema
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py extract "https://example.com/pricing" \
  --schema '{"type": "object", "properties": {"price": {"type": "string"}, "features": {"type": "array"}}}'

# Enable web search for additional context
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py extract "https://example.com/*" \
  --prompt "Find company funding information" --web-search

# Check status
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py extract-status <job_id>
```

**Parameters**:
- `urls`: URLs to extract from (supports wildcards like `example.com/*`)
- `--prompt, -p`: Natural language description of data to extract
- `--schema`: JSON schema for structured output
- `--web-search`: Enable web search for additional data
- `--sources`: Show sources in response
- `--json`: Output raw JSON

---

### agent - Autonomous Extraction

The most powerful feature. Describe what data you want - the agent searches, navigates, and extracts automatically. **URLs are optional.**

```bash
# No URLs needed - agent finds the data
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py agent "Find YC W24 AI startups with funding info"

# With specific URLs (faster)
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py agent "Extract all pricing tiers" \
  --urls https://firecrawl.dev/pricing https://competitor.com/pricing

# Use spark-1-fast for simple lookups (cheapest, v2.8.0+)
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py agent "What is Anthropic's main product?" \
  --model spark-1-fast

# Use spark-1-pro for complex extractions
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py agent "Find detailed technical specs" \
  --model spark-1-pro

# Limit credits spent on this job
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py agent "Find 50 AI startups" --max-credits 100

# Async for long jobs
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py agent "Find 50 AI startups" --async
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py status <job_id>

# Cancel a running agent job
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py agent-cancel <job_id>
```

**Parameters**:
- `prompt`: Natural language description of data to find (max 10,000 chars)
- `--urls`: Optional URLs to focus extraction on
- `--model`: Agent model selection:
  - `spark-1-fast` - Instant retrieval, 10 credits/cell, simple lookups (v2.8.0+)
  - `spark-1-mini` (default) - Balanced speed/quality, general extraction
  - `spark-1-pro` - Thorough, complex multi-page research
- `--max-credits`: Maximum credits to spend on this job (budget limit)
- `--webhook`: Webhook URL for async job completion notification (v2.8.0+)
- `--async`: Start async job, return job ID
- `--json`: Output raw JSON

**Use cases**:
- Lead generation without knowing URLs
- Competitive research across multiple sites
- Dataset curation from scattered sources
- Complex navigation (login flows, pagination, dynamic content)

### parallel-agent - Bulk Agent Queries (v2.8.0+)

Run multiple agent queries in parallel with Intelligent Waterfall routing.

```bash
# Multiple queries at once
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py parallel-agent \
  "What is Anthropic's main product?" \
  "Find Stripe's pricing tiers" \
  "Get OpenAI's founding team"

# With fastest model (cheapest for bulk)
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py parallel-agent \
  "Query 1" "Query 2" "Query 3" \
  --model spark-1-fast
```

**Parameters**:
- `prompts`: Multiple queries to run in parallel
- `--urls`: Optional URLs to focus on
- `--model`: Starting model (default: spark-1-fast for waterfall routing)
- `--max-credits`: Maximum total credits
- `--webhook`: Completion notification URL
- `--json`: Output raw JSON

---

## Python SDK Examples

For more control, use the Firecrawl Python SDK directly:

### Agent with Structured Schema

```python
from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field
from typing import List, Optional

app = FirecrawlApp(api_key="fc-YOUR_API_KEY")

class Company(BaseModel):
    name: str = Field(description="Company name")
    contact_email: Optional[str] = Field(None, description="Contact email")
    funding: Optional[str] = Field(None, description="Funding amount")

class CompaniesSchema(BaseModel):
    companies: List[Company]

result = app.agent(
    prompt="Find YC W24 dev tool companies with contact info",
    schema=CompaniesSchema
)

for company in result.data.companies:
    print(f"{company.name}: {company.contact_email}")
```

### Async Agent for Large Jobs

```python
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="fc-YOUR_API_KEY")

# Start async job
agent_job = app.start_agent(prompt="Find 100 AI companies with funding info")

# Check status later
status = app.get_agent_status(agent_job.id)
if status.status == 'completed':
    print(status.data)
```

---

## Common Workflows

### Workflow 1: Single Page Scraping

```bash
# Option 1: Official CLI with clean output
firecrawl scrape https://example.com/page --only-main-content

# Option 2: Auto-save (saves to ~/Desktop/.../Web-Scrapes/)
fc-save https://example.com/page

# Option 3: Save to specific file
firecrawl scrape https://example.com/page --only-main-content -o page.md

# Option 4: Jina (backup)
jina https://example.com/page
```

### Workflow 2: Documentation Crawling

```bash
# Map the site first to find relevant URLs
firecrawl map https://docs.example.com --search "API"

# Crawl with progress tracking
firecrawl crawl https://docs.example.com --limit 50 --max-depth 3 --wait --progress -o docs.json

# Or filter to specific paths
firecrawl crawl https://docs.example.com --include-paths /api,/guides --wait --progress
```

### Workflow 3: Research Workflow

```bash
# Search and scrape results
firecrawl search "machine learning best practices 2026" --scrape --scrape-formats markdown --pretty

# Search recent content only
firecrawl search "AI news" --tbs qdr:w --limit 10  # Last week
```

### Workflow 4: Competitive Pricing Research

```bash
# Use agent (Python API) - no URLs needed
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py agent \
  "Compare pricing tiers for Firecrawl, Apify, and ScrapingBee - extract all plans with prices and features"
```

### Workflow 5: Lead Generation

```bash
# Use agent for autonomous lead finding
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py agent \
  "Find 20 B2B SaaS companies in developer tools with contact emails"
```

### Workflow 6: GitHub Repo Documentation via DeepWiki

```bash
# Quick architecture overview of any GitHub repo
~/.claude/skills/Firecrawl/scripts/deepwiki.sh karpathy/nanochat

# Browse available sections first
~/.claude/skills/Firecrawl/scripts/deepwiki.sh anthropics/anthropic-sdk-python --toc

# Deep-dive into a specific subsystem
~/.claude/skills/Firecrawl/scripts/deepwiki.sh langchain-ai/langchain 3.1-agent-system

# Dump full wiki for offline reading or RAG ingestion
~/.claude/skills/Firecrawl/scripts/deepwiki.sh openai/openai-python --all --save
```

### Workflow 7: Batch URL Scraping

```bash
# Start batch job (Python API)
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py batch-scrape \
  https://site.com/page1 https://site.com/page2 https://site.com/page3

# Check status
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py batch-status <job_id>
```

---

## Tool Selection Guide

| Task | Best Tool |
|------|-----------|
| Single page → markdown (quick auto-save) | `fc-save URL` |
| Single page with options | `firecrawl scrape URL --only-main-content` |
| Crawl entire site with progress | `firecrawl crawl URL --wait --progress` |
| Discover all site URLs | `firecrawl map URL` |
| Web search | `firecrawl search "query"` |
| Search + scrape results | `firecrawl search "query" --scrape` |
| Agent (autonomous extraction) | Python API script `agent` command |
| Batch scrape multiple URLs | Python API script `batch-scrape` command |
| LLM-powered extraction | Python API script `extract` command |
| GitHub repo documentation (AI wiki) | `deepwiki.sh owner/repo` |
| Fallback / Twitter scraping | `jina URL` |

### When to use Official CLI (`firecrawl`):
- **scrape**: Single page extraction with clean output
- **crawl**: Website crawling with `--wait --progress`
- **map**: URL discovery
- **search**: Web search with optional scraping

### When to use `fc-save`:
- Quick single page scraping
- When you want auto-save to `~/Desktop/.../Web-Scrapes/`
- Don't need crawl/map/search features

### When to use Python API Script:
- **agent**: Autonomous extraction (no URLs needed)
- **batch-scrape**: Multiple URLs concurrently
- **extract**: LLM-powered structured extraction
- Advanced features not in official CLI

### When to use DeepWiki (`deepwiki.sh`):
- Understanding a GitHub repo's architecture without reading source
- Getting structured docs for any public GitHub repo on demand
- Research workflow: `--toc` to browse, then fetch specific sections
- Full wiki dump for RAG ingestion (`--all --save`)

### When to use Jina:
- When Firecrawl fails
- Twitter/X URLs (Firecrawl blocks, Jina works)
- Alternative parsing approach

---

## File Management

**Official CLI (`firecrawl`)**: Outputs to stdout by default. Use `-o` to save:
```bash
firecrawl scrape https://example.com -o output.md
firecrawl crawl https://example.com --wait -o results.json
```

**Auto-Save Alias (`fc-save`)**: Automatically saves to:
```
~/Desktop/Screencaps & Chats/Web-Scrapes/
```

**Filename format**: `docs-example-com-api.md` (sanitized from URL)

```bash
# List recent scrapes
ls -lt ~/Desktop/Screencaps\ \&\ Chats/Web-Scrapes/ | head -10

# Pipe official CLI to other tools
firecrawl scrape https://example.com --only-main-content | head -50
firecrawl map https://example.com | wc -l
```

---

## Troubleshooting

### Check CLI status and credits:
```bash
firecrawl --status
firecrawl credit-usage
```

### Firecrawl fails to scrape:
1. Try Jina: `jina URL`
2. Check if URL is accessible in browser
3. Some sites block automated scraping
4. Try `--wait-for 3000` for JavaScript-heavy sites

### Authentication issues:
```bash
# Check current auth
firecrawl config

# Re-authenticate
firecrawl logout
firecrawl login --api-key $FIRECRAWL_API_KEY
```

### API errors:
1. Verify FIRECRAWL_API_KEY is set: `echo $FIRECRAWL_API_KEY`
2. Check credits: `firecrawl credit-usage`
3. Review error message for rate limits or quota

### Async job not completing (Python API script):
1. Check status: `crawl-status`, `batch-status`, or `extract-status`
2. Large jobs may take several minutes
3. Cancel if stuck: `crawl-cancel` or `batch-cancel`

### Disable telemetry (optional):
```bash
export FIRECRAWL_NO_TELEMETRY=1
```

---

## Reference Documentation

For detailed API documentation and advanced features, see:
- `references/firecrawl-api.md` - Firecrawl Search API reference
- `references/firecrawl-agent-api.md` - Firecrawl Agent API for autonomous extraction (spark-1-fast/mini/pro models, parallel agents, webhooks, maxCredits)
- `references/actions-reference.md` - Page actions for dynamic content (click, write, wait, scroll)
- `references/branding-format.md` - Brand identity extraction (colors, fonts, UI components)

## Test Suite

Verify your Firecrawl setup:

```bash
# Run all tests
python3 ~/.claude/skills/Firecrawl/scripts/test_firecrawl.py

# Quick tests only (no async jobs)
python3 ~/.claude/skills/Firecrawl/scripts/test_firecrawl.py --quick

# Verbose output
python3 ~/.claude/skills/Firecrawl/scripts/test_firecrawl.py --verbose

# Specific test
python3 ~/.claude/skills/Firecrawl/scripts/test_firecrawl.py --test scrape
```
