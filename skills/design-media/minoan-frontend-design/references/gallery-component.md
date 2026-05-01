# Gallery Component

Horizontal scroll showcase for work samples, screenshots, creative outputs, and mixed-media collections. Handles mixed aspect ratios, snap scrolling, and optional lightbox interaction.

---

## Anatomy

```
┌──────────────────────────────────────────────────────┐
│ overflow-x: auto, scroll-snap-type: x mandatory      │
│ ┌─────────┐ ┌───────────────┐ ┌─────────┐ ┌─────┐  │
│ │ 4:3     │ │ 16:9          │ │ 4:3     │ │ 1:1 │  │
│ │ tall    │ │ wide          │ │ tall    │ │     │  │
│ │         │ │               │ │         │ │     │  │
│ └─────────┘ └───────────────┘ └─────────┘ └─────┘  │
│ ← drag or swipe to scroll →                         │
│ ● ○ ○ ○  (optional dot indicators)                  │
└──────────────────────────────────────────────────────┘
```

**Container**: `overflow-x: auto`, `scroll-snap-type: x mandatory`, horizontal flex or grid.
**Items**: Fixed height (constraint), variable width based on aspect ratio. `scroll-snap-align: start`.
**Indicators**: Optional dot row or progress bar below.

## Tailwind Implementation

### Horizontal Scroll Gallery (Mixed Sizes)

```html
<div class="relative">
  <div
    class="flex gap-4 overflow-x-auto scroll-smooth snap-x snap-mandatory
           pb-4 -mx-4 px-4 scrollbar-hide"
    role="region"
    aria-label="Work showcase"
    tabindex="0"
  >
    <!-- Large item (landscape) -->
    <div class="snap-start shrink-0 w-[560px] h-[420px] rounded-xl overflow-hidden">
      <img src="..." alt="..." class="w-full h-full object-cover" loading="lazy" />
    </div>

    <!-- Small item (portrait) -->
    <div class="snap-start shrink-0 w-[280px] h-[420px] rounded-xl overflow-hidden">
      <img src="..." alt="..." class="w-full h-full object-cover" loading="lazy" />
    </div>

    <!-- Square item -->
    <div class="snap-start shrink-0 w-[420px] h-[420px] rounded-xl overflow-hidden">
      <img src="..." alt="..." class="w-full h-full object-cover" loading="lazy" />
    </div>

    <!-- More items... -->
  </div>
</div>
```

### Scrollbar Hide Utility

```css
.scrollbar-hide {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-hide::-webkit-scrollbar {
  display: none;
}
```

## Variants

| Variant | Implementation |
|---------|---------------|
| Fixed-height, variable-width | Set `h-[420px]` on all items, `w-auto` on images. Width derives from aspect ratio. |
| Uniform grid | Replace flex with `grid-auto-columns: minmax(300px, 1fr)` + `grid-auto-flow: column` |
| Masonry (vertical) | `columns: 3` + `break-inside: avoid` (see creative-arsenal.md) |
| Lightbox on click | Wrap each image in a `<button>` or `<a>`, open in shadcn `Dialog` or custom modal |
| Gradient edge fade | `mask-image: linear-gradient(to right, transparent, black 5%, black 95%, transparent)` on container |
| Progress bar | Track `scrollLeft / (scrollWidth - clientWidth)` → update `scaleX` on a bar element |
| Auto-scroll | `setInterval` calling `scrollBy({ left: itemWidth, behavior: 'smooth' })` with pause on hover/focus |

## Scroll Progress Indicator

```html
<div class="h-0.5 bg-zinc-800 rounded-full mt-4">
  <div
    class="h-full bg-zinc-400 rounded-full transition-transform origin-left"
    style="transform: scaleX(var(--scroll-progress, 0))"
  ></div>
</div>
```

```js
const gallery = document.querySelector('[role="region"]');
gallery.addEventListener('scroll', () => {
  const progress = gallery.scrollLeft / (gallery.scrollWidth - gallery.clientWidth);
  gallery.parentElement.style.setProperty('--scroll-progress', progress);
});
```

## Dot Indicators

```html
<div class="flex justify-center gap-2 mt-4" role="group" aria-label="Gallery navigation">
  <button class="w-2 h-2 rounded-full bg-zinc-400" aria-label="Slide 1" aria-current="true"></button>
  <button class="w-2 h-2 rounded-full bg-zinc-700" aria-label="Slide 2"></button>
  <button class="w-2 h-2 rounded-full bg-zinc-700" aria-label="Slide 3"></button>
</div>
```

Track active dot via IntersectionObserver on each gallery item (threshold 0.6).

## Accessibility

- Container: `role="region"` + `aria-label`, `tabindex="0"` for keyboard scrolling
- Arrow key navigation: listen for `ArrowLeft` / `ArrowRight` on focused container, call `scrollBy`
- Images: `alt` text on every image (never empty unless purely decorative)
- `prefers-reduced-motion: reduce` → disable auto-scroll, smooth scrolling
- Touch: native horizontal scroll works on mobile. No custom gesture handlers needed.

## Responsive Behavior

| Breakpoint | Adjustment |
|-----------|------------|
| Desktop (lg+) | Full-size items, 4-5 visible, scroll progress bar |
| Tablet (md) | Slightly smaller items (80% width), 2-3 visible |
| Mobile (sm) | Single item visible, full-width snap, dot indicators preferred |

Edge padding (`-mx-4 px-4`) ensures items peek from off-screen, signaling scrollability.

## Edge Cases

- **Few items** (< 3): disable scroll, center items, hide indicators
- **Single item**: no scroll container needed, render as full-width hero image
- **Loading**: skeleton shimmer placeholders at item dimensions (see creative-arsenal.md Skeleton Shimmer)
- **Broken images**: `object-cover` on a neutral background prevents layout collapse. Add `onerror` handler for fallback.
