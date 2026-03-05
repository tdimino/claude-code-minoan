# Mintlify Component Patterns

Reverse-engineered component architecture from mintlify.com and its documentation platform (March 2026). Each entry: component name, visual description, DOM/CSS mechanism, and when to use. Complements `mintlify-design-tokens.md` and `mintlify-signature-techniques.md`.

---

## Structure Components

**Tabs** --- Horizontal tab group for organizing related content variants.
Container with tab bar: `display: flex; gap: 0; border-bottom: 1px solid var(--border)`. Active tab: `border-bottom: 2px solid var(--accent); font-weight: 500; color: var(--text-primary)`. Inactive: `color: var(--text-muted)`. Content area renders below with `padding: 16px 0`. MDX syntax: `<Tabs><Tab title="Label">content</Tab></Tabs>`. Use for language variants, OS-specific instructions, framework alternatives.

**Code Groups** --- Tabbed multi-language code blocks in a single container.
Wraps multiple fenced code blocks: `<CodeGroup>` renders a tabbed interface with language labels extracted from the code fence. Tab bar: `background: var(--surface-2); border-radius: 8px 8px 0 0; padding: 8px 16px`. Each tab shows the language name or custom title. Active tab underlined with accent. Code area: `background: var(--code-bg); border-radius: 0 0 8px 8px; padding: 16px; font: 14px/1.6 "Fira Code"`. Use for API examples with multiple SDKs, installation commands across package managers.

**Steps** --- Numbered sequential instructions with visual step indicators.
Ordered container with left-side step numbers: `<Steps><Step title="Step label">content</Step></Steps>`. Each step renders as: number circle (24px, accent bg, white text) + title (16px/600) + content block with left border continuation line (`2px solid var(--border)`, connecting step circles). Content can include code blocks, images, nested components. Use for setup guides, tutorials, multi-step processes.

**Columns** --- Multi-column layout grid.
`<Columns columns={2}>` renders `display: grid; grid-template-columns: repeat(N, 1fr); gap: 24px`. Responsive: collapses to single column on mobile. Accepts any child content. Use for side-by-side comparisons, feature grids, image galleries.

**Panel** --- Full-width content block with background and optional title.
Container: `background: var(--surface); border-radius: 12px; padding: 32px`. Optional title in 20px/600. Content area below. Use for highlighted sections, feature showcases, promotional blocks within docs.

---

## Emphasis Components

**Callouts** --- Semantic alert boxes with icon, colored border, and background.
7 variants: Note, Warning, Info, Tip, Check, Danger, plus custom. Structure: `border-left: 4px solid {color}; background: {tinted-bg}; border-radius: 8px; padding: 16px 20px`. Icon: Lucide icon (16px) in semantic color. Title: optional bold label. Body: standard doc text. MDX: `<Note>content</Note>`, `<Warning>content</Warning>`, etc. Colors shift fully between light/dark modes. Use for important information, deprecation notices, best practices, breaking changes.

**Banner** --- Full-width announcement bar, typically at page top.
`width: 100%; padding: 12px 24px; background: var(--accent); color: white; text-align: center; font-size: 14px`. Optional dismiss button. Sticky: `position: sticky; top: 0; z-index: 50`. MDX: `<Banner title="Text" dismissible />`. Use for announcements, migration notices, new feature alerts.

**Badge** --- Inline status pill with semantic color.
`display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 9999px; font-size: 12px; font-weight: 500`. Variants: default (gray), success (green), warning (amber), error (red), info (blue). Background at 10% opacity of the text color. MDX: `<Badge variant="success">Active</Badge>`. Use for status indicators, version labels, API method tags (GET, POST, DELETE).

**Update** --- Changelog-style entry with date and description.
`<Update date="YYYY-MM-DD" title="Feature name">description</Update>`. Renders: date in muted 12px, title in 18px/600, description in body text. Optional `badge` prop for version tag. Left timeline indicator: `border-left: 2px solid var(--border)` with dot at the date. Use for changelogs, release notes, feature announcements.

**Frames** --- Decorative border wrapper for showcasing images or content.
`<Frame caption="Description">content</Frame>`. Renders: `border: 1px solid var(--border); border-radius: 12px; overflow: hidden; padding: 0`. Caption below in 14px muted text. Optional `color` prop for custom border accent. Use for product screenshots, UI previews, diagram showcases.

**Tooltips** --- Hover-triggered info popover.
`<Tooltip tip="Explanation">trigger text</Tooltip>`. Trigger gets dotted underline. Popover: `background: var(--surface-2); border: 1px solid var(--border); border-radius: 8px; padding: 8px 12px; font-size: 14px; max-width: 240px`. Positioned above by default, flips on overflow. Use for term definitions, abbreviation expansions, supplementary context.

---

## AI Components

**Prompt** --- AI prompt showcase with Cursor integration.
`<Prompt prompt="Your prompt text" />`. Renders: monospace text in a bordered block with accent left-bar, copy button, and optional "Open in Cursor" action. Background: `var(--code-bg)`. Purpose-built for documenting AI workflows and showing users how to interact with AI tools using the documented API/SDK. Use for AI-native documentation, LLM integration guides, agent setup instructions.

---

## Disclosure Components

**Accordions** --- Expandable/collapsible content sections.
`<Accordion title="Section title">content</Accordion>`. Collapsed state: title only with chevron icon (rotates on expand). Expanded: smooth height transition revealing content. Group variant: `<AccordionGroup>` renders multiple accordions with optional mutual exclusion. Border: `1px solid var(--border); border-radius: 8px; padding: 16px`. Title: 16px/500. Content supports all MDX including nested code blocks. Use for FAQs, optional details, API parameter descriptions.

