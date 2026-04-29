# Pellicola Color System

OKLCH palette for warm analog cinema aesthetic. Two palettes coexist in one page: cream (default) and dark (gallery section).

## Why OKLCH

OKLCH is perceptually uniform — equal steps in lightness/chroma/hue produce equal visual contrast. HSL does not. This matters for the cream palette where subtle warmth shifts need to feel consistent.

All pellicola tokens use OKLCH. Never use hex or HSL in component definitions.

## Cream Palette (Default)

The page lives on warm cream — not white, not beige. The warmth comes from a deliberate hue shift toward amber (hue 80-85) with minimal chroma.

```
oklch(97.5% 0.012 85)  --pel-cream       Page background
oklch(95%   0.015 80)  --pel-cream-deep   Card/frame background (slightly more saturated)
oklch(85%   0.01  80)  --pel-border       Default border
oklch(15%   0.005 80)  --pel-ink          Primary text
oklch(40%   0.01  80)  --pel-ink-muted    Secondary text, captions
```

**Design rationale:** The cream hue (85) sits in the warm amber range. Chroma is extremely low (0.012) — enough to feel warm, not enough to feel tinted. Ink color has the same hue family, creating tonal harmony between text and background.

**What kills the analog feeling:**
- `#FFFFFF` (oklch 100% 0 0) — no warmth, no character
- `#FAFAFA` — close but zero chroma reads as grey, not warm
- `#F5F5DC` (beige) — too yellow, reads as aged paper, not cinema
- Any blue-tinted grey — fights the warm direction

## Dark Gallery Palette

One section per page inverts to dark — the footage/gallery section. This creates visual breathing: cream → dark → cream.

```
oklch(10% 0 0)    --pel-black         Gallery background
oklch(25% 0 0)    --pel-border-dark   Gallery borders
oklch(98% 0 0)    --pel-ink-light     Text on dark
```

**Design rationale:** Gallery background is achromatic (chroma 0) — true near-black, not tinted. This makes the film stills the only source of color in the section. The contrast with the warm cream sections above and below creates a deliberate "lights off in the theater" rhythm.

**Transition between palettes:**
- No gradient blend between cream and dark sections
- Hard cut — `pel-section-divider` marks the boundary
- Dark section uses full-bleed width (breaks out of max-width container)
- Gallery items hover: `filter: brightness(1.08)` for subtle lift

## Accent: Red

```
oklch(55% 0.22 25)  --pel-red  Play button only
```

One accent color, one purpose. The red sits at high chroma (0.22) in the warm red range (hue 25). It reads as cinematic red — the color of a projector power light, not a warning badge.

**Reserved exclusively for:**
- Play button circle background
- Play button triangle fill

**Never use for:** headings, borders, section backgrounds, links, badges, dividers, hover states.

Additional color comes from the film's own imagery — hero photos, gallery stills. The palette stays restrained so the film's visual identity dominates.

## Customization

To adapt for a specific film or brand:

1. **Cream warmth** — Shift `--pel-cream` hue (80-90 range). Lower hue = more neutral. Higher = warmer amber.
2. **Accent swap** — Replace `--pel-red` with the film's brand color. Keep chroma > 0.15 for sufficient contrast against cream.
3. **Dark gallery tint** — Optionally add minimal chroma to `--pel-black` (e.g., `oklch(10% 0.005 250)` for a cool blue-black tint that makes warm stills pop).

## Contrast Ratios

| Pair | Ratio | WCAG |
|------|-------|------|
| `--pel-ink` on `--pel-cream` | 14.8:1 | AAA |
| `--pel-ink-muted` on `--pel-cream` | 5.2:1 | AA |
| `--pel-ink-light` on `--pel-black` | 17.1:1 | AAA |
| `--pel-red` on `--pel-cream` | 4.6:1 | AA (large text) |
| `--pel-ink` on `--pel-cream-deep` | 12.4:1 | AAA |

All text pairs meet WCAG AA minimum. Primary text pairs meet AAA.
