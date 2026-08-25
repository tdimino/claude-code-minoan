#!/usr/bin/env python3
"""Keenable web search — search the web and return ranked results."""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

API_BASE = "https://api.keenable.ai"


def search(query, **kwargs):
    api_key = os.environ.get("KEENABLE_API_KEY")
    if not api_key:
        print("Error: KEENABLE_API_KEY environment variable not set", file=sys.stderr)
        print("Get your key at https://app.keenable.ai", file=sys.stderr)
        sys.exit(1)

    endpoint = f"{API_BASE}/v1/search"

    body = {"query": query}
    for key in ("site", "max_results", "snippet_max_length", "acquired_after", "acquired_before",
                "published_after", "published_before", "query_time"):
        if kwargs.get(key) is not None:
            body[key] = kwargs[key]

    data = json.dumps(body).encode()
    req = urllib.request.Request(
        endpoint,
        data=data,
        headers={
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"Error {e.code}: {e.reason}", file=sys.stderr)
        if error_body:
            print(error_body, file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def format_results(results, raw_json=False):
    if raw_json:
        print(json.dumps(results, indent=2))
        return

    items = results.get("results", [])

    if not items:
        print("No results found.")
        return

    for i, item in enumerate(items, 1):
        title = item.get("title", "No title")
        url = item.get("url", "")
        description = item.get("description", "")
        snippet = item.get("snippet", "")

        print(f"\n{'─' * 60}")
        print(f"  [{i}] {title}")
        print(f"  {url}")
        if description:
            print(f"  {description[:200]}")
        if snippet:
            print(f"\n  {snippet[:500]}")

    print(f"\n{'─' * 60}")
    print(f"  {len(items)} result(s)")


def main():
    parser = argparse.ArgumentParser(description="Search the web with Keenable AI")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--site", help="Restrict to a specific domain")
    parser.add_argument("--count", type=int, dest="max_results",
                        help="Number of results (1-50, default 10)")
    parser.add_argument("--snippet-length", type=int, dest="snippet_max_length",
                        help="Snippet max character length (180-10000)")
    parser.add_argument("--acquired-after", dest="acquired_after",
                        help="Filter: acquired after date (YYYY-MM-DD, or relative: 7d, 30min, 2h)")
    parser.add_argument("--acquired-before", dest="acquired_before",
                        help="Filter: acquired before date")
    parser.add_argument("--published-after", dest="published_after",
                        help="Filter: published after date (YYYY-MM-DD, or relative: 7d, 30min)")
    parser.add_argument("--published-before", dest="published_before",
                        help="Filter: published before date")
    parser.add_argument("--query-time", dest="query_time",
                        help="Point-in-time search — query index as of this datetime (YYYY-MM-DD or ISO 8601)")
    parser.add_argument("--json", action="store_true", help="Raw JSON output")

    args = parser.parse_args()

    kwargs = {}
    for field in ("site", "max_results", "snippet_max_length", "acquired_after", "acquired_before",
                  "published_after", "published_before", "query_time"):
        val = getattr(args, field, None)
        if val is not None:
            kwargs[field] = val

    results = search(args.query, **kwargs)
    format_results(results, raw_json=args.json)


if __name__ == "__main__":
    main()
