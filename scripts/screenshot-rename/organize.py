#!/usr/bin/env python3
"""One-time migration: move and rename existing CleanShot screenshots.

Finds CleanShot files on ~/Desktop and ~/Desktop/Screencaps & Chats/,
moves them into the Screenshots/ subfolder, and renames them using the
vision provider.

Usage:
    python organize.py --dry-run              # Preview what would happen
    python organize.py --execute              # Actually move and rename
    python organize.py --execute --limit 5    # Process first 5 only
    python organize.py --execute --provider openai
"""

import argparse
import os
import sys
import time
from pathlib import Path

# Import from watcher
from watcher import (
    WATCH_DIR, parse_screenshot, process_file, get_provider,
    setup_logging, logger, SCRIPT_DIR, PROVIDERS,
)


def find_cleanshot_files() -> list[Path]:
    """Find CleanShot/Screenshot files across Desktop locations."""
    files = []
    search_dirs = [
        Path.home() / "Desktop",
        Path.home() / "Desktop" / "Screencaps & Chats",
    ]
    for d in search_dirs:
        if not d.exists():
            continue
        for path in sorted(d.iterdir()):
            if path.is_file() and parse_screenshot(path.name):
                files.append(path)
    return files


def main():
    parser = argparse.ArgumentParser(description="Migrate existing screenshots")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Preview only")
    group.add_argument("--execute", action="store_true", help="Actually move/rename")
    parser.add_argument("--limit", type=int, default=0, help="Max files to process")
    parser.add_argument("--provider", default=None,
                        help=f"Vision provider override. Options: {list(PROVIDERS)}")
    args = parser.parse_args()

    setup_logging()

    # Load .env
    from dotenv import load_dotenv
    env_path = SCRIPT_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    # Provider (only needed for --execute on images)
    provider = None
    if args.execute:
        provider_name = args.provider or os.environ.get("PROVIDER", "gemini-flash")
        try:
            provider = get_provider(provider_name)
            logger.info(f"Provider: {provider_name}")
        except Exception as e:
            logger.error(f"Failed to initialize provider: {e}")
            sys.exit(1)

    # Ensure target directory exists
    WATCH_DIR.mkdir(parents=True, exist_ok=True)

    # Find files
    files = find_cleanshot_files()
    if not files:
        print("No CleanShot/Screenshot files found to migrate.")
        return

    print(f"Found {len(files)} screenshot(s) to migrate:\n")

    processed = 0
    for path in files:
        if args.limit and processed >= args.limit:
            print(f"\nReached limit of {args.limit} files.")
            break

        # Target: move into Screenshots/ subfolder
        target = WATCH_DIR / path.name

        if args.dry_run:
            print(f"  MOVE  {path.name}")
            print(f"    -> {WATCH_DIR.name}/{path.name}")
            print(f"    -> (would rename via vision)")
            processed += 1
            continue

        # Move file
        if path.parent != WATCH_DIR:
            if target.exists():
                print(f"  SKIP  {path.name} (already exists in target)")
                continue
            os.replace(str(path), str(target))
            logger.info(f"Moved: {path} -> {target}")

        # Rename via vision provider
        if provider:
            success = process_file(target, provider)
            if success:
                processed += 1
            # Small delay between API calls
            time.sleep(0.5)

    print(f"\n{'Would process' if args.dry_run else 'Processed'} {processed} file(s).")


if __name__ == "__main__":
    main()
