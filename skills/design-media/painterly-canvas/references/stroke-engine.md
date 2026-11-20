# Stroke Engine

The brushstroke is the only primitive that matters. Geometry supplies positions and flat underpaint, and every surface the eye lands on is a stroke.

Two implementations are described here and their numbers differ. **Starter** means `assets/painterly-starter.html`, the file to copy. **Genesis** means `assets/genesis/endless-painted-world.html`, cited by line number. The starter's `stroke()` follows the layer recipe of the genesis's `paintedStroke` in simplified form. Function names differ between the two, and `genesis-map.md` has the name map.

## Contents

1. Epoch hashing
2. Stroke anatomy
3. Parameters
4. Stroke ids
5. The genesis primitives
6. Anchoring strokes to the world
7. Broken color
8. Painted polygons
9. Failure modes

## 1. Epoch hashing

Each stroke takes a stable integer `id` and the current `frame`. Its jitter comes from a hash, not from `Math.random()`:

```js
const epoch = floor((frame + (id % hold)) / hold);
const j = hash(id, epoch, k) / 2147483648 - 1;   // -1..1, k picks the channel
```

Three consequences follow from that one line.

- **Stable within an epoch.** For `hold` consecutive frames the stroke gets identical jitter, so it sits still. At the epoch boundary it re-rolls once: position, angle, length, width and color all shift slightly, as if repainted.
- **Staggered across strokes.** The `id % hold` offset puts each stroke's boundary on a different frame. Without it every stroke re-rolls together and the whole image pulses.
- **Deterministic.** Frame N always paints the same picture, so `?frame=N` screenshots and regression checks are possible.

The id must be non-negative: JavaScript `%` keeps the sign, so a negative id puts its epoch boundary on the wrong frame and breaks the stagger.

The render loop repaints at 12 fps while physics runs every animation frame (genesis 7366, starter section 11). At 60 fps the re-rolls read as noise, at 12 they read as animation drawn on twos. Leave the paint rate alone.

## 2. Stroke anatomy

One stroke is a quadratic curve drawn several times with `lineCap = 'butt'`, each pass offset along the stroke's normal `(nx, ny) = (-sin a, cos a)`. Offsets and widths are fractions of the stroke width `W`.

| Pass | Starter | Genesis (876–916) |
|---|---|---|
| Under-shadow | Offset `+0.28 W`, width `0.58 W`, hue +10, light −18, when `impasto > 0.2` | Offset `+0.28 W` plus 0.75 px down, width `0.58 W`, hue +10, sat ×0.88, light −19, alpha `× impasto × 0.40`, only when `impasto > 0.22` and `W > 2.8` |
| Body | Width `0.78 W`, alpha ×0.85 | Width `0.76 W`, alpha ×0.84, ends shortened when feathered |
| Dark streak | Always: offset `+0.22 W`, width `0.22 W`, hue +12, light −8 | Only as a feather band: offset `(0.24 + 0.05 r) W`, width `0.23 W`, hue +12, light −8, alpha ×0.66 |
| Lit ridge | Offset `−0.27 W`, width `0.20 W`, hue −9, sat +10, light `+12 + 9 × impasto` | Offset `−(0.27 + 0.04 r) W`, same color shifts, alpha ×0.72, overshoots each end by 3–9% of the length |
| Body-only cutoff | `W < 3` or `L < 8` | `W <= 3.1` or `L <= 8` |

The shadow side shifts hue up and darker, the lit side shifts hue down and lighter. That warm-light, cool-shadow split keeps a single mark from reading as a flat rectangle.

Small strokes draw the body only: the passes would overlap into mud, and small strokes are the majority by count.

Two genesis behaviors the starter simplifies away:

- **No under-shadow at low impasto.** Genesis terrain washes (0.16–0.18), water strokes and sky sit at or below the 0.22 threshold, so they are two- or three-pass marks with no cast shadow.
- **Feathering** for large strokes (`W > 4.2` and `L > 13`): the body is shortened by 7.5% at each end, and three thin bands overshoot the ends by different jittered amounts, so the stroke tapers into ragged bristle tips. The dark streak exists only as one of those bands. The starter's marks look like slabs next to the genesis because it omits this. Port it for marks above about 13 px long.

## 3. Parameters

