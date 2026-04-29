# Pellicola Animation System

Declarative scroll-choreographed reveals using `data-pel` attributes and IntersectionObserver. No animation library required.

## Architecture

Every animated element carries a `data-pel` attribute. A single IntersectionObserver watches all `[data-pel]` elements, adding `.is-visible` when the element enters the viewport. CSS handles the transition.

```
[data-pel] (hidden state)  →  IntersectionObserver fires  →  .is-visible (revealed state)
```

## Attribute Reference

| Attribute | Effect | CSS Transform | Duration |
|-----------|--------|--------------|----------|
| `data-pel="y"` | Slide up + fade | `translateY(40px) → none` | `--pel-duration` (0.8s) |
| `data-pel="alpha"` | Fade only | `opacity: 0 → 1` | `--pel-duration` (0.8s) |
| `data-pel="line"` | Horizontal line reveal | `::after scaleX(0 → 1)` | `--pel-duration` (0.8s) |
| `data-pel="parallax"` | Parallax scroll offset | JS-driven `translateY` | Continuous |
| `data-pel="stagger"` | Children cascade | Per-child `translateY(20px → 0)` | 0.1s delay each |
| `data-pel="title"` | Split text line reveal | Per-line `translateY(100%) → 0` | 0.12s delay/line |

## CSS Setup

### Base Hidden State

```css
[data-pel] {
  opacity: 0;
  transition:
    opacity var(--pel-duration) var(--pel-ease),
    transform var(--pel-duration) var(--pel-ease);
}

[data-pel="y"] {
  transform: translateY(40px);
}

[data-pel="alpha"] {
  transform: none;
}
```

### Revealed State

```css
[data-pel].is-visible {
  opacity: 1;
  transform: none;
}
```

### Line Reveal (Section Dividers)

The `pel-divider` uses `::after` for the line. The line scales from left origin.

```css
[data-pel="line"]::after {
  transform: scaleX(0);
  transition: transform var(--pel-duration) var(--pel-ease);
}

[data-pel="line"].is-visible {
  opacity: 1;
}

[data-pel="line"].is-visible::after {
  transform: scaleX(1);
}
```

### Stagger (Credit Grid, Gallery, Prizes)

Parent element gets `data-pel="stagger"`. Children start hidden, then cascade in with incremental delay.

```css
[data-pel="stagger"] > * {
  opacity: 0;
  transform: translateY(20px);
  transition:
    opacity var(--pel-duration) var(--pel-ease),
    transform var(--pel-duration) var(--pel-ease);
}

[data-pel="stagger"].is-visible > * {
  opacity: 1;
  transform: none;
}
```

JS sets `transitionDelay` per child:

```js
if (entry.target.dataset.pel === 'stagger') {
  Array.from(entry.target.children).forEach((child, i) => {
    child.style.transitionDelay = `${i * 0.1}s`;
  });
}
```

### Stagger Math

| Children | Total Duration | Formula |
|----------|---------------|---------|
| 3 | 1.0s | 0.8s + (2 × 0.1s) |
| 6 | 1.3s | 0.8s + (5 × 0.1s) |
| 9 | 1.6s | 0.8s + (8 × 0.1s) |
| 12 | 1.9s | 0.8s + (11 × 0.1s) |

Keep stagger groups under 12 children. Beyond that, the total cascade time exceeds 2s and feels sluggish.

## JavaScript Setup

### IntersectionObserver

```js
(function() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');

        // Handle stagger children
        if (entry.target.dataset.pel === 'stagger') {
          Array.from(entry.target.children).forEach((child, i) => {
            child.style.transitionDelay = `${i * 0.1}s`;
          });
        }

        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll('[data-pel]').forEach(el => observer.observe(el));
})();
```

**Threshold:** `0.15` — triggers when 15% of the element is visible. High enough to avoid premature reveals, low enough for tall elements.

**Unobserve:** Each element is unobserved after first reveal. No re-triggering on scroll back.

### Parallax

