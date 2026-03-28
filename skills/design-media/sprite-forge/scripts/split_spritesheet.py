#!/usr/bin/env python3
"""Split a sprite sheet PNG into individual frames with alpha preserved.

Handles horizontal strips (1 row) and NxM grids. Auto-detects frame count
from image dimensions when --cols is provided.

Usage:
  python3 split_spritesheet.py sheet.png --cols 6 --output frames/
  python3 split_spritesheet.py sheet.png --cols 4 --rows 2 --output frames/
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow required: uv pip install Pillow", file=sys.stderr)
    sys.exit(1)


def split_sheet(image_path: str, cols: int, rows: int = 1, output_dir: str = "frames") -> list:
    """Split sprite sheet into individual frame PNGs.

    Returns list of output file paths.
    """
    img = Image.open(image_path).convert("RGBA")
    w, h = img.size

    frame_w = w // cols
    frame_h = h // rows

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    paths = []
    idx = 0
    for row in range(rows):
        for col in range(cols):
            x0 = col * frame_w
            y0 = row * frame_h
            frame = img.crop((x0, y0, x0 + frame_w, y0 + frame_h))

            # Skip fully transparent frames
            if frame.getextrema()[3][1] == 0:
                continue

            path = out / f"frame_{idx:04d}.png"
            frame.save(path, "PNG")
            paths.append(str(path))
            idx += 1

    return paths


def auto_detect_rows(image_path: str, cols: int) -> int:
    """Guess row count from aspect ratio. If frame_w ≈ frame_h, it's a grid."""
    img = Image.open(image_path)
    w, h = img.size
    frame_w = w // cols
    # Estimate rows from height
    rows = max(1, round(h / frame_w))
    return rows


def main():
    parser = argparse.ArgumentParser(description="Split sprite sheet into individual frames")
    parser.add_argument("image", help="Sprite sheet PNG path")
    parser.add_argument("--cols", type=int, required=True, help="Number of columns in the grid")
    parser.add_argument("--rows", type=int, default=0, help="Number of rows (0 = auto-detect)")
    parser.add_argument("--output", "-o", default="frames", help="Output directory")

    args = parser.parse_args()

    rows = args.rows if args.rows > 0 else auto_detect_rows(args.image, args.cols)

    paths = split_sheet(args.image, args.cols, rows, args.output)
    print(f"Split into {len(paths)} frames in {args.output}/", file=sys.stderr)
    for p in paths:
        print(p)


if __name__ == "__main__":
    main()
