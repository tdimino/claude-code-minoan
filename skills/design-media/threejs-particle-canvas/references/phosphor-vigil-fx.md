# Phosphor Vigil — Shared CRT Post-Processing Pipeline

`assets/phosphor-vigil.js` — a 4-pass pipeline used by Modes 3 (tunnel) and 4 (specimens), and importable standalone into any Three.js project. All four fragment shaders are ported verbatim from `celescript.dev/experiments/3d-butterfly` (`ButterflyScene`, chunk `128.64bb229c36552b0d`). Every shader constant is preserved — the aesthetic is recognizable exactly because the constants are exactly right.

## Why a shared module

Two independent modes needed post-FX; we could have inlined the shaders in each template. Doing so would have lost the single source of truth. The CRT look is **identity**, not decoration — every mode that uses it should render through the same `PhosphorVigil` instance, so tweaking one knob anywhere propagates coherently. The module also stays portable: drop the file into World War Watcher's Vector Ghost Protocol work and the exact same aesthetic appears without re-deriving a single shader line.

**Anti-pattern**: Never embed the phosphor-vigil shaders inline in a new template. Import them. If you need to tune them per-mode, pass constructor options.

## Pipeline

Five render stages, one forward flow, two ping-pong targets:

```
scene ─▶ rtScene
           │
           └─▶ Feedback (ping-pong A↔B, reads previous frame)
                  │
                  ├─▶ Threshold ──▶ Blur ──▶ rtBloomBlur
                  │                             │
                  └─────────────────────────────┴─▶ Composite → screen
```

### Pass 0 — Scene render

`renderer.render(scene, camera)` into `rtScene`. The only pass that needs `depthBuffer: true`. Everything downstream is a fullscreen triangle.

### Pass 1 — Feedback trail (ping-pong)

Reads the live scene frame AND the previous feedback frame, RGB-shifts the previous frame along velocity, and composites them. Three per-channel UV offsets:

- **R**: velocity × +0.22  + perpendicular × +0.09
- **G**: unchanged (center)
- **B**: velocity × −0.22  + perpendicular × −0.09

This is what creates the directional chromatic trails. The perpendicular spread (`vec2(-vel.y, vel.x) * 0.09`) adds lateral bloom so fast-moving bright points smear into a streak rather than a line.

**Brightness clamp**: `if (trailMax > 0.85) trailFaded *= 0.85 / trailMax`. Without this, overlapping R+G+B trails where all three channels align sum to white and burn out. The clamp preserves iridescence even under high feedback.

**Iridescent tint**: `0.5 + 0.5 * cos(6.28318 * (phase + vec3(0.0, 0.33, 0.67)))`. Phase-shifted RGB cosines create an oil-slick rainbow that drifts with `uTime` and `length(vUv - 0.5)`. Only applied to the trail (not the live frame), and only when `trailAmount > 0.02` — so edges of stationary shapes don't shimmer.

**Ping-pong**: After each render, the source and destination render targets swap. Next frame, the just-written target becomes the new "previous" frame.

### Pass 2 — Bloom threshold

```glsl
float brightness = max(max(color.r, color.g), color.b);
float soft = smoothstep(uThreshold - 0.1, uThreshold + 0.2, brightness);
```

Smoothstep (not step) so the bloom doesn't clip at the threshold boundary. The 0.1/0.2 asymmetry keeps the lower edge soft but the upper edge biased toward brighter pixels.

### Pass 3 — Bloom blur

Single-iteration 4-tap box blur at `uOffset + 0.5` offset corners. This is deliberately cheap — not a proper separable Gaussian. The feedback trail already does most of the glow work; this pass exists to soften the thresholded bloom before the composite adds it back.

### Pass 4 — CRT composite

The signature pass. Applied in this order:

