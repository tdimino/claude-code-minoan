#!/usr/bin/env python3
"""Combine multiple images into a sprite sheet with optional atlas metadata.

Supports horizontal strips, NxM grids, and generates JSON or XML atlas files
compatible with Phaser, Unity, and Godot.

Usage:
  python3 stitch_spritesheet.py --input-dir frames/ --cols 8 --atlas json -o sheet.png
  python3 stitch_spritesheet.py --inputs f1.png f2.png f3.png --layout strip -o strip.png
  python3 stitch_spritesheet.py --input-dir frames/ --cell-size 64x64 --padding 2 --atlas xml
"""

import argparse
import json
import math
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow required: uv pip install Pillow", file=sys.stderr)
    sys.exit(1)


def collect_frames(inputs: list, input_dir: str) -> list:
    if inputs:
        return [Path(f) for f in inputs]
    if input_dir:
        d = Path(input_dir)
        exts = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}
        return sorted(f for f in d.iterdir() if f.suffix.lower() in exts)
    return []


def parse_size(s: str) -> tuple:
    parts = s.lower().split("x")
    return int(parts[0]), int(parts[1])


def stitch(frames: list, cols: int, rows: int, cell_w: int, cell_h: int,
           padding: int) -> Image.Image:
    sheet_w = cols * cell_w + padding * (cols - 1)
    sheet_h = rows * cell_h + padding * (rows - 1)
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (0, 0, 0, 0))

    for i, frame_path in enumerate(frames):
        r, c = divmod(i, cols)
        if r >= rows:
            break
        img = Image.open(frame_path).convert("RGBA")
        # Center in cell
        if img.width == 0 or img.height == 0:
            continue
        rw = min(cell_w / img.width, cell_h / img.height)
        new_w, new_h = int(img.width * rw), int(img.height * rw)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        x = c * (cell_w + padding) + (cell_w - new_w) // 2
        y = r * (cell_h + padding) + (cell_h - new_h) // 2
        sheet.paste(img, (x, y), img)

    return sheet


def write_json_atlas(frames: list, cols: int, cell_w: int, cell_h: int,
                     padding: int, sheet_w: int, sheet_h: int, output: str):
    atlas = {"frames": {}, "meta": {
        "image": Path(output).name,
        "size": {"w": sheet_w, "h": sheet_h},
        "format": "RGBA8888",
        "scale": 1
    }}
    for i in range(len(frames)):
        r, c = divmod(i, cols)
        x = c * (cell_w + padding)
        y = r * (cell_h + padding)
        atlas["frames"][f"frame_{i:03d}"] = {"x": x, "y": y, "w": cell_w, "h": cell_h}

    atlas_path = Path(output).with_suffix(".json")
    with open(atlas_path, "w") as f:
        json.dump(atlas, f, indent=2)
    return atlas_path


def write_xml_atlas(frames: list, cols: int, cell_w: int, cell_h: int,
                    padding: int, output: str):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             f'<TextureAtlas imagePath="{Path(output).name}">']
    for i in range(len(frames)):
        r, c = divmod(i, cols)
        x = c * (cell_w + padding)
        y = r * (cell_h + padding)
        lines.append(f'  <SubTexture name="frame_{i:03d}" x="{x}" y="{y}" '
                     f'width="{cell_w}" height="{cell_h}"/>')
    lines.append("</TextureAtlas>")
    atlas_path = Path(output).with_suffix(".xml")
    atlas_path.write_text("\n".join(lines))
    return atlas_path


def main():
    parser = argparse.ArgumentParser(description="Stitch images into a sprite sheet")
    parser.add_argument("--inputs", nargs="+", help="Frame image files")
    parser.add_argument("--input-dir", help="Directory of frame images (sorted)")
    parser.add_argument("--cols", type=int, help="Columns (default: auto)")
    parser.add_argument("--rows", type=int, help="Rows (default: auto)")
    parser.add_argument("--layout", choices=["strip", "grid"], help="Layout mode")
    parser.add_argument("--cell-size", help="Cell size WxH (default: largest frame)")
    parser.add_argument("--padding", type=int, default=0, help="Pixels between frames")
    parser.add_argument("-o", "--output", default="spritesheet.png", help="Output file")
    parser.add_argument("--atlas", choices=["json", "xml", "none"], default="json",
                        help="Atlas metadata format")
    args = parser.parse_args()

    frames = collect_frames(args.inputs, args.input_dir)
    if not frames:
        print("No frames found. Use --inputs or --input-dir.", file=sys.stderr)
        sys.exit(1)

    n = len(frames)

    # Determine cell size
    if args.cell_size:
        cell_w, cell_h = parse_size(args.cell_size)
    else:
        max_w, max_h = 0, 0
        for f in frames:
            img = Image.open(f)
            max_w = max(max_w, img.width)
            max_h = max(max_h, img.height)
        cell_w, cell_h = max_w, max_h

    # Determine layout: explicit --cols/--rows take priority, then --layout, then auto
    if args.cols:
        cols = args.cols
        rows = args.rows or math.ceil(n / cols)
    elif args.rows:
        rows = args.rows
        cols = math.ceil(n / rows)
    elif args.layout == "strip" or (args.layout is None and n <= 8):
        cols = n
        rows = 1
    else:
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)

    sheet = stitch(frames, cols, rows, cell_w, cell_h, args.padding)
    sheet.save(args.output)

    atlas_path = None
    if args.atlas == "json":
        atlas_path = write_json_atlas(frames, cols, cell_w, cell_h, args.padding,
                                      sheet.width, sheet.height, args.output)
    elif args.atlas == "xml":
        atlas_path = write_xml_atlas(frames, cols, cell_w, cell_h, args.padding,
                                     args.output)

    atlas_msg = f", atlas: {atlas_path}" if atlas_path else ""
    print(f"Stitched {n} frames → {cols}x{rows} grid ({sheet.width}x{sheet.height}){atlas_msg}")


if __name__ == "__main__":
    main()
