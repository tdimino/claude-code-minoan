# Mintlify Design Tokens

Concrete token values extracted from mintlify.com and its documentation platform (March 2026). Use when building dark-first documentation, AI-native developer portals, or knowledge platforms. Complements `mintlify-component-patterns.md` and `mintlify-signature-techniques.md`.

---

## 1. Color System

### Brand Accent

Mintlify's signature color is a fresh mint/emerald green, tuned per context.

| Name | Hex | Usage |
|------|-----|-------|
| Mintlify Green | `#0D9373` | Primary accent, CTA buttons, active sidebar states |
| Mintlify Light Green | `#16B674` | Hover states, link highlights |
| Mintlify Teal | `#0E7C6B` | Darker accent variant for pressed states |

### Light Mode Palette

| Role | Hex | Usage |
|------|-----|-------|
| Background | `#FFFFFF` | Page background |
| Surface | `#F9FAFB` | Card backgrounds, sidebar bg, off-white sections |
| Surface-2 | `#F3F4F6` | Hover states, code block backgrounds |
| Border | `#E5E7EB` | Card borders, dividers, sidebar separators |
| Border-subtle | `#F3F4F6` | Inner borders, input borders at rest |
| Text primary | `#111827` | Headlines, nav links |
| Text secondary | `#4B5563` | Body text, descriptions |
| Text muted | `#6B7280` | Sidebar inactive links, breadcrumbs, meta text |
| Text faint | `#9CA3AF` | Placeholder text, disabled states |

### Dark Mode Palette

| Role | Hex | Usage |
|------|-----|-------|
| Background | `#0F1117` | Page background (near-black with blue tint) |
| Surface | `#1A1D27` | Card backgrounds, sidebar bg |
| Surface-2 | `#21242E` | Hover states, elevated surfaces |
| Border | `#2D3039` | Card borders, dividers |
| Border-subtle | `#252830` | Inner borders |
| Text primary | `#F9FAFB` | Headlines, nav links |
| Text secondary | `#D1D5DB` | Body text |
| Text muted | `#9CA3AF` | Sidebar inactive, meta |
| Text faint | `#6B7280` | Placeholder, disabled |

Key principle: Mintlify's dark mode uses blue-tinted blacks (`#0F1117`), not pure black (`#000000`). This creates depth without harshness---the same strategy as Stripe's navy text, applied to backgrounds.

### Semantic Colors (Callouts)

| Type | Light bg | Dark bg | Icon color | Usage |
|------|----------|---------|------------|-------|
| Note | `#EFF6FF` | `#1E293B` | `#3B82F6` (blue) | General information |
| Warning | `#FFFBEB` | `#422006` | `#F59E0B` (amber) | Cautions, deprecations |
| Tip | `#F0FDF4` | `#052E16` | `#22C55E` (green) | Best practices, suggestions |
| Info | `#EFF6FF` | `#1E293B` | `#3B82F6` (blue) | Technical details |
| Check | `#F0FDF4` | `#052E16` | `#22C55E` (green) | Success, completion |
| Danger | `#FEF2F2` | `#450A0A` | `#EF4444` (red) | Breaking changes, errors |

---

## 2. Typography

### Font Stacks

| Surface | Stack | Notes |
|---------|-------|-------|
| Marketing | `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` | Homepage, pricing, customer pages |
| Documentation | `Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif` | Same font for brand unity |
| Code | `"Fira Code", "JetBrains Mono", Menlo, Monaco, Consolas, monospace` | Code blocks, inline code |

Unlike Stripe (which separates marketing/docs fonts), Mintlify uses one font throughout---Inter as the foundation for a developer-facing audience that values consistency over typographic expression.

### Type Scale

**Marketing pages (Inter):**

| Role | Size | Weight | Line Height | Letter Spacing |
|------|------|--------|-------------|----------------|
| Hero H1 | 56px | 700 | 1.1 | -0.025em |
| Section H2 | 36px | 700 | 1.2 | -0.02em |
| Feature H3 | 24px | 600 | 1.3 | -0.01em |
| Body (hero) | 20px | 400 | 1.5 | normal |
| Body (standard) | 16px | 400 | 1.6 | normal |

