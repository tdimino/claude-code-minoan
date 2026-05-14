# Raven Component Patterns

Reverse-engineered component architecture from withraven.ai (May 2026). Each entry: component name, visual description, DOM/CSS mechanism, and when to use. Complements `raven-design-tokens.md` and `raven-signature-techniques.md`.

---

## Glass Nav Bar

Floating sticky navigation inset from all edges—not edge-to-edge. Blurred glass background with near-invisible border.

```css
.nav {
  position: sticky;
  top: calc(16px + env(safe-area-inset-top, 0px));
  margin: calc(16px + env(safe-area-inset-top, 0px)) max(20px, env(safe-area-inset-right)) 0 max(20px, env(safe-area-inset-left));
  padding: 18px 40px;
  border-radius: 14px;
  background: rgba(0, 0, 0, 0.28);
  backdrop-filter: blur(26px) saturate(1.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-bottom-color: transparent;
  box-shadow: 0 18px 50px rgba(0, 0, 0, 0.35);
}
```

Layout: logo left, nav links center (`500 13px sans, rgba(255,255,255,0.68)`), CTAs right. Dropdown menus appear as near-solid panels (`rgba(10,11,13,0.995)`) with icon + title + description rows. On scroll: background darkens to 50% opacity, border brightens. Active items: white text + 4px accent dot with glow.

Mobile: hamburger button reveals slide-down panel with section labels in mono caps and full-width CTAs.

Use for dark-mode marketing sites, product landing pages, intelligence dashboards.

---

## Breadcrumb Lockup

Parent-brand → product navigation in the nav bar. Two elements: parent name (mono 10px, 55% white) + separator (mono 12px, 22% white).

```css
.breadcrumb-parent {
  font: 500 10px/1 var(--font-mono);
  letter-spacing: 0.12em;
  color: rgba(255, 255, 255, 0.55);
}
.breadcrumb-sep {
  color: rgba(255, 255, 255, 0.22);
  font: 400 12px/1 var(--font-mono);
}
```

Hover: parent text goes white. Use when the product is part of a larger brand family.

---

## Section Eyebrow

Mono-caps wayfinding label above every section heading. Two variants:

**Numbered variant** (primary sections):
```html
<div class="section-eyebrow">
  <span class="sym">§</span><span class="num">02</span>
  <span class="sep">·</span> Find Region · Geoestimation
  <span class="count">02</span>
</div>
```
Number in accent blue, symbol/separator in 55% white. Font: `500 11px/1 mono, 0.22em tracking, uppercase`.

**Dot variant** (subsections):
```css
.eyebrow .dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 14px var(--accent-wash);
}
```
Font: `500 10px/1 mono, 0.28em tracking`.

Both are always uppercase. Always above the headline, never inline.

Use above every section on a long-form page. The section number creates a classified-document feel.

---

## Section Heading

Section headlines beneath the eyebrow.

```css
.section-h {
  font: 300 clamp(40px, 5.6vw, 72px)/1.0 var(--font-sans);
  letter-spacing: -0.03em;
  color: #fff;
  text-wrap: balance;
}
.section-sub {
  font: 300 18px/1.5 var(--font-serif);
  color: rgba(255, 255, 255, 0.72);
  max-width: 640px;
  text-wrap: pretty;
}
```

The heading is light-weight sans (300), the subheading is light-weight serif (300). The serif creates a briefing-document counterpoint. `text-wrap: balance` on the heading prevents awkward orphans at responsive sizes.

---

## Buttons

**Primary** — Near-white on dark. The inset hairline creates a subtle bevel.
```css
.btn-primary {
  background: #fff;
  color: #0A0B0D;
  font: 500 13px/1 var(--font-sans);
  padding: 12px 20px;
  border-radius: 3px;
  letter-spacing: -0.005em;
  box-shadow: none;
}
```

**Outline** — Hairline border, transparent background.
```css
.btn-outline {
  background: transparent;
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.28);
}
/* hover: border-color rgba(255,255,255,0.6), bg rgba(255,255,255,0.03) */
```

**Ghost** — No border, text only.
```css
.btn-ghost { background: transparent; color: rgba(255, 255, 255, 0.75); }
```

**Dossier variant** — Mono caps with tick-arrow indicator. Applied via `body[data-btn-style="dossier"]`:
```css
.dossier .btn {
  font: 500 11px/1 var(--font-mono);
  letter-spacing: 0.22em;
  text-transform: uppercase;
}
```

Key: 3px radius on all buttons (sharper than the 6px/8px convention). 120ms color transitions. Arrow-hover links slide the arrow 2px right on hover (200ms ease).

---

## Fan-Out Pipeline Stage

The signature visual: one input image fans out via SVG connector lines to three output cards. Represents "fragments in, intelligence out."

