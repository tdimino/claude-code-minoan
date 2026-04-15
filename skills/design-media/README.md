# Design & Media Skills

Frontend design, image generation/editing, vision models, TTS, and visual effects.

## Design Workflow

The design skills form a composable pipeline: **shape** (plan) **minoan-frontend-design** (build) **design-audit** + **design-critique** (evaluate) **design-polish** (refine).

| Skill | Phase | Description |
|-------|-------|-------------|
| `shape` | Plan | Pre-code design brief through structured discovery interview. Produces `.design-context.md` with audience, brand personality, aesthetic direction, design dials (DESIGN_VARIANCE, MOTION_INTENSITY, VISUAL_DENSITY) |
| `minoan-frontend-design` | Build | Canonical frontend design skill: creative direction + engineering standards with eval infrastructure (70% win rate vs baseline in blind A/B). Context protocol, font reflex-reject procedure, OKLCH-first color, absolute CSS bans, 32 reference files |
| `design-audit` | Evaluate | Technical quality checks: 5 dimensions scored /20 (accessibility, performance, responsive, theming, anti-patterns). P0-P3 severity. Report-only |
| `design-critique` | Evaluate | UX review: Nielsen's 10 heuristics scored /40, cognitive load (8-item checklist), persona-based testing, AI Slop Test. Report-only |
| `design-polish` | Refine | Final quality pass: alignment, spacing, 8 interaction states per element, transitions, tinted neutrals, WCAG contrast, touch targets, code cleanup. The only design skill that makes changes |

### Lineage & Attribution

**minoan-frontend-design** descends from Anthropic's [frontend-design](https://github.com/anthropics/skills/tree/main/skills/frontend-design) skill. The creative philosophy (syncretic-v3) was developed through blind A/B eval testing, achieving 70% win rate at 907 words.

The satellite skills adapt patterns from [Impeccable](https://github.com/pbakaus/impeccable) by Paul Bakaus (Apache 2.0)—decomposed command architecture, font reflex-reject protocol, CSS-level anti-pattern bans, context gathering, dual-assessment critique. Additional references from [meodai/skill.color-expert](https://github.com/meodai/skill.color-expert), [Vercel Web Interface Guidelines](https://vercel.com/design), and [Linear's DESIGN.md](https://linear.app/design).

## Image & Media Skills

| Skill | Description |
|-------|-------------|
| `component-gallery` | Encyclopedic UI pattern research: 60 components, 95 design systems, 8,692 RAG chunks. Also: mesh3d.gallery (207 curated 3D/WebGL websites), Astryx hero pattern, fluid-dom pattern. Pairs with `minoan-frontend-design` |
| `gemini-claude-resonance` | Cross-model dialogue between Claude and Gemini with shared visual memory |
| `gemini-forge` | Frontend code drafts via Gemini 3.1 Pro — UI generation, screenshot-to-code, SVG animation |
| `image-well` | Multi-source image search: 12 APIs (Openverse, Pexels, Met, NASA, Wikimedia, etc.), presets, license filtering, download with metadata sidecars. `--format tunnel` bridge pipes results into the threejs-particle-canvas Mode 3 corridor |
| `image-forge` | Precision image editing: ImageMagick 7, rembg, sips, JSON pipelines |
| `meshy` | 3D model generation via Meshy API: text-to-3D, image-to-3D, texture, batch manifests |
| `nano-banana-pro` | Image generation/editing via Google Gemini 3 Pro |
| `paper-design` | Paper Design MCP: 21 tools for DOM-based design, React+Tailwind export via `get_jsx`, design-to-code/code-to-design workflows. Coexists with Pencil |
| `smolvlm` | Local vision-language model (SmolVLM-2B) for image analysis |
| `speak-response` | Local TTS using Qwen3-TTS with Oracle voice clone |

## Visual Effects & Typography

| Skill | Description |
|-------|-------------|
| `rocaille-shader` | Rocaille-style domain warping shaders, depth-parallax displacement heroes (Astryx), stable fluid simulations over live DOM (fluid-dom), and mouse-reactive liquid logo effects. 4 modes: `rocaille`, `liquid-logo`, `astryx-statue`, `fluid-dom` |
| `threejs-particle-canvas` | Interactive Three.js canvases in four modes: narrative particle phase cycles (Mode 1), WebGPU + TSL spinner/loaders (Mode 2, 9 curve types), infinite scrollable image tunnels (Mode 3), and behavior-driven glTF specimen scenes (Mode 4). Ships a shared Phosphor Vigil FX module |
| `pretext` | Text effects impossible with CSS alone — kinetic typography, calligrams, shrinkwrap bubbles, typographic ASCII art, glyph morphing, illuminated manuscripts. Uses `@chenglou/pretext` |
| `sprite-forge` | Game sprites, SVG characters, ASCII art (static + animated), animated mascots, isometric turnarounds — 5 output modes with chongdashu pipeline, video-to-spritesheet, Gemini SVG-as-code, GSAP animation |
| `grainient` | 16 composable dark-mode effects: WebGL2 aurora shader, vignette overlays, 9-layer box shadows, Lenis-style smooth scroll, spring animations, hover zoom, ticker marquee, glassmorphism, 3D card flip, bento grid, gradient CTAs. 5 modes, generator script, validator |
| `webgpu-threejs-tsl` | WebGPU reference skill for Three.js + TSL: renderer setup, node materials, compute shaders, post-processing, WGSL integration. Reference/learning — for generating scenes, use `threejs-particle-canvas`. Adopted from [dgreenheck/webgpu-claude-skill](https://github.com/dgreenheck/webgpu-claude-skill) |

## Component Libraries

| Skill | Description |
|-------|-------------|
| `shadcn` | Install, customize, compose shadcn/ui components with Tailwind v4 OKLCH theming |
| `mindnode-ui` | MindNode-inspired mind mapping interfaces (ReactFlow, D3, 27+ themes) |

## Recording & Presentation

| Skill | Description |
|-------|-------------|
| `recordly` | Screen recording polish (auto-zoom, cursor animations, webcam overlays) + Slant 3D perspective renderer (12 presets, HDRI reflections, DOF, MP4/GIF export). Open-source Screen Studio alternative |
