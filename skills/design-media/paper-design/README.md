# Paper Design

MCP skill for [Paper Design](https://paper.design) — a DOM-based design tool where designs are HTML/CSS structures that Claude reads and writes natively.

## What It Does

Connects Claude Code to Paper's 21-tool MCP server for bi-directional design workflows:

- **Design to code** — `get_jsx` exports any Paper element as React + Tailwind JSX
- **Code to design** — `write_html` imports raw HTML/CSS into the Paper canvas
- **Visual QA** — `get_screenshot` verifies designs after every write
- **Token sync** — `get_computed_styles` extracts colors, spacing, typography for code integration

## Setup

1. Install [Paper Desktop](https://paper.design/downloads) (auto-starts MCP server at `127.0.0.1:29979`)
2. Register the MCP server:
   ```bash
   bash scripts/setup.sh
   ```
3. Add `mcp__paper` to `permissions.allow` in `~/.claude/settings.json`
4. Restart Claude Code

Verify with:
```bash
python3 scripts/health-check.py
```

## Structure

```
paper-design/
├── SKILL.md                          # 4-phase workflow: Orient, Create, Verify, Export
├── scripts/
│   ├── setup.sh                      # Idempotent MCP registration
│   └── health-check.py               # 3-check diagnostic (process, HTTP, registration)
├── references/
│   ├── tool-reference.md             # All 21 tools with signatures and 9 gotchas
│   ├── workflow-patterns.md          # 6 recipes (new design, extract code, responsive, etc.)
│   └── paper-vs-pencil.md            # Decision matrix for Paper vs Pencil
└── assets/                           # (reserved for future templates)
```

## Paper vs Pencil

Both coexist. Use Paper for design-to-code, code-to-design, and rapid prototyping (native DOM). Use Pencil for reusable design systems, existing `.pen` files, and presentations.

## Dependencies

- Paper Desktop app (macOS, from paper.design/downloads)
- Claude Code with MCP support

## Pairs With

- `minoan-frontend-design` — creative direction before building in Paper
- `shadcn` — map Paper tokens to shadcn OKLCH theme variables
- `component-gallery` — research patterns before designing
