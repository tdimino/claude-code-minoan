# Typographic ASCII Art with Pretext

## Overview
Pretext's `prepareWithSegments()` measures individual character widths with proportional font precision. Combined with brightness estimation via canvas `getImageData`, this enables rendering visual data (fluid simulations, 3D geometry, images) as proportionally-spaced ASCII art that looks dramatically better than monospace ASCII.

## Palette Architecture

The palette is a sorted array of `{ char, weight, style, font, width, brightness }` entries. Built once at startup, queried per-cell per-frame.

### Building the Palette
1. Iterate CHARSET × WEIGHTS × STYLES
2. For each combination, measure width via `prepareWithSegments(ch, font).widths[0]`
3. Estimate brightness via canvas `getImageData` (render char to small canvas, sum alpha channel)
4. Normalize brightness to 0-1 range
5. Sort by brightness ascending

### Key Constants
```
CHARSET: ' .,:;!+-=*#@%&abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
WEIGHTS: [300, 500, 800]
STYLES: ['normal', 'italic']
FONT_SIZE: 14
LINE_HEIGHT: 17
FONT_FAMILY: 'Georgia, Palatino, "Times New Roman", serif'
```

### Character Lookup
Binary search by brightness, then linear scan ±15 entries scoring by both brightness match (weight 2.5) and width match (normalized). This dual-scoring is what makes proportional ASCII look good—characters match both the visual density AND the spatial width of the cell.

## Grid Rendering

### DOM Structure
```html
<div id="art">
  <div class="r"><!-- row: spans with class="w3 a5" etc --></div>
  <div class="r"><!-- row --></div>
  ...
</div>
```

### CSS Classes
Weight: `.w3` (300), `.w5` (500), `.w8` (800)
Style: `.it` (italic)
Opacity: `.a1` through `.a10` (0.08 to 1.0 in 10 steps)
Row: `.r` with `white-space: pre; overflow: hidden; font-family: Georgia, ...; font-size: 14px;`

### Per-Cell HTML Generation
```js
function esc(c) {
  if (c === '&') return '&amp;'
  if (c === '<') return '&lt;'
  if (c === '>') return '&gt;'
  return c
}

function weightClass(w, s) {
  const wc = w === 300 ? 'w3' : w === 500 ? 'w5' : 'w8'
  return s === 'italic' ? wc + ' it' : wc
}

// For each cell: find best char, determine opacity class from brightness
const alphaClass = 'a' + Math.max(1, Math.min(10, Math.round(brightness * 10)))
html += `<span class="${weightClass(best.weight, best.style)} ${alphaClass}">${esc(best.char)}</span>`
```

### Grid Sizing
```js
// Calculate grid dimensions from viewport
const avgCharW = palette.reduce((s, p) => s + p.width, 0) / palette.length
const aspect = avgCharW / LINE_HEIGHT
const COLS = Math.floor(viewportWidth / avgCharW)
const ROWS = Math.floor(viewportHeight / LINE_HEIGHT)
```

## Visual Data Sources

### Fluid Simulation (Fluid Smoke)
- Simple Euler-advection density field on the grid
- Multiple orbiting emitters inject density
- Velocity field from layered sinusoidal functions
- Brightness = density value at each cell
- Width target = average char width (uniform grid)

### 3D Wireframe (Wireframe Torus)
- Parametric torus: major radius 0.42, minor radius 0.12
- Project 3D vertices to 2D with perspective
- Rasterize edges to small canvas
- Read pixel brightness from canvas
- Brightness = rasterized wireframe intensity

### Particle System (Variable Typographic ASCII)
- Particles with position, velocity, attractors
- Stamp particles onto a density field (Gaussian splat)
- Field decays each frame (multiply by 0.82)
- Brightness = field value at cell
- Width target can vary with field gradient

## Performance Notes
- Build palette ONCE at startup (expensive: ~200ms)
- Use `innerHTML` batch update per row, not per-character DOM ops
- Limit grid to ~200 cols × 80 rows max
- Use `requestAnimationFrame` for animation
- Show FPS/timing in a fixed stats div at bottom

## Color Schemes
The demos use gold-on-black: `rgba(196,163,90, alpha)`. Other good schemes:
- Green terminal: `rgba(0,255,65, alpha)` on `#0a0a0a`
- Blue hologram: `rgba(100,180,255, alpha)` on `#06060e`
- Amber CRT: `rgba(255,176,0, alpha)` on `#0a0800`
- White-on-dark: `rgba(255,255,255, alpha)` on `#08080e`
