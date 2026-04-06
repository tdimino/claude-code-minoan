# mesh3d.gallery — 3D Interactive Website Directory

Curated gallery of 207+ interactive WebGL/3D websites. Hand-picked by human curators. Filterable by tags, makers, and technology. Think Awwwards for 3D web experiences.

**URL**: https://mesh3d.gallery/
**LLM data endpoint**: https://mesh3d.gallery/llms-full.txt

## What It Contains

Each entry includes:
- Website title and URL
- Studio/maker name and website
- Description
- Technologies used (Three.js, WebGL, Spline, Rive, Babylon.js, GSAP, etc.)
- Tags (Interactive, Agency, Landing Page, Portfolio, Experiment, etc.)
- Featured/hero status
- Date added

## Top Makers (by entry count)

| Studio | Entries | Website |
|--------|---------|---------|
| Unseen Studio | 22 | unseen.co |
| PeachWeb | 15 | peachweb.io |
| Lusion | 13+ | lusion.co |
| Monopo | ~10 | monopo.co.jp |

## Technologies Tracked

Three.js, WebGL, Spline, Rive, Babylon.js, GSAP, WebGPU, Shader, Canvas

## Querying

Use the fetch script for structured queries:

```bash
# Fetch and cache the full directory
python3 ~/.claude/skills/component-gallery/scripts/fetch_mesh3d.py

# Filter by technology
python3 ~/.claude/skills/component-gallery/scripts/fetch_mesh3d.py --tech "Three.js"

# Filter by maker
python3 ~/.claude/skills/component-gallery/scripts/fetch_mesh3d.py --maker "Lusion"

# Search by keyword
python3 ~/.claude/skills/component-gallery/scripts/fetch_mesh3d.py --search "portfolio"
```

The `/llms-full.txt` endpoint is explicitly designed for LLM consumption — structured plain text with consistent field formatting.

## When to Use

- **Before building a 3D web experience** — see how top studios approach similar projects
- **For creative direction** — browse featured entries for interaction patterns and visual ideas
- **For technology selection** — see which technologies real projects use for specific effects
- **For studio discovery** — find studios specializing in specific types of 3D web work

## Relationship to component-gallery

component-gallery covers 2D UI component patterns across design systems. mesh3d.gallery extends this to the 3D/WebGL domain. Use component-gallery for structural UI patterns (buttons, modals, forms). Use mesh3d.gallery for 3D interaction patterns, WebGL visual techniques, and creative studio work.
