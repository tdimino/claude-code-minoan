# Overwatch Mode — WebGPU Shaders

## Overview

Overwatch Mode supports real-time WebGPU shaders rendered to `<canvas>` elements. The `WebGPUCanvas` component handles device initialization, uniform buffers, and the render loop, with an animated CSS gradient fallback for browsers without WebGPU support.

## WebGPU Support

As of 2026, WebGPU is supported in:
- Chrome/Edge 113+ (desktop)
- Chrome Android 121+
- Safari 18+ (macOS/iOS) — behind flag in some versions
- Firefox — behind flag (`dom.webgpu.enabled`)

**Always provide a fallback.** The `WebGPUCanvas` component does this automatically.

## Using WebGPUCanvas

```tsx
import { WebGPUCanvas } from "../components/graphics/WebGPUCanvas";
import shaderCode from "../components/graphics/shaders/lava-nebula.wgsl?raw";

<WebGPUCanvas
  shaderCode={shaderCode}
  className="absolute inset-0 w-full h-full"
  fallbackColors={["#0c0c0e", "#ff6e41", "#0c0c0e"]}
/>
```

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `shaderCode` | `string` | required | WGSL shader source code |
| `className` | `string` | `""` | CSS classes for canvas element |
| `fallbackColors` | `[string, string, string]` | `["#0c0c0e", "#ff6e41", "#0c0c0e"]` | Gradient colors when WebGPU unavailable |

### Vite Import

Import `.wgsl` files as raw strings using Vite's `?raw` suffix:
```tsx
import shaderCode from "./shaders/my-shader.wgsl?raw";
```

Type declaration in `vite-env.d.ts`:
```typescript
declare module "*.wgsl?raw" {
  const content: string;
  export default content;
}
```

## Uniform Buffer Layout

The `WebGPUCanvas` provides these uniforms to every shader:

| Offset | Type | Name | Description |
|--------|------|------|-------------|
| 0 | `vec2f` | `resolution` | Canvas size in pixels (devicePixelRatio-adjusted) |
| 8 | `f32` | `time` | Seconds since mount |
| 12 | `f32` | `_pad` | Padding (alignment) |
| 16 | `vec2f` | `mouse` | Normalized mouse position (0-1), lerped for smoothing |
| 24 | `vec2f` | — | Padding |

### Shader Struct

```wgsl
struct Uniforms {
  resolution: vec2f,
  time: f32,
  _pad: f32,
  mouse: vec2f,
}

@group(0) @binding(0) var<uniform> u: Uniforms;
```

## Included Shader: Lava Nebula

`shaders/lava-nebula.wgsl` — The signature Overwatch cover effect.

### Technique
- **Raymarching accumulation** — 80 iterations building up color
- **Sinusoidal displacement** — `sin(a * d + vec3f(t)).zxy / d` creates organic warping
- **Mouse reactivity** — Camera offset based on normalized mouse position
- **tanh() tone mapping** — Soft HDR rolloff preventing harsh clipping
- **Color base** — `vec3f(0.0, 1.0, 8.0)` biases toward blue/orange spectrum

### Key Parameters to Customize

| Line | Parameter | Effect |
|------|-----------|--------|
| `uv += ... * 0.15` | Mouse sensitivity | Higher = more camera movement |
| `i < 80` | Iteration count | Higher = denser, richer (but slower) |
| `fi * 0.02` | Depth scaling | Controls how "deep" the raymarching goes |
| `t * 0.3` | Time speed | Animation speed |
| `vec3f(0.0, 1.0, 8.0)` | Color base | R/G/B weighting in final output |

## Writing Custom Shaders

### Minimal Template

```wgsl
struct Uniforms {
  resolution: vec2f,
  time: f32,
  _pad: f32,
  mouse: vec2f,
}

@group(0) @binding(0) var<uniform> u: Uniforms;

@vertex
fn vs(@builtin(vertex_index) i: u32) -> @builtin(position) vec4f {
  let pos = array<vec2f, 4>(
    vec2f(-1, -1), vec2f(1, -1), vec2f(-1, 1), vec2f(1, 1)
  );
  return vec4f(pos[i], 0, 1);
}

@fragment
fn fs(@builtin(position) fragCoord: vec4f) -> @location(0) vec4f {
  let uv = fragCoord.xy / u.resolution;
  let t = u.time;

  // Your shader logic here
  let col = vec3f(uv.x, uv.y, sin(t) * 0.5 + 0.5);

  return vec4f(col, 1.0);
}
```

### Performance Tips

- Keep iteration counts below 100 for real-time performance
- Use `tanh()` or `clamp()` for tone mapping
- Mouse smoothing is handled by the component (lerp factor 0.05)
- The canvas auto-resizes using `devicePixelRatio`

## CSS Gradient Fallback

When WebGPU is unavailable, `WebGPUCanvas` renders an animated CSS gradient:

```css
@keyframes gradient-shift {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.animate-gradient-shift {
  animation: gradient-shift 8s ease infinite;
}
```

The three `fallbackColors` create a diagonal gradient that slowly shifts position.
