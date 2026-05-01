#!/usr/bin/env python3
"""
Tavily Search & Extract - AI-optimized web search with grounded answers.

Provides access to Tavily's /search and /extract endpoints for web search,
news retrieval, and content extraction with optional AI-generated answers.

Features:
- Search depths: basic (fast) and advanced (comprehensive)
- Topic modes: general, news, finance
- AI-generated answer synthesis with source citations
- Raw full-page content retrieval
- Domain inclusion/exclusion filtering
- Recency filtering (last N days)
- Content extraction from arbitrary URLs
- Pipe-friendly --answer-only mode
- Markdown and JSON output modes

Usage:
    tavily_search.py "Iran oil sanctions" -n 10
    tavily_search.py "semiconductor supply chain" --advanced --answer
    tavily_search.py "crude oil futures" --finance --days 3 --answer-only
    tavily_search.py "Ukraine ceasefire" --news --answer --markdown
    tavily_search.py extract https://example.com/article https://foo.bar/page
    tavily_search.py "drone warfare" --domains militarytracker.com --raw-content

Requires: TAVILY_API_KEY environment variable
Install: pip install requests
"""

import os
import sys
import json
import argparse
import requests
from typing import Optional, List, Dict, Any

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
BASE_URL = "https://api.tavily.com"


def _headers() -> Dict[str, str]:
    """Get authentication headers."""
    if not TAVILY_API_KEY:
        raise ValueError(
            "TAVILY_API_KEY environment variable not set. "
            "Get your key at https://app.tavily.com"
        )
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TAVILY_API_KEY}",
    }


def search(
    query: str,
    search_depth: str = "basic",
    topic: str = "general",
    max_results: int = 5,
    include_answer: bool = False,
    include_raw_content: bool = False,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    days: Optional[int] = None,
    include_images: bool = False,
    chunks_per_source: int = 3,
) -> Dict[str, Any]:
    """
    Search the web via Tavily's /search endpoint.

    Args:
        query: Natural language search query
        search_depth: "basic" (fast, ~1s) or "advanced" (comprehensive, ~3-5s)
        topic: "general", "news", or "finance"
        max_results: Number of results to return (1–20)
        include_answer: Whether to include AI-synthesized answer
        include_raw_content: Whether to include full page content per result
        include_domains: Restrict results to these domains
        exclude_domains: Exclude results from these domains
        days: Only return results published within the last N days
        include_images: Whether to include image results
        chunks_per_source: Number of content chunks per source (1–10)

    Returns:
        Dict with keys: query, answer (optional), results, images (optional)
    """
    valid_depths = ("basic", "advanced")
    if search_depth not in valid_depths:
        raise ValueError(f"Invalid search_depth '{search_depth}'. Must be one of: {valid_depths}")

    valid_topics = ("general", "news", "finance")
    if topic not in valid_topics:
        raise ValueError(f"Invalid topic '{topic}'. Must be one of: {valid_topics}")

    payload: Dict[str, Any] = {
        "query": query,
        "search_depth": search_depth,
        "topic": topic,
        "max_results": max(1, min(max_results, 20)),
        "include_answer": include_answer,
        "include_raw_content": include_raw_content,
        "include_images": include_images,
        "chunks_per_source": max(1, min(chunks_per_source, 10)),
    }

    if include_domains:
        payload["include_domains"] = include_domains
    if exclude_domains:
        payload["exclude_domains"] = exclude_domains
    if days is not None:
        payload["days"] = days

    response = requests.post(
        f"{BASE_URL}/search",
        headers=_headers(),
        json=payload,
    )
    response.raise_for_status()
    return response.json()


def extract(
    urls: List[str],
    include_images: bool = False,
) -> Dict[str, Any]:
    """
    Extract full content from one or more URLs via Tavily's /extract endpoint.

    Args:
        urls: List of URLs to extract content from
        include_images: Whether to include images found on each page

    Returns:
        Dict with keys: results (list of {url, raw_content}), failed_results
    """
    if not urls:
        raise ValueError("At least one URL is required for extraction")

    payload: Dict[str, Any] = {
        "urls": urls,
        "include_images": include_images,
    }

    response = requests.post(
        f"{BASE_URL}/extract",
        headers=_headers(),
        json=payload,
    )
    response.raise_for_status()
    return response.json()


