# DESIGN.md Format Specification

The DESIGN.md format originates from [Google Stitch](https://stitch.withgoogle.com/docs/design-md/format/). It is a plain-text design system document that AI agents read to generate consistent UI. Markdown is the format LLMs read best — no Figma exports, no JSON schemas, no special tooling.

## Relationship to Other Design Files

| File | Layer | What it captures |
|------|-------|-----------------|
| `.design-context.md` | Intent | Audience, mood, anti-goals, design dials (from `/shape`) |
| `DESIGN.md` | Tokens | Hex values, font stacks, shadow systems, component specs |
| `globals.css` / `tailwind.config` | Implementation | The actual CSS that renders the design |

`.design-context.md` and `DESIGN.md` are complementary — the first says *who* and *why*, the second says *what exactly*. Both are consumed by `/minoan-frontend-design` during implementation.

## The 9 Sections

### 1. Visual Theme & Atmosphere

**Format**: Prose (2-4 paragraphs)

Capture the overall mood, design philosophy, and visual density. Describe the experience of using the interface — not just what it looks like, but what it *feels* like. Name the native medium (dark-mode-first? light editorial? high-density dashboard?). Call out distinctive characteristics.

**Include**:
- Core mood / philosophy (e.g., "darkness as the native medium," "editorial warmth")
- Key visual characteristics as a bulleted list
- Technology stack if relevant (Radix UI, specific OpenType features, etc.)

**Example**:
```markdown
## 1. Visual Theme & Atmosphere

Linear's website is a masterclass in dark-mode-first product design — a near-black
canvas (#08090a) where content emerges from darkness like starlight. The overall
impression is one of extreme precision engineering...

**Key Characteristics:**
- Dark-mode-native: #08090a marketing background, #0f1011 panel background
- Inter Variable with "cv01", "ss03" globally
- Brand indigo-violet: #5e6ad2 (bg) / #7170ff (accent)
- Semi-transparent white borders throughout: rgba(255,255,255,0.05)
```

### 2. Color Palette & Roles

**Format**: Grouped lists with semantic names, hex values, and functional roles

Organize colors into functional groups: backgrounds/surfaces, text/content, brand/accent, status, border/divider, overlay. Every color needs three things: a **semantic name**, a **value** (hex or rgba), and a **functional role** (what it's used for).

**Example**:
```markdown
## 2. Color Palette & Roles

### Background Surfaces
- **Marketing Black** (#010102 / #08090a): The deepest background — hero sections
- **Panel Dark** (#0f1011): Sidebar and panel backgrounds
- **Level 3 Surface** (#191a1b): Elevated surface areas, card backgrounds

### Text & Content
- **Primary Text** (#f7f8f8): Near-white, default text color
- **Secondary Text** (#d0d6e0): Body text, descriptions
- **Tertiary Text** (#8a8f98): Placeholders, metadata

### Brand & Accent
- **Brand Indigo** (#5e6ad2): CTA button backgrounds, brand marks
- **Accent Violet** (#7170ff): Links, active states, selected items
```

### 3. Typography Rules

**Format**: Font family declarations + hierarchy table

Specify primary and monospace font families with full fallback stacks. Include OpenType feature flags if relevant. The hierarchy table must include: Role, Font, Size, Weight, Line Height, Letter Spacing, and Notes.

**Example**:
```markdown
## 3. Typography Rules

### Font Family
- **Primary**: Inter Variable, SF Pro Display, -apple-system, system-ui, sans-serif
- **Monospace**: Berkeley Mono, ui-monospace, SF Mono, Menlo
- **OpenType Features**: "cv01", "ss03" enabled globally

### Hierarchy

| Role | Font | Size | Weight | Line Height | Letter Spacing | Notes |
|------|------|------|--------|-------------|----------------|-------|
| Display XL | Inter Variable | 72px | 510 | 1.00 | -1.584px | Hero headlines |
| Display | Inter Variable | 48px | 510 | 1.00 | -1.056px | Section headlines |
| Heading 1 | Inter Variable | 32px | 400 | 1.13 | -0.704px | Major sections |
| Body | Inter Variable | 16px | 400 | 1.50 | normal | Standard reading |
| Caption | Inter Variable | 13px | 400-510 | 1.50 | -0.13px | Metadata |
| Mono Body | Berkeley Mono | 14px | 400 | 1.50 | normal | Code blocks |
```

### 4. Component Stylings

**Format**: Subsections per component type, each with named variants listing CSS properties

Cover: Buttons (with all variants and states), Cards & Containers, Inputs & Forms, Badges & Pills, Navigation, Image Treatment. Each variant needs: background, text color, padding, radius, border, and relevant states (hover, focus, active, disabled).

**Example**:
```markdown
## 4. Component Stylings

### Buttons

**Ghost Button (Default)**
- Background: rgba(255,255,255,0.02)
- Text: #e2e4e7
- Padding: 8px 16px
- Radius: 6px
- Border: 1px solid rgb(36, 40, 44)
- Use: Standard actions, secondary CTAs

**Primary Brand Button**
- Background: #5e6ad2 (brand indigo)
- Text: #ffffff
- Hover: #828fff shift
- Use: Primary CTAs

### Cards & Containers
- Background: rgba(255,255,255,0.02) to rgba(255,255,255,0.05)
- Border: 1px solid rgba(255,255,255,0.08)
- Radius: 8px (standard), 12px (featured)
```

### 5. Layout Principles

**Format**: Spacing scale, grid spec, whitespace philosophy, border-radius scale

Define the base spacing unit and the full scale. Describe the grid and container system. Articulate the whitespace philosophy — this is often the most distinctive aspect of a design system.

**Example**:
```markdown
## 5. Layout Principles

### Spacing System
- Base unit: 8px
- Scale: 4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px

### Grid & Container
- Max content width: 1200px
- Hero: centered single-column, generous vertical padding
- Feature sections: 2-3 column grids

### Whitespace Philosophy
- Darkness as space: the near-black background IS the whitespace
- Section isolation: 80px+ vertical padding, no visible dividers

### Border Radius Scale
- Micro (2px): Inline badges, toolbar buttons
- Standard (6px): Buttons, inputs
- Card (8px): Cards, dropdowns
- Full Pill (9999px): Chips, tags
```

### 6. Depth & Elevation

**Format**: Table with Level, Treatment, and Use columns

Define the shadow system and surface hierarchy. On dark themes, elevation is often communicated through background luminance steps rather than traditional shadows.

**Example**:
```markdown
## 6. Depth & Elevation

| Level | Treatment | Use |
|-------|-----------|-----|
| Flat (0) | No shadow, #010102 bg | Page background |
| Surface (2) | rgba(255,255,255,0.05) bg + border | Cards, inputs |
| Ring (3) | rgba(0,0,0,0.2) 0px 0px 0px 1px | Border-as-shadow |
| Elevated (4) | rgba(0,0,0,0.4) 0px 2px 4px | Floating elements |
| Dialog (5) | Multi-layer shadow stack | Modals, popovers |
```

### 7. Do's and Don'ts

**Format**: Two bulleted lists

Design guardrails and anti-patterns specific to this system. The "Don't" list is often more valuable than the "Do" list — it prevents the most common mistakes.

**Example**:
```markdown
## 7. Do's and Don'ts

### Do
- Use Inter Variable with "cv01", "ss03" on ALL text
- Use weight 510 as default emphasis weight
- Apply aggressive negative letter-spacing at display sizes
- Keep button backgrounds nearly transparent: rgba(255,255,255,0.02-0.05)

### Don't
- Don't use pure white (#ffffff) as primary text — use #f7f8f8
- Don't use solid colored backgrounds for buttons
- Don't apply the brand indigo decoratively — it's reserved for CTAs
- Don't use weight 700 (bold) — maximum is 590
```

### 8. Responsive Behavior

**Format**: Breakpoints table + touch targets + collapsing strategy

Define named breakpoints with pixel ranges and key changes at each. Specify minimum touch target sizes. Describe how layouts collapse from desktop to mobile.

**Example**:
```markdown
## 8. Responsive Behavior

### Breakpoints
| Name | Width | Key Changes |
|------|-------|-------------|
| Mobile | <640px | Single column, compact padding |
| Tablet | 640-1024px | Two-column grids begin |
| Desktop | >1024px | Full layout, generous margins |

### Touch Targets
- Minimum button padding: 8px with 6px radius
- Icon buttons: 44x44px minimum hit area

### Collapsing Strategy
- Hero: 72px → 48px → 32px display text
- Navigation: horizontal → hamburger at 768px
- Feature cards: 3-col → 2-col → stacked
```

### 9. Agent Prompt Guide

**Format**: Quick-reference color map + ready-to-use prompt snippets

A copy-paste block that agents can use directly. Include the most commonly needed values: CTA color, backgrounds, text colors, accent, border default.

**Example**:
```markdown
## 9. Agent Prompt Guide

### Quick Color Reference
- Primary CTA: #5e6ad2
- Page Background: #08090a
- Panel Background: #0f1011
- Surface: #191a1b
- Heading text: #f7f8f8
- Body text: #d0d6e0
- Muted text: #8a8f98
- Accent: #7170ff
- Border (default): rgba(255,255,255,0.08)
```

## File Naming

- **Reference DESIGN.md** (from getdesign library): place at project root as `DESIGN.md`
- **If multiple design systems coexist** (e.g., light + dark): use `DESIGN.md` for the primary and `DESIGN-dark.md` or `DESIGN-{variant}.md` for alternates
- **Custom project DESIGN.md**: same location, same format, generated via `generate_design_md.py` or written manually

## Quality Checklist

A complete DESIGN.md should have:
- [ ] All 9 sections present (prose sections can be brief but not empty)
- [ ] Every color has a semantic name, hex value, and functional role
- [ ] Typography hierarchy table with at least 6 roles
- [ ] At least 2 button variants with full CSS properties
- [ ] Spacing scale with base unit identified
- [ ] At least 3 elevation levels defined
- [ ] Do's/Don'ts with 4+ entries each
- [ ] Breakpoints table with 3+ named sizes
- [ ] Agent prompt guide with quick color reference

**Automated validation**: Run `npx @google/design.md lint DESIGN.md` to check the structural items above. See `references/google-cli.md` for rule-to-checklist mapping.
