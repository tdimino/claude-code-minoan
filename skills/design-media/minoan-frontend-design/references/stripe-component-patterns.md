# Stripe Component Patterns

Reverse-engineered component architecture from stripe.com (March 2026). Each entry: component name, visual description, DOM/CSS mechanism, and when to use. Complements `stripe-design-tokens.md` and `stripe-signature-techniques.md`.

---

## Buttons

**Primary CTA** — Solid purple button with white text, subtle shadow on hover.
`background: #533AFD; color: #fff; padding: 8px 16.5px; border-radius: 4px; font-weight: 500; transition: background-color 0.3s cubic-bezier(0.25, 1, 0.5, 1)`. Hover darkens ~10%. Use for primary actions, hero CTAs.

**Secondary / Ghost Button** — White background with lavender border, purple text.
`background: #fff; border: 1px solid #B9B9F9; color: #533AFD; border-radius: 4px`. Hover fills with light lavender wash. Use for secondary actions alongside primary CTAs.

**Pill CTA (Pricing)** — High-radius button used exclusively on pricing pages for conversion.
`border-radius: 16.5px; padding: 8px 20px; background: #635BFF; color: #fff`. The pill shape signals "buy now" intent. Use for pricing CTAs, checkout buttons.

**Arrow Hover Button** — Text link with animated right-arrow that slides in on hover.
`<a>Link text <span class="arrow">→</span></a>` where `.arrow` has `transform: translateX(0); transition: transform 0.2s ease`. On hover: `transform: translateX(4px)`. The arrow is an inline SVG (`<svg width="12" height="12">`). Use for "Learn more" links, section CTAs.

**Google OAuth Button** — Social login with Google icon, system font, strict brand compliance.
`background: #fff; border: 1px solid #d3d3d3; border-radius: 4px; padding: 10px 24px`. Google "G" logo as inline SVG. Font matches system stack, not Sohne. Use for third-party auth buttons.

---

## Cards

**Pricing Tier Card** — White card with shadow elevation, internal header/body/footer zones.
DOM: `Card Card--shadowMedium > CardHeader > CardBody > CardFooter`. CSS: `background: #fff; border-radius: 8px; box-shadow: rgba(50, 50, 93, 0.25) 0px 2px 5px -1px, rgba(0, 0, 0, 0.3) 0px 1px 3px -1px; padding: 32px`. Header contains plan name + price, body has feature list with check icons, footer has pill CTA. Use for pricing tiers, plan comparison.

**Product Feature Card** — Icon + heading + description in a vertical stack within a grid cell.
`display: flex; flex-direction: column; gap: 16px; padding: 24px`. Icon is 40x40 SVG in accent color. Heading is 18px/600. Description is 14px/400 in muted navy. No border—relies on grid gap for separation. Use for feature grids, capability showcases.

**Customer Story Card** — Logo + quote + attribution, minimal chrome.
White background, company logo (grayscale, 80px wide), pull quote in 16px/400 italic, attribution in 14px/600. Hover: subtle shadow elevation. Use for testimonials, social proof sections.

**Bento Card** — Oversized grid cell with illustration or interactive demo inside.
`grid-column: span 2` or `span 3` in a named grid. Contains either a product screenshot, animated SVG, or live code demo. Background often tinted (`#F6F9FC` or gradient). Use for hero features, product demos in grid layouts.

**Utility Card** — Compact icon + label card for secondary features.
`padding: 16px; display: flex; align-items: center; gap: 12px`. 24x24 icon, 14px/500 label. Optional right-arrow on hover. Use for feature lists, integration grids, resource links.

---

## Navigation

**Global HDS Nav** — Sticky top bar with logo, mega-menu dropdowns, and dual CTAs.
`position: sticky; top: 0; z-index: 100; background: #fff; border-bottom: 1px solid #e6e6e6; height: 64px`. Logo left, nav links center (Products, Solutions, Developers, Resources, Pricing), "Sign in" text + "Contact sales" primary button right. Dropdowns are full-width mega-menus with icon + title + description columns. BEM: `hds-nav`, `hds-nav__item`, `hds-nav__dropdown`.

**Docs Sidebar** — Fixed left panel with collapsible section groups.
`width: 250px; position: fixed; top: 64px; left: 0; height: calc(100vh - 64px); overflow-y: auto; padding: 24px 0`. Section headings are 12px/600 uppercase in muted color. Links are 14px/400, active state: `color: #5469D4; font-weight: 700; border-left: 2px solid #5469D4`. Use for documentation, knowledge bases.

