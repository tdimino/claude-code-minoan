# Design System Checklist

Concrete values for accessibility, responsive patterns, spacing, component states, animation timing, design tokens, and testing. Complements `vercel-web-interface-guidelines.md`.

---

## 1. Accessibility

### Contrast Ratios (WCAG 2.2 AA — current legal standard)

| Element | Minimum |
|---------|---------|
| Normal text (<18pt / <14pt bold) | **4.5:1** |
| Large text (≥18pt / ≥14pt bold) | **3:1** |
| UI components, borders, icons | **3:1** |
| Focus indicators | **3:1** between focused/unfocused states |

### APCA (WCAG 3 candidate — use alongside WCAG 2 for better perceptual accuracy)

| Use case | Min Lc | Preferred Lc |
|----------|--------|-------------|
| Body text (14–16px, 400wt) | Lc 75 | Lc 90 |
| Headlines (24px+, 700wt) | Lc 60 | Lc 75 |
| UI elements (icons, borders) | Lc 45 | Lc 60 |
| Placeholder / disabled text | Lc 30 | Lc 45 |

APCA is polarity-aware (dark-on-light ≠ light-on-dark) and font-size/weight-aware. More accurate than WCAG 2 for dark mode, thin fonts, and colored backgrounds.

### Touch Targets

- **WCAG 2.2 AA**: 24×24 CSS px minimum (or equivalent spacing)
- **Apple HIG / AAA target**: 44×44 CSS px
- **Adjacent target spacing**: ≥8px gap
- Expand small icons to 44×44 via padding or `::before` pseudo-element

### WCAG 2.2 New Criteria (beyond 2.1)

| Criterion | Key requirement |
|-----------|----------------|
| Focus Not Obscured (2.4.11) | Focused element not entirely hidden by sticky headers/footers |
| Focus Appearance (2.4.13) | ≥2px perimeter, 3:1 contrast change |
| Dragging Movements (2.5.7) | Non-dragging alternative for all drag interactions |
| Target Size Minimum (2.5.8) | 24×24 CSS px or sufficient spacing |
| Accessible Auth (3.3.8) | No cognitive tests; allow paste + password managers |
| Redundant Entry (3.3.7) | Auto-populate previously entered data in multi-step flows |
| Consistent Help (3.2.6) | Help mechanism in same position on every page |

### Focus Ring

```css
*:focus-visible {
  outline: 3px solid var(--color-focus-ring, #005fcc);
  outline-offset: 2px;
}
```

Use `:focus-visible` (keyboard/AT only), not `:focus` (fires on mouse click too).

---

## 2. Responsive Patterns

### Breakpoints (Tailwind v4 defaults)

| Prefix | Width | Target |
|--------|-------|--------|
| (base) | 0px | Mobile-first |
| `sm` | 640px | Large phones |
| `md` | 768px | Tablets (universal consensus) |
| `lg` | 1024px | Laptops / sidebar collapse point |
| `xl` | 1280px | Desktops |
| `2xl` | 1536px | Large desktops |

Add `--breakpoint-3xl: 120rem` (1920px) for ultra-wide. 375px is a design target, not a breakpoint.

### Layout Transformations

| Pattern | Mobile (base) | Desktop (lg+) |
|---------|--------------|---------------|
| Grid | `grid-cols-1` | `grid-cols-3` |
| Sidebar | Off-screen drawer (`-translate-x-full`) | Static (`lg:static`) |
| Nav | Hamburger (`md:hidden`) | Horizontal (`hidden md:flex`) |
| Images | Scale (`w-full object-cover`) | Art direction (`<picture>`) |
| Tables | Card layout or simplified list | Full columns |

### Typography Scaling

| Element | Mobile | Tablet (md) | Desktop (lg+) |
|---------|--------|-------------|----------------|
| H1 | 30px (`text-3xl`) | 36px (`text-4xl`) | 48–60px |
| H2 | 24px (`text-2xl`) | 30px (`text-3xl`) | 36px |
| Body | 16px (`text-base`) | 16–18px | 16–18px |
| Small | 12px (`text-xs`) | 14px (`text-sm`) | 14px |

### Container Queries vs Media Queries

- **Components** (cards, widgets): container queries (`@container`, `@md`)
- **Page layout** (nav, sidebar, grid): media queries
- Container size queries: 97%+ browser support. Style queries: Chrome-only.

---

## 3. Spacing System (8px grid)

Tailwind v4 base: `--spacing: 0.25rem` (4px). The 8px grid uses every even step.

| Token | Value | Usage |
|-------|-------|-------|
| `p-1` | 4px | Dense UI: icon padding, badges |
| `p-2` | 8px | Minimum spacing, icon gaps |
| `p-3` | 12px | Compact card/button padding |
| `p-4` | 16px | **Standard**: cards, inputs, modals |
| `p-6` | 24px | Section spacing, form groups |
| `p-8` | 32px | Section padding, page margins (tablet) |
| `p-12` | 48px | Hero padding, vertical rhythm |
| `p-16` | 64px | Major section dividers |
| `p-24` | 96px | Full-page section spacing |

Page margins: `px-4 md:px-6 lg:px-8 xl:px-16`

---

## 4. Component States

### State List

