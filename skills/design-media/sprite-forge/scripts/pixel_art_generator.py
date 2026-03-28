#!/usr/bin/env python3
"""Convert an image to pixel-art SVG using only <rect> elements.

Pipeline:
  1. Load image (PNG/JPG/WebP)
  2. Resize to target grid (default 24x24)
  3. Quantize to N colors (default 6)
  4. Remove background color (optional)
  5. Generate SVG with one <rect> per pixel (or merged runs for optimization)
  6. Auto-label body part groups by position heuristics

Output: SVG string or file with named groups for animation targeting.

Usage:
  python3 pixel_art_generator.py input.png --grid 24 --colors 6 --output mascot.svg
  python3 pixel_art_generator.py input.png --grid 16 --merge --remove-bg
"""

import argparse
import json
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow required: uv pip install Pillow", file=sys.stderr)
    sys.exit(1)


def load_and_quantize(image_path: str, grid_size: int, num_colors: int) -> tuple:
    """Load image, resize to grid, quantize colors. Returns (pixel_grid, palette, width, height)."""
    img = Image.open(image_path).convert("RGBA")

    # Resize to grid using nearest-neighbor (preserves pixel edges)
    aspect = img.width / img.height
    if aspect >= 1:
        w = grid_size
        h = max(1, round(grid_size / aspect))
    else:
        h = grid_size
        w = max(1, round(grid_size * aspect))

    img_resized = img.resize((w, h), Image.NEAREST)

    # Separate alpha channel
    alpha = img_resized.split()[3]

    # Quantize RGB to N colors
    img_rgb = img_resized.convert("RGB")
    img_quantized = img_rgb.quantize(colors=num_colors, method=Image.Quantize.MEDIANCUT)
    palette_data = img_quantized.getpalette()[:num_colors * 3]

    # Build palette as hex strings
    palette = []
    for i in range(num_colors):
        r, g, b = palette_data[i*3], palette_data[i*3+1], palette_data[i*3+2]
        palette.append(f"#{r:02X}{g:02X}{b:02X}")

    # Build pixel grid with palette indices and alpha
    pixels = list(img_quantized.getdata())
    alpha_data = list(alpha.getdata())

    grid = []
    for y in range(h):
        row = []
        for x in range(w):
            idx = y * w + x
            a = alpha_data[idx]
            if a < 128:  # transparent
                row.append(None)
            else:
                color_idx = pixels[idx]
                if color_idx < num_colors:
                    row.append(color_idx)
                else:
                    row.append(None)
        grid.append(row)

    return grid, palette, w, h


def detect_bg_color(grid: list, palette: list) -> int | None:
    """Detect background color as most common color on edges."""
    if not grid or not grid[0]:
        return None

    h = len(grid)
    w = len(grid[0])
    edge_counts = {}

    for y in range(h):
        for x in range(w):
            if y == 0 or y == h-1 or x == 0 or x == w-1:
                c = grid[y][x]
                if c is not None:
                    edge_counts[c] = edge_counts.get(c, 0) + 1

    if not edge_counts:
        return None

    return max(edge_counts, key=edge_counts.get)


def remove_background(grid: list, bg_idx: int) -> list:
    """Set all pixels matching bg_idx to None."""
    return [
        [None if c == bg_idx else c for c in row]
        for row in grid
    ]


def merge_horizontal_runs(grid: list) -> list:
    """Merge adjacent same-color pixels into wider rects. Returns [(x, y, w, h, color_idx)]."""
    rects = []
    h = len(grid)
    if h == 0:
        return rects
    w = len(grid[0])

    for y in range(h):
        x = 0
        while x < w:
            c = grid[y][x]
            if c is None:
                x += 1
                continue
            # Find run length
            run = 1
            while x + run < w and grid[y][x + run] == c:
                run += 1
            rects.append((x, y, run, 1, c))
            x += run

    return rects


def single_pixel_rects(grid: list) -> list:
    """One rect per pixel. Returns [(x, y, 1, 1, color_idx)]."""
    rects = []
    for y, row in enumerate(grid):
        for x, c in enumerate(row):
            if c is not None:
                rects.append((x, y, 1, 1, c))
    return rects


def auto_label_groups(rects: list, grid_w: int, grid_h: int) -> dict:
    """Heuristic body-part grouping based on rect positions.

    Returns dict of group_name -> list of rect indices.
    Groups: head (top 30%), body (middle 40%), legs (bottom 30%),
    left-hand (leftmost 20% of body zone), right-hand (rightmost 20% of body zone),
    eyes (small dark rects in head zone).
    """
    head_threshold = grid_h * 0.30
    body_threshold = grid_h * 0.70

    groups = {
        "head": [],
        "body": [],
        "legs": [],
        "left-hand": [],
        "right-hand": [],
        "eyes": [],
    }

    body_x_min = grid_w * 0.20
    body_x_max = grid_w * 0.80

    for i, (x, y, w, h, c) in enumerate(rects):
        center_y = y + h / 2
        center_x = x + w / 2

        if center_y < head_threshold:
            # Small rects in head = eyes
            if w <= 2 and h <= 2:
                groups["eyes"].append(i)
            else:
                groups["head"].append(i)
        elif center_y < body_threshold:
            if center_x < body_x_min:
                groups["left-hand"].append(i)
            elif center_x > body_x_max:
                groups["right-hand"].append(i)
            else:
                groups["body"].append(i)
        else:
            groups["legs"].append(i)

    # Remove empty groups
    return {k: v for k, v in groups.items() if v}


