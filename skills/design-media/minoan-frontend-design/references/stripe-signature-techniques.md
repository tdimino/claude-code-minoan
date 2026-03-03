# Stripe Signature Techniques

High-level design patterns and techniques that define Stripe's visual identity. Not individual tokens or components—these are the *why* behind Stripe's aesthetic decisions. Complements `stripe-design-tokens.md` and `stripe-component-patterns.md`.

---

## Light-Mode-First Premium

Stripe's entire marketing surface is light mode. Dark backgrounds appear only inside code blocks (`rgb(33, 45, 99)`) and the hero gradient mesh. Everything else: white or off-white (`#F6F9FC`).

**Key rules:**
- Page background: `#FFFFFF` or `#F6F9FC`, never dark
- Text: navy (`#0A2540`), never pure black (`#000000`)
- Shadows: tinted with text color (`rgba(60, 66, 87, 0.08)`), never pure black shadows
- Cards: white on off-white, elevation via shadow only—no visible borders on feature cards
- The light-mode constraint forces premium through whitespace and typography rather than contrast tricks

**When to apply:** Any time the direction says "premium," "clean," "Stripe-like," or "professional." Light-mode-first is the single most defining Stripe trait.

---

## Mesh Gradient Hero

The homepage hero uses an animated gradient mesh rendered via WebGL/canvas—not CSS gradients. It produces organic, flowing color transitions impossible with `linear-gradient` or `radial-gradient`.

**CSS approximation for static builds:**
```css
.stripe-hero {
  background: linear-gradient(135deg, #533AFD 0%, #0A2540 40%, #00D4AA 100%);
  /* Layered radials for depth */
  background:
    radial-gradient(ellipse at 20% 50%, rgba(83, 58, 253, 0.6), transparent 60%),
    radial-gradient(ellipse at 80% 20%, rgba(0, 212, 170, 0.4), transparent 50%),
    linear-gradient(135deg, #0A2540 0%, #0D1F3C 100%);
}
```

**Key traits:** Colors bleed into each other without hard edges. The gradient shifts subtly on scroll/time. Background is dark navy, accent blobs float on top.

**When to apply:** Landing page heroes, app backgrounds. Pair with white text (48px/700) and a primary CTA pair.

---

## Contextual Color Tuning

Stripe doesn't use one purple everywhere. Each page gets a tuned variant from the same violet family:

| Page | Accent | Hex | Rationale |
|------|--------|-----|-----------|
| Homepage | Stripe Purple | `#533AFD` | High-energy, brand-forward |
| Pricing | Stripe Blurple | `#635BFF` | Softer, decision-friendly |
| Payments | Stripe Violet | `#9966FF` | Warmer, product-specific |
| Docs | Docs Blue | `#5469D4` | Subdued, reading-optimized |

**Implementation:** Define accent as a CSS custom property (`--accent`) and set it per page/section. All components reference `--accent` rather than a hardcoded hex.

**When to apply:** Multi-page sites where different sections have different emotional registers (marketing vs. docs vs. pricing).

---

## Documentation-as-Design

Stripe treats documentation as a first-class design surface, not an afterthought. Docs pages have the same visual care as marketing pages.

**Key patterns:**
- **System font stack** for body text—optimized for reading, not brand expression
- **Fixed sidebar** (250px) with collapsible sections, active state via left border + weight change
- **Code blocks as visual anchors:** dark navy (`rgb(33, 45, 99)`) blocks break up the white page rhythm
- **Generous padding:** 32px top, 48px sides on content area—never cramped
- **Breadcrumbs** in muted color above the title, establishing location
- **API reference** uses the same code block styling as marketing, creating visual unity

**When to apply:** Any project with a docs or reference section. The principle: docs should look like they belong to the same brand as the marketing site.

---

## Color-Shifting Section Backgrounds

Stripe alternates section backgrounds to create visual rhythm without borders or dividers:

```
Section 1: #FFFFFF (white)
Section 2: #F6F9FC (off-white)
Section 3: #FFFFFF (white)
Section 4: #0A2540 (navy, inverted text)
```

