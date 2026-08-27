# Composio Component Patterns

Reverse-engineered component architecture from composio.dev (August 2026). Each entry: component name, visual description, DOM/CSS mechanism, and when to use. Complements `composio-design-tokens.md` and `composio-signature-techniques.md`.

---

## Labels & Buttons

**Mono Eyebrow Chip** — Section label as a bordered chip: small filled square + uppercase monospace text.
`<span class="eyebrow">■ WHY COMPOSIO</span>` with `font-family: 'JetBrains Mono'; font-size: 14px; border: 1px solid var(--border); padding: 4px 8px; display: inline-flex; gap: 8px; align-items: center`. Caps are typed into the content (no `text-transform`); tracking is near-flat (−0.011em). The square is a `6px × 6px` filled span, not a bullet glyph. Use for section eyebrows on both dark and light bands—the chip border keys to the band's hairline color.

**Uppercase-Mono CTA Pair** — Primary + secondary buttons, both uppercase JetBrains Mono, near-square corners.
Primary inverts against the band: white bg/black text on dark, black bg/white text on light. Secondary is transparent with 1px hairline border. `padding: 10px 16px; border-radius: 0; font-size: 14px; font-family: 'JetBrains Mono'`—hard square corners, caps typed into the label content (`GET STARTED FOR FREE`, `GET A DEMO`), no `text-transform`. Use for hero and final-CTA sections; the mono treatment makes buttons read as terminal commands.

**Variant Tag Chip** — Small outlined chip in brand color appended to a product name.
`Composio [FOR YOU]` where the chip is `border: 1px solid #51a2ff; color: #51a2ff; font-family: mono; font-size: 11px; padding: 2px 8px; border-radius: 4px`. A green variant (`PLATFORM`) distinguishes product lines. Use for product-line disambiguation next to headings.

---

## Feature Sections

**Numbered Feature Rail** — Scroll-linked 01–04 feature tour: sticky tab list left, per-feature art + copy right.
Left column: stacked tabs `01 SMART TOOLS / 02 CONSTANT EVOLUTION / ...` in mono, active tab highlighted with brand-blue index. Right: each feature row pairs a glitch-art panel with an embedded product mock (search bar, chat window, code pane) and copy. Copy block: `02`-style mono index chip, grotesk `<h3>`, paragraph, then a bullet list where each bullet is a `2px` left rule + text (`border-left: 2px solid rgba(255,255,255,0.3); padding-left: 12px`), not a bullet glyph. Use for 3–5-pillar product tours on dark bands.

**Left-Rule Bullet List** — Feature bullets marked by short vertical rules instead of dots.
`li { border-left: 2px solid rgba(255,255,255,0.3); padding-left: 12px; margin-bottom: 12px; }`. Reads as annotation marks in a technical document. Use inside feature rails and comparison columns; pairs with mono eyebrow chips.

**Accordion (Hairline Rows)** — Security/FAQ accordion as full-width hairline rows with +/− toggles.
Rows separated by `border-bottom: 1px solid rgba(255,255,255,0.12)`; open row shows a `−`, closed rows `+`, right-aligned; open-row title white, closed-row titles at `rgba(255,255,255,0.32)`. Content is a single muted line under the title. Use for FAQ/security/detail sections where content should stay quiet until summoned.

---

## Cards & Grids

**Blueprint Grid Cards** — Feature cards whose hairline borders extend past the card bounds into the surrounding band.
Cards sit in a CSS grid; horizontal and vertical rules are drawn as full-width/full-height `1px` lines (pseudo-elements or grid-gap borders) that continue beyond card edges, producing a drafting-table/blueprint effect. Some grid cells are intentionally empty. `border: 1px solid rgba(255,255,255,0.12)` on dark. Use for SDK/capability grids where the layout itself should feel engineered.

**Agent Status Card** — Compact card representing a running agent: title + pulse dot + app icons + last-action caption.
`Card > header (mono title + animate-pulse-dot emerald dot) > icon row (16–20px app logos) > footer caption ("Drafted reply to Sarah", muted)`. Cards tile in a 3×2 grid on `rgb(30,30,30)` panels with hairline borders. Use for showing a fleet of agents/automations at a glance—each card implies live activity without real data.

**Task-Chip Scatter** — Floating task chips (app icon + imperative label) scattered around a central terminal mock.
Each chip: `display: inline-flex; gap: 8px; padding: 10px 14px; background: #fff; border: 1px solid var(--border); border-radius: 4px; box-shadow: 2px 2px 0 rgba(0,0,0,0.08)` containing one or two 16px app logos + text like "Create a PR and post to #engineering". Chips are absolutely positioned at varied offsets, overlapping the terminal's frame. Use for "what can it do" moments—concrete tasks orbiting the tool that executes them.

**Selection-Handles Frame** — Media framed by design-tool selection chrome: dashed bounding box + square resize handles.
Image sits inside a container with `outline: 1px dashed rgba(255,255,255,0.3)`; eight `8px × 8px` white squares positioned at corners and edge midpoints; optional perspective lines converging to a vanishing point. Use for making static imagery feel like a live, manipulable object—one framed asset per section, not repeated.

---

## Footer & Chrome

**Mono Mega-Footer** — Five-column uppercase monospace link directory over black.
Columns (`PRODUCTS / SOLUTIONS / FOR AGENTS / RESOURCES / COMPANY`) with mono uppercase column headers at `rgba(255,255,255,0.4)` and link rows at `rgba(255,255,255,0.8)`; hairline column separators; social icon row bottom-left, copyright bottom-right. Everything 11–13px mono. Use for developer-tool footers—the directory doubles as a sitemap and reads as a man page.

**Logo Marquee (Dark-Band Variant)** — Infinite client-logo ticker, logos rendered monochrome at low opacity on the dark hero.
Mechanism per `marquee-component.md` (triplicated list, `translateX(-33.33%)` loop; Composio uses three `.logoloop__list` runs of six inside a `.logoloop__track`). The monochrome treatment is a `grayscale` filter class on the wrapper (`overflow-hidden px-4 py-[14px] grayscale`), logos at full opacity—not an opacity fade. No separators, sitting directly under the hero CTA pair. Extends `marquee-component.md`—see that file for the base implementation.
