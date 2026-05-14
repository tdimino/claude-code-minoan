# Raven Design Tokens

Concrete token values extracted from withraven.ai (May 2026). Use when building intelligence-aesthetic interfaces or when the direction is "intelligence dossier." Complements `raven-signature-techniques.md` and `raven-component-patterns.md`.

Source: Graylark's Raven visual intelligence platform (formerly GeoSpy). Three CSS files: `colors_and_type.css` (base tokens), `theme-monochrome.css` (accent override), `page-monochromatic.css` (component styles).

---

## 1. Color System

### Near-Black Neutral Spine

The entire interface lives on a near-black scale—no colored tints, no warm/cool bias. Depth comes from luminance steps alone.

| Token | Value | Usage |
|-------|-------|-------|
| `--gs-black` | `rgb(0, 0, 0)` | HTML background, deepest surface |
| `--gs-ink` | `rgb(10, 10, 10)` | Blurred overlay backgrounds |
| `--gs-chrome` | `rgb(17, 17, 17)` | Sidenav, primary chrome, `--bg-app` |
| `--gs-canvas` | `rgb(25, 25, 25)` | Content canvas, subtle button base, `--bg-canvas` |
| `--gs-surface-1` | `rgb(38, 38, 38)` | Hover raise on canvas |
| `--gs-surface-2` | `rgb(58, 58, 58)` | Ring strokes, progress tracks |
| `--gs-muted` | `rgb(96, 96, 96)` | Disabled foreground |
| `--gs-line` | `rgb(179, 179, 179)` | Secondary foreground, `--fg-muted` |
| `--gs-fg-2` | `rgb(201, 201, 201)` | Tertiary text |
| `--gs-fg-1` | `rgb(238, 238, 238)` | Primary text—NOT pure white, `--fg-default` |
| `--gs-white` | `rgb(255, 255, 255)` | Display headlines only |

Key principle: primary text is `rgb(238, 238, 238)`, never `rgb(255, 255, 255)`. Pure white is reserved for display-weight headlines. This creates a subtle vellum quality even on black.

### Translucent Alpha Tokens

Used constantly for borders, dividers, and glass effects. Five named levels:

| Token | Value | Usage |
|-------|-------|-------|
| `--gs-alpha-hairline` | `rgba(255, 255, 255, 0.11)` | Inner button rings |
| `--gs-alpha-divider` | `rgba(255, 255, 255, 0.13)` | Dividers in overlays |
| `--gs-alpha-border` | `rgba(255, 255, 255, 0.17)` | Dashed drop zones |
| `--gs-alpha-edge` | `rgba(255, 255, 255, 0.23)` | Sidenav hairlines |
| `--gs-alpha-avatar` | `rgba(255, 255, 255, 0.39)` | Avatar rings, strong borders |
| `--gs-overlay-80` | `rgba(10, 10, 10, 0.8)` | Glass panel fill |
| `--gs-overlay-33` | `rgba(0, 0, 0, 0.33)` | Glass footer fill |

### Monochromatic Blue Accent (Landing Page)

The product app uses a signal-lamp palette (jade/lime/amber/red for confidence tiers). The marketing landing page collapses ALL status colors to a single blue:

| Token | Value | Role |
|-------|-------|------|
| Accent blue | `rgb(24, 81, 255)` | Every interactive element, every badge, every indicator |
| Accent soft | `rgb(138, 161, 255)` | Soft variant for chip text |
| Accent bg | `rgb(14, 30, 90)` | Filled chip backgrounds |
| Accent fg | `rgb(220, 232, 255)` | Text on accent backgrounds |
| Accent wash | `rgba(24, 81, 255, 0.35)` | Hover glows, ring shadows |
| Accent deep | `rgb(18, 60, 200)` | Filled pin, pressed state |
| Accent glow | `rgb(70, 120, 255)` | Highlight stroke on active rings |

When implementing: use one accent color for the entire page. The monochromatic constraint forces every element to earn its place through luminance and typography, not color differentiation.

### Product Signal-Lamp Palette (App Context Only)

For dashboards that need multi-status confidence tiers:

| Tier | Token | Value | Meaning |
|------|-------|-------|---------|
| Strong | `--gs-jade` | `rgb(31, 216, 164)` | Primary action, strongest match |
| Good | `--gs-lime` | `rgb(100, 172, 29)` | Second-tier match |
| Mid | `--gs-amber` | `rgb(216, 154, 31)` | Mid confidence |
| Weak | `--gs-red` | `rgb(216, 31, 31)` | Warning, weak match |
| Data | `--gs-iris` | `rgb(123, 122, 254)` | Metadata, data-dense pills |

---

## 2. Typography

### Font Families

| Role | Canonical Font | Libre Substitute | CSS Variable |
|------|---------------|-----------------|--------------|
| Sans (primary) | ABC Diatype (Dinamo) | IBM Plex Sans | `--font-sans`, `--font-display` |
| Serif (prose) | Tobias (Dinamo) | Source Serif 4 or Lora | `--font-serif` |
| Mono (data) | DM Mono (Google) | DM Mono (already free) | `--font-mono` |

