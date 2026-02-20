---
name: frontend-design
description: This skill should be used when building web components, pages, artifacts, posters, or applications (websites, landing pages, dashboards, React components, HTML/CSS layouts, or styling/beautifying any web UI). Creates distinctive, production-grade frontend interfaces with high design quality that avoids generic AI aesthetics.
license: Complete terms in LICENSE.txt
---

Create distinctive, production-grade frontend interfaces that avoid generic "AI slop" aesthetics. Implement real working code with exceptional attention to aesthetic details and creative choices.

Accept frontend requirements: a component, page, application, or interface to build. The request may include context about purpose, audience, or technical constraints.

## Design Thinking

Before coding, understand the context and commit to a BOLD aesthetic direction:
- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Commit to a distinct direction: brutally minimal, maximalist chaos, luxury/refined, lo-fi/zine, dark/moody, soft/pastel, editorial/magazine, brutalist/raw, retro-futuristic, handcrafted/artisanal, organic/natural, art deco/geometric, playful/whimsical, industrial/utilitarian, etc. There are infinite varieties to start from and surpass. Use these as inspiration, but the final design should feel singular, with every detail working in service of one cohesive direction.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

Choose a clear conceptual direction and execute it with commitment. Bold maximalism and refined minimalism both work—the key is intentionality, not intensity.

Then implement working code (HTML/CSS/JS, React, Vue, etc.) that is:
- Production-grade, functional, and responsive
- Visually striking and memorable
- Cohesive with a clear aesthetic point-of-view
- Meticulously refined in every detail

## Frontend Aesthetics Guidelines

Focus on:
- **Typography**: Typography carries the design's singular voice. Choose fonts with interesting personality. Default fonts signal default thinking: skip Arial, Inter, Roboto, system stacks. Font choices should be inseparable from the aesthetic direction. Display type should be expressive, even risky. Body text should be legible, refined. Pair them like actors in a scene. Work the full typographic range: size, weight, case, spacing to establish hierarchy.
- **Color & Theme**: Commit to a cohesive aesthetic. Palettes should take a clear position: bold and saturated, moody and restrained, or high-contrast and minimal. Lead with a dominant color, punctuate with sharp accents. Avoid timid, non-committal distributions. Use CSS variables for consistency.
- **Motion**: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Use Motion library for React when available. Focus on high-impact moments: one well-orchestrated page load with staggered reveals (animation-delay) creates more delight than scattered micro-interactions. Use scroll-triggering and hover states that surprise.
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap and z-depth. Diagonal flow. Grid-breaking elements. Dramatic scale jumps. Full-bleed moments. Generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Add contextual effects and textures that match the overall aesthetic. Apply creative forms like gradient meshes, noise and grain overlays, geometric patterns, layered transparencies and glassmorphism, dramatic or soft shadows and glows, parallax depth, decorative borders and clip-path shapes, print-inspired textures (halftone, duotone, stipple), knockout typography, and custom cursors.

Avoid generic AI-generated aesthetics: overused font families (Inter, Roboto, Arial, Space Grotesk, system fonts), cliched color schemes (particularly purple gradients on white backgrounds), predictable layouts and component patterns, and cookie-cutter designs that lack context-specific character.
Prefer distinctive fonts, bold committed palettes, layouts that surprise, bespoke details. Root every choice in the specific context.

Build creatively on the user's intent, and make unexpected choices that feel genuinely designed for the context. Every design should feel distinct. Actively explore the full range: light and dark themes, unexpected font pairings, substantially varied aesthetic directions. Let the specific context drive choices rather than familiar defaults.

Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate code with extensive animations and effects. Minimalist or refined designs need restraint, elegance, and precision. All designs need careful attention to spacing, typography, and subtle details. Excellence comes from executing the vision well.

## Implementation Standards (2025-2026)

