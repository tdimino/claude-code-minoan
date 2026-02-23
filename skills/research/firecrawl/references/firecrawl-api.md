# Firecrawl API Reference

This document provides detailed information about the Firecrawl API, specifically the Search endpoint and advanced scraping features.

**Note**: This reference covers the Python/Node API. For simple single-page scraping, use the local CLI command `firecrawl scrape URL` instead.

## Search Endpoint Overview

The `/search` endpoint performs web searches and optionally retrieves content from the search results in one operation.

**Key capabilities**:
- Search the web with customizable parameters
- Automatically scrape search results
- Filter by categories (GitHub, Research, PDF)
- Filter by sources (web, news, images)
- Time-based filtering
- Location customization
- Content extraction in multiple formats

## Installation

```python
# Python
pip install firecrawl-py

from firecrawl import Firecrawl
firecrawl = Firecrawl(api_key="fc-YOUR-API-KEY")
```

```javascript
// Node.js
npm install @mendable/firecrawl-js

import Firecrawl from '@mendable/firecrawl-js';
const firecrawl = new Firecrawl({ apiKey: 'fc-YOUR-API-KEY' });
```

## Basic Search

```python
from firecrawl import Firecrawl

firecrawl = Firecrawl(api_key="fc-YOUR-API-KEY")

results = firecrawl.search(
    query="firecrawl",
    limit=3,
)
print(results)
```

**Response structure**:
```json
{
  "success": true,
  "data": {
    "web": [
      {
        "url": "https://www.firecrawl.dev/",
        "title": "Firecrawl - The Web Data API for AI",
        "description": "The web crawling, scraping, and search API for AI...",
        "position": 1
      }
    ],
    "images": [
      {
        "title": "Quickstart | Firecrawl",
        "imageUrl": "https://...",
        "imageWidth": 5814,
        "imageHeight": 1200,
        "url": "https://docs.firecrawl.dev/",
        "position": 1
      }
    ],
    "news": [
      {
        "title": "Y Combinator startup Firecrawl...",
        "url": "https://techcrunch.com/...",
        "snippet": "...",
        "date": "3 months ago",
        "position": 1
      }
    ]
  }
}
```

## Search Result Types

Use the `sources` parameter to specify result types:

**Available sources**:
- `web` (default) - Standard web results
- `news` - News-focused results
- `images` - Image search results

**Examples**:

```python
# News search
results = firecrawl.search(
    "openai",
    sources=["news"],
    limit=5
)

# Image search
results = firecrawl.search(
    "jupiter",
    sources=["images"],
    limit=8
)
```

## Search Categories

Filter results by specific categories using the `categories` parameter:

**Available categories**:
- `github` - GitHub repositories, code, issues, documentation
- `research` - Academic/research websites (arXiv, Nature, IEEE, PubMed)
- `pdf` - PDF documents

### GitHub Category Search

```python
results = firecrawl.search(
    "web scraping python",
    categories=["github"],
    limit=10
)
```

**Use cases**:
- Find code examples and implementations
- Discover relevant repositories
- Search through GitHub issues and discussions

### Research Category Search

```python
results = firecrawl.search(
    "machine learning transformers",
    categories=["research"],
    limit=10
)
```

**Use cases**:
- Academic paper discovery
- Research literature review
- Finding scholarly articles

**Covered sources**:
- arXiv
- Nature
- IEEE
- PubMed
- Other academic databases

### Mixed Category Search

Combine multiple categories:

```python
results = firecrawl.search(
    "neural networks",
    categories=["github", "research"],
    limit=15
)
```

**Response includes category field**:
```json
{
  "url": "https://github.com/example/neural-network",
  "title": "Neural Network Implementation",
  "description": "A PyTorch implementation...",
  "category": "github"
}
```

## HD Image Search

Use Google Images operators to find high-resolution images:

```python
# Find specific resolution
results = firecrawl.search(
    "sunset imagesize:1920x1080",
    sources=["images"],
    limit=5
)

# Find images larger than resolution
results = firecrawl.search(
    "mountain wallpaper larger:2560x1440",
    sources=["images"],
    limit=8
)
```

