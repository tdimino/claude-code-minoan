# Inline Data Visualization

Lightweight, CSS-first data visualization patterns for embedding within cards, articles, and landing page sections. No charting library dependencies—pure CSS + minimal JS for animation.

---

## Pattern 1: Horizontal Bar Chart

For win rates, completion percentages, survey results. Used inline within research cards and article figures.

```html
<div class="space-y-3" role="group" aria-label="Win rates by phase">
  <!-- Single bar row -->
  <div class="flex items-center gap-3">
    <span class="w-20 text-right text-xs text-zinc-500 uppercase tracking-wider">
      Ideation
    </span>
    <div class="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
      <div
        class="h-full rounded-full bg-amber-500 transition-all duration-700 ease-out"
        style="width: 79.8%"
        role="meter"
        aria-valuenow="79.8"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-label="Ideation: 79.8%"
      ></div>
    </div>
    <span class="w-14 text-right text-sm font-mono tabular-nums text-zinc-300">
      79.8%
    </span>
  </div>

  <div class="flex items-center gap-3">
    <span class="w-20 text-right text-xs text-zinc-500 uppercase tracking-wider">
      Mockup
    </span>
    <div class="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
      <div
        class="h-full rounded-full bg-amber-500/70"
        style="width: 68.9%"
        role="meter" aria-valuenow="68.9" aria-valuemin="0" aria-valuemax="100"
      ></div>
    </div>
    <span class="w-14 text-right text-sm font-mono tabular-nums text-zinc-300">
      68.9%
    </span>
  </div>

  <div class="flex items-center gap-3">
    <span class="w-20 text-right text-xs text-zinc-500 uppercase tracking-wider">
      Refinement
    </span>
    <div class="flex-1 h-2 bg-zinc-800 rounded-full overflow-hidden">
      <div
        class="h-full rounded-full bg-emerald-500"
        style="width: 60%"
        role="meter" aria-valuenow="60" aria-valuemin="0" aria-valuemax="100"
      ></div>
    </div>
    <span class="w-14 text-right text-sm font-mono tabular-nums text-zinc-300">
      60.0%
    </span>
  </div>
</div>
```

### Bar Color Semantics

| Context | Color | Tailwind |
|---------|-------|---------|
| Default/primary metric | Amber | `bg-amber-500` |
| Secondary/supporting | Amber reduced | `bg-amber-500/70` |
| Positive/winning | Emerald | `bg-emerald-500` |
| Negative/declining | Rose | `bg-rose-500` |
| Neutral/baseline | Zinc | `bg-zinc-500` |
| Brand accent | Custom | Use OKLCH variable |

### Bar Height Variants

| Context | Height | Class |
|---------|--------|-------|
| Inline in card (compact) | 6px | `h-1.5` |
| Article figure (standard) | 8px | `h-2` |
| Dashboard (prominent) | 12px | `h-3` |
| Hero stat (bold) | 16px | `h-4` |

---

## Pattern 2: Stat Callout Block

Large single-stat highlight for embedding in cards or article margins.

```html
<div class="rounded-xl bg-zinc-800/50 p-6 text-center">
  <span class="block text-4xl font-bold text-white font-mono tabular-nums">
    66%
  </span>
  <p class="mt-2 text-sm text-zinc-400 max-w-xs mx-auto leading-relaxed">
    of independent creatives report higher earning potential since adopting AI
  </p>
  <p class="mt-1 text-xs text-zinc-600">
    26% no · 8% other
  </p>
</div>
```

### Stat Callout Variants

| Layout | Description |
|--------|-------------|
| Centered (default) | Number above, description below, centered text |
| Left-aligned inline | Number and description on same line, `flex items-baseline gap-3` |
| With comparison | Two numbers side by side with arrow or delta indicator |
| With sparkline | Number above, tiny CSS sparkline below (see Pattern 5) |

---

## Pattern 3: Animated Number Counter

Count-up animation triggered on scroll into view. No library needed.

```html
<span
  class="text-5xl font-bold text-white font-mono tabular-nums"
  data-count-to="1500000"
  data-count-suffix="+"
  data-count-prefix=""
>
  0
</span>
```

