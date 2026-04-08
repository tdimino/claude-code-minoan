# rocaille-shader

WebGL/GLSL shader generation skill with four modes: organic domain-warp visuals, pointer-reactive liquid logo effects, depth-parallax editorial heroes, and stable fluid simulations over live DOM.

## Modes

| Mode | Description | Output |
|------|-------------|--------|
| `rocaille` | Domain warping via `v += sin(v.yx + t) / amplitude` — organic, flowing light patterns | Shadertoy, Three.js, WebGL2, P5.js |
| `liquid-logo` | Chromatic aberration + Gaussian falloff on an image/SVG texture, pointer-reactive | Self-contained HTML (single file, no deps) |
| `astryx-statue` | Depth-map parallax displacement — static image appears to shift in 3D as cursor moves | Documentation-only (Scope A); shader in Scope B |
| `fluid-dom` | Navier-Stokes stable fluid simulation applied as WebGL overlays to live DOM elements | Documentation-only (Scope A); shader in Scope B |

## Architecture

```
rocaille-shader/
├── SKILL.md                          Skill definition (4 modes, tuning params)
├── README.md                         This file
├── scripts/
│   └── rocaille_generator.py         Generator: --mode rocaille|liquid-logo [--warps N] [--color MODE]
├── assets/templates/
│   ├── shadertoy.glsl                Shadertoy-compatible fragment shader
│   ├── threejs.js                    Three.js ShaderMaterial with uniforms
│   ├── vanilla-webgl.html            Pure WebGL2, no dependencies
│   ├── p5js.js                       P5.js shader mode integration
│   ├── interactive.html              Full demo with controls
│   ├── liquid-logo.glsl              Shadertoy liquid-logo reference
│   └── liquid-logo.html              Standalone liquid-logo runtime
└── references/
    ├── rocaille-complete.md           Full 8-step shader breakdown
    ├── domain-warping.md              Theory from Inigo Quilez
    ├── glsl-patterns.md               Common GLSL patterns used
    ├── liquid-logo.md                 Liquid logo math (falloff, pull, chromatic offset)
    └── fluid-dom.md                   Stable fluid sim: Navier-Stokes pipeline, VFX-JS lineage
```

## Usage

```bash
# Rocaille domain warp
python3 scripts/rocaille_generator.py --warps 5 --color rainbow --format shadertoy

# Liquid logo from an image
python3 scripts/rocaille_generator.py --mode liquid-logo --input logo.svg --output liquid.html

# Interactive demo
python3 scripts/rocaille_generator.py --demo
```

### Tuning (liquid-logo mode)

| Flag | Default | Effect |
|------|---------|--------|
| `--distortion` | `0.40` | Peak UV pull toward cursor |
| `--radius` | `0.25` | Gaussian falloff radius |
| `--decay` | `3.0` | Release decay rate |
| `--chroma` | `0.015` | RGB-channel UV split magnitude |
| `--idle` / `--no-idle` | on | Lissajous idle breathing |

## Astryx-Statue Mode (documentation-only)

Depth-map parallax displacement hero inspired by https://indigo-type-231733.framer.app/astryx. A single-tap inverse displacement shader (Robin Delaporte lineage) uses a color image + grayscale depth map to create the illusion of 3D parallax without real geometry.

Key properties:
- DPR clamped to 1.5
- `uDepthInvert` uniform for depth polarity (white-near vs black-near)
- `prefers-reduced-motion`: static `<img>` fallback
- Depth-seam contract: `astryx-depth-1.0` (PNG, 8-bit grayscale, polarity-tagged)

See `references/` in `minoan-frontend-design` for the full pattern anatomy (`astryx-hero.md`).

## Fluid-DOM Mode (documentation-only)

Pointer-reactive Navier-Stokes stable fluid simulation over live DOM elements, inspired by Amagi's VFX-JS CodePen. Six shader passes per frame (curl, vorticity, divergence, pressure solve, gradient subtract, advect) with persistent velocity state.

Key properties:
- Wraps live DOM (not a canvas texture)
- Velocity persists after pointer stops
- Half-resolution sim recommended for performance
- `prefers-reduced-motion`: clear velocity texture + skip all passes

See `references/fluid-dom.md` for the full pipeline documentation.

## Attribution

- **Rocaille domain-warp technique** — [Inigo Quilez's domain warping article](https://iquilezles.org/articles/warp/) (iq / Shadertoy)
- **Liquid Logo mode** — inspired by [LiquidLogo](https://gustavwf.supply/product/liquidlogo) by Gustav WF ([@gustavwf](https://x.com/gustavwf)). Reimplemented from scratch from first principles—not a port of Gustav's code
- **Astryx-statue mode** — pattern studied from [Astryx](https://indigo-type-231733.framer.app/astryx) (Framer + Unicorn Studio). Shader technique descends from [Robin Delaporte's CodePen](https://codepen.io/robin-dela/pen/vaQQNL). Production reference: [DepthFlow](https://github.com/BrokenSource/DepthFlow) (AGPL, reference only)
- **Fluid-DOM mode** — pattern studied from [Amagi's "Stable Fluid on VFX-JS" CodePen](https://codepen.io/editor/fand/pen/019d61f5-aadf-7e18-851c-0ebd317146c7). Shader lineage: [Pavel DoGreat's WebGL-Fluid-Simulation](https://github.com/PavelDoGreat/WebGL-Fluid-Simulation) (MIT). Theory: Jos Stam, "Real-Time Fluid Dynamics for Games" (GDC 2003)
