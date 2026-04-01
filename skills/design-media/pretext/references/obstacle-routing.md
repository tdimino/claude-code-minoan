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

### Simple Mode — Single-Sided Routing

For each line band, calculate where a circle intersects and push text to one side:

```js
function circleIntervalForBand(cx, cy, r, bandTop, bandBottom) {
  const closestY = Math.max(bandTop, Math.min(cy, bandBottom))
  const dy = Math.abs(closestY - cy)
  if (dy >= r) return null
  const dx = Math.sqrt(r * r - dy * dy)
  return { left: cx - dx, right: cx + dx }
}

function getAvailableWidth(y, lineHeight, obstacles, colLeft, colRight) {
  let availLeft = colLeft, availRight = colRight
  for (const obs of obstacles) {
    const iv = circleIntervalForBand(obs.x, obs.y, obs.r + obs.padding, y, y + lineHeight)
    if (!iv) continue
    if (iv.left <= availLeft + 10) availLeft = Math.max(availLeft, iv.right)
    else if (iv.right >= availRight - 10) availRight = Math.min(availRight, iv.left)
    else {
      if (iv.left - availLeft >= availRight - iv.right) availRight = iv.left
      else availLeft = iv.right
    }
  }
  return { left: availLeft, right: availRight, width: availRight - availLeft }
}
```

### Advanced Mode — Slot Carving (from Cheng Lou's Editorial Engine)

The real Editorial Engine fills text on **BOTH sides** of an obstacle simultaneously. Instead of choosing one side, it carves the line into multiple viable slots:

```js
const MIN_SLOT_WIDTH = 50

// Subtract all blocked intervals from the available line width.
// Returns array of remaining viable slots.
function carveTextLineSlots(base, blocked) {
  let slots = [base]
  for (const iv of blocked) {
    const next = []
    for (const s of slots) {
      if (iv.right <= s.left || iv.left >= s.right) { next.push(s); continue }
      if (iv.left > s.left) next.push({ left: s.left, right: iv.left })
      if (iv.right < s.right) next.push({ left: iv.right, right: s.right })
    }
    slots = next
  }
  return slots.filter(s => s.right - s.left >= MIN_SLOT_WIDTH)
}

// Circle-band intersection with padding (horizontal + vertical).
function circleIntervalForBand(cx, cy, r, bandTop, bandBottom, hPad, vPad) {
  const top = bandTop - vPad, bottom = bandBottom + vPad
  if (top >= cy + r || bottom <= cy - r) return null
  const minDy = (cy >= top && cy <= bottom) ? 0 : (cy < top ? top - cy : cy - bottom)
  if (minDy >= r) return null
  const maxDx = Math.sqrt(r * r - minDy * minDy)
  return { left: cx - maxDx - hPad, right: cx + maxDx + hPad }
}
```

**Usage in the layout loop** — text fills every viable slot on each line:

```js
function layoutColumn(prepared, startCursor, regionX, regionY, regionW, regionH,
                      lineHeight, circleObs, rectObstacles) {
  let cursor = startCursor, lineTop = regionY
  const lines = []
  while (lineTop + lineHeight <= regionY + regionH) {
    const blocked = []
    for (const c of circleObs) {
      const iv = circleIntervalForBand(c.cx, c.cy, c.r, lineTop, lineTop + lineHeight, c.hPad, c.vPad)
      if (iv) blocked.push(iv)
    }
    for (const r of rectObstacles) {
      if (lineTop + lineHeight > r.y && lineTop < r.y + r.h)
        blocked.push({ left: r.x, right: r.x + r.w })
    }
    const slots = carveTextLineSlots({ left: regionX, right: regionX + regionW }, blocked)
    if (slots.length === 0) { lineTop += lineHeight; continue }
    slots.sort((a, b) => a.left - b.left)
    for (const slot of slots) {
      const line = layoutNextLine(prepared, cursor, slot.right - slot.left)
      if (!line) return { lines, cursor }
      lines.push({ x: Math.round(slot.left), y: Math.round(lineTop), text: line.text, width: line.width })
      cursor = line.end
    }
    lineTop += lineHeight
  }
  return { lines, cursor }
}
```

**Key difference:** Simple mode picks one side. Slot carving fills *all* viable gaps — text flows around both sides of an orb in the middle of a column. This is what CSS Shapes cannot do.

## Animated Obstacle Physics (from Cheng Lou's Editorial Engine)

The real Editorial Engine uses 5 orbs with velocity, edge bounce, mutual repulsion, and drag:

### Orb State
```js
const orbDefs = [
  { fx: 0.52, fy: 0.22, r: 110, vx: 24, vy: 16, color: [196, 163, 90] },
  { fx: 0.18, fy: 0.48, r: 85, vx: -19, vy: 26, color: [100, 140, 255] },
  { fx: 0.74, fy: 0.58, r: 95, vx: 16, vy: -21, color: [232, 100, 130] },
  { fx: 0.38, fy: 0.72, r: 75, vx: -26, vy: -14, color: [80, 200, 140] },
  { fx: 0.86, fy: 0.18, r: 65, vx: -13, vy: 19, color: [150, 100, 220] },
]
// fx/fy are fractional positions: x = fx * window.innerWidth
```

