#!/usr/bin/env python3
"""
Exa Find Similar - Discover related pages and content.

DEPRECATED ENDPOINT: Exa marks /findSimilar deprecated (spec 2.0.0). It still works;
prefer exa_search.py with a query that describes the source page.

This script provides access to Exa's /findSimilar endpoint for finding
pages semantically similar to a reference URL. Great for discovering
related articles, similar research, competing products, or related content.

Use Cases:
- Find articles similar to one you liked
- Discover competing products/companies
- Find related research papers
- Expand reading lists with similar content
- Competitive analysis
- Content discovery and recommendations

Usage:
    exa_similar.py "https://example.com/article"
    exa_similar.py "https://arxiv.org/abs/2307.06435" -n 20 --category publication
    exa_similar.py "https://github.com/langchain-ai/langchain" --domains github.com
    exa_similar.py URL --summary "Key differentiators" --highlights

Requires: EXA_API_KEY environment variable
Install: pip install requests
"""

import sys
import json
import argparse
from typing import Optional, List, Dict, Any

from _exa_common import (
    CATEGORY_CHOICES, LIVECRAWL_CHOICES, VALID_SECTIONS, ExaAPIError, add_list_arg, context_option,
    date_bound, die, extras_option, format_cost, highlights_option, legacy, note, post, resolve_category,
    resolve_max_age, text_option,
)

DEPRECATION = ("Note: /findSimilar is deprecated; prefer exa_search.py with a query "
               "describing the source page.")


