#!/usr/bin/env python3
"""
Firecrawl API wrapper for comprehensive web scraping and data extraction.

Provides direct API access to ALL Firecrawl v2 endpoints:
- search: Search the web with optional content scraping
- scrape: Extract content from a single URL
- batch-scrape: Scrape multiple URLs concurrently
- crawl: Crawl entire sites with link following
- map: Discover all URLs on a website
- extract: LLM-powered structured data extraction
- agent: Autonomous multi-page data extraction

Job management:
- crawl-status / batch-status / extract-status: Check job status
- crawl-cancel / batch-cancel: Cancel running jobs

Usage:
    python firecrawl_api.py search "web scraping best practices"
    python firecrawl_api.py scrape "https://example.com/page"
    python firecrawl_api.py batch-scrape URL1 URL2 URL3
    python firecrawl_api.py crawl "https://docs.example.com" --limit 10
    python firecrawl_api.py map "https://example.com" --limit 100
    python firecrawl_api.py extract "https://example.com/*" --prompt "Find pricing"
    python firecrawl_api.py agent "Find YC W24 AI startups with funding info"

Requires: FIRECRAWL_API_KEY environment variable
Install: pip install firecrawl-py requests
"""

import os
import sys
import json
import argparse
import time
from typing import Optional, List, Dict, Any

try:
    from firecrawl import FirecrawlApp
    HAS_FIRECRAWL_SDK = True
except ImportError:
    HAS_FIRECRAWL_SDK = False
    import requests

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY")
BASE_URL = "https://api.firecrawl.dev/v1"
BASE_URL_V2 = "https://api.firecrawl.dev/v2"


def _get_app() -> 'FirecrawlApp':
    """Get FirecrawlApp instance with API key."""
    if not FIRECRAWL_API_KEY:
        raise ValueError("FIRECRAWL_API_KEY environment variable not set")
    return FirecrawlApp(api_key=FIRECRAWL_API_KEY)


def _headers() -> Dict[str, str]:
    """Get headers for direct API calls."""
    if not FIRECRAWL_API_KEY:
        raise ValueError("FIRECRAWL_API_KEY environment variable not set")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}"
    }


