# Creative Arsenal

Advanced technique library for distinctive interfaces. Each entry: name, description, CSS/HTML mechanism, and when to use. Pull from this when a design needs a specific high-impact technique.

---

## Navigation & Interaction

**Dock Magnification** — Icons scale fluidly on hover like macOS Dock.
`transform: scale(calc(1 + 0.5 * var(--proximity)))` with CSS `--proximity` set via mousemove. Use for icon-heavy nav bars.

**Magnetic Button** — Button pulls toward cursor on approach.
`transform: translate(var(--dx), var(--dy))` with `transition: transform 0.3s cubic-bezier(0.33, 1, 0.68, 1)`, coordinates from mousemove. Use for hero CTAs.

**Contextual Radial Menu** — Circular menu expanding from click coordinates.
`transform: rotate(calc(var(--i) * 60deg)) translateX(80px)` with staggered delays. Use for right-click or long-press contexts.

**Dynamic Island** — Pill-shaped element that morphs to show status/alerts.
`border-radius: 9999px` + `width`/`height` transitions with `overflow: hidden`. Use for persistent status indicators.

## Layout & Grids

**Bento Grid** — Asymmetric tile-based grouping (Apple Control Center style).
`grid-template: "a a b" "a a c" "d e c" / 1fr 1fr 1fr` with named areas. Use for feature sections, dashboards.

**Split Screen Scroll** — Two halves sliding in opposite directions on scroll.
Two columns with `position: sticky; top: 0` on one side, normal scroll on the other. Use for comparison layouts, before/after.

**Curtain Reveal** — Content parts like curtains on scroll.
Two `clip-path: inset()` elements animated via scroll position. Use for dramatic section transitions.

**Masonry Layout** — Staggered grid without fixed row heights.
CSS `columns: 3` with `break-inside: avoid`, or `grid-template-rows: masonry` (Firefox). Use for galleries, portfolios, card collections.

## Cards & Surfaces

**Parallax Tilt Card** — 3D card tracking mouse coordinates.
`transform: perspective(1000px) rotateX(var(--ry)) rotateY(var(--rx))` from mousemove. Use for featured product cards, testimonials.

**Spotlight Border** — Card border illuminates under cursor.
`background: radial-gradient(circle at var(--x) var(--y), accent 0%, transparent 60%)` on a pseudo-element with `padding: 1px`. Use for grid cards, pricing tiers.

**Glassmorphism Panel** — True frosted glass with refraction edges.
`backdrop-filter: blur(16px); background: oklch(1 0 0 / 0.1); border: 1px solid oklch(1 0 0 / 0.15); box-shadow: inset 0 1px 0 oklch(1 0 0 / 0.1)`. Use for overlays, floating panels, nav bars over images.

**Holographic Foil** — Iridescent rainbow reflections shifting on hover.
`background: linear-gradient(var(--angle), #ff0080, #7928ca, #0070f3, #00dfd8)` with `--angle` from mousemove. Use for premium cards, badges.

## Scroll Animations

**Sticky Scroll Stack** — Cards stick to top and stack over each other.
`position: sticky; top: calc(var(--i) * 2rem)` with `z-index: var(--i)`. Use for feature walkthroughs, timeline sections.

**Horizontal Scroll Hijack** — Vertical scroll translates into horizontal pan.
Container with `position: sticky; top: 0; overflow: hidden`, inner element with `transform: translateX(calc(var(--scroll-pct) * -100%))`. Use for project galleries, case studies.

**Scroll Progress Path** — SVG path draws itself as user scrolls.
`stroke-dasharray: var(--length); stroke-dashoffset: calc(var(--length) * (1 - var(--scroll-pct)))` driven by IntersectionObserver. Use for journey maps, process flows.

**Zoom Parallax** — Background image scales with scroll position.
`transform: scale(calc(1 + var(--scroll-pct) * 0.3))` with `overflow: hidden` container. Use for hero sections, immersive intros.

## Typography Effects

**Kinetic Marquee** — Endless text bands that reverse on scroll.
`@keyframes marquee { to { transform: translateX(-50%); } }` with duplicated content. Reverse direction via `animation-direction: reverse` on scroll event. Use for brand tickers, announcement bars.

**Text Mask Reveal** — Large typography as window to video/image.
`background-clip: text; -webkit-text-fill-color: transparent; background-image: url(...)` or `mix-blend-mode: screen` over video. Use for hero headlines, section dividers.

**Text Scramble** — Characters decode on load or hover.
CSS `@keyframes` cycling `content` on pseudo-elements, or JS interval swapping random characters until resolved. Use for tech brands, loading states, reveal moments.

**Circular Text Path** — Text curved along spinning SVG path.
`<textPath href="#circle">` with `@keyframes spin { to { transform: rotate(360deg); } }`. Use for decorative badges, logos, section accents.

## Micro-Interactions

**Directional Hover Fill** — Color fills from the mouse entry side.
`background-position` or `clip-path: inset()` transition based on entry direction detected via mousemove. Use for navigation links, menu items.

**Ripple Click** — Material-style waves from click coordinates.
`::after` pseudo-element with `@keyframes ripple { to { transform: scale(4); opacity: 0; } }` positioned at `--click-x, --click-y`. Use for buttons, list items.

**Animated SVG Line Drawing** — Vectors draw their own contours.
`stroke-dasharray: var(--total); stroke-dashoffset: var(--total); animation: draw 1.5s ease-out forwards` with `@keyframes draw { to { stroke-dashoffset: 0; } }`. Use for illustrations, icons, logo reveals.

**Skeleton Shimmer** — Loading placeholder with moving light.
`background: linear-gradient(90deg, transparent, oklch(1 0 0 / 0.4), transparent); background-size: 200%; animation: shimmer 1.5s infinite`. Use for content loading states.

**Particle Burst** — Elements shatter into particles on action.
Multiple `<span>` with randomized `transform: translate(var(--dx), var(--dy)) rotate(var(--r)); opacity: 0` transitions. Use for success confirmations, delete actions.

**Mesh Gradient Background** — Organic, animated color blobs.
Multiple radial gradients with `@keyframes blob { 50% { transform: translate(20px, -20px) scale(1.1); } }` on absolute-positioned elements with `filter: blur(60px)`. Use for hero backgrounds, ambient atmosphere.

## Dashboard Archetypes

**Bloomberg Terminal** — Maximum data density, monochrome with one accent.
Single-pixel borders, `font-family: monospace`, `font-size: 12px`, ticker-style scrolling data, grid packed to edges. Accent color for alerts only.

**Mission Control** — Real-time status with hierarchical panels.
Large central visualization, smaller metric panels around edges, breathing status indicators (`@keyframes pulse`), live-updating numbers.

**Editorial Data Viz** — Charts and metrics with magazine typography.
Serif headlines over clean data tables, generous whitespace between metric groups, accent color for key figures, annotation-style callouts.

**Command Center** — Dense functional layout, sidebar + main + detail.
Three-column layout, collapsible sidebar, resizable panels via CSS `resize: horizontal`, contextual right panel, keyboard-navigable.
