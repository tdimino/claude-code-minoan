#!/usr/bin/env python3
"""Smart crop with gravity modes.

Crops an image to a target size using different gravity strategies.

Usage:
    python smart_crop.py <image> --target 800x600
    python smart_crop.py <image> --target 800x600 --gravity center
    python smart_crop.py <image> --target 800x600 --gravity north
    python smart_crop.py <image> --target 800x600 --output cropped/
    python smart_crop.py <image> --target 800x600 --dry-run

Gravity modes:
    center      Standard center crop (default)
    north       Top-aligned crop
    south       Bottom-aligned crop
    east        Right-aligned crop
    west        Left-aligned crop
    northwest   Top-left crop
    northeast   Top-right crop
    southwest   Bottom-left crop
    southeast   Bottom-right crop
"""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys


GRAVITIES = [
    "center", "north", "south", "east", "west",
    "northwest", "northeast", "southwest", "southeast",
]


def parse_dimensions(dim_str: str) -> tuple[int, int]:
    """Parse WxH string into (width, height)."""
    match = re.match(r"(\d+)x(\d+)", dim_str.lower())
    if not match:
        raise ValueError(f"Invalid dimensions: {dim_str}. Use WxH format (e.g., 800x600)")
    return int(match.group(1)), int(match.group(2))


def get_image_dimensions(path: str) -> tuple[int, int]:
    """Get image width and height."""
    result = subprocess.run(
        ["magick", "identify", "-format", "%wx%h", f"{path}[0]"],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        raise RuntimeError(f"Cannot read image: {result.stderr.strip()}")
    w, h = result.stdout.strip().split("x")
    return int(w), int(h)


def build_crop_command(
    input_path: str,
    output_path: str,
    target_w: int,
    target_h: int,
    gravity: str = "center",
) -> list[str]:
    """Build a magick command to fill-crop to target dimensions."""
    # Strategy: resize to fill (^), then crop to exact size
    cmd = [
        "magick", input_path,
        "-resize", f"{target_w}x{target_h}^",
        "-gravity", gravity.capitalize() if gravity.lower() != "center" else "Center",
        "-extent", f"{target_w}x{target_h}",
        output_path,
    ]
    # Fix multi-word gravities
    for i, arg in enumerate(cmd):
        if arg in ("-gravity",) and i + 1 < len(cmd):
            g = cmd[i + 1].lower()
            gravity_map = {
                "center": "Center", "north": "North", "south": "South",
                "east": "East", "west": "West",
                "northwest": "NorthWest", "northeast": "NorthEast",
                "southwest": "SouthWest", "southeast": "SouthEast",
            }
            if g in gravity_map:
                cmd[i + 1] = gravity_map[g]
    return cmd


def main():
    parser = argparse.ArgumentParser(description="Smart crop with gravity modes")
    parser.add_argument("image", help="Input image path")
    parser.add_argument("--target", required=True,
                        help="Target dimensions as WxH (e.g., 800x600)")
    parser.add_argument("--gravity", default="center",
                        choices=GRAVITIES,
                        help="Crop gravity (default: center)")
    parser.add_argument("--output", default=None,
                        help="Output path or directory")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print command without executing")
    args = parser.parse_args()

    if not os.path.isfile(args.image):
        print(f"File not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    target_w, target_h = parse_dimensions(args.target)

    # Determine output path
    if args.output:
        if os.path.isdir(args.output) or args.output.endswith("/"):
            os.makedirs(args.output, exist_ok=True)
            base = os.path.basename(args.image)
            name, ext = os.path.splitext(base)
            output_path = os.path.join(args.output, f"{name}_crop{ext}")
        else:
            output_dir = os.path.dirname(args.output)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            output_path = args.output
    else:
        name, ext = os.path.splitext(args.image)
        output_path = f"{name}_crop_{target_w}x{target_h}{ext}"

    # Get source dimensions for info
    src_w, src_h = get_image_dimensions(args.image)

    cmd = build_crop_command(args.image, output_path, target_w, target_h, args.gravity)

    if args.dry_run:
        print(shlex.join(cmd))
        sys.exit(0)

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"magick failed: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps({
        "status": "ok",
        "input": os.path.abspath(args.image),
        "output": os.path.abspath(output_path),
        "source_dimensions": f"{src_w}x{src_h}",
        "target_dimensions": f"{target_w}x{target_h}",
        "gravity": args.gravity,
        "command": shlex.join(cmd),
    }, indent=2))


if __name__ == "__main__":
    main()
