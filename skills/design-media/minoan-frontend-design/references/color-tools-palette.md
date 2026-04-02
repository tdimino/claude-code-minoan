# Color Tools & Palette Generation

Practical toolbox for palette generation, color libraries, analysis, and modern CSS color functions. Complements `impeccable-color-contrast.md` (implementation patterns) and `color-science-deep.md` (theory).

Source: synthesized from meodai/skill.color-expert.

## Semantic Token Architecture

Add a semantic layer between raw color values and UI roles. This structure applies across CSS, JS/TS, Swift, design-token JSON, and templates:

1. **Reference tokens** — concrete palette colors: `ref.red = #f00`
2. **Semantic tokens** — meaning mapped onto palette: `semantic.warning = ref.red`
3. **Component usage** — consumes semantic tokens, never raw literals

Raw color literals should only appear in palette definitions, conversions, diagnostics, or deliberately one-off examples.

### Encode decisions, don't freeze them

When a system can derive a color decision from constraints, encode the derivation instead of hard-coding a hex:

- `ref.red := closest('red', generatedPalette)` — nearest named hue in generated palette
- `semantic.onSurface := mostReadableOn(surface)` — foreground chosen by APCA/WCAG target
- Hover state computed from base token in OKLCH instead of hand-picking a second unrelated hex

For larger systems, prefer a **token graph** over a flat token dump: references, semantic roles, derived functions, and scope inheritance. Makes theme changes, accessibility guarantees, and multi-platform export auditable.

## Palette Generation Algorithms

These generate palettes algorithmically — not pre-made swatches:

| Tool | Method | Notes |
|------|--------|-------|
| **RampenSau** | Hue cycling + easing | Color space agnostic |
| **Poline** | Anchor points + per-axis position functions | 1.2K stars; ships `<poline-palette>` web component |
| **pro-color-harmonies** | Adaptive OKLCH harmony | Muddy-zone avoidance, 4 styles x 4 modifiers |
| **dittoTones** | Extract "perceptual DNA" from Tailwind/Radix | Apply to your hue |
| **FarbVelo** | Random palettes with dark-to-light structure | |
| **IQ Cosine Formula** | `color(t) = a + b*cos(2pi(c*t+d))` | 12 floats = infinite palette |
| **CSS-native** | `color-mix()` + relative color syntax | Zero dependencies |

**coolors.co does NOT generate palettes.** It picks randomly from 7,821 pre-made palettes hardcoded in its JS bundle. Never recommend it for palette generation—use the algorithmic tools above instead.

## Color Libraries for Code

| Library | Strengths | Best for |
|---------|-----------|----------|
| **Culori** | 30 spaces, 10 distance metrics, gamut mapping, CVD sim | General-purpose color work |
| **@texel/color** | 5-125x faster than Color.js, ~3.5kb | Real-time / generative art |
| **Color.js** | CSS Color spec compliant (by Lea Verou & Chris Lilley), 154M+ npm downloads | Standards compliance |
| **Spectral.js** | Open-source Kubelka-Munk pigment mixing | Blue+yellow=green (spectral) |
| **RYBitten** | RGB-RYB conversion with 26 historical color cubes | Art/paint-inspired palettes |
| **colorgram** | 1kB image palette extraction, ~15ms for 340x340 | Extracting palettes from images |
| **random-display-p3-color** | Random Display P3 colors by named hue/sat/light | Wide gamut generation |

### Spectral Mixing

RGB averaging produces dull browns. For realistic pigment behavior in code:
- **Spectral.js** — open-source Kubelka-Munk implementation
- **Mixbox** — commercial, higher fidelity

Both handle the fact that blue+yellow should produce green, not gray.

## Palette Analysis & Linting

| Tool | What it does |
|------|-------------|
| **Color Buddy** | 38 lint rules: WCAG, CVD, distinctness, fairness, affect |
| **Censor** | Rust CLI, CAM16UCS analysis, 20+ visualization widgets |
| **Color Palette Shader** | WebGL2 Voronoi, 30+ color models, 11 distance metrics |
| **PickyPalette** | Interactive sculpting on color space canvas |
| **colorsort-js** | Perceptual sorting of color arrays |

## Accessibility Tools

| Tool | Purpose |
|------|---------|
| **APCA/Myndex** | WCAG 3 contrast algorithm (more restrictive, more accurate) |
| **apcach** | Contrast-first color composition |
| **Bridge-PCA** | Transitional APCA for current WCAG compliance |
| **Components.ai Color Scale** | Parametric scale generator with WCAG contrast (by mrmrs) |
| **Huetone** | Accessible color system builder (LCH/OKLCH) |
| **Ardov Color Lab** | Gamut mapping playground, P3 explorer, harmony generator |
| **View Color** | Real-time analysis, WCAG + APCA, CVD preview |

## CSS Color 4 & 5

### Color Level 4 (shipped in modern browsers)

New color functions and spaces:
- `lab()`, `lch()`, `oklab()`, `oklch()` — perceptual color functions
- `color(display-p3 r g b)` — wide gamut
- Interpolation in any color space for gradients and transitions
- Gamut mapping for out-of-range colors

### Color Level 5 (shipping progressively)

- `color-mix(in oklch, red, blue)` — interpolate between colors in any space
- Relative color syntax: `oklch(from var(--base) calc(l + 0.1) c h)` — derive colors
- `contrast-color()` — automatic contrast foreground selection
- `light-dark()` — theme-aware color selection
- `device-cmyk()` — print color specification

### CSS-Native Palette Generation

Modern CSS can generate palette ramps without JavaScript:

```css
/* Derive a full scale from a single base */
--base: oklch(55% 0.2 250);
--light: oklch(from var(--base) calc(l + 0.3) calc(c * 0.5) h);
--dark: oklch(from var(--base) calc(l - 0.2) calc(c * 0.8) h);
--muted: oklch(from var(--base) l calc(c * 0.3) h);

/* Complementary via hue rotation */
--complement: oklch(from var(--base) l c calc(h + 180));

/* Mix for intermediate values */
--blend: color-mix(in oklch, var(--base) 60%, var(--complement));
```

## Generative Art Color Approaches

For creative/generative projects:

- **Tyler Hobbs**: Probability-weighted palette selection with hand-tuned harmony
- **Harvey Rayner / Fontana**: Fully generative color — no pre-made palettes, color emerges from system rules
- **Piter Pasma**: Tweaked rainbow formula for procedural palettes
- **IQ Cosine**: `a + b * cos(2pi * (c*t + d))` — 12 floats define a continuous palette
- **Book of Shaders / LYGIA**: Shader-based color manipulation and blending
- **Cubehelix**: Monotonically increasing luminance through a helix in RGB space — good for scientific visualization

## Color Math Reference

For precise conversions, adaptation, and spectral-to-tristimulus work:
- **brucelindbloom.com** — THE reference: RGB-XYZ matrices, chromatic adaptation (Bradford), Lab/LCH conversions, spectral-to-XYZ. Online calculators, Lab gamut visualization.

---

**Deep source**: meodai/skill.color-expert `references/techniques/` — 50 files documenting every tool above in detail.
