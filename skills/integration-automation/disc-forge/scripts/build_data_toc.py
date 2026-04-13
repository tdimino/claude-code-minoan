#!/usr/bin/env python3
"""
build_data_toc.py — Build an ISO9660+Joliet hybrid image and a cdrdao data TOC.

Used for MP3 data CDs (readable by car stereos that support MP3 discs) instead
of Red Book audio CDs. Swaps in place of build_toc.py when the orchestrator
runs in --mp3-disc mode.

Outputs two files:
    --iso-output    the hybrid ISO (MP3 files live inside)
    --toc-output    the cdrdao TOC that references the ISO

Usage:
    build_data_toc.py --source-dir ~/burn-staging/mantras \\
                      --volume-label MANTRAS \\
                      --iso-output ~/burn-staging/mantras.iso \\
                      --toc-output ~/burn-staging/mantras.toc
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


def sanitize_volume_label(raw: str) -> str:
    """ISO9660 volume label: uppercase, A-Z/0-9/_ only, max 32 chars."""
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", raw).upper().strip("_")
    return (cleaned or "DATA")[:32]


def main() -> int:
    ap = argparse.ArgumentParser(description="Build ISO9660+Joliet hybrid + cdrdao data TOC")
    ap.add_argument("--source-dir", type=Path, required=True, help="Directory of files to burn")
    ap.add_argument("--volume-label", required=True, help="CD volume label (will be sanitized)")
    ap.add_argument("--iso-output", type=Path, required=True, help="Where to write the .iso")
    ap.add_argument("--toc-output", type=Path, required=True, help="Where to write the .toc")
    args = ap.parse_args()

    if not args.source_dir.is_dir():
        print(f"source dir not found: {args.source_dir}", file=sys.stderr)
        return 1

    label = sanitize_volume_label(args.volume_label)

    # Build hybrid ISO. -iso + -joliet gives ISO9660 Level 1 with Joliet extensions
    # for long filenames — readable by Windows, macOS, Linux, and car stereos.
    cmd = [
        "hdiutil", "makehybrid",
        "-iso", "-joliet",
        "-default-volume-name", label,
        "-o", str(args.iso_output),
        str(args.source_dir),
    ]
    print(f"building hybrid ISO: {args.iso_output} (label={label})")
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"hdiutil makehybrid failed (exit {r.returncode})", file=sys.stderr)
        return r.returncode

    # cdrdao data TOC: single MODE1 track pointing at the ISO.
    # DATAFILE path must be relative to the TOC or absolute. Use absolute.
    toc = (
        "CD_ROM\n"
        "\n"
        "TRACK MODE1\n"
        f'DATAFILE "{args.iso_output.resolve()}"\n'
    )
    args.toc_output.write_text(toc)
    print(f"wrote TOC: {args.toc_output}")

    # Validate the TOC — cdrdao show-toc will print track layout or error loudly.
    print("validating TOC:")
    v = subprocess.run(["cdrdao", "show-toc", str(args.toc_output)], capture_output=True, text=True)
    if v.returncode != 0:
        print(v.stderr, file=sys.stderr)
        return v.returncode
    # Print just the summary lines (TOC TYPE + track info), skip version chatter.
    for ln in v.stdout.splitlines():
        if ln.startswith("TOC TYPE") or ln.startswith("TRACK") or ln.strip().startswith(("START", "END", "COPY")):
            print(f"  {ln.strip()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