```js
const parallaxEls = document.querySelectorAll('[data-pel="parallax"]');
if (parallaxEls.length && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
  let ticking = false;
  window.addEventListener('scroll', () => {
    if (!ticking) {
      requestAnimationFrame(() => {
        const scrollY = window.scrollY;
        parallaxEls.forEach(el => {
          const rect = el.getBoundingClientRect();
          const offset = (rect.top + scrollY - window.innerHeight / 2) * 0.15;
          el.style.transform = `translateY(${offset}px)`;
        });
        ticking = false;
      });
      ticking = true;
    }
  }, { passive: true });
}
```

**Speed factor:** `0.15` — subtle. Image moves at 15% of scroll speed. Higher values (0.3+) feel aggressive.

**Passive listener:** Required for scroll performance.

**rAF throttle:** Single `requestAnimationFrame` per scroll event. Never use `setInterval`.

### Title Split (Advanced)

For `data-pel="title"`, split text into line-wrapped spans for per-line reveal.

```js
document.querySelectorAll('[data-pel="title"]').forEach(el => {
  const text = el.textContent;
  el.innerHTML = '';
  el.style.overflow = 'hidden';

  const words = text.split(' ');
  const container = document.createElement('span');
  container.style.display = 'block';
  el.appendChild(container);

  // Measure line breaks by adding words and checking offsetTop
  let lines = [];
  let currentLine = [];
  let lastTop = null;

  words.forEach(word => {
    const span = document.createElement('span');
    span.textContent = word + ' ';
    span.style.display = 'inline';
    container.appendChild(span);

    const top = span.offsetTop;
    if (lastTop !== null && top !== lastTop) {
      lines.push(currentLine.join(' ').trim());
      currentLine = [];
    }
    currentLine.push(word);
    lastTop = top;
  });
  lines.push(currentLine.join(' ').trim());

  // Replace with animated line spans
  container.remove();
  lines.forEach((line, i) => {
    const wrapper = document.createElement('span');
    wrapper.style.cssText = 'display: block; overflow: hidden;';
    const inner = document.createElement('span');
    inner.textContent = line;
    inner.style.cssText = `display: block; transform: translateY(100%); transition: transform var(--pel-duration) var(--pel-ease); transition-delay: ${i * 0.12}s;`;
    wrapper.appendChild(inner);
    el.appendChild(wrapper);
  });
});
```

Then in the IntersectionObserver callback, when `data-pel="title"` elements become visible, animate the inner spans:

```js
if (entry.target.dataset.pel === 'title') {
  entry.target.querySelectorAll('span > span').forEach(inner => {
    inner.style.transform = 'translateY(0)';
  });
}
```

## Reduced Motion

All animations must respect `prefers-reduced-motion`:

```css
@media (prefers-reduced-motion: reduce) {
  [data-pel],
  [data-pel="stagger"] > * {
    opacity: 1 !important;
    transform: none !important;
    transition: none !important;
  }
  [data-pel="line"]::after {
    transform: scaleX(1) !important;
    transition: none !important;
  }
}
```

JS parallax checks the media query before attaching the scroll listener.

## Easing Curves

```css
--pel-ease: cubic-bezier(.19, 1, .22, 1);
```

This is a custom ease-out curve — fast start, very gradual stop. Feels cinematic, not springy. Used for all reveals and transitions.

```css
--pel-ease-back: cubic-bezier(.175, 0, .77, 1);
```

Slight overshoot ease-out. Reserved for hover interactions (play button scale, image zoom) where a subtle bounce adds life.

## Panel Animations (Widget Dropdown)

Accordion-style reveals using CSS Grid, no JS height calculation:

```css
.pel-widget__dropdown {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows var(--pel-duration) var(--pel-ease);
  overflow: hidden;
}

.pel-widget__dropdown.is-open {
  grid-template-rows: 1fr;
}

.pel-widget__dropdown > * {
  overflow: hidden;
}
```

Toggle via JS class addition. Never use `height` transitions — `grid-template-rows` handles unknown content heights.

## Mask-Image Edge Fading

Optional: fade content edges for horizontal scroll sections or gallery edges.

```css
.pel-gallery__grid {
  mask-image: linear-gradient(
    to right,
    transparent 0%,
    black 3%,
    black 97%,
    transparent 100%
  );
}
```

Use sparingly — only for horizontal overflow or edge-bleeding content.
