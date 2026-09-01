#!/usr/bin/env python3
"""Fetch and query mesh3d.gallery directory via /llms-full.txt endpoint."""

import argparse
import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
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


def parse_entries(raw: str) -> tuple[list[dict], int | None]:
    """Parse ### website entries under the '## Websites' section.

    Returns (entries, declared_total). Only ### headings with a URL field
    are counted as valid entries. Section headings (H1/H2) are skipped.
    """
    declared_total = None
    entries = []
    current: dict = {}
    in_websites = False

    for line in raw.splitlines():
        stripped = line.strip()

        h2_match = re.match(r"^##\s+(.+)$", stripped)
        if h2_match:
            title = h2_match.group(1).strip()
            if current and "url" in current:
                entries.append(current)
                current = {}
            websites_match = re.match(
                r"Websites\s*\((\d+)\s+entries?\)", title
            )
            if websites_match:
                in_websites = True
                declared_total = int(websites_match.group(1))
            elif title.startswith("Websites"):
                in_websites = True
            else:
                in_websites = False
            continue

        if re.match(r"^#\s+", stripped):
            continue

        if not in_websites:
            continue

        h3_match = re.match(r"^###\s+(.+)$", stripped)
        if h3_match:
            if current and "url" in current:
                entries.append(current)
            current = {"title": h3_match.group(1).strip()}
            continue

        if not stripped:
            continue

        bullet_match = re.match(r"^-\s+([A-Za-z_\- ]+):\s*(.+)$", stripped)
        if bullet_match and current:
            key = (
                bullet_match.group(1)
                .strip()
                .lower()
                .replace(" ", "_")
                .replace("-", "_")
            )
            value = bullet_match.group(2).strip()
            current[key] = value
            continue

        kv_match = re.match(r"^([A-Za-z_\- ]+):\s*(.+)$", stripped)
        if kv_match and current:
            key = (
                kv_match.group(1)
                .strip()
                .lower()
                .replace(" ", "_")
                .replace("-", "_")
            )
            value = kv_match.group(2).strip()
            current[key] = value

    if current and "url" in current:
        entries.append(current)

    return entries, declared_total


def load_cached() -> list[dict] | None:
    """Load cached entries if fresh enough."""
    if not CACHE_FILE.exists():
        return None
    age_hours = (time.time() - CACHE_FILE.stat().st_mtime) / 3600
    if age_hours > MAX_AGE_HOURS:
        return None
    data = json.loads(CACHE_FILE.read_text())
    if isinstance(data, dict):
        return data.get("entries", data.get("data", []))
    return data


def save_cache(
    entries: list[dict],
    declared_total: int | None = None,
) -> None:
    """Save entries to cache with metadata."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_data = {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "declared_total": declared_total,
        "entry_count": len(entries),
        "entries": entries,
    }
    CACHE_FILE.write_text(json.dumps(cache_data, indent=2))


def get_entries(force_refresh: bool = False) -> tuple[list[dict], dict]:
    """Get entries, using cache if available.

    Returns (entries, meta) where meta has fetched_at, declared_total, entry_count.
    """
    if not force_refresh:
        cached = load_cached()
        if cached is not None:
            if CACHE_FILE.exists():
                try:
                    raw_cache = json.loads(CACHE_FILE.read_text())
                    if isinstance(raw_cache, dict):
                        meta = {
                            "fetched_at": raw_cache.get("fetched_at", "unknown"),
                            "declared_total": raw_cache.get("declared_total"),
                            "entry_count": raw_cache.get("entry_count", len(cached)),
                        }
                        return cached, meta
                except (json.JSONDecodeError, KeyError):
                    pass
            return cached, {
                "fetched_at": "unknown",
                "declared_total": None,
                "entry_count": len(cached),
            }

    print("Fetching mesh3d.gallery directory...", file=sys.stderr)
    raw = fetch_raw()
    entries, declared_total = parse_entries(raw)
    save_cache(entries, declared_total)
    meta = {
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "declared_total": declared_total,
        "entry_count": len(entries),
    }
    print(
        f"Cached {len(entries)} entries (endpoint declares {declared_total})",
        file=sys.stderr,
    )
    return entries, meta


def filter_entries(
    entries: list[dict],
    tech: str = None,
    maker: str = None,
    search: str = None,
) -> list[dict]:
    """Filter entries by criteria."""
    results = entries

    if tech:
        tech_lower = tech.lower()
        results = [e for e in results if tech_lower in json.dumps(e).lower()]

    if maker:
        maker_lower = maker.lower()
        results = [
            e
            for e in results
            if any(maker_lower in str(v).lower() for v in e.values())
        ]

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
    parser.add_argument(
        "--refresh", action="store_true", help="Force refresh from web"
    )
    parser.add_argument(
        "--no-cache", action="store_true", help="Force refresh (alias for --refresh)"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--limit", type=int, default=20, help="Max results (default: 20)"
    )
    args = parser.parse_args()

    force = args.refresh or args.no_cache
    entries, meta = get_entries(force_refresh=force)

    if args.tech or args.maker or args.search:
        results = filter_entries(
            entries, tech=args.tech, maker=args.maker, search=args.search
        )
    else:
        results = entries

    results = results[: args.limit]

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        declared = meta.get("declared_total")
        fetched = meta.get("fetched_at", "unknown")
        total_line = f"{len(results)} results (of {len(entries)} cached"
        if declared:
            total_line += f", endpoint declares {declared}"
        total_line += f", fetched {fetched})"
        print(f"mesh3d.gallery: {total_line}\n")
        for entry in results:
            print(format_entry(entry))
            print()


if __name__ == "__main__":
    main()
