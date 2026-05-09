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

---

## CSS Starfield

Dense star effect using `box-shadow` on `body::before` (small dots) and `body::after` (bright feature stars with glow). Replaces the crosshatch texture for dark-themed sites.

```css
body {
  background:
    radial-gradient(ellipse 900px 450px at 15% 25%, oklch(0.30 0.10 290 / 0.28) 0%, transparent 70%),
    radial-gradient(ellipse 700px 350px at 80% 55%, oklch(0.25 0.08 260 / 0.35) 0%, transparent 65%),
    radial-gradient(ellipse 500px 600px at 45% 85%, oklch(0.28 0.06 210 / 0.18) 0%, transparent 60%),
    var(--bg);
  background-attachment: fixed;
}

@keyframes twinkle {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

body::before {
  content: ''; position: fixed; top: 0; left: 0;
  width: 1px; height: 1px;
  pointer-events: none; z-index: 0;
  box-shadow:
    72px 44px 0 0 rgba(255,255,255,0.7),
    183px 112px 0 0 rgba(255,255,255,0.5),
    /* ... 50-60 entries for dense star field */
    1330px 1250px 0 0 rgba(255,255,255,0.7);
}

body::after {
  content: ''; position: fixed; top: 0; left: 0;
  width: 2px; height: 2px; border-radius: 50%;
  pointer-events: none; z-index: 0;
  box-shadow:
    240px 160px 1px 1px rgba(255,255,255,0.9),
    670px 236px 1px 1px rgba(200,220,255,0.85),
    /* ... 20-30 brighter entries with colored tints */
    950px 1450px 2px 1px rgba(255,255,255,0.95);
  animation: twinkle 8s ease-in-out infinite;
}

body > * { position: relative; z-index: 1; }
```

### Construction Rules

1. **Two layers**: `::before` for dense small dots (0px spread, rgba white 0.45-0.7), `::after` for bright feature stars (1-2px spread, tinted rgba).
2. **Twinkle**: Only `::after` animates. 8s cycle, subtle opacity 1→0.4. Respects `prefers-reduced-motion`.
3. **Coverage**: Distribute stars across viewport width (0-1440px) and height (0-1800px). ~50 entries in `::before`, ~25 in `::after`.
4. **Color tints**: Feature stars use slight blue (`200,220,255`) or purple (`220,200,255`) tints for depth.
5. **Nebula gradients**: 2-3 `radial-gradient` ellipses behind the star layers create atmospheric depth. Use oklch with alpha for color.
6. **`background-attachment: fixed`**: Nebulae stay fixed while content scrolls. Stars stay fixed via `position: fixed`.

## Stagger-In Load Animations

Page-load reveal animation using CSS `animation-delay` calculated from a `--stagger-index` custom property.

```css
@keyframes stagger-in {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: translateY(0); }
}
.stagger-in {
  animation: stagger-in 300ms cubic-bezier(0.25, 1, 0.5, 1) both;
  animation-delay: calc(var(--stagger-index, 0) * 80ms);
}
@media (prefers-reduced-motion: reduce) {
  .stagger-in { animation: none; opacity: 1; }
}
```

```html
<div class="states-grid">
  <div class="state-card stagger-in" style="--stagger-index: 0">...</div>
  <div class="state-card stagger-in" style="--stagger-index: 1">...</div>
  <div class="state-card stagger-in" style="--stagger-index: 2">...</div>
</div>
```

### Rules

- **80ms per element** produces a natural cascade. Increase to 120ms for fewer items, decrease to 50ms for dense grids.
- **12px translateY** is subtle enough for content-heavy pages. Use 20px for hero sections.
- **`animation-fill-mode: both`** prevents flash-of-visible-content before animation starts.
- **Max stagger depth**: Cap at ~12-15 items (960ms-1200ms total) to avoid content feeling stuck.
- Apply to cards, grid items, list entries. Don't apply to body text or navigation.

## Auth Gate Theming

The auth gate overlay should match the active palette. The overlay uses inline styles set in `_auth.js`.

### Dark Theme Auth Gate

```javascript
overlay.style.cssText = 'position:fixed;inset:0;z-index:9999;' +
  'background:radial-gradient(ellipse 800px 400px at 40% 45%,' +
  'oklch(0.25 0.08 260/0.35) 0%,transparent 65%),' +
  'oklch(0.10 0.03 265);' +
  'display:flex;align-items:center;justify-content:center;' +
  'font-family:Inconsolata,monospace';
```

### Warm Theme Auth Gate

```javascript
overlay.style.cssText = 'position:fixed;inset:0;z-index:9999;' +
  'background:oklch(0.96 0.008 80);' +
  'display:flex;align-items:center;justify-content:center;' +
  'font-family:Inconsolata,monospace';
```

### Key Details

- Auth uses FNV-1a hash comparison. Change the `HASH` constant to change the password.
- On success, dispatches `window.dispatchEvent(new CustomEvent('vellum:authenticated'))` so other components (audio player, animations) can respond.
- All `sessionStorage` calls wrapped in try-catch for private browsing compatibility.
- The `vellum:authenticated` event solves the race condition where `DOMContentLoaded` fires before auth completes.

## Era Color Taxonomy Mapping

When content is organized by era, period, or category, map each era to a semantic color using the `base / bg / border` triple pattern documented in `design-tokens.md`.

### Application Patterns

**Era top-bar on cards:**

```css
.era-bar { position: relative; overflow: hidden; }
.era-bar::before {
  content: ''; display: block;
  height: 3px; width: 100%;
  background: var(--era-accent, var(--copper));
}
```

Apply via inline style: `<div class="era-bar" style="--era-accent: var(--era-jk2)">`.

**Era-tinted sections:**

```css
.section--era-jk2 {
  background: var(--era-jk2-bg);
  border: 1px solid var(--era-jk2-border);
  border-radius: 6px;
  padding: 1.25rem;
}
```

**Density indicators:**

```css
.density-bar {
  height: 3px; border-radius: 2px; margin-top: 0.5rem;
  background: var(--era-accent, var(--copper));
  opacity: 0.6;
}
```

Width set inline as percentage: `<div class="density-bar" style="width: 75%; --era-accent: var(--era-aim)">`.

### Hue Distribution

Spread era hues around the OKLCH wheel for maximum visual distinction:

| Hue range | Character | Example |
|-----------|-----------|---------|
| 10-30 | Red/warm | Clans, conflict, urgency |
| 55-85 | Gold/amber | Games, achievement |
| 145-195 | Cyan/teal | Technology, communication |
| 210-260 | Blue | Messaging, archival |
| 280-310 | Purple | Virtual worlds, imagination |