1. **Barrel distortion** — `uv + cc * dot(cc,cc) * uBarrelDistortion`. Pixels outside the unit square are clamped to black (the curved edge of the virtual CRT).
2. **Chromatic aberration** — R/G/B sampled from three offset UVs along the dir-from-center vector. `length(dir) * uAberrationStrength` means more aberration at the edges, matching real optics.
3. **Bloom add** — `color += bloom * uBloomIntensity`.
4. **Dual-frequency scanlines** — fine (1.5× resY) modulated by coarse (0.25× resY). The fine lines are the CRT raster; the coarse envelope is the subtle horizontal banding real CRTs exhibit.
5. **RGB subpixel columns** — `mod(gl_FragCoord.x, 3.0)` split into three smoothstep masks. This is the physical shadow mask simulation — adjacent pixel columns glow slightly different colors like on a trinitron.
6. **Vignette** — `pow(uv.x*(1-uv.x) * uv.y*(1-uv.y) * 15.0, 0.25)`. Multiplicative, darker edges.
7. **Dual-frequency flicker** — 8 Hz slow pulse + 60 Hz fast jitter. Multiplicative. The slow component is what the eye reads as "tube warmth", the fast component is organic noise.
8. **Phosphor glow** — `color += color * brightness * 0.18`. Self-bloom that brightens bright pixels further, mimicking the way real phosphor excites itself.
9. **Grain** — hash-based noise at `uTime * 100.0` drift. Additive.
10. **Phosphor tint** — `color *= vec3(0.95, 1.0, 0.92)`. Slight green bias, warm falloff on red and blue. This is the green-gun dominance of classic phosphors.

## Integration pattern

```js
import * as THREE from 'three';
import { PhosphorVigil } from './phosphor-vigil.js';

const renderer = new THREE.WebGLRenderer({ antialias: true });
const fx = new PhosphorVigil(renderer, {
    width: window.innerWidth,
    height: window.innerHeight,
});

// In your animate loop:
function animate() {
    requestAnimationFrame(animate);
    const t = clock.getElapsedTime();

    // Optional: feed a velocity vector so the trails track motion
    fx.setVelocity({ x: sceneVelocity.x, y: sceneVelocity.y });

    // Replaces renderer.render(scene, camera)
    fx.render(scene, camera, t);
}

// On resize:
window.addEventListener('resize', () => {
    const w = window.innerWidth;
    const h = window.innerHeight;
    renderer.setSize(w, h);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    fx.setSize(w, h);
});
```

The host **must not** call `renderer.render(scene, camera)` — `fx.render()` is the replacement entry point.

## Configurable knobs

All exposed via constructor options. Defaults match celescript exactly.

| Knob | Default | Range | Effect |
|---|---|---|---|
| `feedbackStrength` | 0.90 | 0.5–0.98 | Trail persistence per frame |
| `bloomThreshold` | 0.55 | 0.3–0.9 | Brightness cutoff for bloom |
| `bloomIntensity` | 0.35 | 0.0–1.0 | Additive bloom mix in composite |
| `aberrationStrength` | 0.006 | 0.0–0.02 | Chromatic offset magnitude |
| `flickerAmount` | 0.02 | 0.0–0.08 | Slow flicker depth |
| `grainAmount` | 0.06 | 0.0–0.15 | Film grain depth |
| `barrelDistortion` | 0.18 | 0.0–0.40 | CRT curvature |
| `phosphorTint` | `[0.95, 1.0, 0.92]` | hex triplet 0..1 | Warm/green RGB multiplier |
| `pixelRatioCap` | 2.0 | 1.0–3.0 | Max device pixel ratio |

## Per-mode defaults

- **Mode 3 (tunnel)** — `fx: "phosphor-vigil"` is optional. When enabled, the scroll velocity feeds `setVelocity()` so the trails align with camera motion. Consider lowering `feedbackStrength` to 0.85 if the corridor grid looks too ghostly.
- **Mode 4 (specimens)** — `fx: "phosphor-vigil"` is ON by default. The shared `Specimen` velocity channel feeds `setVelocity()` directly. The trails are the point of the scene — don't disable them casually.

## Adaptation

To add a new mode that uses the pipeline: import the module, construct an instance after creating your renderer, call `fx.render(scene, camera, elapsedTime)` in the animate loop instead of `renderer.render`, and call `fx.setSize()` in your resize handler. No shader changes required — everything is tunable via constructor options. If you genuinely need a different shader, open a second FX module (e.g. `phosphor-vigil-light.js`) rather than forking this one in-place.

## Anti-patterns specific to this pipeline

- Never call `renderer.render(scene, camera)` directly when `PhosphorVigil` is active — you'll bypass the pipeline and draw to screen without effects
- Never construct multiple `PhosphorVigil` instances sharing one renderer — the render targets collide
- Never forget `fx.setSize()` in your resize handler — stale RT dimensions cause blurring and scanline banding
- Never pass velocity magnitudes larger than ~1.5 UV units — the trail streak becomes discontinuous
- Never embed the shader source inline in a new template — import the module