Starter signature: `stroke(c, x, y, len, wid, ang, curve, col, alpha, impasto, id, frame, hold, drift)`. The genesis passes `h, s, l` separately in place of `col`.

| Parameter | Meaning | Notes |
|---|---|---|
| `len`, `wid` | Screen pixels before jitter | Clamped after jitter to 320 and 46 in the starter, 340 and 48 in the genesis |
| `ang` | Screen-space radians | Derive it from projected geometry wherever possible. Jitter is ±0.1 rad (starter), ±0.11 (genesis) |
| `curve` | Perpendicular bend of the control point, px | 0 for water and architecture, about `−len × 0.1` for ground, `−len × 0.16` for grass |
| `alpha` | Body opacity | 0.84–0.95 for objects, 0.44–0.68 for washes laid over a filled polygon |
| `impasto` | 0–1 paint thickness: shadow strength and ridge brightness | 0.18–0.28 terrain washes and water, 0.42 ground, 0.5–0.62 leaves and petals |
| `hold` | Frames between re-rolls | Genesis: 2 for water, flowers and grass, 3 for vines, 4 for ground, outdoor walls and frames, 6 for interior dabs |
| `drift` | Position jitter in px | Genesis: 0.7 for architectural frames, 1.0–1.8 for plants, 1.3 for wall strokes, 2.0 for ground |

`hold` is the liveliness dial and `drift` the looseness dial: water at `hold = 2` shimmers, an interior wall at `hold = 6` barely stirs. Set the pair per material before tuning anything else.

## 4. Stroke ids

Ids are stable, non-negative integers, unique among everything in view.

- **Chunk content (starter)**: each chunk owns a block of 512 ids packed from its coordinates, `1000000 + ((cx & 1023) * 1024 + (cz & 1023)) * 512`, and increments through it. Rebuilding the chunk reproduces the same ids, and no two loaded chunks share a block.
- **Chunk content (genesis)**: a counter seeded from the chunk hash, `(seed & 0x0fffffff) || 1`. Ranges of different chunks can overlap by chance. The cost is two distant strokes sharing a jitter stream, which nobody sees, but the starter's packing removes the possibility.
- **Multi-stroke objects**: the starter reserves 40 ids per tree and uses `tr.id + 1 + k` for its dabs. The genesis draws one id from the chunk counter per canopy blob (1166–1168).
- **Global sets**: fixed bases far apart. Starter: far washes 700000+, sky 900000+. Genesis: sky 900000+, clouds 910000+, petals 920000+, stars 930000+.
- **Derived from position**: the genesis keys a terrain quad's washes as `abs(round(xm * 7.3 + zm * 13.7)) + 500000`. The starter keys far washes from a hash of their world grid cell.
- **Never** the array index of a per-frame list, the loop counter of a sorted draw list, or anything derived from screen position. Those change as the camera moves, and the stroke re-rolls every frame.

## 5. The genesis primitives

| Primitive | Line | Use |
|---|---|---|
| `paintedStroke` | 876 | The full layered mark. Ground, foliage, structure, sky |
| `paintFastDab` | 2688 | Up to three passes, or four with tapered ends when `softCap` is set. Drift is fixed near 1 px. For filling interior surfaces where dozens of dabs tile one polygon |
| `paintRoundDab` | 2722 | A wobbled ellipse (8 or 12 jittered control points, closed with quadratic midpoints) filled with a three-stop gradient plus an arc highlight. Fruit, bottles, bread, lamp globes |
| `drawPaintedSegment` | 917 | Splits a long line into strokes of about 110 px (at most 10 segments, so very long lines get longer pieces), alternating lightness, ids stepping by 13. Beams, rails, masts, frames |

A single stroke cannot bend past its quadratic, so long edges are segmented. Segments overlap by 12% to hide the joins. The starter has `stroke()` only.

## 6. Anchoring strokes to the world

A ground stroke stores a world position and a world-space direction vector `(dx, dy, dz)`, where `dy` is the terrain's rise along the stroke. At draw time both ends are projected. Starter:

```js
const p = project(cam, [s.x, s.y, s.z], 0.35);
const tip = project(cam, [s.x + s.dx, s.y + s.dy, s.z + s.dz], 0.2);
if (!tip) continue;
const ang = atan2(tip.sy - p.sy, tip.sx - p.sx);
const len = clamp(hypot(tip.sx - p.sx, tip.sy - p.sy) * 2, 9, 110);
const wid = clamp(s.wid * p.scale, 4, 38);
```

