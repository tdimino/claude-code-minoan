# World Pipeline

How a frame is assembled, from noise fields to the linen overlay. Line numbers and function names refer to the genesis, `assets/genesis/endless-painted-world.html`, unless a passage says **starter** (`assets/painterly-starter.html`). The starter implements a simplified version of §1–3 and §5–10. `genesis-map.md` maps the function names between the two.

## Contents

1. Frame anatomy
2. Surfaces and resolution
3. Fields: terrain as pure functions
4. Macro geography: regions and landmarks
5. Near field: chunks
6. Far field: the ring grid and its cache
7. The draw list
8. Color pipeline: grade, shadow, fog
9. Day state
10. Post
11. Budgets
12. Failure modes

## 1. Frame anatomy

```
loop (every animation frame)
  update physics, audio, time of day
  every 1/12 s:
    ds  = dayState(tod)                     one lighting object for the frame
    cam = camera(player pose)
    if pose, time or weather moved: repaint far canvas (sky, then horizon rings)
    blit far canvas to back buffer
    gather near items from visible chunks and landmarks into one list
    sort back to front, paint each
    interior of the building the player stands in, painted last
    post: linen multiply, vignette
    blit back buffer to the visible canvas
```

Three canvases: visible, back buffer, far cache. Only the final blit touches the visible canvas, so a half-painted frame never shows.

## 2. Surfaces and resolution

Logical size is fixed (genesis 1120×700, starter 960×600) and every draw call uses logical pixels, with `setTransform(DPR, 0, 0, DPR, 0, 0)` handling density. CSS scales the canvas to fit. Fixed logical size means stroke widths, clamps and culling margins are tuned once.

- Cap DPR at 2. On phones with a short edge under 900 px the genesis forces DPR 1 (line 52). Stroke count dominates cost, but 3× buffers triple the fill work for no visible gain under brushwork.
- `getContext('2d', { alpha: false })` on all three.
- `FOCAL = (H / 2) / tan(fov / 2)` with a 52–54° vertical field of view.

## 3. Fields

Every property of the land is a pure function of `(x, z)`: no stored heightmap, no generation step.

- `valueNoise2D` (91) hashes the four lattice corners and smoothstep-interpolates. `fbm2` (104) sums three octaves weighted 0.56 / 0.30 / 0.14 with offset, non-integer frequency ratios (2.03, 4.11) so octaves never align. `ridged2` (111) is `1 − |2n − 1|`, squared, for mountain crests.
- Low-frequency **mask fields** decide what kind of place this is: `rawSeaField` (343) and `rawMtnField` (362) at about 0.0015 cycles per meter, plus `warmth` and `ridge` in `biomeAt` (492). Biomes are thresholds on those four numbers.
- `terrainY` (507) composes macro fbm scaled by the ridge field, a sine-product roll, mountains added through `pow(mf, 1.35)`, coast shaping where the sea field nears zero, then landmark flattening.
- `surfaceAt` (684) classifies a point into a material name used for palette choice and footstep sound: meadow, path, sand, chalk, rock, snow, cobble, vineyard, water, sea, tarn, pier, wood, stone. Chunk generation remaps `pier`, `wood` and `stone` to ground materials (1673–1674, 1700).

Because the functions are pure, the far horizon samples the same land at 640 m that the chunks build at 20 m. There is no level-of-detail mesh to manage, only the number of samples to take.

**Hand-authored origin.** To open an endless world on a composed view, the sea and mountain fields blend toward authored shapes near the origin: a coastline along a chosen x, three Gaussian peaks. The sea field uses the mask `1 − smoothstep(560, 820, r)`, the mountain field `1 − smoothstep(580, 860, r)` with an extra calm zone around spawn (`smoothstep(140, 290, r)`, line 378). Beyond that radius the procedural field takes over.

**Flattening.** Wherever something must stand, blend height toward a target: `y = y * (1 − m) + target * m` with `m = 1 − smoothstep(inner, outer, dist)`. Spawn meadow, town plateau, lighthouse headland and tarn basin all use it.

## 4. Macro geography

The world divides into 460 m regions (339–473). `getRegionFeature(rx, rz)` hashes the region coordinates and rolls for a feature: at most 68% of regions get one, and open-sea regions get none. It places the feature at a jittered center and chooses the type from the fields at that point: seaside where the sea field is near zero, mountains where the mountain field is high, otherwise town, vineyard or aqueduct by roll. Seaside features sample the sea-field gradient once, then take six steps along that fixed direction toward the `sf = −0.05` contour, which puts the harbor on the actual shoreline (420–428).

- Five origin regions are hand-specified in `ORIGIN_FEATURES` so the starting area is curated.
- Results go through an LRU map capped at 512.
- `nearestFeature(x, z)` checks only the 3×3 neighborhood.
- `buildLandmark(feat)` (1200) expands a feature into buildings, piers, trees and props, seeded from `feat.seed`.

