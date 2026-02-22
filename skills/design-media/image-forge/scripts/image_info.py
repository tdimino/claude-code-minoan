#!/usr/bin/env python3
"""Report image metadata as clean JSON.

Wraps `magick identify -verbose` and parses into structured output.
Saves Claude from parsing raw identify output.

Usage:
    python image_info.py <image_path>
    python image_info.py <image_path> --json
    python image_info.py <image_path> --field width
    python image_info.py <image_path> --field dimensions
"""

import argparse
import json
import os
import re
import subprocess
import sys
from math import gcd


def get_image_info(path: str) -> dict:
    """Extract image metadata via magick identify."""
    if not os.path.isfile(path):
        return {"error": f"File not found: {path}"}

    # Get basic info via format string (fast, reliable)
    fmt = "%w|%h|%m|%z|%r|%b|%[channels]|%A|%x|%y|%[orientation]"
    try:
        result = subprocess.run(
            ["magick", "identify", "-format", fmt, path],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return {"error": f"magick identify failed: {result.stderr.strip()}"}
    except FileNotFoundError:
        return {"error": "ImageMagick not found. Install with: brew install imagemagick"}
    except subprocess.TimeoutExpired:
        return {"error": "magick identify timed out after 30s"}

    parts = result.stdout.strip().split("|")
    if len(parts) < 10:
        return {"error": f"Unexpected identify output: {result.stdout}"}

    width = int(parts[0])
    height = int(parts[1])
    fmt_name = parts[2]
    depth = int(parts[3])
    colorspace = parts[4]
    filesize = parts[5]
    channels = parts[6]
    has_alpha = parts[7].lower() in ("true", "blend")
    dpi_x = parts[8]
    dpi_y = parts[9]
    orientation = parts[10] if len(parts) > 10 else ""

    # Compute aspect ratio
    d = gcd(width, height)
    aspect_w, aspect_h = width // d, height // d
    # Simplify common ratios
    aspect_ratio = f"{aspect_w}:{aspect_h}"

    # Parse file size to KB
    file_size_bytes = os.path.getsize(path)
    file_size_kb = round(file_size_bytes / 1024, 1)

    info = {
        "path": os.path.abspath(path),
        "format": fmt_name,
        "width": width,
        "height": height,
        "dimensions": f"{width}x{height}",
        "aspect_ratio": aspect_ratio,
        "color_space": colorspace,
        "depth": depth,
        "channels": channels,
        "has_alpha": has_alpha,
        "file_size_kb": file_size_kb,
        "file_size_human": filesize.strip(),
        "dpi": f"{dpi_x}x{dpi_y}",
        "orientation": orientation if orientation else "Undefined",
    }

    # Try to get ICC profile
    try:
        icc_result = subprocess.run(
            ["magick", "identify", "-format", "%[icc:description]", path],
            capture_output=True, text=True, timeout=10
        )
        icc = icc_result.stdout.strip()
        if icc:
            info["icc_profile"] = icc
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # Try to get EXIF data (common fields)
    exif_fields = {
        "Make": "exif:Make",
        "Model": "exif:Model",
        "DateTime": "exif:DateTime",
        "ExposureTime": "exif:ExposureTime",
        "FNumber": "exif:FNumber",
        "ISOSpeedRatings": "exif:ISOSpeedRatings",
        "FocalLength": "exif:FocalLength",
        "GPSLatitude": "exif:GPSLatitude",
        "GPSLongitude": "exif:GPSLongitude",
    }
    exif_fmt = "|".join(f"%[{v}]" for v in exif_fields.values())
    try:
        exif_result = subprocess.run(
            ["magick", "identify", "-format", exif_fmt, path],
            capture_output=True, text=True, timeout=10
        )
        exif_parts = exif_result.stdout.strip().split("|")
        exif = {}
        for i, key in enumerate(exif_fields.keys()):
            if i < len(exif_parts) and exif_parts[i].strip():
                exif[key] = exif_parts[i].strip()
        if exif:
            info["exif"] = exif
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return info


def main():
    parser = argparse.ArgumentParser(description="Report image metadata as JSON")
    parser.add_argument("image", help="Path to image file")
    parser.add_argument("--field", type=str, default=None,
                        help="Output single field value (e.g., width, dimensions, format)")
    args = parser.parse_args()

    info = get_image_info(args.image)

    if "error" in info:
        print(json.dumps(info), file=sys.stderr)
        sys.exit(1)

    if args.field:
        value = info.get(args.field)
        if value is None:
            # Check nested exif
            if "exif" in info and args.field in info["exif"]:
                value = info["exif"][args.field]
            else:
                print(f"Unknown field: {args.field}", file=sys.stderr)
                sys.exit(1)
        print(value)
    else:
        print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
