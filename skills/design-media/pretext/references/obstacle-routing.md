# Obstacle-Aware Text Routing with Pretext

## Overview
Pretext's `layoutNextLine()` accepts a different `maxWidth` for each line, enabling text to flow around arbitrary obstacles. Combined with column-based layout and headline fitting, this creates sophisticated editorial layouts with zero DOM measurement.

## Multi-Column Flow

### Basic Two-Column Layout
```js
const GUTTER = 48        // left/right page margin
const COL_GAP = 40       // gap between columns
const BODY_FONT = '18px "Iowan Old Style", "Palatino Linotype", Palatino, serif'
const LINE_HEIGHT = 30

function layoutColumns(text, pageWidth, pageHeight) {
  const contentWidth = pageWidth - GUTTER * 2
  const colWidth = (contentWidth - COL_GAP) / 2
  const colLeft = [GUTTER, GUTTER + colWidth + COL_GAP]

  const prepared = prepareWithSegments(text, BODY_FONT)
  let cursor = { segmentIndex: 0, graphemeIndex: 0 }
  const allLines = []

  for (let col = 0; col < 2; col++) {
    let y = GUTTER
    while (y + LINE_HEIGHT <= pageHeight - GUTTER) {
      const line = layoutNextLine(prepared, cursor, colWidth)
      if (!line) break
      allLines.push({ x: colLeft[col], y, text: line.text, width: line.width })
      cursor = line.end
      y += LINE_HEIGHT
    }
    if (layoutNextLine(prepared, cursor, colWidth) === null) break
  }
  return allLines
}
```

Key: The left column exhausts text first, then the right column resumes from the same cursor.

## Circle Obstacle Avoidance

### Interval Carving
For each line band (y to y + lineHeight), calculate where a circle intersects:

```js
function circleIntervalForBand(cx, cy, r, bandTop, bandBottom) {
  // Distance from band to circle center
  const closestY = Math.max(bandTop, Math.min(cy, bandBottom))
  const dy = Math.abs(closestY - cy)
  if (dy >= r) return null // no intersection

  const dx = Math.sqrt(r * r - dy * dy)
  return { left: cx - dx, right: cx + dx }
}

function getAvailableWidth(y, lineHeight, obstacles, colLeft, colRight) {
  let availLeft = colLeft
  let availRight = colRight

  for (const obs of obstacles) {
    const interval = circleIntervalForBand(obs.x, obs.y, obs.r + obs.padding, y, y + lineHeight)
    if (!interval) continue

    // If obstacle is near the left edge, push text right
    if (interval.left <= availLeft + 10) {
      availLeft = Math.max(availLeft, interval.right)
    }
    // If obstacle is near the right edge, push text left
    else if (interval.right >= availRight - 10) {
      availRight = Math.min(availRight, interval.left)
    }
    // If obstacle is in the middle, take the wider side
    else {
      const leftSpace = interval.left - availLeft
      const rightSpace = availRight - interval.right
      if (leftSpace >= rightSpace) availRight = interval.left
      else availLeft = interval.right
    }
  }

  return { left: availLeft, right: availRight, width: availRight - availLeft }
}
```

## Draggable Orb Physics

### Orb State
```js
const orbs = [
  { x: 300, y: 200, r: 70, vx: 0.3, vy: 0.2, color: [196, 163, 90] },
  { x: 600, y: 400, r: 55, vx: -0.2, vy: 0.15, color: [120, 180, 220] },
]
```

### Animation Loop
```js
function updateOrbs(orbs, dt, pageWidth, pageHeight) {
  for (const orb of orbs) {
    if (orb.paused) continue
    orb.x += orb.vx * dt
    orb.y += orb.vy * dt
    // Bounce off edges
    if (orb.x - orb.r < 0 || orb.x + orb.r > pageWidth) orb.vx *= -1
    if (orb.y - orb.r < 0 || orb.y + orb.r > pageHeight) orb.vy *= -1
    orb.x = Math.max(orb.r, Math.min(pageWidth - orb.r, orb.x))
    orb.y = Math.max(orb.r, Math.min(pageHeight - orb.r, orb.y))
  }
}
```