| State | Visual | Cursor | ARIA |
|-------|--------|--------|------|
| Default | Base colors | `pointer` | Semantic role |
| Hover | Background shift, elevation | `pointer` | None (visual-only) |
| Active | Darker bg, scale(0.98) | `pointer` | `aria-pressed` (toggles) |
| Focus | Focus ring (see §1) | unchanged | `:focus-visible` |
| Disabled | 40–50% opacity | `not-allowed` | `aria-disabled="true"` |
| Loading | Skeleton/spinner/progress | `wait` | `aria-busy="true"` |
| Error | Red border, icon, message | `default` | `aria-invalid`, `aria-describedby` |
| Empty | Illustration + headline + CTA | `default` | Descriptive text |
| Success | Green indicator, check icon | `default` | `role="status"` |

### Key Rules

- **Disabled is a dead end** — nothing transitions to/from disabled except prop changes
- **Loading blocks interaction** — only system events trigger transitions
- **Hover + Focus coexist** — show both focus ring and hover background
- **Error is recoverable** — always provide retry or correction path

### Loading Indicators

| Duration | Indicator |
|----------|-----------|
| <1s | None |
| 1–3s, known layout | Skeleton screen |
| 1–3s, unknown layout | Spinner (16–24px inline, 32–48px page) |
| 3–10s, measurable | Progress bar with `role="progressbar"` |
| 10s+ | Progress bar + status text |

---

## 5. Design Tokens

### Color (OKLCH, shadcn/ui pattern)

Semantic tokens as CSS variables: `--primary`, `--secondary`, `--muted`, `--accent`, `--destructive`, `--card`, `--popover`, `--border`, `--input`, `--ring`. Each with `-foreground` pair.

Dark mode: `color-scheme: dark` on `<html>`, remap semantic tokens. Radix 12-step scale: steps 1–3 backgrounds, 4–6 borders, 7–8 high-contrast bg, 9–10 solids, 11–12 text.

### Typography (Major Third scale — 1.25 ratio)

| Role | Size | Weight | Line-height |
|------|------|--------|-------------|
| Display | 61px (3.815rem) | 700 | 1.1 |
| H1 | 49px (3.052rem) | 700 | 1.15 |
| H2 | 39px (2.441rem) | 600 | 1.2 |
| H3 | 31px (1.953rem) | 600 | 1.25 |
| H4 | 25px (1.563rem) | 600 | 1.3 |
| Body | 16px (1rem) | 400 | 1.5 |
| Small | 13px (0.8rem) | 400 | 1.5 |
| Caption | 10px (0.64rem) | 400 | 1.625 |

### Shadows (3 levels minimum)

| Level | CSS | Usage |
|-------|-----|-------|
| sm | `0 1px 2px oklch(0 0 0 / 0.05)` | Inputs, cards at rest |
| md | `0 4px 6px -1px oklch(0 0 0 / 0.1), 0 2px 4px -2px oklch(0 0 0 / 0.1)` | Cards on hover, dropdowns |
| lg | `0 10px 15px -3px oklch(0 0 0 / 0.1), 0 4px 6px -4px oklch(0 0 0 / 0.1)` | Modals, popovers |

### Border Radius

Base: `--radius: 0.625rem` (10px). Derive: `sm` = `calc(var(--radius) - 4px)`, `md` = `calc(var(--radius) - 2px)`, `lg` = `var(--radius)`, `full` = `9999px`.

### Export Formats

- **Primary**: CSS custom properties (consumed directly by components)
- **Tooling**: DTCG JSON (`$type`, `$value`, `$description`) for design tool interop
- **Utilities**: Tailwind `@theme` generates utility classes from CSS variables

---

## 6. Animation Timing

### Easing Curves

| Name | Value | Use |
|------|-------|-----|
| ease-out | `cubic-bezier(0.33, 1, 0.68, 1)` | Most UI transitions |
| ease-out-expo | `cubic-bezier(0.16, 1, 0.3, 1)` | Page load, reveals (Linear's signature) |
| ease-in-expo | `cubic-bezier(0.7, 0, 0.84, 0)` | Exit animations |
| ease-in-out | `cubic-bezier(0.65, 0, 0.35, 1)` | Page transitions |
| spring | `cubic-bezier(0.68, -0.55, 0.27, 1.55)` | Playful interactions |

### Duration Per Interaction

| Interaction | Duration | Easing | Notes |
|-------------|----------|--------|-------|
| Hover | 150ms | ease-out | Never `transition: all` |
| Active/press | 50–100ms | ease-out | Must feel instant |
| Modal open | 250ms | ease-out-expo | Close: 150ms ease-in-expo |
| Page load stagger | 75ms/element | ease-out-expo | Cap total at 600ms |
| Page transition | 300–500ms | ease-in-out | translateX(16px) entrance |
| Scroll reveal | 600ms | ease-out-expo | IntersectionObserver threshold 0.15 |

### Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Hierarchy

CSS transitions > Web Animations API > JS libraries. Animate only `transform` and `opacity` (compositor-friendly). Never auto-play decorative animations.

---

## 7. Testing

### Automated

| Tool | Scope | What it catches |
|------|-------|----------------|
| axe-core (jest-axe) | Component | ARIA, contrast, labels (~30–50% of issues) |
| Playwright + @axe-core/playwright | Page | Keyboard nav, live regions, focus management |
| Chromatic | Storybook | Visual regression per component per state |
| Playwright `toHaveScreenshot()` | Page | Layout regression across breakpoints |

### Responsive Test Breakpoints

Must test: **375px**, **768px**, **1440px**, **1920px**

### Manual Testing (supplement automated)

- Keyboard: Tab, Shift+Tab, Enter, Space, Escape, Arrow keys
- Screen reader: VoiceOver (Mac), NVDA (Windows)
- Color: high-contrast mode, `prefers-color-scheme`
- Motion: `prefers-reduced-motion` verification
