#!/usr/bin/env python3
"""
Brave Search - Privacy-focused web search with news, summarization, and custom reranking.

This script provides access to Brave's Search API including web search, dedicated
news search, and the LLM Context API for AI-powered summarization alongside results.

Features:
- Web search with full result metadata and extra snippets
- Dedicated news search endpoint with freshness filtering
- LLM Context API: AI-generated summary + supporting results in one call
- Goggles support for custom result reranking
- Freshness filtering: past day/week/month/year or custom date ranges
- Result type filtering: web, news, images, videos
- Country and language targeting
- Safe search control
- Pagination via offset
- Markdown output mode for LLM consumption

Usage:
    brave_search.py "Iran oil production 2025"
    brave_search.py "US carrier group deployment" --news --freshness pd
    brave_search.py "conflict escalation timeline" --summarize -n 5
    brave_search.py "Hezbollah drone strike" --freshness pw --extra-snippets
    brave_search.py "defense contractor earnings" --filter web,news --markdown

Requires: BRAVE_API_KEY environment variable
Install: pip install requests
"""

import os
import sys
import json
import argparse
import requests
from typing import Optional, Dict, Any

BRAVE_API_KEY = os.environ.get("BRAVE_API_KEY")
BASE_URL = "https://api.search.brave.com/res/v1"


def _headers() -> Dict[str, str]:
    """Get authentication headers for Brave Search API."""
    if not BRAVE_API_KEY:
        raise ValueError(
            "BRAVE_API_KEY environment variable not set. "
            "Get your key at https://brave.com/search/api/"
        )
    return {
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
        "X-Subscription-Token": BRAVE_API_KEY,
    }


def web_search(
    query: str,
    count: int = 10,
    offset: int = 0,
    freshness: Optional[str] = None,
    country: Optional[str] = None,
    search_lang: Optional[str] = None,
    goggles_id: Optional[str] = None,
    result_filter: Optional[str] = None,
    safesearch: str = "moderate",
    extra_snippets: bool = False,
    text_decorations: bool = False,
    spellcheck: bool = True,
) -> Dict[str, Any]:
    """
    Perform a web search using Brave's /web/search endpoint.

    Args:
        query: Search query string
        count: Number of results to return (max 20)
        offset: Pagination offset
        freshness: Recency filter — pd (past day), pw (past week), pm (past month),
                   py (past year), or YYYY-MM-DDtoYYYY-MM-DD custom range
        country: Two-letter country code for localized results (e.g. "US", "GB")
        search_lang: Language code for search (e.g. "en", "fr")
        goggles_id: Goggles ID for custom result reranking
        result_filter: Comma-separated types to include — web, news, images, videos
        safesearch: Content filter — off, moderate, strict
        extra_snippets: Include additional snippets for richer context (up to 5 extra)
        text_decorations: Include bold/italic HTML decorations in snippets
        spellcheck: Enable query spellcheck

    Returns:
        Dict with web results, optional news/image/video results, and query metadata
    """
    params: Dict[str, Any] = {
        "q": query,
        "count": min(count, 20),
        "safesearch": safesearch,
        "text_decorations": str(text_decorations).lower(),
        "spellcheck": str(spellcheck).lower(),
    }

    if offset:
        params["offset"] = offset
    if freshness:
        params["freshness"] = freshness
    if country:
        params["country"] = country
    if search_lang:
        params["search_lang"] = search_lang
    if goggles_id:
        params["goggles_id"] = goggles_id
    if result_filter:
        params["result_filter"] = result_filter
    if extra_snippets:
        params["extra_snippets"] = "true"

    response = requests.get(
        f"{BASE_URL}/web/search",
        headers=_headers(),
        params=params,
    )
    response.raise_for_status()
    return response.json()


