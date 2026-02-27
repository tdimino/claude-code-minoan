# Aldea Slide Deck Design System

Complete design tokens, typography, and styling conventions.

---

## Color Palette

### Canvas Layers (Backgrounds)

| Token | Hex | Usage |
|-------|-----|-------|
| `canvas-900` | `#0a0f1a` | Main slide background |
| `canvas-800` | `#0f1729` | Card backgrounds, secondary areas |
| `canvas-700` | `#141e35` | Highlighted areas, tertiary |
| `canvas-600` | `#1a2744` | Hover states, borders |

### Blueprint Accents

| Token | Hex | Usage |
|-------|-----|-------|
| `blueprint-cyan` | `#00d4ff` | Primary accent, highlights |
| `blueprint-teal` | `#0ea5a0` | Secondary accent |
| `blueprint-accent` | `#22d3ee` | Light cyan, hover states |
| `blueprint-muted` | `#3b5a7a` | Muted blue-gray |
| `blueprint-grid` | `#1e3a5f` | Grid lines, subtle borders |

### Text Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `text-primary` | `#e2e8f0` | Main body text |
| `text-secondary` | `#94a3b8` | Secondary, descriptions |
| `text-muted` | `#64748b` | Labels, metadata |

### Chapter Spectrum (TOC)

| Chapter | Background | Accent |
|---------|------------|--------|
| 01 | `rgba(239,68,68,0.10)` | `#f87171` |
| 02 | `rgba(251,146,60,0.10)` | `#fb923c` |
| 03 | `rgba(250,204,21,0.10)` | `#facc15` |
| 04 | `rgba(163,230,53,0.10)` | `#a3e635` |
| 05 | `rgba(45,212,191,0.10)` | `#2dd4bf` |
| 06 | `rgba(96,165,250,0.10)` | `#60a5fa` |
| 07 | `rgba(167,139,250,0.10)` | `#a78bfa` |
| 08 | `rgba(232,121,249,0.10)` | `#e879f9` |

### Light Mode Chapter Accents (Darkened for Readability)

| Chapter | Dark Accent | Light Accent |
|---------|-----------|-------------|
| 01 | `#f87171` | `#1E3A8A` (blue-800) |
| 02 | `#fbbf24` | `#D97706` (amber-600) |
| 03 | `#22d3ee` | `#0891B2` (cyan-600) |
| 04 | `#fb7185` | `#78350F` (amber-900) |
| 05 | `#34d399` | `#059669` (emerald-600) |
| 06 | `#a78bfa` | `#7C3AED` (violet-600) |

---

## Light Mode Color Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `canvas-900` | `#FAFBFC` | Main slide background |
| `canvas-800` | `#F1F3F5` | Card backgrounds, secondary areas |
| `canvas-700` | `#E8ECF0` | Highlighted areas, tertiary |
| `text-primary` | `#1A1D23` | Main body text (near-black) |
| `text-secondary` | `#4A5568` | Secondary, descriptions |
| `text-muted` | `#8896A6` | Labels, metadata |
| `blueprint-cyan` | `#0891B2` | Primary accent (darkened for light bg) |
| `blueprint-teal` | `#0D9488` | Secondary accent |
| `blueprint-grid` | `#C4CFD9` | Grid lines, subtle borders |
| `grid-lines` | `rgba(100,130,170,0.08)` | Blueprint grid |
| `fine-grid` | `rgba(100,130,170,0.04)` | Fine grid overlay |
| `code-block-bg` | `rgba(30,40,60,0.06)` | Code block background |

### Light Mode CSS Variables

```css
:root {
  --canvas-900: #FAFBFC;
  --canvas-800: #F1F3F5;
  --canvas-700: #E8ECF0;
  --blueprint-cyan: #0891B2;
  --blueprint-teal: #0D9488;
  --blueprint-grid: #C4CFD9;
}
```

---

## Card Color Strategy

In grids of 3+ cards, assign distinct accent colors to each card. Colors should match any corresponding StatsBar values below. Use the chapter color for the first/primary card, then complementary colors for others.

