#!/usr/bin/env python3
"""Batch rename unrenamed CleanShot/macOS screenshots using vision API.

Scans a directory for files matching CleanShot/macOS screenshot patterns
and renames them using the same vision provider as the watcher daemon.

Usage:
    python3 batch-rename.py                          # dry-run, current WATCH_DIR parent
    python3 batch-rename.py --execute                # actually rename
    python3 batch-rename.py --dir ~/Desktop/folder   # custom directory
    python3 batch-rename.py --provider gemini-flash   # specific provider
    python3 batch-rename.py --concurrency 5          # parallel API calls
"""

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Add script dir to path so we can import from watcher
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

# Load .env from script directory
env_path = SCRIPT_DIR / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

from watcher import (
    parse_screenshot,
    preprocess_image,
    slugify,
    get_provider,
    normalize,
    resolve_collision,
    append_index,
    PROVIDERS,
    IMAGE_EXTS,
    VIDEO_EXTS,
    WATCH_DIR,
    count_index_entries,
)


def find_unrenamed(directory: Path) -> list[Path]:
    """Find all files matching CleanShot/macOS screenshot patterns."""
    results = []
    for f in sorted(directory.iterdir()):
        if f.is_file() and parse_screenshot(f.name):
            results.append(f)
    return results


def rename_one(path: Path, provider, dest_dir: Path, dry_run: bool) -> dict:
    """Rename a single screenshot. Returns result dict."""
    info = parse_screenshot(path.name)
    if not info:
        return {"file": path.name, "status": "skip", "reason": "not a screenshot"}

    date_str = info["date"]
    retina = info["retina"]
    ext = f".{info['ext']}"
    original_name = path.name

    if ext in VIDEO_EXTS:
        slug = "screen-recording" if ext == ".mp4" else "animation"
        description = slug
    elif ext in IMAGE_EXTS:
        try:
            image_bytes = preprocess_image(path)
            raw_desc = provider.describe(image_bytes)
            slug = slugify(raw_desc)
            description = raw_desc
            if not slug:
                raise ValueError("Empty slug")
        except Exception as e:
            return {"file": original_name, "status": "error", "reason": str(e)}
    else:
        return {"file": original_name, "status": "skip", "reason": f"unsupported ext {ext}"}

    new_name = normalize(f"{date_str}-{slug}{retina}{ext}")

    if dry_run:
        return {
            "file": original_name,
            "status": "dry-run",
            "new_name": new_name,
            "description": description,
        }

    # Rename into dest_dir (usually the Screenshots subfolder)
    new_path = resolve_collision(dest_dir / new_name)
    new_name = new_path.name
    try:
        os.replace(str(path), str(new_path))
    except Exception as e:
        try:
            os.unlink(new_path)
        except OSError:
            pass
        return {"file": original_name, "status": "error", "reason": str(e)}

    # Update INDEX.md in dest_dir
    try:
        append_index(date_str, new_name, original_name, description)
    except Exception:
        pass

    return {
        "file": original_name,
        "status": "renamed",
        "new_name": new_name,
        "description": description,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Batch rename unrenamed screenshots using vision API"
    )
    parser.add_argument(
        "--dir", type=Path, default=WATCH_DIR.parent,
        help=f"Directory to scan (default: {WATCH_DIR.parent})",
    )
    parser.add_argument(
        "--dest", type=Path, default=WATCH_DIR,
        help=f"Destination for renamed files (default: {WATCH_DIR})",
    )
    parser.add_argument(
        "--in-place", action="store_true",
        help="Rename files in place (don't move to --dest)",
    )
    parser.add_argument(
        "--provider", default=None,
        help=f"Vision provider (default: from .env). Options: {list(PROVIDERS)}",
    )
    parser.add_argument(
        "--concurrency", type=int, default=3,
        help="Number of parallel API calls (default: 3)",
    )
    parser.add_argument(
        "--execute", action="store_true",
        help="Actually rename files (default: dry-run)",
    )
    args = parser.parse_args()

    scan_dir = args.dir.expanduser().resolve()
    dest_dir = scan_dir if args.in_place else args.dest.expanduser().resolve()

    if not scan_dir.is_dir():
        print(f"Error: {scan_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    dry_run = not args.execute

    # Find unrenamed files
    files = find_unrenamed(scan_dir)
    if not files:
        print("No unrenamed screenshots found.")
        return

    print(f"Found {len(files)} unrenamed screenshot(s) in {scan_dir}")
    if dry_run:
        print("DRY RUN — pass --execute to rename\n")
    else:
        dest_dir.mkdir(parents=True, exist_ok=True)
        print(f"Renaming to: {dest_dir}\n")

    # Init provider
    provider_name = args.provider or os.environ.get("PROVIDER", "openrouter")
    print(f"Provider: {provider_name}")
    try:
        provider = get_provider(provider_name)
    except Exception as e:
        print(f"Error initializing provider: {e}", file=sys.stderr)
        sys.exit(1)

    # Process files
    results = []
    succeeded = 0
    failed = 0
    start = time.time()

    if args.concurrency > 1 and not dry_run:
        with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
            futures = {
                pool.submit(rename_one, f, provider, dest_dir, dry_run): f
                for f in files
            }
            for future in as_completed(futures):
                r = future.result()
                results.append(r)
                _print_result(r)
                if r["status"] == "renamed":
                    succeeded += 1
                elif r["status"] == "error":
                    failed += 1
    else:
        for f in files:
            r = rename_one(f, provider, dest_dir, dry_run)
            results.append(r)
            _print_result(r)
            if r["status"] in ("renamed", "dry-run"):
                succeeded += 1
            elif r["status"] == "error":
                failed += 1

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.1f}s — {succeeded} renamed, {failed} failed, {len(files) - succeeded - failed} skipped")


def _print_result(r: dict):
    status = r["status"]
    if status in ("renamed", "dry-run"):
        tag = "RENAME" if status == "renamed" else "PREVIEW"
        print(f"  [{tag}] {r['file']}")
        print(f"       -> {r['new_name']}")
        print(f"          ({r['description']})")
    elif status == "error":
        print(f"  [ERROR] {r['file']}: {r['reason']}")
    elif status == "skip":
        print(f"  [SKIP]  {r['file']}: {r['reason']}")


if __name__ == "__main__":
    main()