The starter has no regions or landmarks.

## 5. Near field: chunks

`buildChunk(cx, cz)` (1639) runs once per 24 m chunk, seeded by `hash2i(cx, cz, 9001)`. It produces:

| Content | Count | Notes |
|---|---|---|
| Ground quads | 6×6 | Shared 7×7 corner heights and colors, so neighbors meet exactly. Opposite-corner colors are stored for a gradient fill |
| Ground strokes | 250 plus shore | World-anchored paint; see `stroke-engine.md` §6. Extra strokes are seeded on quads that straddle the waterline, where foam and sand need density |
| Anchors | 108 attempts, 165 in vineyard chunks | Grass, flowers, reeds, lavender, sunflowers, lilies, vines: a base point, height, width, color and phase. Attempts on unsuitable surfaces are discarded (`SKIP_ANCHOR_SURFS`) |
| Trees, cottages, walls, fences, boulders, lanterns | few | The chunk checks whether it sits in a landmark's core (`inLandmarkCore`) so the two generators do not build on top of each other |

`ensureChunksAround` (1943) builds a 7×7 block around the player and evicts only beyond radius + 1, so up to 81 chunks stay in memory. The one-chunk margin prevents rebuild thrash when the player paces across a boundary.

Chunks hold only static data. Anything that moves (wind sway, water shimmer, sheep) is computed at draw time from `t` and the object's stored phase.

**Starter:** 20 m chunks of 5×5 quads, 280 ground strokes, 70 tufts and up to three trees, with two corner colors per quad.

## 6. Far field

`renderFarHorizon` (2242) covers 52 m to 640 m with a polar grid centered on the camera: 14 rings at geometrically shrinking radii (`FAR_RINGS`, 2238), bounding 13 bands of cells, by at least 72 azimuth columns across a fan around the view direction.

- Sample `terrainY` at each grid vertex, project, and fill each cell as a quad, outermost band first.
- Color each cell from `evalLandscapeColor` at its center, graded, cloud-shadowed, then mixed toward fog by ring distance. Land above 16 m fogs toward a bluer haze than lowlands, so ranges recede.
- A second pass (2331–2381) lays broad washes over the cells, keyed by `hash2i(floor(xm / step), floor(zm / step))`. Mountain cells get one to three faceted dabs along the ridge angle (2360–2370).
- Sea cells take their own fog curve and a vertical gradient between ring fog levels. Sun-glint strokes within 0.24 rad of the sun's azimuth, warmer at golden hour, and moon-glint strokes at night are laid on alternate cells (2296–2310, 2345–2358). These glints are the main painterly cue on open water.
- **Landmark impostors** (2384–2470): from about 102 m to 580 m, towns, lighthouses with a sweeping beam, harbors, aqueducts and vineyards are painted into the far canvas as a few strokes each, with lit windows at night. Landmarks are therefore visible long before the near renderer picks them up at about 220 m.
- The fan widens with pitch (2247–2256), up to a half-angle of 1.38 rad and 132 columns. Looking steeply up or down a hillside, a fixed fan exposes wedges of sky at the screen edges.

**Grid cells are camera-relative.** The grid's azimuths are measured from the camera's yaw, so each cell slides over the land as the view turns. In the genesis the wash's key is world-derived but its position follows the cell. The starter corrects both halves that turning exposes:

- **Washes sit on two world grids**, a 12 m grid out to 140 m and a 30 m grid beyond, every cell painted, bucketed into ring bands for painter's order. Across 110–140 m the fine grid fades out as the coarse one fades in, so walking never pops a ring of paint. Ids pack the grid coordinates, so no two washes in view share a jitter stream.
- **Column azimuths snap to a world-fixed lattice** (`floor((yaw − halfFov) / dAz) * dAz`), so turning in place re-uses the same terrain samples and the silhouette turns rigidly. On ridged relief this cut the pixels changed by a 0.2 rad turn from 2.4% to 0.9%. Walking still resamples the rings, which stay centered on the camera.

**The cache.** Sky and horizon are painted to `farCanvas` and reused until something invalidates them (5471–5479):

- the camera moved more than 0.25 m horizontally or 0.20 m vertically, or turned more than 0.0028 rad
- time of day changed by more than 0.0012, or rain by more than 0.015
- a rare event is active
- three frames have passed

The cache pays only while the camera is nearly still. Walking covers about 0.6 m per painted frame and keyboard turning about 0.16 rad, so either repaints the far layer every frame. At rest the far layer repaints roughly one frame in three, enough for its strokes to breathe. Budget for the moving case.

## 7. The draw list

Canvas 2D has no depth buffer. Everything near is pushed into one array with a sort key and painted back to front (5503–5628).