def format_results(results: Dict[str, Any], no_text: bool = False) -> str:
    """Format search results for readable display."""
    output = []

    query = results.get("query", "")
    if query:
        output.append(f"Query: {query}")

    search_results = results.get("results", [])
    output.append(f"\n{'='*60}")
    output.append(f"RESULTS ({len(search_results)} found):")

    for i, r in enumerate(search_results, 1):
        output.append(f"\n[{i}] {r.get('title', 'No title')}")
        output.append(f"    URL: {r.get('url', 'No URL')}")

        score = r.get("score")
        if score is not None:
            output.append(f"    Score: {score:.3f}")

        pub_date = r.get("published_date")
        if pub_date:
            output.append(f"    Published: {str(pub_date)[:10]}")

        if not no_text:
            content = r.get("content") or r.get("raw_content", "")
            if content:
                snippet = content[:500]
                if len(content) > 500:
                    snippet += "..."
                output.append(f"    Content: {snippet}")

    images = results.get("images", [])
    if images:
        output.append(f"\n{'='*60}")
        output.append(f"IMAGES ({len(images)} found):")
        for img in images[:5]:
            if isinstance(img, dict):
                output.append(f"  - {img.get('url', img)}")
            else:
                output.append(f"  - {img}")

    answer = results.get("answer")
    if answer:
        output.append(f"\n{'='*60}")
        output.append("AI ANSWER:")
        output.append("-" * 40)
        output.append(answer)
        output.append("")
        output.append("Sources:")
        for i, r in enumerate(search_results[:5], 1):
            title = r.get("title", "No title")[:70]
            url = r.get("url", "")
            output.append(f"  [{i}] {title}")
            output.append(f"      {url}")

    return "\n".join(output)


def format_answer(results: Dict[str, Any]) -> str:
    """Format just the AI answer with source citations."""
    answer = results.get("answer", "")
    if not answer:
        return "(No AI answer returned. Pass --answer to request one.)"

    lines = [answer, "", "Sources:"]
    for i, r in enumerate(results.get("results", [])[:5], 1):
        title = r.get("title", "No title")[:70]
        url = r.get("url", "")
        lines.append(f"  [{i}] {title}")
        lines.append(f"      {url}")

    return "\n".join(lines)


def format_extract(results: Dict[str, Any]) -> str:
    """Format extraction results for readable display."""
    output = []

    extracted = results.get("results", [])
    output.append(f"EXTRACTED ({len(extracted)} URL(s)):")

    for r in extracted:
        output.append(f"\n{'='*60}")
        output.append(f"URL: {r.get('url', 'unknown')}")
        content = r.get("raw_content", "")
        if content:
            snippet = content[:1000]
            if len(content) > 1000:
                snippet += f"\n... [{len(content) - 1000} chars remaining]"
            output.append(snippet)
        else:
            output.append("(no content returned)")

    failed = results.get("failed_results", [])
    if failed:
        output.append(f"\n{'='*60}")
        output.append(f"FAILED ({len(failed)}):")
        for f in failed:
            if isinstance(f, dict):
                output.append(f"  - {f.get('url', f)}: {f.get('error', 'unknown error')}")
            else:
                output.append(f"  - {f}")

    return "\n".join(output)


def format_markdown(results: Dict[str, Any]) -> str:
    """Format search results as Markdown."""
    lines = []

    query = results.get("query", "")
    if query:
        lines.append(f"# Search: {query}\n")

    answer = results.get("answer")
    if answer:
        lines.append("## Answer\n")
        lines.append(answer)
        lines.append("")

    search_results = results.get("results", [])
    if search_results:
        lines.append(f"## Results ({len(search_results)})\n")
        for i, r in enumerate(search_results, 1):
            title = r.get("title", "No title")
            url = r.get("url", "")
            score = r.get("score")
            pub_date = r.get("published_date")

            lines.append(f"### {i}. [{title}]({url})\n")
            meta = []
            if score is not None:
                meta.append(f"Score: `{score:.3f}`")
            if pub_date:
                meta.append(f"Published: {str(pub_date)[:10]}")
            if meta:
                lines.append("  ".join(meta) + "\n")

            content = r.get("content") or r.get("raw_content", "")
            if content:
                snippet = content[:400]
                if len(content) > 400:
                    snippet += "..."
                lines.append(f"{snippet}\n")

    images = results.get("images", [])
    if images:
        lines.append(f"## Images ({len(images)})\n")
        for img in images[:5]:
            url = img.get("url", img) if isinstance(img, dict) else img
            lines.append(f"- {url}")
        lines.append("")

    return "\n".join(lines)


