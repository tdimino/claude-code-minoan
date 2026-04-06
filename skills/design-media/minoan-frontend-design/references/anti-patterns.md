# Anti-Patterns & Technical Standards

Condensed from Impeccable (pbakaus/impeccable v1.6.0) domain references. Use this as a checklist to catch common mistakes after building.

## AI Slop Tells

These patterns signal AI-generated design. Avoid all of them:
- **Fonts**: Inter, Roboto, Arial, Open Sans, Lato, Montserrat. Better alternatives: Instrument Sans, Plus Jakarta Sans, Outfit, Onest, Figtree, Fraunces, Newsreader
- **Color**: Purple gradients on white, cyan/neon on dark, gradient text on headings/metrics, glowing accents, generic glassmorphism
- **Layout**: Three equal feature cards, hero metric template (big number + subtitle + icon), everything centered, cards wrapping everything, cards nested inside cards, modals for everything (modals are lazy — use inline or progressive disclosure), rounded rectangles with generic drop shadows
- **Motion**: Bounce/elastic easing (tacky since ~2015), overshoot effects
- **Content**: "Elevate your workflow," John Doe, 99.99%, emoji avatars, SVG-egg placeholders, repeating the same information (redundant headers, intros that restate the heading)
- **Decoration**: Large icons with rounded corners above every heading (templated look), rounded elements with thick colored border on one side (lazy accent), sparklines as decoration (look sophisticated, convey nothing), monospace typography as lazy shorthand for "technical/developer" vibes
- **Hierarchy**: Making every button primary — use ghost buttons, text links, secondary styles; hierarchy matters
- **Portfolio sites**:
  - Three-column card grid for portfolio items — use timeline lists or logo grids
  - Gradient CTA buttons on personal sites — use text-only CTAs
  - Stock hero image behind name — let typography be the hero
  - "Skills" section with progress bars
  - Animated statistics counters

## Typography

- **Vertical rhythm**: Line-height is the base unit for ALL vertical spacing. If body is `line-height: 1.5` on 16px (=24px), spacing should be multiples of 24px
- **Modular scale**: Use 5 sizes with clear contrast, not 14/15/16/18 muddy steps. Ratios: 1.25 (major third), 1.333 (perfect fourth), 1.5 (perfect fifth)
- **Measure**: `max-width: 65ch` for body text. Increase line-height (+0.05-0.1) for light-on-dark
- **Font loading**: Use `font-display: swap` + size-adjust fallback metrics to prevent layout shift
- **OpenType**: `tabular-nums` for data tables, `diagonal-fractions` for recipes, `all-small-caps` for abbreviations
- **Accessibility**: Never `user-scalable=no`. Use rem/em not px for body. Minimum 16px body. 44px+ tap targets on text links

## Color & Contrast