- **Sort key is depth plus a bias**, not raw depth. Genesis ground quads take `max(cz + 2.2, maxCz + 0.55)`, ground strokes `cz + 0.4`, trees `cz − 0.3`, and a tower `cz − radius` so its nearest face decides.
- **Starter:** ground quads sort at `maxCz + 4.5`, one quad-depth behind their farthest corner. A key based on mean depth fails twice: strokes beyond the quad's center sort beneath it and are covered, and every stroke paints before the next-nearer quad row, whose flat fill then slices the stroke along a straight line. The larger bias fixes both. Its cost is that paint standing within about 4 m behind a crest can show over the crest's front quads, so check a steep ridge after changing terrain scale, and try `maxCz + 2.5` if paint bleeds.
- **Cull before projecting.** Each kind has its own distance cutoff (ground strokes 54 m, anchors 42 m, trees 78 m, churches 135 m) and screen margin. Small things vanish early, large things late.
- **Hand the mid-ground from strokes to washes.** Ground strokes fade out over 34–54 m while each near quad's own washes fade in over camera depth 25–36 m (5705–5742). Quads continue to 76 m and overlap the far layer, which starts at 52 m. The wash rules:
  - a flat quad nearer than about 25 m gets no wash, only its gradient fill and the ground strokes over it
  - beyond 26 m each quad gets one or two broad strokes at alpha 0.44–0.52 and impasto 0.18–0.28, with a position-derived id and hold 4
  - close steep, rock, chalk or snow quads (depth up to 34 m, more than 48×40 px visible) get a clipped grid of 2–6 by 2–6 large strokes, 46–156 px long and 16–44 px wide, at alpha 0.48 and impasto 0.24
  
  Without these the foreground is over-painted or the 34–76 m band lies flat. The starter has the first two rules (`quadWash`): a wash is its own draw-list item sorted at `maxCz + 1`, after the fills of its row and before the paint standing on its quad, and ground strokes fade over 30–44 m as the washes take over. It omits the third rule, the clipped grid on close steep faces: a gorge or cliff scene needs it.
- **Gradient fills.** Under 44 m, each quad's two stored corner colors are graded and cloud-shadowed separately and joined by a linear gradient along the screen diagonal (5685–5701). Water quads build a two-stop shimmer gradient from a sine of time and position. Flat color per quad shows the quad grid near the camera.
- Large objects are split into several items (a pier is nine segments) so they interleave correctly with what passes between their parts.
- Every item paints through one `if (it.kind === ...)` chain. No scene graph, no classes.

Interiors are the one exception to the sort: the building the player stands in is painted after everything else (6286), and inside it furniture gets its own small sorted list (`addProp` / `flushProps`, 3721). See `living-details.md`.

**Grounding objects.** `drawCastShadow3D` (935) projects a ground quad away from the sun, length clamped to 1.1–4.4 times the object's radius, fills it in violet (`[218, 38, 22]`, or `[246, 36, 22]` at golden hour) and adds a soft stroke along the shadow axis. `drawWaterReflection` (968) paints three to seven wobbling horizontal bands under trees near water. Both do much of the work of seating objects on the land, and the starter has neither.

## 8. Color pipeline

Every color reaching the canvas passes through the same chain, in this order:

```
base HSL (palette or landscape function)
  → gradeColor(col, ds)              golden hour, night, rain
  → applyCloudShadow(col, csh, ds)   drifting indigo bands
  → mixHslRgb(col, fogCol, fog)      aerial perspective toward the horizon color
```

The starter's chain is `grade(col, ds)` then `mix(col, ds.fog, fogAt(depth))`, with no cloud shadow.

- **Fog color is the sky's horizon color**, resampled each frame. Distant land therefore dissolves into whatever the sky is doing, at any hour, with no separate tuning.
- `gradeColor` (247) mixes toward `[26, 78, 56]` at `goldenFactor × 0.34`, then toward `[222, 52, max(8, l × 0.36)]` at `nightFactor × 0.74`, then toward `[212, max(12, s × 0.48), l × 0.80]` at `rain × 0.34`. Those weights set how strong dusk and night look.
- **Genesis fog curves differ by kind.** Ground quads: `clamp((cz − 24) / 76, 0, 0.78)` scaled by about 0.76, plus a rain term. Ground strokes: `clamp((cz − 16) / 42, 0, 0.72) × 0.78`. Every other near object: `clamp((cz − 18) / 86, 0, 0.82) × 0.72`. Far cells: by ring distance over 560 m. None reaches 1, so silhouettes survive.
- **Use one fog function for both layers.** Separate near and far curves disagree where the layers meet: in an early starter the near field at 70 m was fogged three times as heavily as the far cells behind it, and the far land showed as a dark band on the horizon. The genesis has the same inversion. The starter now calls one `fogAt(distance)` from both layers.
- **Compositing.** Door light spill and the aurora's full-frame tint use `screen`, the aurora's sky curtain uses `lighter`, and every other glow (sun, moon, halos, window light) is a translucent source-over fill.