def news_search(
    query: str,
    count: int = 10,
    freshness: Optional[str] = None,
    country: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search news articles using Brave's dedicated /news/search endpoint.

    Args:
        query: Search query string
        count: Number of results to return (max 20)
        freshness: Recency filter — pd, pw, pm, py, or YYYY-MM-DDtoYYYY-MM-DD
        country: Two-letter country code (e.g. "US")

    Returns:
        Dict with news results and query metadata
    """
    params: Dict[str, Any] = {
        "q": query,
        "count": min(count, 20),
    }

    if freshness:
        params["freshness"] = freshness
    if country:
        params["country"] = country

    response = requests.get(
        f"{BASE_URL}/news/search",
        headers=_headers(),
        params=params,
    )
    response.raise_for_status()
    return response.json()


def summarize_search(
    query: str,
    count: int = 5,
) -> Dict[str, Any]:
    """
    LLM Context API — returns web search results plus an AI-generated summary.

    Uses Brave's summarizer feature (summary=true + extra_snippets=true) to produce
    a synthesized answer alongside supporting results for LLM consumption.

    Args:
        query: Search query string
        count: Number of supporting results to return (max 20)

    Returns:
        Dict with web results and a 'summarizer' key containing the AI-generated summary
    """
    params: Dict[str, Any] = {
        "q": query,
        "count": min(count, 20),
        "summary": "true",
        "extra_snippets": "true",
    }

    response = requests.get(
        f"{BASE_URL}/web/search",
        headers=_headers(),
        params=params,
    )
    response.raise_for_status()
    return response.json()


def _extract_summary(results: Dict[str, Any]) -> str:
    """Extract AI summary text from Brave summarizer response."""
    summarizer = results.get("summarizer")
    if not summarizer:
        return ""
    summary_key = summarizer.get("key", "")
    summary_data = results.get(summary_key, {})
    if summary_data:
        return summary_data.get("text") or summary_data.get("answer", "")
    if isinstance(summarizer, dict) and summarizer.get("text"):
        return summarizer["text"]
    return ""


def format_results(
    results: Dict[str, Any],
    show_news: bool = False,
    no_text: bool = False,
) -> str:
    """
    Format Brave search results for human-readable display.

    Args:
        results: Raw API response dict
        show_news: Render news results section (for web searches with news in result_filter)
        no_text: Show titles and URLs only, no descriptions or snippets

    Returns:
        Formatted multi-line string
    """
    output = []

    # Query info
    query_info = results.get("query", {})
    if query_info.get("original"):
        output.append(f"Query: {query_info['original']}")
    if query_info.get("altered"):
        output.append(f"Spellcheck: {query_info['altered']}")

    # AI summary (LLM Context API)
    summary_text = _extract_summary(results)
    if summary_text:
        output.append(f"\n{'='*60}")
        output.append("AI SUMMARY:")
        output.append("-" * 40)
        output.append(summary_text)

    # Web results
    web = results.get("web", {})
    web_results = web.get("results", [])
    if web_results:
        output.append(f"\n{'='*60}")
        output.append(f"WEB RESULTS ({len(web_results)} found):")

        for i, r in enumerate(web_results, 1):
            output.append(f"\n[{i}] {r.get('title', 'No title')}")
            output.append(f"    URL: {r.get('url', 'No URL')}")

            if no_text:
                continue

            if r.get("description"):
                output.append(f"    {r['description']}")

            if r.get("page_age"):
                output.append(f"    Age: {r['page_age'][:10]}")

            extra = r.get("extra_snippets", [])
            if extra:
                output.append("    Snippets:")
                for snippet in extra[:3]:
                    output.append(f"      - {snippet[:200]}")

    # News results (dedicated news search or result_filter=news)
    news = results.get("news", {})
    news_results = news.get("results", [])
    if news_results and show_news:
        output.append(f"\n{'='*60}")
        output.append(f"NEWS RESULTS ({len(news_results)} found):")

        for i, r in enumerate(news_results, 1):
            output.append(f"\n[{i}] {r.get('title', 'No title')}")
            output.append(f"    URL: {r.get('url', 'No URL')}")

            if no_text:
                continue

            if r.get("description"):
                output.append(f"    {r['description']}")
            if r.get("age"):
                output.append(f"    Published: {r['age']}")
            if r.get("meta_url", {}).get("hostname"):
                output.append(f"    Source: {r['meta_url']['hostname']}")

    # Pure news endpoint response (has top-level results, not nested under web)
    top_results = results.get("results", [])
    if top_results and not web_results:
        output.append(f"\n{'='*60}")
        output.append(f"NEWS RESULTS ({len(top_results)} found):")

        for i, r in enumerate(top_results, 1):
            output.append(f"\n[{i}] {r.get('title', 'No title')}")
            output.append(f"    URL: {r.get('url', 'No URL')}")

            if no_text:
                continue

            if r.get("description"):
                output.append(f"    {r['description']}")
            if r.get("age"):
                output.append(f"    Published: {r['age']}")
            if r.get("meta_url", {}).get("hostname"):
                output.append(f"    Source: {r['meta_url']['hostname']}")

    return "\n".join(output)


def format_markdown(results: Dict[str, Any], no_text: bool = False) -> str:
    """
    Format results as Markdown for LLM consumption or documentation.

    Args:
        results: Raw API response dict
        no_text: Show titles and URLs only

    Returns:
        Markdown-formatted string
    """
    output = []

    query_info = results.get("query", {})
    if query_info.get("original"):
        output.append(f"# Search: {query_info['original']}\n")

    # AI summary
    summary_text = _extract_summary(results)
    if summary_text:
        output.append("## AI Summary\n")
        output.append(summary_text + "\n")

    # Web results
    web = results.get("web", {})
    web_results = web.get("results", [])

    # Fall back to top-level results (news endpoint)
    all_results = web_results or results.get("results", [])

    if all_results:
        output.append("## Results\n")
        for i, r in enumerate(all_results, 1):
            title = r.get("title", "No title")
            url = r.get("url", "")
            output.append(f"### {i}. [{title}]({url})\n")

            if no_text:
                continue

            if r.get("description"):
                output.append(r["description"] + "\n")

            extra = r.get("extra_snippets", []) or []
            if extra:
                for snippet in extra[:2]:
                    output.append(f"> {snippet}\n")

            age = r.get("page_age") or r.get("age", "")
            if age:
                output.append(f"*{age[:10]}*\n")

    return "\n".join(output)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Brave Search — privacy-focused web and news search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Iran oil exports 2025"
  %(prog)s "carrier group Red Sea" --news --freshness pd
  %(prog)s "conflict escalation" --summarize -n 5
  %(prog)s "defense spending NATO" --freshness pw --extra-snippets
  %(prog)s "Hezbollah drone strike Lebanon" --country US --lang en
  %(prog)s "missile defense intercept" --filter web,news --markdown
  %(prog)s "submarine deployment Pacific" --safe strict --offset 20

Freshness values: pd (past day), pw (past week), pm (past month), py (past year)
                  or YYYY-MM-DDtoYYYY-MM-DD for a custom range
        """,
    )

    # Positional
    parser.add_argument("query", help="Search query")

    # Result count and pagination
    parser.add_argument(
        "-n", "--num",
        type=int,
        default=10,
        help="Number of results (default: 10, max: 20)",
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Pagination offset",
    )

    # Search mode
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--news",
        action="store_true",
        help="Dedicated news search mode",
    )
    mode_group.add_argument(
        "--summarize",
        action="store_true",
        help="LLM Context API — returns results + AI-generated summary",
    )

    # Filtering
    parser.add_argument(
        "--freshness",
        help="Recency filter: pd/pw/pm/py or YYYY-MM-DDtoYYYY-MM-DD",
    )
    parser.add_argument(
        "--country",
        help="Two-letter country code for localized results (e.g. US, GB)",
    )
    parser.add_argument(
        "--lang",
        dest="search_lang",
        help="Search language code (e.g. en, fr, ar)",
    )
    parser.add_argument(
        "--goggles",
        dest="goggles_id",
        help="Goggles ID for custom result reranking",
    )
    parser.add_argument(
        "--filter",
        dest="result_filter",
        help="Comma-separated result types: web,news,images,videos",
    )
    parser.add_argument(
        "--safe",
        dest="safesearch",
        choices=["off", "moderate", "strict"],
        default="moderate",
        help="Safe search level (default: moderate)",
    )

    # Content options
    parser.add_argument(
        "--extra-snippets",
        action="store_true",
        help="Include extra snippets per result for richer context",
    )
    parser.add_argument(
        "--no-text",
        action="store_true",
        help="Show titles and URLs only, no descriptions or snippets",
    )

    # Output format
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON",
    )
    output_group.add_argument(
        "--markdown",
        action="store_true",
        help="Markdown-formatted output for LLM consumption",
    )

    args = parser.parse_args()

    try:
        if args.summarize:
            results = summarize_search(
                query=args.query,
                count=args.num,
            )
        elif args.news:
            results = news_search(
                query=args.query,
                count=args.num,
                freshness=args.freshness,
                country=args.country,
            )
        else:
            results = web_search(
                query=args.query,
                count=args.num,
                offset=args.offset,
                freshness=args.freshness,
                country=args.country,
                search_lang=args.search_lang,
                goggles_id=args.goggles_id,
                result_filter=args.result_filter,
                safesearch=args.safesearch,
                extra_snippets=args.extra_snippets,
            )

        if args.json:
            print(json.dumps(results, indent=2))
        elif args.markdown:
            print(format_markdown(results, no_text=args.no_text))
        else:
            show_news = bool(args.result_filter and "news" in args.result_filter)
            print(format_results(results, show_news=show_news, no_text=args.no_text))

    except requests.exceptions.HTTPError as e:
        print(f"API Error: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
