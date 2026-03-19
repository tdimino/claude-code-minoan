## Reading Tools (11)

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `get_basic_info` | File name, page name, node count, artboard list with dimensions | First call — orient to the document |
| `get_selection` | Details about currently selected nodes (IDs, names, types, size) | User says "this element" or "the selected thing" |
| `get_node_info` | Full properties of a node by ID (size, visibility, lock, parent, children, text) | Inspect a specific element before modifying |
| `get_children` | Direct children of a node (IDs, names, types, child counts) | Explore structure without full tree overhead |
| `get_tree_summary` | Compact text summary of a subtree hierarchy (optional depth limit) | Understand document or artboard structure at a glance |
| `get_screenshot` | Screenshot of a node by ID (base64 image; 1x or 2x scale) | Verify visual results after any write operation |
| `get_jsx` | JSX for a node and descendants (Tailwind or inline-styles format) | Export design to React code — the primary design-to-code tool |
| `get_computed_styles` | Resolved CSS styles for one or more nodes (batch) | Extract design tokens (colors, spacing, typography) |
| `get_fill_image` | Image data from a node with an image fill (base64 JPEG) | Extract images from designs |
| `get_font_family_info` | Font availability (user's machine or Google Fonts); weights and styles | Verify fonts before shipping code |
| `get_guide` | Paper's built-in workflow guides for specific topics | Learn Paper-recommended approaches (e.g., figma-import) |

## Writing Tools (7)

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `create_artboard` | New artboard with optional name and styles (width, height) | Start a new design; always create before writing HTML |
| `write_html` | Parse HTML and add/replace nodes — pass mode explicitly: `insert-children` (append) or `replace` (overwrite) | Primary creation tool — write semantic HTML with inline styles or Tailwind |
| `set_text_content` | Set text content of one or more Text nodes (batch) | Text-only updates without structural changes |
| `rename_nodes` | Rename one or more layers (batch) | Organize layer names for clarity |
| `duplicate_nodes` | Deep-clone nodes; returns new IDs and descendant ID map | Create responsive variants (clone desktop → resize to mobile) |
| `update_styles` | Update CSS styles on one or more nodes | Targeted style changes without rewriting HTML |
| `delete_nodes` | Delete one or more nodes and all descendants | Remove elements |

## Workflow Tools (3)

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `find_placement` | Suggested x/y for new artboard without overlap | Before `create_artboard` to avoid overlap with existing work |
| `start_working_on_nodes` | Mark artboards as being worked on (shows indicator) | Before any multi-step modification — locks the user out |
| `finish_working_on_nodes` | Clear the working indicator | After modifications complete — always pair with start |

## Common Artboard Sizes

| Name | Width | Height |
|------|-------|--------|
| Desktop | 1440 | 900 |
| Laptop | 1280 | 800 |
| Tablet | 768 | 1024 |
| Mobile | 375 | 812 |

## Gotchas

**`write_html` replaces entire node content.** To update part of a design, target a specific child node by ID, not the artboard root. Use `get_children` to find the right target.

**`get_jsx` outputs Tailwind classes.** If the project uses plain CSS or a different framework, post-process the output. The JSX is production-quality but framework-specific.

**Always `get_screenshot` after writing.** DOM structure can be correct while the visual result is wrong (overlapping elements, invisible text, broken layout). Visual verification catches what structural checks miss.

**`start/finish_working_on_nodes` are locks.** `start` prevents the user from editing those nodes in the Paper UI. Forgetting `finish` locks the user out until the next session. Always call `finish` — even if an error occurs mid-workflow.

**Long sessions can drop MCP connection.** If tools start failing with connection errors, the fix is to restart the Claude Code session. The Paper Desktop app itself stays running.

**`write_html` mode matters.** It supports `insert-children` (append into existing node) and `replace` (overwrite node content). Default to `replace` for full-page writes, `insert-children` for adding elements to an existing layout.

**Image fills are JPEG.** `get_fill_image` returns base64-encoded JPEG regardless of the original format. Plan for lossy compression when extracting images.

**Artboard dimensions constrain layout.** A 1440x900 artboard with mobile-width content renders with excess whitespace. Match artboard size to the target viewport before writing HTML — wrong dimensions produce wrong layouts even if the HTML is structurally correct.

**Image paths must be translated from relative to absolute.** Paper may reference images as `./images/file.png`; code requires `/images/file.png`. Always translate when extracting or syncing design-to-code.

**Tailwind class support scope is unknown.** Paper renders HTML/CSS in its own viewport, which may not include all Tailwind utilities. Stick to common layout and typography classes. If a design renders incorrectly, check whether the specific Tailwind class is supported by calling `get_screenshot` to verify. When in doubt, use inline styles instead of obscure Tailwind utilities.
