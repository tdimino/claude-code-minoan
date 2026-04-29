# Pellicola Design Tokens

Complete reference of `--pel-*` CSS custom properties, typography, spacing, and infrastructure.

## Core Palette

```css
:root {
  /* ── Background ── */
  --pel-cream: oklch(97.5% 0.012 85);      /* Page background — warm, not white */
  --pel-cream-deep: oklch(95% 0.015 80);    /* Card/panel background — slightly warmer */
  --pel-black: oklch(10% 0 0);              /* Gallery section background */

  /* ── Text ── */
  --pel-ink: oklch(15% 0.005 80);           /* Primary text — headlines, body */
  --pel-ink-muted: oklch(40% 0.01 80);      /* Secondary text — captions, metadata */
  --pel-ink-light: oklch(98% 0 0);          /* Text on dark backgrounds */

  /* ── Accent ── */
  --pel-red: oklch(55% 0.22 25);            /* Play button ONLY — one accent, one purpose */

  /* ── Borders ── */
  --pel-border: oklch(85% 0.01 80);         /* Default borders — credit grid, dividers */
  --pel-border-dark: oklch(25% 0 0);        /* Borders on dark gallery section */
}
```

## Typography

```css
:root {
  /* ── Font families ── */
  --pel-font-display: 'Playfair Display', 'Cormorant Garamond', serif;
  --pel-font-body: 'DM Sans', 'Outfit', sans-serif;
}
```

**Google Fonts URL:**

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,400;0,500;0,700;1,400&family=Playfair+Display:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet">
```

**Icon library (optional):**

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2/src/regular/style.css">
```

## Type Scale

| Element | Font | Size | Weight | Extras |
|---------|------|------|--------|--------|
| Hero title | Display | clamp(3rem, 8vw, 7rem) | 400 | — |
| Section heading (h2) | Display | clamp(2rem, 4vw, 3.5rem) | 400 | — |
| Credit name | Display | clamp(1.25rem, 2vw, 1.75rem) | 400 | — |
| Director name | Display | clamp(1.5rem, 3vw, 2.5rem) | 400 | — |
| Body text | Body | 1rem (16px) | 400 | line-height: 1.6 |
| Genre/metadata label | Body | 0.75rem | 500 | letter-spacing: 0.1em; text-transform: uppercase |
| Credit role | Body | 0.75rem | 500 | letter-spacing: 0.1em; text-transform: uppercase |
| Nav/widget text | Body | 0.875rem | 500 | — |
| Section divider label | Body | 0.6875rem | 500 | letter-spacing: 0.15em; text-transform: uppercase |

## Easing

```css
:root {
  --pel-ease: cubic-bezier(.19, 1, .22, 1);        /* Custom ease-out for most transitions */
  --pel-ease-back: cubic-bezier(.175, 0, .77, 1);   /* Ease-out with slight overshoot */
  --pel-duration: 0.8s;                              /* Standard animation duration */
  --pel-duration-long: 1.1s;                         /* Extended animations (hero, gallery) */
  --pel-duration-short: 0.4s;                        /* Hover states, small transitions */
  --pel-stagger-delay: 0.1s;                         /* Per-child stagger increment */
}
```

## Spacing

| Token | Value | Usage |
|-------|-------|-------|
| `--pel-section-gap` | `clamp(4rem, 8vw, 8rem)` | Gap between major sections |
| `--pel-content-pad` | `clamp(1.5rem, 4vw, 3rem)` | Horizontal page padding |
| `--pel-max-width` | `1200px` | Max content width |
| `--pel-frame-pad` | `clamp(0.75rem, 2vw, 1.25rem)` | Film-frame image padding |
| `--pel-frame-radius` | `8px` | Film-frame corner radius |
| `--pel-grid-gap` | `1px` | Credit grid border gap |

```css
:root {
  --pel-section-gap: clamp(4rem, 8vw, 8rem);
  --pel-content-pad: clamp(1.5rem, 4vw, 3rem);
  --pel-max-width: 1200px;
  --pel-frame-pad: clamp(0.75rem, 2vw, 1.25rem);
  --pel-frame-radius: 8px;
  --pel-grid-gap: 1px;
}
```

## Film-Frame Image Treatment

The signature visual element — image wrapped in cream padding like a polaroid/celluloid frame.

```css
.pel-frame {
  background: var(--pel-cream-deep);
  padding: var(--pel-frame-pad);
  border-radius: var(--pel-frame-radius);
  box-shadow:
    0 1px 2px oklch(15% 0 0 / 0.04),
    0 4px 8px oklch(15% 0 0 / 0.03),
    0 8px 24px oklch(15% 0 0 / 0.02);
}

.pel-frame img {
  width: 100%;
  display: block;
  border-radius: calc(var(--pel-frame-radius) - 2px);
}
```

## Dark Gallery Tokens

Palette inversion for the footage/gallery section:

```css
.pel-gallery {
  --pel-bg-local: var(--pel-black);
  --pel-text-local: var(--pel-ink-light);
  --pel-border-local: var(--pel-border-dark);
  background: var(--pel-bg-local);
  color: var(--pel-text-local);
}
```

## Responsive Breakpoints

| Breakpoint | Target | Key changes |
|------------|--------|-------------|
| `1024px` | Small desktop | Credit grid 3-col → 2-col, reduce section gap |
| `768px` | Tablet | Hero title scales down, widget hides, content padding reduces |
| `480px` | Mobile | Credit grid → 1-col, gallery grid → 1-col, nav simplifies |

## Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  [data-pel] {
    opacity: 1 !important;
    transform: none !important;
    transition: none !important;
  }
  .pel-play__text { transition: none; }
  .pel-gallery__item { transition: none; }
  html { scroll-behavior: auto; }
}
```

## Z-Index Stack

```
Layer 0  z-index: 0    Body background (--pel-cream)
Layer 1  z-index: 1    Content sections (position: relative)
Layer 2  z-index: 10   Director card overlay
Layer 3  z-index: 50   Context widget (position: fixed)
Layer 4  z-index: 100  Skip link (position: fixed)
```

## Infrastructure

**Viewport meta:**
```html
<meta name="viewport" content="width=device-width, initial-scale=1">
```

**Skip link:**
```html
<a href="#main" class="pel-skip-link">Skip to content</a>
```

```css
.pel-skip-link {
  position: fixed;
  top: -100%;
  left: 1rem;
  z-index: 100;
  padding: 0.5rem 1rem;
  background: var(--pel-ink);
  color: var(--pel-ink-light);
  font-family: var(--pel-font-body);
  text-decoration: none;
  border-radius: 4px;
}
.pel-skip-link:focus {
  top: 1rem;
}
```
