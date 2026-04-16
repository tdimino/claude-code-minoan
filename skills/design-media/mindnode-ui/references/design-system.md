# MindNode-Inspired Design System

Reference for building mind-map UIs with MindNode's Apple-native aesthetic adapted for React + Tailwind CSS 3 + CSS custom properties.

---

## Color Palette

### Brand Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--mn-purple` | `#6C63FF` | Primary accent, CTA buttons, active nav, links |
| `--mn-purple-hover` | `#5A52E0` | Button hover state |
| `--mn-purple-light` | `#E8E6FF` | Purple tint backgrounds, selected states |
| `--mn-navy` | `#1A1A3E` | Dark sections, footer, hero wave backgrounds |
| `--mn-navy-mid` | `#2D2D5E` | Dark section secondary |

### Neutral Scale

| Token | Hex | Usage |
|-------|-----|-------|
| `--mn-white` | `#FFFFFF` | Page background, card backgrounds |
| `--mn-gray-50` | `#F8F8FC` | Subtle section alternation, input backgrounds |
| `--mn-gray-100` | `#F0F0F5` | Borders, dividers, sidebar backgrounds |
| `--mn-gray-200` | `#E2E2EA` | Card borders, inactive states |
| `--mn-gray-400` | `#9898AD` | Placeholder text, muted icons |
| `--mn-gray-600` | `#5C5C7A` | Secondary text, descriptions |
| `--mn-gray-900` | `#1A1A2E` | Primary text, headings |

### Illustration / Accent Pastels

