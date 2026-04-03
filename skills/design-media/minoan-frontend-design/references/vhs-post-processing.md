# VHS Post-Processing Pipeline

A 5-pass WebGL post-processing pipeline for "VHS dreamworld", "analog TV", and "retro-futuristic" creative directions. Extracted from Jake Archibald's [curved-markup](https://github.com/jakearchibald/random-stuff/tree/main/apps/curved-markup) html-in-canvas demo.

## Pipeline Overview

| Pass | Input | Output | Effect |
|------|-------|--------|--------|
| Buffer A | Source texture | bufA | Color channel separation / initial processing |
| Buffer B | bufA | bufB | Gaussian blur + luminance extraction |
| Buffer C | bufB + prevC | currC | Temporal feedback via ping-pong (motion trails, VHS ghosting) |
| Buffer D | currC | bufD | Chromatic aberration + scanline overlay + film grain |
| Image | bufD + source | final | Soft light blend composite with original |

## Key GLSL Utilities

Shared `common.glsl` prepended to all fragment shaders:

```glsl
#define PI 3.1415926535897932384626433832795
#define W vec3(0.2126, 0.7152, 0.0722)  // Rec. 709 luminance

float GetLuminance(vec3 color) {
    return dot(W, color);
}

float GetGaussianWeight(vec2 i, float sigma) {
    return 1.0 / (2.0 * PI * sigma * sigma) *
           exp(-(dot(i, i) / (2.0 * sigma * sigma)));
}

vec4 Blur(float size, vec2 fragCoord, vec2 resolution,
          bool useGaussian, sampler2D source, float lodBias) {
    vec4 pixel; float sum;
    vec2 uv = fragCoord / resolution;
    vec2 scale = 1.0 / resolution;
    if (!useGaussian) size *= 0.333;
    for (float y = -size; y < size; y++)
        for (float x = -size; x < size; x++) {
            vec2 off = vec2(x, y);
            float w = useGaussian ? GetGaussianWeight(off, size * 0.25) : 1.0;
            pixel += texture(source, uv + off * scale) * w;
            sum += w;
        }
    return pixel / sum;
}

float GoldNoise(vec2 xy, float seed) {
    return fract(sin(dot(xy * seed, vec2(12.9898, 78.233))) * 43758.5453);
}

float BlendSoftLight(float base, float blend) {
    return (blend < 0.5)
        ? (2.0*base*blend + base*base*(1.0-2.0*blend))
        : (sqrt(base)*(2.0*blend-1.0) + 2.0*base*(1.0-blend));
}

vec4 BlendSoftLight(vec4 base, vec4 blend) {
    return vec4(BlendSoftLight(base.r,blend.r),
                BlendSoftLight(base.g,blend.g),
                BlendSoftLight(base.b,blend.b), 1.0);
}

vec4 BlendSoftLight(vec4 base, vec4 blend, float opacity) {
    return BlendSoftLight(base, blend) * opacity + base * (1.0 - opacity);
}
```

## Three.js Integration

### Fullscreen Quad Setup

```js
const VERT = `
in vec3 position; out vec2 vUv;
void main() {
  vUv = position.xy * 0.5 + 0.5;
  gl_Position = vec4(position.xy, 0.0, 1.0);
}`

function shadertoyFrag(body) {
  return `
precision highp float;
in vec2 vUv; out vec4 fragColor;
uniform sampler2D iChannel0, iChannel1;
uniform vec3 iResolution;
uniform float iTime;
uniform int iFrame;
${commonGlsl}
${body}
void main() {
  mainImage(fragColor, vUv * iResolution.xy);
}`
}
```

### Render Pass Factory

```js
function makePass(fragBody) {
  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.BufferAttribute(
    new Float32Array([-1,-1,0, 1,-1,0, -1,1,0, 1,-1,0, 1,1,0, -1,1,0]), 3))
  return {
    geo,
    mat: new THREE.RawShaderMaterial({
      vertexShader: VERT,
      fragmentShader: shadertoyFrag(fragBody),
      uniforms: {
        iChannel0: { value: null }, iChannel1: { value: null },
        iResolution: { value: new THREE.Vector3() },
        iTime: { value: 0 }, iFrame: { value: 0 },
      },
      glslVersion: THREE.GLSL3,
      depthTest: false, depthWrite: false,
    }),
    mesh: null  // set mesh = new THREE.Mesh(geo, mat)
  }
}
```

### Ping-Pong for Temporal Feedback

Buffer C reads its own previous output—requires two render targets swapped each frame:

```js
let cTargets = [makeTarget(w, h), makeTarget(w, h)]
let cIdx = 0

// Each frame:
const prevC = cTargets[1 - cIdx]
const currC = cTargets[cIdx]
runPass(renderer, passC, currC, bufB.texture, prevC.texture, w, h, time, frame)
cIdx = 1 - cIdx
```

This creates VHS ghosting—previous frame content bleeds into the current with decay.

### Full Pipeline Render

```js
render(renderer, sourceTexture, width, height, time, frame) {
  ensureTargets(width, height)
  // A: source → bufA
  runPass(renderer, passA, targets.a, sourceTexture, null, ...)
  // B: bufA → bufB
  runPass(renderer, passB, targets.b, targets.a.texture, null, ...)
  // C: bufB + prevC → currC (temporal feedback)
  runPass(renderer, passC, currC, targets.b.texture, prevC.texture, ...)
  cIdx = 1 - cIdx
  // D: currC → bufD
  runPass(renderer, passD, targets.d, currC.texture, null, ...)
  // Image: bufD + source → final
  runPass(renderer, passImage, targets.img, targets.d.texture, sourceTexture, ...)
  return targets.img.texture
}
```

## When to Use

- **"VHS dreamworld"** creative direction—the defining post-processing effect
- **"Analog TV"**—scanlines + noise + chromatic aberration
- **"Retro-futuristic"**—apply to character grid backgrounds or Three.js scenes
- **Transition effects**—apply pipeline temporarily during page transitions, fade opacity
- **Hero backgrounds**—subtle VHS treatment on looping video or animated canvas

## When NOT to Use

- Clean/modern designs—VHS treatment reads as intentionally degraded
- Text-heavy pages—chromatic aberration impairs readability
- Mobile-first—5 fullscreen draw calls per frame may impact battery on low-end devices
- Designs requiring WCAG contrast compliance—blur + aberration reduce effective contrast

## Standalone Extraction

The pipeline is self-contained (~190 lines TS). To adapt for any project:

1. Copy `vhsPipeline.ts` and `shaders/` directory (common.glsl + 5 shader files)
2. Create your source texture (canvas capture, video, Three.js scene)
3. Call `pipeline.render(renderer, sourceTexture, w, h, time, frame)` each frame
4. The returned texture is the post-processed result

**Dependencies**: Three.js only. GLSL3 required (WebGL2).

## Performance

- 5 draw calls per frame—negligible on modern GPUs
- Render targets auto-resize when dimensions change
- Ping-pong buffer adds one extra target allocation
- Total GPU memory: ~6 render targets at viewport resolution

## Source

- Pipeline: [`vhsPipeline.ts`](https://github.com/jakearchibald/random-stuff/blob/main/apps/curved-markup/src/App/vhsPipeline.ts)
- Shaders: [`shaders/`](https://github.com/jakearchibald/random-stuff/tree/main/apps/curved-markup/src/App/shaders) (common.glsl, buffer-a through buffer-d, image.glsl)
- GLSL utilities: Shadertoy community patterns
- Soft light blend: Jamie Owen's [glsl-blend](https://github.com/jamieowen/glsl-blend)
