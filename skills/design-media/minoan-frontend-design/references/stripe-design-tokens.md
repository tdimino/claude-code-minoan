# Stripe Design Tokens

Concrete token values extracted from stripe.com (March 2026). Use when building Stripe-aesthetic interfaces or when the direction is "premium light-mode." Complements `stripe-component-patterns.md` and `stripe-signature-techniques.md`.

---

## 1. Color System

### Primary Accent Palette

Stripe uses contextual purple tuning—the same violet family, shifted per page intent.

| Name | Hex | RGB | Usage |
|------|-----|-----|-------|
| Stripe Purple | `#533AFD` | `rgb(83, 58, 253)` | Homepage primary CTA, marketing accent |
| Stripe Blurple | `#635BFF` | `rgb(99, 91, 255)` | Pricing CTAs, product accent, brand signature |
| Stripe Violet | `#9966FF` | `rgb(153, 102, 255)` | Payments product page accent |
| Docs Blue | `#5469D4` | `rgb(84, 105, 212)` | Documentation links, active sidebar states |

When implementing: pick one from this family based on context. Marketing → `#533AFD`. Product/pricing → `#635BFF`. Documentation → `#5469D4`.

### Neutral Scale

| Step | Hex | RGB | Usage |
|------|-----|-----|-------|
| Navy (logo/headline) | `#0A2540` | `rgb(10, 37, 64)` | Logo fill, marketing headlines, primary text |
| Dark Navy | `#061B31` | `rgb(6, 27, 49)` | Homepage primary text |
| Docs Headline | `#1A1F36` | `rgb(26, 31, 54)` | Docs h1-h3, pricing card text |
| Docs Nav | `#1A2C44` | `rgb(26, 44, 68)` | Sidebar nav links |
| Docs Body | `#3C4257` | `rgb(60, 66, 87)` | Docs paragraph text, secondary text |
| Docs Input | `#273951` | `rgb(39, 57, 81)` | Input field text |
| Docs Muted | `#414552` | `rgb(65, 69, 82)` | Docs secondary text |
| Off-White | `#F6F9FC` | `rgb(246, 249, 252)` | Page background (product/pricing pages) |
| White | `#FFFFFF` | `rgb(255, 255, 255)` | Primary background, button text, docs content area |

Key principle: Stripe never uses pure black (`#000000`) for text on marketing pages. The darkest text is `#0A2540` (navy)—this creates warmth without harshness.

### Button & UI Colors

| Element | Color | Context |
|---------|-------|---------|
| Secondary button border | `#B9B9F9` | Lavender border on homepage secondary buttons |
| Secondary button shadow | `rgba(0, 0, 0, 0.1)` | `0px 4px 8px` on product/pricing pages |
| Docs button shadow | `rgba(60, 66, 87, 0.08), rgba(0, 0, 0, 0.12)` | Layered: `0px 2px 5px`, `0px 1px 1px` |

### Code Block Syntax Colors

Used in documentation code blocks against `rgb(33, 45, 99)` background:

| Token | Color | RGB | Usage |
|-------|-------|-----|-------|
| Strings | `#85D996` | `rgb(133, 217, 150)` | JSON string values, quoted text |
| Numbers | `#E4AB80` | `rgb(228, 171, 128)` | Numeric values |
| Booleans | `#7FD3ED` | `rgb(127, 211, 237)` | true/false, null |
| Default | `#F5FBFF` | `rgb(245, 251, 255)` | Braces, colons, default text |
| Muted | `#C1C9D2` | `rgb(193, 201, 210)` | Comments, line numbers |

---

## 2. Typography

### Font Stacks

| Surface | Stack | Notes |
|---------|-------|-------|
| Marketing | `Sohne, "Helvetica Neue", Arial, sans-serif` | Homepage, Payments, Pricing. Custom font. |
| Homepage variant | `Sohne, "SF Pro Display", sans-serif` | Lighter fallback chain |
| Documentation heading | `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif` | System stack for docs |
| Documentation body | `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Ubuntu, sans-serif` | Optimized for reading |
| Code | `Menlo, Consolas, monospace` | All code blocks, inline code |

When implementing: use a geometric sans-serif (Sohne-like) for marketing surfaces. System stack for documentation. Menlo/Consolas for code.

### Type Scale

**Marketing pages (Sohne):**

| Role | Size | Weight | Line Height | Letter Spacing |
|------|------|--------|-------------|----------------|
| Hero H1 | 48px | 700 | 1.1 | -0.02em |
| Section H2 | 32px | 700 | 1.2 | normal |
| Feature H3 | 18px | 600 | 1.3 | normal |
| Body (hero) | 32px | 400 | 1.4 | normal |
| Body (standard) | 14px | 400 | 1.5 | normal |

**Documentation pages (system font):**

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Doc H1 | 32px | 700 | 40px (1.25) |
| Doc H2 | 24px | 400 | 1.3 |
| Doc H3 | 16px | 600 | 1.4 |
| Doc Body | 16px | 400 | 26px (1.625) |
| Sidebar Nav | 14px | 400 (700 active) | 1.4 |
| Code | 13px | 400 | 19px (1.46) |

---

## 3. Spacing

| Token | Value | Usage |
|-------|-------|-------|
| Base unit | 4px | Consistent across product/docs pages |
| Docs content padding | `32px 48px 0px` | Top/sides/bottom of article area |
| Docs sidebar width | 250px | Fixed sidebar |
| Docs content width | 1030px | Article container |
| Sidebar nav link padding | `0px 0px 0px 16px` | Left indent for nav items |

---

## 4. Shadows

| Level | CSS | Context |
|-------|-----|---------|
| Button (product) | `0px 4px 8px rgba(0, 0, 0, 0.1)` | Secondary buttons on /payments, /pricing |
| Button (docs) | `0px 2px 5px rgba(60, 66, 87, 0.08), 0px 1px 1px rgba(0, 0, 0, 0.12)` | Layered shadow, docs buttons |
| Card (pricing) | `Card--shadowMedium`, `Card--shadowXSmall` | BEM classes, computed to subtle elevation |

Note: Stripe's shadows use tinted values (`rgba(60, 66, 87, 0.08)`)—never pure black. This is the "premium shadow" technique: shadow color matches the text color at very low opacity.

---

## 5. Border Radius

Stripe varies radius by page intent and component type:

| Component | Homepage | Product Pages | Pricing | Docs |
|-----------|----------|--------------|---------|------|
| Primary button | 4px | 6px | 16.5px (pill) | 4px |
| Secondary button | 4px | 8px | 8px | 8px |
| Input fields | — | — | — | 6px |
| Code blocks | — | — | — | 4px |
| Cards | — | — | varies | — |

Pricing page uses pill-shaped primary CTAs (`border-radius: 16.5px`) for higher conversion. Other pages use sharp rectangles (4-8px). This is intentional contextual variation, not inconsistency.

---

## 6. Color Scheme Metadata

| Property | Value |
|----------|-------|
| Color scheme | Light (all pages) |
| Design system | HDS (Hybrid Design System) on marketing, BEM + utility classes on docs |
| Tone | Professional |
| Framework | Custom (no detected component library) |