def _build_extract_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tavily_search.py extract",
        description="Extract full content from URLs via Tavily",
    )
    parser.add_argument("urls", nargs="+", help="URLs to extract content from")
    parser.add_argument("--images", action="store_true", help="Include images in extraction")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    return parser


def _build_search_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tavily Search - AI-optimized web search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Iran oil sanctions" -n 10
  %(prog)s "semiconductor supply chain" --advanced --answer
  %(prog)s "crude oil futures" --finance --days 3 --answer-only
  %(prog)s "Ukraine ceasefire" --news --answer --markdown
  %(prog)s "drone warfare OSINT" --domains militarytracker.com bellingcat.com
  %(prog)s extract https://example.com/article https://foo.bar/page

Topics: general (default), news, finance
        """,
    )

    parser.add_argument("query", help="Search query")
    parser.add_argument("-n", "--num", type=int, default=5, help="Number of results (default 5, max 20)")

    depth_group = parser.add_mutually_exclusive_group()
    depth_group.add_argument(
        "--advanced",
        action="store_true",
        help="Deep search mode (search_depth=advanced, ~3-5s)",
    )

    topic_group = parser.add_mutually_exclusive_group()
    topic_group.add_argument("--news", action="store_true", help="Search news topic")
    topic_group.add_argument("--finance", action="store_true", help="Search finance topic")

    parser.add_argument("--answer", action="store_true", help="Include AI-generated answer")
    parser.add_argument("--raw-content", action="store_true", help="Include full page content per result")
    parser.add_argument("--images", action="store_true", help="Include image results")
    parser.add_argument("--chunks", type=int, default=3, help="Chunks per source (default 3, max 10)")

    parser.add_argument("--domains", nargs="+", metavar="D", help="Only include these domains")
    parser.add_argument("--exclude-domains", nargs="+", metavar="D", help="Exclude these domains")
    parser.add_argument("--days", type=int, help="Results from the last N days only")

    parser.add_argument("--no-text", action="store_true", help="Titles, URLs, and scores only")
    parser.add_argument("--json", action="store_true", help="Raw JSON output")
    parser.add_argument("--markdown", action="store_true", help="Markdown-formatted output")
    parser.add_argument("--answer-only", action="store_true", help="Print just the AI answer (pipe-friendly)")

    return parser


def main():
    is_extract = len(sys.argv) > 1 and sys.argv[1] == "extract"

    try:
        if is_extract:
            parser = _build_extract_parser()
            args = parser.parse_args(sys.argv[2:])
            results = extract(
                urls=args.urls,
                include_images=args.images,
            )
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print(format_extract(results))
            return

        parser = _build_search_parser()
        args = parser.parse_args()

        search_depth = "advanced" if args.advanced else "basic"
        topic = "news" if args.news else "finance" if args.finance else "general"

        include_answer = args.answer or args.answer_only

        results = search(
            query=args.query,
            search_depth=search_depth,
            topic=topic,
            max_results=args.num,
            include_answer=include_answer,
            include_raw_content=args.raw_content,
            include_domains=args.domains,
            exclude_domains=args.exclude_domains,
            days=args.days,
            include_images=args.images,
            chunks_per_source=args.chunks,
        )

        if args.json:
            print(json.dumps(results, indent=2))
        elif args.answer_only:
            print(format_answer(results))
        elif args.markdown:
            print(format_markdown(results))
        else:
            print(format_results(results, no_text=args.no_text))

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
