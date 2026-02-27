# 2026 Presentation Design Best Practices

Updated guidance for deck building. When this file conflicts with `design-system.md`, prefer these rules — they reflect current research on engagement, readability, and persuasion.

---

## Typography

- Set body text minimum at 16px (`text-base` in Tailwind). Never use `text-sm` (14px) for body content.
- Follow the Major Third ratio (1.25x) for the full type scale:

| Token | Size | Tailwind | Usage |
|-------|------|----------|-------|
| `display` | 48px | `text-5xl` | Title slide only |
| `heading-1` | 36px | `text-4xl` | Section headers |
| `heading-2` | 24px | `text-2xl` | Card group titles |
| `heading-3` | 20px | `text-xl` | Card titles |
| `stat` | 30px | `text-3xl` | Metric numbers |
| `body` | 16px | `text-base` | Main body text |
| `body-sm` | 14px | `text-sm` | Secondary descriptions only |
| `label` | 12px | `text-xs` | Badges, chapter numbers, citations |
| `fine` | 10px | `text-[10px]` | Tech labels, corner annotations only |

- Never use arbitrary sizes like `text-[42px]` — stay on the scale.
- Set line height to 1.5x for body, 1.2x for headers.
- Limit to 2 typefaces maximum: one for display (Playfair Display), one for body (DM Sans), plus mono (JetBrains Mono) for technical labels.

---

## Content Density

- Cap at 30-40 words per slide maximum.
- Enforce one message per slide. If it needs a full minute of explanation, split it.
- Target distribution: 20% text, 40% visuals, 40% whitespace.
- Favor graphs over tables, bullet points over paragraphs.
- Decks with a clear, focused message per slide are 43% more persuasive.

---

## Slide Count

- Target 10-18 slides for the full deck.
- 10-slide decks achieve the highest completion rate (32% vs 22% average).
- Engagement drops sharply after 18 slides.
- Prioritize substance over count — cut filler slides ruthlessly.

---

## Color

- Use 3-5 colors maximum per deck.
- Assign one accent color for emphasis on key metrics and CTAs.
- Give each chapter a distinct accent that carries through its slides.
- Never mix dark and light backgrounds arbitrarily within a single deck.
- Apply color semantics consistently:

| Color | Semantic | Usage Rule |
|-------|----------|------------|
| Red | Urgency, critical | Use sparingly — critical metrics only |
| Blue | Trust, stability, intelligence | Dominant choice for tech audiences |
| Green (accent) | Growth, progress | Positive metrics, success indicators |
| Purple | Premium, visionary | Transformative themes |
| Orange (accent) | Energy, urgency | Calls to action |

---

## Light vs Dark Mode

### Dark Mode (default for Aldea)

- Stronger signal for tech/AI audiences. Modern and premium feel.
- Use deep navy or near-black bases (`#0a0f1a` to `#1A1A2E`) with white text.
- Vivid accent colors pop naturally on dark backgrounds.
- Matches the existing Aldea blueprint aesthetic.

### Light Mode (use for specific audiences)

- Better for PDF distribution, printed decks, and non-technical audiences.
- Use off-white or soft gray bases (`#FAFBFC`, `#F1F3F5`) with dark text.
- Darken chapter accents for readability (e.g., `#fbbf24` becomes `#D97706`).
- Test contrast ratios — light mode requires more careful accent tuning.

---

## Data Visualization

- Make every chart readable without explanation.
- Include a 1-line interpretation caption on every graph.
- Prefer icon-based visualizations over traditional charts for simple comparisons.
- Use bold number callouts (72-120pt / `text-7xl` to `text-9xl`) for key metrics.
- Never use a table where a chart will suffice.
- Maintain consistent chart styling (colors, fonts, grid lines) across all slides.

---

## Structural Best Practices

- Include a team slide. 96% of top-performing decks have one.
- Include client logos. 97% of top decks show them.
- Open with market pain, not technology. Lead with the problem.
- Show product early (slides 3-4) — screenshots, not architecture diagrams.
- Cite every metric. "95% failure rate" needs a source annotation.

---

## Personalization

- Including the recipient's name or context yields +29% engagement.
- Adapting to the audience's domain yields +33% engagement.
- Combining both yields +47% improvement.
- When building for a known audience, tailor the opening slide, examples, and metric selections to their specific context.

---

## Reconciliation with Aldea Design System

This file updates the following defaults from `design-system.md`:

| Element | Old Default | New Default | Reason |
|---------|-------------|-------------|--------|
| Body text | `text-sm` (14px) | `text-base` (16px) | Readability research |
| Display | `text-6xl` (60px) | `text-5xl` (48px) | Major Third scale alignment |
| H2 | `text-3xl` (30px) | `text-2xl` (24px) | Cleaner hierarchy |
| H3 | `text-sm` (14px) | `text-xl` (20px) | Card titles need prominence |

All other design tokens (colors, spacing, grid, animations) remain unchanged. Apply the updated scale when building new decks; existing decks do not need retroactive changes.