**Documentation pages (Inter):**

| Role | Size | Weight | Line Height |
|------|------|--------|-------------|
| Doc H1 | 30px | 700 | 1.25 |
| Doc H2 | 24px | 600 | 1.3 |
| Doc H3 | 20px | 600 | 1.4 |
| Doc Body | 16px | 400 | 1.7 |
| Sidebar section heading | 12px | 600 | 1.4 |
| Sidebar nav link | 14px | 400 (500 active) | 1.5 |
| Code | 14px | 400 | 1.6 |

---

## 3. Spacing

| Token | Value | Usage |
|-------|-------|-------|
| Base unit | 4px | Consistent across marketing and docs |
| Docs sidebar width | 240px | Fixed left sidebar |
| Docs content max-width | 768px | Article content area |
| Docs content padding | `32px 24px` | Top and sides of article |
| Section gap (marketing) | 80-120px | Between major homepage sections |
| Card internal padding | 24px | All card variants |
| Component gap (docs) | 16px | Between adjacent components |
| Nav height | 56px | Global navigation bar |

---

## 4. Shadows & Borders

Mintlify favors **borders over shadows** for elevation---the opposite of Stripe's shadow-heavy approach.

| Element | Light Mode | Dark Mode |
|---------|-----------|-----------|
| Card border | `1px solid #E5E7EB` | `1px solid #2D3039` |
| Card hover | `1px solid #D1D5DB` | `1px solid #3D4049` |
| Nav border-bottom | `1px solid #E5E7EB` | `1px solid #2D3039` |
| Callout border-left | `4px solid {semantic-color}` | `4px solid {semantic-color}` |
| Code block | No border, bg color shift | No border, bg color shift |
| Dropdown shadow | `0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -2px rgba(0,0,0,0.1)` | `0 4px 6px -1px rgba(0,0,0,0.3)` |

Key principle: Borders create cleaner separation in dual-mode interfaces. Shadows that look premium in light mode often disappear or look muddy in dark mode. Mintlify's border-first approach ensures consistent hierarchy across both modes.

---

## 5. Border Radius

| Component | Radius | Notes |
|-----------|--------|-------|
| Buttons (primary) | 8px | Rounded but not pill |
| Cards | 12px | Generous rounding |
| Code blocks | 8px | Slightly less than cards |
| Callouts | 8px | Matches code blocks |
| Inputs | 6px | Slightly sharper |
| Badges | 9999px | Full pill |
| Accordions | 8px | Consistent with blocks |
| Search modal | 12px | Matches card radius |

---

## 6. Code Block Styling

| Token | Light Mode | Dark Mode |
|-------|-----------|-----------|
| Background | `#F8FAFC` | `#1E1E2E` |
| Text default | `#1E293B` | `#CDD6F4` |
| Strings | `#059669` (green) | `#A6E3A1` |
| Numbers | `#D97706` (amber) | `#FAB387` |
| Keywords | `#7C3AED` (purple) | `#CBA6F7` |
| Comments | `#9CA3AF` | `#6C7086` |
| Functions | `#2563EB` (blue) | `#89B4FA` |
| Tab bar bg | `#F1F5F9` | `#181825` |
| Tab active | `accent + underline` | `accent + underline` |
| Font | `14px/1.6 "Fira Code"` | Same |
| Copy button | `opacity: 0` until hover | Same |

---

## 7. Color Scheme Metadata

| Property | Value |
|----------|-------|
| Default scheme | Dual (light + dark, system preference) |
| Design system | Custom component library (React/MDX) |
| Themes | 9 named themes (Mint, Maple, Palm, Willow, Linden, Almond, Aspen, Sequoia, Luma) |
| Theme config | `docs.json` with `theme` field |
| Tone | Developer-friendly, clean, modern |
| Framework | Next.js (detected from `_next/image` URLs) |
