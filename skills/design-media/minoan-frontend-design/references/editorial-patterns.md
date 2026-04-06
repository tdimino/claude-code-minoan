# Editorial Patterns

Techniques distilled from 73 blind A/B eval comparisons against the wetch baseline. These patterns consistently appear in judge praise for winning designs. Consult when building landing pages, dashboards, or components that need editorial-level distinction.

---

## Photo vs SVG Distinction

When testimonials, team members, or customer photos are requested, use real portrait URLs (`https://i.pravatar.cc/` or Unsplash face queries) — SVG initial circles read as placeholder to judges. Reserve custom SVG illustration for heroes, backgrounds, and contextual imagery where the art IS the design.

| Content Type | Approach |
|-------------|----------|
| Human faces, testimonials, team photos | Real photo URLs (pravatar, Unsplash) |
| Hero imagery, decorative elements | Custom SVG fitted to context |
| Product screenshots, data visualizations | Generated SVG charts/mockups |
| Logos, brand marks | Typographic or geometric SVG |

## Asymmetric Grid Ratios

Equal-width columns (`1fr 1fr`, `repeat(3, 1fr)`) read as "template" to judges. Asymmetric ratios create editorial dynamism:

| Layout | Ratio | CSS |
|--------|-------|-----|
| Two-column, content-heavy left | 7fr 5fr | `grid-template-columns: 7fr 5fr` |
| Two-column, content-heavy right | 5fr 7fr | `grid-template-columns: 5fr 7fr` |
| Three-column, weighted center | 3fr 5fr 4fr | `grid-template-columns: 3fr 5fr 4fr` |
| Three-column, progressive | 2fr 3fr 5fr | `grid-template-columns: 2fr 3fr 5fr` |
| Bento with feature tile | named grid areas | `grid-template: "a a b" "a a c" "d e c"` |

## Ghost Text & Watermark Implementation

Ghost numbers and decorative text behind content add editorial depth — but implementation matters. Too visible (opacity > 0.08) creates "visual noise" per judges. Too faint is invisible in screenshots.

- **Opacity**: 0.03–0.06 range. Start at 0.04 and adjust.
- **Rotation**: 30–45deg, positioned as background texture
- **Position**: `position: absolute` behind content, never inline
- **Content**: Roman numerals, section numbers, brand marks, single oversized letters
- **Never**: Competing with foreground text or cluttering composition

## Singular Accent Strategy

Multi-color accent systems read as "balanced" but not "bold." One electric accent color against a committed base creates stronger editorial identity:

| Base | Accent | Mood |
|------|--------|------|
| Rich off-black (zinc-950) | Acid yellow (#E5FF00) | Tech/terminal |
| Deep navy (#0a0e27) | Signal cyan (#00f0ff) | Data/fintech |
| Warm cream (#faf5eb) | Hot coral (#ff4444) | Editorial/luxury |
| Charcoal (#1a1a2e) | Deep rose (#e94560) | Creative/bold |
| Parchment (#f4efe6) | Amber (#d4a017) | Scholarly/warm |

Use the accent for: primary CTAs, key metrics, active states, one decorative element. Everything else stays in the base palette.

## Category-Specific Patterns

From per-category win rates across all eval rounds:

**Landing pages (88% win rate)**: Warm palettes + context-rooted concepts + editorial typography. Lead with warmth over darkness. The cream/parchment/amber palette family is our strongest differentiator.

**Dashboards (50%, up from 0%)**: Dense information above the fold. Monospace for all numbers. Terminal-style conceptual framing ("command center," "mission control"). Thin borders over card containers.

**Components (67%)**: Engineering awareness helps — semantic HTML, keyboard navigation, proper states. Wins come from working functionality paired with visual refinement.

**Creative/edge prompts**: Boldness wins. The completeness mandate should not suppress creative risk. Push past the first satisfying idea.

## Portfolio & Personal Site Patterns

Patterns for portfolio sites, freelancer pages, and personal brand sites. See `rothenberg-portfolio-patterns.md` for the full "Dark Editorial Portfolio" archetype with CSS snippets.

**Text-only CTA**: On personal sites, button chrome feels commercial. Use large editorial text with italic emphasis and a Unicode arrow (→) as the action affordance. The typography IS the button — no background, no border. Only works when surrounding content has built trust.

**Section labels as monospace wayfinding**: Small monospace text (`0.75rem`, uppercase, `letter-spacing: 0.12em`, muted color) that orients without demanding attention. Functions as wayfinding ("I FREELANCE", "I WRITE WORDS"), not heading hierarchy. Precedes each content block.

**Oversized body text as design statement**: Setting body prose at 32-40px (2-2.5rem) makes text the hero. No images needed. The constraint forces premium through font selection and spacing. Effective for portfolios where the person's voice is the product.

**Link underline opacity**: Instead of changing link color, keep `color: inherit` and set `text-decoration-color` at 40% opacity, rising to 80% on hover. Maintains typographic rhythm — links don't break the reading flow. See `rothenberg-portfolio-patterns.md` for the full CSS snippet.
