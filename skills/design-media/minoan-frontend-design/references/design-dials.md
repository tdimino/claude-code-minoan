# Design Dials

Three calibration scales for controlling design output. Default baseline: **8 / 6 / 4**. Override when the user specifies intensity ("make it minimal," "pack it dense," "go cinematic").

---

## DESIGN_VARIANCE (1-10)

Controls layout asymmetry, grid complexity, and spatial risk.

| Range | Behavior | CSS Patterns |
|-------|----------|-------------|
| 1-3 | Symmetric, centered, predictable | `justify-center`, 12-column even grids, equal padding |
| 4-5 | Slight offset, mixed alignment | `margin-top: -2rem` overlaps, left-aligned headers over centered data |
| 6-7 | Asymmetric grids, varied ratios | `grid-template-columns: 2fr 1fr`, mixed aspect ratios (4:3 beside 16:9) |
| 8-9 | Masonry, fractional units, dramatic whitespace | `grid-template-columns: 2fr 1fr 1fr`, `padding-left: 20vw` |
| 10 | Grid-breaking, overlapping layers, z-depth chaos | `position: absolute` overlaps, `clip-path` fragments, rotated elements |

**Mobile override (levels 4+):** Asymmetric layouts collapse to single-column (`w-full`, `px-4`, `py-8`) below 768px. High variance at desktop does not mean high variance at mobile.

## MOTION_INTENSITY (1-10)

Controls animation complexity and continuous movement.

| Range | Behavior | CSS Patterns |
|-------|----------|-------------|
| 1-2 | Static. No automatic animations | CSS `:hover` and `:active` states only |
| 3-4 | Subtle transitions on interaction | `transition: transform 0.2s ease-out, opacity 0.2s ease-out` |
| 5-6 | Staggered load-in, scroll reveals | `animation-delay: calc(var(--i) * 75ms)`, IntersectionObserver triggers |
| 7-8 | Parallax, continuous micro-animations | `@keyframes float`, scroll-driven transforms, breathing status indicators |
| 9-10 | Choreographed sequences, physics-based | Spring easings, scroll-hijack galleries, perpetual carousel loops |

**Constraint at all levels:** Content visible at `t=0` with CSS only. Motion enhances what's already rendered—never gates visibility behind JavaScript class toggles or animation delays on opacity.

## VISUAL_DENSITY (1-10)

Controls information packing, spacing, and container usage.

| Range | Behavior | CSS Patterns |
|-------|----------|-------------|
| 1-2 | Art gallery. Huge section gaps, everything breathes | `py-24`, `max-w-2xl`, generous line-height |
| 3-4 | Editorial. Comfortable reading density | `py-16`, `max-w-4xl`, standard spacing |
| 5-6 | Standard app. Normal spacing for web applications | `py-8`, `gap-4`, balanced card layouts |
| 7-8 | Dense app. Compact metrics, tight grids | `py-2`, `gap-2`, `text-sm`, thin border separators |
| 9-10 | Cockpit. Maximum data above fold, no card containers | `py-1`, `divide-y`, `font-mono` for numbers, 1px separators |

**Dashboard rule (density 7+):** Replace card containers with logic-grouping via `border-t`, `divide-y`, or negative space. Monospace for all numerical data. Every metric, chart, and control visible without scrolling.

---

## Natural Language Mapping

| User says | Suggested dials |
|-----------|----------------|
| "clean," "minimal," "simple" | VARIANCE 3-4, MOTION 2-3, DENSITY 2-3 |
| "modern SaaS," "professional" | VARIANCE 5-6, MOTION 5-6, DENSITY 5-6 |
| "editorial," "magazine" | VARIANCE 7-8, MOTION 4-5, DENSITY 3-4 |
| "Bloomberg terminal," "command center" | VARIANCE 3-4, MOTION 4, DENSITY 9-10 |
| "cinematic," "immersive" | VARIANCE 8-9, MOTION 8-9, DENSITY 2-3 |
| "brutalist," "raw" | VARIANCE 9-10, MOTION 1-2, DENSITY 5-7 |
| "luxury," "refined" | VARIANCE 5-6, MOTION 3-4, DENSITY 2-3 |
| "dashboard," "analytics" | VARIANCE 3-5, MOTION 3-4, DENSITY 8-9 |
| "playful," "whimsical" | VARIANCE 7-8, MOTION 7-8, DENSITY 3-4 |
| "data-dense," "packed" | VARIANCE 2-3, MOTION 2-3, DENSITY 9-10 |
