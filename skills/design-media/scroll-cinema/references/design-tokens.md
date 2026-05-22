# Design Tokens

CSS custom property system for scroll-cinema output. All tokens use the `--sc-*` prefix.

## Color Tokens (OKLCH-Based)

```css
:root {
  /* Chapter color system — GSAP-animated via ScrollTrigger */
  --sc-hue: 250deg;
  --sc-chroma: 0.15;
  --sc-lightness: 0.25;
  --sc-bg: oklch(var(--sc-lightness) var(--sc-chroma) var(--sc-hue));

  /* Text colors — contrast-safe for dark backgrounds */
  --sc-text: #E8ECF4;
  --sc-text-muted: rgba(232, 236, 244, 0.6);
  --sc-text-heading: #FFFFFF;

  /* Accent — override with --accent CLI flag */
  --sc-accent: oklch(0.75 0.18 160);
}
```

## Typography Tokens

```css
:root {
  --sc-font-display: 'Geist', system-ui, -apple-system, sans-serif;
  --sc-font-body: 'Geist', system-ui, -apple-system, sans-serif;
  --sc-font-mono: 'Geist Mono', ui-monospace, 'SFMono-Regular', monospace;

  --sc-heading-size: clamp(2.5rem, 5vw, 4.5rem);
  --sc-heading-weight: 700;
  --sc-heading-tracking: -0.02em;
  --sc-heading-leading: 1.1;

  --sc-body-size: clamp(1rem, 1.2vw, 1.25rem);
  --sc-body-weight: 400;
  --sc-body-leading: 1.7;
  --sc-body-max-width: 42rem;

  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

Font import (Google Fonts CDN):
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400&display=swap" rel="stylesheet">
```

## Spacing & Layout Tokens

```css
:root {
  --sc-chapter-height: 200vh;
  --sc-chapter-padding: clamp(2rem, 5vw, 6rem);
  --sc-content-max-width: 800px;
  --sc-section-gap: 0;
}
```

## Animation Tokens

```css
:root {
  --sc-entrance-duration: 1.2s;
  --sc-stagger-delay: 0.08s;
  --sc-scrub-duration: 1;
  --sc-scroll-smoothness: 0.05;
  --sc-mouse-smoothness: 0.08;
  --sc-velocity-smoothness: 0.10;
  --sc-chapter-smoothness: 0.03;
}
```

## Light Mode

```css
@media (prefers-color-scheme: light) {
  :root {
    --sc-text: #1a1a2e;
    --sc-text-muted: rgba(26, 26, 46, 0.6);
    --sc-text-heading: #0a0a1a;
    --sc-lightness: 0.85;
  }
}
```

Override via `--color-scheme light` CLI flag, which forces the light tokens regardless of system preference.

## Responsive Overrides

```css
@media (max-width: 768px) {
  :root {
    --sc-chapter-height: 150vh;
    --sc-chapter-padding: clamp(1.5rem, 4vw, 3rem);
    --sc-heading-size: clamp(1.8rem, 4vw, 2.5rem);
  }
}

@media (max-width: 480px) {
  :root {
    --sc-chapter-height: 120vh;
    --sc-body-size: 1rem;
  }
}
```

## Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  :root {
    --sc-entrance-duration: 0s;
    --sc-stagger-delay: 0s;
    --sc-scrub-duration: 0;
  }
  .chapter-content {
    opacity: 1 !important;
    transform: none !important;
    clip-path: none !important;
  }
}
```

## Pacing Multipliers

Applied via JavaScript to scale animation tokens:

| Token | Slow (1.5×) | Medium (1.0×) | Fast (0.6×) |
|-------|-------------|---------------|-------------|
| `--sc-chapter-height` | 250vh | 200vh | 150vh |
| `--sc-entrance-duration` | 1.8s | 1.2s | 0.72s |
| `--sc-stagger-delay` | 0.104s | 0.08s | 0.056s |

```js
const multipliers = { slow: 1.5, medium: 1.0, fast: 0.6 };
const m = multipliers[pacing];
document.documentElement.style.setProperty('--sc-chapter-height', `${200 * m}vh`);
document.documentElement.style.setProperty('--sc-entrance-duration', `${1.2 * m}s`);
document.documentElement.style.setProperty('--sc-stagger-delay', `${0.08 * m}s`);
```

## Base Styles

```css
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  font-family: var(--sc-font-body);
  font-size: var(--sc-body-size);
  line-height: var(--sc-body-leading);
  color: var(--sc-text);
  background-color: var(--sc-bg);
  overflow-x: hidden;
}

html.lenis, html.lenis body {
  height: auto;
}

.lenis.lenis-smooth {
  scroll-behavior: auto !important;
}
```