Distilled from the Vercel Web Interface Guidelines, Linear's quality-as-strategy, and Resend's code-first design. Full specification: `references/vercel-web-interface-guidelines.md`
Also see: `references/design-system-checklist.md` for accessibility, responsive patterns, spacing, component states, animation timing, and design token structure.

Core principles (consult reference for complete details):

- **Interactions**: URL as state (deep-link everything), optimistic updates, `:focus-visible` over `:focus`, keyboard-navigable (WAI-ARIA), minimum hit targets (24px desktop / 44px mobile), confirm destructive actions, designed loading states (150-300ms show-delay, 300-500ms minimum visible)
- **Animation**: CSS > Web Animations API > JS libraries. Compositor-friendly (`transform`, `opacity`). Honor `prefers-reduced-motion`. Interruptible and input-driven. Never `transition: all`.
- **Design craft**: Layered shadows (2+ layers), semi-transparent borders, nested radii (child <= parent), APCA contrast over WCAG 2, optical alignment (+/-1px), interactions increase contrast on hover/active/focus
- **Forms**: Allow submitting incomplete forms for validation feedback. Enter submits single-control forms. Error placement next to fields. Warn before navigation on unsaved changes.
- **Performance**: Network latency < 500ms for mutations. Virtualize large lists. Mobile input font >= 16px.
- **Copy**: Active voice, title case for headings/buttons, error messages that guide the exit path

## Modern Color & Typography

### Color
- **OKLCH as default color space** — more vibrant, perceptually uniform than RGB/HSL. Use CSS `oklch()` function.
- **P3 wide-gamut** where supported — use `color()` function with Display P3 space for richer colors
- **Semantic 10-step color scales** (Geist pattern): backgrounds (1-3), borders (4-6), high-contrast backgrounds (7-8), text/icons (9-10). Two background colors (BG-1 for most surfaces, BG-2 sparingly).
- **Accessible palette creation** — hand-pick vibrant colors that meet APCA contrast standards. Test across light and dark contexts.
- **CSS variables drive theming** — all color tokens as custom properties. `color-scheme: dark` on `<html>` for proper scrollbar/form contrast.

### Typography
- **Variable fonts** for interaction-responsive or context-adaptive weight/width
- **Kinetic lettering** — scroll-triggered text animation as storytelling option
- **Custom fonts as brand differentiator** — system fonts for UI performance, distinctive fonts for identity
- **Full typographic scale** — separate scales for headings, buttons, labels (single-line, ample line-height for icon pairing), and copy (multi-line, higher line-height). Each supports Subtle and Strong modifiers.
- **Tabular numbers** for data comparisons and tables. Typographic (curly) quotes in prose.

## Component Architecture

### Open Code Model (shadcn/ui paradigm, 2025-2026)
- Generate components inline in the codebase (not as `node_modules` dependencies). Favor composition over configuration with consistent, composable interfaces.
- Apply beautiful defaults that work as a coherent system out of the box.

### Accessible Foundations
- **Radix UI primitives** for unstyled, accessible component foundations — built-in WAI-ARIA, keyboard navigation, focus management
- **Accessibility is the foundation, not an afterthought** — using the components correctly AUTOMATICALLY produces accessible output

### CSS-First Configuration (Tailwind v4)
- **`@theme`** for design tokens as CSS custom properties — generates utility classes automatically
- **`@utility`** for custom utility classes with full CSS
- **`@variant`** for custom variant selectors (e.g., `@variant hocus (&:hover, &:focus)`)
- **OKLCH colors by default** — Tailwind v4 ships with OKLCH
- **Namespace overrides** — `--font-*: initial` disables all defaults, then define only yours

### Machine-Readable Design
- **Semantic tokens** — use `button-primary-background` not `blue-500`. Machines and humans both need to understand INTENT.
- **Component metadata describes intent** — what the component IS FOR, not just how it looks
- **DTCG token format** — three-layer architecture: primitives (raw values), semantics (intent-based), components (element-specific)
