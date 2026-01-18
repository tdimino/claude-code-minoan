#!/usr/bin/env python3
"""
Exa Find Similar - Discover related pages and content.

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
    exa_similar.py "https://arxiv.org/abs/2307.06435" -n 20 --category "research paper"
    exa_similar.py "https://github.com/langchain-ai/langchain" --domains github.com
    exa_similar.py URL --summary "Key differentiators" --highlights

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

# Valid category options (same as search)
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


def find_similar(
    url: str,
    # Results
    num_results: int = 10,
    # Category
    category: Optional[str] = None,
    # Domain filtering
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    # Date filtering
    start_crawl_date: Optional[str] = None,
    end_crawl_date: Optional[str] = None,
    start_published_date: Optional[str] = None,
    end_published_date: Optional[str] = None,
    # Content options
    get_text: bool = True,
    max_characters: Optional[int] = None,
    get_summary: Optional[str] = None,
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
) -> Dict[str, Any]:
    """
    Find pages similar to a reference URL using Exa's /findSimilar endpoint.

    Args:
        url: Reference URL to find similar pages for
        num_results: Number of similar results (max 100)
        category: Filter by category (see VALID_CATEGORIES)
        include_domains: Only include results from these domains
        exclude_domains: Exclude results from these domains
        start_crawl_date: Results crawled after this date (YYYY-MM-DD)
        end_crawl_date: Results crawled before this date (YYYY-MM-DD)
        start_published_date: Published after this date (YYYY-MM-DD)
        end_published_date: Published before this date (YYYY-MM-DD)
        get_text: Include full text content
        max_characters: Limit text length
        get_summary: Generate summary with this query
        get_highlights: Include key excerpts
        highlights_query: Custom query for highlights
        num_sentences: Sentences per highlight
        highlights_per_url: Max highlights per result
        subpages: Number of subpages to crawl per result
        subpage_target: Where to find subpage links
        get_links: Number of links to extract per result
        get_image_links: Number of images to extract per result
        exclude_source_domain: Exclude the source URL's domain from results
        include_text: Results must contain ALL of these strings
        exclude_text: Results must NOT contain ANY of these strings
        moderation: Enable content moderation filter
        get_context: Combine all contents into one RAG context string
        context_max_chars: Limit context string length (None = unlimited)

    Returns:
        Dict with similar pages
    """
    # Validate category
    if category and category not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category '{category}'. Must be one of: {VALID_CATEGORIES}")

    # Build payload
    payload: Dict[str, Any] = {
        "url": url,
        "numResults": min(num_results, 100),
    }

    # Category
    if category:
        payload["category"] = category

    # Domain filtering
    domains_to_exclude = list(exclude_domains) if exclude_domains else []
    if exclude_source_domain:
        # Extract domain from URL
        from urllib.parse import urlparse
        source_domain = urlparse(url).netloc
        if source_domain and source_domain not in domains_to_exclude:
            domains_to_exclude.append(source_domain)

    if include_domains:
        payload["includeDomains"] = include_domains
    if domains_to_exclude:
        payload["excludeDomains"] = domains_to_exclude

    # Text filtering
    if include_text:
        payload["includeText"] = include_text
    if exclude_text:
        payload["excludeText"] = exclude_text

    # Moderation
    if moderation:
        payload["moderation"] = True

    # Date filtering
    if start_crawl_date:
        payload["startCrawlDate"] = f"{start_crawl_date}T00:00:00.000Z"
    if end_crawl_date:
        payload["endCrawlDate"] = f"{end_crawl_date}T23:59:59.999Z"
    if start_published_date:
        payload["startPublishedDate"] = f"{start_published_date}T00:00:00.000Z"
    if end_published_date:
        payload["endPublishedDate"] = f"{end_published_date}T23:59:59.999Z"

    # Build contents object
    contents: Dict[str, Any] = {}

    if get_text:
        if max_characters:
            contents["text"] = {"maxCharacters": max_characters}
        else:
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

    # Context for RAG applications
    if get_context:
        if context_max_chars:
            contents["context"] = {"maxCharacters": context_max_chars}
        else:
            contents["context"] = True

    if contents:
        payload["contents"] = contents

    # Make request
    response = requests.post(
        f"{BASE_URL}/findSimilar",
        headers=_headers(),
        json=payload
    )
    response.raise_for_status()
    return response.json()


def format_results(results: Dict[str, Any], max_text_length: int = 500) -> str:
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
            output.append(f"\n[{i}] {r.get('title', 'No title')}")
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
                output.append(f"    Highlights:")
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

    # Cost
    if results.get("costDollars"):
        cost = results["costDollars"]
        output.append(f"\n{'='*60}")
        output.append(f"COST: ${cost.get('total', 0):.4f}")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Exa Find Similar - Discover related pages and content",
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

Categories: company, research paper, news, pdf, github, tweet, personal site, people, financial report
        """
    )

    # Required
    parser.add_argument("url", help="Reference URL to find similar pages for")

    # Results
    parser.add_argument("-n", "--num", type=int, default=10, help="Number of results (max 100)")
    parser.add_argument("--category", "-c", choices=VALID_CATEGORIES, help="Filter by category")

    # Domain filtering
    parser.add_argument("--domains", nargs="+", help="Only include these domains")
    parser.add_argument("--exclude-domains", nargs="+", help="Exclude these domains")
    parser.add_argument("--exclude-source", action="store_true",
                        help="Exclude source URL's domain from results")

    # Date filtering
    parser.add_argument("--after", help="Published after date (YYYY-MM-DD)")
    parser.add_argument("--before", help="Published before date (YYYY-MM-DD)")
    parser.add_argument("--crawled-after", help="Crawled after date (YYYY-MM-DD)")
    parser.add_argument("--crawled-before", help="Crawled before date (YYYY-MM-DD)")

    # Content options
    parser.add_argument("--no-text", action="store_true", help="Don't include full text")
    parser.add_argument("--max-chars", type=int, help="Limit text length")
    parser.add_argument("--summary", help="Generate summary with this query")
    parser.add_argument("--highlights", action="store_true", help="Include key excerpts")
    parser.add_argument("--highlights-query", help="Custom query for highlights")

    # Subpages
    parser.add_argument("--subpages", type=int, default=0, help="Number of subpages to crawl")
    parser.add_argument("--subpage-target", help="Where to find subpage links")

    # Extras
    parser.add_argument("--links", type=int, default=0, help="Extract N links per result")
    parser.add_argument("--images", type=int, default=0, help="Extract N images per result")

    # Text filtering
    parser.add_argument("--must-include", nargs="+",
                        help="Results must contain ALL of these strings")
    parser.add_argument("--must-exclude", nargs="+",
                        help="Results must NOT contain ANY of these strings")

    # Moderation
    parser.add_argument("--safe", action="store_true",
                        help="Enable content moderation filter")

    # Context (RAG)
    parser.add_argument("--context", action="store_true",
                        help="Combine all contents into one RAG context string")
    parser.add_argument("--context-chars", type=int,
                        help="Limit context string length (use with --context)")

    # Output
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--text-limit", type=int, default=500,
                        help="Max text chars to display (default: 500)")

    args = parser.parse_args()

    try:
        results = find_similar(
            url=args.url,
            num_results=args.num,
            category=args.category,
            include_domains=args.domains,
            exclude_domains=args.exclude_domains,
            start_published_date=args.after,
            end_published_date=args.before,
            start_crawl_date=args.crawled_after,
            end_crawl_date=args.crawled_before,
            get_text=not args.no_text,
            max_characters=args.max_chars,
            get_summary=args.summary,
            get_highlights=args.highlights,
            highlights_query=args.highlights_query,
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