Used for section differentiation, node level colors, and decorative elements (inspired by MindNode's hero illustrations and mind map branch colors).

| Token | Hex | Usage |
|-------|-----|-------|
| `--mn-coral` | `#FF6B6B` | Warm accent, error states, branch color |
| `--mn-peach` | `#FFAB91` | Illustration accent, branch color |
| `--mn-orange` | `#FFB74D` | Warm mid-tone, badge accent |
| `--mn-mint` | `#81E6D9` | Cool accent, success states, branch color |
| `--mn-green` | `#68D391` | Positive states, task complete |
| `--mn-sky` | `#63B3ED` | Info states, link accent, branch color |
| `--mn-lavender` | `#B794F6` | Tertiary accent, branch color |
| `--mn-pink` | `#F687B3` | Decorative, branch color |
| `--mn-yellow` | `#F6E05E` | Highlight, attention, branch color |
| `--mn-teal` | `#4FD1C5` | Cool accent variant, branch color |

### CSS Custom Property Definitions

```css
:root {
  /* Brand */
  --mn-purple: #6C63FF;
  --mn-purple-hover: #5A52E0;
  --mn-purple-light: #E8E6FF;
  --mn-navy: #1A1A3E;
  --mn-navy-mid: #2D2D5E;

  /* Neutrals */
  --mn-white: #FFFFFF;
  --mn-gray-50: #F8F8FC;
  --mn-gray-100: #F0F0F5;
  --mn-gray-200: #E2E2EA;
  --mn-gray-400: #9898AD;
  --mn-gray-600: #5C5C7A;
  --mn-gray-900: #1A1A2E;

  /* Pastels */
  --mn-coral: #FF6B6B;
  --mn-peach: #FFAB91;
  --mn-orange: #FFB74D;
  --mn-mint: #81E6D9;
  --mn-green: #68D391;
  --mn-sky: #63B3ED;
  --mn-lavender: #B794F6;
  --mn-pink: #F687B3;
  --mn-yellow: #F6E05E;
  --mn-teal: #4FD1C5;

  /* Semantic */
  --mn-bg-primary: var(--mn-white);
  --mn-bg-secondary: var(--mn-gray-50);
  --mn-bg-dark: var(--mn-navy);
  --mn-text-primary: var(--mn-gray-900);
  --mn-text-secondary: var(--mn-gray-600);
  --mn-text-muted: var(--mn-gray-400);
  --mn-border: var(--mn-gray-200);
  --mn-accent: var(--mn-purple);
  --mn-accent-hover: var(--mn-purple-hover);

  /* Canvas */
  --mn-canvas-bg: var(--mn-white);
  --mn-node-shadow: 0 2px 8px rgba(26, 26, 62, 0.08);
  --mn-node-shadow-hover: 0 4px 16px rgba(26, 26, 62, 0.12);

  /* Radii */
  --mn-radius-sm: 6px;
  --mn-radius-md: 10px;
  --mn-radius-lg: 16px;
  --mn-radius-xl: 24px;
  --mn-radius-pill: 9999px;

  /* Spacing scale */
  --mn-space-xs: 4px;
  --mn-space-sm: 8px;
  --mn-space-md: 16px;
  --mn-space-lg: 24px;
  --mn-space-xl: 32px;
  --mn-space-2xl: 48px;
  --mn-space-3xl: 64px;

  /* Transitions */
  --mn-transition-fast: 150ms ease;
  --mn-transition-normal: 250ms ease;
  --mn-transition-slow: 400ms ease;
}
```

### Tailwind CSS Extension

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        mn: {
          purple: 'var(--mn-purple)',
          'purple-hover': 'var(--mn-purple-hover)',
          'purple-light': 'var(--mn-purple-light)',
          navy: 'var(--mn-navy)',
          'navy-mid': 'var(--mn-navy-mid)',
          coral: 'var(--mn-coral)',
          peach: 'var(--mn-peach)',
          orange: 'var(--mn-orange)',
          mint: 'var(--mn-mint)',
          green: 'var(--mn-green)',
          sky: 'var(--mn-sky)',
          lavender: 'var(--mn-lavender)',
          pink: 'var(--mn-pink)',
          yellow: 'var(--mn-yellow)',
          teal: 'var(--mn-teal)',
        },
      },
      borderRadius: {
        mn: 'var(--mn-radius-md)',
        'mn-lg': 'var(--mn-radius-lg)',
        'mn-xl': 'var(--mn-radius-xl)',
      },
      boxShadow: {
        'mn-node': 'var(--mn-node-shadow)',
        'mn-node-hover': 'var(--mn-node-shadow-hover)',
      },
    },
  },
};
```

---

## Typography

### Font Stack

MindNode uses a clean, rounded sans-serif typeface. For web, map this to the SF Pro / system stack with Inter as the cross-platform fallback.

```css
:root {
  --mn-font-sans: 'Inter', -apple-system, BlinkMacSystemFont,
    'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
  --mn-font-mono: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
}
```

### Type Scale

| Level | Size | Weight | Line-Height | Letter-Spacing | Usage |
|-------|------|--------|-------------|----------------|-------|
| Display | 48px / 3rem | 800 | 1.1 | -0.02em | Hero headlines |
| H1 | 36px / 2.25rem | 700 | 1.2 | -0.015em | Page titles |
| H2 | 28px / 1.75rem | 700 | 1.25 | -0.01em | Section titles |
| H3 | 22px / 1.375rem | 600 | 1.3 | -0.005em | Card titles, sub-sections |
| H4 | 18px / 1.125rem | 600 | 1.4 | 0 | Node labels (root level) |
| Body | 16px / 1rem | 400 | 1.6 | 0 | Paragraph text, descriptions |
| Body Small | 14px / 0.875rem | 400 | 1.5 | 0 | Secondary text, metadata |
| Caption | 12px / 0.75rem | 500 | 1.4 | 0.01em | Badges, tags, timestamps |
| Node Text | 14px / 0.875rem | 500 | 1.4 | 0 | Mind map node content |

### Typography CSS

```css
.mn-display { font-size: 3rem; font-weight: 800; line-height: 1.1; letter-spacing: -0.02em; }
.mn-h1 { font-size: 2.25rem; font-weight: 700; line-height: 1.2; letter-spacing: -0.015em; }
.mn-h2 { font-size: 1.75rem; font-weight: 700; line-height: 1.25; letter-spacing: -0.01em; }
.mn-h3 { font-size: 1.375rem; font-weight: 600; line-height: 1.3; letter-spacing: -0.005em; }
.mn-h4 { font-size: 1.125rem; font-weight: 600; line-height: 1.4; }
.mn-body { font-size: 1rem; font-weight: 400; line-height: 1.6; }
.mn-body-sm { font-size: 0.875rem; font-weight: 400; line-height: 1.5; }
.mn-caption { font-size: 0.75rem; font-weight: 500; line-height: 1.4; letter-spacing: 0.01em; }
```

---

## Visual Language Principles

### 1. Rounded Everything

All interactive and container elements use generous border-radius. Sharp corners appear only in code blocks and data tables.

- Buttons: `border-radius: var(--mn-radius-pill)` (fully rounded)
- Cards: `border-radius: var(--mn-radius-lg)` (16px)
- Node shapes: `border-radius: var(--mn-radius-md)` to `var(--mn-radius-pill)` depending on node type
- Inputs: `border-radius: var(--mn-radius-md)` (10px)
- Badges/Tags: `border-radius: var(--mn-radius-pill)` (fully rounded)

### 2. Generous Whitespace

MindNode breathes. Preserve ample spacing between sections and within components.

- Section padding: `py-16` to `py-24` (64px-96px vertical)
- Card padding: `p-6` (24px)
- Element spacing within cards: `space-y-3` to `space-y-4`
- Page max-width: `max-w-6xl` (1152px) centered
- Canvas area: full viewport width/height, no max-width constraint

### 3. Soft Shadows and Elevation

Shadows are subtle, cool-toned, and never harsh. Two elevation levels for most UI:

```css
/* Resting */
box-shadow: 0 2px 8px rgba(26, 26, 62, 0.08);