```
┌─────────────────┐       ┌── Output A (Where)
│  INPUT IMAGE    │──────>├── Output B (Which)
│  [corner marks] │       └── Output C (What)
└─────────────────┘
   36% width               72% left offset
```

**Input frame** (left, ~36% width):
```css
.input-frame {
  position: relative;
  aspect-ratio: 4/3;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: #000;
}
.input-frame img {
  filter: grayscale(0.1) brightness(0.86) contrast(1.05);
}
```
Corner brackets at all four corners (see below). Mono-caps label above ("INPUT · LOW-CONTEXT IMAGE").

**SVG connectors** (middle): Absolute-positioned SVG with curved paths from input center to each output position. Hidden on mobile.

**Output cards** (right, stacked at 72% left):
```css
.output-kind {
  font: 500 10px/1 var(--font-mono);
  letter-spacing: 0.26em;
  color: var(--accent);
  text-transform: uppercase;
}
.output-name {
  font: 400 clamp(22px, 2.4vw, 30px)/1.1 var(--font-sans);
  letter-spacing: -0.02em;
  color: #fff;
}
.output-result {
  font: 400 14px/1.4 var(--font-serif);
  font-style: italic;
  color: rgba(255, 255, 255, 0.6);
}
.output-jump {
  font: 500 10px/1 var(--font-mono);
  letter-spacing: 0.22em;
  color: rgba(255, 255, 255, 0.6);
  text-transform: uppercase;
}
```

Mobile collapse: stacked layout with 92px left column for thumbnails, 1fr right column for text. SVG connectors hidden.

Use for product capability showcases, data pipeline explainers, any input→process→output narrative.

---

## Corner Bracket Viewfinder

10×10px L-shaped border marks at image corners. Creates a forensic targeting reticle.

```css
.corner { position: absolute; width: 10px; height: 10px; border: 1px solid rgba(255,255,255,0.35); }
.corner.tl { top: -1px; left: -1px; border-right: none; border-bottom: none; }
.corner.tr { top: -1px; right: -1px; border-left: none; border-bottom: none; }
.corner.bl { bottom: -1px; left: -1px; border-right: none; border-top: none; }
.corner.br { bottom: -1px; right: -1px; border-left: none; border-top: none; }
```

Use on evidence images, uploaded content being analyzed, any image that represents "input under examination."

---

## Dossier Frame

Double-layer overlay on evidence containers: dashed inner border + grid pattern.

```css
.dossier-frame::before {
  content: ""; position: absolute; inset: 8px;
  border: 1px dashed rgba(255, 255, 255, 0.18);
  pointer-events: none;
}
.dossier-frame::after {
  content: ""; position: absolute; inset: 0;
  background-image:
    linear-gradient(to right, rgba(255,255,255,0.035) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(255,255,255,0.035) 1px, transparent 1px);
  background-size: 18px 18px;
  pointer-events: none;
}
```

Reserve for focal content—analysis results, primary evidence. Don't apply to every card.

---

## Capability Index Card

Three-column grid of capability previews with numbered headers.

```css
.cap-index {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1px;
  background: rgba(255, 255, 255, 0.08); /* gap color */
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  overflow: hidden;
}
.cap-index-cell {
  padding: 36px 32px 32px;
  background: #070809; /* near-void */
}
```

Content stack: number (mono 11px, accent blue) → kind (mono 11px, uppercase, 78% white) → heading (sans 26px/300, `-0.018em`) → sub (serif 15px/300, 68% white) → footer link (mono 11px, uppercase, top hairline border). Hover: background shifts to `#0d0f14`.

Single column on mobile. Use for capability showcases, feature comparison, product overview grid.

---

## KPI Stat

Hero metrics in a horizontal row. Three elements stacked.

```css
.kpi-eyebrow {
  font: 500 10px/1 var(--font-mono);
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.55);
}
.kpi-eyebrow::before {
  content: "";
  display: inline-block;
  width: 8px; height: 2px;
  background: var(--accent);
  margin-right: 8px;
  vertical-align: middle;
}
.kpi-n {
  font: 700 48px/1.0 var(--font-sans);
  color: #fff;
  letter-spacing: -0.01em;
}
.kpi-u {
  font: 400 14px/1.0 var(--font-sans);
  color: rgba(255, 255, 255, 0.55);
}
.kpi-cap {
  font: 400 14px/1.4 var(--font-serif);
  color: rgba(255, 255, 255, 0.55);
  font-style: italic;
}
```

Pattern: eyebrow ("TIME") → number ("7") → unit ("seconds") → qualifier ("*From photo* to actionable lead"). The qualifier uses serif italic for the contextual phrase—the only place serif appears inline with data.

Use for hero stats, product metrics, confidence summaries.

---

## Lead Row

Ranked result display with confidence score.

