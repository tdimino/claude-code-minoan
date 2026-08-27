# Composio Signature Techniques

High-level design patterns that define composio.dev's visual identity (August 2026). Not individual tokens or components—the *why* behind the aesthetic. Complements `composio-design-tokens.md` and `composio-component-patterns.md`.

---

## Mono-as-Chrome Typography System

Every piece of interface *chrome*—eyebrow labels, buttons, panel titles, tab labels, footer nav, metadata captions—is uppercase JetBrains Mono, while every piece of *content*—headlines, body copy—is a humanist grotesk (ABC Diatype). The split is absolute: mono never carries prose, grotesk never carries chrome.

**Key rules:**
- Mono chrome is always uppercase, 11–13px, `letter-spacing: 0.05–0.1em`
- Buttons become terminal commands (`GET STARTED FOR FREE`), labels become system identifiers (`COMPOSIO_SEARCH_TOOLS`)
- Snake_case and SCREAMING_CASE in labels are features, not bugs—they signal "this is API surface"
- The grotesk stays sentence-case and generously sized (40–72px headlines) so the two voices never blur

**When to apply:** Developer tools, agent products, API companies—anywhere the audience reads code all day and trusts interfaces that speak it. This is the single most transferable Composio trait; it works even without the glitch art.

---

## Product-UI-as-Illustration

There are no abstract illustrations, stock art, or 3D blobs. Every visual on the page is a mock of the product itself: a chat window mid-conversation, tool-call panels with real-looking payloads (`NOTION_CREATE_PAGE`, `200 OK · page created`), sandbox code panes with plausible Python, a full Claude Code terminal with ASCII banner and version line. Panels are wired together with thin connector lines, forming a diorama of the system's architecture.

**Key rules:**
- Mocks carry *plausible* data, not lorem ipsum—user IDs (`usr_9x2kLm7`), model names, HTTP statuses
- Status dots pulse (`animate-pulse-dot`), carets blink—two or three tiny live signals make the whole diorama feel running
- Panels use mac-window chrome (three dots) or mono title bars, never both on one panel
- Connector lines are 1px, drawn between panel edges, implying data flow

**When to apply:** When the product is invisible infrastructure (APIs, auth, agents). Show the system operating instead of describing it. Full pattern anatomy: `~/.claude/skills/component-gallery/references/composio-agent-console-pattern.md`.

---

## Pixel-Glitch Art Direction

The one decorative element is a family of pixelated glitch-gradient artifacts—rectangular blocks of blue/cyan/pink/white arranged like corrupted bitmap data or a paused video signal. It appears at three fidelities:

1. **Live canvas hero** — a full-width `<canvas>` (viewport-width × ~644px, positioned at top:0 behind the hero type) animating the glitch blocks generatively. Pattern spec, GPU cost, and fallbacks: `~/.claude/skills/component-gallery/references/composio-glitch-hero-pattern.md`.
2. **Static section art** — pre-rendered PNGs of the same visual language (`managed-auth-art.png`, `triggers-art.png`) inside feature cards. Same palette, zero runtime cost.
3. **ASCII/pixel display type** — headings like `COMPOSIO SDK` and `CLAUDE CODE` set in ASCII box-drawing/block characters, monochrome or single-hue, echoing the bitmap texture in pure text.

**Key rules:**
- Palette stays inside brand blues + cyan + pink + white; the glitch is never rainbow
- Reduced motion / no-JS: freeze the canvas to a static frame or swap a PNG of the same composition—the composition must survive being still
- GPU cost: block-fill canvas painting is cheap (2D context, no WebGL required); cap repaint rate (~12–24fps reads *more* glitchy than 60fps smoothness)
- ASCII headings are real text in `<pre>`—selectable, but give them `aria-label` with the plain word and `aria-hidden` on the art if a visible plain heading exists

**When to apply:** When the direction calls for "technical," "raw," or "systems-level" atmosphere. The three fidelities let one motif scale from expensive (hero) to free (text) across a page.

---

## Dark/Light Band Conversion Rhythm

Dark bands (`#0f0f0f`) carry product demonstration—dioramas, feature rails, SDK grids—while light bands (`#f6f6f6`) carry conversion moments: the "For You" pitch and the final CTA. The page breathes dark→light→dark, and the final CTA's light band after a long dark stretch functions as a spotlight.

**When to apply:** Long-scroll developer landing pages. Put complexity in the dark, asks in the light.
