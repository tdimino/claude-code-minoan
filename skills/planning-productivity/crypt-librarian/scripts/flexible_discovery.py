#!/usr/bin/env python3
"""
Flexible Film Discovery Script
Adapts to user requests rather than enforcing predefined Crypt Librarian filters.

Usage:
    python flexible_discovery.py "your search query" [options]

Options:
    --era DECADE          Filter by decade (70s, 80s, 90s, 2000s, 2010s, any)
    --region REGION       Filter by region (american, european, asian, british, any)
    --mood MOOD           Mood/tone (noir, gothic, thriller, drama, horror, comedy, any)
    --subreddits LIST     Comma-separated subreddits to search
    --limit N             Max results per source (default: 15)
    --sources LIST        Comma-separated: reddit,perplexity,exa (default: all)

Examples:
    python flexible_discovery.py "Korean revenge thrillers"
    python flexible_discovery.py "cozy mysteries" --era 90s --region british
    python flexible_discovery.py "films like Drive" --mood noir --limit 20
    python flexible_discovery.py "documentary nature" --sources reddit
"""

import argparse
import json
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def search_reddit(query: str, subreddits: list[str], limit: int = 15) -> list[dict]:
    """Search Reddit using the JSON API suffix trick."""
    results = []

    default_subreddits = [
        "MovieSuggestions",
        "TrueFilm",
        "criterion",
        "horror",
        "movies",
        "flicks"
    ]

    subs_to_search = subreddits if subreddits else default_subreddits

    for sub in subs_to_search:
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://www.reddit.com/r/{sub}/search.json?q={encoded_query}&restrict_sr=1&sort=relevance&limit={limit}"

            req = urllib.request.Request(
                url,
                headers={"User-Agent": "FlexibleFilmDiscovery/1.0"}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                posts = data.get("data", {}).get("children", [])

                for post in posts[:limit]:
                    post_data = post.get("data", {})
                    results.append({
                        "source": f"r/{sub}",
                        "title": post_data.get("title", ""),
                        "score": post_data.get("score", 0),
                        "url": f"https://reddit.com{post_data.get('permalink', '')}",
                        "selftext": post_data.get("selftext", "")[:500]
                    })
        except Exception as e:
            print(f"  [Reddit r/{sub}] Error: {e}", file=sys.stderr)

    # Sort by score and dedupe by title similarity
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:limit * 2]


def build_enhanced_query(base_query: str, era: str, region: str, mood: str) -> str:
    """Build an enhanced search query with filters."""
    parts = [base_query]

    era_map = {
        "70s": "1970s",
        "80s": "1980s",
        "90s": "1990s",
        "2000s": "2000s",
        "2010s": "2010s",
    }

    if era and era != "any":
        parts.append(era_map.get(era, era))

    if region and region != "any":
        parts.append(region)

    if mood and mood != "any":
        parts.append(mood)

    return " ".join(parts)


def format_reddit_results(results: list[dict]) -> str:
    """Format Reddit results for display."""
    if not results:
        return "No Reddit results found."

    output = []
    seen_titles = set()

    for r in results:
        # Basic deduplication
        title_key = r["title"][:50].lower()
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)

        output.append(f"[{r['source']}] ({r['score']} pts) {r['title'][:100]}")
        if r["selftext"]:
            # Extract film mentions from selftext
            text = r["selftext"][:200].replace("\n", " ")
            output.append(f"    {text}...")

    return "\n".join(output[:30])


def main():
    parser = argparse.ArgumentParser(
        description="Flexible film discovery - adapts to your request",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument("query", help="Your search query")
    parser.add_argument("--era", default="any",
                       help="Decade filter: 70s, 80s, 90s, 2000s, 2010s, any")
    parser.add_argument("--region", default="any",
                       help="Region: american, european, asian, british, any")
    parser.add_argument("--mood", default="any",
                       help="Mood/tone: noir, gothic, thriller, drama, horror, any")
    parser.add_argument("--subreddits", default="",
                       help="Comma-separated subreddits to search")
    parser.add_argument("--limit", type=int, default=15,
                       help="Max results per source")
    parser.add_argument("--sources", default="reddit",
                       help="Comma-separated: reddit,perplexity,exa")
    parser.add_argument("--json", action="store_true",
                       help="Output as JSON for programmatic use")

    args = parser.parse_args()

    # Build enhanced query
    enhanced_query = build_enhanced_query(
        args.query, args.era, args.region, args.mood
    )

    sources = [s.strip().lower() for s in args.sources.split(",")]
    subreddits = [s.strip() for s in args.subreddits.split(",") if s.strip()]

    all_results = {}

    print(f"\n🎬 Flexible Film Discovery", file=sys.stderr)
    print(f"   Query: {enhanced_query}", file=sys.stderr)
    print(f"   Sources: {', '.join(sources)}", file=sys.stderr)
    print("-" * 50, file=sys.stderr)

    # Reddit search
    if "reddit" in sources:
        print("\n📍 Searching Reddit...", file=sys.stderr)
        reddit_results = search_reddit(enhanced_query, subreddits, args.limit)
        all_results["reddit"] = reddit_results

        if not args.json:
            print("\n## Reddit Results\n")
            print(format_reddit_results(reddit_results))

    # For Perplexity and Exa, output the command to run
    # (These require MCP or API access that's better handled by Claude directly)
    if "perplexity" in sources and not args.json:
        print("\n## Perplexity Query\n")
        print(f"Use mcp__perplexity__search with query:")
        print(f'  "{enhanced_query} film recommendations underrated"')

    if "exa" in sources and not args.json:
        print("\n## Exa Query\n")
        print(f"Run: python exa_film_search.py search \"{enhanced_query}\" -n {args.limit}")

    if args.json:
        print(json.dumps(all_results, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