### Drag Handling
```js
let dragState = null

stage.addEventListener('pointerdown', e => {
  for (let i = orbs.length - 1; i >= 0; i--) {
    const dx = e.clientX - orbs[i].x
    const dy = e.clientY - orbs[i].y
    if (dx * dx + dy * dy <= orbs[i].r * orbs[i].r) {
      dragState = { orbIndex: i, offsetX: dx, offsetY: dy }
      orbs[i].paused = true
      break
    }
  }
})

stage.addEventListener('pointermove', e => {
  if (!dragState) return
  const orb = orbs[dragState.orbIndex]
  orb.x = e.clientX - dragState.offsetX
  orb.y = e.clientY - dragState.offsetY
})

stage.addEventListener('pointerup', () => {
  if (dragState) orbs[dragState.orbIndex].paused = false
  dragState = null
})
```

## Headline Font-Size Fitting

Binary search for the largest font size that fits a headline within a region:

```js
function fitHeadline(text, maxWidth, maxHeight, fontFamily) {
  let lo = 12, hi = 200
  while (lo < hi) {
    const mid = (lo + hi + 1) >>> 1
    const font = `700 ${mid}px ${fontFamily}`
    const prepared = prepareWithSegments(text, font)
    const lh = Math.round(mid * 1.08)
    const { height } = layoutWithLines(prepared, maxWidth, lh)
    height <= maxHeight ? lo = mid : hi = mid - 1
  }
  const font = `700 ${lo}px ${fontFamily}`
  const prepared = prepareWithSegments(text, font)
  const lh = Math.round(lo * 1.08)
  return { fontSize: lo, ...layoutWithLines(prepared, maxWidth, lh) }
}
```

## Pull Quotes

Place a pull quote as a rectangular obstacle with a left border:

```js
function layoutPullquote(quoteText, colLeft, colWidth, yStart, quoteFraction) {
  const qWidth = colWidth * quoteFraction
  const qFont = 'italic 20px "Iowan Old Style", Palatino, serif'
  const qLineHeight = 28
  const prepared = prepareWithSegments(quoteText, qFont)
  const { lines, height } = layoutWithLines(prepared, qWidth - 14, qLineHeight) // 14px for border+padding

  return {
    rect: { x: colLeft, y: yStart, w: qWidth, h: height + 16 },
    lines: lines.map((line, i) => ({
      x: colLeft + 14,
      y: yStart + 8 + i * qLineHeight,
      text: line.text,
      width: line.width
    }))
  }
}
```

## Drop Caps

Reserve space for a large initial letter:

```js
function layoutDropCap(firstChar, bodyFont, bodyLineHeight, dropCapLines) {
  // Find font size where the character is exactly dropCapLines tall
  const targetHeight = bodyLineHeight * dropCapLines
  let lo = 20, hi = 200
  while (lo < hi) {
    const mid = (lo + hi + 1) >>> 1
    mid * 1.1 <= targetHeight ? lo = mid : hi = mid - 1
  }
  const dcFont = `700 ${lo}px "Iowan Old Style", Palatino, serif`
  const prepared = prepareWithSegments(firstChar, dcFont)
  const width = prepared.widths[0] || lo * 0.7
  return { font: dcFont, fontSize: lo, width: width + 8, height: targetHeight }
}
```

## DOM Rendering

All text is positioned absolutely:
```js
function renderLine(container, line, font, className) {
  const div = document.createElement('div')
  div.className = className // 'line', 'headline-line', 'pullquote-line'
  div.style.cssText = `position:absolute;left:${line.x}px;top:${line.y}px;white-space:pre;font:${font}`
  div.textContent = line.text
  container.appendChild(div)
  return div
}
```

Orbs are `position: absolute; border-radius: 50%; pointer-events: none` divs with radial gradient backgrounds.