**Common HD resolutions**:
- `imagesize:1920x1080` - Full HD (1080p)
- `imagesize:2560x1440` - QHD (1440p)
- `imagesize:3840x2160` - 4K UHD
- `larger:1920x1080` - HD and above
- `larger:2560x1440` - QHD and above

## Search with Content Scraping

Search and retrieve content from results in one operation:

```python
from firecrawl import Firecrawl

firecrawl = Firecrawl(api_key="fc-YOUR_API_KEY")

# Search and scrape content
results = firecrawl.search(
    "firecrawl web scraping",
    limit=3,
    scrape_options={
        "formats": ["markdown", "links"]
    }
)
```

**Every option from the scrape endpoint is supported** through the `scrape_options` parameter.

**Response with scraped content**:
```json
{
  "success": true,
  "data": [
    {
      "title": "Firecrawl - The Ultimate Web Scraping API",
      "description": "Firecrawl is a powerful web scraping API...",
      "url": "https://firecrawl.dev/",
      "markdown": "# Firecrawl\n\nThe Ultimate Web Scraping API...",
      "links": [
        "https://firecrawl.dev/pricing",
        "https://firecrawl.dev/docs",
        "https://firecrawl.dev/guides"
      ],
      "metadata": {
        "title": "Firecrawl - The Ultimate Web Scraping API",
        "description": "...",
        "sourceURL": "https://firecrawl.dev/",
        "statusCode": 200
      }
    }
  ]
}
```

## Advanced Search Options

### Location Customization

Search results geotargeted to specific location:

```python
from firecrawl import Firecrawl

firecrawl = Firecrawl(api_key="fc-YOUR_API_KEY")

# Search with location settings
search_result = firecrawl.search(
    "web scraping tools",
    limit=5,
    location="Germany"
)

# Process results
for result in search_result.data:
    print(f"Title: {result['title']}")
    print(f"URL: {result['url']}")
```

### Time-Based Search

Filter results by recency using the `tbs` parameter:

**Common time filters**:
- `qdr:h` - Past hour
- `qdr:d` - Past 24 hours
- `qdr:w` - Past week
- `qdr:m` - Past month
- `qdr:y` - Past year

**Example**:
```python
# Results from past 24 hours
results = firecrawl.search(
    query="firecrawl",
    limit=5,
    tbs="qdr:d",
)
```

**Custom date range**:
```python
# Results from specific date range (December 2024)
search_result = firecrawl.search(
    "firecrawl updates",
    limit=10,
    tbs="cdr:1,cd_min:12/1/2024,cd_max:12/31/2024"
)
```

**Format**: `cdr:1,cd_min:MM/DD/YYYY,cd_max:MM/DD/YYYY`

### Custom Timeout

Set custom timeout for search operations:

```python
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="fc-YOUR_API_KEY")

# Set 30-second timeout
search_result = app.search(
    "complex search query",
    limit=10,
    timeout=30000  # milliseconds
)
```

## Cost Implications

**Base costs**:
- Basic search (no scraping): 2 credits per 10 results
- Basic scraping: Standard scraping costs (no additional charge)

**Additional costs**:
- PDF parsing: +1 credit per PDF page
- Stealth proxy mode: +4 credits per result
- JSON mode: +4 credits per result

**Cost optimization strategies**:
- Use `limit` parameter to control result count
- Set `parsers: []` if PDF content not needed
- Use `proxy: "basic"` instead of `"stealth"`
- Avoid scraping when search results alone are sufficient

## Advanced Scraping Options

All scraping options from the Scrape endpoint are supported via the `scrape_options` parameter:

```python
results = firecrawl.search(
    "technical documentation",
    limit=5,
    scrape_options={
        "formats": ["markdown", "html", "links", "screenshot"],
        "onlyMainContent": True,
        "includeTags": ["article", "main"],
        "excludeTags": ["nav", "footer", "aside"],
        "timeout": 30000,
        "proxy": "basic"  # or "stealth" for harder sites
    }
)
```

**Supported formats**:
- `markdown` - Clean markdown output (recommended)
- `html` - Raw HTML
- `links` - Extract all links
- `screenshot` - Page screenshot

