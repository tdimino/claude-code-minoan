# Marquee Component

Infinite horizontal scroll ticker for partner logos, brand names, announcement bars, and social proof strips. Extends the Kinetic Marquee entry in `creative-arsenal.md` with full implementation detail.

---

## Anatomy

```
┌──────────────────────────────────────────────────┐
│ overflow: hidden                                 │
│ ┌────────────────────────────────────────────┐   │
│ │ flex, animate translateX(-50%)             │   │
│ │ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐       │   │
│ │ │ Item │ │ Item │ │ Item │ │ Item │ ...   │   │
│ │ └──────┘ └──────┘ └──────┘ └──────┘       │   │
│ │ ← duplicated set for seamless loop →      │   │
│ └────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
```

**Outer container**: `overflow: hidden`, full viewport width, no horizontal scrollbar.
**Inner track**: `display: flex`, contains items twice (original + duplicate for seamless loop).
**Items**: Consistent height, variable or fixed width, separated by gap.

## Tailwind Implementation

```html
<div class="w-full overflow-hidden" aria-label="Our partners" role="marquee">
  <div class="flex animate-marquee">
    <!-- Original set -->
    <div class="flex shrink-0 items-center gap-12 px-6">
      <span class="text-lg font-medium text-zinc-400 whitespace-nowrap">Framer</span>
      <span class="text-lg font-medium text-zinc-400 whitespace-nowrap">Webflow</span>
      <!-- ... more items -->
    </div>
    <!-- Duplicate set (identical content for seamless loop) -->
    <div class="flex shrink-0 items-center gap-12 px-6" aria-hidden="true">
      <span class="text-lg font-medium text-zinc-400 whitespace-nowrap">Framer</span>
      <span class="text-lg font-medium text-zinc-400 whitespace-nowrap">Webflow</span>
      <!-- ... same items -->
    </div>
  </div>
</div>
```

## CSS Animation

```css
@keyframes marquee {
  from { transform: translateX(0); }
  to   { transform: translateX(-50%); }
}

.animate-marquee {
  animation: marquee var(--marquee-duration, 30s) linear infinite;
}
```

**Tailwind config extension**:
```js
extend: {
  animation: {
    marquee: 'marquee var(--marquee-duration, 30s) linear infinite',
  },
  keyframes: {
    marquee: {
      from: { transform: 'translateX(0)' },
      to:   { transform: 'translateX(-50%)' },
    },
  },
}
```

## Variants

| Variant | Modification |
|---------|-------------|
| Reverse direction | `animation-direction: reverse` or `translateX(50%)` → `translateX(0)` |
| Scroll-reactive reverse | Swap `animation-direction` on scroll event (see creative-arsenal.md Kinetic Marquee) |
| Pause on hover | `.group:hover .animate-marquee { animation-play-state: paused }` |
| Logo images | Replace `<span>` with `<img>` — set `h-8` or similar, `w-auto`, `object-contain` |
| Dual-row | Stack two marquee containers, second with `animation-direction: reverse` |
| Gradient fade edges | Overlay `pointer-events-none` pseudo-elements with `bg-gradient-to-r from-background via-transparent to-background` on the outer container |

## Speed & Responsiveness

| Content volume | Duration | Viewport feel |
|---------------|----------|---------------|
| 5–10 items | 15–20s | Brisk but readable |
| 15–25 items | 25–35s | Measured, editorial |
| 30+ items (Contra-scale) | 40–60s | Slow, cinematic |

For responsive speed, set the custom property via media queries:
```css
:root { --marquee-duration: 30s; }
@media (min-width: 768px)  { :root { --marquee-duration: 25s; } }
@media (min-width: 1280px) { :root { --marquee-duration: 20s; } }
```

## Accessibility

- Outer container: `role="marquee"` + `aria-label="Our partners"` (or contextual label)
- Duplicate set: `aria-hidden="true"` (screen readers should only read items once)
- `prefers-reduced-motion: reduce` → stop animation entirely:
  ```css
  @media (prefers-reduced-motion: reduce) {
    .animate-marquee {
      animation: none;
    }
  }
  ```
- Content should remain visible and scrollable without animation (flex wrapping or static display as fallback)

## Edge Cases

- **Very few items** (< 5): items may not fill the viewport. Either duplicate more than once, or set `min-width: 200vw` on the track to ensure continuous loop.
- **Mixed-width items**: works naturally with flex. Gap handles spacing. No fixed widths needed.
- **SSR/no-JS**: animation is CSS-only, works without JavaScript. Content visible by default.
- **Mobile**: reduce gap (`gap-6` instead of `gap-12`), optionally reduce font size. Speed stays the same or slightly slower for readability.
