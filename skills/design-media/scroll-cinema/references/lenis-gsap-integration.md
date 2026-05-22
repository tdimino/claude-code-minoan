# Lenis + GSAP ScrollTrigger Integration

The most critical integration in scroll-cinema. Lenis and GSAP ScrollTrigger both want to control the animation loop — if both run their own `requestAnimationFrame`, animations stutter, triggers fire at wrong positions, and scroll feels broken.

## Non-Negotiable Initialization Sequence

```js
import Lenis from 'lenis';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { CustomEase } from 'gsap/CustomEase';

// Step 1: Register GSAP plugins FIRST — before any animation code
gsap.registerPlugin(ScrollTrigger, CustomEase);

// Step 2: Define cinematic easings
CustomEase.create("cinematicSilk",   "0.45,0.05,0.55,0.95");
CustomEase.create("cinematicSmooth", "0.25,0.1,0.25,1");
CustomEase.create("cinematicFlow",   "0.33,0,0.2,1");
CustomEase.create("cinematicLinear", "0.4,0,0.6,1");

// Step 3: Init Lenis with autoRaf OFF — GSAP drives the loop
const lenis = new Lenis({ autoRaf: false });

// Step 4: Connect Lenis to GSAP ticker
const lenisRafCallback = (time) => {
  lenis.raf(time * 1000); // GSAP time is in seconds, Lenis expects milliseconds
};
gsap.ticker.add(lenisRafCallback);

// Step 5: Disable lag smoothing — prevents jumps in Lenis interpolation
gsap.ticker.lagSmoothing(0);

// Step 6: Sync ScrollTrigger with Lenis scroll position
lenis.on('scroll', ScrollTrigger.update);
```

## Why Each Step Matters

### `autoRaf: false`

Lenis's default (`autoRaf: true`) creates its own `requestAnimationFrame` loop. With GSAP also running rAF, two competing animation frames fire per display refresh — inconsistent timing, scroll position mismatches, and visible stutter. Setting `autoRaf: false` tells Lenis to wait for an external tick.

### `time * 1000`

GSAP's ticker delivers time in **seconds**. Lenis's `.raf()` expects **milliseconds**. Omitting the multiplication makes Lenis run 1000x too slow — scroll appears frozen or moves in imperceptible micro-increments.

### `lagSmoothing(0)`

GSAP's default lag smoothing caps frame time during slow frames (when the browser lags). This creates visible jumps in Lenis's smooth interpolation — the scroll position snaps forward instead of gliding.

### `ScrollTrigger.update` in scroll callback

Without this, ScrollTrigger reads the scroll position from the native DOM — but Lenis is intercepting scroll. ScrollTrigger's triggers fire at wrong positions or not at all.

## Cleanup / Destroy

Critical for SPAs, page transitions, and React/Astro/Next.js unmounts:

```js
function cleanup() {
  // Remove the GSAP ticker callback
  gsap.ticker.remove(lenisRafCallback);

  // Destroy Lenis instance (stops smooth scroll, removes listeners)
  lenis.destroy();

  // Kill all ScrollTrigger instances (removes scroll listeners, markers)
  ScrollTrigger.killAll();

  // If Three.js is present, dispose renderer
  if (renderer) {
    renderer.dispose();
    renderer.forceContextLoss();
    renderer.domElement.remove();
  }
}
```

## Anchor Link Fix

Lenis intercepts native anchor clicks. Smooth-scroll to anchors explicitly:

```js
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', (e) => {
    e.preventDefault();
    const target = document.querySelector(anchor.getAttribute('href'));
    if (target) lenis.scrollTo(target, { offset: 0, duration: 1.2 });
  });
});
```

## React / SPA Lifecycle

> **Note:** The generator produces vanilla HTML (Implementation Rule #1). This React example is for teams embedding scroll-cinema output inside an existing SPA — it shows correct cleanup, not a recommended stack.

```jsx
useEffect(() => {
  gsap.registerPlugin(ScrollTrigger);

  const lenis = new Lenis({ autoRaf: false });
  const tick = (time) => lenis.raf(time * 1000);
  gsap.ticker.add(tick);
  gsap.ticker.lagSmoothing(0);
  lenis.on('scroll', ScrollTrigger.update);

  // ScrollTrigger.refresh() after DOM hydration
  requestAnimationFrame(() => ScrollTrigger.refresh());

  return () => {
    gsap.ticker.remove(tick);
    lenis.destroy();
    ScrollTrigger.killAll();
  };
}, []);
```

## Common Misconfigurations

| Mistake | Symptom | Fix |
|---------|---------|-----|
| `autoRaf: true` with GSAP | Double rAF, visible stutter | `autoRaf: false` |
| Missing `lagSmoothing(0)` | Scroll jumps on lag frames | `gsap.ticker.lagSmoothing(0)` |
| No `ScrollTrigger.update` in scroll callback | Triggers fire at wrong positions | `lenis.on('scroll', ScrollTrigger.update)` |
| Using ScrollSmoother | Requires GSAP Club (paid) | Use Lenis instead (free, equivalent) |
| Missing cleanup | Memory leaks, ghost listeners | Call destroy/killAll on unmount |
| `lenis.raf(time)` without `* 1000` | Lenis runs 1000x too slow | GSAP delivers seconds, Lenis expects ms |
| `ScrollTrigger.refresh()` before DOM ready | Triggers calculate wrong positions | Call after `requestAnimationFrame` or `DOMContentLoaded` |
| Lenis wrapper missing CSS | Scroll container not configured | Import `lenis/dist/lenis.css` or add `html.lenis { height: auto; }` |

## Lenis CSS Requirements

```css
html.lenis, html.lenis body {
  height: auto;
}
.lenis.lenis-smooth {
  scroll-behavior: auto !important;
}
.lenis.lenis-smooth [data-lenis-prevent] {
  overscroll-behavior: contain;
}
.lenis.lenis-stopped {
  overflow: hidden;
}
```

Or import the stylesheet: `<link rel="stylesheet" href="https://unpkg.com/lenis@1.2.3/dist/lenis.css">`
