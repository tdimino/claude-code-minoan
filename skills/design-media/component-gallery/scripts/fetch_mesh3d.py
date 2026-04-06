#!/usr/bin/env python3
"""Fetch and query mesh3d.gallery directory via /llms-full.txt endpoint."""

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

CACHE_DIR = Path(__file__).parent.parent / ".staging"
CACHE_FILE = CACHE_DIR / "mesh3d-entries.json"
LLM_URL = "https://mesh3d.gallery/llms-full.txt"
MAX_AGE_HOURS = 24


def fetch_raw() -> str:
    """Fetch the llms-full.txt content."""
    req = urllib.request.Request(LLM_URL, headers={"User-Agent": "claude-skill/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def parse_entries(raw: str) -> list[dict]:
    """Parse the llms-full.txt Markdown format into structured entries.

    Format: ### Title headings with - Key: Value bullet lists.
    """
    entries = []
    current = {}

    for line in raw.splitlines():
        stripped = line.strip()

        # New entry: ### Title
        heading_match = re.match(r"^#{1,4}\s+(.+)$", stripped)
        if heading_match:
            if current:
                entries.append(current)
            current = {"title": heading_match.group(1).strip()}
            continue

        if not stripped:
            continue

        # Bullet field: - Key: Value
        bullet_match = re.match(r"^-\s+([A-Za-z_\- ]+):\s*(.+)$", stripped)
        if bullet_match:
            key = bullet_match.group(1).strip().lower().replace(" ", "_").replace("-", "_")
            value = bullet_match.group(2).strip()
            current[key] = value
            continue

        # Plain key: value (fallback)
        kv_match = re.match(r"^([A-Za-z_\- ]+):\s*(.+)$", stripped)
        if kv_match:
            key = kv_match.group(1).strip().lower().replace(" ", "_").replace("-", "_")
            value = kv_match.group(2).strip()
            current[key] = value

    if current:
        entries.append(current)

    return entries


def load_cached() -> list[dict] | None:
    """Load cached entries if fresh enough."""
    if not CACHE_FILE.exists():
        return None
    import time
    age_hours = (time.time() - CACHE_FILE.stat().st_mtime) / 3600
    if age_hours > MAX_AGE_HOURS:
        return None
    return json.loads(CACHE_FILE.read_text())


def save_cache(entries: list[dict]) -> None:
    """Save entries to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(entries, indent=2))


def get_entries(force_refresh: bool = False) -> list[dict]:
    """Get entries, using cache if available."""
    if not force_refresh:
        cached = load_cached()
        if cached is not None:
            return cached

    print("Fetching mesh3d.gallery directory...", file=sys.stderr)
    raw = fetch_raw()
    entries = parse_entries(raw)
    save_cache(entries)
    print(f"Cached {len(entries)} entries", file=sys.stderr)
    return entries


def filter_entries(entries: list[dict], tech: str = None, maker: str = None, search: str = None) -> list[dict]:
    """Filter entries by criteria."""
    results = entries

    if tech:
        tech_lower = tech.lower()
        results = [e for e in results if tech_lower in json.dumps(e).lower()]

    if maker:
        maker_lower = maker.lower()
        results = [e for e in results if any(maker_lower in str(v).lower() for v in e.values())]

    if search:
        search_lower = search.lower()
        results = [e for e in results if search_lower in json.dumps(e).lower()]

    return results


def format_entry(entry: dict) -> str:
    """Format a single entry for display."""
    lines = []
    title = entry.get("title", entry.get("name", "Unknown"))
    url = entry.get("url", entry.get("website", ""))
    maker = entry.get("makers", entry.get("maker", entry.get("studio", "")))
    desc = entry.get("description", "")
    tech = entry.get("technologies", entry.get("technology", ""))
    tags = entry.get("tags", "")

    lines.append(f"  {title}")
    if url:
        lines.append(f"    URL: {url}")
    if maker:
        lines.append(f"    Maker: {maker}")
    if tech:
        lines.append(f"    Tech: {tech}")
    if tags:
        lines.append(f"    Tags: {tags}")
    if desc:
        lines.append(f"    {desc[:120]}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Query mesh3d.gallery directory")
    parser.add_argument("--tech", help="Filter by technology (e.g., 'Three.js')")
    parser.add_argument("--maker", help="Filter by maker/studio name")
    parser.add_argument("--search", help="Search all fields by keyword")
    parser.add_argument("--refresh", action="store_true", help="Force refresh from web")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--limit", type=int, default=20, help="Max results (default: 20)")
    args = parser.parse_args()

    entries = get_entries(force_refresh=args.refresh)

    if args.tech or args.maker or args.search:
        results = filter_entries(entries, tech=args.tech, maker=args.maker, search=args.search)
    else:
        results = entries

    results = results[:args.limit]

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"mesh3d.gallery: {len(results)} results (of {len(entries)} total)\n")
        for entry in results:
            print(format_entry(entry))
            print()


if __name__ == "__main__":
    main()
