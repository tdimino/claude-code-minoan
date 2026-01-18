#!/usr/bin/env python3
"""
Exa Contents - Extract clean content from URLs.

This script provides comprehensive access to Exa's /contents endpoint for
extracting and processing web page content. Unlike web scrapers, Exa's
contents endpoint uses its pre-indexed data for fast, clean extraction.

Features:
- Extract full text content formatted as markdown
- Generate AI summaries with custom queries
- Get key highlights/excerpts from content
- Crawl subpages for deeper content extraction
- Extract links and images
- Handle multiple URLs in a single request
- Livecrawl for fresh content

Usage:
    exa_contents.py "https://example.com/article"
    exa_contents.py URL1 URL2 URL3 --summary "Key findings"
    exa_contents.py "https://arxiv.org/abs/2307.06435" --highlights --subpages 3
    exa_contents.py URLs --livecrawl --timeout 30000

Requires: EXA_API_KEY environment variable
Install: pip install requests
"""

import os
import sys
import json
import argparse
import requests
from typing import Optional, List, Dict, Any

EXA_API_KEY = os.environ.get("EXA_API_KEY")
BASE_URL = "https://api.exa.ai"


def _headers() -> Dict[str, str]:
    """Get authentication headers."""
    if not EXA_API_KEY:
        raise ValueError("EXA_API_KEY environment variable not set. Get your key at https://dashboard.exa.ai")
    return {
        "Content-Type": "application/json",
        "x-api-key": EXA_API_KEY
    }