ABC Diatype is a trial-licensed grotesque from ABC Dinamo. IBM Plex Sans matches its neutral, slightly condensed proportions. Tobias is a high-contrast transitional serif; Source Serif 4 or Lora approximate its weight range.

### Type Scale

| Token | Size | Line Height | Usage |
|-------|------|------------|-------|
| `--fs-meta` | 10px | 1.0 | Mono tracked caps labels |
| `--fs-caption` | 11px | 1.0 | OR dividers, dossier buttons |
| `--fs-small` | 12px | 1.5 | Result descriptions, case details |
| `--fs-body` | 14px | 1.36 | Default body text |
| `--fs-title` | 16px | 1.0 | Panel titles |
| `--fs-h3` | 20px | 1.0 | Prompts, mid headings |
| `--fs-display` | 48px | 1.0 | Map numerals, hero display |

Display headlines scale responsively: `clamp(40px, 5.6vw, 72px)` with `-0.03em` tracking.

### Semantic Text Classes

| Class | Font | Size | Weight | Color | Extras |
|-------|------|------|--------|-------|--------|
| `.gs-display` | sans | 48px | 700 | white | `-0.01em` tracking |
| `.gs-h3` | sans | 20px | 400 | fg-default | — |
| `.gs-title` | sans | 16px | 400 | fg-default | — |
| `.gs-body` | sans | 14px | 400 | fg-default | — |
| `.gs-body-prose` | sans | 14px | 400 | fg-default | 1.36 line-height |
| `.gs-muted` | sans | 14px | 400 | fg-muted | — |
| `.gs-small` | sans | 12px | 400 | fg-default | 1.5 line-height |
| `.gs-caption` | sans | 11px | 400 | fg-default | uppercase, `0.16em` tracking |
| `.gs-mono` | mono | 10px | 400 | fg-default | — |
| `.gs-mono-caps` | mono | 10px | 400 | fg-default | uppercase |

### Weight Distribution

- 300 (Light): Display headlines, section headings, serif prose
- 400 (Regular): Body text, descriptions, mono labels
- 500 (Medium): Navigation, buttons, eyebrow labels, panel titles
- 600 (SemiBold): Step headings
- 700 (Bold): Hero display, bold body variant

---

## 3. Spacing

8pt base grid with two exceptions (4px for tight internal gaps, 12px for medium internal gaps):

| Token | Value |
|-------|-------|
| `--space-1` | 4px |
| `--space-2` | 8px |
| `--space-3` | 12px |
| `--space-4` | 16px |
| `--space-5` | 20px |
| `--space-6` | 24px |
| `--space-7` | 28px |
| `--space-8` | 32px |
| `--space-10` | 40px |
| `--space-12` | 48px |

Section padding: 120px vertical on desktop, 80px on mobile. Nav inset: 16px + safe-area from top, 20px + safe-area from sides.

---

## 4. Radii

| Token | Value | Usage |
|-------|-------|-------|
| (button) | 3px | Buttons—sharper than most systems |
| `--radius-xs` | 5px | Thumbnail corners |
| `--radius-sm` | 6px | Chips, list rows |
| `--radius-md` | 16px | Inner dashed drop zones |
| `--radius-lg` | 24px | Glass panels |
| `--radius-pill` | 9999px | Pills, badges |

Buttons use 3px (sharper than most systems). Nav bar uses 14px. The tight button radius is deliberate—military/intelligence aesthetic avoids soft rounding.

---

## 5. Shadows & Elevation

All shadows are warm-black—no colored shadows anywhere.

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-panel` | `0 24px 48px rgba(0,0,0,0.45), 0 8px 16px rgba(0,0,0,0.25)` | Cards, floating panels |
| `--shadow-sidenav` | `3px 0 24px rgba(0,0,0,0.45), 2px 0 8px rgba(0,0,0,0.25)` | Side navigation |
| `--shadow-pin` | `0 8px 4px rgba(0,0,0,0.32)` | Map pins |
| `--shadow-pill` | `0 4px 4px rgba(0,0,0,0.25)` | Pill badges |
| `--shadow-btn-primary` | `0 3px 2px rgba(0,0,0,0.36), inset 0 0 0 0.5px rgba(0,0,0,0.41)` | Primary button (light bg) |
| `--shadow-btn-secondary` | `0 3px 3px rgba(0,0,0,0.26), inset 0 0 0 0.5px rgba(255,255,255,0.11)` | Secondary button (dark bg) |

The inset `0.5px` hairline on buttons creates a subtle bevel—pressed look on primary, top highlight on secondary.

---

## 6. Motion

| Token | Value | Usage |
|-------|-------|-------|
| `--ease-std` | `cubic-bezier(0.2, 0, 0, 1)` | Standard easing (decelerate-dominant) |
| `--dur-fast` | 120ms | Hover state changes |
| `--dur-med` | 220ms | Panel transitions, menu open/close |

Scroll-driven animations use CSS custom properties (e.g., `--hero-scrub-expand`) interpolated via `IntersectionObserver` or scroll position—not GSAP or JS animation libraries.
