# Composio Agent-Console Pattern

Product diorama built entirely from UI mocks: a central chat window flanked by labeled tool-call panels, sandbox code panes, and config readouts, wired together with thin connector lines. The system's architecture is *shown operating* instead of illustrated abstractly.

> Not yet in the RLAMA semantic collection (built from `.staging/` scrapes)—discoverable via Read/Grep only, same status as the Astryx pattern.

## Source

- **URL**: https://composio.dev/ ("Watch Composio In Action" section)
- **Engine**: Static React components styled with Tailwind (`animate-pulse`, `animate-pulse-dot` utilities)
- **Platform**: Custom React / Tailwind v4 / shadcn tokens

## Technique

A center-weighted composition on a dark band: the hero panel is a chat mock (rounded card, product logo header, user prompt, reply input with model badge), while satellite panels carry SCREAMING_CASE mono titles (`COMPOSIO_SEARCH_TOOLS`, `COMPOSIO_MANAGE_CONNECTIONS`, `AGENT_CONFIG`, `COMPOSIO_SANDBOX`) and plausible payloads—tool names with app logos, key/value config rows (`MODEL: claude-sonnet-4-6`), HTTP results (`200 OK · page created`), monospace Python in sandbox panes. 1px connector lines run between panel edges, implying data flow. Two or three micro-animations (emerald pulse dots, a blinking caret) make the whole diorama feel live at near-zero cost.

Credibility comes from data realism: user IDs (`usr_9x2kLm7`), version strings, OAuth labels—never lorem ipsum. Panels use either mac-window chrome (three dots) or a mono title bar, not both.

## Tags

`diorama`, `product-mock`, `terminal`, `tool-call`, `dark`, `developer-tool`, `agent`, `connector-lines`

## Key Properties

| Property | Value |
|----------|-------|
| Effect family | Static composition + micro-animation accents |
| Motion | `animate-pulse-dot` status dots, `animate-pulse` caret; nothing else moves |
| GPU cost | None (pure DOM/CSS) |
| Pointer input | None (decorative mocks, not interactive) |
| Reduced motion | Drop the pulses; composition is fully static-safe |
| A11y | Mocks are decorative—`aria-hidden="true"` on the diorama, real copy lives outside it |
| Panel chrome | Mono uppercase title bars or mac three-dot chrome, `rgb(30,30,30)` on `#0f0f0f`, 1px hairlines |
| Typography | JetBrains Mono for all panel text; 10–13px |

## Cross-References

- **Design reference**: `~/.claude/skills/minoan-frontend-design/references/composio-component-patterns.md` (agent status cards, task-chip scatter—sibling mocks from the same page)
- **Rationale**: `~/.claude/skills/minoan-frontend-design/references/composio-signature-techniques.md` (product-UI-as-illustration rules)
- **Sibling pattern**: [Composio Glitch Hero](composio-glitch-hero-pattern.md) (same page's decorative layer)
- **Related component doc**: `~/.claude/skills/minoan-frontend-design/references/research-card-component.md` (inline data-viz cards—similar "plausible data" discipline)
