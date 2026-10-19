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
- Freshness control (maxAgeHours) and historical snapshots (snapshotAsOf)
- Dynamic Highlights (beta) across all URLs in one request

Billing: $1/1k pages per content type (text, highlights, summary each count).

Usage:
    exa_contents.py "https://example.com/article"
    exa_contents.py URL1 URL2 URL3 --summary "Key findings"
    exa_contents.py "https://arxiv.org/abs/2307.06435" --highlights --no-text
    exa_contents.py URL --max-age-hours 0 --timeout 30000

Requires: EXA_API_KEY environment variable
Install: pip install requests
"""

import sys
import json
import argparse
from typing import Optional, List, Dict, Any, Tuple

from _exa_common import (
    LIVECRAWL_CHOICES, VALID_SECTIONS, ExaAPIError, add_list_arg, check_snapshot, context_option, die,
    extras_option, format_cost, format_notices, highlights_option, legacy, post, report_warnings,
    resolve_max_age, text_option,
)


def build_contents_payload(
    urls: List[str],
    # Text options
    get_text: bool = True,
    max_characters: Optional[int] = None,
    include_html_tags: bool = False,
    verbosity: Optional[str] = None,
    include_sections: Optional[List[str]] = None,
    exclude_sections: Optional[List[str]] = None,
    # Summary options
    get_summary: Optional[str] = None,
    summary_schema: Optional[Dict[str, Any]] = None,
    # Highlights options
    get_highlights: bool = False,
    highlights_query: Optional[str] = None,
    highlights_max_chars: Optional[int] = None,
    dynamic_highlights: bool = False,
    # Subpages
    subpages: int = 0,
    subpage_target: Optional[str] = None,
    # Extras
    get_links: int = 0,
    get_image_links: int = 0,
    # Freshness
    livecrawl: Optional[str] = None,
    livecrawl_timeout: Optional[int] = None,
    max_age_hours: Optional[int] = None,
    snapshot_as_of: Optional[str] = None,
    # Context (RAG)
    get_context: bool = False,
    context_max_chars: Optional[int] = None,
) -> Tuple[Dict[str, Any], List[str]]:
    """
    Build the /contents request body. Returns (payload, beta flags).

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
        highlights_max_chars: Fixed highlight budget per page
        dynamic_highlights: Dynamic Highlights beta (shared budget; not with highlights_max_chars)
        subpages: Number of subpages to crawl per URL
        subpage_target: Where to find subpage links
        get_links: Number of links to extract per URL
        get_image_links: Number of images to extract per URL
        livecrawl: (Deprecated) mapped to max_age_hours
        livecrawl_timeout: Timeout in ms for fetching fresh pages
        max_age_hours: Max cached age in hours (0=always fetch fresh, -1=cache only)
        snapshot_as_of: Return page versions as of this date/time
        get_context: (Deprecated) combine all contents into one context string
        context_max_chars: Limit context string length (None = unlimited)
    """
    check_snapshot(snapshot_as_of, max_age_hours, livecrawl, subpages, livecrawl_timeout)
    highlights, betas = highlights_option(get_highlights, highlights_query, highlights_max_chars,
                                          dynamic_highlights)

    payload: Dict[str, Any] = {
        "urls": urls
    }

    # Text options
    if get_text:
        payload["text"] = text_option(max_characters, verbosity, include_sections, exclude_sections,
                                      html=include_html_tags)

    # Summary options
    if get_summary:
        summary_config: Dict[str, Any] = {"query": get_summary}
        if summary_schema:
            summary_config["schema"] = summary_schema
        payload["summary"] = summary_config

    # Highlights options
    if highlights is not None:
        payload["highlights"] = highlights

    # Subpages
    if subpages > 0:
        payload["subpages"] = subpages
        if subpage_target:
            payload["subpageTarget"] = subpage_target

    # Extras
    extras = extras_option(get_links, get_image_links)
    if extras:
        payload["extras"] = extras

    # Freshness options
    max_age = resolve_max_age(max_age_hours, livecrawl)
    if max_age is not None:
        payload["maxAgeHours"] = max_age
    if livecrawl_timeout:
        payload["livecrawlTimeout"] = livecrawl_timeout
    if snapshot_as_of:
        payload["snapshotAsOf"] = snapshot_as_of

    # Context (deprecated)
    context = context_option(get_context, context_max_chars)
    if context is not None:
        payload["context"] = context

    return payload, betas


def get_contents(urls: List[str], **kwargs) -> Dict[str, Any]:
    """Get clean content from specific URLs. Keyword arguments match build_contents_payload."""
    payload, betas = build_contents_payload(urls, **kwargs)
    return post("/contents", payload, betas=betas)


def failed_urls(results: Dict[str, Any]) -> List[str]:
    """One line per URL whose status is error (statuses[].error may be null)."""
    lines = []
    for st in results.get("statuses") or []:
        if st.get("status") == "error":
            info = st.get("error") or {}
            lines.append(f"{st.get('id')}: {info.get('tag', 'error')} (HTTP {info.get('httpStatusCode', '?')})")
    return lines


def format_results(results: Dict[str, Any], max_text_length: int = 2000, show_cost: bool = False) -> str:
    """Format content results for readable display."""
    output = []

    # Request info
    if results.get("requestId"):
        output.append(f"Request ID: {results['requestId']}")

    output.extend(format_notices(results))

    # Per-URL failures
    errors = failed_urls(results)
    if errors:
        output.append(f"\nWARNING: {len(errors)} URL(s) had errors:")
        output.extend(f"  - {line}" for line in errors)

    # Results
    content_results = results.get("results", [])
    if content_results:
        output.append(f"\n{'='*60}")
        output.append(f"CONTENTS ({len(content_results)} URLs processed):")

        for i, r in enumerate(content_results, 1):
            output.append(f"\n[{i}] {r.get('title') or 'No title'}")
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
                output.append("\n    SUMMARY:")
                output.append(f"    {r['summary'][:500]}")

            # Highlights
            if r.get('highlights'):
                output.append("\n    HIGHLIGHTS:")
                for j, h in enumerate(r['highlights'], 1):
                    score = ""
                    scores = r.get('highlightScores') or []
                    if scores and j <= len(scores):
                        score = f" (relevance: {scores[j-1]:.2f})"
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
                    output.append(f"      - {(sp.get('title') or 'No title')[:50]}")
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

    if show_cost:
        output.extend(format_cost(results.get("costDollars")))

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Exa Contents - Extract clean content from URLs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://arxiv.org/abs/2307.06435"
  %(prog)s URL1 URL2 URL3 --summary "Key findings"
  %(prog)s "https://docs.python.org" --highlights --no-text --subpages 5
  %(prog)s "https://example.com" --max-age-hours 0 --timeout 30000
  %(prog)s URL1 URL2 URL3 --dynamic --highlights-query "pricing" --no-text
  %(prog)s "https://news.ycombinator.com" --links 10 --images 5

Freshness (--max-age-hours): 0 = always fetch fresh, N = refetch if cache older
than N hours, -1 = cache only. Omitted = cache when available, else fetch.
--livecrawl still works and maps: always→0, preferred→1, never→-1, fallback→omitted.
        """
    )

    # Required
    parser.add_argument("urls", nargs="+", help="URLs to extract content from")

    # Text options
    parser.add_argument("--no-text", action="store_true", help="Don't include full text")
    parser.add_argument("--max-chars", type=int, help="Limit text length")
    parser.add_argument("--html", action="store_true", help="Include HTML tags in text")

    # Text verbosity and section filtering (requires --max-age-hours 0)
    parser.add_argument("--verbosity", choices=["compact", "standard", "full"],
                        help="Content verbosity level (requires --max-age-hours 0)")
    add_list_arg(parser, "--include-sections", choices=VALID_SECTIONS,
                 help="Only include these page sections (requires --max-age-hours 0)")
    add_list_arg(parser, "--exclude-sections", choices=VALID_SECTIONS,
                 help="Exclude these page sections (requires --max-age-hours 0)")

    # Summary options
    parser.add_argument("--summary", help="Generate summary with this query")
    parser.add_argument("--summary-schema", type=str, help="JSON schema for structured summaries")

    # Highlights options
    parser.add_argument("--highlights", action="store_true", help="Include query-relevant excerpts")
    parser.add_argument("--highlights-query", help="Custom query for highlights (implies --highlights)")
    parser.add_argument("--highlights-max-chars", type=int,
                        help="Fixed highlight budget per page (implies --highlights)")
    parser.add_argument("--dynamic", action="store_true",
                        help="Dynamic Highlights (beta): one shared budget across all URLs")
    parser.add_argument("--sentences", type=int, help="(Ignored) Exa deprecated numSentences")
    parser.add_argument("--highlights-per-url", type=int, help="(Ignored) Exa deprecated highlightsPerUrl")

    # Subpages
    parser.add_argument("--subpages", type=int, default=0, help="Number of subpages to crawl")
    parser.add_argument("--subpage-target", help="Where to find subpage links")

    # Extras
    parser.add_argument("--links", type=int, default=0, help="Extract N links per URL")
    parser.add_argument("--images", type=int, default=0, help="Extract N images per URL")

    # Freshness
    parser.add_argument("--max-age-hours", type=int,
                        help="Max cached age in hours (0=always fetch fresh, -1=cache only)")
    parser.add_argument("--livecrawl", choices=LIVECRAWL_CHOICES,
                        help="(Deprecated) mapped to --max-age-hours")
    parser.add_argument("--timeout", type=int, help="Fresh-fetch timeout in ms")
    parser.add_argument("--snapshot-as-of", help="Page versions as of a date/time (paid tiers)")

    # Context (RAG)
    parser.add_argument("--context", action="store_true",
                        help="(Deprecated) combine all contents into one context string")
    parser.add_argument("--context-chars", type=int,
                        help="(Deprecated) limit context string length (use with --context)")

    # Output
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--cost", action="store_true", help="Show cost breakdown")
    parser.add_argument("--text-limit", type=int, default=2000,
                        help="Max text chars to display (default: 2000)")

    args = parser.parse_args()

    # Parse schema if provided
    summary_schema = None
    if args.summary_schema:
        try:
            summary_schema = json.loads(args.summary_schema)
        except json.JSONDecodeError as e:
            parser.error(f"Invalid JSON in --summary-schema: {e}")
        if not args.summary:
            parser.error("--summary-schema requires --summary")

    if args.sentences is not None:
        legacy("--sentences", "ignored; use --highlights-max-chars for a fixed budget.")
    if args.highlights_per_url is not None:
        legacy("--highlights-per-url", "ignored; use --highlights-max-chars for a fixed budget.")

    try:
        payload, betas = build_contents_payload(
            urls=args.urls,
            get_text=not args.no_text,
            max_characters=args.max_chars,
            include_html_tags=args.html,
            verbosity=args.verbosity,
            include_sections=args.include_sections,
            exclude_sections=args.exclude_sections,
            get_summary=args.summary,
            summary_schema=summary_schema,
            get_highlights=args.highlights,
            highlights_query=args.highlights_query,
            highlights_max_chars=args.highlights_max_chars,
            dynamic_highlights=args.dynamic,
            subpages=args.subpages,
            subpage_target=args.subpage_target,
            get_links=args.links,
            get_image_links=args.images,
            livecrawl=args.livecrawl,
            livecrawl_timeout=args.timeout,
            max_age_hours=args.max_age_hours,
            snapshot_as_of=args.snapshot_as_of,
            get_context=args.context,
            context_max_chars=args.context_chars,
        )
    except ValueError as e:
        parser.error(str(e))

    try:
        results = post("/contents", payload, betas=betas)
    except (ExaAPIError, ValueError) as e:
        die(e)

    report_warnings(results)
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_results(results, max_text_length=args.text_limit, show_cost=args.cost))

    errors = failed_urls(results)
    for line in errors:
        print(f"Failed: {line}", file=sys.stderr)
    if errors and not results.get("results"):
        sys.exit(1)


if __name__ == "__main__":
    main()