def build_similar_payload(
    url: str,
    # Results
    num_results: int = 10,
    # Category
    category: Optional[str] = None,
    # Domain filtering
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    # Date filtering
    start_published_date: Optional[str] = None,
    end_published_date: Optional[str] = None,
    # Content options
    get_text: bool = True,
    max_characters: Optional[int] = None,
    get_summary: Optional[str] = None,
    get_highlights: bool = False,
    highlights_query: Optional[str] = None,
    # Subpages
    subpages: int = 0,
    subpage_target: Optional[str] = None,
    # Extras
    get_links: int = 0,
    get_image_links: int = 0,
    # Exclude source
    exclude_source_domain: bool = False,
    # Text filtering
    include_text: Optional[List[str]] = None,
    exclude_text: Optional[List[str]] = None,
    # Moderation
    moderation: bool = False,
    # Context (RAG)
    get_context: bool = False,
    context_max_chars: Optional[int] = None,
    # Content freshness
    max_age_hours: Optional[int] = None,
    livecrawl: Optional[str] = None,
    # Text verbosity and section filtering
    verbosity: Optional[str] = None,
    include_sections: Optional[List[str]] = None,
    exclude_sections: Optional[List[str]] = None,
    # Highlights
    highlights_max_chars: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Build the /findSimilar request body.

    Args:
        url: Reference URL to find similar pages for
        num_results: Number of similar results (max 100)
        category: Filter by category (see CATEGORIES)
        include_domains: Only include results from these domains
        exclude_domains: Exclude results from these domains
        start_published_date: Published after this date (YYYY-MM-DD)
        end_published_date: Published before this date (YYYY-MM-DD)
        get_text: Include full text content
        max_characters: Limit text length
        get_summary: Generate summary with this query
        get_highlights: Include key excerpts
        highlights_query: Custom query for highlights
        subpages: Number of subpages to crawl per result
        subpage_target: Where to find subpage links
        get_links: Number of links to extract per result
        get_image_links: Number of images to extract per result
        exclude_source_domain: Exclude the source URL's domain from results
        include_text: (Deprecated) text results should contain; matched approximately
        exclude_text: (Deprecated) text results should not contain; matched approximately
        moderation: Ignored; /findSimilar has no moderation field
        get_context: (Deprecated) combine all contents into one context string
        context_max_chars: Limit context string length (None = unlimited)
    """
    category = resolve_category(category)
    if num_results < 1:
        raise ValueError("-n/--num must be at least 1")
    highlights, _ = highlights_option(get_highlights, highlights_query, highlights_max_chars)

    # Build payload
    payload: Dict[str, Any] = {
        "url": url,
        "numResults": min(num_results, 100),
    }

    # Category
    if category:
        payload["category"] = category

    # Domain filtering
    if include_domains:
        payload["includeDomains"] = include_domains
    if exclude_domains:
        payload["excludeDomains"] = exclude_domains
    if exclude_source_domain:
        payload["excludeSourceDomain"] = True

    # Text filtering (deprecated)
    if include_text:
        legacy("--must-include", "Exa matches it approximately at word level.")
        payload["includeText"] = include_text
    if exclude_text:
        legacy("--must-exclude", "Exa matches it approximately at word level.")
        payload["excludeText"] = exclude_text

    if moderation:
        note("--safe ignored; /findSimilar has no moderation option (use exa_search.py --safe).")

    # Date filtering
    if start_published_date:
        payload["startPublishedDate"] = date_bound(start_published_date)
    if end_published_date:
        payload["endPublishedDate"] = date_bound(end_published_date, end=True)

    # Build contents object
    contents: Dict[str, Any] = {}

    if get_text:
        contents["text"] = text_option(max_characters, verbosity, include_sections, exclude_sections)
    if get_summary:
        contents["summary"] = {"query": get_summary}
    if highlights is not None:
        contents["highlights"] = highlights

    if subpages > 0:
        legacy("--subpages", "deprecated here; prefer exa_contents.py URL --subpages N.")
        contents["subpages"] = subpages
        if subpage_target:
            contents["subpageTarget"] = subpage_target

    extras = extras_option(get_links, get_image_links)
    if extras:
        contents["extras"] = extras
    context = context_option(get_context, context_max_chars)
    if context is not None:
        contents["context"] = context

    # Content freshness
    max_age = resolve_max_age(max_age_hours, livecrawl)
    if max_age is not None:
        contents["maxAgeHours"] = max_age

    if contents:
        payload["contents"] = contents
    return payload


def find_similar(url: str, **kwargs) -> Dict[str, Any]:
    """Find pages similar to a URL. Keyword arguments match build_similar_payload."""
    return post("/findSimilar", build_similar_payload(url, **kwargs))


def format_results(results: Dict[str, Any], max_text_length: int = 500, show_cost: bool = False) -> str:
    """Format similar results for readable display."""
    output = []

    # Request info
    if results.get("requestId"):
        output.append(f"Request ID: {results['requestId']}")

    # Results
    similar_results = results.get("results", [])
    if similar_results:
        output.append(f"\n{'='*60}")
        output.append(f"SIMILAR PAGES ({len(similar_results)} found):")

        for i, r in enumerate(similar_results, 1):
            output.append(f"\n[{i}] {r.get('title') or 'No title'}")
            output.append(f"    URL: {r.get('url', 'No URL')}")

            # Similarity score if available
            if r.get('score'):
                output.append(f"    Similarity: {r['score']:.2f}")

            if r.get('author'):
                output.append(f"    Author: {r['author'][:80]}")
            if r.get('publishedDate'):
                output.append(f"    Published: {r['publishedDate'][:10]}")

            # Summary
            if r.get('summary'):
                output.append(f"    Summary: {r['summary'][:300]}...")

            # Highlights
            if r.get('highlights'):
                output.append("    Highlights:")
                for h in r['highlights'][:3]:
                    output.append(f"      - {h[:150]}...")

            # Text
            if r.get('text'):
                text = r['text'][:max_text_length]
                if len(r['text']) > max_text_length:
                    text += "..."
                output.append(f"    Text: {text}")

            # Subpages
            if r.get('subpages'):
                output.append(f"    Subpages: {len(r['subpages'])} found")

            # Extras
            if r.get('extras'):
                extras = r['extras']
                if extras.get('links'):
                    output.append(f"    Links: {len(extras['links'])} extracted")
                if extras.get('imageLinks'):
                    output.append(f"    Images: {len(extras['imageLinks'])} found")

    if show_cost:
        output.extend(format_cost(results.get("costDollars")))

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Exa Find Similar (deprecated endpoint) - Discover related pages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "https://arxiv.org/abs/2307.06435"
  %(prog)s "https://github.com/langchain-ai/langchain" -n 20
  %(prog)s "https://stripe.com" --category company --exclude-source
  %(prog)s "https://blog.example.com/post" --domains medium.com substack.com
  %(prog)s URL --summary "How is this different?" --highlights

Use Cases:
  - Find similar research papers to expand literature review
  - Discover competing companies/products
  - Find related articles on the same topic
  - Build recommendation systems
  - Competitive analysis and market research

Categories: company, publication, news, personal site, financial report, people
        """
    )

    # Required
    parser.add_argument("url", help="Reference URL to find similar pages for")

    # Results
    parser.add_argument("-n", "--num", type=int, default=10, help="Number of results (max 100)")
    parser.add_argument("--category", "-c", choices=CATEGORY_CHOICES, help="Filter by category")

    # Domain filtering
    add_list_arg(parser, "--domains", split_commas=True, help="Only include these domains (repeatable)")
    add_list_arg(parser, "--exclude-domains", split_commas=True, help="Exclude these domains (repeatable)")
    parser.add_argument("--exclude-source", action="store_true",
                        help="Exclude source URL's domain from results")

    # Date filtering
    parser.add_argument("--after", help="Published after date (YYYY-MM-DD)")
    parser.add_argument("--before", help="Published before date (YYYY-MM-DD)")

    # Content options
    parser.add_argument("--no-text", action="store_true", help="Don't include full text")
    parser.add_argument("--max-chars", type=int, help="Limit text length")
    parser.add_argument("--summary", help="Generate summary with this query")
    parser.add_argument("--highlights", action="store_true", help="Include key excerpts")
    parser.add_argument("--highlights-query", help="Custom query for highlights")
    parser.add_argument("--highlights-max-chars", type=int,
                        help="Fixed highlight budget per page")

    # Content freshness
    parser.add_argument("--max-age-hours", type=int,
                        help="Max cached age in hours (0=always fetch fresh, -1=cache only)")
    parser.add_argument("--livecrawl", choices=LIVECRAWL_CHOICES,
                        help="(Deprecated) mapped to --max-age-hours")

    # Text verbosity and section filtering (requires --max-age-hours 0)
    parser.add_argument("--verbosity", choices=["compact", "standard", "full"],
                        help="Content verbosity level (requires --max-age-hours 0)")
    add_list_arg(parser, "--include-sections", choices=VALID_SECTIONS,
                 help="Only include these page sections (requires --max-age-hours 0)")
    add_list_arg(parser, "--exclude-sections", choices=VALID_SECTIONS,
                 help="Exclude these page sections (requires --max-age-hours 0)")

    # Subpages
    parser.add_argument("--subpages", type=int, default=0, help="Number of subpages to crawl")
    parser.add_argument("--subpage-target", help="Where to find subpage links")

    # Extras
    parser.add_argument("--links", type=int, default=0, help="Extract N links per result")
    parser.add_argument("--images", type=int, default=0, help="Extract N images per result")

    # Text filtering
    add_list_arg(parser, "--must-include", help="(Deprecated) text results should contain")
    add_list_arg(parser, "--must-exclude", help="(Deprecated) text results should not contain")

    # Moderation
    parser.add_argument("--safe", action="store_true",
                        help="Enable content moderation filter")

    # Context (RAG)
    parser.add_argument("--context", action="store_true",
                        help="(Deprecated) combine all contents into one context string")
    parser.add_argument("--context-chars", type=int,
                        help="Limit context string length (use with --context)")

    # Output
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--cost", action="store_true", help="Show cost breakdown")
    parser.add_argument("--text-limit", type=int, default=500,
                        help="Max text chars to display (default: 500)")

    args = parser.parse_args()
    print(DEPRECATION, file=sys.stderr)

    try:
        payload = build_similar_payload(
            url=args.url,
            num_results=args.num,
            category=args.category,
            include_domains=args.domains,
            exclude_domains=args.exclude_domains,
            start_published_date=args.after,
            end_published_date=args.before,
            get_text=not args.no_text,
            max_characters=args.max_chars,
            get_summary=args.summary,
            get_highlights=args.highlights,
            highlights_query=args.highlights_query,
            highlights_max_chars=args.highlights_max_chars,
            max_age_hours=args.max_age_hours,
            livecrawl=args.livecrawl,
            verbosity=args.verbosity,
            include_sections=args.include_sections,
            exclude_sections=args.exclude_sections,
            subpages=args.subpages,
            subpage_target=args.subpage_target,
            get_links=args.links,
            get_image_links=args.images,
            exclude_source_domain=args.exclude_source,
            include_text=args.must_include,
            exclude_text=args.must_exclude,
            moderation=args.safe,
            get_context=args.context,
            context_max_chars=args.context_chars,
        )
    except ValueError as e:
        parser.error(str(e))

    try:
        results = post("/findSimilar", payload)
    except (ExaAPIError, ValueError) as e:
        die(e)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_results(results, max_text_length=args.text_limit, show_cost=args.cost))


if __name__ == "__main__":
    main()
