# Fluid-DOM Mode

A Navier-Stokes stable fluid simulation applied as WebGL overlays to live DOM
elements. Pointer movement splats velocity into a persistent field, producing
flowing, organic distortion of images, headings, and sections underneath.

Inspired by Amagi (fand)'s CodePen "Stable Fluid on VFX-JS"
(https://codepen.io/editor/fand/pen/019d61f5-aadf-7e18-851c-0ebd317146c7).
The shader lineage traces to Pavel DoGreat's WebGL-Fluid-Simulation (MIT):
https://github.com/PavelDoGreat/WebGL-Fluid-Simulation

## How It Differs from Liquid Logo and Astryx

| Property | Liquid Logo | Astryx | Fluid-DOM |
|----------|-------------|--------|-----------|
| Target | Single uploaded texture | Single hero image + depth map | Live DOM elements |
| Technique | Radial Gaussian falloff + chromatic aberration | Single-tap inverse displacement | Full Navier-Stokes sim |
| Shader passes | 1 | 1 | 6+ (curl, vorticity, divergence, pressure, gradient, advect) |
| Velocity state | None (decays in ~1s) | None | Persistent (flows after pointer stops) |
| GPU cost per frame | Low (~0.5ms) | Low (~0.5ms) | Medium-High (~2-4ms at half-res) |
| Pattern scope | Single element | Single hero section | Multiple sections (editorial page) |

## The Simulation Pipeline

Six shader passes per frame, ping-ponging between framebuffers:

### 1. Curl

Measures angular velocity of the velocity field. Used by vorticity to add
confinement force.

```glsl
float L = texture(velocity, uv - vec2(t.x, 0.0)).y;
float R = texture(velocity, uv + vec2(t.x, 0.0)).y;
float T = texture(velocity, uv + vec2(0.0, t.y)).x;
float B = texture(velocity, uv - vec2(0.0, t.y)).x;
outColor = vec4(0.5 * (R - L - T + B), 0.0, 0.0, 1.0);
```

### 2. Vorticity + Pointer Splat

Adds a confinement force proportional to curl gradient (prevents numerical
dissipation from killing the swirls). Then splats pointer delta into the
velocity field:

```glsl
// Confinement force
vec2 force = vec2(T - B, R - L);
force = normalize(force) * curlStrength * C;
vel += force * dt;

// Pointer splat (Gaussian, aspect-corrected)
vec2 diff = uv - mouseUv;
diff.x *= aspect;
float mSplat = exp(-dot(diff, diff) / splatRadius);
vel += (mouseDelta / resolution) * mSplat * splatForce;
```

**Velocity clamping**: `clamp(vel, vec2(-1000), vec2(1000))` prevents runaway
accumulation — a practical stability hack from the Pavel DoGreat lineage.

### 3. Divergence

Measures how much the velocity field is compressing or expanding at each point.
Setup for the pressure solve.

### 4. Pressure Solve (Jacobi iteration)

20-50 iterations of Jacobi to approximate the pressure field that, when
subtracted as a gradient, makes the velocity divergence-free (incompressible).

### 5. Gradient Subtract

Subtracts the pressure gradient from velocity to enforce incompressibility.

### 6. Advect

Moves the velocity (and optionally dye/color) forward in time by tracing
backward along the velocity field and sampling (semi-Lagrangian advection).

## Pointer Input

| Uniform | Type | Description |
|---------|------|-------------|
| `mouse` | `vec2` | Cursor position in pixels |
| `mouseDelta` | `vec2` | Frame-to-frame cursor displacement in pixels |
| `splatRadius` | `float` | Gaussian splat radius (smaller = tighter vortex) |
| `splatForce` | `float` | Multiplier on velocity injection |
| `curlStrength` | `float` | Vorticity confinement intensity |

Use W3C Pointer Events (`pointermove`) exclusively — not `mousemove` +
`touchmove` separately. Set `touch-action: pan-y` on the container to
preserve native scroll.

## Prefers-Reduced-Motion

The liquid-logo approach of freezing the RAF loop is **insufficient** for
fluid-dom because the velocity texture persists. Freezing RAF leaves frozen
distortion on screen. The correct approach:

1. Detect `prefers-reduced-motion: reduce`
2. Clear the velocity texture to zero
3. Skip all shader passes
4. Show the underlying DOM elements undistorted
5. Subscribe to `matchMedia` changes to restore on toggle

## Performance Considerations

The multi-pass pipeline is significantly more expensive than single-tap shaders.
Mitigations:

- **Half-resolution velocity**: run the sim at `canvas / 2` and bilinear-upsample
  for the advection sample. Cuts fragment count by 4x.
- **Viewport cull**: for long editorial pages, only run the sim on sections
  within the viewport (IntersectionObserver). The CodePen runs one global field;
  a production build should scope per-section.
- **DPR clamp**: cap at 1.5 (matching Astryx convention).
- **Mobile fallback**: static (no fluid sim) below 640px viewport or on
  `(hover: none)` devices.

## Library Dependency

The source CodePen uses `@vfx-js/core` by amagi.dev. **License status
UNVERIFIED as of 2026-04-08.** Before any Scope B implementation:

1. Check the npm package `LICENSE` field and repository
2. If unlicensed or restrictively licensed, reproduce the shader family from
   scratch using Pavel DoGreat's WebGL-Fluid-Simulation (MIT) as reference
3. The simulation math is well-documented (Jos Stam, "Real-Time Fluid Dynamics
   for Games", GDC 2003) — no library is required to implement it

## External References

- Pavel DoGreat's WebGL-Fluid-Simulation (MIT): https://github.com/PavelDoGreat/WebGL-Fluid-Simulation
- Jos Stam — "Real-Time Fluid Dynamics for Games" (GDC 2003): https://www.dgp.toronto.edu/public_user/stam/reality/Research/pdf/GDC03.pdf
- VFX-JS homepage: https://amagi.dev/vfx-js
- Source CodePen: https://codepen.io/editor/fand/pen/019d61f5-aadf-7e18-851c-0ebd317146c7
- Sibling pattern — Astryx hero: `~/.claude/skills/minoan-frontend-design/references/astryx-hero.md`
- Sibling pattern — Liquid Logo: `references/liquid-logo.md` in this skill
