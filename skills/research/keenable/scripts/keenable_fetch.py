#!/usr/bin/env python3
"""Keenable page fetch — fetch webpage contents as markdown with optional LLM extraction."""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse

API_BASE = "https://api.keenable.ai"


def fetch(url, live=False, prompt=None, max_chars=None):
    api_key = os.environ.get("KEENABLE_API_KEY")
    if not api_key:
        print("Error: KEENABLE_API_KEY environment variable not set", file=sys.stderr)
        print("Get your key at https://app.keenable.ai", file=sys.stderr)
        sys.exit(1)

    params = {"url": url}
    if live:
        params["live"] = "true"
    if prompt:
        params["prompt"] = prompt
    if max_chars is not None:
        params["max_chars"] = str(max_chars)

    endpoint = f"{API_BASE}/v1/fetch?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        endpoint,
        headers={"X-API-Key": api_key},
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
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


def format_output(result, raw_json=False):
    if raw_json:
        print(json.dumps(result, indent=2))
        return

    if isinstance(result, str):
        print(result)
        return

    content = result.get("content", "")
    title = result.get("title", "")
    url = result.get("url", "")

    if title:
        print(f"# {title}")
    if url:
        print(f"Source: {url}\n")
    if content:
        print(content)
    elif not title and not url:
        print(json.dumps(result, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Fetch webpage contents with Keenable AI")
    parser.add_argument("url", help="URL to fetch")
    parser.add_argument("--live", action="store_true",
                        help="Force live fetch instead of cached/indexed copy")
    parser.add_argument("--prompt",
                        help="LLM-driven extraction — describe what to extract (e.g. 'List all pricing tiers')")
    parser.add_argument("--max-chars", type=int, dest="max_chars",
                        help="Max characters of content (default 50000)")
    parser.add_argument("--json", action="store_true", help="Raw JSON output")

    args = parser.parse_args()
    result = fetch(args.url, live=args.live, prompt=args.prompt, max_chars=args.max_chars)
    format_output(result, raw_json=args.json)


if __name__ == "__main__":
    main()
