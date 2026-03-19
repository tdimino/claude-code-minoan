## 1. New Design from Brief

Start from a text description or requirements and create a full design.

1. `get_guide("responsive")` — learn Paper's recommended responsive patterns
2. `find_placement` — find empty canvas space
3. `create_artboard` with name and dimensions (e.g., "Homepage Desktop", 1440x900)
4. `start_working_on_nodes` on the new artboard
5. `write_html` with full page HTML — use semantic elements, flexbox layout, inline styles or Tailwind
6. `finish_working_on_nodes`
7. `get_screenshot` — verify the result visually
8. Iterate: `start_working_on_nodes` → `update_styles` or `write_html` → `finish_working_on_nodes` → `get_screenshot`

## 2. Extract Code from Design

Convert an existing Paper design into React/Tailwind code.

1. `get_selection` or `get_node_info` — identify the target node
2. `get_jsx` — export as React + Tailwind JSX
3. `get_computed_styles` — extract design tokens (colors, spacing, font sizes)
4. `get_font_family_info` — verify fonts are available for the target environment
5. `get_fill_image` — extract any images used in the design
6. Assemble into a React component, mapping Paper tokens to the project's design system

## 3. Import Existing Component

Bring an existing React component into Paper for visual iteration.

1. Convert JSX to an HTML string (strip React-specific syntax, expand component references)
2. `find_placement` — find canvas space
3. `create_artboard` sized to match the component's viewport
4. `write_html` with the converted HTML
5. `get_screenshot` — verify it renders correctly in Paper
6. Iterate visually in Paper, then re-export via `get_jsx` when done

## 4. Responsive Variants

Create tablet and mobile versions of an existing desktop design.

1. `get_node_info` on the desktop artboard — note its ID and dimensions
2. `duplicate_nodes` — clone the artboard; save the new artboard ID from the response
3. `rename_nodes` — rename to "Homepage Tablet" (or similar)
4. `update_styles` — resize to 768x1024
5. `start_working_on_nodes` on the new artboard
6. `write_html` — adjust layout for tablet (stack columns, resize typography)
7. `finish_working_on_nodes`
8. `get_screenshot` — verify
9. Repeat for mobile (375x812)

## 5. Design Token Sync

Extract or apply design tokens between Paper and code.

**Paper → Code:**
1. `get_computed_styles` on key elements (buttons, headings, cards, backgrounds)
2. Extract color values, spacing, border-radius, font sizes, line heights
3. Write to project's CSS variables, Tailwind config, or shadcn OKLCH theme

**Code → Paper:**
1. Read the project's CSS variables or Tailwind config
2. `start_working_on_nodes` on target elements
3. `update_styles` to apply token values
4. `finish_working_on_nodes`
5. `get_screenshot` — verify tokens render correctly

## 6. Iterative Refinement

Tight feedback loop for polishing a design.

1. `get_screenshot` — assess current state
2. Identify what needs to change (layout, colors, spacing, typography)
3. `start_working_on_nodes` on affected artboards
4. For structural changes: `write_html` on the specific child node
5. For style tweaks: `update_styles` with targeted CSS properties
6. For text updates: `set_text_content`
7. `finish_working_on_nodes`
8. `get_screenshot` — verify improvement
9. Repeat until satisfied
