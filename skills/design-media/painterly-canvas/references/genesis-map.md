# Genesis Map

A line index of `assets/genesis/endless-painted-world.html`: 7,397 lines, 470 KB, one `<style>` block, one IIFE `<script>` (lines 35–7395), 158 top-level functions.

Do not read the file whole: it is roughly 130,000 tokens, and the CSS on line 22 alone is 4,500 characters. Read by `offset` and `limit` from the ranges below, or grep for a function name. Line numbers are exact for the checksummed copy recorded in `assets/genesis/PROVENANCE.md`. If the checksum does not match, regenerate this index with the grep at the foot before trusting any number here.

## Name map: starter to genesis

Work happens in the starter, and the references cite the genesis. The same concept has two names.

| Concept | Starter | Genesis |
|---|---|---|
| Brushstroke | `stroke` | `paintedStroke` (876) |
| Jitter hash | `jitter`, `hash` | `epochHash` (117), `hash2i` (86) |
| Seeded generator | `rng` | `mulberry32` (76) |
| Noise | `noise`, `fbm` | `valueNoise2D` (91), `fbm2` (104) |
| Project a point | `project` | `project3D` (739) |
| Near-clip and project a polygon | `clipPoly` | `projectClippedPoly` (745) |
| Day state | `dayState` | `sampleDayState` (211) |
| Grade | `grade` | `gradeColor` (247) |
| RGB mix of HSL colors | `mix` | `mixHslRgb` (173) |
| Color to CSS string | `css` | `colStr` (823), `hslaStr` (182) |
| Height | `height`, `groundY` | `terrainY` (507), `groundY` (586) |
| Land color | `landColor` | `evalLandscapeColor` (2214) |
| Chunk build and streaming | `buildChunk`, `ensureChunks` | `buildChunk` (1639), `ensureChunksAround` (1943) |
| Far layer | `renderFar`, `RINGS` | `renderSky` (2027) + `renderFarHorizon` (2242), `FAR_RINGS` |
| Frame painter | `render` | `renderWorld` (5465) |
| Paint step | `STEP` | `STEP_SEC` (6363) |
| Fog | `fogAt(distance)` | Inline per kind in `renderWorld` |

## Sections

| Lines | Section | Read it for |
|---|---|---|
| 1–34 | Head, CSS, DOM | Fixed-aspect stage, touch nav pad, mobile media queries |
| 36–59 | Surfaces | Three canvases, DPR rule, `FOCAL`, the `farCache` record |
| 71–190 | Math and color utilities | `mulberry32`, `hash2i`, `valueNoise2D`, `fbm2`, `ridged2`, `epochHash`, HSL/RGB mixing |
| 192–202 | Linen pattern | The 48 px weave tile |
| 204–259 | Day state | `SKY_KEYS`, `sampleDayState`, `gradeColor` |
| 261–312 | Atmosphere | Rain schedule, `cloudShadowAt`, `applyCloudShadow`, `windWaveAt`, water ripples |
| 314–337 | Interaction state | `interactState`, `EASEL_PALETTE` |
| 339–473 | Macro geography | Sea and mountain fields, LRU, `ORIGIN_FEATURES`, `getRegionFeature`, `nearestFeature` |
| 475–602 | Terrain | `isOnPath`, `biomeAt`, `terrainY`, `groundY`, pier decks |
| 604–714 | Enterable-building lookup and surfaces | `getActiveInterior`, `walkSurfaceY`, `surfaceAt` |
| 717–874 | Camera and 2D helpers | `makeFPCamera`, `project3D`, `projectClippedPoly`, `withClippedPoly`, gradients, `makeRoomTransform`, `cylGrad` |
| 876–932 | **Stroke engine** | `paintedStroke`, `drawPaintedSegment` |
| 934–1085 | Painterly effects | Cast shadows, water reflections, light spill, chimney smoke, ripples, rain streaks |
| 1087–1636 | Palettes, trees, landmarks | `CHUNK_SIZE`, palette arrays, `makeTreeObj`, `buildLandmark` (towns, harbors, aqueducts, vineyards, alpine passes) |
| 1638–1958 | Near chunks | `buildChunk`, `ensureChunksAround` |
| 1960–2212 | Sky | Sky strokes, clouds, stars, birds, petals, `projSkyDir`, `renderSky` |
| 2214–2471 | Far horizon | `evalLandscapeColor`, `FAR_RINGS`, `renderFarHorizon`, landmark impostors (2384–2470) |
| 2473–2646 | Simple house exteriors | `drawPaintedBuilding`: non-enterable townhouses and cottages only |
| 2648–3069 | Interior brushwork | `paintFastDab`, `paintRoundDab`, `makeBrokenPalette`, halos, fire, bottles, vases, sacks, window light, curtains |
| 3071–3192 | Painted geometry | `drawPaintedPoly3D`, `drawBox3D` |
| 3194–3573 | Wall art and walls | `paintArtSubject`, `paintWallTapestry3D`, `emitWallWithOpenings` |
| 3575–3770 | Room scaffolding | Church campanile, `makeRoomCtx`, room constants, `buildOpenings` |
| 3772–4913 | Enterable building | `drawEnterableBuilding`: pass 1 shell (3813), pass 2 furniture (4131), pass 3 exterior (4835) |
| 4915–5206 | Round rooms | Lighthouse interior and lantern room, windmill interior |
| 5208–5463 | Vehicles | Rowboat cockpit, parked bicycle, bicycle cockpit |
| 5465–6320 | **Main renderer** | `renderWorld`: far cache (5471), gather (5493), sort (5628), per-kind painting (5666), interior last (6286), post (6307) |
| 6322–6399 | Presets and player | `PRESETS`, `STEP_SEC`, `DAY_CYCLE_SEC`, player state |
| 6401–6813 | Input | Boats, bikes, `pickInteractiveTarget`, `handleWorldClick`, touch and nav pad |
| 6815–6893 | Collision and rare events | `hitsRotatedBox`, `hitsEnterableBuilding`, `hitsStructure`, rare-event setup |
| 6895–7082 | Simulation | `updateRareEvents`, `updatePhysics` |
| 7084–7099 | Frame entry | `drawCurrent` |
| 7101–7364 | Audio | `initAudio`, one-shot helpers, `updateAudio` |
| 7366–7394 | Loop and boot | `loop`, the `?frame` branch |