Skipping the chain for even one object type is immediately visible: that object stays noon-bright at dusk.

## 9. Day state

`sampleDayState(tod, t)` (211) is called once per frame and returns everything lighting-related: four sky colors interpolated between five keyframes (`SKY_KEYS`, line 204: midnight, dawn, noon, dusk, midnight) with a smoothstep ease, cloud highlight and shadow colors, the fog color, and four scalars.

| Scalar | Formula | Drives |
|---|---|---|
| `sunElev` | `−cos(tod · 2π)` | Sun and moon position |
| `dayFactor` | `clamp((sunElev + 0.25) / 1.05)` | Cloud shadow strength, birds, wind highlights |
| `nightFactor` | `clamp((−sunElev + 0.12) / 0.85)` | Night grade, stars, fireflies, window glow |
| `goldenFactor` | `max(0, 1 − |sunElev| / 0.42) × (1 − rain × 0.55)` | Warm grade, sun glints on water |

The full cycle is 240 s. Rain enters here too: it pulls all four sky colors toward slate before anything else reads them, so the whole pipeline grays out from one place.

## 10. Post

Two full-screen passes with `globalCompositeOperation = 'multiply'` (6307–6319):

1. A 48 px tiling pattern of 1 px lines every 3 px at about 5% opacity: canvas weave. Applied twice indoors.
2. A radial vignette from transparent at 34% of width to a warm brown at 72%, deep blue at night. The starter interpolates the vignette color by the night factor so it does not switch on one frame.

Both are cheap. The weave gives every stroke a shared substrate, and without it the image reads as vector shapes.

## 11. Budgets

The unit throughout is calls to `CanvasRenderingContext2D.prototype.stroke`, the canvas method. One brushstroke (the starter's `stroke()` function, the genesis's `paintedStroke`) costs one to five of them.

Fixed by the genesis constants:

| Quantity | Value |
|---|---|
| Chunks built around the player | 49 (7×7 of 24 m), up to 81 retained |
| Ground quads per chunk | 36 |
| Ground strokes per chunk | 250 plus shoreline extras (0.43 per m²) |
| Far-layer terrain samples per repaint | 14 rings × 73 columns = 1,022, up to 14 × 133 when pitched |

Measured over four seconds in headless Chromium at DPR 1, and reproduced independently in review:

| Scene | Context `stroke()` per frame | `fill()` per frame |
|---|---|---|
| Genesis, `?at=meadow`, at rest | ~13,000–13,600 | ~820–870 |
| Genesis, `?at=town`, at rest | ~17,600 | ~1,800 |
| Genesis, walking forward from meadow | ~18,800 | ~1,560 |
| Starter, default view | ~8,500 with the far layer repainting | ~940 |

Both held their 12 fps repaint at those counts. Design within **20,000 context stroke calls per painted frame while moving**, and re-measure after adding content. The starter does this itself: open it with `?stats=1` and read `window.__paintStats` (`{ frame, stroke, fill }` for the last painted frame). Walk or turn while measuring, since the far layer repaints every frame only while the camera moves.

The levers when a scene runs slow, in order of effect: ground-stroke distance cutoff, strokes per chunk, far-grid resolution, DPR.

## 12. Failure modes

| Symptom | Cause |
|---|---|
| Polygons explode into screen-filling wedges underfoot | Projecting without near-plane clipping. Use `clipPoly` (genesis `projectClippedPoly`) for anything the camera can stand on or inside |
| Sky visible through the ground at the edge of the chunk radius | Far grid's innermost ring starts beyond the near field's reach. They must overlap |
| Dark or light band where near ground meets the horizon | Near and far layers use different fog curves |
| Ground strokes sliced along straight horizontal lines | Ground quads sorted on mean depth instead of behind their farthest corner |
| Visible grid of flat tiles near the camera | One flat color per quad instead of a corner-to-corner gradient |
| Hard line where brushwork ends | No distance fade on ground strokes, or no quad washes to take over |
| Object stays bright at night | Color bypassed the grade |
| Horizon washes slide or blink when turning | Washes positioned on the camera-relative grid instead of a world grid |
| Stutter every few seconds while walking | Chunk eviction radius equal to load radius, or `buildChunk` doing per-frame work |
| Trees visible through hills | Sort bias on ground quads too small, or tree culled by distance later than the hill's quads |
| Far layer repaints every frame at rest | A cache key that changes continuously (time `t` in place of `tod`), or a rare event left active |
| Player stuck after a URL spawn | Spawned in deep water with a move rule that only accepts shallow destinations. Always accept a move that does not go deeper |
