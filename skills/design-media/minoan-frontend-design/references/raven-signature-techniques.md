# Raven Signature Techniques

High-level design patterns that define the Raven/Graylark intelligence aesthetic. Not individual tokens or components—these are the *why* behind the visual decisions and when to deploy them. Complements `raven-design-tokens.md` and `raven-component-patterns.md`.

Creative direction name: **Intelligence Dossier.**

---

## Near-Black-Only Dark Mode

Raven's neutral spine is 10 shades of grey between `rgb(0,0,0)` and `rgb(238,238,238)`. No warm tints, no cool tints, no hue in the neutrals at all. Depth is built entirely through luminance steps: chrome (17) vs. canvas (25) vs. surface (38).

**Key rules:**
- Background: `#000` (HTML) or `rgb(17,17,17)` (chrome), never a tinted dark (no navy, no charcoal-blue)
- Primary text: `rgb(238,238,238)`, never pure white—pure white reserved for display headlines
- Borders: translucent white at 5 named opacity levels (0.11–0.39), never solid grey
- Shadows: warm-black `rgba(0,0,0,...)` only—no colored shadows, no blur-glow
- The achromatic constraint means every accent color hits harder because it has zero competition

**When to apply:** Any time the direction says "intelligence," "surveillance," "classified," "forensic," or "operations center." The near-black spine is the defining Raven trait—everything else follows from this constraint.

---

## Monochromatic Accent Collapse

The product app uses a four-color signal-lamp palette (jade/lime/amber/red) for confidence tiers. The marketing landing page overrides ALL of these to a single blue: `rgb(24, 81, 255)`. Every button, every badge, every active indicator, every section number—one color.

**Implementation:**
```css
:root {
  --accent: rgb(24, 81, 255);
  --accent-wash: rgba(24, 81, 255, 0.35);
  --accent-deep: rgb(18, 60, 200);
  --accent-glow: rgb(70, 120, 255);
}
```
Override all status/semantic colors to `var(--accent)`. Amber and red collapse to white (neutral warnings), jade and lime collapse to accent blue (positive signals).

**When to apply:** Marketing pages, product landing pages, case studies—anywhere the message is "this is one tool with one purpose." Use the multi-color signal-lamp palette only inside the actual product UI where status differentiation is functional.

---

## Dossier Frame

Evidence containers use a double-layer overlay: (1) dashed inner border at 8px inset, (2) 18×18px grid-line pattern at near-invisible opacity (`rgba(255,255,255,0.035)`). This creates a forensic evidence-bag or document-scan feel.

**CSS pattern:**
```css
.dossier-frame {
  position: relative;
}
.dossier-frame::before {
  content: "";
  position: absolute;
  inset: 8px;
  border: 1px dashed rgba(255, 255, 255, 0.18);
  pointer-events: none;
}
.dossier-frame::after {
  content: "";
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(to right, rgba(255,255,255,0.035) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(255,255,255,0.035) 1px, transparent 1px);
  background-size: 18px 18px;
  pointer-events: none;
}
```

**When to apply:** Around primary evidence images, analysis results, or any container that represents "material under examination." Don't apply to every card—reserve for focal content that the user is meant to scrutinize.

---

## Fan-Out Pipeline

The core visual metaphor: one input image on the left, SVG connector lines fanning out to 3 output cards on the right. Represents "fragments in, intelligence out." The input sits at ~36% width with corner brackets; outputs stack vertically at ~72% left offset.

**Structure:**
1. **Input frame** (left): Image with corner brackets + mono-caps label ("INPUT · LOW-CONTEXT IMAGE")
2. **SVG connectors** (middle): Curved lines from input to each output, drawn as absolute-positioned SVG
3. **Output cards** (right, stacked): Each has a mono-caps kind label (blue), a sans heading, serif-italic result line, and a mono-caps jump link

**Key details:**
- The input image is desaturated slightly: `filter: grayscale(0.1) brightness(0.86) contrast(1.05)`
- Corner brackets are `10px × 10px` L-shaped borders at each corner (see Corner Bracket Viewfinder below)
- Output cards are text-only—no backgrounds, no borders—just type hierarchy against the dark background
- On mobile, collapses to a stacked layout with thumbnails replacing the SVG connectors

