# Pellicola Anti-Patterns

## 1. White background

**Wrong:** `background: #FFFFFF` or `background: white`
**Right:** `background: var(--pel-cream)`. White kills the analog warmth. The cream hue (oklch 97.5% 0.012 85) is the foundation of pellicola's visual identity.

## 2. Card containers for credits

**Wrong:** Credit names in cards with `box-shadow`, `border-radius`, `padding` — looks like a team page, not film credits.
**Right:** Bordered grid cells with `border: 1px solid var(--pel-border)`. Role in tracked small caps, name in display serif. No shadows, no card elevation.

## 3. Avatar circles for director

**Wrong:** `border-radius: 50%; width: 80px` headshot circle — looks like a social profile.
**Right:** Cropped photographic portrait at `aspect-ratio: 3/4` with dark gradient overlay and display serif name. The director card is cinematic, not a profile widget.

## 4. Default fonts

**Wrong:** Inter, Roboto, Arial, Open Sans, Lato, Montserrat, system-ui, or any of the reflex-reject list.
**Right:** Display serif must be dramatic (Playfair Display, Cormorant Garamond). Body sans must be geometric and specific (DM Sans, Outfit). Follow `minoan-frontend-design` font reflex-reject procedure.

## 5. Page-load animations without IntersectionObserver

**Wrong:** All elements animate on `DOMContentLoaded` — everything moves at once, nothing is choreographed.
**Right:** All `data-pel` reveals trigger via IntersectionObserver as elements enter the viewport. The only exception: the hero title, which animates on load because it's immediately visible.

## 6. Red accent for non-play-button elements

**Wrong:** `--pel-red` on headings, borders, links, section backgrounds, badges, hover states.
**Right:** `--pel-red` is exclusively for the play button circle and play icon. One accent, one purpose. Additional color comes from the film's own imagery.

## 7. Missing `prefers-reduced-motion`

**Wrong:** `data-pel` animations fire regardless of user preference.
**Right:** All animated elements have a `prefers-reduced-motion: reduce` override that sets `opacity: 1`, `transform: none`, `transition: none`. JS parallax checks the media query before attaching scroll listeners.

## 8. Height transitions for panels

**Wrong:** `transition: height 0.4s ease` — requires JS to measure content height, breaks with dynamic content.
**Right:** `grid-template-rows: 0fr` → `1fr` for accordion/dropdown reveals. CSS Grid handles unknown content heights natively.

## 9. All-dark page

**Wrong:** `body { background: #000; color: #fff; }` — this is grainient's territory.
**Right:** Body background is `--pel-cream`. The dark gallery is one section within a cream page. The palette rhythm is cream → dark → cream, once. For all-dark designs, use `grainient` instead.

## 10. Broken section sequence

**Wrong:** Gallery before credits, prizes before gallery, or any arbitrary ordering.
**Right:** Canonical sequence is hero → credits → footage/gallery → prizes → investors → next-project. Sections can be omitted, but the order is fixed. This matches film industry convention: you see the title, then who made it, then what it looks like, then who recognized it.
