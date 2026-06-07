# Skills (`skills/`)

Custom Claude Code capabilities organized by category. Each skill extends Claude with specialized workflows, tools, and domain knowledge.

## Installation

**Option A: Copy all skills**
```bash
cp -r skills/*/* ~/.claude/skills/
```

**Option B: Symlink individual skills**
```bash
ln -s "$(pwd)/skills/core-development/stop-slop" ~/.claude/skills/stop-slop
```

**Toggle skills on/off:**
```bash
python3 ~/.claude/skills/skill-toggle/scripts/skill_toggle.py list
python3 ~/.claude/skills/skill-toggle/scripts/skill_toggle.py disable <skill-name>
python3 ~/.claude/skills/skill-toggle/scripts/skill_toggle.py enable <skill-name>
```

## Categories

### Core Development (`core-development/`)
| Skill | Description |
|-------|-------------|
| `agents-md-manager` | Create and maintain [AGENTS.md](https://agentskills.io/) files and Codex CLI configuration (config.toml, .rules, .agents/skills/) |
| `architecture-md-builder` | ARCHITECTURE.md generation following [matklad's guidelines](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html) |
| `claude-agent-sdk` | Build AI agents using the [Claude Agent SDK](https://docs.anthropic.com/en/docs/agents-and-tools/claude-agent-sdk) |
| `claude-md-manager` | CLAUDE.md creation using WHAT/WHY/HOW framework |
| `dag-typesafe` | Deterministic type safety for LLM pipelines via typed DAGs and [GraphSentry](https://arxiv.org/abs/2502.12345) certificates |
| `react-best-practices` | React/Next.js optimization from [Vercel Engineering](https://vercel.com/blog) |
| `openrouter-usage` | Query OpenRouter API costs, credits, and usage by model/provider/date |
| `glossary` | Domain glossary builder — creates `CONTEXT.md` with shared vocabulary, avoid-aliases, and term relationships. Adapted from [mattpocock/skills](https://github.com/mattpocock/skills) |
| `skill-optimizer` | Meta-skill for creating and reviewing other skills |

### Integration & Automation (`integration-automation/`)
| Skill | Description |
|-------|-------------|
| `agent-browser` | Browser automation via [Vercel agent-browser](https://github.com/AkshitIredworworwordy/agent-browser) CLI |
| `codex-cto` | [Codex CLI](https://github.com/openai/codex) as CTO: GPT-5.4-Pro plans, GPT-5.4 reviews, Claude Code executes |
| `codex-orchestrator` | Orchestrate [OpenAI Codex CLI](https://github.com/openai/codex) subagents (GPT-5.4/5.4-Pro) for review, debug, architect, security |
| `llama-cpp` | Local LLM inference via [llama.cpp](https://github.com/ggerganov/llama.cpp) with LoRA hot-loading |
| `beautiful-mermaid` | Mermaid diagrams as ASCII/Unicode art or SVG with 17 themes + custom colors via [beautiful-mermaid](https://github.com/nicepkg/beautiful-mermaid). Cross-skill integration for vellum-editorial, design-md, and project-specific palettes |
| `parakeet` | Speech-to-text via [NVIDIA Parakeet](https://docs.nvidia.com/nemo/asr/models/parakeet.html) + [Handy](https://github.com/cjpais/Handy) |
| `rlama` | Local RAG via [RLAMA](https://github.com/dontizi/rlama) with Ollama |
| `opencli` | Universal CLI for 80+ websites, desktop apps, browser automation via Chrome session reuse ([jackwener/opencli](https://github.com/jackwener/opencli)) |
| `twitter` | Twitter/X — search/research via x-search (official API v2), posting via OAuth 1.0a, reading via [bird CLI](https://github.com/steipete/bird) |
| `smolvlm` | Local vision-language via [SmolVLM](https://huggingface.co/HuggingFaceTB/SmolVLM-Instruct) on MLX |
| `speak-response` | Local TTS via [Qwen3-TTS](https://huggingface.co/Qwen/Qwen3-TTS) |
| `classical-887` | WRHV 88.7 FM (Classical WMHT) — now playing, playlist history, Markdown reports, Spotify playlist creation via [NPR Composer API](https://classicalwmht.org/playlist) |
| `disc-forge` | Burn Red Book audio CDs on macOS via [cdrdao](https://cdrdao.sourceforge.net/) with CD-Text from ID3 tags — works with USB burners `drutil` labels "Unsupported" |
| `resend` | Send email via [Resend](https://resend.com/) API — text, HTML, attachments, CC/BCC, stdin pipe, sender aliases |
| `slack` | [Slack](https://api.slack.com/) workspace integration — 7 on-demand scripts (post, read, search, react, upload, channels, users) + Session Bridge for connecting Claude Code sessions to Slack |
| `slack-respond` | Process unhandled Slack messages as [Claudicle](https://github.com/tdimino/claudicle) with persistent memory, cognitive pipeline, and soul state |
| `linkedin-export` | Parse LinkedIn GDPR data exports — search messages, analyze connections, export Markdown, ingest into RLAMA |

### Design & Media (`design-media/`)
| Skill | Description |
|-------|-------------|
| `minoan-frontend-design` | Eval-validated frontend design (70% vs baseline in blind A/B). Context protocol, font reflex-reject procedure, OKLCH-first color, absolute CSS bans. 32 reference files, progressive disclosure. |
| `shape` | Pre-code design brief through structured discovery interview. Produces `.design-context.md` with audience, brand personality, aesthetic direction, design dials. |
| `design-audit` | Technical quality checks: 5 dimensions scored /20 (a11y, performance, responsive, theming, anti-patterns). P0-P3 severity. Report-only. |
| `design-critique` | UX review: Nielsen's 10 heuristics scored /40, cognitive load, persona-based testing, AI Slop Test. Report-only. |
| `design-polish` | Final quality pass: alignment, spacing, 8 interaction states, transitions, WCAG contrast, code cleanup. Makes changes. |
| `gemini-claude-resonance` | Cross-model dialogue between Claude and [Gemini](https://deepmind.google/technologies/gemini/) |
| `nano-banana-pro` | Image generation via [Gemini 3 Pro](https://deepmind.google/technologies/gemini/) |
| `image-forge` | Precision image editing via [ImageMagick](https://imagemagick.org/) 7, sips, rembg, Pillow — JSON pipeline specs, batch ops, smart crop, montage builder |
| `pretext` | Text effects impossible with CSS — kinetic typography, flowing text around animated obstacles, calligrams, shrinkwrap bubbles, typographic ASCII art, glyph path animation, variable font waves, glyph morphing. Powered by [@chenglou/pretext](https://github.com/chenglou/pretext) + [opentype.js](https://opentype.js.org/). 10 templates, 5 references, validation script. |
| `rocaille-shader` | Procedural shader generation for WebGL/GLSL |
| `conductor-motion` | Behavioral animation patterns that simulate live software: typewriter/rotator, progress bars, file review state machines, stagger reveals, terminal displays, Lottie orchestration, workflow graphs. 8 modes, 10 references, validator. Distilled from [ConductorAI.com](https://www.conductorai.com/) |
| `grainient` | 16 composable dark-mode effects: WebGL2 aurora shader, vignette overlays, 9-layer box shadows, smooth scroll, spring animations, hover zoom, ticker marquee, glassmorphism, 3D card flip, bento grid, gradient CTAs. 5 modes, generator, validator |
| `particle-swarm-sim` | 20K+ particle swarm simulator: sandbox runtime (Three.js host, gesture OS, code injection, security validation) + behavior function bodies. AI writes only the math; runtime handles rendering. Distilled from [particles.casberry.in](https://particles.casberry.in/) |
| `threejs-particle-canvas` | Interactive Three.js particle canvases: narrative phase cycles, WebGPU spinners, infinite gallery tunnels, behavior-driven glTF specimens |
| `sprite-forge` | Game sprites, SVG characters, ASCII art, animated mascots, isometric turnarounds — 5 output modes |
| `webgpu-threejs-tsl` | WebGPU reference skill for [Three.js](https://threejs.org/) + [TSL](https://github.com/mrdoob/three.js/wiki/Three.js-Shading-Language): renderer setup, node materials, compute shaders, WGSL integration. Adopted from [dgreenheck/webgpu-claude-skill](https://github.com/dgreenheck/webgpu-claude-skill) |
| `scroll-cinema` | Cinematic scrolltelling: Lenis smooth scroll + GSAP ScrollTrigger + Three.js painted-texture shader backgrounds. 4 modes, 4 entrance patterns, 3 shader presets, OKLCH color transitions, 27-check validator |
| `atmosphere-shader` | Physically-based atmospheric scattering — sky domes, planetary atmospheres, LUT pipelines. 4 modes, 6 gotchas. Distilled from [Maxime Heckel](https://blog.maximeheckel.com/posts/on-rendering-the-sky-sunsets-and-planets/) |
| `tamarru` | Daimonic voice channeling — inhabit Tom di Mino's writing voice across prose, tweets, poetry, and technical docs. 8 registers, 14 sentence mechanics, 18 anti-patterns, 40 calibration quotes. Named for poem #86 in [Shirat Ha Kotharot](https://tomdimino.substack.com/) |

### Research (`research/`)
| Skill | Description |
|-------|-------------|
| `academic-research` | Paper search via Exa + [ArXiv](https://arxiv.org/) |
| `ancient-near-east-research` | Biblical Hebrew, Semitic linguistics, cuneiform, Minoan/Aegean archaeology — [Sefaria](https://www.sefaria.org/), CDLI/ORACC APIs + web discovery |
| `exa-search` | Neural search via [Exa AI](https://exa.ai/) — 5 specialized scripts, all API endpoints |
| `firecrawl` | Web scraping via [Firecrawl](https://firecrawl.dev/) v2 — JS rendering, site crawls, Agent API, Interact API |
| `geo-seo` | AI search visibility audit + artifact generator — 7-dimension scorecard (crawler access, discovery, schema, citability, SEO, entity signals, multi-engine), deployable llms.txt/schema/robots.txt, tailored by site type and scale. Grounded in [Princeton KDD 2024](https://arxiv.org/abs/2311.09735), [CMU ICLR 2026](https://arxiv.org/abs/2510.11438), and 6 more papers |
| `omnisearch` | Unified meta-router across 5 providers ([Brave](https://brave.com/search/api/), [Tavily](https://tavily.com/), [Xpoz](https://xpoz.ai/), Exa, Firecrawl) — auto-routing, parallel search with dedup, social media, AI answers |
| `openplanter` | Plant care monitoring and advice via [OpenPlanter](https://github.com/OpenPlanter) sensor data |
| `scrapling` | Local stealth web scraping: anti-bot bypass, Cloudflare solver, adaptive element tracking |
| `reverse-trace` | Reverse image/video source identification — chains [Google Vision](https://cloud.google.com/vision), [Picarta](https://picarta.ai/) geolocation, and [Gemini](https://ai.google.dev/) in parallel to trace TV shows, movies, locations |

### Planning & Productivity (`planning-productivity/`)
| Skill | Description |
|-------|-------------|
| `claude-tracker-suite` | Session search, resume, project detection, resume-in-terminal (Ghostty/VS Code/Cursor) |
| `crypt-librarian` | Film curator for pre-2016 gothic/occult/noir cinema |
| `minoan-swarm` | Agent Teams orchestration with ancient Mediterranean naming |
| `planning-with-files` | Structured planning with file-based plan artifacts |
| `skill-toggle` | Enable/disable skills and manage named collections — batch-toggle skill sets by project context |
| `super-ralph-wiggum` | Autonomous iteration loops based on [AI Hero's 11 Tips](https://www.aihero.dev/tips-for-ai-coding-with-ralph-wiggum) |
| `travel-requirements-expert` | Visa, passport, entry requirements research for international travel |

## Skill Structure

Every skill follows this layout:
```
skill-name/
├── SKILL.md          # Required — instructions loaded when skill is invoked
├── scripts/          # Optional — executable scripts
└── references/       # Optional — additional documentation
```

`SKILL.md` is the entry point. It tells Claude what the skill does, what tools/scripts are available, and how to use them.

## Credits & Inspiration

- **[Claude Code Skills](https://docs.anthropic.com/en/docs/claude-code/skills)** by Anthropic — the skills framework
- **[compound-engineering](https://github.com/every-ai-labs/compound-engineering)** by Every AI Labs — multi-agent review workflows
- **[feature-dev plugin](https://github.com/anthropics/claude-code)** by the Claude Code team — code-architect, code-explorer, code-reviewer agents
- **[super-ralph-wiggum](https://www.aihero.dev/tips-for-ai-coding-with-ralph-wiggum)** by AI Hero — autonomous iteration loop pattern
- **[llama.cpp](https://github.com/ggerganov/llama.cpp)** by Georgi Gerganov — local LLM inference engine
- **[RLAMA](https://github.com/dontizi/rlama)** by dontizi — local RAG system
- **[Firecrawl](https://firecrawl.dev/)** by Mendable — web scraping and content extraction
- **[Scrapling](https://github.com/D4Vinci/Scrapling)** by D4Vinci — local stealth web scraping
- **[Exa](https://exa.ai/)** — neural web search API
- **[Handy](https://github.com/cjpais/Handy)** by CJ Pais — push-to-talk speech-to-text
- **[ccstatusline](https://github.com/sirmalloc/ccstatusline)** by sirmalloc — terminal statusline for Claude Code
- **[beautiful-mermaid](https://github.com/nicepkg/beautiful-mermaid)** by Craft — Mermaid diagram rendering
- **[matklad's ARCHITECTURE.md](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html)** — the canonical guide for codebase documentation
- **[@chenglou/pretext](https://github.com/chenglou/pretext)** by Cheng Lou — DOM-free text measurement and layout (24.5K stars)
- **[opentype.js](https://opentype.js.org/)** — JavaScript font parser for per-glyph SVG path rendering
- **[flubber](https://github.com/veltman/flubber)** by Noah Veltman — SVG shape morphing for glyph interpolation
- **[Impeccable](https://github.com/pbakaus/impeccable)** by Paul Bakaus — decomposed design command architecture, font reflex-reject protocol, CSS anti-pattern bans
- **[meodai/skill.color-expert](https://github.com/meodai/skill.color-expert)** — color science, OKLCH decision matrices, palette generation
- **[Matt Pocock's Skills](https://github.com/mattpocock/skills)** — `CONTEXT.md` ubiquitous language convention, `/grill-with-docs` pattern
- **[Open Souls](https://github.com/opensouls/opensouls)** — the AI souls paradigm that shapes our agent architecture
- **[webgpu-claude-skill](https://github.com/dgreenheck/webgpu-claude-skill)** by Dan Greenheck — Three.js WebGPU + TSL reference skill
