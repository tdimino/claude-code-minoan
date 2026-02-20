# Vercel Web Interface Guidelines (Distilled)

Reference standard for quality web interfaces, published Sep 2025. Source: vercel.com/design/guidelines

## Interactions

- Keyboard works everywhere (WAI-ARIA patterns)
- `:focus-visible` over `:focus` — avoid distracting pointer users
- Match visual & hit targets (min 24px desktop, 44px mobile)
- Mobile input font >= 16px (prevents iOS auto-zoom)
- Loading buttons: show spinner + keep original label
- Min loading-state duration: 150-300ms show-delay, 300-500ms minimum visible
- URL as state — persist in URL so share/refresh/Back work (nuqs library recommended)
- Optimistic updates: update UI immediately, reconcile on server response
- Ellipsis for further input ("Rename...") and loading states ("Saving...")
- Confirm destructive actions
- Tooltip timing: delay first, no delay for subsequent peers
- Autofocus on desktop for single primary input
- Deep-link everything: filters, tabs, pagination, expanded panels
- `inert` attribute during drag operations
- Locale-aware keyboard shortcuts for non-QWERTY layouts

## Animations

- Honor `prefers-reduced-motion` — mandatory
- Implementation preference: CSS > Web Animations API > JS libraries
- Compositor-friendly: GPU-accelerated (`transform`, `opacity`) over reflow triggers (`width`, `height`, `top`, `left`)
- Only animate when it clarifies cause & effect or adds deliberate delight
- Easing fits the subject — spring for natural, sharp for decisive
- Interruptible by user input — always
- Input-driven (avoid autoplay)
- Never `transition: all` — explicitly list animated properties

## Layout

- Optical alignment: adjust +/-1px when perception beats geometry
- Deliberate alignment: every element aligns with something intentionally
- Balance contrast in lockups (text + icons side by side)
- Responsive: mobile, laptop, ultra-wide
- No excessive scrollbars
- Let the browser size things (flex/grid/intrinsic over JS measurement)

## Content

- Inline help first, tooltips as last resort
- Stable skeletons that mirror final content layout
- All states designed: empty, sparse, dense, error
- Typographic (curly) quotes
- Tabular numbers for comparisons
- Redundant status cues — never color alone
- Icons have labels
- Use the ellipsis character (…), not three periods (...)

## Forms

- Enter submits (single control); Cmd+Enter in textarea
- Labels everywhere
- Don't pre-disable submit — allow submitting incomplete forms to surface validation
- Don't block typing — allow any input, show validation feedback
- Error placement next to fields; focus first error on submit
- Placeholders signal emptiness (end with ellipsis)
- Warn before navigation when unsaved changes
- Idempotency keys on form submission
- Windows `<select>` needs explicit `background-color` and `color` for dark mode

## Design Craft

- Layered shadows: ambient + direct light, at least two layers
- Crisp borders: combine borders & shadows; semi-transparent borders
- Nested radii: child radius <= parent radius, concentric
- Hue consistency: tint borders/shadows/text toward same hue on non-neutral backgrounds
- APCA over WCAG 2 for contrast measurement
- Interactions increase contrast: hover/active/focus > rest state
- Browser `theme-color` meta matches page background
- `color-scheme: dark` on `<html>` for proper scrollbar contrast
- Never gradient banding — use background images over CSS masks for dark fades

## Performance

- Network latency budgets: `POST/PATCH/DELETE` < 500ms
- Virtualize large lists (`virtua` or `content-visibility: auto`)
- Prefer uncontrolled inputs; make controlled loops cheap
- Move expensive work to Web Workers

## Copywriting

- Active voice
- Title Case for headings/buttons (Chicago style)
- Prefer `&` over `and`
- Action-oriented language
- Second person, not first
- Numerals for counts
- Error messages guide the exit: "Your API key is incorrect. Generate a new key in account settings."

## Color System (Geist)

- 10 semantic color scales, P3 on supported browsers
- Colors 1-3: Component backgrounds (default, hover, active)
- Colors 4-6: Borders (default, hover, active)
- Colors 7-8: High contrast backgrounds
- Colors 9-10: Text and icons (secondary, primary)
- Two background colors: BG-1 for most surfaces, BG-2 sparingly
- Semantic scales: Gray, Gray Alpha, Blue, Red, Amber, Green, Teal, Purple, Pink

## Typography (Geist)

- Geist Sans + Geist Mono — Swiss-inspired, 1:1 Figma-to-code parity
- Headings: 72, 64, 56, 48, 40, 32, 24, 20, 16, 14
- Buttons: 16, 14, 12
- Labels: 20-12 (single-line, ample line-height for icon pairing)
- Copy: 24-13 (multi-line, higher line-height)
- Each supports Subtle and Strong modifiers via `<strong>` nesting
- Typography classes pre-set `font-size`, `line-height`, `letter-spacing`, `font-weight`

## Icons (Geist)

- 450+ icons, geometric Swiss principles
- Designed at 16x16px, 1.5pt stroke width
- Outline style with hard caps, consistent angles
- Optimized for HiDPI displays

## Source

- [vercel.com/design/guidelines](https://vercel.com/design/guidelines)
- [vercel.com/geist](https://vercel.com/geist)
- Available as AGENTS.md or `/web-interface-guidelines` command for AI coding agents