```css
.lead-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.lead-row-rank {
  font: 500 14px/1 var(--font-mono);
  color: rgba(255, 255, 255, 0.38);
  min-width: 24px;
}
.lead-row.top .lead-row-rank {
  color: rgb(24, 81, 255);
}
.lead-row-mid {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}
.lead-row-h {
  font: 500 15px/1.25 var(--font-sans);
  color: #fff;
  letter-spacing: -0.005em;
}
.lead-row-p {
  font: 400 13px/1.45 var(--font-sans);
  color: rgba(255, 255, 255, 0.55);
}
.lead-row-conf {
  font: 500 14px/1 var(--font-mono);
  color: rgba(255, 255, 255, 0.55);
  white-space: nowrap;
}
.lead-row.top .lead-row-conf {
  color: rgb(24, 81, 255);
  font-weight: 700;
}
```

Top-ranked row gets accent styling (blue rank number, bolder confidence). Use for search results, ranked matches, investigation leads.

---

## Case Card

Investigation card with status badge, image, and metadata.

```css
.case-card {
  border-radius: 8px; overflow: hidden;
  background: rgb(25, 25, 25); /* --gs-canvas */
}
.case-card-shot { aspect-ratio: 16/10; overflow: hidden; }
.case-card-body { padding: 20px 22px; }
.case-k { font: 500 10px/1 var(--font-mono); letter-spacing: 0.22em; text-transform: uppercase; color: rgba(255,255,255,0.38); }
.case-h { font: 500 19px/1.25 var(--font-sans); color: #fff; letter-spacing: -0.01em; text-wrap: balance; }
.case-p { font: 400 13px/1.55 var(--font-sans); color: rgba(255,255,255,0.55); text-wrap: pretty; }
```

Status badges: `closed` (accent wash bg + accent text), `located` (iris soft), `recovered` (amber). Footer has mono timestamp with accent-colored time value.

Use for investigation cases, project cards, content with lifecycle status.

---

## Source Feed Row

Evidence source in a case timeline.

```
GEO  Miami, FL — Find Region     14:22 · IMG_8125.jpg    94%
CAR  2019 Honda Civic Si          14:24 · bumper.png      87%
OP   Home — S. Biscayne Dr        14:25 · operator pin    fixed
TIP  Anonymous · street obs       1h ago · ingest channel  med
```

```css
.source-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}
.source-type {
  font: 500 10px/1 var(--font-mono);
  letter-spacing: 0.18em;
  text-transform: uppercase;
  min-width: 32px;
}
.source-type.geo, .source-type.car { color: rgb(24, 81, 255); }
.source-type.op { color: rgba(255, 255, 255, 0.55); }
.source-type.tip { color: rgba(255, 255, 255, 0.38); }
.source-heading {
  font: 400 14px/1.3 var(--font-sans);
  color: rgba(255, 255, 255, 0.85);
  flex: 1;
  min-width: 0;
}
.source-meta {
  font: 400 11px/1 var(--font-mono);
  color: rgba(255, 255, 255, 0.38);
  white-space: nowrap;
}
.source-conf {
  font: 500 12px/1 var(--font-mono);
  color: rgba(255, 255, 255, 0.55);
  min-width: 36px;
  text-align: right;
}
```

Three-letter type prefix (GEO/CAR/OP/TIP) in accent or neutral, heading, timestamp + filename in muted mono, confidence or status badge right-aligned. Use for activity feeds, evidence timelines, audit logs.

---

## Dropdown Nav Menu

Full-featured dropdown from nav items. Near-solid background (not translucent—legibility over hero content).

```css
.nav-menu {
  min-width: 380px;
  padding: 10px;
  border-radius: 12px;
  background: rgba(10, 11, 13, 0.995);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 24px 60px rgba(0, 0, 0, 0.65), 0 1px 0 rgba(255,255,255,0.05) inset;
}
```

Rows: 36px icon glyph (accent-colored, 8px radius, faint border) → title (sans 14px/500) + version tag (mono 9px, 0.2em tracking) → description (sans 12px, 68% white). Hover: blue wash on glyph, description brightens. 14px bridge pseudo-element prevents hover dropout between trigger and menu.

Use for product navigation with multiple capability sections.

---

## Scroll-Scrub Hero

Video card that expands from inset preview to full-bleed viewport on scroll.

**Initial state** (expand=0): `max-width: 688px; border-radius: 22px; transform: perspective(2400px) rotateX(2.6deg) scale(0.91)`. Heavy multi-layer shadow.

**Final state** (expand=1): full width, no radius, no transform, reduced shadow.

Driven by CSS custom property `--hero-scrub-expand` (0→1) set from scroll position. Copy above the card fades via opacity + max-height interpolation. Video uses `object-fit: cover`.

Mobile: perspective tilt removed, card still expands but without 3D effect. `prefers-reduced-motion`: video hidden entirely.

Use for product hero sections where the key visual should start contained and become immersive.
