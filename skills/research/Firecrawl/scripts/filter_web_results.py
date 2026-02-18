#!/usr/bin/env python3
"""
Dynamic Filtering for Web Results — Post-process Firecrawl/Exa output
before it enters Claude's context window.

Accepts piped markdown or JSON from stdin and filters by:
- Heading/section extraction (--sections)
- Keyword filtering (--keywords)
- Length truncation (--max-chars, --max-lines)
- JSON field extraction (--fields)

Inspired by Anthropic's dynamic filtering technique:
https://claude.com/blog/improved-web-search-with-dynamic-filtering

Usage:
    firecrawl scrape URL --only-main-content | filter_web_results.py --sections "API,Auth"
    firecrawl search "query" --pretty | filter_web_results.py --keywords "pricing,cost" --max-chars 5000
    exa_search.py "query" --json | filter_web_results.py --fields "title,url,text" --max-chars 3000
    cat scraped.md | filter_web_results.py --sections "Installation" --keywords "pip,npm"
"""

import sys
import re
import json
import argparse
from typing import List, Optional


def extract_sections(text: str, section_names: List[str]) -> str:
    """Extract markdown sections matching any of the given heading keywords."""
    lines = text.split("\n")
    result = []
    capturing = False
    current_level = 0

    for line in lines:
        heading_match = re.match(r"^(#{1,6})\s+(.+)", line)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()

            # Check if this heading matches any section name (case-insensitive)
            matches = any(
                s.lower() in title.lower() for s in section_names
            )

            if matches:
                if not capturing:
                    capturing = True
                    current_level = level
                elif level < current_level:
                    current_level = level
                result.append(line)
            elif capturing and level <= current_level:
                # Hit a heading at same or higher level — stop capturing
                capturing = False
            elif capturing:
                result.append(line)
        elif capturing:
            result.append(line)

    return "\n".join(result)


def filter_by_keywords(text: str, keywords: List[str], context_lines: int = 1) -> str:
    """Keep only paragraphs/blocks containing at least one keyword."""
    lines = text.split("\n")
    keep = set()

    for i, line in enumerate(lines):
        line_lower = line.lower()
        if any(kw.lower() in line_lower for kw in keywords):
            # Keep this line plus context
            for j in range(max(0, i - context_lines), min(len(lines), i + context_lines + 1)):
                keep.add(j)
            # Also keep the nearest preceding heading
            for j in range(i - 1, -1, -1):
                if re.match(r"^#{1,6}\s+", lines[j]):
                    keep.add(j)
                    break

    return "\n".join(lines[i] for i in sorted(keep))


def truncate(text: str, max_chars: Optional[int] = None, max_lines: Optional[int] = None) -> str:
    """Truncate text to character or line limit."""
    if max_lines is not None:
        lines = text.split("\n")
        if len(lines) > max_lines:
            text = "\n".join(lines[:max_lines]) + f"\n\n[... truncated at {max_lines} lines]"

    if max_chars is not None and len(text) > max_chars:
        text = text[:max_chars] + f"\n\n[... truncated at {max_chars} chars]"

    return text


def extract_json_fields(data, fields: List[str]):
    """Extract specified fields from JSON data (handles lists and dicts)."""
    def extract_from_obj(obj):
        if isinstance(obj, dict):
            return {k: v for k, v in obj.items() if k in fields}
        return obj

    if isinstance(data, list):
        return [extract_from_obj(item) for item in data]
    elif isinstance(data, dict):
        # Check if it has a 'data' or 'results' key (common API pattern)
        for key in ("data", "results", "items", "annotations"):
            if key in data and isinstance(data[key], list):
                data[key] = [extract_from_obj(item) for item in data[key]]
                return data
        return extract_from_obj(data)
    return data


def main():
    parser = argparse.ArgumentParser(
        description="Filter web results before they enter context. Pipe from firecrawl/exa.",
        epilog="Examples:\n"
               "  firecrawl scrape URL | filter_web_results.py --sections 'API,Auth'\n"
               "  exa_search.py 'q' --json | filter_web_results.py --fields 'title,url' --max-chars 3000",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--sections", "-s", help="Comma-separated heading keywords to extract")
    parser.add_argument("--keywords", "-k", help="Comma-separated keywords — keep only matching paragraphs")
    parser.add_argument("--context-lines", type=int, default=1, help="Lines of context around keyword matches (default: 1)")
    parser.add_argument("--max-chars", "-c", type=int, help="Maximum output characters")
    parser.add_argument("--max-lines", "-l", type=int, help="Maximum output lines")
    parser.add_argument("--fields", "-f", help="Comma-separated JSON fields to extract (for JSON input)")
    parser.add_argument("--strip-links", action="store_true", help="Remove markdown links, keep text")
    parser.add_argument("--strip-images", action="store_true", help="Remove markdown images")
    parser.add_argument("--compact", action="store_true", help="Collapse multiple blank lines to one")
    parser.add_argument("--stats", action="store_true", help="Print input/output stats to stderr")

    args = parser.parse_args()

    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)

    input_chars = len(raw)
    input_lines = raw.count("\n")

    # Try JSON mode first
    is_json = False
    if args.fields:
        try:
            data = json.loads(raw)
            is_json = True
            fields = [f.strip() for f in args.fields.split(",")]
            data = extract_json_fields(data, fields)
            text = json.dumps(data, indent=2)
        except json.JSONDecodeError as e:
            print(f"error: --fields requires valid JSON input ({e})", file=sys.stderr)
            sys.exit(2)
    else:
        text = raw

    # Markdown filtering (skip for JSON)
    if not is_json:
        if args.sections:
            section_names = [s.strip() for s in args.sections.split(",") if s.strip()]
            if section_names:
                text = extract_sections(text, section_names)

        if args.keywords:
            keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
            text = filter_by_keywords(text, keywords, args.context_lines)

        if args.strip_images:
            text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)

        if args.strip_links:
            text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

        if args.compact:
            text = re.sub(r"\n{3,}", "\n\n", text)

    # Truncation (always last)
    text = truncate(text, args.max_chars, args.max_lines)

    output_chars = len(text)
    output_lines = text.count("\n")

    if args.stats:
        reduction = (1 - output_chars / input_chars) * 100 if input_chars > 0 else 0
        print(f"[filter] {input_chars:,} → {output_chars:,} chars ({reduction:.0f}% reduction), "
              f"{input_lines} → {output_lines} lines", file=sys.stderr)

    print(text)


if __name__ == "__main__":
    main()