```js
const counters = document.querySelectorAll('[data-count-to]');

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (!entry.isIntersecting) return;
    const el = entry.target;
    const target = parseInt(el.dataset.countTo, 10);
    const suffix = el.dataset.countSuffix || '';
    const prefix = el.dataset.countPrefix || '';
    const duration = 1500;
    const start = performance.now();

    function update(now) {
      const progress = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      const current = Math.floor(eased * target);
      el.textContent = prefix + current.toLocaleString() + suffix;
      if (progress < 1) requestAnimationFrame(update);
    }

    requestAnimationFrame(update);
    observer.unobserve(el);
  });
}, { threshold: 0.3 });

counters.forEach((el) => observer.observe(el));
```

### Number Formatting

| Value | Display | Implementation |
|-------|---------|---------------|
| 1500000 | 1,500,000+ | `toLocaleString() + suffix` |
| 1500000 | 1.5M+ | Custom formatter: `(n / 1e6).toFixed(1) + 'M'` |
| 250000000 | $250M+ | `prefix: '$'`, format as above |
| 26 | 26x | `suffix: 'x'` |

---

## Pattern 4: Comparison Row

Side-by-side percentage comparison, used for A/B results or before/after.

```html
<div class="flex items-center gap-4 py-3">
  <!-- Left value -->
  <div class="text-right w-20">
    <span class="text-2xl font-bold text-emerald-400 font-mono tabular-nums">61%</span>
    <p class="text-xs text-zinc-500 mt-0.5">Ideation</p>
  </div>

  <!-- Visual bar comparison -->
  <div class="flex-1 flex h-3 rounded-full overflow-hidden bg-zinc-800">
    <div class="bg-emerald-500 rounded-l-full" style="width: 61%"></div>
    <div class="bg-rose-500 rounded-r-full" style="width: 39%"></div>
  </div>

  <!-- Right value -->
  <div class="w-20">
    <span class="text-2xl font-bold text-rose-400 font-mono tabular-nums">39%</span>
    <p class="text-xs text-zinc-500 mt-0.5">Refinement</p>
  </div>
</div>
```

---

## Pattern 5: CSS Sparkline

Tiny inline trend indicator (no SVG, pure CSS gradient).

```html
<div class="inline-flex items-end gap-px h-4 w-16">
  <div class="w-1 bg-zinc-500 rounded-sm" style="height: 40%"></div>
  <div class="w-1 bg-zinc-500 rounded-sm" style="height: 55%"></div>
  <div class="w-1 bg-zinc-500 rounded-sm" style="height: 45%"></div>
  <div class="w-1 bg-zinc-500 rounded-sm" style="height: 70%"></div>
  <div class="w-1 bg-zinc-500 rounded-sm" style="height: 65%"></div>
  <div class="w-1 bg-zinc-500 rounded-sm" style="height: 80%"></div>
  <div class="w-1 bg-emerald-500 rounded-sm" style="height: 90%"></div>
</div>
```

Last bar highlighted in accent color to indicate current/latest value.

---

## Pattern 6: Phase Flow Indicator

Visual representation of a multi-phase process with control intensity gradient (Contra's "grip" metaphor).

```html
<div class="flex items-stretch gap-0.5 rounded-lg overflow-hidden h-2">
  <div class="flex-1 bg-amber-500/40" aria-label="Ideation — Loose grip"></div>
  <div class="flex-1 bg-amber-500/70" aria-label="Mockup — Narrowed"></div>
  <div class="flex-1 bg-amber-500" aria-label="Refinement — Firm grip"></div>
</div>
<div class="flex justify-between mt-1.5 text-xs text-zinc-500">
  <span>Ideation</span>
  <span>Mockup</span>
  <span>Refinement</span>
</div>
```

---

## Accessibility

- Bar charts: `role="meter"` with `aria-valuenow`, `aria-valuemin`, `aria-valuemax`
- Chart containers: `role="img"` with `aria-label` describing the data
- Animated counters: final value set immediately for screen readers (animation is visual-only enhancement)
- Color alone never carries meaning—pair with labels, patterns, or position
- `prefers-reduced-motion: reduce` → skip count-up animation, show final value immediately. Handle in the JS observer callback:
  ```js
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReducedMotion) {
    el.textContent = prefix + target.toLocaleString() + suffix;
    observer.unobserve(el);
    return;
  }
  ```

## Responsive

All patterns are flex-based and scale naturally. For very narrow viewports:
- Bar labels stack vertically (`flex-col` instead of row)
- Stat callouts shrink text (`text-3xl` → `text-2xl`)
- Sparklines maintain fixed width (`w-16`) regardless of container