def generate_svg(
    rects: list,
    palette: list,
    grid_w: int,
    grid_h: int,
    pixel_size: int = 11,
    groups: dict | None = None,
    crisp_edges: bool = True,
) -> str:
    """Generate SVG string from rects.

    Args:
        rects: List of (x, y, w, h, color_idx) tuples
        palette: List of hex color strings
        grid_w, grid_h: Grid dimensions
        pixel_size: Size of each pixel in SVG units
        groups: Optional body-part grouping dict
        crisp_edges: Add shapeRendering="crispEdges" for pixel-perfect rendering
    """
    svg_w = grid_w * pixel_size
    svg_h = grid_h * pixel_size
    crisp = ' shapeRendering="crispEdges"' if crisp_edges else ""

    lines = [
        f'<svg viewBox="0 0 {svg_w} {svg_h}" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg"{crisp}>'
    ]

    if groups:
        # Emit grouped SVG
        grouped_indices = set()
        for indices in groups.values():
            grouped_indices.update(indices)

        for group_name, indices in groups.items():
            lines.append(f'  <g id="{group_name}">')
            for i in indices:
                x, y, w, h, c = rects[i]
                color = palette[c]
                lines.append(
                    f'    <rect x="{x * pixel_size}" y="{y * pixel_size}" '
                    f'width="{w * pixel_size}" height="{h * pixel_size}" '
                    f'fill="{color}"/>'
                )
            lines.append("  </g>")

        # Ungrouped rects
        ungrouped = [i for i in range(len(rects)) if i not in grouped_indices]
        if ungrouped:
            lines.append('  <g id="other">')
            for i in ungrouped:
                x, y, w, h, c = rects[i]
                color = palette[c]
                lines.append(
                    f'    <rect x="{x * pixel_size}" y="{y * pixel_size}" '
                    f'width="{w * pixel_size}" height="{h * pixel_size}" '
                    f'fill="{color}"/>'
                )
            lines.append("  </g>")
    else:
        # Flat SVG
        for x, y, w, h, c in rects:
            color = palette[c]
            lines.append(
                f'  <rect x="{x * pixel_size}" y="{y * pixel_size}" '
                f'width="{w * pixel_size}" height="{h * pixel_size}" '
                f'fill="{color}"/>'
            )

    lines.append("</svg>")
    return "\n".join(lines)


def generate_from_grid(
    grid: list,
    palette: list,
    grid_w: int,
    grid_h: int,
    merge: bool = True,
    pixel_size: int = 11,
    auto_group: bool = True,
) -> str:
    """High-level: grid → SVG string."""
    if merge:
        rects = merge_horizontal_runs(grid)
    else:
        rects = single_pixel_rects(grid)

    groups = auto_label_groups(rects, grid_w, grid_h) if auto_group else None
    return generate_svg(rects, palette, grid_w, grid_h, pixel_size, groups)



def main():
    parser = argparse.ArgumentParser(description="Convert image to pixel-art SVG rects")
    parser.add_argument("image", help="Input image path (PNG/JPG/WebP)")
    parser.add_argument("--grid", type=int, default=24, help="Grid size (longest dimension)")
    parser.add_argument("--colors", type=int, default=6, help="Number of palette colors")
    parser.add_argument("--pixel-size", type=int, default=11, help="SVG units per pixel")
    parser.add_argument("--merge", action="store_true", help="Merge adjacent same-color rects")
    parser.add_argument("--remove-bg", action="store_true", help="Remove detected background color")
    parser.add_argument("--no-groups", action="store_true", help="Skip auto body-part grouping")
    parser.add_argument("--output", "-o", help="Output SVG file (default: stdout)")

    args = parser.parse_args()

    grid, palette, w, h = load_and_quantize(args.image, args.grid, args.colors)

    if args.remove_bg:
        bg = detect_bg_color(grid, palette)
        if bg is not None:
            grid = remove_background(grid, bg)

    if args.json:
        meta = export_metadata(grid, palette, w, h)
        result = json.dumps(meta, indent=2)
    else:
        result = generate_from_grid(
            grid, palette, w, h,
            merge=args.merge,
            pixel_size=args.pixel_size,
            auto_group=not args.no_groups,
        )

    if args.output:
        Path(args.output).write_text(result)
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
