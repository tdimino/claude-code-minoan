#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""
Image Well — Multi-source image search and download.

Usage:
    well.py search "query" [--sources openverse pexels ...] [--preset museum] [--limit 10]
    well.py sources
    well.py cache stats|clear
"""

import argparse
import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path

# Ensure sources package is importable
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from _well_utils import (
    ImageResult,
    cache_clear,
    cache_get,
    cache_put,
    cache_stats,
    format_html,
    format_json,
    format_table,
    format_urls,
    license_matches,
    warn,
)
from sources import PRESETS, TIER_1, TIER_2, TIER_3, get_source, list_sources

import aiohttp


async def search_sources(
    query: str,
    source_names: list[str],
    limit: int,
    license_filter: str,
    timeout: int,
    quiet: bool,
) -> list[ImageResult]:
    """Search multiple sources in parallel."""
    sources = []
    for name in source_names:
        src = get_source(name)
        if src is None:
            if not quiet:
                warn(f"Unknown source: {name}")
            continue
        if not src.is_available():
            if not quiet:
                warn(f"{name}: {src.key_env_var} not set, skipping")
            continue
        sources.append(src)

    if not sources:
        warn("No available sources to search")
        return []

    if not quiet:
        names = ", ".join(s.name for s in sources)
        print(f"Searching {len(sources)} sources: {names}", file=sys.stderr)

    async with aiohttp.ClientSession(
        headers={"User-Agent": "ImageWell/1.0 (github.com/tdimino)"}
    ) as session:
        tasks = [
            asyncio.wait_for(
                src.search(query, limit, license_filter, session),
                timeout=timeout,
            )
            for src in sources
        ]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

    # Collect results, log errors
    per_source: list[list[ImageResult]] = []
    for src, result in zip(sources, raw_results):
        if isinstance(result, Exception):
            if not quiet:
                warn(f"{src.name}: {result}")
            per_source.append([])
        else:
            per_source.append(result)
            if not quiet:
                print(f"  {src.name}: {len(result)} results", file=sys.stderr)

    # Interleave results round-robin
    merged: list[ImageResult] = []
    seen_urls: set[str] = set()
    max_len = max((len(r) for r in per_source), default=0)
    for i in range(max_len):
        for source_results in per_source:
            if i < len(source_results):
                r = source_results[i]
                if r.url not in seen_urls:
                    seen_urls.add(r.url)
                    merged.append(r)

    # Apply license filter
    if license_filter and license_filter != "any":
        merged = [r for r in merged if license_matches(r.license, license_filter)]

    return merged


async def download_results(
    results: list[ImageResult],
    output_dir: Path,
    quiet: bool,
) -> int:
    """Download images and write metadata sidecars. Returns count downloaded."""
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded = 0
    sem = asyncio.Semaphore(5)

    async def download_one(r: ImageResult, session: aiohttp.ClientSession) -> bool:
        if not r.url:
            return False
        async with sem:
            try:
                async with session.get(r.url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status != 200:
                        if not quiet:
                            warn(f"Download failed ({resp.status}): {r.url[:60]}")
                        return False
                    data = await resp.read()
            except (aiohttp.ClientError, TimeoutError) as e:
                if not quiet:
                    warn(f"Download error: {e}")
                return False

            # Determine extension from URL or content-type
            ext = ".jpg"
            url_lower = r.url.lower().split("?")[0]
            if url_lower.endswith(".png"):
                ext = ".png"
            elif url_lower.endswith(".webp"):
                ext = ".webp"
            elif url_lower.endswith(".svg"):
                ext = ".svg"

            # Sanitize filename
            safe_title = "".join(c if c.isalnum() or c in "-_ " else "" for c in r.title)[:40].strip()
            safe_title = safe_title.replace(" ", "_") or "image"
            h = hashlib.sha256(r.url.encode()).hexdigest()[:8]
            filename = f"{r.source}_{safe_title}_{h}{ext}"

            filepath = output_dir / filename
            filepath.write_bytes(data)

            # Write metadata sidecar
            meta_path = output_dir / f"{filename}.meta.json"
            meta_path.write_text(json.dumps(r.to_dict(), indent=2))

            if not quiet:
                size_kb = len(data) / 1024
                print(f"  \u2193 {filename} ({size_kb:.0f} KB)")
            return True

    async with aiohttp.ClientSession(
        headers={"User-Agent": "ImageWell/1.0 (github.com/tdimino)"}
    ) as session:
        tasks = [download_one(r, session) for r in results]
        outcomes = await asyncio.gather(*tasks)
        downloaded = sum(1 for ok in outcomes if ok)

    return downloaded


def resolve_sources(args: argparse.Namespace) -> list[str]:
    """Resolve which sources to search based on args."""
    if args.preset:
        preset = PRESETS.get(args.preset)
        if not preset:
            print(f"Unknown preset: {args.preset}. Available: {', '.join(PRESETS.keys())}", file=sys.stderr)
            sys.exit(1)
        return preset["sources"]

    if args.sources:
        return args.sources

    # Auto: start with Tier 1
    return list(TIER_1)


def cmd_search(args: argparse.Namespace) -> int:
    """Execute search command."""
    query = " ".join(args.query)
    if not query.strip():
        print("Error: search query required", file=sys.stderr)
        return 1

    source_names = resolve_sources(args)
    license_filter = args.license or "any"
    if args.preset and PRESETS.get(args.preset, {}).get("license"):
        license_filter = PRESETS[args.preset]["license"]

    # Check cache
    if not args.no_cache:
        cached = cache_get(query, source_names, license_filter)
        if cached is not None:
            if not args.quiet:
                print(f"Cache hit ({len(cached)} results)", file=sys.stderr)
            results = cached
        else:
            results = asyncio.run(search_sources(
                query, source_names, args.limit, license_filter, args.timeout, args.quiet
            ))
            if results:
                cache_put(query, source_names, license_filter, results)
    else:
        results = asyncio.run(search_sources(
            query, source_names, args.limit, license_filter, args.timeout, args.quiet
        ))

    if not results:
        print("No results found.", file=sys.stderr)
        return 0

    # Output
    fmt = args.format or "table"
    if fmt == "download":
        output_dir = Path(args.output)
        count = asyncio.run(download_results(results, output_dir, args.quiet))
        print(f"\nDownloaded {count}/{len(results)} images to {output_dir}", file=sys.stderr)
    elif fmt == "json":
        print(format_json(results))
    elif fmt == "urls":
        print(format_urls(results))
    elif fmt == "html":
        html_path = format_html(results, query)
        print(f"Preview: {html_path}", file=sys.stderr)
        # Auto-open on macOS
        import subprocess
        subprocess.run(["open", str(html_path)], check=False)
    else:
        print(format_table(results))

    return 0


def cmd_sources(args: argparse.Namespace) -> int:
    """List all sources and their status."""
    print("Image Well Sources")
    print("=" * 60)
    for name in list_sources():
        src = get_source(name)
        if src:
            print(src.status_line())
    print()
    print("Presets:")
    for preset_name, config in PRESETS.items():
        src_list = ", ".join(config["sources"])
        lic = config.get("license") or "any"
        print(f"  {preset_name:<12s}  [{lic}]  {src_list}")
    return 0


def cmd_cache(args: argparse.Namespace) -> int:
    """Manage cache."""
    sub = args.cache_action
    if sub == "stats":
        stats = cache_stats()
        print(f"Cache entries: {stats['entries']}")
        print(f"Cache size: {stats['size_kb']} KB")
    elif sub == "clear":
        removed = cache_clear()
        print(f"Removed {removed} cache entries")
    else:
        print(f"Unknown cache action: {sub}", file=sys.stderr)
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="well",
        description="Image Well — Multi-source image search and download",
    )
    subparsers = parser.add_subparsers(dest="command")

    # search
    search_p = subparsers.add_parser("search", help="Search for images")
    search_p.add_argument("query", nargs="+", help="Search query")
    search_p.add_argument("--sources", nargs="+", help="Sources to search")
    search_p.add_argument("--preset", help="Use a preset (military, museum, texture, stock, all-free)")
    search_p.add_argument("--limit", type=int, default=10, help="Max results per source (default: 10)")
    search_p.add_argument("--license", help="License filter: cc0, cc-by, cc-by-sa, any (default: any)")
    search_p.add_argument("--min-width", type=int, default=0, help="Min image width")
    search_p.add_argument("--min-height", type=int, default=0, help="Min image height")
    search_p.add_argument("--format", choices=["table", "json", "download", "urls", "html"], default="table")
    search_p.add_argument("--output", default="./well-images", help="Download output dir")
    search_p.add_argument("--no-cache", action="store_true", help="Skip cache")
    search_p.add_argument("--timeout", type=int, default=15, help="Per-source timeout (seconds)")
    search_p.add_argument("--quiet", action="store_true", help="Suppress progress")

    # sources
    subparsers.add_parser("sources", help="List available sources and status")

    # cache
    cache_p = subparsers.add_parser("cache", help="Manage search cache")
    cache_p.add_argument("cache_action", choices=["stats", "clear"], help="Cache action")

    args = parser.parse_args()

    if args.command == "search":
        return cmd_search(args)
    elif args.command == "sources":
        return cmd_sources(args)
    elif args.command == "cache":
        return cmd_cache(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
