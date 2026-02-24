# gemini-forge

Frontend code generation via Gemini 3.1 Pro—React, HTML/CSS, SVG animation, screenshot-to-code. Produces fast, cheap drafts that Claude reviews and refines.

## Setup

```bash
export GEMINI_API_KEY="your-key-here"  # https://aistudio.google.com/apikey
pip install requests  # only dependency
```

## Scripts

| Script | Purpose |
|--------|---------|
| `generate_ui.py` | React/HTML/Tailwind generation from prompt |
| `screenshot_to_code.py` | Describe-first screenshot→spec→code pipeline |
| `generate_svg.py` | SVG animation: animate, create, physics, logo |
| `load_design_system.py` | Bundle design tokens into the 1M context window |
| `gemini_text.py` | Shared REST client (auth, backoff, thinking config) |

## Usage

```bash
# Generate a React component
python scripts/generate_ui.py "dark dashboard with metrics" --mode react --thinking medium

# Multi-file app
python scripts/generate_ui.py "SaaS pricing page" --mode react --thinking high --app

# Screenshot to code (full pipeline)
python scripts/screenshot_to_code.py screenshot.png --framework react

# Screenshot to code (inspect spec first)
python scripts/screenshot_to_code.py screenshot.png --analyze-only
python scripts/screenshot_to_code.py --from-spec output/spec_*.md --framework react

# SVG animation
python scripts/generate_svg.py --mode create --description "orbiting dots with spring connections"
python scripts/generate_svg.py --mode animate logo.svg --description "draw-on stroke, 1.2s"
python scripts/generate_svg.py --mode physics --description "particle system, 20 nodes"
python scripts/generate_svg.py --mode logo --description "double-axe labrys, slow rotation"

# Design system context loading
python scripts/load_design_system.py --tokens tokens.css --brief brand.md --output context.txt
python scripts/generate_ui.py "hero section" --design-context context.txt
```

## Thinking Levels

| Level | Budget | Use Case |
|-------|--------|----------|
| low | 1,024 tokens | Single components, simple pages |
| medium | 8,192 tokens | Multi-component layouts, dashboards |
| high | 32,768 tokens | Full apps, complex state, SVG physics |

## Model

- **ID**: `gemini-3.1-pro-preview`
- **Type**: Text-only reasoning (no image generation)
- **Context**: 1M input, 64K output
- **Pricing**: $2/$12 per MTok (under 200K), $4/$18 (over 200K)
- **Auth**: `GEMINI_API_KEY` env var, same key as nano-banana-pro

## Workflow

Gemini drafts at $2/MTok. Claude polishes at $15/MTok:

1. Run a gemini-forge script → output to `./output/`
2. Claude reads the generated file
3. Claude applies minoan-frontend-creative (aesthetics) + minoan-frontend-engineering (production standards)
4. Claude writes the polished output to the project

## Screenshot-to-Code Pipeline

Two-step describe-first approach prevents layout hallucination:

1. **Analyze**: Gemini describes the screenshot as a structured technical spec (layout, components, colors, typography, spacing)
2. **Generate**: Gemini implements the spec as code—grounded in verified text, not the image directly

Use `--analyze-only` to inspect and correct the spec before generation.