**Content filtering**:
- `onlyMainContent: true` - Extract main content only
- `includeTags` - Whitelist specific HTML tags
- `excludeTags` - Blacklist specific HTML tags

**Performance options**:
- `timeout` - Custom timeout in milliseconds
- `proxy` - "basic" (faster, cheaper) or "stealth" (bypasses blocks)

**Note**: FIRE-1 Agent and Change-Tracking features are NOT supported by the Search endpoint.

## Complete Example: Research Workflow

```python
from firecrawl import Firecrawl

firecrawl = Firecrawl(api_key="fc-YOUR-API-KEY")

# Step 1: Search research papers and GitHub repos
results = firecrawl.search(
    "transformer architecture attention mechanism",
    categories=["research", "github"],
    limit=10,
    tbs="qdr:y",  # Past year only
    scrape_options={
        "formats": ["markdown", "links"],
        "onlyMainContent": True
    }
)

# Step 2: Process results
for result in results['data']:
    category = result.get('category', 'web')
    print(f"[{category.upper()}] {result['title']}")
    print(f"URL: {result['url']}")

    if 'markdown' in result:
        # Content was scraped
        print(f"Content length: {len(result['markdown'])} chars")

    print("---")

# Step 3: Filter by category
github_results = [r for r in results['data'] if r.get('category') == 'github']
research_results = [r for r in results['data'] if r.get('category') == 'research']

print(f"\nFound {len(github_results)} GitHub repositories")
print(f"Found {len(research_results)} research papers")
```

## Common Use Cases

### 1. Documentation Discovery
```python
# Find official documentation
results = firecrawl.search(
    "firecrawl API documentation",
    limit=5,
    scrape_options={"formats": ["markdown"]}
)
```

### 2. Code Example Search
```python
# Find code examples on GitHub
results = firecrawl.search(
    "python web scraping BeautifulSoup",
    categories=["github"],
    limit=10
)
```

### 3. Latest News
```python
# Recent news articles
results = firecrawl.search(
    "artificial intelligence",
    sources=["news"],
    tbs="qdr:d",  # Past day
    limit=10
)
```

### 4. Academic Research
```python
# Research papers
results = firecrawl.search(
    "large language models",
    categories=["research"],
    limit=15,
    scrape_options={"formats": ["markdown"]}
)
```

### 5. Image Collection
```python
# HD images
results = firecrawl.search(
    "nature photography larger:2560x1440",
    sources=["images"],
    limit=20
)
```

## Error Handling

```python
try:
    results = firecrawl.search(
        "search query",
        limit=10,
        timeout=30000
    )

    if results.get('success'):
        data = results.get('data', {})
        web_results = data.get('web', [])
        print(f"Found {len(web_results)} results")
    else:
        print("Search failed:", results.get('error'))

except Exception as e:
    print(f"Error during search: {str(e)}")
```

## Best Practices

1. **Use categories** to narrow results (github, research, pdf)
2. **Limit results** to control costs and processing time
3. **Add time filters** for current information (tbs parameter)
4. **Enable scraping selectively** - only when you need full content
5. **Use markdown format** for AI/LLM processing
6. **Set reasonable timeouts** for complex queries
7. **Handle errors gracefully** with try/except blocks
8. **Filter unwanted content** with includeTags/excludeTags
9. **Use basic proxy** unless stealth is absolutely needed
10. **Validate results** before processing

## Limitations

**Search endpoint does NOT support**:
- FIRE-1 Agent features
- Change-Tracking features
- Crawling (use /crawl endpoint instead)
- Map features (use /map endpoint instead)

**For these features**, use the appropriate specialized endpoints.

## Additional Resources

- Official Firecrawl Documentation: https://docs.firecrawl.dev/
- Search API Reference: https://docs.firecrawl.dev/api-reference/endpoint/search
- Scrape Features: https://docs.firecrawl.dev/features/scrape
- Advanced Scraping Guide: https://docs.firecrawl.dev/advanced-scraping-guide
- Python SDK: https://github.com/mendableai/firecrawl
- Node.js SDK: https://www.npmjs.com/package/@mendable/firecrawl-js