def search(
    query: str,
    limit: int = 10,
    categories: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    tbs: Optional[str] = None,
    location: Optional[str] = None,
    scrape: bool = False,
    scrape_formats: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Search the web using Firecrawl's search endpoint.

    Args:
        query: Search query string
        limit: Number of results to return (default: 10)
        categories: Filter by category - "github", "research", "pdf"
        sources: Result types - "web", "news", "images"
        tbs: Time filter - "qdr:h" (hour), "qdr:d" (day), "qdr:w" (week), "qdr:m" (month)
        location: Geotarget results (e.g., "Germany", "United States")
        scrape: Whether to scrape content from results
        scrape_formats: Formats for scraped content - ["markdown", "html", "links"]

    Returns:
        Dict with search results, optionally with scraped content
    """
    payload = {
        "query": query,
        "limit": limit
    }

    if categories:
        payload["categories"] = categories
    if sources:
        payload["sources"] = sources
    if tbs:
        payload["tbs"] = tbs
    if location:
        payload["location"] = location

    if scrape:
        payload["scrapeOptions"] = {
            "formats": scrape_formats or ["markdown"]
        }

    if HAS_FIRECRAWL_SDK:
        app = _get_app()
        return app.search(query, **{k: v for k, v in payload.items() if k != "query"})
    else:
        response = requests.post(
            f"{BASE_URL}/search",
            headers=_headers(),
            json=payload
        )
        response.raise_for_status()
        return response.json()


def scrape(
    url: str,
    formats: Optional[List[str]] = None,
    only_main_content: bool = True,
    include_tags: Optional[List[str]] = None,
    exclude_tags: Optional[List[str]] = None,
    timeout: int = 30000,
    actions: Optional[List[Dict[str, Any]]] = None,
    location: Optional[Dict[str, Any]] = None,
    max_age: Optional[int] = None,
    store_in_cache: bool = True
) -> Dict[str, Any]:
    """
    Scrape a single URL and extract content.

    Args:
        url: URL to scrape
        formats: Output formats - ["markdown", "html", "links", "screenshot", "summary", "images", "branding"]
        only_main_content: Extract only main content, skip nav/footer
        include_tags: Whitelist specific HTML tags
        exclude_tags: Blacklist specific HTML tags
        timeout: Timeout in milliseconds
        actions: Page actions to perform before scraping (click, write, wait, scroll, screenshot)
                 Example: [{"type": "click", "selector": "#load-more"}, {"type": "wait", "milliseconds": 2000}]
        location: Geo-targeting - {"country": "US", "languages": ["en-US"]}
        max_age: Maximum cache age in seconds (use cached result if fresher)
        store_in_cache: Whether to cache this scrape result (default: True)

    Returns:
        Dict with scraped content in requested formats
    """
    payload = {
        "url": url,
        "formats": formats or ["markdown"],
        "onlyMainContent": only_main_content,
        "timeout": timeout
    }

    if include_tags:
        payload["includeTags"] = include_tags
    if exclude_tags:
        payload["excludeTags"] = exclude_tags
    if actions:
        payload["actions"] = actions
    if location:
        payload["location"] = location
    if max_age is not None:
        payload["maxAge"] = max_age
    if not store_in_cache:
        payload["storeInCache"] = False

    if HAS_FIRECRAWL_SDK:
        app = _get_app()
        return app.scrape_url(url, params={k: v for k, v in payload.items() if k != "url"})
    else:
        response = requests.post(
            f"{BASE_URL}/scrape",
            headers=_headers(),
            json=payload
        )
        response.raise_for_status()
        return response.json()


def agent(
    prompt: str,
    urls: Optional[List[str]] = None,
    schema: Optional[Dict[str, Any]] = None,
    async_mode: bool = False,
    model: str = "spark-1-mini",
    max_credits: Optional[int] = None
) -> Dict[str, Any]:
    """
    Autonomous web extraction using natural language prompts.

    The agent searches, navigates, and extracts data automatically.
    URLs are optional - the agent can find relevant pages itself.

    Args:
        prompt: Natural language description of data to extract (max 10,000 chars)
        urls: Optional list of URLs to focus extraction on
        schema: Optional JSON schema for structured output
        async_mode: If True, start job and return job ID for polling
        model: Agent model - "spark-1-mini" (default, 60% cheaper) or "spark-1-pro" (more capable)
        max_credits: Maximum credits to spend on this agent job (budget limit)

    Returns:
        Dict with extracted data, or job info if async_mode=True
    """
    if not HAS_FIRECRAWL_SDK:
        raise RuntimeError("Firecrawl SDK required for agent. Install: pip install firecrawl-py")

    app = _get_app()

    # Build kwargs for SDK calls
    kwargs = {"prompt": prompt}
    if urls:
        kwargs["urls"] = urls
    if schema:
        kwargs["schema"] = schema
    if model != "spark-1-mini":
        kwargs["model"] = model
    if max_credits is not None:
        kwargs["maxCredits"] = max_credits

    if async_mode:
        # Start async job
        agent_job = app.start_agent(**kwargs)
        return {
            "job_id": agent_job.id,
            "status": "processing",
            "message": f"Job started. Check status with: python firecrawl_api.py status {agent_job.id}"
        }
    else:
        # Synchronous execution
        result = app.agent(**kwargs)
        return {
            "success": True,
            "data": result.data if hasattr(result, 'data') else result
        }


def cancel_agent(job_id: str) -> Dict[str, Any]:
    """
    Cancel a running agent job.

    Args:
        job_id: The job ID to cancel

    Returns:
        Dict with cancellation status
    """
    response = requests.delete(
        f"{BASE_URL_V2}/agent/{job_id}",
        headers=_headers()
    )
    response.raise_for_status()
    return response.json()


def get_agent_status(job_id: str) -> Dict[str, Any]:
    """
    Check status of an async agent job.

    Args:
        job_id: The job ID from start_agent

    Returns:
        Dict with status and data if completed
    """
    if not HAS_FIRECRAWL_SDK:
        raise RuntimeError("Firecrawl SDK required. Install: pip install firecrawl-py")

    app = _get_app()
    status = app.get_agent_status(job_id)

    return {
        "job_id": job_id,
        "status": status.status,
        "credits_used": getattr(status, 'credits_used', None),
        "data": status.data if status.status == "completed" else None
    }


def crawl(
    url: str,
    limit: int = 50,
    max_depth: Optional[int] = None,
    include_paths: Optional[List[str]] = None,
    exclude_paths: Optional[List[str]] = None,
    formats: Optional[List[str]] = None,
    async_mode: bool = False
) -> Dict[str, Any]:
    """
    Crawl an entire website, following links.

    Args:
        url: Starting URL to crawl
        limit: Maximum pages to crawl (default: 50)
        max_depth: Maximum link depth to follow
        include_paths: Only crawl URLs matching these paths (regex)
        exclude_paths: Skip URLs matching these paths (regex)
        formats: Output formats for each page
        async_mode: If True, return job ID for polling

    Returns:
        Dict with crawled pages, or job info if async_mode=True
    """
    payload = {
        "url": url,
        "limit": limit,
        "scrapeOptions": {
            "formats": formats or ["markdown"]
        }
    }

    if max_depth is not None:
        payload["maxDepth"] = max_depth
    if include_paths:
        payload["includePaths"] = include_paths
    if exclude_paths:
        payload["excludePaths"] = exclude_paths

    if HAS_FIRECRAWL_SDK:
        app = _get_app()
        if async_mode:
            result = app.async_crawl_url(url, params={k: v for k, v in payload.items() if k != "url"})
            return {
                "job_id": result.get('id'),
                "status": "processing",
                "message": f"Crawl started. Check status with: python firecrawl_api.py crawl-status {result.get('id')}"
            }
        else:
            return app.crawl_url(url, params={k: v for k, v in payload.items() if k != "url"})
    else:
        endpoint = f"{BASE_URL}/crawl"
        response = requests.post(endpoint, headers=_headers(), json=payload)
        response.raise_for_status()
        return response.json()


def get_crawl_status(job_id: str) -> Dict[str, Any]:
    """
    Check status of an async crawl job.

    Args:
        job_id: The job ID from async crawl

    Returns:
        Dict with status and crawled pages if completed
    """
    response = requests.get(
        f"{BASE_URL}/crawl/{job_id}",
        headers=_headers()
    )
    response.raise_for_status()
    return response.json()


def cancel_crawl(job_id: str) -> Dict[str, Any]:
    """
    Cancel a running crawl job.

    Args:
        job_id: The job ID to cancel

    Returns:
        Dict with cancellation status
    """
    response = requests.delete(
        f"{BASE_URL}/crawl/{job_id}",
        headers=_headers()
    )
    response.raise_for_status()
    return response.json()


def get_crawl_errors(job_id: str) -> Dict[str, Any]:
    """
    Get errors from a crawl job.

    Args:
        job_id: The job ID to get errors for

    Returns:
        Dict with crawl errors
    """
    response = requests.get(
        f"{BASE_URL}/crawl/{job_id}/errors",
        headers=_headers()
    )
    response.raise_for_status()
    return response.json()


def get_active_crawls() -> Dict[str, Any]:
    """
    Get all currently active crawl jobs.

    Returns:
        Dict with list of active crawl jobs
    """
    response = requests.get(
        f"{BASE_URL}/crawl/active",
        headers=_headers()
    )
    response.raise_for_status()
    return response.json()


def batch_scrape(
    urls: List[str],
    formats: Optional[List[str]] = None,
    only_main_content: bool = True,
    include_tags: Optional[List[str]] = None,
    exclude_tags: Optional[List[str]] = None,
    timeout: int = 30000,
    async_mode: bool = True
) -> Dict[str, Any]:
    """
    Scrape multiple URLs concurrently.

    Args:
        urls: List of URLs to scrape
        formats: Output formats - ["markdown", "html", "links", "screenshot"]
        only_main_content: Extract only main content
        include_tags: Whitelist specific HTML tags
        exclude_tags: Blacklist specific HTML tags
        timeout: Timeout in milliseconds per page
        async_mode: Always async (returns job ID for polling)

    Returns:
        Dict with job ID for status polling
    """
    payload = {
        "urls": urls,
        "formats": formats or ["markdown"],
        "onlyMainContent": only_main_content,
        "timeout": timeout
    }

    if include_tags:
        payload["includeTags"] = include_tags
    if exclude_tags:
        payload["excludeTags"] = exclude_tags

    response = requests.post(
        f"{BASE_URL_V2}/batch/scrape",
        headers=_headers(),
        json=payload
    )
    response.raise_for_status()
    return response.json()


def get_batch_status(job_id: str) -> Dict[str, Any]:
    """
    Check status of a batch scrape job.

    Args:
        job_id: The job ID from batch_scrape

    Returns:
        Dict with status and scraped pages if completed
    """
    response = requests.get(
        f"{BASE_URL_V2}/batch/scrape/{job_id}",
        headers=_headers()
    )
    response.raise_for_status()
    return response.json()


def cancel_batch(job_id: str) -> Dict[str, Any]:
    """
    Cancel a running batch scrape job.

    Args:
        job_id: The job ID to cancel

    Returns:
        Dict with cancellation status
    """
    response = requests.delete(
        f"{BASE_URL_V2}/batch/scrape/{job_id}",
        headers=_headers()
    )
    response.raise_for_status()
    return response.json()


def get_batch_errors(job_id: str) -> Dict[str, Any]:
    """
    Get errors from a batch scrape job.

    Args:
        job_id: The job ID to get errors for

    Returns:
        Dict with batch scrape errors
    """
    response = requests.get(
        f"{BASE_URL_V2}/batch/scrape/{job_id}/errors",
        headers=_headers()
    )
    response.raise_for_status()
    return response.json()


def map_site(
    url: str,
    search: Optional[str] = None,
    limit: int = 5000,
    include_subdomains: bool = True,
    ignore_query_parameters: bool = True,
    sitemap: str = "include",
    timeout: Optional[int] = None
) -> Dict[str, Any]:
    """
    Map all URLs on a website.

    Discovers all pages on a site using sitemap, crawling, and internal links.

    Args:
        url: Base URL to map
        search: Search query to order results by relevance
        limit: Maximum URLs to return (max: 100000)
        include_subdomains: Include subdomains
        ignore_query_parameters: Exclude URLs with query params
        sitemap: Sitemap handling - "include", "skip", or "only"
        timeout: Timeout in milliseconds

    Returns:
        Dict with discovered URLs, titles, and descriptions
    """
    payload = {
        "url": url,
        "limit": min(limit, 100000),
        "includeSubdomains": include_subdomains,
        "ignoreQueryParameters": ignore_query_parameters,
        "sitemap": sitemap
    }

    if search:
        payload["search"] = search
    if timeout:
        payload["timeout"] = timeout

    response = requests.post(
        f"{BASE_URL_V2}/map",
        headers=_headers(),
        json=payload
    )
    response.raise_for_status()
    return response.json()


def extract(
    urls: List[str],
    prompt: Optional[str] = None,
    schema: Optional[Dict[str, Any]] = None,
    enable_web_search: bool = False,
    include_subdomains: bool = True,
    ignore_sitemap: bool = False,
    show_sources: bool = False
) -> Dict[str, Any]:
    """
    Extract structured data from pages using LLM.

    Args:
        urls: URLs (supports wildcards like "example.com/*")
        prompt: Natural language description of data to extract
        schema: JSON schema for structured output
        enable_web_search: Use web search for additional data
        include_subdomains: Include subdomains in extraction
        ignore_sitemap: Skip sitemap.xml
        show_sources: Include sources in response

    Returns:
        Dict with job ID for status polling
    """
    if not prompt and not schema:
        raise ValueError("Either prompt or schema is required")

    payload = {
        "urls": urls,
        "enableWebSearch": enable_web_search,
        "includeSubdomains": include_subdomains,
        "ignoreSitemap": ignore_sitemap,
        "showSources": show_sources
    }

    if prompt:
        payload["prompt"] = prompt
    if schema:
        payload["schema"] = schema

    response = requests.post(
        f"{BASE_URL_V2}/extract",
        headers=_headers(),
        json=payload
    )
    response.raise_for_status()
    return response.json()


def get_extract_status(job_id: str) -> Dict[str, Any]:
    """
    Check status of an extract job.

    Args:
        job_id: The job ID from extract

    Returns:
        Dict with status and extracted data if completed
    """
    response = requests.get(
        f"{BASE_URL_V2}/extract/{job_id}",
        headers=_headers()
    )
    response.raise_for_status()
    return response.json()


def format_search_results(results: Dict[str, Any], max_text_length: int = 500) -> str:
    """Format search results for display."""
    output = []
    data = results.get("data", results)

    # Handle different response formats
    if isinstance(data, dict):
        for source_type in ["web", "news", "images"]:
            items = data.get(source_type, [])
            if items:
                output.append(f"\n=== {source_type.upper()} RESULTS ===")
                for i, r in enumerate(items, 1):
                    output.append(f"\n[{i}] {r.get('title', 'No title')}")
                    output.append(f"    URL: {r.get('url', 'No URL')}")
                    if r.get('description'):
                        desc = r['description'][:max_text_length]
                        output.append(f"    {desc}")
                    if r.get('markdown'):
                        text = r['markdown'][:max_text_length]
                        output.append(f"    Content: {text}...")
    elif isinstance(data, list):
        for i, r in enumerate(data, 1):
            output.append(f"\n{'='*60}")
            output.append(f"[{i}] {r.get('title', 'No title')}")
            output.append(f"    URL: {r.get('url', 'No URL')}")
            if r.get('markdown'):
                text = r['markdown'][:max_text_length]
                output.append(f"    Content: {text}...")

    return "\n".join(output) if output else "No results found"


def format_scrape_result(result: Dict[str, Any], max_text_length: int = 2000) -> str:
    """Format scrape result for display."""
    output = []
    data = result.get("data", result)

    if isinstance(data, dict):
        output.append(f"URL: {data.get('url', data.get('sourceURL', 'Unknown'))}")
        output.append(f"Title: {data.get('title', 'No title')}")

        if data.get('markdown'):
            text = data['markdown'][:max_text_length]
            if len(data['markdown']) > max_text_length:
                text += "\n... [truncated]"
            output.append(f"\n{text}")

        if data.get('links'):
            output.append(f"\nLinks found: {len(data['links'])}")
            for link in data['links'][:10]:
                output.append(f"  - {link}")
            if len(data['links']) > 10:
                output.append(f"  ... and {len(data['links']) - 10} more")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Firecrawl API wrapper for web scraping and autonomous extraction"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search the web")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-n", "--limit", type=int, default=10, help="Number of results")
    search_parser.add_argument("--categories", nargs="+", help="Filter: github, research, pdf")
    search_parser.add_argument("--sources", nargs="+", help="Types: web, news, images")
    search_parser.add_argument("--time", dest="tbs", help="Time filter: qdr:h, qdr:d, qdr:w, qdr:m")
    search_parser.add_argument("--location", help="Geotarget results")
    search_parser.add_argument("--scrape", action="store_true", help="Also scrape result pages")
    search_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape a single URL")
    scrape_parser.add_argument("url", help="URL to scrape")
    scrape_parser.add_argument("--formats", nargs="+", default=["markdown"],
                               help="Output formats: markdown, html, links, screenshot, summary, images, branding")
    scrape_parser.add_argument("--full", action="store_true", help="Include nav/footer")
    scrape_parser.add_argument("--actions", help="JSON array of page actions (click, write, wait, scroll, screenshot)")
    scrape_parser.add_argument("--country", help="Country code for geo-targeting (e.g., US, GB, DE)")
    scrape_parser.add_argument("--languages", nargs="+", help="Languages for geo-targeting (e.g., en-US es)")
    scrape_parser.add_argument("--max-age", type=int, help="Use cached result if fresher than N seconds")
    scrape_parser.add_argument("--no-cache", action="store_true", help="Don't cache this scrape result")
    scrape_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # Agent command
    agent_parser = subparsers.add_parser("agent", help="Autonomous data extraction")
    agent_parser.add_argument("prompt", help="Natural language description of data to find")
    agent_parser.add_argument("--urls", nargs="+", help="Optional URLs to focus on")
    agent_parser.add_argument("--model", choices=["spark-1-mini", "spark-1-pro"], default="spark-1-mini",
                              help="Agent model: spark-1-mini (default, 60%% cheaper) or spark-1-pro (more capable)")
    agent_parser.add_argument("--max-credits", type=int, help="Maximum credits to spend on this job")
    agent_parser.add_argument("--async", dest="async_mode", action="store_true",
                              help="Start async job, return job ID")
    agent_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # Agent status command
    status_parser = subparsers.add_parser("status", help="Check async agent job status")
    status_parser.add_argument("job_id", help="Job ID to check")
    status_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # Agent cancel command
    agent_cancel_parser = subparsers.add_parser("agent-cancel", help="Cancel a running agent job")
    agent_cancel_parser.add_argument("job_id", help="Job ID to cancel")

    # Crawl command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl entire website")
    crawl_parser.add_argument("url", help="Starting URL")
    crawl_parser.add_argument("-n", "--limit", type=int, default=50, help="Max pages to crawl")
    crawl_parser.add_argument("--depth", type=int, help="Max link depth")
    crawl_parser.add_argument("--include", nargs="+", help="Include paths (regex)")
    crawl_parser.add_argument("--exclude", nargs="+", help="Exclude paths (regex)")
    crawl_parser.add_argument("--async", dest="async_mode", action="store_true", help="Async mode")
    crawl_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # Crawl status command
    crawl_status_parser = subparsers.add_parser("crawl-status", help="Check crawl job status")
    crawl_status_parser.add_argument("job_id", help="Job ID to check")
    crawl_status_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # Crawl cancel command
    crawl_cancel_parser = subparsers.add_parser("crawl-cancel", help="Cancel a crawl job")
    crawl_cancel_parser.add_argument("job_id", help="Job ID to cancel")

    # Crawl errors command
    crawl_errors_parser = subparsers.add_parser("crawl-errors", help="Get errors from a crawl job")
    crawl_errors_parser.add_argument("job_id", help="Job ID to get errors for")
    crawl_errors_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # Active crawls command
    active_crawls_parser = subparsers.add_parser("crawl-active", help="List all active crawl jobs")
    active_crawls_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # Batch scrape command
    batch_parser = subparsers.add_parser("batch-scrape", help="Scrape multiple URLs")
    batch_parser.add_argument("urls", nargs="+", help="URLs to scrape")
    batch_parser.add_argument("--formats", nargs="+", default=["markdown"],
                              help="Output formats: markdown, html, links, screenshot")
    batch_parser.add_argument("--full", action="store_true", help="Include nav/footer")
    batch_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # Batch status command
    batch_status_parser = subparsers.add_parser("batch-status", help="Check batch scrape status")
    batch_status_parser.add_argument("job_id", help="Job ID to check")
    batch_status_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # Batch cancel command
    batch_cancel_parser = subparsers.add_parser("batch-cancel", help="Cancel a batch scrape job")
    batch_cancel_parser.add_argument("job_id", help="Job ID to cancel")

    # Batch errors command
    batch_errors_parser = subparsers.add_parser("batch-errors", help="Get errors from a batch scrape job")
    batch_errors_parser.add_argument("job_id", help="Job ID to get errors for")
    batch_errors_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # Map command
    map_parser = subparsers.add_parser("map", help="Discover all URLs on a website")
    map_parser.add_argument("url", help="Base URL to map")
    map_parser.add_argument("-n", "--limit", type=int, default=5000, help="Max URLs (max: 100000)")
    map_parser.add_argument("--search", help="Search query to order by relevance")
    map_parser.add_argument("--no-subdomains", action="store_true", help="Exclude subdomains")
    map_parser.add_argument("--sitemap", choices=["include", "skip", "only"], default="include",
                           help="Sitemap handling mode")
    map_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # Extract command
    extract_parser = subparsers.add_parser("extract", help="LLM-powered structured extraction")
    extract_parser.add_argument("urls", nargs="+", help="URLs (supports wildcards like 'example.com/*')")
    extract_parser.add_argument("--prompt", "-p", help="What data to extract")
    extract_parser.add_argument("--schema", help="JSON schema for structured output")
    extract_parser.add_argument("--web-search", action="store_true", help="Enable web search")
    extract_parser.add_argument("--sources", action="store_true", help="Show sources")
    extract_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    # Extract status command
    extract_status_parser = subparsers.add_parser("extract-status", help="Check extract job status")
    extract_status_parser.add_argument("job_id", help="Job ID to check")
    extract_status_parser.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "search":
            results = search(
                args.query,
                limit=args.limit,
                categories=args.categories,
                sources=args.sources,
                tbs=args.tbs,
                location=args.location,
                scrape=args.scrape,
                scrape_formats=["markdown"] if args.scrape else None
            )
            if args.json:
                print(json.dumps(results, indent=2, default=str))
            else:
                print(format_search_results(results))

        elif args.command == "scrape":
            # Parse actions if provided
            actions = None
            if args.actions:
                try:
                    actions = json.loads(args.actions)
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON for --actions: {e}", file=sys.stderr)
                    sys.exit(1)

            # Build location dict if country provided
            location = None
            if args.country:
                location = {"country": args.country}
                if args.languages:
                    location["languages"] = args.languages

            result = scrape(
                args.url,
                formats=args.formats,
                only_main_content=not args.full,
                actions=actions,
                location=location,
                max_age=getattr(args, 'max_age', None),
                store_in_cache=not getattr(args, 'no_cache', False)
            )
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                print(format_scrape_result(result))

        elif args.command == "agent":
            result = agent(
                args.prompt,
                urls=args.urls,
                async_mode=args.async_mode,
                model=args.model,
                max_credits=getattr(args, 'max_credits', None)
            )
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                if args.async_mode:
                    print(f"Job ID: {result['job_id']}")
                    print(f"Model: {args.model}")
                    print(result['message'])
                else:
                    print(json.dumps(result.get('data', result), indent=2, default=str))

        elif args.command == "agent-cancel":
            result = cancel_agent(args.job_id)
            print(f"Agent job {args.job_id} cancelled")

        elif args.command == "status":
            result = get_agent_status(args.job_id)
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                print(f"Status: {result['status']}")
                if result['credits_used']:
                    print(f"Credits used: {result['credits_used']}")
                if result['data']:
                    print(f"\nData:\n{json.dumps(result['data'], indent=2, default=str)}")

        elif args.command == "crawl":
            result = crawl(
                args.url,
                limit=args.limit,
                max_depth=args.depth,
                include_paths=args.include,
                exclude_paths=args.exclude,
                async_mode=args.async_mode
            )
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                if args.async_mode:
                    print(f"Job ID: {result['job_id']}")
                    print(result['message'])
                else:
                    pages = result.get('data', result)
                    if isinstance(pages, list):
                        print(f"Crawled {len(pages)} pages")
                        for page in pages[:5]:
                            print(f"\n- {page.get('url', 'Unknown URL')}")
                            print(f"  Title: {page.get('title', 'No title')}")

        elif args.command == "crawl-status":
            result = get_crawl_status(args.job_id)
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                print(f"Status: {result.get('status', 'unknown')}")
                data = result.get('data', [])
                if data:
                    print(f"Pages crawled: {len(data)}")
                    for page in data[:5]:
                        print(f"  - {page.get('url', 'Unknown')}")

        elif args.command == "crawl-cancel":
            result = cancel_crawl(args.job_id)
            print(f"Crawl job {args.job_id} cancelled")

        elif args.command == "crawl-errors":
            result = get_crawl_errors(args.job_id)
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                errors = result.get('errors', result.get('data', []))
                if errors:
                    print(f"Found {len(errors)} error(s):")
                    for err in errors:
                        if isinstance(err, dict):
                            print(f"  - {err.get('url', 'Unknown URL')}: {err.get('error', err.get('message', 'Unknown error'))}")
                        else:
                            print(f"  - {err}")
                else:
                    print("No errors found")

        elif args.command == "crawl-active":
            result = get_active_crawls()
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                crawls = result.get('crawls', result.get('data', []))
                if crawls:
                    print(f"Active crawl jobs: {len(crawls)}")
                    for crawl_job in crawls:
                        if isinstance(crawl_job, dict):
                            print(f"  - ID: {crawl_job.get('id', 'Unknown')}")
                            print(f"    URL: {crawl_job.get('url', 'Unknown')}")
                            print(f"    Status: {crawl_job.get('status', 'Unknown')}")
                        else:
                            print(f"  - {crawl_job}")
                else:
                    print("No active crawl jobs")

        elif args.command == "batch-scrape":
            result = batch_scrape(
                args.urls,
                formats=args.formats,
                only_main_content=not args.full
            )
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                job_id = result.get('id', result.get('job_id'))
                print(f"Batch scrape started")
                print(f"Job ID: {job_id}")
                print(f"Check status: python firecrawl_api.py batch-status {job_id}")

        elif args.command == "batch-status":
            result = get_batch_status(args.job_id)
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                print(f"Status: {result.get('status', 'unknown')}")
                data = result.get('data', [])
                if data:
                    print(f"Pages scraped: {len(data)}")
                    for page in data[:5]:
                        print(f"  - {page.get('url', page.get('sourceURL', 'Unknown'))}")

        elif args.command == "batch-cancel":
            result = cancel_batch(args.job_id)
            print(f"Batch job {args.job_id} cancelled")

        elif args.command == "batch-errors":
            result = get_batch_errors(args.job_id)
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                errors = result.get('errors', result.get('data', []))
                if errors:
                    print(f"Found {len(errors)} error(s):")
                    for err in errors:
                        if isinstance(err, dict):
                            print(f"  - {err.get('url', 'Unknown URL')}: {err.get('error', err.get('message', 'Unknown error'))}")
                        else:
                            print(f"  - {err}")
                else:
                    print("No errors found")

        elif args.command == "map":
            result = map_site(
                args.url,
                search=args.search,
                limit=args.limit,
                include_subdomains=not args.no_subdomains,
                sitemap=args.sitemap
            )
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                links = result.get('links', [])
                print(f"Discovered {len(links)} URLs:")
                for link in links[:20]:
                    if isinstance(link, dict):
                        print(f"  - {link.get('url', 'Unknown')}")
                        if link.get('title'):
                            print(f"    Title: {link['title']}")
                    else:
                        print(f"  - {link}")
                if len(links) > 20:
                    print(f"  ... and {len(links) - 20} more")

        elif args.command == "extract":
            schema = None
            if args.schema:
                try:
                    schema = json.loads(args.schema)
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON schema: {e}", file=sys.stderr)
                    sys.exit(1)
            result = extract(
                args.urls,
                prompt=args.prompt,
                schema=schema,
                enable_web_search=args.web_search,
                show_sources=args.sources
            )
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                job_id = result.get('id', result.get('job_id'))
                print(f"Extract job started")
                print(f"Job ID: {job_id}")
                print(f"Check status: python firecrawl_api.py extract-status {job_id}")

        elif args.command == "extract-status":
            result = get_extract_status(args.job_id)
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                print(f"Status: {result.get('status', 'unknown')}")
                if result.get('data'):
                    print(f"\nExtracted data:")
                    print(json.dumps(result['data'], indent=2, default=str))

    except requests.exceptions.HTTPError as e:
        print(f"API Error: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