**Expandables** --- Inline expand/collapse for supplementary content within a section.
`<Expandable title="Show more">content</Expandable>`. Lighter than Accordion---no border container, just a clickable "Show more" link with expand animation. Use for optional context within a paragraph, verbose error messages, detailed configuration options.

**View** --- Conditional content rendering based on user context.
`<View condition="authenticated">Protected content</View>`. Shows or hides content based on personalization conditions (user role, selected product, feature flag). Invisible to non-matching users. Use for personalized documentation, role-based instructions, product-specific guidance.

---

## API Documentation Components

**Fields** --- Parameter definition list with type annotations.
`<Fields><Field name="param" type="string" required>Description</Field></Fields>`. Each field renders: name in monospace 14px/600, type badge in muted pill, required indicator (red dot), description below. Nested fields supported via indentation. Border-bottom between fields: `1px solid var(--border)`. Use for API request parameters, configuration options, function arguments.

**Response Fields** --- API response schema documentation.
`<Responses><Response name="field" type="object">Description</Response></Responses>`. Same visual structure as Fields but contextually labeled for response data. Expandable nested objects. Use for documenting API response payloads, webhook event schemas.

**Examples** --- Request/response side-by-side display.
`<Examples><Example title="Get user">` with nested request + response code blocks. Renders: two-column layout on desktop (request left, response right), stacked on mobile. Each column has its own code block styling. Use for API endpoint documentation, SDK usage examples, webhook payload previews.

---

## Navigation Components

**Cards** --- Linked navigation blocks with icon, title, and description.
`<Card title="Title" icon="icon-name" href="/path">Description</Card>`. Renders: `border: 1px solid var(--border); border-radius: 12px; padding: 24px; transition: border-color 0.15s`. Hover: `border-color: var(--border-hover)`. Icon: Lucide 24px in accent color. Title: 16px/600. Description: 14px muted. Group variant: `<CardGroup cols={3}>` renders CSS grid. Horizontal layout variant with `horizontal` prop. Image variant with `img` prop for visual cards. Use for feature grids, navigation hubs, quickstart guides.

**Tiles** --- Compact icon+label navigation items in a grid.
`<Tiles><Tile title="Label" icon="icon-name" href="/path" /></Tiles>`. Smaller than Cards: `padding: 16px; display: flex; align-items: center; gap: 12px`. Icon: 20px. Title: 14px/500. No description---tiles are for quick navigation, not explanation. Grid: auto-fill with `min-width: 180px`. Use for integration lists, resource links, quick-access menus.

---

## Visual Components

**Icons** --- Inline Lucide icons with size and color control.
`<Icon icon="name" size={24} color="accent" />`. Renders inline SVG from the Lucide icon library. Size prop maps to pixel dimensions. Color accepts semantic tokens or hex values. Use for inline visual markers, button icons, list item bullets.

**Mermaid Diagrams** --- Rendered Mermaid.js diagrams in docs.
Standard Mermaid code fence: ` ```mermaid `. Renders in a centered container with auto-width. Supports: flowcharts, sequence diagrams, class diagrams, state diagrams, ERDs, Gantt charts. Dark mode: auto-inverts diagram colors. Use for architecture diagrams, API flows, state machines, data models.

**Color Swatches** --- Visual color display with hex values.
`<Color hex="#0D9373" name="Mint Green" />`. Renders: colored circle (32px) + name + hex value. Use for design system documentation, brand guidelines, theme customization guides.

**Tree** --- File/folder hierarchy display.
`<Tree>` renders an indented tree structure with folder/file icons, expand/collapse for directories, and monospace font. Lines connect parent-child nodes. Use for project structure documentation, file organization guides, directory layouts.

---

## Global Navigation

**Top Nav** --- Sticky navigation bar with logo, section links, and CTAs.
`position: sticky; top: 0; z-index: 40; height: 56px; background: var(--bg); border-bottom: 1px solid var(--border); backdrop-filter: blur(8px)`. Logo left, section links center (Documentation, Guides, API reference, Changelog), CTAs right ("Talk to us" ghost + "Get started" primary). Mobile: hamburger menu. Search trigger: `Ctrl K` badge visible.

**Docs Sidebar** --- Fixed left navigation with collapsible section groups.
`width: 240px; position: fixed; top: 56px; height: calc(100vh - 56px); overflow-y: auto; padding: 16px 0`. Section headings: `12px/600 uppercase tracking-wider text-muted`. Links: `14px/400 text-muted; padding: 6px 12px 6px 16px`. Active state: `color: var(--accent); font-weight: 500`. No left border indicator (unlike Stripe). Collapsible groups with chevron rotation.

**On-Page TOC** --- Right sidebar with heading anchors.
`position: sticky; top: 80px; width: 200px`. "On this page" label in 12px/600 uppercase. Links: 13px/400, indent by heading level. Active heading highlighted via scroll spy. Use for long documentation pages with multiple sections.

**Search Modal** --- Cmd+K activated search overlay.
`position: fixed; inset: 0; z-index: 50; background: rgba(0,0,0,0.5)`. Modal: `background: var(--bg); border: 1px solid var(--border); border-radius: 12px; max-width: 640px; margin: 20vh auto`. Input: full-width, autofocused. Results: instant, grouped by section, keyboard-navigable. Footer: `Ctrl+I` shortcut for AI assistant.