- **Use OKLCH, not HSL**. OKLCH is perceptually uniform—equal lightness steps look equal. Reduce chroma as you approach white/black (high chroma at extreme lightness looks garish)
- **Tinted neutrals**: Pure gray is dead. Add chroma 0.01 of your brand hue to all neutrals: `oklch(95% 0.01 250)` for cool, `oklch(95% 0.01 60)` for warm
- **Pure black (#000)**: Never for backgrounds or text. Use rich off-blacks with subtle hue tint
- **Gray text on color**: Always fails readability. Use a darker shade of the background color instead
- **60-30-10 rule**: 60% neutral, 30% secondary, 10% accent. Overusing accent kills its power
- **Alpha transparency**: Heavy use = incomplete palette. Define explicit overlay colors instead
- **WCAG**: Body text 4.5:1, large text 3:1, UI components 3:1. Placeholders need 4.5:1 too
- **Dark mode**: Not inverted light mode. Use lighter surfaces for depth (no shadows), desaturate accents, reduce font weight, never pure black backgrounds (use oklch 12-18%)

## Spacing & Layout

- **4pt base, not 8pt**: 8pt is too coarse—you frequently need 12px. Scale: 4, 8, 12, 16, 24, 32, 48, 64, 96px
- **Semantic token names**: `--space-sm` not `--spacing-8`. Use `gap` over margins for sibling spacing
- **Self-adjusting grid**: `repeat(auto-fit, minmax(280px, 1fr))` for responsive grids without breakpoints
- **The squint test**: Blur your eyes—can you identify the #1 element, #2, and clear groupings? If everything looks same-weight, hierarchy problem
- **Cards are not required**: Spacing and alignment create grouping naturally. Use cards only for distinct actionable items or visual comparison grids. Never nest cards
- **Container queries**: Use for components (`container-type: inline-size`), viewport queries for page layout
- **Optical alignment**: Text at `margin-left: 0` looks indented—use `-0.05em` negative margin. Play icons shift right
- **Z-index**: Semantic scale (dropdown < sticky < modal-backdrop < modal < toast < tooltip), not arbitrary numbers

## Motion

- **100/300/500 rule**: 100-150ms for instant feedback (button, toggle). 200-300ms for state changes (menu, tooltip). 300-500ms for layout (accordion, modal). 500-800ms for entrances (page load, hero). Exits = 75% of entrance duration
- **Easing**: Never use `ease` (it's a compromise). Use `ease-out` (entering), `ease-in` (leaving), `ease-in-out` (toggles). Recommended default: `cubic-bezier(0.25, 1, 0.5, 1)` (quart-out)
- **Bounce/elastic**: Avoid. Real objects decelerate smoothly. Overshoot draws attention to animation, not content
- **Only animate `transform` and `opacity`**—everything else causes layout recalculation. For height: `grid-template-rows: 0fr` to `1fr`
- **Stagger cap**: `animation-delay: calc(var(--i) * 50ms)`. Cap total stagger at ~500ms
- **Reduced motion**: Not optional. `@media (prefers-reduced-motion: reduce)` — crossfade instead of spatial movement. Preserve functional animations (progress, spinners)
- **Perceived performance**: 80ms threshold feels instant. Optimistic UI for low-stakes actions. Ease-in toward completion compresses perceived time

## Interaction

- **Eight states**: Default, hover, focus, active, disabled, loading, error, success. Every interactive element needs all eight designed
- **Focus rings**: Never `outline: none` without replacement. Use `:focus-visible` for keyboard-only rings. 2-3px, offset, 3:1 contrast minimum
- **Placeholders are not labels**: They disappear on input. Always use visible `<label>` elements
- **Validate on blur**, not every keystroke (exception: password strength)
- **Errors below fields** with `aria-describedby` connecting them
- **Modals**: Use `<dialog>` element or `inert` attribute for focus trapping. `dialog.showModal()` handles Escape, backdrop, focus trap
- **Popovers**: Use native `popover` attribute for tooltips/dropdowns—light-dismiss, proper stacking, no z-index wars
- **Destructive actions**: Undo > confirmation dialogs (users click through confirmations mindlessly)
- **Roving tabindex**: For component groups (tabs, menus), one item tabbable, arrow keys move within

## Responsive

- **Mobile-first**: Base styles for mobile, `min-width` queries to layer up. Desktop-first means mobile loads unnecessary styles
- **Content-driven breakpoints**: Don't chase device sizes. Stretch until design breaks, add breakpoint there. Three usually suffice (640, 768, 1024px)
- **Pointer/hover queries**: `@media (pointer: coarse)` for larger touch targets, `@media (hover: none)` to skip hover states. Screen size doesn't tell you input method
- **Safe areas**: `padding: env(safe-area-inset-*)` with `viewport-fit=cover` for notches and home indicators
- **Images**: `srcset` with width descriptors + `sizes` attribute. `<picture>` for art direction (different crops, not just resolution)
- **Test on real devices**: DevTools misses touch interactions, CPU constraints, font rendering, keyboard appearances

## UX Writing

- **Button labels**: Never "OK," "Submit," "Yes/No," "Click here." Use verb + object: "Save changes," "Create account," "Delete message"
- **Destructive buttons**: "Delete" not "Remove" (delete = permanent, remove = recoverable). Show count: "Delete 5 items"
- **Error formula**: What happened + why + how to fix. "Email needs an @ symbol" not "Invalid input"
- **Don't blame users**: "Please enter a date in MM/DD/YYYY format" not "You entered an invalid date"
- **Empty states**: Acknowledge briefly, explain value, provide action. "No projects yet. Create your first one to get started."
- **Terminology consistency**: Pick one and enforce it. Delete/Remove/Trash = just Delete. Settings/Preferences/Options = just Settings
- **Translation**: German +30%, French +20%, Finnish +30-40%. Keep numbers separate, use full sentences, avoid abbreviations
- **Link text**: Standalone meaning—"View pricing plans" not "Click here." Alt text describes information, not the image