**Breadcrumb Trail** — Slash-separated path with linked ancestors.
`font-size: 14px; color: #3C4257`. Links in `#5469D4`, current page unlinked in body color. Separator is `/` with `margin: 0 8px`. Use for docs, multi-level navigation.

**Pricing Sticky Nav** — Horizontal pill-button row that sticks on scroll.
`position: sticky; top: 64px; background: #fff; border-bottom: 1px solid #e6e6e6; padding: 12px 0`. Contains segmented pill buttons (`border-radius: 16.5px`) for product switching. Active pill gets `background: #635BFF; color: #fff`. Use for product comparison, tabbed pricing.

---

## Hero Sections

**Gradient Mesh Hero** — Full-width hero with animated WebGL gradient background.
The mesh is canvas-rendered (not CSS). Fallback: `background: linear-gradient(135deg, #533AFD 0%, #0A2540 50%, #00D4AA 100%)`. Content overlay: headline in 48px/700 white, subtitle in 20px/400 white/80%, CTA pair (primary + ghost). Use for landing page heroes. See `stripe-signature-techniques.md` for mesh details.

**Product Split Hero** — Text left, product screenshot/illustration right at 50/50.
`display: grid; grid-template-columns: 1fr 1fr; align-items: center; gap: 48px; padding: 80px 0`. Left: headline + body + CTA stack. Right: product UI screenshot with tinted shadow, often tilted 2-5deg with `transform: perspective(1000px) rotateY(-5deg)`. Use for product pages, feature announcements.

**Counter Hero** — Live-updating metric (like GDP processed) as the hero focal point.
Large number in 64px/700 with `font-variant-numeric: tabular-nums` for stable width during animation. `requestAnimationFrame` or CSS `@property` counter. Subtitle explains the metric. Use for trust-building stats, live dashboards.

---

## Code Blocks

**Tabbed Code Block** — Multi-language code sample with tab selector.
Container: `background: rgb(33, 45, 99); border-radius: 8px; overflow: hidden`. Tab bar: `background: rgba(255, 255, 255, 0.08); padding: 8px 16px`. Active tab: `border-bottom: 2px solid #fff; color: #fff`. Inactive: `color: rgba(255, 255, 255, 0.5)`. Code area: `padding: 24px; font: 13px/19px Menlo, Consolas, monospace; color: #F5FBFF`. Syntax highlighting via inline styles (see token colors in `stripe-design-tokens.md`). Use for API examples, SDK demos.

**Collapsible JSON** — Expandable/collapsible JSON response with disclosure triangles.
BEM: `CollapsibleJson > CollapsibleJson__toggle + CollapsibleJson__content`. Toggle: `cursor: pointer; color: #C1C9D2` with rotated triangle SVG. Collapsed shows `{...}` or `[...]`. Use for API response previews, webhook payloads.

**Copy Button** — Floating copy-to-clipboard in top-right of code blocks.
`position: absolute; top: 8px; right: 8px; background: rgba(255, 255, 255, 0.1); border-radius: 4px; padding: 4px 8px`. Icon: clipboard SVG, swaps to checkmark for 2s after click. `opacity: 0` until container hover. Use for any code block.

---

## Forms

**Checkout Input** — Clean single-line input with floating label and border highlight.
`border: 1px solid #e6e6e6; border-radius: 6px; padding: 12px 16px; font-size: 16px; color: #273951`. Focus: `border-color: #5469D4; box-shadow: 0 0 0 1px #5469D4`. Label floats up on focus via `transform: translateY(-20px) scale(0.85)`. Error state: `border-color: #CD3D64; color: #CD3D64`. Use for payment forms, sign-up flows.

**Payment Method Tabs** — Horizontal icon+label radio group for selecting payment type.
`display: flex; gap: 0; border: 1px solid #e6e6e6; border-radius: 6px; overflow: hidden`. Each tab: `padding: 12px 16px; border-right: 1px solid #e6e6e6`. Active: `background: #F6F9FC; border-bottom: 2px solid #5469D4`. Icon: 24x24 payment brand SVG. Use for payment method selection, settings tabs.

---

## Badges & Status

**Product Badge** — Small pill with product name and accent color.
`display: inline-flex; align-items: center; gap: 4px; padding: 4px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600`. Background: product accent at 10% opacity. Text: product accent at full. Use for tagging features to products, category labels.

**Pricing Badge** — "Most popular" or "New" label on pricing cards.
`position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #635BFF; color: #fff; padding: 4px 16px; border-radius: 9999px; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em`. Use for highlighting recommended tiers.
