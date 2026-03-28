#!/usr/bin/env python3
"""Convert images to terminal-renderable ASCII or Unicode art.

Three modes: grayscale density ramp, color half-block Unicode, and jp2a passthrough.

Usage:
  python3 image_to_ascii.py photo.png --mode gray --width 80
  python3 image_to_ascii.py photo.png --mode color --width 120
  python3 image_to_ascii.py photo.png --mode jp2a --width 80
  python3 image_to_ascii.py photo.png --mode gray --charset blocks --invert
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow required: uv pip install Pillow", file=sys.stderr)
    sys.exit(1)

CHARSETS = {
    "standard": " .:-=+*#%@",
    "detailed": " .'`^\",:;Il!i><~+_-?][}{1)(|/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$",
    "blocks": " ░▒▓█",
}

ASPECT_RATIO = 0.55  # Terminal chars are ~2x taller than wide


def gray_mode(img: Image.Image, width: int, charset: str, invert: bool) -> str:
    chars = CHARSETS[charset]
    if invert:
        chars = chars[::-1]

    aspect = img.height / img.width
    new_h = int(width * aspect * ASPECT_RATIO)
    img = img.convert("L").resize((width, new_h), Image.LANCZOS)

    lines = []
    for y in range(new_h):
        row = []
        for x in range(width):
            brightness = img.getpixel((x, y))
            idx = int(brightness / 256 * len(chars))
            idx = min(idx, len(chars) - 1)
            row.append(chars[idx])
        lines.append("".join(row))
    return "\n".join(lines)


def color_mode(img: Image.Image, width: int) -> str:
    """Half-block Unicode: ▀ with fg=top pixel, bg=bottom pixel — 2 rows per output line."""
    aspect = img.height / img.width
    new_h = int(width * aspect * ASPECT_RATIO)
    # Height must be even for pair processing
    new_h = new_h + (new_h % 2)

    img = img.convert("RGB").resize((width, new_h), Image.LANCZOS)

    lines = []
    for y in range(0, new_h, 2):
        row = []
        for x in range(width):
            r1, g1, b1 = img.getpixel((x, y))
            if y + 1 < new_h:
                r2, g2, b2 = img.getpixel((x, y + 1))
            else:
                r2, g2, b2 = 0, 0, 0
            # fg = top pixel, bg = bottom pixel, char = upper half block
            row.append(f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m▀")
        row.append("\033[0m")
        lines.append("".join(row))
    return "\n".join(lines)


def jp2a_mode(image_path: str, width: int, invert: bool) -> str:
    if not shutil.which("jp2a"):
        print("jp2a not found. Install with: brew install jp2a", file=sys.stderr)
        sys.exit(1)
    cmd = ["jp2a", f"--width={width}", image_path]
    if invert:
        cmd.append("--invert")
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description="Convert images to ASCII/Unicode art")
    parser.add_argument("image", help="Input image path")
    parser.add_argument("--mode", choices=["gray", "color", "jp2a"], default="gray",
                        help="Rendering mode (default: gray)")
    parser.add_argument("--width", type=int, default=80, help="Output width in characters")
    parser.add_argument("--invert", action="store_true", help="Invert brightness mapping")
    parser.add_argument("--charset", choices=["standard", "detailed", "blocks"], default="standard",
                        help="Character set for gray mode")
    parser.add_argument("--output", help="Save to file instead of stdout")
    args = parser.parse_args()

    if args.mode == "gray":
        img = Image.open(args.image)
        result = gray_mode(img, args.width, args.charset, args.invert)
    elif args.mode == "color":
        img = Image.open(args.image)
        result = color_mode(img, args.width)
    elif args.mode == "jp2a":
        result = jp2a_mode(args.image, args.width, args.invert).rstrip("\n")

    if args.output:
        Path(args.output).write_text(result)
        print(f"Saved to {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()
