# Advanced Patterns

CSS techniques that aren't full components but are needed for complex intelligence sites.

---

## Ghost Watermark Technique

Large, semi-transparent text behind content. Uses `data-watermark` attribute for per-instance text.

```css
.dossier::before {
  content: attr(data-watermark);
  position: absolute;
  right: -0.4rem;
  bottom: -1.9rem;
  font-family: var(--display);
  font-size: clamp(4rem, 16vw, 11rem);
  font-style: italic;
  color: var(--ink);
  opacity: 0.045;
  pointer-events: none;
  white-space: nowrap;
}
```

Each instance: `<article class="dossier" data-watermark="CompanyName">`.

Rules:
- Opacity range: 0.035–0.05 (lower for secondary entities, higher for primary)
- Position: usually `right` + `bottom` to avoid overlapping readable content
- Color: use `var(--ink)` or a platform color for branded watermarks
- Font: always `var(--display)` italic for editorial weight

## Asymmetric Grid Ratios

Standard ratios used across intelligence layouts:

| Ratio | Use case | CSS |
|-------|----------|-----|
| 9rem \| 8fr | Dossier hero (logo \| content) | `grid-template-columns: minmax(9rem, 4fr) minmax(0, 8fr)` |
| 7rem \| 9fr | Secondary dossier hero | `grid-template-columns: minmax(7rem, 3fr) minmax(0, 9fr)` |
| 7fr \| 5fr | Content grid (facts \| sidebar) | `grid-template-columns: minmax(0, 7fr) minmax(16rem, 5fr)` |
| 7fr \| 5fr reduced | Secondary content grid | `grid-template-columns: minmax(0, 7fr) minmax(14rem, 5fr)` |

The `minmax()` values prevent columns from collapsing at narrow viewports while maintaining the asymmetric proportion.

Responsive: all asymmetric grids collapse to `grid-template-columns: 1fr` at 820px.

## clamp() Fluid Typography

Standard fluid formulas:

```css
/* Primary dossier name */
font-size: clamp(2.5rem, 8vw, 5rem);

/* Secondary dossier name */
font-size: clamp(2rem, 6vw, 3.8rem);

/* Editorial note headline */
font-size: clamp(2rem, 5vw, 3.5rem);

/* Primary ghost watermark */
font-size: clamp(4rem, 16vw, 11rem);

/* Secondary ghost watermark */
font-size: clamp(3.5rem, 14vw, 9rem);

/* Dossier padding */
padding: clamp(1.35rem, 3vw, 2rem);

/* Secondary dossier padding */
padding: clamp(1.2rem, 2.5vw, 1.75rem);

/* Hero gap */
gap: clamp(1.25rem, 3vw, 2rem);
```

Pattern: `clamp(mobile-min, fluid-vw, desktop-max)`. The `vw` value determines the transition point.

## Opacity Hierarchy for Primary/Secondary Entities

```css
/* Primary entity: full visual weight */
.dossier {
  border: 1.5px solid var(--border-strong);
  background: var(--dossier-bg);
  box-shadow: 0 18px 45px oklch(0.22 0.04 270 / 0.08);
  opacity: 1;
}

/* Secondary entity: visually diminished */
.dossier--secondary {
  border-width: 1px;
  border-color: var(--border);
  background: var(--dossier-bg-secondary);
  box-shadow: none;
  opacity: 0.92;
}
```

The 4 signals of diminished importance:
1. Thinner border (1px vs 1.5px)
2. Weaker border color (`--border` vs `--border-strong`)
3. Lighter background (0.965 vs 0.98 lightness)
4. Reduced opacity (0.92)

Additional: smaller typography, smaller logo, smaller watermark.

## Logo Handling

### Directory structure
```
logos/
├── company-logo.svg      # Primary SVGs
├── company-logo.png      # Fallback PNGs (for dark logos)
└── company-icon.png      # Square icons (28x28 for entity-flow)
```

### Standard sizes
| Context | Size | CSS |
|---------|------|-----|
| Dossier hero (primary) | 128x128 rendered, fluid | `clamp(7rem, 15vw, 10rem)` |
| Dossier hero (secondary) | 128x128 rendered, fluid | `clamp(5.5rem, 12vw, 8rem)` |
| Entity flow | 28x28 | Fixed `1.8rem` |
| Header badge | 120x120 | Fixed `120px` |

### Dark logo class
For logos on dark backgrounds (white-on-black) that need inversion on light backgrounds:

```css
.profile-header__logo--dark {
  background: oklch(0.22 0.02 270);
  border-color: oklch(0.22 0.02 270);
}
```

Usage: `<img class="profile-header__logo--dark" ...>`.

## Inline Page-Specific Style Conventions

Pages with entity-specific content embed a `<style>` block after CSS links:

```html
<link rel="stylesheet" href="_components.css">
<style>
  /* Page: landscape-profiles — entity-specific overrides */
  .custom-layout { ... }
</style>
```

Appropriate uses:
- Watermark content that can't use `data-watermark` (e.g., `content: "ONE ENTITY"`)
- Custom grid ratios for a specific page layout
- Entity-specific color overrides
- Page-specific responsive breakpoints

Not appropriate:
- Patterns that appear on 2+ pages (move to `_components.css`)
- Generic component styling
- Anything covered by existing component classes

## Scroll Margin with Sub-Nav

When sub-nav is present, anchored sections need extra scroll margin:

```css
.sub-nav ~ main section[id] {
  scroll-margin-top: 5rem;
}
```

This accounts for the sticky page-nav (3.5rem top) + sub-nav height (~1.5rem).

## Verb Chips Pattern

Small inline pills for key data points:

```html
<div class="verb-chips">
  <span class="chip chip--subq">$6M seed</span>
  <span class="chip chip--claude">Spotnana GDS</span>
  <span class="chip chip--codex">$10/mo</span>
</div>
```

Use sparingly — max 3-4 chips per group. Each chip should communicate one discrete fact. Color variants from the platform palette signal category, not severity.