**Rules:**
- Adjacent sections never share the same background
- The navy inversion (`#0A2540` bg + white text) appears at most once per page, usually for a testimonial or key stat
- No visible borders between sections—color change alone creates separation
- Off-white (`#F6F9FC`) is the workhorse neutral; white is the default

**When to apply:** Any long-scroll page with 4+ content sections. The alternation creates rhythm without explicit dividers.

---

## Motion Vocabulary

Stripe uses a single easing curve for nearly all transitions:

```css
transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
```

This curve is "fast-in, gentle-out"—snappy response, soft landing. It's applied to:
- Button hover (background-color, color, border-color)
- Dropdown open/close
- Card hover elevation
- Arrow slide-in on link hover

**Complementary motions:**
- Arrow slide: `transform: translateX(4px)` over `0.2s ease`
- Dropdown: `opacity` + `transform: translateY(-8px)` over `0.2s`
- Code tab switch: instant (no transition)—content swaps feel snappy

**When to apply:** Use `cubic-bezier(0.25, 1, 0.5, 1)` as the default easing for all interactive transitions. Reserve `ease` for micro-animations under 0.2s.

---

## HDS Theme System

Stripe's marketing pages use HDS (Hybrid Design System) with a theme/flavor/accent architecture expressed as CSS classes:

```html
<section class="hds-section theme--Dark flavor--Twilight accent--Cyan">
```

- **Theme**: `theme--Light` (default), `theme--Dark` (navy bg)
- **Flavor**: `flavor--Twilight` (purple-tinted dark), `flavor--Dawn` (warm light)
- **Accent**: `accent--Purple`, `accent--Cyan`, `accent--Green`

HDS ships 506+ CSS custom properties (`--hds-color-*`, `--hds-font-*`, `--hds-space-*`) that components reference. This enables section-level theming without class overrides.

**Key HDS tokens:**
- `--hds-color-action-bg-solid`: primary button background (resolves to accent)
- `--hds-color-surface-1` / `surface-2` / `surface-3`: layered backgrounds
- `--hds-color-brand-*-{25..975}`: full brand color ramp (25 = lightest, 975 = darkest)
- `--hds-shadow-*`: tinted shadow tokens at multiple elevations

**When to apply:** When building a design system that needs per-section theming. The theme/flavor/accent pattern is more flexible than simple light/dark toggle.

---

## Layout Philosophy

**Parallelogram Frames** — Product screenshots are often placed in angled frames (2-5deg rotation via `transform: perspective(1000px) rotateY(-5deg)`). This breaks the grid rigidity and adds depth.

**Alternating Left-Right** — Feature sections alternate: text-left/image-right, then image-left/text-right. Implemented via `grid-template-columns: 1fr 1fr` with `order` property toggling on odd sections.

**Bento Grids** — Major feature sections use named CSS Grid areas where some cells span 2 columns or 2 rows. The asymmetry creates visual hierarchy without explicit sizing.

**Generous Whitespace** — Section padding is typically 80-120px vertical. Content never feels cramped. The whitespace itself communicates premium positioning.

**When to apply:** Product marketing pages, feature showcases. The combination of angled frames + alternating layout + bento grids is distinctly Stripe.

---

## Premium Shadow Technique

Stripe's shadows never use pure black. They tint shadows with the nearby text color at very low opacity:

```css
/* Stripe pricing card shadow */
box-shadow:
  rgba(50, 50, 93, 0.25) 0px 2px 5px -1px,
  rgba(0, 0, 0, 0.3) 0px 1px 3px -1px;

/* Stripe docs button shadow */
box-shadow:
  0px 2px 5px rgba(60, 66, 87, 0.08),
  0px 1px 1px rgba(0, 0, 0, 0.12);
```

**Key traits:**
- First layer: tinted (navy/blue-grey at 8-25% opacity) for warmth
- Second layer: near-black at 12-30% for grounding
- Negative spread (`-1px`) keeps shadows tight
- Result: shadows that feel integrated, not floating

**When to apply:** Any elevated surface (cards, buttons, dropdowns). Replace `rgba(0, 0, 0, 0.1)` with `rgba(50, 50, 93, 0.1)` for instant premium feel.
