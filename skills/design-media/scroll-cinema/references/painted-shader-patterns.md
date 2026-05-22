# Painted Shader Patterns

Three shader presets for atmospheric backgrounds that react to cursor and scroll. These are full-screen background canvases rendered behind HTML content — not interactive 3D scenes.

## Shared Three.js Setup

All presets use the same scene structure:

```js
import * as THREE from 'three';

const canvas = document.getElementById('shader-canvas');
const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: false });
const isMobile = window.innerWidth <= 768;
renderer.setPixelRatio(Math.min(window.devicePixelRatio, isMobile ? 1.5 : 2.0));
renderer.setSize(window.innerWidth, window.innerHeight);

const scene = new THREE.Scene();
const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

const uniforms = {
  uTime: { value: 0 },
  uMouse: { value: new THREE.Vector2(0.5, 0.5) },
  uScroll: { value: 0 },
  uResolution: { value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
  uChapterHue: { value: 0.694 },       // 250/360
  uChapterLightness: { value: 0.25 }
};

const geometry = new THREE.PlaneGeometry(2, 2);
const material = new THREE.ShaderMaterial({
  uniforms,
  vertexShader: VERTEX_SHADER,
  fragmentShader: FRAGMENT_SHADER,
  depthTest: false,
  depthWrite: false
});

scene.add(new THREE.Mesh(geometry, material));
```

### Shared Vertex Shader

All presets use a screen-quad vertex shader — no projection needed:

```glsl
void main() {
  gl_Position = vec4(position.xy, 0.0, 1.0);
}
```

### Canvas Positioning

```css
#shader-canvas {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: -1;
  pointer-events: none;
}
```

Use `position: fixed` with `z-index: -1` so the canvas stays behind scrolling content. The Lenis scroll wrapper handles the HTML content layer independently.

---

## Preset 1: painted-dots

Dot-grid with mouse-reactive ripple and scroll-driven density shift. Lightest shader — runs at 60fps on any GPU.

```glsl
uniform vec2 uResolution;
uniform vec2 uMouse;
uniform float uScroll;
uniform float uTime;
uniform float uVelocity;
uniform float uChapter;
uniform float uChapterHue;
uniform float uChapterLightness;

vec3 hsl2rgb(float h, float s, float l) {
  vec3 rgb = clamp(abs(mod(h * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
  return l + s * (rgb - 0.5) * (1.0 - abs(2.0 * l - 1.0));
}

void main() {
  vec2 screenUv = gl_FragCoord.xy / uResolution;
  float aspect = uResolution.x / uResolution.y;
  vec2 uv = vec2(screenUv.x * aspect, screenUv.y);

  // Grid density increases with scroll, shifts subtly per chapter
  float gridSize = mix(14.0, 28.0, uScroll) * (1.0 + uChapter * 0.05);
  vec2 gridUv = fract(uv * gridSize);
  vec2 gridId = floor(uv * gridSize);

  // Distance from cell center
  float dist = length(gridUv - 0.5);

  // Mouse proximity ripple
  vec2 mouseUv = vec2(uMouse.x * aspect, uMouse.y);
  float mouseDist = length(uv - mouseUv);
  float mouseInfluence = smoothstep(0.35, 0.0, mouseDist);

  // Dot radius: time pulse + mouse ripple + velocity expansion
  float pulse = sin(uTime * 0.5 + gridId.x * 0.3 + gridId.y * 0.5) * 0.04;
  float baseRadius = 0.14 + pulse + mouseInfluence * 0.16;
  float radius = baseRadius * (1.0 + uVelocity * 0.5);

  // Draw dot with soft edge
  float dot = smoothstep(radius + 0.025, radius - 0.025, dist);

  // Color from chapter palette
  float h = uChapterHue;
  float s = 0.4 + mouseInfluence * 0.3;
  float l = uChapterLightness + 0.15 + mouseInfluence * 0.1;
  vec3 dotColor = hsl2rgb(h, s, l);

  // Background — near-black with hint of chapter hue
  vec3 bgColor = hsl2rgb(h, 0.1, uChapterLightness * 0.3);

  gl_FragColor = vec4(mix(bgColor, dotColor, dot), 1.0);
}
```

