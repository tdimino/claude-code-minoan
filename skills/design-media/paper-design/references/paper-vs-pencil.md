## Decision Matrix

| Dimension | Paper | Pencil |
|-----------|-------|--------|
| **Representation** | HTML/CSS DOM | Proprietary `.pen` JSON nodes |
| **Code export** | `get_jsx` → React + Tailwind directly | Manual translation from node schema |
| **Code import** | `write_html` accepts raw HTML/CSS | `batch_design` with I/U/R/C/D/M/G operation DSL |
| **Learning curve (for Claude)** | Zero — native DOM | Moderate — must learn `.pen` schema and operation syntax |
| **Design system components** | Standard HTML/CSS components | Reusable nodes with `ref` instances, deep customization |
| **Existing projects** | New (no `.pen` files to migrate) | 10 `.pen` files in worldwarwatcher |
| **MCP transport** | HTTP (`127.0.0.1:29979`) | stdio (app binary) |
| **Visual QA** | `get_screenshot` with 1x/2x scale | `get_screenshot` |
| **Design variables** | CSS variables via `get_computed_styles` | Native variables via `get_variables`/`set_variables` |
| **Best for** | Prototyping, design-to-code, code-to-design | Complex design systems, multi-variant components, presentations |

## Heuristic

- **Primary goal is generating code from a visual**: Paper
- **Primary goal is building a reusable design system**: Pencil
- **Project already has `.pen` files**: Pencil for those files
- **Rapid prototype that will become code**: Paper
- **Need to import existing HTML/React into a design tool**: Paper
- **Presentation or slide deck**: Pencil
