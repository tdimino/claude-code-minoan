# overwatch-slidedeck

Live web slide decks as deployed SPAs—1920×1080, access-gated, presented from a URL rather than exported to a file. Vite 6 + React 19 + TanStack Router + motion v12 + Tailwind v4, with WebGPU shader covers (WGSL lava-nebula) and CSS fallbacks.

Distilled from Clayton Kim's Overwatch deck (2026). The sibling **aldea-slidedeck** owns static single-file HTML decks (Blueprint Mode); if the deck ships as a URL with runtime interactivity, it's overwatch-slidedeck.

## Quick Start

```bash
# One-time: install script deps (yaml, playwright, pdf-lib)
cd scripts && npm install

# Generate a deck from a YAML spec
node scripts/init-deck-from-spec.mjs assets/examples/sample-spec.yaml ~/my-deck
cd ~/my-deck && npm install && npm run dev

# Present with speaker notes (BroadcastChannel-synced second window)
open http://localhost:5173/presenter/1

# Export PNG per slide + merged PDF
node scripts/export-deck.mjs http://localhost:5173 ./export
```

Specs are validated before any write—unknown slide types, unsafe ids, and invalid transitions are rejected with every error listed at once.

## What the Scaffold Provides

| Layer | Contents |
|-------|----------|
| **Slide archetypes** | 14 types (shader-cover, split-text-list, full-bleed-quote, cli-product-demo, horizontal-timeline, ...) — `references/slide-templates.md` |
| **Components** | 10 layout + 18 interaction + 4 graphics (WebGPU/SVG/particles) + chrome/nav |
| **Hooks** | useReducedMotion, useAutoCycle, useTypewriter — reduced-motion and tab-visibility honored throughout |
| **Transitions** | AnimatePresence at the shell: none/fade/slide/scale, direction-aware, per-slide override |
| **Presenter** | `/presenter/N` route — current + next slide, notes, timer, audience sync |
| **Deploy** | SPA rewrites included for Cloudflare (`wrangler.jsonc`), Vercel, Netlify |

## Structure

```
overwatch-slidedeck/
├── SKILL.md                        # Full build workflow + QA checklist
├── assets/
│   ├── scaffold/                   # Complete Vite project (copy per deck)
│   └── examples/                   # sample-spec.yaml + 15 reference screenshots
├── scripts/
│   ├── init-deck-from-spec.mjs     # YAML spec → buildable deck
│   └── export-deck.mjs             # Playwright PNG/PDF export
├── references/                     # 6 files: deck-schema, slide-templates,
│   │                               # design-system, interactions, shaders,
│   │                               # advanced-patterns
└── evals/evals.json                # 5 skill evals
```

## Design Principles

- **Decks travel.** Every claim sourced; headline states the insight, not the topic; one motion grammar per deck.
- **Access gate, not security.** The password check is client-side—it deters casual sharing, nothing more.
- **Live-first, export-capable.** The deck is the deployed site; PDF export exists for the inbox, not as the primary artifact.

## Cross-Skill Boundaries

- **aldea-slidedeck** — static single-file HTML decks. **conductor-motion** — self-contained behavioral animation demos. **component-gallery** — pattern research feeding slide content.
