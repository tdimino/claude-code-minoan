#!/usr/bin/env python3
"""Build contact sheets and thumbnail grids.

Wraps `magick montage` with sane defaults.

Usage:
    python montage_builder.py *.jpg
    python montage_builder.py *.jpg --cols 4 --thumb 200x200
    python montage_builder.py *.jpg --cols 3 --thumb 300x300 --border 2 --label
    python montage_builder.py *.jpg --output contact_sheet.jpg
    python montage_builder.py *.jpg --background '#1a1a2e' --border-color '#333'
    python montage_builder.py *.jpg --dry-run
"""

import argparse
import glob
import json
import os
import shlex
import subprocess
import sys


def build_montage_command(
    files: list[str],
    output: str,
    cols: int = 4,
    thumb_w: int = 200,
    thumb_h: int = 200,
    gap: int = 5,
    border: int = 0,
    border_color: str = "#cccccc",
    background: str = "white",
    label: bool = False,
    font: str = "Helvetica",
    pointsize: int = 10,
    title: str = None,
    shadow: bool = False,
) -> list[str]:
    """Build a magick montage command."""
    cmd = ["magick", "montage"]

    if label:
        cmd += ["-label", "%f", "-font", font, "-pointsize", str(pointsize)]

    cmd += files
    cmd += ["-geometry", f"{thumb_w}x{thumb_h}+{gap}+{gap}"]
    cmd += ["-tile", f"{cols}x"]
    cmd += ["-background", background]

    if border > 0:
        cmd += ["-bordercolor", border_color, "-border", str(border)]

    if title:
        cmd += ["-title", title, "-font", font, "-pointsize", str(pointsize + 4)]

    if shadow:
        cmd += ["-shadow"]

    cmd.append(output)
    return cmd


def main():
    parser = argparse.ArgumentParser(description="Build contact sheets and thumbnail grids")
    parser.add_argument("files", nargs="+", help="Input image files (supports globs)")
    parser.add_argument("--cols", type=int, default=4, help="Number of columns (default: 4)")
    parser.add_argument("--thumb", default="200x200",
                        help="Thumbnail size as WxH (default: 200x200)")
    parser.add_argument("--gap", type=int, default=5,
                        help="Gap between thumbnails in pixels (default: 5)")
    parser.add_argument("--border", type=int, default=0,
                        help="Border width around each thumbnail (default: 0)")
    parser.add_argument("--border-color", default="#cccccc",
                        help="Border color (default: #cccccc)")
    parser.add_argument("--background", default="white",
                        help="Background color (default: white)")
    parser.add_argument("--label", action="store_true",
                        help="Add filename labels under thumbnails")
    parser.add_argument("--font", default="Helvetica",
                        help="Label font (default: Helvetica)")
    parser.add_argument("--pointsize", type=int, default=10,
                        help="Label font size (default: 10)")
    parser.add_argument("--title", default=None,
                        help="Title text above the montage")
    parser.add_argument("--shadow", action="store_true",
                        help="Add drop shadows to thumbnails")
    parser.add_argument("--output", default="montage.jpg",
                        help="Output file (default: montage.jpg)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print command without executing")
    args = parser.parse_args()

    # Expand globs
    files = []
    for pattern in args.files:
        expanded = sorted(glob.glob(pattern))
        if expanded:
            files.extend(expanded)
        elif os.path.isfile(pattern):
            files.append(pattern)

    if not files:
        print("No files matched", file=sys.stderr)
        sys.exit(1)

    # Parse thumbnail size
    try:
        parts = args.thumb.lower().split("x")
        thumb_w = int(parts[0])
        thumb_h = int(parts[1]) if len(parts) > 1 else thumb_w
    except (ValueError, IndexError):
        print(f"Invalid thumb size: {args.thumb}. Use WxH format.", file=sys.stderr)
        sys.exit(1)

    cmd = build_montage_command(
        files=files,
        output=args.output,
        cols=args.cols,
        thumb_w=thumb_w,
        thumb_h=thumb_h,
        gap=args.gap,
        border=args.border,
        border_color=args.border_color,
        background=args.background,
        label=args.label,
        font=args.font,
        pointsize=args.pointsize,
        title=args.title,
        shadow=args.shadow,
    )

    if args.dry_run:
        print(shlex.join(cmd))
        sys.exit(0)

    # Ensure output directory exists
    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"magick montage failed: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps({
        "status": "ok",
        "output": os.path.abspath(args.output),
        "files": len(files),
        "grid": f"{args.cols}x{-(-len(files) // args.cols)}",
        "thumb_size": f"{thumb_w}x{thumb_h}",
        "command": shlex.join(cmd),
    }, indent=2))


if __name__ == "__main__":
    main()
