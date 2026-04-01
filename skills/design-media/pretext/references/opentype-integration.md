# opentype.js + Pretext Integration

## Why Both Libraries

**Pretext** decides WHERE text goes — line breaking, obstacle routing, height prediction.
**opentype.js** decides HOW each glyph looks — SVG paths, Bezier control points, contour data.

Together they unlock effects neither achieves alone: per-glyph SVG rendering with correct line breaking, live text reflow around animated obstacles with per-character animation, outline calligrams where text fills the actual contour of a glyph.

## Font Loading

```js
// opentype.js — parse font binary for glyph access
const FONT_URL = 'https://cdn.jsdelivr.net/npm/@fontsource/inter@5.0.8/files/inter-latin-400-normal.woff'
const buffer = await fetch(FONT_URL).then(r => r.arrayBuffer())
const font = opentype.parse(buffer)
const scale = fontSize / font.unitsPerEm

// Pretext — needs matching CSS font for canvas measureText
const PRETEXT_FONT = `${fontSize}px Inter, sans-serif`
```

**Critical:** The CSS font loaded by the browser and the binary parsed by opentype.js MUST be the same typeface, or line breaks won't align with glyph widths.

**Font format:** opentype.js cannot parse `.woff2`. Use `.woff` or `.ttf` from `@fontsource` via jsdelivr.

## Integration Pattern: Pretext Layout → opentype.js Render

```js
// 1. Pretext computes line breaks and positions
const prepared = prepareWithSegments(text, pretextFont)
const lines = []
let cursor = { segmentIndex: 0, graphemeIndex: 0 }
let y = 0
while (true) {
  const maxWidth = computeAvailableWidth(y, obstacles)
  const lineX = computeLineStart(y, obstacles)
  const line = layoutNextLine(prepared, cursor, maxWidth)
  if (!line) break
  lines.push({ text: line.text, x: lineX, y, width: line.width })
  cursor = line.end
  y += LINE_HEIGHT
}

// 2. opentype.js renders each character as SVG path
for (const line of lines) {
  const glyphs = font.stringToGlyphs(line.text)
  let cx = line.x
  const baseline = line.y + fontSize
  for (let i = 0; i < glyphs.length; i++) {
    const g = glyphs[i]
    const path = g.getPath(0, 0, fontSize)     // render at origin
    const d = path.toPathData(2)                 // 2 decimal places
    const advW = g.advanceWidth * scale
    const kern = (i < glyphs.length - 1)
      ? font.getKerningValue(g, glyphs[i+1]) * scale : 0

    // Position via SVG group transform (cheap to update on reflow)
    const groupEl = createSvgGroup(cx, baseline)
    const pathEl = createSvgPath(d)
    groupEl.appendChild(pathEl)
    container.appendChild(groupEl)

    cx += advW + kern
  }
}
```

## Key Techniques

### Glyph Path Art (Demo 1)
Render letterforms as SVG with 4 modes: fill, stroke, control points, sinusoidal distortion.

```js
const path = glyph.getPath(x, y, fontSize)
const d = path.toPathData(2)
// Stroke-draw animation via stroke-dashoffset
el.setAttribute('stroke-dasharray', pathLength)
el.setAttribute('stroke-dashoffset', pathLength)
el.style.animation = `draw-stroke ${duration}ms linear forwards`
```

### Text on Path (Demo 2)
Per-glyph placement along Bezier curves using arc-length parameterization.

```js
// Build lookup table from SVG path
const samples = 400
const table = Array.from({length: samples}, (_, i) => {
  const t = i / (samples - 1)
  return { t, len: svgPath.getPointAtLength(t * totalLength) }
})

// Place each glyph at correct arc position with tangent rotation
for (const glyph of glyphs) {
  const pt = getPointAtLength(dist)
  const angle = getTangentAngle(dist)
  el.setAttribute('transform', `translate(${pt.x},${pt.y}) rotate(${angle})`)
  dist += glyph.advanceWidth * scale + 1.5
}
```

### Variable Font Animation (Demo 3)
Requires Google Fonts CSS for the variable font, NOT opentype.js (which reads static .woff).

```js
// CSS loads the variable font
// @import Inter variable from Google Fonts
// Per-character Splitting.js wraps each char in a <span>
// Animate via CSS font-variation-settings
span.style.fontVariationSettings = `'wght' ${weight}, 'wdth' ${width}`
```

### Glyph Morphing (Demo 4)
opentype.js extracts contours, flubber interpolates between them.