### Companion Color Table

| Chapter Color | Companion Colors |
|--------------|-----------------|
| `#1E3A8A` (blue) | `#B45309`, `#92400E` |
| `#D97706` (amber) | `#7C3AED`, `#0891B2`, `#92400E` |
| `#0891B2` (cyan) | `#059669`, `#92400E` |
| `#78350F` (brown) | `#CA8A04`, `#059669`, `#92400E` |
| `#059669` (emerald) | `#1E3A8A`, `#7C3AED` |
| `#7C3AED` (violet) | `#1E3A8A`, `#059669`, `#B45309` |

### Anti-patterns

- Never use `#DC2626` (red-600) or `#E11D48` (rose-600) on light backgrounds — reads as error
- Never use `#fbbf24` (amber-300) on light backgrounds — invisible
- Darken saturated colors to their -700 or -800 variant for light mode

---

## Typography

### Font Stack

```js
// tailwind.config.js
fontFamily: {
  display: ['Playfair Display', 'Georgia', 'serif'],
  body: ['DM Sans', 'system-ui', 'sans-serif'],
  mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
}
```

### Type Scale

| Level | Font | Size | Weight | Class |
|-------|------|------|--------|-------|
| Display | display | 6xl (60px) | semibold | `font-display text-6xl` |
| H1 | display | 4xl (36px) | semibold | `font-display text-4xl` |
| H2 | display | 3xl (30px) | semibold | `font-display text-3xl` |
| H3 | body | sm (14px) | medium | `font-medium text-sm` |
| H4 | mono | xs (12px) | normal | `font-mono text-xs uppercase` |
| Body | body | sm (14px) | normal | `text-sm` |
| Small | body | xs (12px) | normal | `text-xs` |
| Tiny | mono | 10-11px | normal | `text-[10px]` or `text-[11px]` |

### Text Colors

```jsx
// Primary text
<p className="text-text-primary">Main content</p>

// Secondary text
<p className="text-text-secondary">Description</p>

// Muted text
<span className="text-text-muted">Label</span>

// Accent text
<span className="text-blueprint-cyan">Highlight</span>
```

---

## Grid System

### Blueprint Grid (40px)

```css
.blueprint-grid {
  background-image:
    linear-gradient(to right, rgba(30, 58, 95, 0.25) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(30, 58, 95, 0.25) 1px, transparent 1px);
  background-size: 40px 40px;
}
```

### Fine Grid Overlay (10px)

```css
.blueprint-grid-fine {
  background-image:
    linear-gradient(to right, rgba(30, 58, 95, 0.12) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(30, 58, 95, 0.12) 1px, transparent 1px);
  background-size: 10px 10px;
}
```

### Corner Marks

```css
.corner-marks::before,
.corner-marks::after {
  content: '';
  position: absolute;
  width: 20px;
  height: 20px;
  border: 1px solid var(--blueprint-cyan);
  opacity: 0.4;
}

.corner-marks::before {
  top: 24px;
  left: 24px;
  border-right: none;
  border-bottom: none;
}

.corner-marks::after {
  bottom: 24px;
  right: 24px;
  border-left: none;
  border-top: none;
}
```

---

## Spacing Conventions

### Slide Padding

| Area | Class | Value |
|------|-------|-------|
| Horizontal | `px-16` | 64px |
| Top | `pt-16` or `pt-20` | 64-80px |
| Bottom | `pb-10` or `pb-12` | 40-48px |

### Element Gaps

| Context | Class | Value |
|---------|-------|-------|
| Grid items | `gap-3` | 12px |
| Cards | `gap-4` | 16px |
| Sections | `gap-6` | 24px |
| Major areas | `gap-8` | 32px |

### Margins

| Context | Class | Value |
|---------|-------|-------|
| After headings | `mb-4` to `mb-6` | 16-24px |
| Between sections | `mb-8` | 32px |
| Inline spacing | `mr-2` or `mr-3` | 8-12px |

---

## Layout Patterns