**Performance:** ~0.5ms per frame on integrated GPU. The lightest preset.

---

## Preset 2: watercolor

NPR watercolor effect using layered simplex noise with quantized color bands and edge detection. Medium GPU cost.

```glsl
uniform vec2 uResolution;
uniform vec2 uMouse;
uniform float uScroll;
uniform float uTime;
uniform float uVelocity;
uniform float uChapter;
uniform float uMobile;
uniform float uChapterHue;
uniform float uChapterLightness;

// Simplex noise (2D)
vec3 mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec2 mod289(vec2 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec3 permute(vec3 x) { return mod289(((x * 34.0) + 1.0) * x); }

float snoise(vec2 v) {
  const vec4 C = vec4(0.211324865405187, 0.366025403784439,
                     -0.577350269189626, 0.024390243902439);
  vec2 i  = floor(v + dot(v, C.yy));
  vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod289(i);
  vec3 p = permute(permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0);
  m = m * m;
  m = m * m;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
  vec3 g;
  g.x = a0.x * x0.x + h.x * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}

vec3 hsl2rgb(float h, float s, float l) {
  vec3 rgb = clamp(abs(mod(h * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
  return l + s * (rgb - 0.5) * (1.0 - abs(2.0 * l - 1.0));
}

void main() {
  vec2 screenUv = gl_FragCoord.xy / uResolution;
  float aspect = uResolution.x / uResolution.y;
  vec2 uv = vec2(screenUv.x * aspect, screenUv.y);

  // Mouse displacement — like dragging brush through wet paint
  vec2 mouseUv = vec2(uMouse.x * aspect, uMouse.y);
  float mouseDist = length(uv - mouseUv);
  vec2 mouseDisplace = (uv - mouseUv) * smoothstep(0.4, 0.0, mouseDist) * 0.15;

  // Scroll shifts noise offset — painting evolves
  vec2 noiseUv = uv + mouseDisplace + vec2(uScroll * 2.0, uScroll * 0.5);

  // Chapter-aware frequency scaling
  float freqScale = 1.0 + uChapter * 0.15;

  // Layer noise octaves — mobile skips third octave
  float n1 = snoise(noiseUv * 2.0 * freqScale + uTime * 0.05) * 0.6;
  float n2 = snoise(noiseUv * 4.0 * freqScale - uTime * 0.03) * 0.3;
  float noise;
  if (uMobile > 0.5) {
    noise = (n1 + n2) * (1.0 + uVelocity * 0.3);
  } else {
    float n3 = snoise(noiseUv * 8.0 * freqScale + uTime * 0.02) * 0.1;
    noise = (n1 + n2 + n3) * (1.0 + uVelocity * 0.3);
  }

  // Quantize to watercolor-like flat bands (4 levels)
  float quantized = floor(noise * 4.0 + 0.5) / 4.0;

  // Map to chapter-aware color palette
  float h = uChapterHue + quantized * 0.08;
  float s = 0.35 + quantized * 0.15;
  float l = uChapterLightness + 0.1 + quantized * 0.12;
  vec3 color = hsl2rgb(h, s, l);

  // Edge detection via screen-space derivatives — desktop only
  if (uMobile < 0.5) {
    float edge = length(vec2(dFdx(noise), dFdy(noise))) * 80.0;
    float edgeLine = smoothstep(0.15, 0.35, edge);
    color = mix(color, color * 0.6, edgeLine * 0.4);
  }

  gl_FragColor = vec4(color, 1.0);
}
```

**Performance:** ~1.0ms per frame on integrated GPU (desktop with edge detection), ~0.6ms on mobile (2 octaves, no edges). Uses hardware `dFdx`/`dFdy` instead of 4 extra noise samples for edge detection.

---

## Preset 3: domain-warp

Progressive sinusoidal domain warping. Same core technique as `rocaille-shader` but simplified for background use, with scroll-driven warp count.

