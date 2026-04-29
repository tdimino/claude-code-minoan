# Vellum Design Tokens

Complete reference of CSS custom properties, typography, spacing, and infrastructure.

## Core Palette

```css
:root {
  --copper: oklch(0.45 0.12 55);      /* Accent — headings, links, icons */
  --ink: oklch(0.22 0.04 270);         /* Deepest text — h1, strong emphasis */
  --bg: oklch(0.96 0.008 80);          /* Page background */
  --bg-warm: oklch(0.94 0.012 80);     /* Warm background — table headers, hovers */
  --bg-card: oklch(0.98 0.005 80);     /* Card/panel background */
  --border: oklch(0.82 0.015 75);      /* Default borders */
  --border-strong: oklch(0.68 0.02 70);/* Emphasized borders — matrices, debugger */
  --text: oklch(0.22 0.02 55);         /* Primary text (rarely used directly) */
  --text-body: oklch(0.32 0.015 55);   /* Body text */
  --text-dim: oklch(0.45 0.01 55);     /* De-emphasized text */
  --text-muted: oklch(0.42 0.01 55);   /* Labels, section headings */
  --ghost: oklch(0.82 0.015 75);       /* Ghost numbers, decorative text */
}
```

## Severity Tiers

Each tier follows the `base / bg / border` triple pattern.

```css
:root {
  --dealbreaker: oklch(0.50 0.16 25);
  --dealbreaker-bg: oklch(0.50 0.16 25 / 0.06);
  --dealbreaker-border: oklch(0.50 0.16 25 / 0.28);

  --high: oklch(0.44 0.14 55);
  --high-bg: oklch(0.44 0.14 55 / 0.06);
  --high-border: oklch(0.44 0.14 55 / 0.28);

  --moderate: oklch(0.45 0.02 240);
  --moderate-bg: oklch(0.45 0.02 240 / 0.06);
  --moderate-border: oklch(0.45 0.02 240 / 0.22);

  --critical: oklch(0.45 0.18 15);
  --critical-bg: oklch(0.45 0.18 15 / 0.06);
  --critical-border: oklch(0.45 0.18 15 / 0.28);
}
```

## Platform Colors

Rename these for different clients. Default names are SubQ-specific.

```css
:root {
  --subq: oklch(0.38 0.12 160);       /* Teal-green — brand primary */
  --subq-bg: oklch(0.38 0.12 160 / 0.06);
  --subq-border: oklch(0.38 0.12 160 / 0.22);

  --claude: oklch(0.40 0.10 245);      /* Blue — competitor/secondary */
  --claude-bg: oklch(0.40 0.10 245 / 0.06);
  --claude-border: oklch(0.40 0.10 245 / 0.22);

  --cursor: oklch(0.42 0.11 295);      /* Purple */
  --cursor-bg: oklch(0.42 0.11 295 / 0.06);
  --cursor-border: oklch(0.42 0.11 295 / 0.22);

  --codex: oklch(0.42 0.14 145);       /* Green */
  --codex-bg: oklch(0.42 0.14 145 / 0.06);
  --codex-border: oklch(0.42 0.14 145 / 0.22);
}
```

## Status Colors

```css
:root {
  --planned: oklch(0.50 0.01 55);
  --building: oklch(0.55 0.14 85);     /* Animated pulse */
  --shipped: oklch(0.45 0.14 160);
  --blocked: oklch(0.50 0.16 25);
}
```

## Build Tiers (from _components.css)

```css
:root {
  --tier1: oklch(0.38 0.12 160);   --tier1-bg: oklch(0.38 0.12 160 / 0.06);   --tier1-border: oklch(0.38 0.12 160 / 0.22);
  --tier2: oklch(0.40 0.10 245);   --tier2-bg: oklch(0.40 0.10 245 / 0.06);   --tier2-border: oklch(0.40 0.10 245 / 0.22);
  --tier3: oklch(0.44 0.14 55);    --tier3-bg: oklch(0.44 0.14 55 / 0.06);    --tier3-border: oklch(0.44 0.14 55 / 0.22);
  --tier4: oklch(0.48 0.14 75);    --tier4-bg: oklch(0.48 0.14 75 / 0.06);    --tier4-border: oklch(0.48 0.14 75 / 0.22);
}
```

## Typography

```css
:root {
  --display: 'Bodoni Moda', serif;     /* Headlines, section nums, pullquotes */
  --body: 'Source Serif 4', serif;     /* Body text, descriptions */
  --mono: 'Inconsolata', monospace;    /* Labels, badges, code, nav */
}
```

**Google Fonts URL:**
```html
<link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,wght@0,400;0,500;0,700;1,400;1,500&family=Inconsolata:wght@400;500;600;700&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
```

**Icon library:**
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2/src/regular/style.css">
```

## Spacing Utilities

```css
.spaced    { margin-top: 1.25rem; }
.spaced-sm { margin-top: 1rem; }
.gap-below    { margin-bottom: 1.5rem; }
.gap-below-md { margin-bottom: 1.25rem; }
.gap-below-sm { margin-bottom: 1rem; }
.flush     { margin-bottom: 0; }
```

## Crosshatch Texture

Applied as `body::before` with fixed positioning. The SVG draws a subtle grid pattern:

```css
body::before {
  content: ''; position: fixed; inset: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 30h60M30 0v60' stroke='%23c4b99a' stroke-width='0.4' opacity='0.28'/%3E%3C/svg%3E");
  pointer-events: none; z-index: 0;
}
```

All page content uses `position: relative; z-index: 1` to layer above the texture.

## Responsive Breakpoints

| Breakpoint | Target | Key changes |
|------------|--------|-------------|
| `900px` | Tablet | 2-col grids → 2-col, rings reduce margin, h1 → 2.8rem |
| `640px` | Mobile | Grids → 1-col, padding reduces, small text elements hide |

## Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  .console-line { animation: none; }
  .status-dot--building { animation: none; }
  .state-card, .further-card, .phase-block, .page-nav a { transition: none; }
  html { scroll-behavior: auto; }
}
```

## Layout Constants

- Max width: `960px` (header, main, page-nav, footer)
- Content padding: `0 2rem` (desktop), `0 1.25rem` (mobile)
- Section spacing: `margin-bottom: 3.5rem`
- Card border-radius: `12px` (cards), `10px` (hook-card, phase-block), `100px` (pills/badges)
- Ghost section number: `3.2rem` display font, absolute positioned left

## Mermaid Diagram Theme

The `vellum` theme in `beautiful-mermaid` maps CSS variables to hex colors for SVG output:

| DiagramColors | CSS Variable | OKLCH | Hex | Role |
|---|---|---|---|---|
| `bg` | `--bg` | `oklch(0.96 0.008 80)` | `#f5f1eb` | Background |
| `fg` | `--ink` | `oklch(0.22 0.04 270)` | `#2b2836` | Text, node labels |
| `accent` | `--copper` | `oklch(0.45 0.12 55)` | `#7a5a2e` | Arrowheads, highlights |
| `line` | `--border` | `oklch(0.82 0.015 75)` | `#cec7b8` | Edges, connectors |
| `muted` | `--text-dim` | `oklch(0.45 0.01 55)` | `#666059` | Edge labels, secondary text |

Use `--transparent` when inlining SVGs so the panel's `--bg-card` background shows through instead of a hard-coded SVG background.
