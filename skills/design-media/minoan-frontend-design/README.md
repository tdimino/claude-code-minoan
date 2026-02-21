# minoan-frontend-design

Production-grade frontend interfaces that avoid generic AI aesthetics. Bold typography, committed color palettes, unexpected layouts, meticulous detail.

## Lineage

This skill descends from Anthropic's built-in `frontend-design` skill for Claude Code, which ships with the CLI. [Justin Wetch](https://www.linkedin.com/in/justinwetch/) rewrote it with clearer, more actionable instructions and validated the improvement with a 50-prompt blind A/B eval (75% win rate, p=0.006). His write-up: [Teaching Claude to Design Better](https://www.linkedin.com/pulse/teaching-claude-design-better-improving-anthropics-frontend-wetch-x45ec).

This version builds on Wetch's work with three additions:

1. **Vercel Web Interface Guidelines** (`references/vercel-web-interface-guidelines.md`) — distilled from vercel.com/design/guidelines (Sep 2025). Interactions, animation, layout, forms, design craft, performance, copy, Geist color/typography system.

2. **Design System Checklist** (`references/design-system-checklist.md`) — researched via Exa and Firecrawl, synthesized from WCAG 2.2, APCA, Tailwind v4 defaults, shadcn/ui patterns, and Linear/Resend design engineering. Concrete values for contrast ratios, touch targets, breakpoints, spacing grids, component states, animation timing, shadow layers, and token architecture.

3. **Claude 4.6 prompting alignment** — updated per [Anthropic's prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) for the Opus/Sonnet 4.6 generation.

Renamed from `frontend-design` to avoid collision with the Compound Engineering plugin's skill of the same name.

## What It Covers

- **Design thinking** before code — purpose, tone, constraints, differentiation
- **Typography** — variable fonts, kinetic lettering, custom pairings, full typographic scale
- **Color** — OKLCH as default, P3 wide-gamut, semantic 10-step scales, accessible palette creation
- **Motion** — CSS-first, compositor-friendly, `prefers-reduced-motion`, staggered reveals
- **Spatial composition** — asymmetry, z-depth, grid-breaking, dramatic scale jumps
- **Component architecture** — shadcn/ui open code model, Radix primitives, Tailwind v4 CSS-first config, DTCG tokens
- **Implementation standards** — URL as state, optimistic updates, layered shadows, nested radii, APCA contrast

## Files

```
minoan-frontend-design/
├── SKILL.md                                    # Main skill prompt
├── README.md                                   # This file
├── LICENSE.txt                                  # Apache 2.0
└── references/
    ├── vercel-web-interface-guidelines.md       # Distilled Vercel design guidelines
    └── design-system-checklist.md              # Accessibility, responsive, spacing, states, tokens
```

## Usage

Copy to `~/.claude/skills/` — Claude Code loads it automatically when building web interfaces.

```bash
cp -r minoan-frontend-design/ ~/.claude/skills/minoan-frontend-design/
```

## Credits

- **[Anthropic](https://github.com/anthropics/claude-code)** — original `frontend-design` skill
- **[Justin Wetch](https://www.linkedin.com/in/justinwetch/)** — rewrite with actionable instructions and eval-driven validation
- **[Vercel](https://vercel.com/design/guidelines)** — Web Interface Guidelines and Geist design system
- **[Exa](https://exa.ai/)** — neural search for design system research

## License

Apache 2.0 (inherited from Anthropic's original).