```glsl
uniform vec2 uResolution;
uniform vec2 uMouse;
uniform float uScroll;
uniform float uTime;
uniform float uVelocity;
uniform float uChapter;
uniform float uChapterHue;
uniform float uChapterLightness;

vec3 hsl2rgb(float h, float s, float l) {
  vec3 rgb = clamp(abs(mod(h * 6.0 + vec3(0.0, 4.0, 2.0), 6.0) - 3.0) - 1.0, 0.0, 1.0);
  return l + s * (rgb - 0.5) * (1.0 - abs(2.0 * l - 1.0));
}

void main() {
  vec2 screenUv = gl_FragCoord.xy / uResolution;
  float aspect = uResolution.x / uResolution.y;
  vec2 uv = vec2(screenUv.x * aspect, screenUv.y);

  // Mouse offset
  vec2 mouseUv = vec2(uMouse.x * aspect, uMouse.y);
  vec2 mouseOffset = (uv - mouseUv) * smoothstep(0.5, 0.0, length(uv - mouseUv)) * 0.1;

  vec2 v = uv * 2.0 - 1.0 + mouseOffset;

  // Chapter offset gives each chapter a different warp seed
  float t = uTime * 0.3 + uChapter * 0.5;

  // Scroll drives complexity: 2 warps at top → 6 warps at bottom
  int warpCount = int(mix(2.0, 6.0, uScroll));

  // Progressive domain warping — velocity amplifies displacement
  float amplitude = 2.0;
  for (int i = 0; i < 6; i++) {
    if (i >= warpCount) break;
    v += sin(v.yx * (1.0 + float(i) * 0.3) + t) / amplitude * (1.0 + uVelocity * 0.4);
    amplitude += 0.5;
  }

  // Map warped coordinates to color
  float h = uChapterHue + v.x * 0.05 + v.y * 0.03;
  float s = 0.4 + sin(v.x * 3.0) * 0.15;
  float l = uChapterLightness + 0.15 + sin(v.y * 2.0 + v.x) * 0.1;
  vec3 color = hsl2rgb(h, s, clamp(l, 0.05, 0.85));

  gl_FragColor = vec4(color, 1.0);
}
```

**Performance:** ~0.3ms per frame (2 warps) to ~0.8ms (6 warps). The lightest preset at low scroll, builds complexity as the reader goes deeper.

---

---

## Uniform Pipeline

Pipeline for feeding Lenis scroll data and cursor position into Three.js shader uniforms. Never feed raw values — always lerp for smooth visual transitions.

```
Lenis scroll event → normalize to 0-1 → lerp in animation loop → shader uniform
Mouse event         → normalize to 0-1 → lerp in animation loop → shader uniform
                                          ↑
                               GSAP ticker (single rAF)
```

### Scroll Progress Normalization

```js
let scrollProgress = 0;
lenis.on('scroll', ({ scroll, limit }) => {
  scrollProgress = limit > 0 ? scroll / limit : 0; // 0.0 at top, 1.0 at bottom
});
```

### Mouse Position Normalization

```js
let mouseTarget = { x: 0.5, y: 0.5 };

document.addEventListener('mousemove', (e) => {
  mouseTarget.x = e.clientX / window.innerWidth;
  mouseTarget.y = 1.0 - (e.clientY / window.innerHeight); // Flip Y for GL coordinates
});

document.addEventListener('touchmove', (e) => {
  const touch = e.touches[0];
  mouseTarget.x = touch.clientX / window.innerWidth;
  mouseTarget.y = 1.0 - (touch.clientY / window.innerHeight);
}, { passive: true });
```

### Full Uniform Declarations

```js
const uniforms = {
  uTime:              { value: 0 },
  uScroll:            { value: 0 },
  uMouse:             { value: new THREE.Vector2(0.5, 0.5) },
  uResolution:        { value: new THREE.Vector2(window.innerWidth, window.innerHeight) },
  uVelocity:          { value: 0 },
  uChapter:           { value: 0 },
  uMobile:            { value: isMobile ? 1.0 : 0.0 },
  uChapterHue:        { value: 0.694 },
  uChapterLightness:  { value: 0.25 }
};
```

### Smoothed Updates in the Animation Loop

All uniform updates happen inside the GSAP ticker — the single animation frame that also drives Lenis and the Three.js renderer. Use a JS-side `shaderState` object tweened by GSAP to avoid per-frame `getComputedStyle` calls:

