# Stagger Reveal Patterns

Cascading content entrance animations — hero reveals, section reveals, and scroll-triggered variants.

## Hero Cascade Reveal

Page-load entrance: elements cascade in with staggered delay.

### Technique: `@starting-style` (Preferred)

`@starting-style` defines the state an element transitions *from* on first render — the browser handles the initial-to-final transition natively, no JS trigger at all. Chrome 117+, Safari 17.5+, Firefox 129+ (86%+ global support).

```css
.hero-item {
  opacity: 1;
  transform: none;
  transition: opacity 1.3s ease-in-out, transform 1.3s ease-in-out;
}

@starting-style {
  .hero-item {
    opacity: 0;
    transform: translateY(10px);
  }
}

/* Stagger stays in CSS: */
.hero-item:nth-child(1) { transition-delay: 0ms; }
.hero-item:nth-child(2) { transition-delay: calc(1 * var(--cm-stagger)); }
.hero-item:nth-child(3) { transition-delay: calc(2 * var(--cm-stagger)); }

@media (prefers-reduced-motion: reduce) {
  .hero-item { transition: none !important; }
}
```

Content is visible by default (`opacity: 1` is the resting rule), so a JS failure or JS-disabled browser shows the finished page — no gating class required. One cascade caveat: an `animation` with `fill-mode: both` on the same element overrides `@starting-style` (animations sit in a higher cascade origin). Use `animation-fill-mode: backwards` when mixing, or keep entry transitions and keyframe animations on separate elements.

### Technique: CSS Transitions + JS Class Toggle (Fallback)

```css
.hero-item {
  transition: opacity 1.3s ease-in-out, transform 1.3s ease-in-out;
  /* will-change is set from JS just before the reveal and removed on
     transitionend — never left in resting CSS (reserves GPU memory) */
}

html:not(.reveal-ready) .hero-item {
  opacity: 0;
  transform: translateY(10px);
}

html.reveal-ready .hero-item {
  opacity: 1;
  transform: none;
}

@media (prefers-reduced-motion: reduce) {
  .hero-item { transition: none !important; }
}
```

### JS Trigger

```javascript
const items = [
  '.hero-content',
  '.hero-buttons',
  '.hero-stats',
  '.hero-visual',
  '.hero-progress',
  '.hero-files'
];

function initHeroReveal() {
  const els = items.map(s => document.querySelector(s)).filter(Boolean);
  if (!els.length) return;

  els.forEach((el, index) => {
    el.style.transitionDelay = `${index * 200}ms`;
  });

  // Double rAF ensures styles are applied before class toggle
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      document.documentElement.classList.add('reveal-ready');
    });
  });
}
```

### Double rAF Technique

Why two nested `requestAnimationFrame` calls? The first schedules the callback for the next paint. The second ensures the initial styles (opacity: 0, translateY) have been computed and applied before toggling the class. Without this, the browser may batch the style changes and skip the transition.

This trick exists to fake what `@starting-style` now does natively. Reach for it only when supporting browsers older than Chrome 117 / Safari 17.5 / Firefox 129, or when the reveal must be triggered by something other than first render.

### Fade-Only Elements

Some elements only fade (no transform):
```css
html:not(.reveal-ready) .hero-visual {
  opacity: 0;
  /* no translateY — just fades in place */
}
```

```javascript
// will-change lifecycle: add just before animating, remove after
el.style.willChange = 'opacity, transform';
el.addEventListener('transitionend', () => { el.style.willChange = ''; }, { once: true });
```

## Section Reveal (IntersectionObserver)

Scroll-triggered reveals for content sections below the fold.

### Observer Setup

```javascript
function initSectionReveals() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        // Stagger children
        const children = entry.target.querySelectorAll('.reveal-child');
        children.forEach((child, i) => {
          child.style.transitionDelay = `${i * 100}ms`;
        });
        observer.unobserve(entry.target); // one-shot
      }
    });
  }, {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  });

  document.querySelectorAll('.section-reveal').forEach(el => observer.observe(el));
}
```

### CSS

```css
.reveal-child {
  opacity: 0;
  transform: translateY(20px);
  transition:
    opacity 600ms var(--cm-ease-out-cubic),
    transform 600ms var(--cm-ease-out-cubic);
}

.section-reveal.is-visible .reveal-child {
  opacity: 1;
  transform: none;
}
```

### rootMargin

`-50px` on the bottom triggers slightly before the element is fully in view — prevents the user from seeing the "pop" right at the viewport edge.

## Scroll-Triggered Variants

### Navbar Border on Scroll

```javascript
window.addEventListener('scroll', () => {
  const navbar = document.querySelector('.navbar');
  if (!navbar) return;
  navbar.style.borderBottomColor = window.scrollY === 0
    ? 'var(--cm-border-subtle)'
    : 'var(--cm-border)';
});
```

### Parallax

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

### CSS Scroll-Driven (Primary — Baseline all browsers)

```css
@supports (animation-timeline: view()) {
  .scroll-reveal {
    animation: fade-in-up linear backwards;
    animation-timeline: view();
    animation-range: entry 0% entry 30%;
  }

  @keyframes fade-in-up {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: none; }
  }
}
```

Prefer this over IntersectionObserver for section reveals — it runs on the compositor thread and costs nothing at interaction time. Gate the observer path in JS so the two never fight:

```javascript
if (!CSS.supports('animation-timeline: view()')) {
  initSectionReveals(); // IO fallback for older browsers
}
```

Fill mode is `backwards`, not `both` — `both` overrides `@starting-style` entry transitions on the same element.

### `content-visibility` for Long Pages

Multi-section pages benefit from skipping layout and paint for off-screen sections:

```css
.below-fold-section {
  content-visibility: auto;
  contain-intrinsic-size: auto 600px; /* reserve space, prevent scrollbar jumps */
}
```

## Configurable Parameters

| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| Stagger delay | 200ms | 100-400 | Gap between sequential reveals |
| Transition duration | 1300ms | 600-2000 | How long each item takes to appear |
| Translate Y | 10px | 5-40 | Initial offset distance |
| Direction | up | up/down/left/right | Transform direction |
| Observer threshold | 0.1 | 0-1 | How much visible before triggering |

Direction variants:
```css
[data-direction="down"]  { transform: translateY(-10px); }
[data-direction="left"]  { transform: translateX(20px); }
[data-direction="right"] { transform: translateX(-20px); }
```

## Reduced Motion

All elements visible immediately, no transitions:
```css
@media (prefers-reduced-motion: reduce) {
  .hero-item,
  .reveal-child {
    opacity: 1 !important;
    transform: none !important;
    transition: none !important;
    transition-delay: 0ms !important;
  }
}
```
