# Anti-Patterns

What Claude gets wrong when building cinematic scrolltelling sites. Each entry: mistake, symptom, correct approach, and code.

---

### 1. Dual Animation Loops

**Wrong:**
```js
// Three.js has its own loop
function animate() {
  requestAnimationFrame(animate);
  renderer.render(scene, camera);
}
animate();

// GSAP has its own loop
gsap.ticker.add(() => { /* animations */ });
```

**Symptom:** Two competing rAF callbacks fire per frame — inconsistent timing, shader animations stutter, scroll animations desync from rendering.

**Right:**
```js
// Single loop via GSAP ticker drives everything
gsap.ticker.add((time) => {
  lenis.raf(time * 1000);
  uniforms.uTime.value = time;
  renderer.render(scene, camera);
});
```

**Why:** One animation frame per display refresh. GSAP ticker is the master clock — it drives Lenis, updates uniforms, and triggers the Three.js render.

---

### 2. Lenis autoRaf: true with GSAP

**Wrong:**
```js
const lenis = new Lenis(); // autoRaf defaults to true
```

**Symptom:** Lenis creates its own rAF loop alongside GSAP's. Double frame updates, scroll position mismatches, stuttering.

**Right:**
```js
const lenis = new Lenis({ autoRaf: false });
gsap.ticker.add((time) => lenis.raf(time * 1000));
```

**Why:** `autoRaf: false` tells Lenis to wait for external timing. GSAP delivers synchronized ticks.

---

### 3. sRGB Color Interpolation

**Wrong:**
```js
gsap.to('body', {
  backgroundColor: '#FF6B35', // sRGB interpolation
  scrollTrigger: { trigger: section, scrub: 1 }
});
```