### Animation Loop with Mutual Repulsion
```js
function animate(now) {
  requestAnimationFrame(animate)
  const dt = Math.min((now - lastTime) / 1000, 0.05)
  lastTime = now

  // Move orbs
  for (const o of orbs) {
    if (o.paused || o.dragging) continue
    o.x += o.vx * dt
    o.y += o.vy * dt
    if (o.x - o.r < 0) { o.x = o.r; o.vx = Math.abs(o.vx) }
    if (o.x + o.r > pw) { o.x = pw - o.r; o.vx = -Math.abs(o.vx) }
    if (o.y - o.r < 0) { o.y = o.r; o.vy = Math.abs(o.vy) }
    if (o.y + o.r > ph) { o.y = ph - o.r; o.vy = -Math.abs(o.vy) }
  }

  // Mutual repulsion — orbs push each other apart
  for (let i = 0; i < orbs.length; i++) {
    for (let j = i + 1; j < orbs.length; j++) {
      const a = orbs[i], b = orbs[j]
      const dx = b.x - a.x, dy = b.y - a.y
      const dist = Math.sqrt(dx * dx + dy * dy)
      const minDist = a.r + b.r + 20
      if (dist < minDist && dist > 0.1) {
        const force = (minDist - dist) * 0.8
        const nx = dx / dist, ny = dy / dist
        if (!a.paused && !a.dragging) { a.vx -= nx * force * dt; a.vy -= ny * force * dt }
        if (!b.paused && !b.dragging) { b.vx += nx * force * dt; b.vy += ny * force * dt }
      }
    }
  }

  // Build obstacle list for slot-carving
  const circleObs = orbs.map(o => ({ cx: o.x, cy: o.y, r: o.r, hPad: 14, vPad: 4 }))

  // Full layout + render... (see layoutColumn above)
}
```

### Drag Handling (with click-to-pause)
```js
let activeOrb = null

stage.addEventListener('pointerdown', e => {
  const orb = hitTestOrbs(e.clientX, e.clientY)
  if (orb) {
    activeOrb = orb
    orb.dragging = true
    orb.dragStartX = e.clientX; orb.dragStartY = e.clientY
    orb.dragStartOrbX = orb.x; orb.dragStartOrbY = orb.y
    e.preventDefault()
  }
})

window.addEventListener('pointermove', e => {
  if (activeOrb) {
    activeOrb.x = activeOrb.dragStartOrbX + (e.clientX - activeOrb.dragStartX)
    activeOrb.y = activeOrb.dragStartOrbY + (e.clientY - activeOrb.dragStartY)
  }
})

window.addEventListener('pointerup', e => {
  if (activeOrb) {
    // Short drag = toggle pause; long drag = release
    const dx = e.clientX - activeOrb.dragStartX
    const dy = e.clientY - activeOrb.dragStartY
    if (dx * dx + dy * dy < 16) activeOrb.paused = !activeOrb.paused
    activeOrb.dragging = false
    activeOrb = null
  }
})
```

### DOM Element Pooling

The Editorial Engine reuses DOM elements instead of creating/destroying per frame:

```js
function syncPool(pool, count, className) {
  while (pool.length < count) {
    const el = document.createElement('div')
    el.className = className
    stage.appendChild(el)
    pool.push(el)
  }
  for (let i = 0; i < pool.length; i++) {
    pool[i].style.display = i < count ? '' : 'none'
  }
}

// In the animation loop:
syncPool(linePool, allBodyLines.length, 'line')
for (let i = 0; i < allBodyLines.length; i++) {
  linePool[i].textContent = allBodyLines[i].text
  linePool[i].style.left = allBodyLines[i].x + 'px'
  linePool[i].style.top = allBodyLines[i].y + 'px'
}
```

### Animated Character Obstacles

Replace orbs with animated sprites for interactive text-displacing characters. The sprite carries the same circular collision shape — the visual can be anything:

```js
// Creature obstacle with sprite and circular collision
const creature = {
  x: 400, y: 300, r: 60,  // collision circle
  vx: 20, vy: 15,
  spriteUrl: 'dragon-walk.png',
  frameW: 64, frameH: 64, frameCount: 8,
  frame: 0,
  el: createSpriteEl('dragon-walk.png'),
}

// In the animation loop, add to circleObs:
circleObs.push({ cx: creature.x, cy: creature.y, r: creature.r, hPad: 14, vPad: 4 })

// Animate sprite frame:
creature.frame = (creature.frame + 1) % creature.frameCount
creature.el.style.backgroundPosition = `-${creature.frame * creature.frameW}px 0`
```

The text reflows identically whether the obstacle is a glowing orb, a walking dragon, or a growing vine — the slot-carving algorithm only cares about the collision circle.

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
