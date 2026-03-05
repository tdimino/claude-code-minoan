# Mintlify Signature Techniques

High-level design patterns and techniques that define Mintlify's visual identity. Not individual tokens or components---these are the *why* behind Mintlify's aesthetic decisions. Complements `mintlify-design-tokens.md` and `mintlify-component-patterns.md`.

---

## Dark-First Dual-Mode Design

Mintlify treats dark mode as co-equal to light mode, not a derivative. Both modes ship with the same visual weight and polish.

**Key rules:**
- Page backgrounds: blue-tinted blacks (`#0F1117`) in dark, pure white in light
- Never use pure black (`#000000`) for dark backgrounds---the blue tint creates perceived depth
- Borders replace shadows as the primary elevation mechanism (borders work identically in both modes)
- Dual SVG hero illustrations: `hero-image-light.svg` and `hero-image-dark.svg` are completely separate assets, not CSS-filtered
- Logo ships in both variants: distinct light and dark logos, not color-inverted
- Semantic callout colors shift fully: `#EFF6FF` light bg becomes `#1E293B` dark bg for info callouts

**When to apply:** Any project targeting developers, SaaS products, or technical audiences that use both modes. The principle: design dark mode first (where contrast constraints are tighter), then derive light mode.

---

## AI-Native Documentation

Mintlify's core thesis: documentation should serve both human readers and AI agents simultaneously. Every feature reflects this dual audience.

**Key patterns:**
- **llms.txt**: Machine-readable site index at `/llms.txt` for LLM crawlers (analogous to robots.txt for search)
- **Model Context Protocol**: Built-in MCP server support so AI assistants can query docs programmatically
- **skill.md export**: Auto-generated Claude Code skill files from documentation content
- **Markdown export**: Clean markdown of any page for LLM consumption
- **Prompt component**: Dedicated MDX component for showcasing AI prompts (with Cursor integration)
- **Context-aware AI assistant**: Embedded chatbot (Ctrl+I) trained on the docs themselves

**When to apply:** Developer documentation, API references, knowledge bases. If your docs will be consumed by AI agents (and in 2026, they will), build the machine interface alongside the human one.

---

## Progressive Disclosure Architecture

Mintlify aggressively hides content until requested. The default state is *less*, not more.

**Key patterns:**
- **Accordions**: Content sections collapsed by default, each with a title-only preview
- **Expandables**: Inline expand/collapse for supplementary detail within a section
- **View component**: Conditional rendering---show content only when a condition is met
- **Hero entry points**: 4 cards on the docs landing page (Quickstart, CLI, Editor, Components) guide users to different starting paths without overwhelming
- **Sidebar collapse**: Section groups in navigation are collapsible, with current section auto-expanded
- **On-page TOC**: "On this page" links in right sidebar let users jump without scrolling

**When to apply:** Any documentation or content-heavy interface. The principle: show the map first, then let users navigate to detail. Never front-load everything.

---

## Documentation-as-Product

Mintlify treats documentation with the same design investment as marketing pages. Docs are a product surface, not an afterthought.

**Key patterns:**
- **Same font** (Inter) across marketing and docs---no brand discontinuity at the docs boundary
- **Customer logos as social proof**: Anthropic, Coinbase, HubSpot, Vercel, X---woven into the marketing page as design elements, not a separate testimonials section
- **Customer stories as premium content**: Each logo links to a detailed case study with product screenshots
- **"Was this page helpful?" feedback** at page bottom---docs are measured like product features
- **Analytics built in**: Page views, search queries, user paths---treat docs like a product funnel
- **9 named themes**: Customers choose aesthetic identity (Mint, Maple, Palm, Willow, Linden, Almond, Aspen, Sequoia, Luma) like selecting a product template

**When to apply:** Any multi-page docs site. The principle: if your docs look worse than your marketing page, you've told users that documentation is a second-class concern.

---

## Semantic Component Naming

Mintlify names components by *intent*, not by HTML element or visual treatment. The name tells you *when* to use it, not *what* it renders.

**The naming system:**
- **Callout** (not Alert): emphasis on drawing attention to information
- **Steps** (not OrderedList): emphasis on sequential process
- **Expandable** (not Collapsible): emphasis on the action the user takes
- **Frame** (not Border): emphasis on showcasing content
- **Update** (not Changelog entry): emphasis on what changed
- **View** (not ConditionalRender): emphasis on what the reader sees
- **Tile** (not LinkCard): emphasis on the navigational grid

**When to apply:** When designing component libraries or documentation systems. Intent-based names reduce cognitive overhead: users don't need to visualize the component to know when to use it.

---

## Keyboard-First Interaction

Mintlify puts keyboard navigation at the center, not as an accessibility afterthought.

**Key patterns:**
- **Ctrl+K / Cmd+K**: Global search modal, available on every page---the primary navigation method
- **Ctrl+I / Cmd+I**: AI assistant shortcut, persistent across pages
- **Tab navigation**: Full keyboard traversal of sidebar, content, and on-page TOC
- **Focus indicators**: Visible focus rings on all interactive elements
- **Search as navigation**: The search modal serves as both search and command palette

**When to apply:** Developer tools, documentation, productivity apps. The principle: the keyboard is faster than the mouse for users who know it. Make keyboard the primary path, mouse the fallback.

---

## Decorative SVG Illustration

Mintlify's hero sections use organic, flowing SVG patterns---not photography, not abstract gradients, not 3D renders.

**Key traits:**
- **Dual-mode SVGs**: Completely separate light and dark illustrations (not CSS filters)
- **Organic flowing shapes**: Curves, loops, and flowing lines that suggest growth and connection
- **Muted color palette**: Illustrations use the same color family as the UI (greens, grays, teals)
- **Non-competing placement**: Illustrations sit beside text, never behind it or competing with readability
- **Decorative, not informational**: The illustrations set tone, they don't convey data

**When to apply:** Landing pages, hero sections, empty states. The principle: illustrations create atmosphere without demanding attention. They should feel like the room you're in, not the screen you're looking at.

---

## Code-First Interface Design

Mintlify treats developers as the primary audience. Every design decision passes through a "would a developer prefer this?" filter.

**Key patterns:**
- **CLI as co-equal to web editor**: `mintlify dev` for local preview, not just a browser-based CMS
- **Git-versioned content**: Docs live in the repo, not in a separate database---version control is the CMS
- **Code groups**: Multi-language code examples with tabbed switching (not separate pages per language)
- **Copy button on everything**: Code blocks, page content, API examples all have one-click copy
- **`docs.json` configuration**: Theme, navigation, and settings in a JSON file, not a GUI
- **Syntax highlighting**: First-class code coloring with language detection and line numbers
- **"Report incorrect code" link**: Below every code block, acknowledging that code examples can go stale

**When to apply:** Any product where developers are the primary users. The principle: developers trust code over prose, version control over databases, terminals over GUIs.