```js
// flubber loaded as UMD via <script src="cdn...flubber.min.js">
const { interpolate, combine, separate } = window.flubber

const contoursA = splitContours(glyphA.getPath(0, 0, size).toPathData())
const contoursB = splitContours(glyphB.getPath(0, 0, size).toPathData())

// Match contour counts: equal, 1-to-many, many-to-1, or general
if (contoursA.length === contoursB.length) {
  interpolators = contoursA.map((a, i) => interpolate(a, contoursB[i]))
} else if (contoursA.length === 1) {
  interpolators = [separate(contoursA[0], contoursB)]
} else if (contoursB.length === 1) {
  interpolators = [combine(contoursA, contoursB[0])]
}

// In rAF: interpolators.map(fn => fn(t)).join(' ')
```

### Outline Calligrams (Demo 5)
Pretext `layoutNextLine` fills text INSIDE a glyph's actual contour.

```js
// 1. Render large glyph to offscreen canvas
const maskCanvas = document.createElement('canvas')
const ctx = maskCanvas.getContext('2d')
const largePath = glyph.getPath(0, 0, canvasSize)
largePath.draw(ctx) // fills the glyph shape

// 2. For each text line y, scan the canvas row to find interior extent
const imageData = ctx.getImageData(0, y, width, 1)
let left = -1, right = -1
for (let x = 0; x < width; x++) {
  if (imageData.data[x * 4 + 3] > 128) {
    if (left < 0) left = x
    right = x
  }
}
const availableWidth = right - left

// 3. Pretext lays out text within that width
const line = layoutNextLine(prepared, cursor, availableWidth)
```

### Wet Ink Distortion (Manuscript Layer 1)
Oscillate Bezier control points for freshly-written glyphs.

```js
const commands = path.commands.map(c => ({...c}))  // deep copy
// In rAF loop:
const amp = maxAmp * Math.exp(-elapsed / tau)
for (const c of commands) {
  if (c.x1 !== undefined) c.x1 += Math.sin(seed + idx) * amp
  if (c.x2 !== undefined) c.x2 += Math.sin(seed + idx * 2.3) * amp
}
pathEl.setAttribute('d', commandsToPathData(commands))

// Helper: convert opentype.js command objects back to SVG path data string
function commandsToPathData(commands) {
  let d = ''
  for (const c of commands) {
    switch (c.type) {
      case 'M': d += `M${c.x.toFixed(1)} ${c.y.toFixed(1)}`; break
      case 'L': d += `L${c.x.toFixed(1)} ${c.y.toFixed(1)}`; break
      case 'C': d += `C${c.x1.toFixed(1)} ${c.y1.toFixed(1)} ${c.x2.toFixed(1)} ${c.y2.toFixed(1)} ${c.x.toFixed(1)} ${c.y.toFixed(1)}`; break
      case 'Q': d += `Q${c.x1.toFixed(1)} ${c.y1.toFixed(1)} ${c.x.toFixed(1)} ${c.y.toFixed(1)}`; break
      case 'Z': d += 'Z'; break
    }
  }
  return d
}
```

### Iron Gall Aging (Manuscript Layer 7)
Per-glyph fill color based on writtenAt timestamp.

```js
const age = (now - writtenAt) / agingRate
const t = Math.min(1, age)
const fresh = [42, 31, 20]   // #2a1f14
const aged = [107, 93, 79]   // #6b5d4f
const faded = [139, 122, 96] // #8b7a60
const color = t < 0.5
  ? lerp(fresh, aged, t * 2)
  : lerp(aged, faded, (t - 0.5) * 2)
pathEl.setAttribute('fill', `rgb(${color})`)
```

## Performance Notes

| Operation | Cost | Notes |
|-----------|------|-------|
| `prepareWithSegments` | ~19ms/500 texts | One-time. Cache the result. |
| `layoutNextLine` × 40 lines | ~0.5ms | Pure arithmetic. |
| `glyph.getPath()` × 900 | ~20ms | Cache pathData strings. Only regenerate on position change. |
| SVG DOM `setAttribute('d')` × 900 | ~10ms | Avoid when possible — reposition via `<g transform>` instead. |
| SVG DOM `setAttribute('transform')` × 900 | ~5ms | Cheap — preferred for reflow. |
| Wet ink distortion × 15 glyphs | <1ms | Only recent glyphs. Exponential decay limits count. |
| Aging color update × 900 | ~5ms every 500ms | Batch with setInterval, not rAF. |

**Total reflow budget:** <50ms. Layout + SVG transform updates stay well under this.