**Symptom:** Transitioning from blue (#2563EB) to orange (#FF6B35) passes through muddy grey/brown midpoint.

**Right:**
```js
// Register @property for OKLCH components
CSS.registerProperty({ name: '--sc-hue', syntax: '<angle>', inherits: true, initialValue: '0deg' });

gsap.to(':root', {
  '--sc-hue': '25deg',
  '--sc-chroma': 0.20,
  '--sc-lightness': 0.55,
  scrollTrigger: { trigger: section, scrub: 1 }
});

// CSS: body { background-color: oklch(var(--sc-lightness) var(--sc-chroma) var(--sc-hue)); }
```

**Why:** OKLCH interpolates through perceptually uniform color space — midpoints stay vibrant instead of desaturating.

---

### 4. position: fixed on Three.js Canvas Inside Lenis Wrapper

**Wrong:**
```css
canvas { position: fixed; top: 0; left: 0; z-index: -1; }
/* ...while canvas is INSIDE the Lenis scroll wrapper */
```

**Symptom:** Canvas scrolls with content or creates layout conflicts with Lenis's transform-based scrolling.

**Right:**
```css
/* Canvas OUTSIDE the Lenis wrapper, or: */
canvas { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; pointer-events: none; }
/* Ensure canvas element is a sibling of (not child of) the scroll wrapper */
```

**Why:** Lenis transforms its wrapper via `translate3d`. Fixed-position children inside a transformed parent resolve relative to the parent, not the viewport.

---

### 5. Raw Scroll Position in Shaders

**Wrong:**
```js
lenis.on('scroll', ({ scroll }) => {
  material.uniforms.uScroll.value = scroll / limit; // Direct assignment
});
```

**Symptom:** Shader background jerks with every scroll event. Visually harsh, reveals the frame-by-frame nature of scroll.

**Right:**
```js
let scrollProgress = 0;
lenis.on('scroll', ({ scroll, limit }) => { scrollProgress = scroll / limit; });

// In animation loop — lerp
uniforms.uScroll.value += (scrollProgress - uniforms.uScroll.value) * 0.05;
```

**Why:** Lerping smooths the transition over multiple frames. The background follows scroll with organic lag — ambient, not mechanical.

---

### 6. ScrollSmoother Dependency

**Wrong:**
```js
import { ScrollSmoother } from 'gsap/ScrollSmoother';
ScrollSmoother.create({ smooth: 1, effects: true });
```

**Symptom:** Code fails in production — ScrollSmoother requires GSAP Club membership ($99+/year).

**Right:**
```js
const lenis = new Lenis({ autoRaf: false });
// Lenis is free, MIT-licensed, and provides equivalent smooth scrolling
```

**Why:** Lenis is free and provides the same smooth scroll behavior. No paid dependency required.

---

### 7. Missing lagSmoothing(0)

**Wrong:**
```js
gsap.ticker.add((time) => lenis.raf(time * 1000));
// lagSmoothing left at default
```

**Symptom:** During lag frames (complex DOM, slow GPU), GSAP caps frame time — Lenis's interpolation jumps forward visibly instead of catching up smoothly.

**Right:**
```js
gsap.ticker.add((time) => lenis.raf(time * 1000));
gsap.ticker.lagSmoothing(0);
```

**Why:** Disabling lag smoothing lets GSAP report actual elapsed time. Lenis handles its own smoothing — it doesn't need GSAP to cap time.

---

### 8. transition: all on Sections

**Wrong:**
```css
.chapter { transition: all 0.5s ease; }
```

**Symptom:** Every property change triggers layout + paint. Scroll-driven updates cause massive repaints. FPS drops.

**Right:**
```css
.chapter-content {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
```

**Why:** Explicitly list only `opacity` and `transform` — both are compositor-only properties. No layout or paint triggered.

---

### 9. innerHTML for Chapter Text

**Wrong:**
```js
section.innerHTML = `<h2>${chapterTitle}</h2><p>${chapterBody}</p>`;
```

**Symptom:** XSS vulnerability if chapter content comes from user input or CMS. Also destroys event listeners.

**Right:**
```js
const h2 = document.createElement('h2');
h2.textContent = chapterTitle;
h2.className = 'chapter-title';
const p = document.createElement('p');
p.textContent = chapterBody;
p.className = 'chapter-body';
section.appendChild(h2);
section.appendChild(p);
```

**Why:** `textContent` escapes HTML entities. DOM construction preserves existing event listeners and avoids injection.

---

### 10. Missing Cleanup / Destroy

**Wrong:**
```js
// Component unmounts, page navigates — nothing cleaned up
```

**Symptom:** Memory leaks. Ghost scroll listeners. Multiple Lenis instances stacking. Three.js contexts exhausting GPU memory.

**Right:**
```js
function cleanup() {
  gsap.ticker.remove(tickCallback);
  lenis.destroy();
  ScrollTrigger.killAll();
  if (renderer) {
    renderer.dispose();
    renderer.forceContextLoss();
    renderer.domElement.remove();
  }
}
```

**Why:** Each library allocates listeners and GPU resources. Explicit cleanup is mandatory for SPAs, page transitions, and hot-reload.

---

### 11. Animating CSS background-color Directly

**Wrong:**
```js
gsap.to('body', { backgroundColor: '#1a2332', scrollTrigger: { scrub: 1 } });
```

**Symptom:** Triggers paint on every frame during scroll. Slower than necessary, especially on mobile.

**Right:**
```js
CSS.registerProperty({ name: '--sc-lightness', syntax: '<number>', inherits: true, initialValue: '0.25' });
gsap.to(':root', { '--sc-lightness': 0.4, scrollTrigger: { scrub: 1 } });
// CSS: body { background-color: oklch(var(--sc-lightness) var(--sc-chroma) var(--sc-hue)); }
```

**Why:** Registered custom properties animate on the compositor thread. No layout or paint — GPU-accelerated color transitions.

---

### 12. No prefers-reduced-motion

**Wrong:**
```js
// Animations run regardless of user preference
```

**Symptom:** Accessibility violation. Users with vestibular disorders experience discomfort from scroll-driven animations.

**Right:**
```css
@media (prefers-reduced-motion: reduce) {
  .chapter-content { transition: none !important; }
  * { animation: none !important; }
}
```
```js
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
if (reducedMotion) {
  // Show all chapters in final state
  document.querySelectorAll('.chapter-content').forEach(el => {
    el.style.opacity = '1';
    el.style.transform = 'none';
  });
  // Render one static shader frame, then stop
  renderer.render(scene, camera);
  // Revert Lenis to native scroll
  lenis.destroy();
}
```

**Why:** Respecting user preferences is non-negotiable. Content must be accessible without motion.

---

### 13. will-change Left On Permanently

**Wrong:**
```css
.chapter-content { will-change: opacity, transform; }
```

**Symptom:** GPU reserves memory for every chapter simultaneously. On pages with 5+ chapters, GPU memory usage spikes. Mobile devices may drop frames.

**Right:**
```js
// Add before animation
element.style.willChange = 'opacity, transform';
gsap.from(element, {
  opacity: 0, y: 60,
  onComplete: () => { element.style.willChange = 'auto'; }
});
```

**Why:** `will-change` creates a new compositor layer. Useful during animation, wasteful when static. Add → animate → remove.