/* Hover / Active */
box-shadow: 0 4px 16px rgba(26, 26, 62, 0.12);

/* Floating (dropdowns, popovers) */
box-shadow: 0 8px 32px rgba(26, 26, 62, 0.16);
```

### 4. Smooth Transitions

Every interactive state change animates. Use `ease` timing with short durations.

```css
/* Default interactive transition */
transition: all var(--mn-transition-fast);

/* Layout/position changes */
transition: transform var(--mn-transition-normal);

/* Theme/color changes */
transition: background-color var(--mn-transition-slow),
            color var(--mn-transition-slow),
            border-color var(--mn-transition-slow);
```

### 5. Single CTA Focus

Each section/view has one primary action. Avoid competing CTAs. Hierarchy:

1. **Primary** (filled purple pill): One per view/section
2. **Secondary** (outlined or ghost): Supporting actions
3. **Tertiary** (text-only link): Navigation, less important

### 6. Illustration Style

MindNode's illustrations are soft, warm, slightly abstract geometric scenes with pastel fills and subtle gradients. When implementing decorative elements:

- Use SVG with pastel fills (coral, mint, sky, peach)
- Rounded geometric shapes (clouds, hills, organic waves)
- No hard edges or photorealistic imagery
- The wave divider between sections (white-to-navy transition) is characteristic

---

## Component Patterns

### Primary Button (CTA)

```tsx
function PrimaryButton({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className="rounded-full bg-mn-purple px-6 py-2.5 text-sm font-semibold text-white
                 transition-all duration-150 ease-in-out
                 hover:bg-mn-purple-hover hover:shadow-mn-node-hover
                 active:scale-[0.98]
                 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mn-purple focus-visible:ring-offset-2"
      {...props}
    >
      {children}
    </button>
  );
}
```

### Secondary Button

```tsx
function SecondaryButton({ children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      className="rounded-full border border-[var(--mn-border)] bg-white px-5 py-2 text-sm
                 font-medium text-[var(--mn-text-primary)]
                 transition-all duration-150
                 hover:border-mn-purple hover:text-mn-purple hover:shadow-mn-node"
      {...props}
    >
      {children}
    </button>
  );
}
```

### Card

```tsx
function Card({ children, className = '' }: { children: React.ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-[var(--mn-radius-lg)] border border-[var(--mn-border)]
                  bg-white p-6 shadow-mn-node
                  transition-shadow duration-150
                  hover:shadow-mn-node-hover
                  ${className}`}
    >
      {children}
    </div>
  );
}
```

### Badge / Tag

```tsx
function Badge({
  label,
  color = 'var(--mn-purple)',
}: {
  label: string;
  color?: string;
}) {
  return (
    <span
      className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
      style={{
        backgroundColor: `color-mix(in srgb, ${color} 15%, transparent)`,
        color,
      }}
    >
      {label}
    </span>
  );
}
```

### Navigation Bar

```tsx
function NavBar() {
  return (
    <nav className="sticky top-0 z-50 flex items-center justify-between border-b border-[var(--mn-border)]
                    bg-white/80 px-6 py-3 backdrop-blur-md">
      <div className="flex items-center gap-2">
        {/* Logo */}
        <span className="text-lg font-bold text-mn-purple">MindMap</span>
      </div>
      <div className="flex items-center gap-8">
        <a className="text-sm font-medium text-[var(--mn-text-primary)] hover:text-mn-purple transition-colors">
          Features
        </a>
        <a className="text-sm font-medium text-[var(--mn-text-primary)] hover:text-mn-purple transition-colors">
          Themes
        </a>
        <a className="text-sm font-medium text-[var(--mn-text-primary)] hover:text-mn-purple transition-colors">
          Support
        </a>
        <PrimaryButton>Download</PrimaryButton>
      </div>
    </nav>
  );
}
```

### Wave Section Divider

The signature visual of MindNode's marketing: a smooth SVG wave transitioning from light to dark sections.

```tsx
function WaveDivider() {
  return (
    <div className="relative -mb-1">
      <svg
        viewBox="0 0 1440 120"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full"
        preserveAspectRatio="none"
      >
        <path
          d="M0 120V60C240 0 480 0 720 40C960 80 1200 80 1440 40V120H0Z"
          fill="var(--mn-navy)"
        />
      </svg>
    </div>
  );
}
```

---

## Dark Mode Adaptation

Use CSS custom properties to flip the palette. MindNode uses deep navy (not pure black) for dark backgrounds.

```css
[data-theme='dark'] {
  --mn-bg-primary: #1A1A3E;
  --mn-bg-secondary: #232350;
  --mn-bg-dark: #12122A;
  --mn-text-primary: #F0F0F5;
  --mn-text-secondary: #9898AD;
  --mn-text-muted: #6C6C8A;
  --mn-border: #3A3A5E;
  --mn-canvas-bg: #1A1A3E;
  --mn-node-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  --mn-node-shadow-hover: 0 4px 16px rgba(0, 0, 0, 0.4);

  /* Pastels stay vibrant but slightly desaturated in dark mode */
  --mn-purple: #7B73FF;
  --mn-purple-hover: #8C85FF;
  --mn-purple-light: #2A2860;
}
```

---

## Accessibility Checklist

- Maintain WCAG 2.1 AA contrast ratios (4.5:1 body text, 3:1 large text)
- All interactive elements must have visible focus indicators (ring-2 purple)
- Color-only distinctions must have secondary visual cues (shape, icon, text label)
- Reduced-motion media query: disable transition animations

```css
@media (prefers-reduced-motion: reduce) {
  * {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
  }
}
```

---

## Project-Pilot Integration

Map design tokens to project-pilot's existing CSS custom property namespace. Maintain backward compatibility by aliasing:

```css
:root {
  /* project-pilot aliases */
  --pp-accent: var(--mn-purple);
  --pp-accent-hover: var(--mn-purple-hover);
  --pp-bg: var(--mn-bg-primary);
  --pp-bg-secondary: var(--mn-bg-secondary);
  --pp-text: var(--mn-text-primary);
  --pp-text-muted: var(--mn-text-secondary);
  --pp-border: var(--mn-border);
  --pp-radius: var(--mn-radius-md);
}
```
