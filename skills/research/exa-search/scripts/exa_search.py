#!/usr/bin/env python3
"""
Exa Neural Search - Advanced web search with AI-powered embeddings.

This script provides comprehensive access to Exa's /search endpoint with all
available parameters for neural, fast, auto, and deep search modes.

Features:
- 5 search types: auto, neural, fast, deep, instant
- 9 category filters: company, research paper, news, pdf, github, tweet, personal site, people, financial report
- Domain inclusion/exclusion filtering
- Date filtering (crawl date and published date)
- Text inclusion/exclusion filtering
- Content retrieval options: text, summary, highlights, context
- Subpage crawling
- Content moderation
- Geolocation targeting

Usage:
    exa_search.py "AI agent frameworks" -n 10
    exa_search.py "machine learning papers" --category "research paper" --deep
    exa_search.py "Python web scraping" --domains github.com realpython.com
    exa_search.py "startup funding" --category company --after 2024-01-01
    exa_search.py "climate change news" --category news --fast --context

Requires: EXA_API_KEY environment variable
Install: pip install requests
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any

EXA_API_KEY = os.environ.get("EXA_API_KEY")
BASE_URL = "https://api.exa.ai"

# Valid category options
VALID_CATEGORIES = [
    "company", "research paper", "news", "pdf", "github",
    "tweet", "personal site", "people", "financial report"
]

def _headers() -> Dict[str, str]:
    """Get authentication headers."""
    if not EXA_API_KEY:
        raise ValueError("EXA_API_KEY environment variable not set. Get your key at https://dashboard.exa.ai")
    return {
        "Content-Type": "application/json",
        "x-api-key": EXA_API_KEY
    }

def search(
    query: str,
    # Search type
    search_type: str = "auto",
    additional_queries: Optional[List[str]] = None,
    # Category
    category: Optional[str] = None,
    # Results
    num_results: int = 10,
    # Domain filtering
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    # Date filtering
    start_crawl_date: Optional[str] = None,
    end_crawl_date: Optional[str] = None,
    start_published_date: Optional[str] = None,
    end_published_date: Optional[str] = None,
    # Text filtering
    include_text: Optional[List[str]] = None,
    exclude_text: Optional[List[str]] = None,
    # Content options
    get_text: bool = True,
    get_summary: Optional[str] = None,
    get_highlights: bool = False,
    highlights_query: Optional[str] = None,
    num_sentences: int = 3,
    highlights_per_url: int = 3,
    get_context: bool = False,
    context_max_chars: Optional[int] = None,
    # Subpages
    subpages: int = 0,
    subpage_target: Optional[str] = None,
    # Extras
    get_links: int = 0,
    get_image_links: int = 0,
    # Location and moderation
    user_location: Optional[str] = None,
    moderation: bool = False,
) -> Dict[str, Any]:
    """
    Perform a neural search using Exa's /search endpoint.

    Args:
        query: Natural language search query
        search_type: Search method - "auto" (default), "neural", "fast", "deep", "instant"
        additional_queries: Extra queries for deep search mode only
        category: Filter by category (see VALID_CATEGORIES)
        num_results: Number of results (max 100)
        include_domains: Only search these domains
        exclude_domains: Exclude these domains
        start_crawl_date: Results crawled after this date (YYYY-MM-DD)
        end_crawl_date: Results crawled before this date (YYYY-MM-DD)
        start_published_date: Published after this date (YYYY-MM-DD)
        end_published_date: Published before this date (YYYY-MM-DD)
        include_text: Text that must be present in results (1 string, up to 5 words)
        exclude_text: Text that must NOT be present (1 string, up to 5 words)
        get_text: Include full text content (default: True)
        get_summary: Generate summary with this query
        get_highlights: Include key excerpts (default: False)
        highlights_query: Custom query for highlights
        num_sentences: Sentences per highlight
        highlights_per_url: Max highlights per result
        get_context: Combine all results into one context string for RAG
        context_max_chars: Max characters for context string
        subpages: Number of subpages to crawl per result
        subpage_target: Where to find subpage links ("sources", "references", etc.)
        get_links: Number of links to extract per result
        get_image_links: Number of images to extract per result
        user_location: Two-letter country code (e.g., "US")
        moderation: Filter unsafe content

    Returns:
        Dict with search results
    """
    # Validate search type
    valid_types = ["auto", "neural", "fast", "deep", "instant"]
    if search_type not in valid_types:
        raise ValueError(f"Invalid search type '{search_type}'. Must be one of: {valid_types}")

    # Validate category
    if category and category not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category '{category}'. Must be one of: {VALID_CATEGORIES}")

    # Build payload
    payload: Dict[str, Any] = {
        "query": query,
        "type": search_type,
        "numResults": min(num_results, 100),
    }

    # Deep search additional queries
    if additional_queries and search_type == "deep":
        payload["additionalQueries"] = additional_queries

    # Category
    if category:
        payload["category"] = category

    # Domain filtering
    if include_domains:
        payload["includeDomains"] = include_domains
    if exclude_domains:
        payload["excludeDomains"] = exclude_domains

    # Date filtering
    if start_crawl_date:
        payload["startCrawlDate"] = f"{start_crawl_date}T00:00:00.000Z"
    if end_crawl_date:
        payload["endCrawlDate"] = f"{end_crawl_date}T23:59:59.999Z"
    if start_published_date:
        payload["startPublishedDate"] = f"{start_published_date}T00:00:00.000Z"
    if end_published_date:
        payload["endPublishedDate"] = f"{end_published_date}T23:59:59.999Z"

    # Text filtering
    if include_text:
        payload["includeText"] = include_text
    if exclude_text:
        payload["excludeText"] = exclude_text

    # Location and moderation
    if user_location:
        payload["userLocation"] = user_location
    if moderation:
        payload["moderation"] = True

    # Build contents object
    contents: Dict[str, Any] = {}

    if get_text:
        contents["text"] = True

    if get_summary:
        contents["summary"] = {"query": get_summary}

    if get_highlights:
        highlights_config: Dict[str, Any] = {
            "numSentences": num_sentences,
            "highlightsPerUrl": highlights_per_url
        }
        if highlights_query:
            highlights_config["query"] = highlights_query
        contents["highlights"] = highlights_config

    if get_context:
        if context_max_chars:
            contents["context"] = {"maxCharacters": context_max_chars}
        else:
            contents["context"] = True

    if subpages > 0:
        contents["subpages"] = subpages
        if subpage_target:
            contents["subpageTarget"] = subpage_target

    if get_links > 0 or get_image_links > 0:
        extras: Dict[str, int] = {}
        if get_links > 0:
            extras["links"] = get_links
        if get_image_links > 0:
            extras["imageLinks"] = get_image_links
        contents["extras"] = extras

    if contents:
        payload["contents"] = contents

    # Make request
    response = requests.post(
        f"{BASE_URL}/search",
        headers=_headers(),
        json=payload
    )
    response.raise_for_status()
    return response.json()


def format_results(results: Dict[str, Any], max_text_length: int = 500, show_cost: bool = False) -> str:
    """Format search results for readable display."""
    output = []

    # Request info
    if results.get("requestId"):
        output.append(f"Request ID: {results['requestId']}")
    if results.get("searchType"):
        output.append(f"Search Type: {results['searchType']}")

    # Context string (for RAG)
    if results.get("context"):
        output.append(f"\n{'='*60}")
        output.append("CONTEXT STRING (for RAG):")
        output.append("-" * 40)
        ctx = results["context"][:2000]
        if len(results["context"]) > 2000:
            ctx += "\n... [truncated]"
        output.append(ctx)

    # Results
    search_results = results.get("results", [])
    if search_results:
        output.append(f"\n{'='*60}")
        output.append(f"RESULTS ({len(search_results)} found):")

        for i, r in enumerate(search_results, 1):
            output.append(f"\n[{i}] {r.get('title', 'No title')}")
            output.append(f"    URL: {r.get('url', 'No URL')}")

            if r.get('author'):
                output.append(f"    Author: {r['author'][:80]}")
            if r.get('publishedDate'):
                output.append(f"    Published: {r['publishedDate'][:10]}")

            # Summary
            if r.get('summary'):
                output.append(f"    Summary: {r['summary'][:300]}...")

            # Highlights
            if r.get('highlights'):
                output.append(f"    Highlights:")
                for h in r['highlights'][:3]:
                    output.append(f"      - {h[:200]}...")

            # Text
            if r.get('text'):
                text = r['text'][:max_text_length]
                if len(r['text']) > max_text_length:
                    text += "..."
                output.append(f"    Text: {text}")

            # Subpages
            if r.get('subpages'):
                output.append(f"    Subpages: {len(r['subpages'])} found")
                for sp in r['subpages'][:3]:
                    output.append(f"      - {sp.get('title', 'No title')[:60]}")
                    output.append(f"        {sp.get('url', '')}")

            # Extras
            if r.get('extras'):
                extras = r['extras']
                if extras.get('links'):
                    output.append(f"    Links: {len(extras['links'])} extracted")
                if extras.get('imageLinks'):
                    output.append(f"    Images: {len(extras['imageLinks'])} found")

    # Cost breakdown
    if show_cost and results.get("costDollars"):
        cost = results["costDollars"]
        output.append(f"\n{'='*60}")
        output.append(f"COST: ${cost.get('total', 0):.4f}")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Exa Neural Search - AI-powered web search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "AI agent frameworks"
  %(prog)s "machine learning papers" --category "research paper"
  %(prog)s "Python libraries" --domains github.com pypi.org
  %(prog)s "startup news" --category company --after 2024-06-01 --fast
  %(prog)s "climate research" --deep --context
  %(prog)s "CEO profiles" --category people --summary "background and achievements"

Categories: company, research paper, news, pdf, github, tweet, personal site, people, financial report
        """
    )

    # Required
    parser.add_argument("query", help="Search query")

    # Search type
    type_group = parser.add_mutually_exclusive_group()
    type_group.add_argument("--neural", action="store_true", help="Use neural embeddings search")
    type_group.add_argument("--fast", action="store_true", help="Use fast search (~500ms)")
    type_group.add_argument("--instant", action="store_true", help="Use instant search (sub-150ms, real-time)")
    type_group.add_argument("--deep", action="store_true", help="Use deep search (comprehensive)")
    parser.add_argument("--additional-queries", nargs="+", help="Extra queries for deep search")

    # Category and results
    parser.add_argument("--category", "-c", choices=VALID_CATEGORIES, help="Filter by category")
    parser.add_argument("-n", "--num", type=int, default=10, help="Number of results (max 100)")

    # Domain filtering
    parser.add_argument("--domains", nargs="+", help="Only include these domains")
    parser.add_argument("--exclude-domains", nargs="+", help="Exclude these domains")

    # Date filtering
    parser.add_argument("--after", help="Published after date (YYYY-MM-DD)")
    parser.add_argument("--before", help="Published before date (YYYY-MM-DD)")
    parser.add_argument("--crawled-after", help="Crawled after date (YYYY-MM-DD)")
    parser.add_argument("--crawled-before", help="Crawled before date (YYYY-MM-DD)")

    # Text filtering
    parser.add_argument("--must-include", nargs="+", help="Text that must be present")
    parser.add_argument("--must-exclude", nargs="+", help="Text that must NOT be present")

    # Content options
    parser.add_argument("--no-text", action="store_true", help="Don't include full text")
    parser.add_argument("--summary", help="Generate summary with this query")
    parser.add_argument("--highlights", action="store_true", help="Include key excerpts")
    parser.add_argument("--highlights-query", help="Custom query for highlights")
    parser.add_argument("--context", action="store_true", help="Combine results into RAG context string")
    parser.add_argument("--context-chars", type=int, help="Max characters for context")

    # Subpages
    parser.add_argument("--subpages", type=int, default=0, help="Number of subpages to crawl")
    parser.add_argument("--subpage-target", help="Where to find subpage links")

    # Extras
    parser.add_argument("--links", type=int, default=0, help="Extract N links per result")
    parser.add_argument("--images", type=int, default=0, help="Extract N images per result")

    # Location and moderation
    parser.add_argument("--location", help="Two-letter country code (e.g., US)")
    parser.add_argument("--safe", action="store_true", help="Enable content moderation")

    # Output
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--cost", action="store_true", help="Show cost breakdown")

    args = parser.parse_args()

    # Determine search type
    search_type = "auto"
    if args.neural:
        search_type = "neural"
    elif args.fast:
        search_type = "fast"
    elif args.instant:
        search_type = "instant"
    elif args.deep:
        search_type = "deep"

    try:
        results = search(
            query=args.query,
            search_type=search_type,
            additional_queries=args.additional_queries,
            category=args.category,
            num_results=args.num,
            include_domains=args.domains,
            exclude_domains=args.exclude_domains,
            start_published_date=args.after,
            end_published_date=args.before,
            start_crawl_date=args.crawled_after,
            end_crawl_date=args.crawled_before,
            include_text=args.must_include,
            exclude_text=args.must_exclude,
            get_text=not args.no_text,
            get_summary=args.summary,
            get_highlights=args.highlights,
            highlights_query=args.highlights_query,
            get_context=args.context,
            context_max_chars=args.context_chars,
            subpages=args.subpages,
            subpage_target=args.subpage_target,
            get_links=args.links,
            get_image_links=args.images,
            user_location=args.location,
            moderation=args.safe,
        )

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(format_results(results, show_cost=args.cost))

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
