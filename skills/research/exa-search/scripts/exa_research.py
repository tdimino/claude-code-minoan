#!/usr/bin/env python3
"""
Exa Research - AI-powered deep research with citations.

This script provides access to Exa's /answer endpoint for generating
comprehensive answers from web research with automatic source citations.

Features:
- AI-synthesized answers from multiple sources
- Automatic citation generation
- Source text extraction
- Domain filtering for trusted sources
- Date filtering for recency
- Support for complex research questions
- Streaming responses for real-time output

Use Cases:
- Quick research on any topic
- Fact-checking with citations
- Literature synthesis
- Market research summaries
- Technical documentation queries
- Competitive analysis

Usage:
    exa_research.py "What are the main differences between React and Vue?"
    exa_research.py "Latest developments in AI agents" --sources
    exa_research.py "SpaceX valuation history" --after 2024-01-01
    exa_research.py "Python async best practices" --domains docs.python.org realpython.com

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


def research(
    query: str,
    # Search parameters
    num_results: int = 5,
    # Domain filtering
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    # Date filtering
    start_published_date: Optional[str] = None,
    end_published_date: Optional[str] = None,
    # Content options
    get_text: bool = True,
    get_highlights: bool = False,
    # Model
    model: Optional[str] = None,
    # Streaming
    stream: bool = False,
) -> Dict[str, Any]:
    """
    Perform deep research using Exa's /answer endpoint.

    This endpoint searches the web, synthesizes information from multiple
    sources, and generates a comprehensive answer with citations.

    Args:
        query: Research question or topic
        num_results: Number of sources to use (default: 5)
        include_domains: Only search these domains
        exclude_domains: Exclude these domains
        start_published_date: Only sources published after this date (YYYY-MM-DD)
        end_published_date: Only sources published before this date (YYYY-MM-DD)
        get_text: Include source text in response
        get_highlights: Include relevant excerpts from sources
        model: Optional model override for answer generation
        stream: Enable SSE streaming for real-time output

    Returns:
        Dict with answer text, sources, and optional source content
        (If stream=True, returns a generator yielding SSE events)
    """
    # Build payload
    payload: Dict[str, Any] = {
        "query": query,
    }

    # Search options
    if num_results != 5:
        payload["numResults"] = min(num_results, 20)  # Answer endpoint has lower limits

    # Domain filtering
    if include_domains:
        payload["includeDomains"] = include_domains
    if exclude_domains:
        payload["excludeDomains"] = exclude_domains

    # Date filtering
    if start_published_date:
        payload["startPublishedDate"] = f"{start_published_date}T00:00:00.000Z"
    if end_published_date:
        payload["endPublishedDate"] = f"{end_published_date}T23:59:59.999Z"

    # Content options
    if get_text:
        payload["text"] = True
    if get_highlights:
        payload["highlights"] = True

    # Model override
    if model:
        payload["model"] = model

    # Streaming
    if stream:
        payload["stream"] = True

    # Make request
    response = requests.post(
        f"{BASE_URL}/answer",
        headers=_headers(),
        json=payload,
        stream=stream
    )
    response.raise_for_status()

    if stream:
        return response  # Return response object for streaming
    return response.json()


def process_stream(response) -> Dict[str, Any]:
    """
    Process SSE streaming response and print answer in real-time.

    Args:
        response: requests Response object with streaming enabled

    Returns:
        Dict with complete answer and sources after stream ends
    """
    result: Dict[str, Any] = {"answer": "", "results": []}

    for line in response.iter_lines():
        if not line:
            continue

        line_str = line.decode('utf-8')

        # SSE format: "data: {json}"
        if line_str.startswith('data: '):
            data_str = line_str[6:]  # Remove "data: " prefix

            if data_str.strip() == '[DONE]':
                break

            try:
                event = json.loads(data_str)

                # Handle different event types
                if event.get("type") == "answer_chunk":
                    chunk = event.get("data", {}).get("chunk", "")
                    print(chunk, end="", flush=True)
                    result["answer"] += chunk

                elif event.get("type") == "result":
                    # Source/result data
                    result_data = event.get("data", {})
                    result["results"].append(result_data)

                elif event.get("type") == "done":
                    # Final event with complete data
                    if event.get("data"):
                        final_data = event["data"]
                        if final_data.get("answer"):
                            result["answer"] = final_data["answer"]
                        if final_data.get("results"):
                            result["results"] = final_data["results"]
                        if final_data.get("costDollars"):
                            result["costDollars"] = final_data["costDollars"]

            except json.JSONDecodeError:
                # Skip malformed JSON
                continue

    print()  # Newline after streaming completes
    return result


def format_results(results: Dict[str, Any], show_sources: bool = True, max_text_length: int = 500) -> str:
    """Format research results for readable display."""
    output = []

    # Request info
    if results.get("requestId"):
        output.append(f"Request ID: {results['requestId']}")

    # Answer
    if results.get("answer"):
        output.append(f"\n{'='*60}")
        output.append("ANSWER:")
        output.append("-" * 40)
        output.append(results["answer"])

    # Sources
    sources = results.get("results", [])
    if sources and show_sources:
        output.append(f"\n{'='*60}")
        output.append(f"SOURCES ({len(sources)} used):")

        for i, s in enumerate(sources, 1):
            output.append(f"\n[{i}] {s.get('title', 'No title')}")
            output.append(f"    URL: {s.get('url', 'No URL')}")

            if s.get('author'):
                output.append(f"    Author: {s['author'][:60]}")
            if s.get('publishedDate'):
                output.append(f"    Published: {s['publishedDate'][:10]}")

            # Highlights
            if s.get('highlights'):
                output.append(f"    Key excerpts:")
                for h in s['highlights'][:2]:
                    output.append(f"      \"{h[:150]}...\"")

            # Text preview
            if s.get('text'):
                text = s['text'][:max_text_length]
                if len(s['text']) > max_text_length:
                    text += "..."
                output.append(f"    Preview: {text}")

    # Cost
    if results.get("costDollars"):
        cost = results["costDollars"]
        output.append(f"\n{'='*60}")
        output.append(f"COST: ${cost.get('total', 0):.4f}")

    return "\n".join(output)


def format_markdown(results: Dict[str, Any]) -> str:
    """Format research results as markdown with citations."""
    output = []

    # Answer
    if results.get("answer"):
        output.append("## Research Answer\n")
        output.append(results["answer"])

    # Sources as references
    sources = results.get("results", [])
    if sources:
        output.append("\n\n## Sources\n")
        for i, s in enumerate(sources, 1):
            title = s.get('title', 'Untitled')
            url = s.get('url', '')
            date = s.get('publishedDate', '')[:10] if s.get('publishedDate') else ''
            author = s.get('author', '')[:50] if s.get('author') else ''

            ref_parts = [f"[{i}] [{title}]({url})"]
            if author:
                ref_parts.append(f"by {author}")
            if date:
                ref_parts.append(f"({date})")
            output.append(" ".join(ref_parts))

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Exa Research - AI-powered deep research with citations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "What is the latest valuation of SpaceX?"
  %(prog)s "Best practices for Python async programming" --sources
  %(prog)s "Compare React vs Vue vs Svelte" --markdown
  %(prog)s "Recent AI regulation news" --after 2024-06-01 --domains techcrunch.com arstechnica.com
  %(prog)s "How does RLHF work?" --num 10 --highlights

Use Cases:
  - Quick research on any topic with citations
  - Technical documentation queries
  - Market research and competitive analysis
  - Fact-checking and verification
  - Literature reviews and synthesis
  - Current events and news summaries

Tips:
  - Use specific, well-formed questions for best results
  - Filter by domains for authoritative sources
  - Use date filters for recent information
  - Request highlights for key excerpts
        """
    )

    # Required
    parser.add_argument("query", help="Research question or topic")

    # Search options
    parser.add_argument("-n", "--num", type=int, default=5,
                        help="Number of sources to use (default: 5, max: 20)")

    # Domain filtering
    parser.add_argument("--domains", nargs="+", help="Only use these domains as sources")
    parser.add_argument("--exclude-domains", nargs="+", help="Exclude these domains")

    # Date filtering
    parser.add_argument("--after", help="Only sources published after date (YYYY-MM-DD)")
    parser.add_argument("--before", help="Only sources published before date (YYYY-MM-DD)")

    # Content options
    parser.add_argument("--no-text", action="store_true", help="Don't include source text")
    parser.add_argument("--highlights", action="store_true", help="Include key excerpts from sources")

    # Streaming
    parser.add_argument("--stream", action="store_true",
                        help="Stream the answer in real-time")

    # Output options
    parser.add_argument("--sources", action="store_true", help="Show detailed source information")
    parser.add_argument("--markdown", action="store_true", help="Output as markdown with citations")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--answer-only", action="store_true", help="Only output the answer text")
    parser.add_argument("--text-limit", type=int, default=500,
                        help="Max source text chars to display (default: 500)")

    args = parser.parse_args()

    try:
        if args.stream:
            # Streaming mode
            response = research(
                query=args.query,
                num_results=args.num,
                include_domains=args.domains,
                exclude_domains=args.exclude_domains,
                start_published_date=args.after,
                end_published_date=args.before,
                get_text=not args.no_text,
                get_highlights=args.highlights,
                stream=True,
            )
            print("ANSWER:", file=sys.stderr)
            print("-" * 40, file=sys.stderr)
            results = process_stream(response)

            # Show sources after streaming if requested
            if args.sources and results.get("results"):
                print(f"\n{'='*60}")
                print(f"SOURCES ({len(results['results'])} used):")
                for i, s in enumerate(results['results'], 1):
                    print(f"\n[{i}] {s.get('title', 'No title')}")
                    print(f"    URL: {s.get('url', 'No URL')}")
        else:
            # Non-streaming mode
            results = research(
                query=args.query,
                num_results=args.num,
                include_domains=args.domains,
                exclude_domains=args.exclude_domains,
                start_published_date=args.after,
                end_published_date=args.before,
                get_text=not args.no_text,
                get_highlights=args.highlights,
                stream=False,
            )

            if args.json:
                print(json.dumps(results, indent=2))
            elif args.answer_only:
                print(results.get("answer", "No answer generated"))
            elif args.markdown:
                print(format_markdown(results))
            else:
                print(format_results(
                    results,
                    show_sources=args.sources,
                    max_text_length=args.text_limit
                ))

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
