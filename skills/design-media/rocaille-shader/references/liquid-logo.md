# Liquid Logo Mode

A texture-sampling, pointer-reactive extension of the rocaille domain-warp
technique. Instead of coloring a procedural distance field, the shader samples
an image or SVG and displaces the sample UV to make the logo **bulge, ripple,
and refract** around the cursor.

Inspired by [gustavwf.supply/product/liquidlogo](https://gustavwf.supply/product/liquidlogo).
The Framer component is not open source — this is a reimplementation from the
same first principles (radial falloff, UV displacement, chromatic UV split),
not a port of its code.

## The Math

### Radial falloff

Given cursor position `m` (UV space) and pixel position `uv`, the displacement
vector `d = uv - m` is aspect-corrected so the falloff is circular on screen,
not elliptical:

```glsl
vec2 d = vec2((uv.x - m.x) * asp, uv.y - m.y);
```

The weight is a Gaussian in `d`, scaled by an exponential decay on the time
since the last pointer event:

```glsl
float w = exp(-dot(d, d) / (RADIUS * RADIUS))
        * exp(-uTimeSinceInteract * DECAY);
```

- `RADIUS` controls how far the ripple reaches (smaller = tighter).
- `DECAY` controls how fast the ripple relaxes back to rest after the pointer
  leaves. A value of `3.0` gives roughly a one-second fade.

### UV pull (the "bulge")

`d` points **cursor → pixel**. Sampling the texture at `uv - d * strength`
reads content from a position closer to the cursor and paints it outward —
the optical illusion of the logo bulging toward the pointer:

```glsl
vec2 pullUv   = vec2(d.x / asp, d.y) * (DISTORTION * w);
vec2 sampleUv = uv - pullUv;
```

Dividing by `asp` converts the aspect-corrected `d` back into raw UV space
before subtracting from `uv` — otherwise the pull would be squashed on wide
canvases.

`DISTORTION` is the peak pull (at the cursor, when `w = 1`). Values around
`0.3–0.5` look liquid; higher values start to invert and look glitchy.

### Chromatic aberration

To get the "refracting colors like a liquid surface" property, sample the
R and B channels at UVs offset along the cursor-to-pixel direction:

```glsl
vec2 chromaDir = (r2 > 1e-6) ? normalize(d) : vec2(0.0);
vec2 chromaOff = vec2(chromaDir.x / asp, chromaDir.y) * (CHROMA * w);

float r = texture(uLogo, sampleUv - chromaOff).r;
vec4  g = texture(uLogo, sampleUv);
float b = texture(uLogo, sampleUv + chromaOff).b;
fragColor = vec4(r, g.g, b, g.a);
```

**Why along the cursor direction and not axis-aligned?** Axis-aligned
chromatic offsets produce a static "bad lens" look — always pulling red left
and blue right regardless of where the ripple is happening. Offsetting along
`normalize(d)` makes the split *point away from the cursor*, so it reads as
light refracting through a moving blob of liquid rather than a broken lens.

### Idle breathing

When the cursor has been inactive for > 500 ms, the runtime stops using the
real pointer position and drives `uMouse` from a slow Lissajous path instead.
This gives the logo a subtle breathing motion so the page never looks dead,
and matches LiquidLogo's "idle animation" property.

Additionally the shader adds a tiny sinusoidal warp of its own (the `IDLE_*`
block), which runs constantly but with very small amplitude. This is a reuse
of rocaille's core formula `v += sin(v.yx * K + t) / A`, just applied at very
low amplitude to an image sample instead of procedural color.

## Parameters and defaults

| Uniform / flag | Default | Meaning |
|---|---|---|
| `DISTORTION`          | `0.40`  | Peak UV pull toward the cursor |
| `RADIUS`              | `0.25`  | Gaussian falloff radius (NDC) |
| `DECAY`               | `3.0`   | Exponential decay rate post-release |
| `CHROMA`              | `0.015` | RGB-channel UV split magnitude |
| `IDLE_ON`             | `1`     | Enable Lissajous idle breathing |
| `IDLE_AMP`            | `0.012` | Idle warp amplitude |
| `IDLE_SPEED`          | `0.6`   | Idle warp speed |
| `uTimeSinceInteract`  | runtime | Seconds since last `pointermove` |

These are exposed as `#define`s in
`assets/templates/liquid-logo.glsl` and as CLI flags on
`scripts/rocaille_generator.py --mode liquid-logo`.

## Runtime behavior

The WebGL2 runtime in `assets/templates/liquid-logo.html` (and the output of
`rocaille_generator.py --mode liquid-logo`) adds the pieces that pure GLSL
cannot express:

1. **Texture upload.** Loads the image via an `Image` element, uploads it to
   a `TEXTURE_2D` with `UNPACK_FLIP_Y_WEBGL` so the shader's UV origin matches
   the image's top-left visually.
2. **Aspect containment.** Computes a `scale` uniform so the logo fits inside
   the canvas with its own aspect ratio preserved. Outside the logo rect,
   `inside = 0` and the fragment is transparent.
3. **Pointer tracking.** `pointermove` and `touchmove` write into `uMouse`
   in UV space (origin bottom-left to match GLSL). `pointerleave` forces
   `uTimeSinceInteract` large so the decay starts.
4. **Idle path.** When `performance.now() - lastMoveAt > 500ms`, drives
   `uMouse` from a slow Lissajous (`cos(t*1.3), sin(t*1.7)`, amplitude `0.22`
   around center).
5. **Performance gating.** Pauses the RAF loop on `visibilitychange` so the
   shader consumes zero GPU when the tab is hidden. Matches LiquidLogo's
   "performance-aware behavior when offscreen or tabbed away."
6. **Reduced motion.** Reads `prefers-reduced-motion` and halves `DISTORTION`
   and `IDLE_AMP` when the user has opted out of motion.

## Sampling in Shadertoy

`liquid-logo.glsl` is Shadertoy-compatible. Drop an image into `iChannel0`
and the shader will run. Because Shadertoy reports `iMouse.z > 0` only while
the mouse button is held, the reference shader auto-orbits the cursor around
center when the button is released — that way the preview stays alive without
requiring a click. The production runtime replaces this with a real
`uMouse` uniform driven by `pointermove`.
