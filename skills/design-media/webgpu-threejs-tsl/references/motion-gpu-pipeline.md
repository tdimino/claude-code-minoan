# Motion GPU Pipeline

Lightweight WebGPU runtime for fullscreen WGSL fragment shaders and
multi-pass GPU pipelines. Production-grade Shadertoy alternative with
framework adapters. Not a 3D engine — use Three.js WebGPU for scenes
with meshes and cameras. Source: @motion-core/motion-gpu v0.8.0 (MIT).

## Core Architecture (5 stages)

### 1. defineMaterial()

- Contract: `{ fragment, uniforms, textures, storageBuffers }`
- Fragment signature: `fn frag(uv: vec2f) -> vec4f`
- Strict validation at construction, immutable after creation

```javascript
import { defineMaterial } from '@motion-core/motion-gpu';

const material = defineMaterial({
  fragment: `fn frag(uv: vec2f) -> vec4f {
    return vec4f(uv, 0.5, 1.0);
  }`,
  uniforms: { time: 0.0 },
});
```

### 2. Pipeline Signature Derivation

- Deterministic string from compiled shader + layout
- Same signature = skip recompilation, buffer-update only

### 3. Frame Scheduler

- `useFrame()` with topological ordering, invalidation tokens
- Render modes: always | on-demand | manual

### 4. Render Graph (5 pass types)

- **ShaderPass**: `fn shade(inputColor: vec4f, uv: vec2f) -> vec4f`
- **BlitPass**, **CopyPass** (texture routing)
- **ComputePass**: `@compute @workgroup_size(...)` validated
- **PingPongComputePass**: double-buffered compute

## When to Use (vs Three.js WebGPU)

| Feature | Motion GPU | Three.js WebGPU |
|---------|-----------|-----------------|
| Abstraction | Fragment-first | Scene graph |
| Shader lang | WGSL native | TSL → WGSL |
| Multi-pass | Render graph | EffectComposer |
| Compute | First-class | StorageBuffer |
| Bundle | ~15KB | ~300KB |

Use Motion GPU for: fullscreen shader art, multi-pass pipelines,
GPU simulations (particles, fluid, reaction-diffusion).
Use Three.js WebGPU for: 3D scenes with meshes, cameras, lighting.
