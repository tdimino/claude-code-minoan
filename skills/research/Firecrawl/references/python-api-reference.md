# Firecrawl Python API Reference

Complete reference for `python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py <command>`.

**Requires**: `FIRECRAWL_API_KEY` environment variable, `pip install firecrawl-py requests`

---

## search — Web Search

```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py search "query" [options]
```

| Parameter | Description |
|-----------|-------------|
| `-n, --limit` | Number of results (default: 10) |
| `--categories` | Filter: github, research, pdf |
| `--sources` | Result types: web, news, images |
| `--time` | Time filter: qdr:h (hour), qdr:d (day), qdr:w (week), qdr:m (month) |
| `--location` | Geotarget results |
| `--scrape` | Also scrape content from results |
| `--json` | Output raw JSON |

```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py search "web scraping best practices" -n 10
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py search "python web scraping" --categories github
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py search "AI news" --time qdr:d
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py search "firecrawl examples" --scrape
```

---

## scrape — Single URL Extraction

```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py scrape URL [options]
```

| Parameter | Description |
|-----------|-------------|
| `--formats` | Output: markdown, html, links, screenshot, summary, images, branding |
| `--full` | Include navigation and footer |
| `--actions` | JSON array of page actions (click, write, wait, scroll) |
| `--country` | Country code for geo-targeting (US, GB, DE) |
| `--languages` | Language codes (en-US, es) |
| `--max-age` | Use cached result if fresher than N seconds |
| `--no-cache` | Don't cache this result |
| `--json` | Output raw JSON |

**Page Actions** (for dynamic content):
```json
[
  {"type": "click", "selector": "#button"},
  {"type": "write", "selector": "#input", "text": "hello"},
  {"type": "wait", "milliseconds": 2000},
  {"type": "scroll", "direction": "down", "amount": 500},
  {"type": "screenshot"}
]
```

```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py scrape "https://example.com" --formats markdown html links summary
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py scrape "https://example.com" --formats branding
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py scrape "https://example.com" --country US --languages en-US es
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py scrape "https://example.com" --max-age 3600
```

---

## batch-scrape — Multiple URL Scraping

```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py batch-scrape URL1 URL2 URL3 [options]
```

| Parameter | Description |
|-----------|-------------|
| `--formats` | Output: markdown, html, links, screenshot |
| `--full` | Include navigation and footer |
| `--json` | Output raw JSON |

**Job Management:**
```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py batch-status <job_id>
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py batch-cancel <job_id>
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py batch-errors <job_id>
```

---

## crawl — Website Crawling

```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py crawl URL [options]
```

| Parameter | Description |
|-----------|-------------|
| `-n, --limit` | Maximum pages (default: 50) |
| `--depth` | Maximum link depth |
| `--include` | Only crawl URLs matching these paths (regex) |
| `--exclude` | Skip URLs matching these paths (regex) |
| `--sitemap-only` | Only crawl URLs in sitemap (v2.8.0+) |
| `--async` | Return job ID for polling |
| `--json` | Output raw JSON |

**Job Management:**
```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py crawl-status <job_id>
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py crawl-cancel <job_id>
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py crawl-errors <job_id>
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py crawl-active
```

---

## map — URL Discovery

```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py map URL [options]
```

| Parameter | Description |
|-----------|-------------|
| `-n, --limit` | Max URLs (default: 5000, max: 100000) |
| `--search` | Search query to order by relevance |
| `--no-subdomains` | Exclude subdomains |
| `--sitemap` | Sitemap handling: include, skip, only |
| `--json` | Output raw JSON |

---

## extract — LLM-Powered Extraction

```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py extract URL [options]
```

| Parameter | Description |
|-----------|-------------|
| `--prompt, -p` | Natural language description of data to extract |
| `--schema` | JSON schema for structured output |
| `--web-search` | Enable web search for additional data |
| `--sources` | Show sources in response |
| `--json` | Output raw JSON |

```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py extract "https://example.com/*" --prompt "Find all pricing"
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py extract "https://example.com/pricing" \
  --schema '{"type": "object", "properties": {"price": {"type": "string"}, "features": {"type": "array"}}}'
```

---

## agent — Autonomous Extraction

The most powerful feature. Describe what data you want—the agent searches, navigates, and extracts automatically. **URLs are optional.**

```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py agent "prompt" [options]
```

| Parameter | Description |
|-----------|-------------|
| `--urls` | Optional URLs to focus on |
| `--model` | `spark-1-fast` (10 credits, simple), `spark-1-mini` (default), `spark-1-pro` (thorough) |
| `--max-credits` | Budget limit |
| `--webhook` | Completion notification URL (v2.8.0+) |
| `--async` | Start async job |
| `--json` | Output raw JSON |

```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py agent "Find YC W24 AI startups with funding"
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py agent "What is Anthropic's main product?" --model spark-1-fast
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py agent "Find detailed technical specs" --model spark-1-pro
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py agent "Find 50 AI startups" --max-credits 100 --async
```

**Job Management:**
```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py status <job_id>
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py agent-cancel <job_id>
```

---

## extract-status — Check Extract Job

```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py extract-status <job_id>
```

Polls an async extract job until completion and returns the results.

---

## parallel-agent — Bulk Agent Queries (v2.8.0+)

Run multiple agent queries with Intelligent Waterfall routing.

```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py parallel-agent "Q1" "Q2" "Q3" [options]
```

| Parameter | Description |
|-----------|-------------|
| `--urls` | Optional URLs to focus on |
| `--model` | Starting model (default: spark-1-fast for waterfall) |
| `--max-credits` | Maximum total credits |
| `--webhook` | Completion notification URL |
| `--json` | Output raw JSON |

---

## Python SDK Examples

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

agent_job = app.start_agent(prompt="Find 100 AI companies with funding info")

status = app.get_agent_status(agent_job.id)
if status.status == 'completed':
    print(status.data)
```
