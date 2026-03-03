#!/usr/bin/env python3
"""
Component Gallery ingestion pipeline.

Crawls component.gallery, fetches deep-dive content from GitHub,
organizes into per-page markdown files, and builds an RLAMA RAG collection.

Usage:
    python3 ingest.py --full          # Full crawl + deep-dives + RLAMA build
    python3 ingest.py --rebuild-rag   # Rebuild RLAMA from existing .staging/
    python3 ingest.py --skip-rlama    # Crawl + deep-dives, skip RLAMA build
    python3 ingest.py --deep-dives    # Fetch GitHub deep-dives only
"""

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

SKILL_DIR = Path(__file__).resolve().parent.parent
STAGING_DIR = SKILL_DIR / ".staging"
PAGES_DIR = STAGING_DIR / "pages"
DEEP_DIVES_DIR = STAGING_DIR / "deep-dives"
CRAWL_OUTPUT = STAGING_DIR / "crawl-output.json"

RAG_NAME = "component-gallery"

# 12 deep-dive markdown files in the GitHub repo
DEEP_DIVE_FILES = [
    "accordion.md", "breadcrumbs.md", "button-group.md", "button.md",
    "carousel.md", "pagination.md", "popover.md", "quote.md",
    "rating.md", "rich-text-editor.md", "tabs.md", "tree-view.md",
]

GITHUB_RAW_BASE = (
    "https://raw.githubusercontent.com/inbn/component-gallery/"
    "main/src/content/componentContent"
)


def crawl_site():
    """Crawl component.gallery with firecrawl and save JSON output."""
    print("=== Phase A: Crawling component.gallery with Firecrawl ===")
    PAGES_DIR.mkdir(parents=True, exist_ok=True)

    cmd = [
        "firecrawl", "crawl", "https://component.gallery/",
        "--wait", "--progress",
        "--limit", "80",
        "--include-paths", "/components/,/design-systems,/about",
        "-o", str(CRAWL_OUTPUT),
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"ERROR: firecrawl crawl failed with code {result.returncode}")
        sys.exit(1)

    split_crawl_output()


def split_crawl_output():
    """Split the firecrawl JSON blob into per-page markdown files."""
    print("\nSplitting crawl output into per-page files...")

    if not CRAWL_OUTPUT.exists():
        print(f"ERROR: {CRAWL_OUTPUT} not found. Run --full or --crawl-only first.")
        sys.exit(1)

    with open(CRAWL_OUTPUT) as f:
        data = json.load(f)

    pages = data if isinstance(data, list) else data.get("data", [])
    today = datetime.now().strftime("%Y-%m-%d")
    written = 0

    PAGES_DIR.mkdir(parents=True, exist_ok=True)

    for page in pages:
        meta = page.get("metadata", {})
        url = meta.get("url") or meta.get("sourceURL", "") or page.get("url", "")
        markdown = page.get("markdown", "")
        title = meta.get("title", "") or page.get("title", "")

        if not markdown or not url:
            continue

        # Derive filename from URL path
        path = urlparse(url).path.strip("/")
        if not path:
            filename = "index.md"
        else:
            filename = path.replace("/", "-") + ".md"

        # Prepend frontmatter
        content = f"---\nurl: {url}\ntitle: \"{title}\"\nscraped_date: {today}\n---\n\n{markdown}"

        filepath = PAGES_DIR / filename
        filepath.write_text(content)
        written += 1

    print(f"Wrote {written} page files to {PAGES_DIR}")


def fetch_deep_dives():
    """Fetch 12 deep-dive markdown files from GitHub (free, no Firecrawl credits)."""
    print("\n=== Phase B: Fetching deep-dive content from GitHub ===")
    DEEP_DIVES_DIR.mkdir(parents=True, exist_ok=True)

    fetched = 0
    for filename in DEEP_DIVE_FILES:
        url = f"{GITHUB_RAW_BASE}/{filename}"
        filepath = DEEP_DIVES_DIR / filename

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "component-gallery-skill/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8")
                filepath.write_text(content)
                fetched += 1
                print(f"  Fetched {filename} ({len(content)} bytes)")
        except Exception as e:
            print(f"  WARNING: Failed to fetch {filename}: {e}")

        time.sleep(0.3)

    print(f"Fetched {fetched}/{len(DEEP_DIVE_FILES)} deep-dive files to {DEEP_DIVES_DIR}")


def build_rlama_collection():
    """Build the RLAMA RAG collection from .staging/ files."""
    print("\n=== Phase C: Building RLAMA collection ===")

    # Count files
    md_files = list(STAGING_DIR.rglob("*.md"))
    print(f"Found {len(md_files)} markdown files in {STAGING_DIR}")

    if not md_files:
        print("ERROR: No markdown files found. Run crawl first.")
        sys.exit(1)

    # Delete existing collection if it exists
    print(f"Removing existing '{RAG_NAME}' collection (if any)...")
    subprocess.run(["rlama", "delete", RAG_NAME], capture_output=True)

    # Build new collection
    cmd = [
        "rlama", "rag", "qwen2.5:7b", RAG_NAME, str(STAGING_DIR),
        "--chunking=semantic",
        "--chunk-size=1500",
        "--chunk-overlap=300",
        "--process-ext=.md",
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print(f"ERROR: rlama rag failed with code {result.returncode}")
        sys.exit(1)

    print(f"\nRLAMA collection '{RAG_NAME}' built successfully.")


def report_stats():
    """Print summary statistics."""
    print("\n=== Summary ===")
    page_count = len(list(PAGES_DIR.glob("*.md"))) if PAGES_DIR.exists() else 0
    dive_count = len(list(DEEP_DIVES_DIR.glob("*.md"))) if DEEP_DIVES_DIR.exists() else 0
    total_size = sum(f.stat().st_size for f in STAGING_DIR.rglob("*.md")) if STAGING_DIR.exists() else 0
    print(f"  Pages:      {page_count}")
    print(f"  Deep-dives: {dive_count}")
    print(f"  Total:      {page_count + dive_count} files ({total_size / 1024:.0f} KB)")
    print(f"  Collection: {RAG_NAME}")
    print(f"\nQuery with: python3 {SKILL_DIR}/scripts/query.py \"your query\"")


def main():
    parser = argparse.ArgumentParser(description="Component Gallery ingestion pipeline")
    parser.add_argument("--full", action="store_true", help="Full crawl + deep-dives + RLAMA build")
    parser.add_argument("--rebuild-rag", action="store_true", help="Rebuild RLAMA from existing .staging/")
    parser.add_argument("--skip-rlama", action="store_true", help="Crawl + deep-dives, skip RLAMA build")
    parser.add_argument("--deep-dives", action="store_true", help="Fetch GitHub deep-dives only")
    args = parser.parse_args()

    if not any([args.full, args.rebuild_rag, args.skip_rlama, args.deep_dives]):
        args.full = True

    if args.full:
        crawl_site()
        fetch_deep_dives()
        build_rlama_collection()
        report_stats()
    elif args.rebuild_rag:
        build_rlama_collection()
        report_stats()
    elif args.skip_rlama:
        crawl_site()
        fetch_deep_dives()
        report_stats()
    elif args.deep_dives:
        fetch_deep_dives()
        report_stats()


if __name__ == "__main__":
    main()
