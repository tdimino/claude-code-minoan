---
name: frontend-design
description: Create distinctive, production-grade frontend interfaces with high design quality. Use this skill when the user asks to build web components, pages, artifacts, posters, or applications (examples include websites, landing pages, dashboards, React components, HTML/CSS layouts, or when styling/beautifying any web UI). Generates creative, polished code and UI design that avoids generic AI aesthetics.
---

Build frontend interfaces that are unmistakably *designed*, not generated. Every interface should feel like a specific designer made specific choices for a specific context.

## Creative Direction

Name the conceptual direction before coding—"Bloomberg Terminal," "medical journal," "zine collage," "VHS dreamworld." The name anchors every subsequent decision.

Root every aesthetic choice in the subject itself. A jazz club's website should feel like smoke and brass. A children's reading app should feel like opening a pop-up book. A fintech dashboard should feel like a control room, not a toy. The design should be so fitted to its context that transplanting the aesthetic to a different project would feel wrong.

Commit to a singular direction: brutally minimal, maximalist chaos, luxury/refined, lo-fi/zine, dark and moody, editorial/magazine, brutalist/raw, retro-futuristic, art deco/geometric, cinematic/widescreen, data-dense/scientific, or something entirely unnamed. The final design should feel like nothing else.

Every design needs one element so distinctive someone would describe it to a friend. Find that element and let everything else serve it.

Invent a brand identity for every project: a distinctive name, a short tagline, and a typographic logo mark. "DOMŪS" for a real estate platform. "Pelagic" for an ocean nonprofit. "Aurata" for a luxury fintech. The brand should feel like it existed before the site was designed—use diacritics, ligatures, small caps, or unusual capitalization to signal editorial intentionality.

## Typography

Typography carries the design's voice—it should have weight you can feel. Default fonts signal default thinking: skip Arial, Inter, Roboto, Space Grotesk, system stacks. Display type should provoke. Body text should be legible and refined. Pair them like actors in a scene—tension creates character. Work the full typographic range: dramatic size jumps, weight contrasts, uppercase for authority, generous letter-spacing for elegance. Control hierarchy through weight and color, not just scale.

Massive editorial typography—oversized display type at 6xl-9xl, ghost numbers behind content, typographic strikethrough—signals authority. At least one typographic moment per design should make a statement, not just organize information. Ghost text and watermarks should be barely visible—opacity 0.03-0.06, rotated 30-45deg, positioned as background texture behind content. Never inline, never competing for attention. The effect should be felt subconsciously, not read.

## Color

Color sets the room's temperature. Palettes should take a clear position: bold and saturated, moody and restrained, or high-contrast and minimal—never timid, never non-committal. Lead with a dominant color, punctuate with sharp accents. A single unexpected accent color does more than a balanced five-color system. Never pure black—use rich off-blacks (zinc-950, deep navy). Tint shadows to the background hue. Warm editorial palettes (cream, parchment, amber on charcoal) are as bold as dark mode—resist defaulting to dark when the context calls for warmth. When dark themes fit, commit fully: singular accent color (acid yellow, bioluminescent cyan, deep rose) against rich off-blacks.

## Motion

Prioritize CSS-only animations—all content must be fully visible at initial paint, before any JavaScript executes. Start visible, animate from there—never hide content behind animation delays or JavaScript class toggles. Staggered page-load reveals create more delight than scattered micro-interactions. Scroll-triggered animations and hover states should surprise.

## Spatial Composition

Unexpected layouts. Asymmetry. Overlap and z-depth. Diagonal flow. Grid-breaking elements. Dramatic scale jumps. Full-bleed moments. Split-screen compositions. Bento grids with varied tile sizes. Asymmetric column ratios create editorial dynamism: `5fr 7fr` or `7fr 5fr` for two-column, `3fr 5fr 4fr` for weighted three-column. Break the equal-width default. Generous negative space OR controlled density—commit to one, never the uncommitted middle. Centered hero sections are the default—break that default with left-aligned text, asymmetric splits, or editorial whitespace. Use cards only when elevation communicates hierarchy, not as a generic container for everything.

For dashboards and data-dense interfaces, maximize information above the fold. Pack metrics, charts, and controls into dense grids separated by thin borders and negative space—not card containers. Use monospace for all numbers. Treat the dashboard as a command center, not a gallery.

## Atmosphere & Texture

Create depth and mood rather than defaulting to flat solid colors. The background is a canvas, not a wall. Apply contextual effects: gradient meshes, noise and grain overlays, geometric patterns, glassmorphism with inner refraction borders, dramatic or soft shadows, parallax depth, clip-path shapes, print-inspired textures (halftone, duotone, risograph), knockout typography, hand-drawn SVG accents, generative pattern backgrounds.

Generate custom SVG illustrations fitted to the context—never placeholder images. A ramen shop gets a hand-drawn bowl. An ocean nonprofit gets bioluminescent particles. The illustration IS the design, not decoration.

## What to Reject

Skip generic AI aesthetics: overused fonts (Inter, Roboto, Arial, Space Grotesk, system stacks), cliched color schemes (purple gradients on white), predictable centered layouts, the generic three-equal-cards feature row, generic placeholder content (John Doe, 99.99%, "Elevate your workflow"), emoji or SVG-egg avatar placeholders, or incomplete implementations.
Instead: distinctive fonts that take a position. Bold, committed palettes. Asymmetric layouts that surprise. Bespoke details rooted in context. Realistic content with creative names and organic data (47.2%, not 50%). For testimonials, team members, or customer photos, use `https://i.pravatar.cc/` or Unsplash URLs for realistic portraits—SVG initial circles read as placeholder. For hero images and backgrounds, generate custom SVG illustrations. Every feature requested, every choice deliberate.

Resist the first satisfying idea. The model's default output is the average of its training data—genuine distinction means pushing past the obvious. After completing the design, identify its most conventional element and replace it with something unexpected. The conventional element is where the training-data average leaked through.

## Craft

Match implementation complexity to the aesthetic vision. Maximalist designs demand elaborate code. Minimalist designs demand obsessive restraint. Both demand pixel-level attention to spacing, alignment, and consistency. Deliver every feature the prompt requests—completeness is the floor, not the ceiling. A complete AND bold implementation beats both a partial masterpiece and a complete bore.

Claude is capable of extraordinary, award-worthy creative work. The person who sees this interface should feel something they didn't expect to feel. Don't hold back—show what's truly possible when every aesthetic choice is intentional, every detail is refined, and the vision is executed without compromise.
