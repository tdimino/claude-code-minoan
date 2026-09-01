#!/usr/bin/env python3
"""
Component Gallery ingestion pipeline — transactional refresh.

Crawls component.gallery, fetches deep-dive content from GitHub,
copies curated pattern references, validates, builds an RLAMA RAG
collection, and atomically swaps staging directories.

Usage:
    python3 ingest.py --full                   # Full crawl + deep-dives + RLAMA build
    python3 ingest.py --rebuild-rag            # Rebuild RLAMA from existing .staging/
    python3 ingest.py --skip-rlama             # Crawl + deep-dives, skip RLAMA build
    python3 ingest.py --deep-dives             # Fetch GitHub deep-dives only
    python3 ingest.py --skip-crawl --skip-rag  # Dry-run: staging swap, meta, discovery
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

SKILL_DIR = Path(__file__).resolve().parent.parent
STAGING_DIR = SKILL_DIR / ".staging"
STAGING_NEXT_DIR = SKILL_DIR / ".staging-next"
STAGING_PREV_DIR = SKILL_DIR / ".staging-prev"
REFERENCES_DIR = SKILL_DIR / "references"

RAG_NAME = "component-gallery"
CRAWL_LIMIT = 120
CRAWL_URL = "https://component.gallery/"
GITHUB_REPO = "inbn/component-gallery"
GITHUB_CONTENT_PATH = "src/content/componentContent"
GITHUB_RAW_BASE = (
    f"https://raw.githubusercontent.com/{GITHUB_REPO}/"
    f"main/{GITHUB_CONTENT_PATH}"
)

CURATED_FILES = [
    "astryx-hero-pattern.md",
    "fluid-dom-pattern.md",
    "composio-glitch-hero-pattern.md",
    "composio-agent-console-pattern.md",
    "ai-components.md",
    "composite-patterns.md",
    "mesh3d-gallery.md",
]

REQUIRED_STAGING_FILES = ["components.md", "design-systems.md"]


def pages_dir(base: Path) -> Path:
    return base / "pages"


def deep_dives_dir(base: Path) -> Path:
    return base / "deep-dives"


def curated_dir(base: Path) -> Path:
    return base / "curated"


def crawl_output_path(base: Path) -> Path:
    return base / "crawl-output.json"


def crawl_meta_path(base: Path) -> Path:
    return base / "crawl-meta.json"


# --- Phase A: Crawl ---

def crawl_site(target: Path):
    """Crawl component.gallery with firecrawl into target directory."""
    print("=== Phase A: Crawling component.gallery with Firecrawl ===")
    pdir = pages_dir(target)
    pdir.mkdir(parents=True, exist_ok=True)

    output = crawl_output_path(target)
    cmd = [
        "firecrawl", "crawl", CRAWL_URL,
        "--wait", "--progress",
        "--limit", str(CRAWL_LIMIT),
        "--include-paths", "/components/,/design-systems,/about",
        "-o", str(output),
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"ERROR: firecrawl crawl failed with code {result.returncode}")
        sys.exit(1)

    split_crawl_output(target)


def split_crawl_output(target: Path):
    """Split the firecrawl JSON blob into per-page markdown files."""
    print("\nSplitting crawl output into per-page files...")

    output = crawl_output_path(target)
    if not output.exists():
        print(f"ERROR: {output} not found. Run --full first.")
        sys.exit(1)

    with open(output) as f:
        data = json.load(f)

    raw_pages = data if isinstance(data, list) else data.get("data", [])
    today = datetime.now().strftime("%Y-%m-%d")
    written = 0

    pdir = pages_dir(target)
    pdir.mkdir(parents=True, exist_ok=True)

    for page in raw_pages:
        meta = page.get("metadata", {})
        url = meta.get("url") or meta.get("sourceURL", "") or page.get("url", "")
        markdown = page.get("markdown", "")
        title = meta.get("title", "") or page.get("title", "")

        if not markdown or not url:
            continue

        path = urlparse(url).path.strip("/")
        if not path:
            filename = "index.md"
        else:
            filename = path.replace("/", "-") + ".md"

        content = f"---\nurl: {url}\ntitle: \"{title}\"\nscraped_date: {today}\n---\n\n{markdown}"

        filepath = pdir / filename
        filepath.write_text(content)
        written += 1

    print(f"Wrote {written} page files to {pdir}")
    return written


# --- Phase B: Deep-dives (auto-discovered from GitHub) ---

def discover_deep_dive_files() -> tuple[list[str], str, str]:
    """Auto-discover deep-dive markdown files from the GitHub repo tree.
    Returns (file_list, commit_sha, fetched_at).
    """
    print("\nDiscovering deep-dive files from GitHub API...")
    tree_url = f"https://api.github.com/repos/{GITHUB_REPO}/git/trees/main?recursive=1"
    req = urllib.request.Request(tree_url, headers={"User-Agent": "component-gallery-skill/1.0"})

    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.load(resp)

    tree_sha = data.get("sha", "")
    fetched_at = datetime.now(timezone.utc).isoformat()

    files = sorted(
        t["path"].split("/")[-1]
        for t in data["tree"]
        if t["path"].startswith(f"{GITHUB_CONTENT_PATH}/")
        and t["type"] == "blob"
        and t["path"].endswith(".md")
    )

    # Resolve commit SHA via refs API
    commit_sha = resolve_commit_sha()

    print(f"  Found {len(files)} deep-dive files (commit {commit_sha[:10]})")
    return files, commit_sha, fetched_at


def resolve_commit_sha() -> str:
    """Get the current main branch commit SHA."""
    url = f"https://api.github.com/repos/{GITHUB_REPO}/commits/main"
    req = urllib.request.Request(url, headers={"User-Agent": "component-gallery-skill/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
        return data["sha"]
    except Exception:
        return "unknown"


def fetch_deep_dives(target: Path, skip_network: bool = False) -> dict:
    """Fetch deep-dive markdown files from GitHub.
    Returns provenance dict with per-file SHA + timestamp.
    """
    print("\n=== Phase B: Fetching deep-dive content from GitHub ===")
    ddir = deep_dives_dir(target)
    ddir.mkdir(parents=True, exist_ok=True)

    if skip_network:
        print("  --skip-crawl: using discovery only (no file fetch)")
        files, commit_sha, fetched_at = discover_deep_dive_files()
        return {
            "commit_sha": commit_sha,
            "fetched_at": fetched_at,
            "files": {f: {"status": "skipped"} for f in files},
        }

    files, commit_sha, fetched_at = discover_deep_dive_files()

    provenance = {"commit_sha": commit_sha, "fetched_at": fetched_at, "files": {}}
    fetched = 0
    for filename in files:
        url = f"{GITHUB_RAW_BASE}/{filename}"
        filepath = ddir / filename

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "component-gallery-skill/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8")
                filepath.write_text(content)
                fetched += 1
                provenance["files"][filename] = {
                    "bytes": len(content),
                    "status": "ok",
                }
                print(f"  Fetched {filename} ({len(content)} bytes)")
        except Exception as e:
            provenance["files"][filename] = {"status": f"error: {e}"}
            print(f"  WARNING: Failed to fetch {filename}: {e}")

        time.sleep(0.3)

    print(f"Fetched {fetched}/{len(files)} deep-dive files to {ddir}")
    return provenance


# --- Phase C: Curated patterns ---

def copy_curated_patterns(target: Path):
    """Copy curated pattern references into staging for RAG inclusion."""
    print("\n=== Phase C: Copying curated pattern references ===")
    cdir = curated_dir(target)
    cdir.mkdir(parents=True, exist_ok=True)

    copied = 0
    for filename in CURATED_FILES:
        src = REFERENCES_DIR / filename
        if not src.exists():
            print(f"  WARNING: {src} not found, skipping")
            continue
        dst = cdir / filename
        shutil.copy2(src, dst)
        copied += 1
        print(f"  Copied {filename}")

    print(f"Copied {copied}/{len(CURATED_FILES)} curated files to {cdir}")


# --- Phase D: Validate ---

def validate_staging(target: Path, prev: Path | None = None) -> bool:
    """Validate the staging snapshot before proceeding to RAG build.
    Checks: page count sanity vs previous, required files, frontmatter parsing.
    """
    print("\n=== Phase D: Validating staging snapshot ===")
    pdir = pages_dir(target)
    ok = True

    if not pdir.exists():
        print("ERROR: pages/ directory missing")
        return False

    page_files = list(pdir.glob("*.md"))
    page_count = len(page_files)
    print(f"  Page count: {page_count}")

    if page_count < 10:
        print(f"ERROR: Only {page_count} pages — crawl likely failed")
        return False

    # Sanity check vs previous
    if prev and pages_dir(prev).exists():
        prev_count = len(list(pages_dir(prev).glob("*.md")))
        if prev_count > 0:
            ratio = page_count / prev_count
            print(f"  Previous page count: {prev_count} (ratio: {ratio:.2f})")
            if ratio < 0.5:
                print(f"ERROR: Page count dropped >50% ({prev_count} → {page_count})")
                return False

    # Check for expected page types
    filenames = {f.name for f in page_files}
    has_components = any("components-" in n for n in filenames)
    has_design = any("design-systems" in n for n in filenames)
    if not has_components:
        print("WARNING: No components-*.md pages found")
        ok = False
    if not has_design:
        print("WARNING: No design-systems*.md pages found")
        ok = False

    # Validate frontmatter on a sample
    errors = 0
    for page_file in page_files[:20]:
        content = page_file.read_text()
        if not content.startswith("---"):
            print(f"  WARNING: {page_file.name} missing frontmatter")
            errors += 1
            continue
        parts = content.split("---", 2)
        if len(parts) < 3:
            print(f"  WARNING: {page_file.name} malformed frontmatter")
            errors += 1

    if errors > 5:
        print(f"ERROR: {errors} pages with broken frontmatter")
        ok = False

    # Check deep-dives exist
    ddir = deep_dives_dir(target)
    if ddir.exists():
        dd_count = len(list(ddir.glob("*.md")))
        print(f"  Deep-dive count: {dd_count}")
    else:
        print("  WARNING: deep-dives/ directory missing")

    # Check curated
    cdir = curated_dir(target)
    if cdir.exists():
        cu_count = len(list(cdir.glob("*.md")))
        print(f"  Curated count: {cu_count}")
    else:
        print("  WARNING: curated/ directory missing")

    if ok:
        print("  Validation passed")
    else:
        print("  Validation completed with warnings")

    return ok


# --- Phase E: Provenance ---

def write_crawl_meta(target: Path, page_count: int, deep_dive_provenance: dict):
    """Write crawl-meta.json with provenance data."""
    print("\n=== Phase E: Writing crawl-meta.json ===")
    meta = {
        "crawl_timestamp": datetime.now(timezone.utc).isoformat(),
        "source_url": CRAWL_URL,
        "crawl_limit": CRAWL_LIMIT,
        "page_count": page_count,
        "deep_dives": deep_dive_provenance,
    }

    meta_path = crawl_meta_path(target)
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"  Wrote {meta_path}")
    return meta


# --- Phase F: Build RLAMA ---

def build_rlama_collection(source: Path):
    """Build the RLAMA RAG collection from staging files.
    Uses fixed chunking to avoid semantic fragmentation.
    RLAMA has no rename — we build under the real name after validation.
    The embedding step is the remaining failure window.
    """
    print("\n=== Phase F: Building RLAMA collection ===")

    md_files = list(source.rglob("*.md"))
    print(f"Found {len(md_files)} markdown files in {source}")

    if not md_files:
        print("ERROR: No markdown files found")
        sys.exit(1)

    print(f"Removing existing '{RAG_NAME}' collection (if any)...")
    subprocess.run(["rlama", "delete", "-f", RAG_NAME], capture_output=True)

    # Fixed chunking: semantic was fragmenting to ~112 char avg despite
    # chunk-size=1500. Fixed respects the size parameter literally.
    cmd = [
        "rlama", "rag", "qwen2.5:7b", RAG_NAME, str(source),
        "--chunking=fixed",
        "--chunk-size=1000",
        "--chunk-overlap=200",
        "--process-ext=.md",
    ]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=False)

    if result.returncode != 0:
        print(f"ERROR: rlama rag failed with code {result.returncode}")
        sys.exit(1)

    print(f"\nRLAMA collection '{RAG_NAME}' built successfully.")
    report_chunk_quality()


def report_chunk_quality():
    """Print chunk count + average length from the collection metadata."""
    info_path = Path.home() / ".rlama" / RAG_NAME / "info.json"
    if not info_path.exists():
        print("  (chunk stats unavailable — info.json not found)")
        return

    with open(info_path) as f:
        data = json.load(f)

    chunks = data.get("chunks", [])
    if not chunks:
        print("  (no chunks in collection)")
        return

    lengths = [len(c.get("content", "")) for c in chunks]
    avg = sum(lengths) / len(lengths)
    median = sorted(lengths)[len(lengths) // 2]
    under_200 = sum(1 for l in lengths if l < 200)

    print(f"\n  Chunk quality:")
    print(f"    Count:   {len(chunks)}")
    print(f"    Avg len: {avg:.0f} chars")
    print(f"    Median:  {median} chars")
    print(f"    Min/Max: {min(lengths)}/{max(lengths)} chars")
    print(f"    <200ch:  {under_200} ({100*under_200/len(chunks):.0f}%)")


# --- Phase G: Staging swap ---

def swap_staging(next_dir: Path, live_dir: Path, prev_dir: Path):
    """Atomically swap .staging-next → .staging, keeping .staging-prev backup.
    Deletes staged pages that no longer exist upstream.
    """
    print("\n=== Phase G: Swapping staging directories ===")

    if prev_dir.exists():
        print(f"  Removing old {prev_dir.name}/")
        shutil.rmtree(prev_dir)

    if live_dir.exists():
        print(f"  Moving {live_dir.name}/ → {prev_dir.name}/")
        live_dir.rename(prev_dir)

    print(f"  Moving {next_dir.name}/ → {live_dir.name}/")
    next_dir.rename(live_dir)

    print("  Staging swap complete")


# --- Phase H: Report ---

def report_stats(target: Path):
    """Print summary statistics."""
    print("\n=== Summary ===")
    pdir = pages_dir(target)
    ddir = deep_dives_dir(target)
    cdir = curated_dir(target)

    page_count = len(list(pdir.glob("*.md"))) if pdir.exists() else 0
    dive_count = len(list(ddir.glob("*.md"))) if ddir.exists() else 0
    curated_count = len(list(cdir.glob("*.md"))) if cdir.exists() else 0
    total_size = sum(f.stat().st_size for f in target.rglob("*.md")) if target.exists() else 0

    print(f"  Pages:      {page_count}")
    print(f"  Deep-dives: {dive_count}")
    print(f"  Curated:    {curated_count}")
    print(f"  Total:      {page_count + dive_count + curated_count} files ({total_size / 1024:.0f} KB)")
    print(f"  Collection: {RAG_NAME}")

    meta_path = crawl_meta_path(target)
    if meta_path.exists():
        print(f"  Provenance: {meta_path}")

    print(f"\nQuery with: python3 {SKILL_DIR}/scripts/query.py \"your query\"")


def main():
    parser = argparse.ArgumentParser(description="Component Gallery ingestion pipeline")
    parser.add_argument("--full", action="store_true", help="Full crawl + deep-dives + RLAMA build")
    parser.add_argument("--rebuild-rag", action="store_true", help="Rebuild RLAMA from existing .staging/")
    parser.add_argument("--skip-rlama", action="store_true", help="Crawl + deep-dives, skip RLAMA build")
    parser.add_argument("--deep-dives", action="store_true", help="Fetch GitHub deep-dives only into .staging/")
    parser.add_argument("--skip-crawl", action="store_true", help="Skip Firecrawl crawl (dry-run the rest)")
    parser.add_argument("--skip-rag", action="store_true", help="Skip RLAMA build (dry-run staging + meta)")
    args = parser.parse_args()

    # Default to --full if no flags
    if not any([args.full, args.rebuild_rag, args.skip_rlama, args.deep_dives,
                args.skip_crawl, args.skip_rag]):
        args.full = True

    # --skip-crawl --skip-rag: dry-run mode (staging swap, meta, deep-dive discovery)
    if args.skip_crawl and args.skip_rag:
        run_dry(args)
        return

    if args.full or args.skip_rlama:
        run_full(args)
    elif args.rebuild_rag:
        run_rebuild_rag()
    elif args.deep_dives:
        run_deep_dives_only()
    elif args.skip_crawl:
        run_full(args)
    elif args.skip_rag:
        run_full(args)


def run_full(args):
    """Full transactional pipeline: crawl → validate → build → swap."""
    target = STAGING_NEXT_DIR
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    # Phase A: Crawl
    if not args.skip_crawl:
        crawl_site(target)
    else:
        # Copy existing pages into next
        if pages_dir(STAGING_DIR).exists():
            print("=== Phase A: Copying existing pages (--skip-crawl) ===")
            shutil.copytree(pages_dir(STAGING_DIR), pages_dir(target))
            co = crawl_output_path(STAGING_DIR)
            if co.exists():
                shutil.copy2(co, crawl_output_path(target))

    # Phase B: Deep-dives
    dd_prov = fetch_deep_dives(target, skip_network=False)

    # Phase C: Curated patterns
    copy_curated_patterns(target)

    # Phase D: Validate
    prev = STAGING_DIR if STAGING_DIR.exists() else None
    if not validate_staging(target, prev):
        print("\nERROR: Validation failed. Aborting — .staging-next/ preserved for inspection.")
        sys.exit(1)

    # Phase E: Provenance
    page_count = len(list(pages_dir(target).glob("*.md")))
    write_crawl_meta(target, page_count, dd_prov)

    # Phase F: Build RLAMA (under real name, after validation)
    skip_rag = getattr(args, "skip_rag", False) or getattr(args, "skip_rlama", False)
    if not skip_rag:
        build_rlama_collection(target)

    # Phase G: Swap
    swap_staging(target, STAGING_DIR, STAGING_PREV_DIR)

    # Phase H: Report
    report_stats(STAGING_DIR)


def run_dry(args):
    """Dry-run: deep-dive discovery, curated copy, validation, meta — no crawl or RAG."""
    print("=== DRY RUN: --skip-crawl --skip-rag ===\n")
    target = STAGING_NEXT_DIR
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    # Copy existing pages into next
    if pages_dir(STAGING_DIR).exists():
        print("Copying existing pages from .staging/...")
        shutil.copytree(pages_dir(STAGING_DIR), pages_dir(target))
        co = crawl_output_path(STAGING_DIR)
        if co.exists():
            shutil.copy2(co, crawl_output_path(target))
    else:
        print("WARNING: No existing .staging/pages/ to copy")
        pages_dir(target).mkdir(parents=True)

    # Deep-dives: discover only (skip fetch for dry-run)
    dd_prov = fetch_deep_dives(target, skip_network=True)

    # Curated patterns
    copy_curated_patterns(target)

    # Validate
    prev = STAGING_DIR if STAGING_DIR.exists() else None
    validate_staging(target, prev)

    # Provenance
    page_count = len(list(pages_dir(target).glob("*.md")))
    write_crawl_meta(target, page_count, dd_prov)

    # Swap
    swap_staging(target, STAGING_DIR, STAGING_PREV_DIR)

    # Report
    report_stats(STAGING_DIR)


def run_rebuild_rag():
    """Rebuild RLAMA from existing .staging/ without re-crawling."""
    if not STAGING_DIR.exists():
        print("ERROR: .staging/ not found. Run --full first.")
        sys.exit(1)
    build_rlama_collection(STAGING_DIR)
    report_stats(STAGING_DIR)


def run_deep_dives_only():
    """Fetch deep-dives into existing .staging/ directory."""
    if not STAGING_DIR.exists():
        STAGING_DIR.mkdir(parents=True)
    dd_prov = fetch_deep_dives(STAGING_DIR, skip_network=False)
    page_count = len(list(pages_dir(STAGING_DIR).glob("*.md"))) if pages_dir(STAGING_DIR).exists() else 0
    write_crawl_meta(STAGING_DIR, page_count, dd_prov)
    report_stats(STAGING_DIR)


if __name__ == "__main__":
    main()