### Centered Stack

```jsx
<div className="h-full flex flex-col items-center justify-center gap-6">
  {/* Content */}
</div>
```

### Header + Content

```jsx
<div className="h-full flex flex-col px-16 pt-16 pb-10">
  <h2 className="font-display text-3xl mb-6">Title</h2>
  <div className="flex-1">
    {/* Main content */}
  </div>
</div>
```

### Two-Column Split

```jsx
<div className="h-full flex px-16 pt-20 pb-12 gap-8">
  <div className="flex-1">{/* Left content */}</div>
  <div className="w-80">{/* Right sidebar */}</div>
</div>
```

### Grid Layouts

```jsx
// 3-column
<div className="grid grid-cols-3 gap-3">{/* Items */}</div>

// 2-column
<div className="grid grid-cols-2 gap-8">{/* Items */}</div>

// 4-column
<div className="grid grid-cols-4 gap-4">{/* Items */}</div>
```

---

## Visual Elements

### Cards

```jsx
// Standard card
<div className="p-4 bg-canvas-700/40 border border-blueprint-grid/40 rounded">

// Info box
<div className="p-5 bg-canvas-700/40 border border-blueprint-grid/40 rounded">

// Accent box
<div className="p-6 bg-blueprint-cyan/10 border border-blueprint-cyan/30 rounded-lg">
```

### Dividers

```jsx
// Gradient divider
<div className="h-px bg-gradient-to-r from-transparent via-blueprint-cyan/30 to-transparent" />

// Subtle separator
<div className="border-t border-white/10" />
```

### Bullets

```jsx
// Cyan dot
<span className="w-1.5 h-1.5 bg-blueprint-cyan/60 rounded-full" />

// With list item
<li className="flex items-start gap-2">
  <span className="w-1.5 h-1.5 mt-2 bg-blueprint-cyan/60 rounded-full flex-shrink-0" />
  <span>List item text</span>
</li>
```

### Labels

```jsx
// Tech label
<span className="font-mono text-[10px] text-blueprint-cyan uppercase tracking-wider opacity-70">
  Label
</span>

// Chapter badge
<span className="chapter-badge">01 — CHAPTER</span>
```

---

## Opacity Conventions

| Opacity | Usage |
|---------|-------|
| `/10` | Very subtle backgrounds |
| `/20` | Light borders |
| `/30` | Standard borders |
| `/40` | Card backgrounds |
| `/50` | Medium emphasis |
| `/60` | Standard elements |
| `/80` | High emphasis |
| `/99` | Near-full opacity |

---

## CSS Variables (globals.css)

```css
:root {
  --canvas-900: #0a0f1a;
  --canvas-800: #0f1729;
  --canvas-700: #141e35;
  --canvas-600: #1a2744;

  --blueprint-cyan: #00d4ff;
  --blueprint-teal: #0ea5a0;
  --blueprint-accent: #22d3ee;
  --blueprint-muted: #3b5a7a;
  --blueprint-grid: #1e3a5f;

  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
}
```

---

## Animations

### Keyframes

```css
@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slide-up {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes draw-line {
  from { stroke-dashoffset: 100; }
  to { stroke-dashoffset: 0; }
}
```

### Tailwind Animation Classes

```js
// tailwind.config.js
animation: {
  'fade-in': 'fade-in 0.6s ease-out',
  'slide-up': 'slide-up 0.5s ease-out',
  'draw-line': 'draw-line 1s ease-out',
}
```

### Transitions

```jsx
// Standard transition
<div className="transition-all duration-300 ease-out">

// Hover scale
<div className="hover:scale-[1.01] transition-transform">

// Border color on hover
<div className="hover:border-blueprint-cyan/50 transition-colors">
```

---

## Print Styles

```css
@media print {
  @page {
    size: 1280px 720px;
    margin: 0;
  }

  .slide {
    width: 1280px !important;
    height: 720px !important;
    page-break-after: always;
    page-break-inside: avoid;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  .slide:last-child {
    page-break-after: auto;
  }
}
```