def get_contents(
    urls: List[str],
    # Text options
    get_text: bool = True,
    max_characters: Optional[int] = None,
    include_html_tags: bool = False,
    # Summary options
    get_summary: Optional[str] = None,
    summary_schema: Optional[Dict[str, Any]] = None,
    # Highlights options
    get_highlights: bool = False,
    highlights_query: Optional[str] = None,
    num_sentences: int = 3,
    highlights_per_url: int = 3,
    # Subpages
    subpages: int = 0,
    subpage_target: Optional[str] = None,
    # Extras
    get_links: int = 0,
    get_image_links: int = 0,
    # Livecrawl
    livecrawl: Optional[str] = None,
    livecrawl_timeout: Optional[int] = None,
    # Context (RAG)
    get_context: bool = False,
    context_max_chars: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Get clean content from specific URLs using Exa's /contents endpoint.

    Unlike web scraping, this uses Exa's pre-indexed data for fast extraction.
    Great for getting content from URLs you already know.

    Args:
        urls: List of URLs to extract content from
        get_text: Include full text content (default: True)
        max_characters: Limit text length (None = no limit)
        include_html_tags: Include HTML tags in text (default: False)
        get_summary: Generate summary with this query
        summary_schema: JSON schema for structured summaries
        get_highlights: Include key excerpts
        highlights_query: Custom query for highlights
        num_sentences: Sentences per highlight
        highlights_per_url: Max highlights per URL
        subpages: Number of subpages to crawl per URL
        subpage_target: Where to find subpage links
        get_links: Number of links to extract per URL
        get_image_links: Number of images to extract per URL
        livecrawl: Livecrawl mode - "always", "preferred", "fallback", or "never"
        livecrawl_timeout: Timeout in ms for livecrawling
        get_context: Combine all contents into one RAG context string
        context_max_chars: Limit context string length (None = unlimited)

    Returns:
        Dict with extracted content for each URL
    """
    # Build payload
    payload: Dict[str, Any] = {
        "urls": urls
    }

    # Text options
    if get_text:
        text_config: Dict[str, Any] = {}
        if max_characters:
            text_config["maxCharacters"] = max_characters
        if include_html_tags:
            text_config["includeHtmlTags"] = True
        payload["text"] = text_config if text_config else True

    # Summary options
    if get_summary:
        summary_config: Dict[str, Any] = {"query": get_summary}
        if summary_schema:
            summary_config["schema"] = summary_schema
        payload["summary"] = summary_config

    # Highlights options
    if get_highlights:
        highlights_config: Dict[str, Any] = {
            "numSentences": num_sentences,
            "highlightsPerUrl": highlights_per_url
        }
        if highlights_query:
            highlights_config["query"] = highlights_query
        payload["highlights"] = highlights_config

    # Subpages
    if subpages > 0:
        payload["subpages"] = subpages
        if subpage_target:
            payload["subpageTarget"] = subpage_target

    # Extras
    if get_links > 0 or get_image_links > 0:
        extras: Dict[str, int] = {}
        if get_links > 0:
            extras["links"] = get_links
        if get_image_links > 0:
            extras["imageLinks"] = get_image_links
        payload["extras"] = extras

    # Livecrawl options
    if livecrawl:
        payload["livecrawl"] = livecrawl
    if livecrawl_timeout:
        payload["livecrawlTimeout"] = livecrawl_timeout

    # Context for RAG applications
    if get_context:
        if context_max_chars:
            payload["context"] = {"maxCharacters": context_max_chars}
        else:
            payload["context"] = True

    # Make request
    response = requests.post(
        f"{BASE_URL}/contents",
        headers=_headers(),
        json=payload
    )
    response.raise_for_status()
    return response.json()


def format_results(results: Dict[str, Any], max_text_length: int = 2000) -> str:
    """Format content results for readable display."""
    output = []

    # Request info
    if results.get("requestId"):
        output.append(f"Request ID: {results['requestId']}")

    # Check statuses for errors
    statuses = results.get("statuses", [])
    errors = [s for s in statuses if s.get("status") == "error"]
    if errors:
        output.append(f"\nWARNING: {len(errors)} URL(s) had errors:")
        for err in errors:
            error_info = err.get("error", {})
            output.append(f"  - {err.get('id')}: {error_info.get('tag')} (HTTP {error_info.get('httpStatusCode')})")

    # Results
    content_results = results.get("results", [])
    if content_results:
        output.append(f"\n{'='*60}")
        output.append(f"CONTENTS ({len(content_results)} URLs processed):")

        for i, r in enumerate(content_results, 1):
            output.append(f"\n[{i}] {r.get('title', 'No title')}")
            output.append(f"    URL: {r.get('url', 'No URL')}")

            if r.get('author'):
                output.append(f"    Author: {r['author'][:80]}")
            if r.get('publishedDate'):
                output.append(f"    Published: {r['publishedDate'][:10]}")

            # Favicon and image
            if r.get('favicon'):
                output.append(f"    Favicon: {r['favicon']}")
            if r.get('image'):
                output.append(f"    Image: {r['image']}")

            # Summary
            if r.get('summary'):
                output.append(f"\n    SUMMARY:")
                output.append(f"    {r['summary'][:500]}")

            # Highlights
            if r.get('highlights'):
                output.append(f"\n    HIGHLIGHTS:")
                for j, h in enumerate(r['highlights'], 1):
                    score = ""
                    if r.get('highlightScores') and j <= len(r['highlightScores']):
                        score = f" (relevance: {r['highlightScores'][j-1]:.2f})"
                    output.append(f"    {j}. {h[:200]}...{score}")

            # Text
            if r.get('text'):
                text = r['text'][:max_text_length]
                if len(r['text']) > max_text_length:
                    text += "\n    ... [truncated]"
                output.append(f"\n    TEXT ({len(r['text'])} chars):")
                output.append(f"    {text}")

            # Subpages
            if r.get('subpages'):
                output.append(f"\n    SUBPAGES ({len(r['subpages'])} found):")
                for sp in r['subpages'][:5]:
                    output.append(f"      - {sp.get('title', 'No title')[:50]}")
                    output.append(f"        {sp.get('url', '')}")
                    if sp.get('summary'):
                        output.append(f"        Summary: {sp['summary'][:100]}...")

            # Extras
            if r.get('extras'):
                extras = r['extras']
                if extras.get('links'):
                    output.append(f"\n    LINKS ({len(extras['links'])} extracted):")
                    for link in extras['links'][:5]:
                        output.append(f"      - {link}")
                if extras.get('imageLinks'):
                    output.append(f"\n    IMAGES ({len(extras['imageLinks'])} found):")
                    for img in extras['imageLinks'][:3]:
                        output.append(f"      - {img}")

    # Context (RAG)
    if results.get("context"):
        context = results["context"]
        output.append(f"\n{'='*60}")
        output.append(f"CONTEXT ({len(context)} chars):")
        output.append("-" * 40)
        # Show truncated context
        if len(context) > max_text_length:
            output.append(f"{context[:max_text_length]}\n... [truncated, {len(context)} total chars]")
        else:
            output.append(context)

    # Cost
    if results.get("costDollars"):
        cost = results["costDollars"]
        output.append(f"\n{'='*60}")
        output.append(f"COST: ${cost.get('total', 0):.4f}")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Exa Contents - Extract clean content from URLs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://arxiv.org/abs/2307.06435"
  %(prog)s URL1 URL2 URL3 --summary "Key findings"
  %(prog)s "https://docs.python.org" --highlights --subpages 5
  %(prog)s "https://example.com" --livecrawl always --timeout 30000
  %(prog)s "https://news.ycombinator.com" --links 10 --images 5

Livecrawl modes:
  always    - Always fetch fresh content
  preferred - Try to livecrawl, fallback to cache if fails
  fallback  - Use index, fall back to live if not found
  never     - Only use indexed content (default)
        """
    )

    # Required
    parser.add_argument("urls", nargs="+", help="URLs to extract content from")

    # Text options
    parser.add_argument("--no-text", action="store_true", help="Don't include full text")
    parser.add_argument("--max-chars", type=int, help="Limit text length")
    parser.add_argument("--html", action="store_true", help="Include HTML tags in text")

    # Summary options
    parser.add_argument("--summary", help="Generate summary with this query")
    parser.add_argument("--summary-schema", type=str, help="JSON schema for structured summaries")

    # Highlights options
    parser.add_argument("--highlights", action="store_true", help="Include key excerpts")
    parser.add_argument("--highlights-query", help="Custom query for highlights")
    parser.add_argument("--sentences", type=int, default=3, help="Sentences per highlight")
    parser.add_argument("--highlights-per-url", type=int, default=3, help="Max highlights per URL")

    # Subpages
    parser.add_argument("--subpages", type=int, default=0, help="Number of subpages to crawl")
    parser.add_argument("--subpage-target", help="Where to find subpage links")

    # Extras
    parser.add_argument("--links", type=int, default=0, help="Extract N links per URL")
    parser.add_argument("--images", type=int, default=0, help="Extract N images per URL")

    # Livecrawl
    parser.add_argument("--livecrawl", choices=["always", "preferred", "fallback", "never"],
                        help="Livecrawl mode for fresh content")
    parser.add_argument("--timeout", type=int, help="Livecrawl timeout in ms")

    # Context (RAG)
    parser.add_argument("--context", action="store_true",
                        help="Combine all contents into one RAG context string")
    parser.add_argument("--context-chars", type=int,
                        help="Limit context string length (use with --context)")

    # Output
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--text-limit", type=int, default=2000,
                        help="Max text chars to display (default: 2000)")

    args = parser.parse_args()

    # Parse schema if provided
    summary_schema = None
    if args.summary_schema:
        try:
            summary_schema = json.loads(args.summary_schema)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON schema: {e}", file=sys.stderr)
            sys.exit(1)

    try:
        results = get_contents(
            urls=args.urls,
            get_text=not args.no_text,
            max_characters=args.max_chars,
            include_html_tags=args.html,
            get_summary=args.summary,
            summary_schema=summary_schema,
            get_highlights=args.highlights,
            highlights_query=args.highlights_query,
            num_sentences=args.sentences,
            highlights_per_url=args.highlights_per_url,
            subpages=args.subpages,
            subpage_target=args.subpage_target,
            get_links=args.links,
            get_image_links=args.images,
            livecrawl=args.livecrawl,
            livecrawl_timeout=args.timeout,
            get_context=args.context,
            context_max_chars=args.context_chars,
        )

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(format_results(results, max_text_length=args.text_limit))

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
