# Composio Design Tokens

Concrete token values extracted from composio.dev (August 2026, live CSS variable dump). Use when building developer-tool aesthetics with dark/light band rhythm and monospace technical chrome. Complements `composio-component-patterns.md` and `composio-signature-techniques.md`.

---

## 1. Color System

### Foundation

Composio runs a stock shadcn/Tailwind v4 token system (oklch neutrals, `--sidebar-*`/`--chart-*` sets intact) with a thin brand layer on top. When implementing: scaffold with shadcn defaults, then override only the brand and background tokens below.

| Token | Value | Usage |
|-------|-------|-------|
| `--background` | `#f6f6f6` | Light band background (not white—warm gray) |
| `--foreground` | `#0f0f0f` | Ink on light bands (not pure black) |
| `--card` | `#fff` | Cards on light bands |
| `--popover` | `#fafafa` | Popovers, elevated surfaces |
| Dark band bg | `#0f0f0f` – `#000` | Dark sections use the ink color as ground |
| Dark band card | `rgb(30, 30, 30)` | Panels on dark sections |

### Brand Palette

| Name | Hex | Usage |
|------|-----|-------|
| Brand Blue | `#51a2ff` | Links, accents, "FOR YOU" chip borders |
| Brand Hover | `#3590f5` | Hover state |
| Brand Active | `#1f7ee8` | Active/pressed state |
| Deep Blue | `rgb(0, 7, 205)` | Saturated accent (observed in computed styles; likely glitch-art family) |
| Emerald Status | `bg-emerald-400` / `oklch(0.792 0.209 151.711)` | Live/connected status dots |
| Violet Accent | `rgb(139, 92, 246)` | Syntax highlighting, secondary accent |

### Neutral Scale (shadcn defaults, kept)

| Token | Value |
|-------|-------|
| `--primary` | `oklch(20.5% 0 0)` |
| `--secondary` / `--muted` / `--accent` | `oklch(97% 0 0)` |
| `--muted-foreground` | `oklch(55.6% 0 0)` |
| `--border` / `--input` | `oklch(92.2% 0 0)` |
| `--ring` | `oklch(70.8% 0 0)` |
| Dark-section muted text | `rgba(255,255,255,0.4)` – `rgba(255,255,255,0.85)` in ~8 alpha steps |

Key principle: on dark bands, hierarchy comes from white-alpha steps (`/0.85` body, `/0.56` captions, `/0.2` hairlines), never from gray hex values.

### Semantic Colors

| Token | Value |
|-------|-------|
| `--destructive` | `oklch(57.7% .215 27.3)` |
| `--success` | `oklch(54.6% .16 155.8)` |
| `--warning` | `oklch(66.6% .16 75)` |

---

## 2. Typography

| Role | Font | Notes |
|------|------|-------|
| Display + body | ABC Diatype | Licensed (ABC Dinamo). Free substitutes: Inter Tight, Neue Montreal, or Söhne-adjacent grotesks. Never let it silently fall back to system sans—name the substitute. |
| Technical chrome | JetBrains Mono | Eyebrow labels, buttons, panel titles, footer nav, metadata. SIL OFL. |
| Terminal fallback | Menlo | Inside code panes |

Scale observed (1280px viewport): hero 64px/1.05 grotesk; section headers 40–44px; eyebrow chips 14px mono, nav category headers 11px; body 16px. Mono chrome is uppercase by *content*—caps are typed into the HTML, not applied via `text-transform`. Tracking runs near-flat to slightly negative (−0.011em at 14px), turning positive (~0.05em) only on the 11px nav headers.

---

## 3. Radius & Borders

| Token | Value | Usage |
|-------|-------|-------|
| `--radius` | `.625rem` (10px) | shadcn default, used on app-like panels |
| Marketing radius | `0px` | Buttons—hard square corners, technical feel |
| Full round | `9999px` | Status dots only |
| Hairline | `1px` at `--border` (light) / `rgba(255,255,255,0.1–0.15)` (dark) | Card borders, grid rules, accordion rows |

Square-cornered marketing buttons against shadcn's 10px product default is deliberate: the marketing surface reads harder and more technical than the app.

---

## 4. Band Rhythm

Sections alternate `#0f0f0f` dark ↔ `#f6f6f6` light down the page: dark hero → dark feature rail → light "For You" → dark platform → dark SDK → light final CTA → black footer. Each band is full-bleed; content sits in a bordered container whose hairlines extend to the band edges (see blueprint grid in `composio-component-patterns.md`). Use for: developer-tool landing pages where product UI mocks need a dark ground but conversion sections want light-mode clarity.

---

## 5. Motion Tokens

| Animation | Mechanism | Usage |
|-----------|-----------|-------|
| `animate-pulse` | Tailwind default opacity pulse | Loading placeholders, cursor blink (`h-[13px] w-px` caret) |
| `animate-pulse-dot` | Custom pulse on `size-1.5 rounded-full bg-emerald-400` | Live status indicators |
| Canvas hero | Generative glitch animation, JS-driven | See `composio-signature-techniques.md` |

Motion is sparse—status pulses and the hero canvas carry it all; sections themselves are static.
