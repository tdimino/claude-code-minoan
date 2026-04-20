# Interface Craft Techniques

Implementation details for the polish checklist. Each section provides specific CSS/Tailwind values.

## Surfaces

### Concentric Border Radius

Nested rounded elements: `outerRadius = innerRadius + padding`.

```css
.card { border-radius: 20px; padding: 8px; }   /* 12 + 8 = 20 */
.card-inner { border-radius: 12px; }
```

```tsx
// Tailwind: rounded-2xl p-2 → inner rounded-lg (16 - 8 = 8)
<div className="rounded-2xl p-2">
  <div className="rounded-lg">...</div>
</div>
```

If padding exceeds 24px, treat layers as separate surfaces — strict concentric math stops being useful.

### Shadows Instead of Borders

For cards/buttons/containers that use a border for depth, replace with layered `box-shadow`. Shadows adapt to any background; solid borders don't. Do NOT apply to dividers (`border-b`, `border-t`) — those stay as borders.

```css
:root {
  --shadow-border:
    0px 0px 0px 1px rgba(0, 0, 0, 0.06),
    0px 1px 2px -1px rgba(0, 0, 0, 0.06),
    0px 2px 4px 0px rgba(0, 0, 0, 0.04);
  --shadow-border-hover:
    0px 0px 0px 1px rgba(0, 0, 0, 0.08),
    0px 1px 2px -1px rgba(0, 0, 0, 0.08),
    0px 2px 4px 0px rgba(0, 0, 0, 0.06);
}

/* Dark mode: single white ring */
--shadow-border: 0 0 0 1px rgba(255, 255, 255, 0.08);
--shadow-border-hover: 0 0 0 1px rgba(255, 255, 255, 0.13);
```

Apply with `transition-property: box-shadow; transition-duration: 150ms`.

### Image Outlines

Subtle depth without layout impact:

```tsx
<img className="outline outline-1 -outline-offset-1 outline-black/10 dark:outline-white/10" />
```

Pure black in light mode, pure white in dark mode — never tinted neutrals (slate, zinc). Tinted outlines pick up surface color and read as dirt.

## Typography

### Text Wrapping

| Scenario | Property | Tailwind |
|----------|----------|----------|
| Headings (even line distribution) | `text-wrap: balance` | `text-balance` |
| Body text (prevent orphans) | `text-wrap: pretty` | `text-pretty` |
| Long text (10+ lines) | Leave default | — |

`balance` only works on blocks of 6 lines or fewer (Chromium). `pretty` works on any length.

### Font Smoothing

Apply once at root — macOS renders heavier without it:

```css
html { -webkit-font-smoothing: antialiased; -moz-osx-font-smoothing: grayscale; }
```

Tailwind: `<html className="antialiased">`.

### Tabular Numbers

Dynamic numbers (counters, prices, timers, table columns) need equal-width digits:

```css
.counter { font-variant-numeric: tabular-nums; }
```

Tailwind: `tabular-nums`. Prevents layout shift as values change.

## Animation

### Transitions vs Keyframes

| | CSS Transitions | CSS Keyframes |
|---|---|---|
| Interruptible | Yes — retargets mid-animation | No — restarts from beginning |
| Use for | Interactive state changes (hover, toggle, drawer) | One-shot sequences (page entrance, loading) |

Always prefer transitions for interactive elements. A drawer that uses keyframes will jank if toggled mid-animation.

### Never transition: all

Specify exact properties. `transition: all` forces the browser to watch everything and causes unexpected animations.

```css
/* Good */
.button { transition-property: scale, background-color; transition-duration: 150ms; }

/* Bad */
.button { transition: all 150ms ease-out; }
```

Tailwind: `transition-transform` (covers transform/translate/scale/rotate). For mixed: `transition-[scale,opacity,filter]`.

### Scale on Press

`scale(0.96)` on `:active` — always 0.96, never below 0.95.

```tsx
<button className="transition-transform duration-150 ease-out active:scale-[0.96]">
```

Add a `static` prop to button components to disable when motion is distracting. Framer Motion: `whileTap={{ scale: 0.96 }}`.

### Staggered Enter/Exit

Split content into semantic chunks (title, description, buttons). Stagger ~100ms per group.

Enter: `opacity: 0→1`, `translateY: 12px→0`, `blur: 4px→0`.
Exit: shorter (150ms vs 300ms), subtle fixed `translateY: -12px` — not full container height.

```css
.stagger-item {
  opacity: 0; transform: translateY(12px); filter: blur(4px);
  animation: fadeInUp 400ms ease-out forwards;
}
.stagger-item:nth-child(1) { animation-delay: 0ms; }
.stagger-item:nth-child(2) { animation-delay: 100ms; }
.stagger-item:nth-child(3) { animation-delay: 200ms; }

@keyframes fadeInUp { to { opacity: 1; transform: translateY(0); filter: blur(0); } }
```

### Icon Cross-Fade (CSS-only)

For toggling icons (play/pause, like/liked) without Framer Motion: keep both in DOM, one absolute-positioned. Cross-fade with `cubic-bezier(0.2, 0, 0, 1)`.

```tsx
<div className="relative">
  <div className={cn(
    "absolute inset-0 flex items-center justify-center",
    "transition-[opacity,filter,scale] duration-300",
    isActive ? "scale-100 opacity-100 blur-0" : "scale-[0.25] opacity-0 blur-[4px]"
  )}>
    <ActiveIcon />
  </div>
  <div className={cn(
    "transition-[opacity,filter,scale] duration-300",
    isActive ? "scale-[0.25] opacity-0 blur-[4px]" : "scale-100 opacity-100 blur-0"
  )}>
    <InactiveIcon />
  </div>
</div>
```

Values: scale `0.25→1`, opacity `0→1`, blur `4px→0`. The non-absolute icon defines layout size.

### Skip Animation on Page Load

Elements in their default state shouldn't animate in on first render.

Framer Motion: `<AnimatePresence initial={false}>` on default-state elements. Don't use on intentional page entrance animations (staggered heroes).

CSS: use class-triggered animations rather than load-triggered keyframes.

## Performance

### will-change

Only for GPU-compositable properties when first-frame stutter is observed:

| Property | GPU-compositable | Worth `will-change` |
|----------|-----------------|---------------------|
| transform | Yes | Yes |
| opacity | Yes | Yes |
| filter (blur, brightness) | Yes | Yes |
| clip-path | Yes | Yes |
| top, left, width, height | No | No |
| background, border, color | No | No |

Never `will-change: all`. Each compositing layer costs memory.

### Hit Area Expansion

Extend small interactive elements to 40-44px minimum with a pseudo-element:

```css
.small-control {
  position: relative;
}
.small-control::after {
  content: "";
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 44px; height: 44px;
}
```

Tailwind: `relative after:absolute after:top-1/2 after:left-1/2 after:size-11 after:-translate-x-1/2 after:-translate-y-1/2`.

Never let two hit areas overlap — shrink if needed but maximize within available space.
