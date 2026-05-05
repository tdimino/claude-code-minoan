# Design System — VELVET CATALOGUE

## Conceptual Direction

**Candlelit rare-book room.** Leather, foxed parchment, amber lamplight, wine-dark velvet.

| Dial | Value | Meaning |
|------|-------|---------|
| VARIANCE | 6 | Editorial asymmetry, not dashboard |
| MOTION | 4 | Subtle hover warmth, staggered load |
| DENSITY | 5 | Comfortable reading, not cockpit |

---

## Color Tokens

All tokens defined in `app/globals.css` `:root`, registered as Tailwind v4 utilities via `@theme inline` (e.g., `bg-binding`, `text-amber`, `border-crease`).

### Surfaces

Named for physical layers of a bound book, from deepest to lightest.

| Token | Hex | Usage |
|-------|-----|-------|
| `--binding` | #1a1612 | Body, nav background, deepest surface |
| `--endpaper` | #241f1a | Card backgrounds, panels |
| `--page` | #2e2822 | Elevated surfaces, modals |
| `--crease` | #3d352d | Borders, dividers |
| `--spine` | #4a4038 | Subtle UI boundaries |

### Accents

| Token | Hex | Usage |
|-------|-----|-------|
| `--amber` | #d4a017 | Primary accent, lamplight, interactive elements |
| `--amber-dim` | #a07b10 | Subdued amber, hover states |
| `--amber-rgb` | 212, 160, 23 | For `rgba()` compositing |
| `--oxblood` | #8b2232 | Secondary accent, velvet, danger |
| `--oxblood-dim` | #6b1a27 | Subdued oxblood |
| `--oxblood-text` | #e06070 | WCAG AA readable on all dark surfaces |

### Text

| Token | Hex | Usage |
|-------|-----|-------|
| `--parchment` | #f4efe6 | Cream, primary text |
| `--vellum` | #c4b9a7 | Aged, secondary text |
| `--foxing` | #9a8d7b | Muted, tertiary/meta text |

### Candle Ratings

Graduated amber tones for the 1-5 candle rating system.

| Token | Hex |
|-------|-----|
| `--candle-5` | #d4a017 |
| `--candle-4` | #c49315 |
| `--candle-3` | #a07b10 |
| `--candle-2` | #7d600c |
| `--candle-1` | #5a4508 |
| `--candle-unlit` | #3d352d |

---

## Typography

All fonts loaded via `next/font/google` with `display: "swap"` in `app/layout.tsx`. Applied as CSS variables on `<body>`.

| Role | Font | Weights | CSS Variable | Tailwind |
|------|------|---------|--------------|----------|
| Display / Film Titles | Cormorant Garamond | 400, 600, 700 | `--font-cormorant` | `font-display` |
| Body / Commentary | Source Serif 4 | 400, 600 | `--font-source-serif` | `font-body` |
| Labels / Metadata | JetBrains Mono | 400, 500 | `--font-jetbrains` | `font-mono` |
| Navigation / UI | Figtree | 400, 500, 600 | `--font-figtree` | `font-sans` |

---

## Rating System

Candle flames (SVG), not stars. `CandleRating` component renders 1-5 flame icons with graduated amber tones from `--candle-1` (dimmest) to `--candle-5` (brightest). Unlit candles use `--candle-unlit`. Tom and Mary rate independently. Consistent with the `watchlist.md` convention of "5 candles."

---

## Layout

### Navigation

| Breakpoint | Component | Behavior |
|------------|-----------|----------|
| Desktop (>=768px) | `SideNav` | Fixed left sidebar with route links, film count, avatar |
| Mobile (<768px) | `BottomNav` | Fixed bottom tab bar with 5 tabs |

### Film Detail Panel

Desktop: 780px side panel. Two columns — 300px poster column (`bg-binding`, warm candlelit shadow, museum-placard caption) + 480px detail column (scrollable). Close button pinned in non-scrolling header.

Mobile: bottom sheet, poster hidden. Overlay `tabIndex={-1}` to prevent focus trap escape.

---

## Motion

| Component | Animation | Duration |
|-----------|-----------|----------|
| PageTransition | Amber flash crossfade | ~300ms |
| TiltCard | Parallax 3D tilt, spring return | Spring (stiffness: 300, damping: 30) |
| FilmDetail | Slide-in from right (desktop), slide-up (mobile) | ~250ms |
| KotharAvatar | Forge Pulse — 4s amber ring breathing | 4s infinite |
| OracleSmoke | Smooth activation/deactivation | ~2.5s activate, ~6s deactivate |

All animations respect `prefers-reduced-motion`. Three.js components fall back to static alternatives when reduced motion is active.

---

## Accessibility

| Concern | Implementation |
|---------|----------------|
| Skip link | `<a>` with `sr-only` + `focus:not-sr-only` in `layout.tsx` |
| Focus indicators | Amber ring on all interactive elements |
| Color contrast | `--parchment` on `--binding` = 13.6:1. `--foxing` on `--binding` = 4.7:1 (AA). `--oxblood-text` = AA compliant variant |
| Reduced motion | All R3F canvases check `prefers-reduced-motion`, fall back to static |
| Keyboard navigation | Arrow keys in queue, Esc to close panels, Ctrl+Shift+D for dev mode |
| Semantic HTML | `<main>`, `<nav>`, `<article>` used appropriately |

---

## Where to Look

| What | File |
|------|------|
| All color/typography tokens | `app/globals.css` |
| Font loading + body setup | `app/layout.tsx` |
| Candle rating component | `components/shared/CandleRating.tsx` |
| Desktop navigation | `components/shared/SideNav.tsx` |
| Mobile navigation | `components/shared/BottomNav.tsx` |
| Film detail panel | `components/archive/FilmDetail.tsx` |
| Page transition | `components/shared/PageTransition.tsx` |
