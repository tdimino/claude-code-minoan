# Tunnel Patterns — Mode 3 Anatomy

Architectural map of `assets/tunnel-gallery-source.html`. The source is a vanilla port of [thebuggeddev/Infinitor](https://github.com/thebuggeddev/Infinitor) — React Three Fiber stripped, rendering logic preserved verbatim, extended with keyboard scroll, drift-to-stop signature moment, phosphor-vigil FX hook, and a sentinel injection point so `image-well --format tunnel` can populate it with search results.

## 1. HTML/CSS Structure

**What it does**: Full-viewport canvas with minimal chrome — theme toggle button (top-right), scroll hint (bottom-left), WebGL fallback modal (hidden unless triggered).

**Pattern**: The tunnel is the content. Unlike Mode 1 (Instance), there's no phase text, no progress bar, no author's note — the corridor itself is the experience. Overlays stay under `z-index: 3` so nothing covers the canvas center. `body.light` modifier class inverts the button palette for light theme without recomputing CSS.

**Adaptation**: Add overlays sparingly. If you need labels for images, attach them to individual meshes, not the HTML layer — they need to move with the camera.

## 2. Config Block

**What it does**: Single top-level `CONFIG` object holds every tunable parameter. Defaults mirror Infinitor exactly.

**Pattern**: Flat object, no nesting. `imageSource` is a function (callable, returns URL for a random seed). `images` is a separate array that takes precedence when non-null. This split lets the template run in three modes:

1. **Seed mode** (default) — `images: null`, `imageSource` called per spawn with a random seed
2. **Manifest mode (inline)** — `images: ["url1", "url2", ...]` set at build time
3. **Injection mode** — the `IMAGE_MANIFEST` const below is rewritten by `image-well --format tunnel`

**Adaptation**: Override any knob by editing CONFIG. For a branded gallery, set `theme: 'light'` and supply a custom `imageSource` that points at a specific API.

## 3. Sentinel Injection Point

**What it does**: A literal comment block in the source file that `image-well` can find and replace with an `IMAGE_MANIFEST` array.

**Pattern**:
```javascript
// ═══════════════════════════════════════════════════════════════
// IMAGES_INJECTION_POINT
// Leave this sentinel in place. `image-well --format tunnel` will
// replace the next line with `const IMAGE_MANIFEST = [...];`
// ═══════════════════════════════════════════════════════════════
images: null,
```

The `IMAGE_MANIFEST` const is declared just below CONFIG and defaults to `null`. The `image-well` bridge greps for `const IMAGE_MANIFEST = null;` and swaps it for the real manifest. The `nextUrl()` method checks `IMAGE_MANIFEST` first, then falls back to `CONFIG.images`, then to `CONFIG.imageSource(seed)`.

**Adaptation**: Never delete the sentinel or rename `IMAGE_MANIFEST` — that breaks the image-well bridge.

## 4. Path Generator

**What it does**: Infinite procedural 3D path. Each control point advances the previous position by `POINT_SPACING` (20 units) along a direction defined by mutating yaw/pitch with small random walks, plus occasional roll kicks (15% chance per point).

**Pattern**: Module-level state (`pathPoints`, `pathYaw`, `pathPitch`, `pathPos`, `pathUp`) acts as a lazy generator. `generateNextPoint()` extends `pathPoints` by one; `getInterpolatedData(d)` looks up the index, calls `generateNextPoint()` if needed, then Catmull-Rom-interpolates position and linearly interpolates dir/up/right.

The seed loop `for (let i = 0; i < 200; i++) generateNextPoint();` ensures the first 200 points exist before the first frame.

**Key math**:
- `dir = vec3(sin(yaw)*cos(pitch), sin(pitch), -cos(yaw)*cos(pitch))` — standard spherical
- `right = cross(dir, up)` — needs fallback for singular case (`lengthSq < 0.01`)
- `up = cross(right, dir)` — orthonormal basis
- Catmull-Rom uses `[i-1, i, i+1, i+2]` as the 4 control points, clamped at the start

**Adaptation**: Tune `POINT_SPACING` for wider corridors. Increase yaw/pitch variance for tighter turns. The roll kicks are what make the corridor feel organic — disable them for a calmer ride.

## 5. Tunnel Mesh

**What it does**: Procedural buffer geometry with `(segs+1) * 5` vertices per frame. 5 vertices per ring (4 corners + closing repeat of v0 so UVs wrap). Index buffer is static (precomputed once in `createTunnel`).

**Pattern**:
- **Rebuilt in-place every frame**: `updateTunnel()` overwrites the position and UV arrays, never reallocating. `position.needsUpdate = true` + `uv.needsUpdate = true` flush to GPU.
- **Window centered on camera**: Rings from `currentDist - 50` to `currentDist + 600`. The 50-unit tail prevents visible pop-in when you reverse.
- **UV.x**: `j * 0.25` (0, 0.25, 0.5, 0.75, 1.0) — wraps around the 4 walls.
- **UV.y**: `d / 4.0` — denser lengthwise, matches Infinitor's `gridScale = (20.0, 1.0)` so the grid squares look square in perspective.
- **Shader**: custom GLSL, not built-in. `min(lineX, lineY)` picks the closer edge; `smoothstep` produces the grid line with a glow falloff; `smoothstep(fogStart, fogEnd, vDepth)` fades distant lines into `bgColor`. `side: THREE.BackSide` so we see the inside of the tube.

**Adaptation**: Replace the shader with a different pattern (diagonal, dots, text glyphs) by swapping the fragment shader body. Keep the vertex shader and vDepth varying intact — the fog falloff is critical for the sense of distance.

## 6. Image Manager

**What it does**: Spawns flat image quads on the four walls of each "cell" (4-unit stride along the path). Culls images behind the camera to free GPU memory. Selects URLs from the manifest, the static images array, or the seed function in that priority order.

**Pattern**: Class with module-level `lastGeneratedDist` state. `update()` advances generation until `currentDist + 500`; culls from the tail when `image.distance < currentDist - 50`. Per-ring spawn probability is `CONFIG.imageDensity` (0.6); when a ring fires, 1–3 images spawn on unique `(wallIndex, cellOffset)` slots.

**Image geometry**: 4×4 quad mesh (not a simple plane — the vertices follow the path's right/up basis so images curve naturally when the tunnel bends). Each vertex is placed by:
1. Interpolating the path at `distance ± halfSize`
2. Offsetting along `up` (wall 0/2) or `right` (wall 1/3) by `radius - 0.05` to avoid z-fighting
3. Lateral offset by `cellOffset * 4 - halfSize + xd * size`

**Cleanup discipline**: On cull, the mesh is removed from the scene AND its geometry + texture + material are disposed. Without this, picsum seeds leak GPU memory over a long session.

**Adaptation**: Increase `maxImagesPerRing` for denser galleries. Change the 4×4 subdivision to a flat plane (2×2) if your images don't need to curve with the tunnel.

## 7. Camera & Scroll

**What it does**: Camera sits on the path at `currentDist`, looks 10 units ahead at `currentDist + 10`. Scroll input (wheel + touch + keyboard arrows) modifies `targetDist`; `animate()` lerps `currentDist` toward it every frame.

**Pattern**: Two-variable smooth scroll — `targetDist` is what the user's input asked for, `currentDist` is what the camera has actually reached. The `scrollEasing` factor (0.08) controls how quickly the camera catches up; lower values create a creamier ride, higher values make it snappier.

**Keyboard**: arrow up/left subtracts step, arrow down/right adds. Accessibility addition not present in Infinitor.

**Adaptation**: For a slower, more meditative ride, drop `scrollSpeed` to 0.08 and `scrollEasing` to 0.05. For a kinetic ride, raise to 0.3 / 0.15.

## 8. Phosphor Vigil FX Integration

**What it does**: Optional post-processing pipeline. When `CONFIG.fx === 'phosphor-vigil'`, a `PhosphorVigil` instance is constructed in `init()` and used as the render entry point in `animate()`.

**Pattern**: Single flag controls the branch. Scroll velocity is fed into `sharedVelocity` and passed to `fx.setVelocity()` so the RGB trails align with camera motion — faster scroll = longer chromatic trail. The velocity is scaled by 0.003 to bring dist-space into the UV-space units the feedback shader expects.

**Adaptation**: Set `fx: 'phosphor-vigil'` in CONFIG for the CRT look. Adjust the `0.003` velocity scale if trails look too subtle or too smeared.

## 9. Validator Contract

`scripts/validate_tunnel.py` regex-checks the source for every required element from sections 2–8 above. If you rename `IMAGE_MANIFEST`, delete the sentinel, or stop using `PerspectiveCamera`, it will fail. That's intentional — the validator is the guardrail for the image-well bridge.

## Anti-Patterns

- Never use React/Vue — vanilla ES modules only
- Never allocate tunnel geometry in the animate loop — mutate the existing BufferAttributes
- Never skip texture disposal on image cull — GPU memory leaks accumulate fast on long sessions
- Never use pure black background — `#050508` dark, `#fafafa` light
- Never rename the sentinel comment or the `IMAGE_MANIFEST` const — the image-well bridge depends on them
- Never call `renderer.render()` directly when `fx` is active — route through `fx.render()`
- Never use `THREE.Geometry` — always `BufferGeometry`
