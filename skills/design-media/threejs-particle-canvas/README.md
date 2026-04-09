# threejs-particle-canvas

Generate interactive Three.js canvases as self-contained HTML files in four modes: narrative particle phase cycles, parametric curve spinners/loaders, infinite scrollable image tunnels, and behavior-driven glTF specimen scenes. All modes can render through a shared CRT post-processing pipeline (Phosphor Vigil) that is also importable standalone into any Three.js project.

Each generated file is a single offline-runnable HTML page — no build step, no framework, no bundler. Vanilla ES modules with an import map pointing to Three.js r175 from jsdelivr.

## When to Use

Whenever a project needs an ambient WebGL/WebGPU canvas, a polished loading spinner, an infinite scroll gallery, or a flying-creature scene. Fills the gap between "ad-hoc Three.js boilerplate" and "fully bundled creative coding project."

## Modes

| Mode | Source | Output |
|---|---|---|
| **1. Narrative Canvas** | `assets/instance-source.html` | Particle phase cycles with geodesic lattices, orbital camera, ambient WebGL effects. Built around named phases ("lattice", "void", "awakening") with phase-driven update functions. |
| **2. Spinner / Loader** | (algorithmic) | Parametric curve particle trails via Three.js WebGPU + TSL. 9 curve types: lemniscate, rose, spirograph, Lissajous, circle, triskelion, heart, sphere, spiral. ES module or HTML output. |
| **3. Infinite Gallery Tunnel** | `assets/tunnel-gallery-source.html` | Scroll-driven procedural corridor with images embedded on the four walls of each tunnel cell. Catmull-Rom path generator, custom wireframe-grid GLSL shader, lazy ring-based image spawning. Vanilla port of [thebuggeddev/Infinitor](https://github.com/thebuggeddev/Infinitor). |
| **4. Living Specimens** | `assets/butterfly-specimen-source.html` | Three glTF creatures (butterflies, parrots, fish) with flight physics — `followMouse` and `wander` behaviors, soft-wall repulsion, velocity-modulated wing-flap speed. Vanilla port of [celescript.dev/experiments/3d-butterfly](https://celescript.dev/experiments/3d-butterfly). |

## Shared FX: Phosphor Vigil

`assets/phosphor-vigil.js` — a 4-pass post-processing ES module that both Mode 3 and Mode 4 import, and that can be dropped into any other Three.js project as a standalone CRT pipeline.

| Pass | What it does |
|---|---|
| 1. Feedback trail (ping-pong) | Per-channel UV offset by velocity (R trails forward, B backward, G center) + perpendicular spread + iridescent oil-slick tint. Brightness clamp prevents R+G+B sum-to-white. |
| 2. Bloom threshold | Smoothstep brightness extraction. |
| 3. Bloom blur | 4-tap box blur, single iteration. |
| 4. CRT composite | Barrel distortion, chromatic aberration, dual-frequency scanlines, RGB subpixel shadow mask, vignette, dual-frequency flicker, phosphor glow, hash-noise grain, warm/green phosphor tint. |

Every shader constant is preserved verbatim from the celescript butterfly bundle — the exact values define the aesthetic signature.

```js
import { PhosphorVigil } from './phosphor-vigil.js';

const fx = new PhosphorVigil(renderer, { width, height });
// replaces renderer.render(scene, camera) in the animate loop:
fx.setVelocity(sharedVelocity);
fx.render(scene, camera, elapsedTime);
```

Configurable via constructor options: `feedbackStrength`, `bloomThreshold`, `bloomIntensity`, `aberrationStrength`, `flickerAmount`, `grainAmount`, `barrelDistortion`, `phosphorTint`. Defaults match celescript exactly.

## Structure

```
threejs-particle-canvas/
├── SKILL.md                              # Skill definition, mode docs, anti-patterns
├── README.md                             # This file
├── assets/
│   ├── instance-source.html              # Mode 1: narrative particle canvas (1,192 lines)
│   ├── tunnel-gallery-source.html        # Mode 3: infinite gallery tunnel
│   ├── butterfly-specimen-source.html    # Mode 4: living specimens
│   └── phosphor-vigil.js                 # Shared CRT FX module (importable standalone)
├── references/
│   ├── instance-anatomy.md               # Mode 1 source map
│   ├── particle-patterns.md              # Mode 1 particle systems
│   ├── phase-engine.md                   # Mode 1 phase state machine
│   ├── camera-and-input.md               # Mode 1 spherical camera
│   ├── atmosphere.md                     # Mode 1 fog/stars/threads
│   ├── design-references.md              # Aesthetic reference (Instance, Vellum)
│   ├── spinner-patterns.md               # Mode 2 architecture
│   ├── parametric-curves.md              # Mode 2 curve formulas
│   ├── tunnel-patterns.md                # Mode 3 anatomy (path gen, ring spawn)
│   ├── specimen-patterns.md              # Mode 4 anatomy (physics, glTF)
│   └── phosphor-vigil-fx.md              # Shared FX pipeline reference
└── scripts/
    ├── validate_canvas.py                # Mode 1 validator
    ├── validate_spinner.py               # Mode 2 validator
    ├── validate_tunnel.py                # Mode 3 validator (21 checks)
    └── validate_specimen.py              # Mode 4 validator (25 checks)
```

## Usage

### Mode 1 — Narrative canvas

```bash
/threejs-particle-canvas the lifecycle of a star — nebula collapse, ignition, main sequence, red giant, supernova, remnant
```

Produces a self-contained HTML file with phase cycles, geodesic lattice, particles, star field, and orbital spherical camera.

### Mode 2 — Spinner

```bash
/threejs-particle-canvas spinner — infinity loop loading indicator with breathing animation
```

Produces an ES module or HTML wrapper with particle-trail spinner using TSL on WebGPU.

### Mode 3 — Infinite gallery tunnel

```bash
/threejs-particle-canvas tunnel — infinite scrollable gallery of Aegean frescoes
```

Produces a vanilla port of Infinitor with keyboard scroll, drift-to-stop signature moment, and optional phosphor-vigil FX. Image source defaults to `picsum.photos` seed mode; override via the `IMAGE_MANIFEST` sentinel injection (used by `image-well --format tunnel`).

### Mode 4 — Living specimens

```bash
/threejs-particle-canvas butterfly — three emerald and amber moths chasing the cursor through a scanline void
```

Produces a glTF specimen scene defaulting to Three.js's `Parrot.glb` (CC0, served via jsdelivr). Swap `modelUrl` for any rigged glTF/glb. Phosphor-vigil FX is on by default — the trails are the soul of the scene.

## Validators

```bash
python3 scripts/validate_canvas.py output.html       # Mode 1
python3 scripts/validate_spinner.py output.{js,html} # Mode 2
python3 scripts/validate_tunnel.py output.html       # Mode 3 (21 checks)
python3 scripts/validate_specimen.py output.html     # Mode 4 (25 checks)
```

The Mode 3 and Mode 4 validators include anti-pattern checks: presence of React/JSX/drei imports or pure-black backgrounds (`#000`) cause hard fails. Both also verify the `phosphor-vigil` FX module hookup and the structural pieces (path generator, spawn loop, glTF loader, mouse unproject, etc.).

## image-well Bridge

The `image-well` skill ships a `--format tunnel` output that pipes search results directly into the Mode 3 template:

```bash
uv run ~/.claude/skills/image-well/scripts/well.py search "Minoan fresco" \
    --preset museum --license cc0 \
    --format tunnel --output minoan-corridor.html
open minoan-corridor.html
```

The bridge:
1. Reads `assets/tunnel-gallery-source.html` from this skill
2. Replaces the `// IMAGES_INJECTION_POINT` sentinel `const IMAGE_MANIFEST = null;` with the actual URL array
3. Copies `assets/phosphor-vigil.js` as a sibling of the output HTML (the template imports it as a static ES module — required even when `fx: 'none'`)
4. Updates the `<title>` to include the search query

Result: a museum/stock search becomes an instantly browsable 3D corridor.

## Key Design Decisions

- **Vanilla ES modules only** — no React, no Vue, no drei, no bundler. Each output is openable offline.
- **Three.js r175 via jsdelivr import map** — Modes 3 & 4 use modern ESM. Mode 1 stays on its original cdnjs r134 classic script for backward compatibility.
- **Shared FX as a module, not inlined** — `phosphor-vigil.js` is the single source of truth. Inlining the shaders into each template would lose coherence. The module is importable standalone into any Three.js project (e.g. World War Watcher's Vector Ghost Protocol work).
- **Background colors are never pure black** — `#050508` dark, `#fafafa` light. Enforced by validators.
- **Aesthetic constants are preserved verbatim** — every shader value in `phosphor-vigil.js` comes from the celescript butterfly bundle. They are not magic numbers; they are the aesthetic signature.
- **Anti-patterns enforced by validators** — React imports, drei imports, pure black backgrounds, missing keyboard handlers, missing WebGL fallback all fail the validator.

## Anti-Patterns

See `SKILL.md` for the full list. Key rules:

- Never use React/Vue/framework code — vanilla ES modules only
- Never use `THREE.OrbitControls` — implement spherical camera directly
- Never use `THREE.Geometry` — always `BufferGeometry`
- Never use pure black backgrounds — `#050508` dark, `#fafafa` light
- Never embed the phosphor-vigil shaders inline — always `import { PhosphorVigil } from './phosphor-vigil.js'`
- Never rename the `IMAGES_INJECTION_POINT` sentinel or the `IMAGE_MANIFEST` const in Mode 3 — the image-well bridge depends on both
- Never clone skinned meshes with plain `.clone()` in Mode 4 — always `SkeletonUtils.clone`

## Installation

```bash
cp -R threejs-particle-canvas/ ~/.claude/skills/threejs-particle-canvas/
```

The skill is model-invocable. Trigger phrases include narrative canvas, particle art, spinner, loader, infinite gallery, tunnel flythrough, 3D butterfly, glTF specimen, and CRT post-processing.

## Source Material

- Mode 1 (Instance) — original AI self-portrait by the skill author
- Mode 2 (spinners) — built on the Spinner class pattern from the Three.js TSL examples
- Mode 3 — vanilla port of [thebuggeddev/Infinitor](https://github.com/thebuggeddev/Infinitor) (MIT license)
- Mode 4 — vanilla port of [celescript.dev/experiments/3d-butterfly](https://celescript.dev/experiments/3d-butterfly), reverse-engineered from the production bundle. Shaders preserved verbatim.
- Default Mode 4 model — Three.js's official `Parrot.glb` from `examples/models/gltf/`, served via jsdelivr (CC0)