The genesis (5745–5760) clamps length to 9–112 and width to 4–40 and bends ground strokes by `−len × 0.11`.

The paint then foreshortens and converges with the ground it lies on. Strokes given a screen-space angle and length without projection float in front of the terrain like stickers. When the far end falls behind the camera, skip the stroke; do not fall back to a fixed screen-space mark.

Direction comes from the land (genesis 1707–1711):

- slopes steeper than about 0.34: perpendicular to the gradient, so strokes run along contours
- flats: a slow sine of position
- paths, vineyard rows and cobbles: fixed
- water: zero in the genesis. The starter aims water strokes along the camera's right vector, which lies in the water plane, so ripples read level from any heading

## 7. Broken color

A flat fill looks digital however good the hue. `makeBrokenPalette` (genesis 2755) turns one base color into five by mixing toward fixed notes:

| Note | Mix toward | Amount |
|---|---|---|
| warm | `[40, 76, l+12]` golden bounce | 0.30 (0.20 for cool bases) |
| cool | `[232, 40, l−15]` violet-indigo shadow | 0.32 |
| rose | `[16, 58, l+4]` | 0.22 (0.14 cool) |
| hi | `[44, 46, l+19]` cream highlight | 0.36 |
| base | unchanged | — |

Dabs tiling a surface pick from the five by a fixed index, `(row × 7 + col × 11 + id) % 5` (3138). The eye mixes them back to the base color and the surface vibrates.

Shadows in the genesis mix toward indigo-violet, hue about 218–246 at saturation about 20–55, never toward gray or black: cloud shadow (295), night grade (253), cast shadows (955), ambient occlusion on walls (3087) and cylinder shading (840). Gray shadows read as mud and drain the palette. The starter applies this in its night grade only; its stroke shadow darkens in place, and its day vignette is a warm brown.

Mix through RGB, store as HSL. `mix()` converts both ends to RGB, interpolates, and converts back. Interpolating hue directly between green (100) and violet (270) passes through cyan and blue.

## 8. Painted polygons

`drawPaintedPoly3D` (genesis 3071) is the workhorse for anything with flat faces. The starter has no equivalent, so port this when adding buildings.

1. Back-face cull against the supplied normal.
2. Near-clip and project.
3. Grade the color for light, time of day and fog.
4. Fill the polygon. Options: `wallAO` (vertical gradient, violet at the ceiling line, warm at the floor) or `depthGrad` (gradient along the receding edge).
5. Clip to the polygon and lay strokes over it. The two cases differ:
   - **Indoor faces** (3126–3142): a staggered grid of `paintFastDab` marks in the five-note broken palette, angled along the polygon's first screen edge so brushwork runs with the surface in perspective, optionally cross-hatched.
   - **Outdoor faces** (3143–3149): a plain grid of one or two columns by two or three rows of `paintedStroke`, horizontal unless `opts.strokeAng` is set, at alpha 0.68, impasto 0.42, hold 4, drift 1.3.

The flat fill underneath is required. Strokes alone leave gaps that show the sky through a wall.

Walls of a room the player is in or near are a separate case, painted by `paintWallTapestry3D`. See `living-details.md` §2.

## 9. Failure modes

| Symptom | Cause |
|---|---|
| Whole image boils every frame | `Math.random()` at draw time, or ids derived from per-frame order |
| Image pulses in unison every few frames | `id % hold` stagger missing from the epoch |
| Strokes swim across the ground when turning | Angle and length not derived from projected endpoints |
| Ground strokes sliced along straight lines, or missing in patches | Ground quads sorted on mean depth; see `world-pipeline.md` §7 |
| Hairline cracks between terrain quads | Fill without the same-color 1.25 px outline |
| Muddy dark patches | Too many layered passes on strokes under 3 px wide, or shadows mixed toward gray |
| Giant slabs across the screen near the camera | Width and length not clamped after multiplying by `scale` |
| One frame hitches, then recovers | Unbounded stroke count near the camera; cull by distance before projecting |
| `NaN` poisoning a canvas path | Non-finite coordinate reaching `quadraticCurveTo`; the guard at the top of `stroke()` exists for this |
