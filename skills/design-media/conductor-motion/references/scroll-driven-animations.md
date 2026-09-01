# Scroll-Driven Animations

Three tiers: CSS-native (Baseline, prefer it), IntersectionObserver (legacy fallback), GSAP ScrollTrigger (optional enhancement).

## Tier 1: CSS Scroll-Driven (Baseline — all major browsers)

Chrome 115+, Edge 115+, Firefox 128+, Safari 18+. This is no longer a progressive enhancement — it is the default scroll mechanism, with IntersectionObserver as the fallback for older browsers. CSS timelines run on the compositor thread: zero main-thread work, zero INP cost, immune to jank from busy JS. An IntersectionObserver reveal can block on the main thread; `animation-timeline` cannot.

```css
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: none; }
}

.scroll-reveal {
  animation: fade-in-up linear backwards;
  animation-timeline: view();
  animation-range: entry 0% entry 30%;
}
```

Use `animation-fill-mode: backwards`, not `both` — `both` sits in a higher cascade origin than `@starting-style`, so a `both` fill silently overrides any entry transition on the same element (Bramus, Nov 2025). `backwards` composes cleanly.

### `animation-timeline` Values

| Value | Behavior |
|-------|----------|
| `scroll()` | Progress-based, tied to scroll container |
| `view()` | Tied to element entering/exiting viewport |
| `scroll(root)` | Tied to document scroll |
| `scroll(nearest)` | Tied to nearest scrollable ancestor |

### `animation-range` Values

| Range | When it plays |
|-------|---------------|
| `entry 0% entry 100%` | Element entering viewport (bottom edge in → top edge in) |
| `exit 0% exit 100%` | Element exiting viewport |
| `contain 0% contain 100%` | Element fully visible |
| `entry 0% entry 30%` | First 30% of entry — quick reveal |

### Feature Detection

```css
@supports (animation-timeline: view()) {
  .scroll-reveal {
    animation: fade-in-up linear both;
    animation-timeline: view();
    animation-range: entry 0% entry 30%;
  }
}
```

## Tier 2: IntersectionObserver (Universal Fallback)

```javascript
function initScrollReveals(selector, options = {}) {
  const {
    threshold = 0.1,
    rootMargin = '0px 0px -50px 0px',
    stagger = 100,
    once = true
  } = options;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const children = entry.target.querySelectorAll('.reveal-child');
        if (children.length) {
          children.forEach((child, i) => {
            child.style.transitionDelay = `${i * stagger}ms`;
            child.classList.add('is-visible');
          });
        } else {
          entry.target.classList.add('is-visible');
        }
        if (once) observer.unobserve(entry.target);
      }
    });
  }, { threshold, rootMargin });

  document.querySelectorAll(selector).forEach(el => observer.observe(el));
}
```

### Threshold Array for Progress

```javascript
const thresholds = Array.from({ length: 20 }, (_, i) => i / 19);

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    const progress = entry.intersectionRatio;
    entry.target.style.setProperty('--scroll-progress', progress);
  });
}, { threshold: thresholds });
```

Use with CSS:
```css
.parallax-element {
  transform: translateY(calc(var(--scroll-progress, 0) * -30px));
  opacity: var(--scroll-progress, 0);
}
```

## Tier 3: GSAP ScrollTrigger (Optional)

CDN:
```html
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15/dist/gsap.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15/dist/ScrollTrigger.min.js"></script>
```

```javascript
gsap.registerPlugin(ScrollTrigger);

gsap.from('.feature-card', {
  y: 40,
  opacity: 0,
  duration: 0.8,
  stagger: 0.15,
  scrollTrigger: {
    trigger: '.features-section',
    start: 'top 80%',
    toggleActions: 'play none none none'
  }
});
```

### Pin + Scrub (scroll-linked progress)

```javascript
gsap.to('.progress-fill', {
  scaleX: 1,
  transformOrigin: 'left center',
  scrollTrigger: {
    trigger: '.progress-section',
    start: 'top center',
    end: 'bottom center',
    scrub: true
  }
});
```

### License Note

GSAP is fully free since 3.13 (April 2025, post-Webflow acquisition) — every plugin included, the formerly-paid Club plugins among them (SplitText, ScrambleText, MorphSVG, Flip, ScrollSmoother). No Business license for SaaS, no registration, no keys. SplitText and ScrambleText are directly relevant here: they cover per-character splitting and decode effects that the typewriter and terminal patterns build by hand — reach for them only when a page already loads GSAP; the vanilla implementations stay the default.

## Progressive Enhancement Strategy

```
Base layer (no-JS / reduced-motion):
  All content visible, no animation

Primary layer (CSS scroll-driven):
  @supports (animation-timeline: view()) { ... }
  Compositor-thread, zero JS, zero INP cost

Fallback layer (IntersectionObserver, older browsers):
  .scroll-reveal { opacity: 0; transform: translateY(20px); }
  .scroll-reveal.is-visible { opacity: 1; transform: none; }
  Gate in JS: if (CSS.supports('animation-timeline: view()')) skip attaching

Optional layer (GSAP):
  Complex choreography, pin-and-scrub, multi-element timelines
```

Implementation order: start with the base layer, write the CSS scroll-driven path as primary, attach IntersectionObserver only where `animation-timeline` is unsupported, and reach for GSAP only when choreography outgrows both.

## Parallax

```javascript
function initParallax(selector, speed = 0.3) {
  const els = document.querySelectorAll(selector);
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  function tick() {
    els.forEach(el => {
      const rect = el.getBoundingClientRect();
      const centerY = rect.top + rect.height / 2;
      const viewCenter = window.innerHeight / 2;
      const offset = (centerY - viewCenter) * speed;
      el.style.transform = `translateY(${offset}px)`;
    });
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}
```

Speed values: 0.1 (subtle), 0.3 (medium), 0.5 (dramatic). Negative values reverse direction.

## Reduced Motion

Disable all scroll animations:
```css
@media (prefers-reduced-motion: reduce) {
  .scroll-reveal,
  .parallax-element {
    opacity: 1 !important;
    transform: none !important;
    transition: none !important;
    animation: none !important;
  }
}
```

```javascript
if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  // Skip all scroll animation initialization
  document.querySelectorAll('.scroll-reveal').forEach(el => {
    el.classList.add('is-visible');
  });
  return;
}
```
