# Research / Article Card Component

Card pattern for research articles, blog posts, and case studies with metadata, inline data visualizations, and category tagging. Designed for content-heavy research pages like Contra Labs, Stripe Press, or Vercel blog.

---

## Anatomy

```
┌───────────────────────────────────────────────┐
│ ┌─────────────────────────────────────────┐   │
│ │  Apr 28, 2026 · 5 min read              │   │  ← metadata row
│ │  ┌──────────┐                           │   │
│ │  │Benchmark │                           │   │  ← category tag
│ │  └──────────┘                           │   │
│ │                                         │   │
│ │  Grok Imagine is the "Polisher"         │   │  ← H3 title
│ │  model. Hand off the early rounds,      │   │
│ │  bring it in for refinement.            │   │
│ │                                         │   │
│ │  Contra Labs ran xAI's Grok Imagine...  │   │  ← summary
│ │                                         │   │
│ │  ┌────────────────────────────────────┐  │   │
│ │  │ 46% IDEATION  ████████░░░░░░░░░░  │  │   │  ← inline data viz
│ │  │ 44% MOCKUP    ████████░░░░░░░░░░  │  │   │
│ │  │ 56% REFINEMENT ██████████░░░░░░░  │  │   │
│ │  └────────────────────────────────────┘  │   │
│ │                                         │   │
│ │  Read →                                 │   │  ← CTA
│ └─────────────────────────────────────────┘   │
└───────────────────────────────────────────────┘
```

## Tailwind Implementation

### Full Card

```html
<article class="group rounded-2xl border border-zinc-800 bg-zinc-900/50 p-6
                hover:border-zinc-600 hover:bg-zinc-900 transition-all duration-200
                hover:-translate-y-0.5 hover:shadow-lg hover:shadow-zinc-950/50">
  <!-- Metadata row -->
  <div class="flex items-center gap-3 text-sm text-zinc-500">
    <time datetime="2026-04-28">Apr 28, 2026</time>
    <span aria-hidden="true">·</span>
    <span>5 min read</span>
  </div>

  <!-- Category tag -->
  <div class="mt-3">
    <span class="inline-flex items-center rounded-full px-2.5 py-0.5
                 text-xs font-medium bg-amber-500/10 text-amber-400
                 ring-1 ring-inset ring-amber-500/20">
      Benchmark
    </span>
  </div>

  <!-- Title -->
  <h3 class="mt-4 text-lg font-semibold text-zinc-100 leading-snug
             group-hover:text-white transition-colors">
    Grok Imagine is the "Polisher" model. Hand off the early rounds,
    bring it in for refinement.
  </h3>

  <!-- Summary -->
  <p class="mt-3 text-sm text-zinc-400 leading-relaxed line-clamp-3">
    Contra Labs ran xAI's Grok Imagine through every phase of ad video
    production: ideation, mockup, refinement.
  </p>

  <!-- Inline data viz (optional) -->
  <div class="mt-4 space-y-2" role="group" aria-label="Win rates by phase">
    <div class="flex items-center gap-3 text-xs">
      <span class="w-16 text-zinc-500 font-mono tabular-nums">46%</span>
      <span class="text-zinc-500 uppercase tracking-wider w-24">Ideation</span>
      <div class="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
        <div class="h-full bg-amber-500 rounded-full"
             style="width: 46%"
             role="meter" aria-valuenow="46" aria-valuemin="0" aria-valuemax="100"
             aria-label="Ideation: 46%"></div>
      </div>
    </div>
    <div class="flex items-center gap-3 text-xs">
      <span class="w-16 text-zinc-500 font-mono tabular-nums">44%</span>
      <span class="text-zinc-500 uppercase tracking-wider w-24">Mockup</span>
      <div class="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
        <div class="h-full bg-amber-500/70 rounded-full"
             style="width: 44%"
             role="meter" aria-valuenow="44" aria-valuemin="0" aria-valuemax="100"
             aria-label="Mockup: 44%"></div>
      </div>
    </div>
    <div class="flex items-center gap-3 text-xs">
      <span class="w-16 text-zinc-500 font-mono tabular-nums">56%</span>
      <span class="text-zinc-500 uppercase tracking-wider w-24">Refinement</span>
      <div class="flex-1 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
        <div class="h-full bg-emerald-500 rounded-full"
             style="width: 56%"
             role="meter" aria-valuenow="56" aria-valuemin="0" aria-valuemax="100"
             aria-label="Refinement: 56%"></div>
      </div>
    </div>
  </div>

  <!-- CTA -->
  <div class="mt-5">
    <a href="/research/article-slug"
       class="text-sm font-medium text-zinc-300 group-hover:text-white
              transition-colors">
      Read <span aria-hidden="true">→</span>
    </a>
  </div>
</article>
```

## Category Tag Colors

| Category | Background | Text | Ring |
|----------|-----------|------|------|
| Benchmark | `bg-amber-500/10` | `text-amber-400` | `ring-amber-500/20` |
| Research | `bg-cyan-500/10` | `text-cyan-400` | `ring-cyan-500/20` |
| White Paper | `bg-violet-500/10` | `text-violet-400` | `ring-violet-500/20` |
| Case Study | `bg-emerald-500/10` | `text-emerald-400` | `ring-emerald-500/20` |

Use semantic ring-inset with low-opacity background — not solid fills, which read as buttons.

## Layout Variants

| Layout | Grid | Use when |
|--------|------|----------|
| Single column | `max-w-2xl mx-auto` | Few articles, focused reading |
| Two column | `grid grid-cols-2 gap-6` | 4-8 articles, balanced density |
| Featured + grid | First card `col-span-2`, rest `grid-cols-2` | Hero article + supporting |
| List (no cards) | `divide-y divide-zinc-800` | High density, research index |

## Stat Callout Variant

For cards that lead with a single large stat instead of a bar chart:

```html
<div class="mt-4 flex items-baseline gap-2">
  <span class="text-3xl font-bold text-white font-mono tabular-nums">66%</span>
  <span class="text-sm text-zinc-500">of independent creatives report higher earning potential</span>
</div>
```

## Accessibility

- Use `<article>` as the card element
- `<time datetime="...">` for dates
- Bar charts: `aria-label` on each bar describing the data point (e.g., `aria-label="Ideation: 46% win rate"`)
- Link: wrap entire card in `<a>` or use `<a>` on the CTA only (not both — avoid nested interactive elements)
- Category tags: not interactive, no `role="button"`

## Responsive

| Breakpoint | Behavior |
|-----------|----------|
| Desktop | 2-column grid, full metadata, inline data viz visible |
| Tablet | 2-column, data viz may collapse to stat callout variant |
| Mobile | Single column, full-width cards, data viz remains (horizontal bars scale naturally) |

## Edge Cases

- **No data viz**: card works without the inline chart section — just metadata + title + summary + CTA
- **Long titles**: `line-clamp-2` on title, or let it wrap naturally (prefer wrapping for research content)
- **Missing date**: gracefully omit, don't show "Invalid Date"
- **Many categories**: if more than one tag per article, stack horizontally with `flex-wrap gap-2`