**When to apply:** Product capability sections, data pipeline explainers, any "input → process → output" narrative. The asymmetric left-input/right-output composition signals directional transformation.

---

## Section Numbering as Document Structure

Sections use `§01`, `§02` prefixes in mono caps, rendered as eyebrow labels above section headlines. The section symbol (§) + zero-padded number gives the page a classified-document or technical-manual feel.

**Pattern:**
```html
<div class="section-eyebrow">
  <span class="sect-label">
    <span class="sym">§</span><span class="num">02</span>
    <span class="sep">·</span> Find Region
  </span>
</div>
```

**Styling:** `font: 500 11px/1 var(--font-mono); letter-spacing: 0.22em; text-transform: uppercase`. The number gets accent-blue color; the symbol and separator get 55% white opacity.

**When to apply:** Long-form product pages, documentation, multi-section landing pages. Creates a sense of structured intelligence briefing rather than marketing fluff.

---

## Corner Bracket Viewfinder

Evidence images get `10px × 10px` L-shaped corner indicators—each corner has two sides of a border, creating a forensic viewfinder or camera targeting reticle effect.

**CSS pattern:**
```css
.viewfinder-corner {
  position: absolute;
  width: 10px;
  height: 10px;
  border: 1px solid rgba(255, 255, 255, 0.35);
}
.viewfinder-corner.tl { top: -1px; left: -1px; border-right: none; border-bottom: none; }
.viewfinder-corner.tr { top: -1px; right: -1px; border-left: none; border-bottom: none; }
.viewfinder-corner.bl { bottom: -1px; left: -1px; border-right: none; border-top: none; }
.viewfinder-corner.br { bottom: -1px; right: -1px; border-left: none; border-top: none; }
```

**When to apply:** Primary analysis images, uploaded evidence, any image that represents "input being examined." Pairs with the Dossier Frame—brackets on the image, dossier grid on the container.

---

## Scroll-Scrub Expand

The hero video starts as an inset card (688px max-width, rounded corners, perspective tilt, heavy shadow) and expands to full-bleed viewport on scroll. Driven entirely by a CSS custom property (`--hero-scrub-expand`, 0→1) set from scroll position.

**Key interpolations as expand goes 0→1:**
- `max-width`: 688px → 100%
- `border-radius`: 22px → 0
- `transform`: `perspective(2400px) rotateX(2.6deg) scale(0.91)` → `none`
- Shadow intensity decreases as the card fills the viewport
- Copy above the card fades out and shrinks via `opacity` + `max-height` + `font-size` interpolation

**When to apply:** Product hero sections where you want the key visual to start as a contained preview and expand into an immersive full-bleed experience. The perspective tilt gives the initial card a 3D "floating document" quality.

---

## Glass Navigation Bar

The nav is a floating, inset bar—not edge-to-edge. It sits 16px + safe-area below the top, 20px + safe-area from sides, with 14px border-radius.

**Key traits:**
- Background: `rgba(0,0,0,0.28)` with `backdrop-filter: blur(26px) saturate(1.06)`
- Border: `1px solid rgba(255,255,255,0.08)`, bottom border transparent
- Shadow: `0 18px 50px rgba(0,0,0,0.35)`
- On scroll: background darkens to `rgba(0,0,0,0.5)`, border becomes visible at 0.12 opacity
- Active nav items get a 4px accent-blue dot with `box-shadow: 0 0 6px` glow

**When to apply:** Dark-mode marketing sites, product landing pages. The inset-from-edges pattern (not flush) is distinctive—most navs go edge-to-edge. The floating quality reinforces the "operations overlay" metaphor.

---

## Eyebrow Conventions

Raven uses two eyebrow styles, both in mono caps:

1. **Section eyebrow**: 11px, 500 weight, 0.24em tracking, with `§` prefix and number in accent color
2. **Contextual eyebrow**: 10px, 500 weight, 0.28em tracking, with a 6px colored dot (`box-shadow: 0 0 14px` wash) or a 40px × 1px bar separator

Both are uppercase. Both use `--font-mono`. The eyebrow is ALWAYS above the headline, never inline.

**When to apply:** Every section needs an eyebrow. It's the primary wayfinding device on the page—without it, sections blend into a wall of headlines.