## Where to look for a technique

| Wanting to build | Read |
|---|---|
| The brushstroke itself | 876–932, then 2688–2753 for the cheaper variants |
| Ground that looks painted | 1696–1740 (stroke seeding), 5667–5762 (quad fills, quad washes and stroke painting) |
| Plants that sway | 1742–1776 (anchors), 5767–5813 |
| A tree | grep `makeTreeObj`, then `it.kind === 'tree'` in `renderWorld` |
| A distant mountain range | 362–382, 2214–2236, 2242–2382 |
| Distant towns and lighthouses on the horizon | 2384–2470 |
| A simple house exterior | 2474–2646 |
| The exterior of an enterable building, church or chalet | 4835–4913 (pass 3) |
| A room to walk into | 3686–3770, then the first 200 lines from 3772 |
| Interior wall brushwork | `paintWallTapestry3D` 3359 |
| A cylinder (tower, mill) | `cylGrad` 835, `drawCircularRoomShell` 4915 |
| Fire, lamplight, halos | 2766–2866, 989–1016 |
| Cast shadows and water reflections | 935–987 |
| Water: ripples, foam, glints | 1034–1055, shore strokes 1727–1740, far-sea glints 2345–2358 |
| Day and night | 204–259, `renderSky` 2027 |
| Click targets | grep `lastClickPts.push`, then 6559–6676 |
| A new prop in a town or landmark | Follow `lm.fountains` end to end: `addFountain` 1214 (data), 1243 (placement in the home town), gather 5587, `it.kind === 'fountain'` (paint), `hitsStructure` 6858 (collision) |
| A vehicle with its own physics | 6434–6552, 6963–7040, 5208–5463 |
| Any sound | 7119–7364 |

## Regenerating the index

```bash
grep -n -E '^\s*// ---' assets/genesis/endless-painted-world.html
grep -n -o -E '^function [A-Za-z0-9_]+\([^)]*\)' assets/genesis/endless-painted-world.html
```

## Reading notes

- The file is machine-dense: one-letter locals, long lines, heavy inline constants. Read for structure and tuning values, and write fresh code in the target project's style in place of transplanted blocks.
- Nearly every drawing function takes the same leading arguments: `(gctx, cam, ..., ds, fogCol, fog, id, frame)`. Recognizing that signature makes the rest legible.
- Colors are `[h, s, l]` arrays with h in degrees and s, l in 0–100, converted to strings only at the canvas call.
- World units are meters, +Y is up and yaw 0 looks along +Z.
- `random` is destructured from `Math` on line 44, so `grep Math.random` finds nothing. Bare `random()` appears in simulation and audio only (from line 6887 on), never in painting. Grep `random()` when auditing for draw-time randomness.
- The comment above `drawPaintedBuilding` (2473) says "townhouse / chalet / church exterior". It is stale: chalets, churches and every enterable building are drawn by `drawEnterableBuilding`.
