# Skills (`skills/`)

Custom Claude Code capabilities organized by category. Each skill extends Claude with specialized workflows, tools, and domain knowledge.

## Installation

**Option A: Copy all skills**
```bash
cp -r skills/*/* ~/.claude/skills/
```

**Option B: Symlink individual skills**
```bash
ln -s "$(pwd)/skills/core-development/beads-task-tracker" ~/.claude/skills/beads-task-tracker
```

**Toggle skills on/off:**
```bash
./skills/skill-toggle.sh
```

## Categories

### Core Development (`core-development/`)
| Skill | Description |
|-------|-------------|
| `agents-md-manager` | Create and maintain [AGENTS.md](https://agentskills.io/) files and Codex CLI configuration (config.toml, .rules, .agents/skills/) |
| `architecture-md-builder` | ARCHITECTURE.md generation following [matklad's guidelines](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html) |
| `beads-task-tracker` | Dependency-aware task tracking with SQLite + JSONL sync |
| `claude-agent-sdk` | Build AI agents using the [Claude Agent SDK](https://docs.anthropic.com/en/docs/agents-and-tools/claude-agent-sdk) |
| `claude-md-manager` | CLAUDE.md creation using WHAT/WHY/HOW framework |
| `osgrep-reference` | [OSGrep](https://osgrep.app/) semantic code search reference |
| `react-best-practices` | React/Next.js optimization from [Vercel Engineering](https://vercel.com/blog) |
| `openrouter-usage` | Query OpenRouter API costs, credits, and usage by model/provider/date |
| `skill-optimizer` | Meta-skill for creating and reviewing other skills |

### Integration & Automation (`integration-automation/`)
| Skill | Description |
|-------|-------------|
| `agent-browser` | Browser automation via [Vercel agent-browser](https://github.com/AkshitIredworworwordy/agent-browser) CLI |
| `codex-orchestrator` | Orchestrate [OpenAI Codex CLI](https://github.com/openai/codex) with specialized subagents |
| `llama-cpp` | Local LLM inference via [llama.cpp](https://github.com/ggerganov/llama.cpp) with LoRA hot-loading |
| `beautiful-mermaid` | Mermaid diagrams as ASCII art via [beautiful-mermaid](https://github.com/nicepkg/beautiful-mermaid) |
| `parakeet` | Speech-to-text via [NVIDIA Parakeet](https://docs.nvidia.com/nemo/asr/models/parakeet.html) + [Handy](https://github.com/cjpais/Handy) |
| `rlama` | Local RAG via [RLAMA](https://github.com/dontizi/rlama) with Ollama |
| `Firecrawl` | Web scraping via [Firecrawl](https://firecrawl.dev/) CLI + Agent API |
| `exa-search` | Neural search via [Exa AI](https://exa.ai/) API |
| `twitter` | Twitter/X — search/research via x-search (official API v2), posting via OAuth 1.0a, reading via [bird CLI](https://github.com/steipete/bird) |
| `smolvlm` | Local vision-language via [SmolVLM](https://huggingface.co/HuggingFaceTB/SmolVLM-Instruct) on MLX |
| `speak-response` | Local TTS via [Qwen3-TTS](https://huggingface.co/Qwen/Qwen3-TTS) |
| `classical-887` | WRHV 88.7 FM (Classical WMHT) — now playing, playlist history, Markdown reports, Spotify playlist creation via [NPR Composer API](https://classicalwmht.org/playlist) |
| `slack` | [Slack](https://api.slack.com/) workspace integration — 7 on-demand scripts (post, read, search, react, upload, channels, users) + Session Bridge for connecting Claude Code sessions to Slack |
| `slack-respond` | Process unhandled Slack messages as [Claudicle](https://github.com/tdimino/claudicle) with persistent memory, cognitive pipeline, and soul state |
| `linkedin-export` | Parse LinkedIn GDPR data exports — search messages, analyze connections, export Markdown, ingest into RLAMA |

### Design & Media (`design-media/`)
| Skill | Description |
|-------|-------------|
| `minoan-frontend-design` | Production-grade UI creation with distinctive aesthetics (customized fork) |
| `gemini-claude-resonance` | Cross-model dialogue between Claude and [Gemini](https://deepmind.google/technologies/gemini/) |
| `nano-banana-pro` | Image generation via [Gemini 3 Pro](https://deepmind.google/technologies/gemini/) |
| `rocaille-shader` | Procedural shader generation for WebGL/GLSL |

### Research (`research/`)
| Skill | Description |
|-------|-------------|
| `academic-research` | Paper search via Exa + [ArXiv](https://arxiv.org/) |
| `exa-search` | Full [Exa AI](https://exa.ai/) API with 6 specialized scripts |
| `Firecrawl` | [Firecrawl](https://firecrawl.dev/) official CLI + Agent API |
| `linear-a-decipherment` | Computational [Linear A](https://en.wikipedia.org/wiki/Linear_A) analysis — [Gordon](https://en.wikipedia.org/wiki/Cyrus_H._Gordon) 5-step pipeline, cognate search, corpus statistics, sign analysis |

### Planning & Productivity (`planning-productivity/`)
| Skill | Description |
|-------|-------------|
| `claude-tracker-suite` | Session search, resume, project detection, resume-in-terminal (Ghostty/VS Code/Cursor) |
| `crypt-librarian` | Film curator for pre-2016 gothic/occult/noir cinema |
| `mdpreview` | Catppuccin live-reloading Markdown viewer with multi-tab support and margin annotations |
| `minoan-swarm` | Agent Teams orchestration with ancient Mediterranean naming |
| `super-ralph-wiggum` | Autonomous iteration loops based on [AI Hero's 11 Tips](https://www.aihero.dev/tips-for-ai-coding-with-ralph-wiggum) |

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
- **[Exa](https://exa.ai/)** — neural web search API
- **[Handy](https://github.com/cjpais/Handy)** by CJ Pais — push-to-talk speech-to-text
- **[ccstatusline](https://github.com/sirmalloc/ccstatusline)** by sirmalloc — terminal statusline for Claude Code
- **[beautiful-mermaid](https://github.com/nicepkg/beautiful-mermaid)** by Craft — Mermaid diagram rendering
- **[matklad's ARCHITECTURE.md](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html)** — the canonical guide for codebase documentation
- **[Open Souls](https://github.com/opensouls/opensouls)** — the AI souls paradigm that shapes our agent architecture
