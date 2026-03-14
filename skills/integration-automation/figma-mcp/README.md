# Figma MCP

The design-to-code bridge. Convert Figma designs into production-ready code using MCP server tools that extract semantic design data---component hierarchy, design tokens, auto-layout properties, and style definitions---directly from Figma files.

**Last updated:** 2026-01-02

**Reflects:** Figma MCP server API, Figma auto-layout semantics, and design-to-code conversion patterns.

---

## Why This Skill Exists

Screenshot-based design-to-code produces approximate results. MCP-based access gives Claude the actual design data: exact spacing values, color tokens, typography scales, component variants, and auto-layout direction. The difference is between guessing `padding: 16px` from pixels and reading `paddingLeft: 16` from the design spec.

This skill teaches Claude how to use the Figma MCP tools effectively, map auto-layout to Flexbox, extract design system tokens, and preserve responsive behavior through constraint interpretation.

---

## Structure

```
figma-mcp/
  SKILL.md                                 # Workflow and conversion patterns
  README.md                                # This file
  references/
    setup-guide.md                         # MCP server configuration
    best-practices.md                      # Extended examples and design system integration
```

---

## What It Covers

### MCP Tools

| Tool | Purpose |
|------|---------|
| `get_figma_data` | Extract full node hierarchy with properties |
| `get_figma_variables` | Read design tokens (colors, spacing, typography) |
| `get_figma_components` | List component definitions and variants |
| `get_figma_styles` | Get shared styles (fills, strokes, effects, text) |

### Auto-Layout to Flexbox

Figma auto-layout maps directly to CSS Flexbox:

| Figma Property | CSS Equivalent |
|---------------|---------------|
| `layoutMode: "HORIZONTAL"` | `flex-direction: row` |
| `layoutMode: "VERTICAL"` | `flex-direction: column` |
| `primaryAxisAlignItems` | `justify-content` |
| `counterAxisAlignItems` | `align-items` |
| `itemSpacing` | `gap` |
| `paddingLeft/Right/Top/Bottom` | `padding` |

### Design Token Extraction

Extract variables from Figma and generate CSS custom properties, Tailwind config, or theme objects. Supports color modes (light/dark) and responsive tokens.

### Conversion Workflow

```
1. Fetch component hierarchy via get_figma_data
2. Extract design tokens via get_figma_variables
3. Map auto-layout → Flexbox
4. Generate semantic HTML structure
5. Apply extracted tokens as CSS variables
6. Validate spacing and typography accuracy
```

---

## Requirements

- Figma MCP server configured (see `references/setup-guide.md`)
- Figma API access token
- Target project with Figma design files

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/figma-mcp ~/.claude/skills/
```
