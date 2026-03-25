# Pixel Art SVG Techniques

## Core Principle: Rects Only

Pixel-art SVGs use `<rect>` elements exclusively — no `<path>`, `<circle>`, or curves. Every pixel in the source image maps to one axis-aligned rectangle in the SVG.

## shapeRendering

Add `shapeRendering="crispEdges"` to the root `<svg>` to prevent anti-aliasing:
```xml
<svg viewBox="0 0 264 176" shapeRendering="crispEdges" fill="none" xmlns="http://www.w3.org/2000/svg">
```

## Grid-to-SVG Conversion

Each pixel at grid position (x, y) with color C becomes:
```xml
<rect x="{x * pixelSize}" y="{y * pixelSize}" width="{pixelSize}" height="{pixelSize}" fill="{C}"/>
```

Default `pixelSize = 11` (matches the ayotomcs reference).

## Run-Length Optimization

Adjacent same-color pixels in a row merge into a single wider rect:
```
Before: 3 individual rects at x=0,11,22 (color #DD775B)
After:  1 rect at x=0, width=33, same color
```

This reduces SVG file size by ~40-60% for typical pixel art.

## Body Part Auto-Grouping

Position-based heuristics assign `id` attributes for GSAP targeting:

| Zone | Y Range | ID |
|------|---------|-----|
| Head | Top 30% | `head` |
| Eyes | Small dark rects in head zone | `eyes` |
| Body | Middle 40% | `body` |
| Left hand | Body zone, left 20% | `left-hand` |
| Right hand | Body zone, right 20% | `right-hand` |
| Legs | Bottom 30% | `legs` |

## Color Quantization Pipeline

1. Load image as RGBA
2. Resize to grid (nearest-neighbor to preserve edges)
3. Quantize RGB to N colors (median cut)
4. Detect background (most common edge color)
5. Remove background pixels (set to transparent)

## Palette Constraints

The ayotomcs reference uses only 4 colors:
- `#DD775B` — Claude terracotta (body)
- `black` — Eyes
- `#1A4C81` — Dark blue (code/props)
- `#5D5B56` — Gray (details)

Limiting to 4-6 colors produces cleaner, more iconic pixel art.

## Frame-Based Animation

For complex animations (typing, detailed gestures), create multiple complete SVG groups:
```xml
<svg viewBox="0 0 158 128">
  <g style="display: inline"><!-- Frame 0: idle --></g>
  <g style="display: none"><!-- Frame 1: lean left --></g>
  <g style="display: none"><!-- Frame 2: type --></g>
  <!-- ... up to 36 frames -->
</svg>
```

Toggle visibility via JavaScript — only one frame visible at a time.
