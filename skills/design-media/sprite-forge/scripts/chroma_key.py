#!/usr/bin/env python3
"""Remove chroma key background from images.

Replaces pixels matching a key color (default #00FF00) with transparency.
Supports tolerance-based matching, green spill suppression, and edge feathering.

Usage:
  python3 chroma_key.py --input sprite.png --output sprite_alpha.png
  python3 chroma_key.py --input sprite.png --output out.png --color 00FF00 --tolerance 40 --despill
  python3 chroma_key.py --input sprite.png --output out.png --feather 2
"""

import argparse
import math
import sys

try:
    from PIL import Image, ImageFilter
except ImportError:
    print("Pillow required: uv pip install Pillow", file=sys.stderr)
    sys.exit(1)


def hex_to_rgb(hex_str: str) -> tuple:
    h = hex_str.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def color_distance(c1: tuple, c2: tuple) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(c1[:3], c2[:3])))


def remove_chroma(img: Image.Image, key_rgb: tuple, tolerance: int,
                   despill: bool, feather: int) -> tuple:
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size
    removed = 0
    soft_edge = tolerance * 1.5

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            dist = color_distance((r, g, b), key_rgb)

            if dist < tolerance:
                pixels[x, y] = (0, 0, 0, 0)
                removed += 1
            elif dist < soft_edge:
                # Linear falloff for semi-transparent edge
                alpha = int(255 * (dist - tolerance) / (soft_edge - tolerance))
                if despill:
                    g = min(g, max(r, b))
                pixels[x, y] = (r, g, b, min(a, alpha))
                removed += 1
            elif despill and g > max(r, b) * 1.2:
                # Suppress green spill on opaque edge pixels
                g_new = min(g, int(max(r, b) * 1.1))
                pixels[x, y] = (r, g_new, b, a)

    if feather > 0:
        # Extract alpha, blur, re-threshold
        alpha_band = img.split()[3]
        blurred = alpha_band.filter(ImageFilter.GaussianBlur(radius=feather))
        img.putalpha(blurred)

    return img, removed


def main():
    parser = argparse.ArgumentParser(description="Remove chroma key background from images")
    parser.add_argument("--input", required=True, help="Input image path")
    parser.add_argument("--output", required=True, help="Output image path")
    parser.add_argument("--color", default="00FF00", help="Key color hex (default: 00FF00)")
    parser.add_argument("--tolerance", type=int, default=30, help="Color distance tolerance (default: 30)")
    parser.add_argument("--despill", action="store_true", help="Reduce green spill on edges")
    parser.add_argument("--feather", type=int, default=1, help="Edge feather radius in pixels (default: 1)")
    args = parser.parse_args()

    key_rgb = hex_to_rgb(args.color)
    img = Image.open(args.input)
    total_pixels = img.size[0] * img.size[1]

    result, removed = remove_chroma(img, key_rgb, args.tolerance, args.despill, args.feather)
    result.save(args.output)

    pct = (removed / total_pixels) * 100
    print(f"Removed {removed} pixels ({pct:.1f}%), output saved to {args.output}")


if __name__ == "__main__":
    main()