```js
let scrollVelocity = 0;
lenis.on('scroll', ({ velocity }) => {
  scrollVelocity = velocity;
});

const shaderState = { hue: 250, lightness: 0.25 };

gsap.ticker.add((time) => {
  lenis.raf(time * 1000);

  uniforms.uScroll.value += (scrollProgress - uniforms.uScroll.value) * 0.05;
  uniforms.uMouse.value.x += (mouseTarget.x - uniforms.uMouse.value.x) * 0.08;
  uniforms.uMouse.value.y += (mouseTarget.y - uniforms.uMouse.value.y) * 0.08;

  const clampedVelocity = Math.min(Math.max(scrollVelocity, -3), 3);
  uniforms.uVelocity.value += (Math.abs(clampedVelocity) / 3 - uniforms.uVelocity.value) * 0.10;

  uniforms.uTime.value = time;

  uniforms.uChapterHue.value += (shaderState.hue / 360.0 - uniforms.uChapterHue.value) * 0.03;
  uniforms.uChapterLightness.value += (shaderState.lightness - uniforms.uChapterLightness.value) * 0.03;

  renderer.render(scene, camera);
});
```

### Lerp Rates

| Uniform | Lerp Rate | Resulting Lag | Why |
|---------|-----------|--------------|-----|
| `uScroll` | 0.05 | ~400ms | Background follows scroll with organic lag |
| `uMouse` | 0.08 | ~250ms | Responsive cursor influence that glides, not twitches |
| `uVelocity` | 0.10 | ~200ms | Velocity effects persist briefly after scroll stops |
| `uChapter` | 0.03 | ~600ms | Very smooth chapter transitions |
| `uChapterHue` | 0.03 | ~600ms | Hue shift follows CSS transition, not jumps |
| `uChapterLightness` | 0.03 | ~600ms | Lightness shift in sync with hue |

Lower lerp rate = more lag = smoother. Higher = more responsive.

### Chapter-Aware Tracking

Track which chapter is currently active as a smooth float:

```js
let currentChapter = 0;
const sections = document.querySelectorAll('.chapter');

sections.forEach((section, i) => {
  ScrollTrigger.create({
    trigger: section,
    start: 'top center',
    end: 'bottom center',
    onUpdate: (self) => { currentChapter = i + self.progress; }
  });
});

// In animation loop
uniforms.uChapter.value += (currentChapter - uniforms.uChapter.value) * 0.03;
```

### Velocity-Driven Shader Effects

Scroll velocity drives visual intensity per preset:

```glsl
uniform float uVelocity;

// painted-dots: expand dot radius
float radius = baseRadius * (1.0 + uVelocity * 0.5);

// watercolor: intensify noise
float noise = baseNoise * (1.0 + uVelocity * 0.3);

// domain-warp: amplify warp
float warpAmp = baseAmp * (1.0 + uVelocity * 0.4);
```

Clamp velocity to ±3 before feeding to the uniform.

### Resize Handler

Call `setPixelRatio()` before `setSize()` to avoid double framebuffer allocation:

```js
let resizeTimeout;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimeout);
  resizeTimeout = setTimeout(() => {
    const w = window.innerWidth, h = window.innerHeight;
    const mobile = w <= 768;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, mobile ? 1.5 : 2.0));
    renderer.setSize(w, h);
    uniforms.uResolution.value.set(w, h);
    uniforms.uMobile.value = mobile ? 1.0 : 0.0;
  }, 80);
});
```

### Reduced Motion

When `prefers-reduced-motion` is active, freeze shader animation:

```js
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

if (reducedMotion) {
  renderer.render(scene, camera);
} else {
  gsap.ticker.add(tickCallback);
}
```

---

## Performance Comparison

| Preset | Typical Frame Time | GPU Pressure | Best For |
|--------|-------------------|-------------|----------|
| `painted-dots` | ~0.5ms | Low | Any device, editorial sites |
| `watercolor` | ~1.5ms | Medium | Desktop-first, artistic sites |
| `domain-warp` | 0.3–0.8ms | Low → Medium | Progressive complexity, story depth |
