<p align="center">
  <img src="public/images/tanit.svg" alt="Symbol of Tanit" width="80"/>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/Version-1.0.0-blue.svg" alt="Version"></a>
  <a href="#available-skills"><img src="https://img.shields.io/badge/Skills-34-green.svg" alt="Skills"></a>
  <a href="#all-slash-commands"><img src="https://img.shields.io/badge/Commands-30+-purple.svg" alt="Commands"></a>
</p>

# Minoan Claude Code Configuration

Curated Claude Code configuration including skills, MCP servers, and slash commands for professional development workflows.

<p align="center">
  <img src="public/images/be_minoan.jpg" alt="Minoan fresco - Cross-model resonance" width="600"/>
</p>

## Repository Contents

```
claude-code-minoan/
├── .mcp.json                    # MCP server configurations
├── bin/                         # CLI tools (copy to ~/.local/bin/)
│   ├── cc                       # Quick Claude Code launcher
│   ├── cckill                   # Kill Claude Code processes
│   ├── ccls                     # List Claude Code sessions
│   ├── ccpick                   # Interactive session picker
│   ├── claude-tmux-status       # Tmux statusline integration
│   ├── claude-tracker           # Session listing & crash recovery
│   ├── claude-tracker-resume    # Find & resume crashed sessions in tmux
│   └── claude-tracker-search    # Search sessions by summary/content/ID
├── lib/                         # Shared libraries (copy to ~/.claude/lib/)
│   └── tracker-utils.js         # Session parsing, path decoding, status detection
├── extensions/                  # VS Code extensions
│   └── claude-session-tracker/  # Track & resume Claude sessions across windows
├── skills/                      # Custom Claude Code skills
│   ├── core-development/        # Core development tools
│   │   ├── architecture-md-builder/ # ARCHITECTURE.md codebase documentation
│   │   ├── beads-task-tracker/      # Dependency-aware task tracking
│   │   ├── claude-agent-sdk/        # Build AI agents with Claude Agent SDK
│   │   ├── claude-md-manager/       # CLAUDE.md creation and optimization
│   │   ├── osgrep-reference/        # Semantic code search
│   │   ├── react-best-practices/    # React/Next.js performance optimization
│   │   └── skill-optimizer/         # Guide for creating and reviewing skills
│   ├── integration-automation/  # Infrastructure & integrations
│   │   ├── agent-browser/            # Browser automation using Vercel CLI
│   │   ├── codex-orchestrator/       # ⭐ Orchestrate Codex CLI with specialized subagents
│   │   ├── figma-mcp/               # Figma design integration
│   │   ├── mcp-server-manager/      # MCP server configuration
│   │   ├── netlify-integration/     # Netlify deployment management
│   │   ├── llama-cpp/               # ⭐ Secondary LLM inference with llama.cpp
│   │   ├── beautiful-mermaid/       # ⭐ NEW - Mermaid diagrams as ASCII art or SVG
│   │   ├── parakeet/                # Local speech-to-text with NVIDIA Parakeet TDT
│   │   ├── rlama/                   # ⭐ Local RAG system for semantic document search
│   │   ├── supabase-skill/          # Supabase project management
│   │   ├── telnyx-api/              # Telnyx telephony integration
│   │   └── twilio-api/              # Twilio SMS/Voice integration
│   ├── design-media/            # Design & media tools
│   │   ├── frontend-design/         # Distinctive UI creation
│   │   ├── gemini-claude-resonance/ # Cross-model AI dialogue with visual memory
│   │   ├── nano-banana-pro/         # Gemini 3 Pro AI image generation
│   │   ├── photo-to-slack-emoji/    # Photo to Slack emoji converter
│   │   ├── rocaille-shader/         # Domain warping shader generator
│   │   ├── smolvlm/                # Local vision-language model (SmolVLM-2B)
│   │   └── speak-response/          # Local TTS with Qwen3-TTS (Oracle voice)
│   ├── research/                # Research tools
│   │   ├── academic-research/       # Academic paper search with Exa + ArXiv
│   │   ├── atk-ux-research/         # America's Test Kitchen UX research
│   │   ├── exa-search/              # Full Exa AI API access
│   │   └── Firecrawl/               # Official CLI + Agent API (prefer over WebFetch)
│   └── planning-productivity/   # Planning tools
│       ├── claude-tracker-search/     # ⭐ NEW - Session search, project detection, setup bootstrap
│       ├── crypt-librarian/         # Film curator persona
│       ├── minoan-swarm/            # Agent Teams orchestration (Minoan-Semitic naming)
│       ├── super-ralph-wiggum/      # ⭐ Autonomous iteration loops (11 Tips)
│       └── travel-requirements-expert/  # Travel itinerary planning
├── commands/                    # Slash commands
│   ├── workflows/               # Multi-agent workflow commands
│   │   ├── review.md             # 12+ agent code review
│   │   ├── work.md               # Plan execution
│   │   ├── plan.md               # Feature planning
│   │   └── plan_review.md        # Parallel plan review
│   ├── audit-plans.md           # Plan completeness auditing
│   ├── code-review.md           # PR code review
│   ├── interview.md             # Plan clarification questions
│   └── ... (30+ slash commands)
├── hooks/                       # Claude Code hooks
│   ├── multi-response-prompt.py  # /5x trigger for 5 alternative responses
│   ├── terminal-title.sh         # Dynamic tab titles + notifications
│   ├── on-thinking.sh            # Symlink to terminal-title.sh
│   └── on-ready.sh               # Symlink to terminal-title.sh
├── sounds/                      # Notification sounds
│   └── soft-ui.mp3               # Ready notification sound
└── README.md                    # This file
```

## Quick Start

> **New here?** Jump to [Recommended Workflow Commands](#recommended-workflow-commands) to see the most powerful commands: `/requirements-start`, `/workflows:review`, `feature-dev` plugin, `codex-orchestrator` skill, `minoan-swarm` agent teams, and `/code-review`.

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/claude-code-minoan.git
cd claude-code-minoan
```

### 2. Set Up Skills

Skills are custom Claude Code capabilities that extend functionality with specialized workflows.

**Option A: Copy to Personal Skills Directory** (recommended)
```bash
cp -r skills/* ~/.claude/skills/
```

**Option B: Symlink Individual Skills**
```bash
ln -s "$(pwd)/skills/core-development/beads-task-tracker" ~/.claude/skills/beads-task-tracker
ln -s "$(pwd)/skills/integration-automation/agent-browser" ~/.claude/skills/agent-browser
```

### 3. Set Up Slash Commands

```bash
cp -r commands/* ~/.claude/commands/
```

### 4. Set Up MCP Servers

Add servers using the Claude Code CLI:

```bash
# Playwright (browser automation)
claude mcp add playwright -c npx -a "@playwright/mcp@latest" -s user

# Perplexity (AI search)
claude mcp add perplexity -c node -a "/path/to/perplexity-mcp/build/index.js" -s user -e PERPLEXITY_API_KEY=your_key

# shadcn/ui (HTTP)
claude mcp add shadcn --http "https://www.shadcn.io/api/mcp" -s user

# Figma (HTTP)
claude mcp add figma --http "https://mcp.figma.com/mcp" -s user
```

## Recommended Workflow Commands

These are the most powerful commands for professional development workflows:

### `/requirements-start` Series - Extensive Project Planning

**Use when**: Starting any new feature or project that needs careful planning

The requirements workflow creates comprehensive specifications through structured discovery:

1. **`/requirements-start <description>`** - Initiates requirements gathering
   - Asks 5 high-level yes/no questions to understand scope
   - Analyzes codebase context and existing patterns
   - Generates 5 detailed technical questions
   - Creates comprehensive specification document

2. **`/requirements-continue`** - Resume interrupted requirements session
3. **`/requirements-review`** - Review and refine existing requirements
4. **`/requirements-implement`** - Begin implementation from specification

**Why it's powerful**:
- Prevents scope creep through structured discovery
- Documents decisions for future reference
- Catches architectural conflicts early
- Creates implementation-ready specifications
- Saves hours of refactoring later

**Example workflow**:
```bash
/requirements-start Implement user authentication with OAuth
# Answer discovery questions
# Answer technical questions
# Review specification
/requirements-implement
```

### `/workflows:review` - Comprehensive Code Review

**Use when**: Before committing significant changes or reviewing pull requests

> **Note**: This command is token-intensive due to parallel subagents. Use for thorough reviews; for quick checks, use `/code-review`.

Analyzes code for:
- Security vulnerabilities (credential exposure, input validation)
- Performance bottlenecks (inefficient patterns, memory leaks)
- Code quality (complexity, maintainability, best practices)
- Architecture issues (layer separation, dependency direction)

Creates prioritized issues with:
- Exact file locations and line numbers
- Problem explanation and impact assessment
- Specific remediation steps
- Severity and effort estimates

**Why it's powerful**:
- Uses 12+ specialized parallel subagents (security-sentinel, performance-oracle, architecture-strategist, etc.)
- Catches issues before they reach production
- Provides actionable feedback, not just complaints
- Creates GitHub issues automatically if requested

### `feature-dev` Plugin - Claude Code Team's Arsenal

**Use when**: Building features, exploring codebases, or reviewing code with specialized agents

The `feature-dev` plugin is the **official Claude Code team's toolkit** - the same agents they use internally. Install it with:

```bash
/plugin marketplace add anthropics/claude-code
/plugin install feature-dev
```

**Available agents** (invoke via Task tool with `subagent_type`):

| Agent | Purpose |
|-------|---------|
| `feature-dev:code-architect` | Designs feature architectures by analyzing existing patterns, providing implementation blueprints with specific files, component designs, data flows, and build sequences |
| `feature-dev:code-explorer` | Deeply analyzes codebase features by tracing execution paths, mapping architecture layers, understanding patterns/abstractions, and documenting dependencies |
| `feature-dev:code-reviewer` | Reviews code for bugs, logic errors, security vulnerabilities, and quality issues using confidence-based filtering to surface only high-priority findings |

**Why it's powerful**:
- Built by the Claude Code team for their own workflows
- Specialized agents outperform general-purpose prompts
- `code-architect` creates comprehensive blueprints before you write code
- `code-explorer` maps unfamiliar codebases quickly
- `code-reviewer` catches issues with confidence-based prioritization

**Example workflow**:
```bash
# Explore an unfamiliar codebase
# (Claude uses feature-dev:code-explorer agent)
"How does the authentication system work in this codebase?"

# Design a new feature
# (Claude uses feature-dev:code-architect agent)
"Design the architecture for adding OAuth support"

# Review your changes
# (Claude uses feature-dev:code-reviewer agent)
"Review my recent changes for any issues"
```

### `codex-orchestrator` Skill - Delegate to Specialized Codex Subagents

**Use when**: You need focused code review, debugging, architecture analysis, security audits, or documentation from Codex CLI

The codex-orchestrator skill lets Claude delegate tasks to OpenAI's Codex CLI with specialized AGENTS.md personas. Each profile shapes the agent's behavior for a specific task type.

**Available profiles**:

| Profile | Purpose | Best For |
|---------|---------|----------|
| `reviewer` | Code quality, bugs, performance | Pre-commit review, PR assessment |
| `debugger` | Root cause analysis, fixes | Investigating bugs, tracing issues |
| `architect` | System design, component boundaries | Planning changes, evaluating architecture |
| `security` | OWASP, vulnerabilities, secrets | Security audits, compliance checks |
| `refactor` | Code cleanup, modernization | Reducing tech debt, improving structure |
| `docs` | API docs, READMEs, comments | Documentation tasks |

**Quick execution**:
```bash
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh reviewer "Review src/auth.ts for security issues"
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh debugger "Debug the login timeout on slow networks"
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh architect "Design a caching layer for the API"
```

**Why it's powerful**:
- Each profile has deep expertise in its domain
- AGENTS.md persona injection guides Codex behavior
- Supports chaining patterns (review → debug → fix)
- Works with codex-mini, o3, o4-mini models
- Full-auto mode for unattended execution

**Example workflow**:
```bash
# 1. Find issues
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh reviewer "Review src/api/ for bugs"

# 2. Investigate specific bug
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh debugger "Debug the race condition found in cache.ts"

# 3. Design fix approach
~/.claude/skills/codex-orchestrator/scripts/codex-exec.sh architect "Design fix for the cache race condition"
```

### `super-ralph-wiggum` Skill - Autonomous Iteration Loops

**Use when**: Running Claude Code in autonomous loops for bulk tasks like test coverage, lint fixing, code cleanup, or PRD-based feature development

Based on [AI Hero's 11 Tips](https://www.aihero.dev/tips-for-ai-coding-with-ralph-wiggum), this skill runs the same prompt repeatedly until task completion, with context persisting through files and git history.

**Available templates**:

| Template | Use Case |
|----------|----------|
| `test-coverage` | Improve test coverage to target % |
| `feature-prd` | Implement features from PRD file |
| `lint-fix` | Fix lint errors incrementally |
| `entropy-loop` | Remove dead code, smells, TODOs |
| `duplication-loop` | Extract duplicate code into utilities |

**Quick usage**:
```
Run super-ralph-wiggum with test-coverage template, max 20 iterations
Run super-ralph-wiggum with feature-prd template using ./prd.json
```

**Why it's powerful**:
- The agent chooses tasks from your PRD, not you
- HITL mode for learning, AFK mode for overnight runs
- Progress file persists learning across iterations
- Docker sandbox support for safe unattended execution
- "Fight entropy" and quality-first principles built in

### `minoan-swarm` Skill - Agent Team Orchestration

**Use when**: A task benefits from parallel agents — feature development across frontend/backend, research swarms, code review tribunals, or phased project execution

Claude Code now supports native Agent Teams: multiple Claude instances working in parallel, coordinated through shared task lists and direct messaging. This is a paradigm shift from single-agent workflows with persistent memory plugins. Instead of one agent remembering everything, you orchestrate a team of specialists that divide, conquer, and converge.

The `minoan-swarm` skill provides the orchestration layer: auto-discovery of project context (CLAUDE.md, roadmaps, plans, issues), pre-built team templates, and a naming codex drawn from Ugaritic, Akkadian, Hebrew, Egyptian, Linear B, and pre-Islamic Arabian traditions.

**Available team templates**:

| Template | Pattern | Use Case |
|----------|---------|----------|
| Parallel Features | Fan-out/fan-in | Build independent features simultaneously |
| Pipeline | Sequential handoff | Research → Design → Implement → Review |
| Research Swarm | Competitive search | Multiple agents explore different angles |
| Phase Completion | Milestone-gated | Execute a phased plan with verification gates |
| Code Review Tribunal | Multi-perspective | 3+ reviewers with different specializations |

**Quick usage**:
```
Load the minoan-swarm skill, then create a Research Swarm team for investigating caching strategies
```

**Why it's powerful**:
- Native Claude Code agent teams — no plugins, no external dependencies
- Shared task lists with dependency tracking across agents
- Direct messaging between teammates for real-time coordination
- Auto-discovers project context so agents start informed
- 30+ named teammate roles from ancient Mediterranean traditions
- Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

### `/audit-plans` - Plan Completeness Auditing

**Use when**: Before implementing a plan to ensure nothing is missed

Systematically audits implementation plans:
- Reads phases chronologically
- Evaluates against completeness criteria (acceptance criteria, implementation steps, dependencies, edge cases)
- Invokes `/interview` to fill gaps with structured questions
- Updates plan and related documentation

---

## Available Skills

### Core Development (`skills/core-development/`)

- **architecture-md-builder** - Build comprehensive ARCHITECTURE.md files for any repository following matklad's canonical guidelines. Produces bird's eye views, ASCII/Mermaid diagrams, codemaps, invariants, and layer boundaries
- **beads-task-tracker** - Dependency-aware task tracking with Beads. SQLite + JSONL sync, hash-based IDs, daemon process for cross-session continuity
- **claude-agent-sdk** - Build AI agents using the Claude Agent SDK (Python & TypeScript). Covers query functions, ClaudeSDKClient, custom tools with @tool decorator, MCP servers, hooks, permissions, and subagents. Includes 7 production-ready templates and 9 reference docs
- **claude-md-manager** - Create, audit, and maintain CLAUDE.md documentation files. Uses the WHAT/WHY/HOW framework, progressive disclosure patterns with agent_docs/, conciseness optimization, and anti-pattern detection
- **osgrep-reference** - Semantic code search using natural language queries. Find code by concept rather than keyword matching ("where do we handle authentication?" vs "grep 'auth'")
- **react-best-practices** - React and Next.js performance optimization guidelines from Vercel Engineering. Use when writing, reviewing, or refactoring React/Next.js code for optimal performance patterns
- **skill-optimizer** - Guide for creating and reviewing Claude Code skills. Use when creating new skills, reviewing existing skills for quality, or optimizing skills with specialized knowledge and workflows

### Integration & Automation (`skills/integration-automation/`)

- **agent-browser** - Browser automation using Vercel's agent-browser CLI. Ref-based selection (@e1, @e2) from accessibility snapshots. Simple Bash commands for navigation, forms, screenshots, scraping
- **codex-orchestrator** ⭐ - Orchestrate OpenAI Codex CLI with specialized subagents (reviewer, debugger, architect, security, refactor, docs). Each profile injects a custom AGENTS.md persona. Supports chaining patterns (review → debug → fix) and parallel delegation. Works with codex-mini, o3, o4-mini models
- **figma-mcp** - Convert Figma designs to production code with accurate styling
- **llama-cpp** ⭐ - Secondary local LLM inference via llama.cpp on Apple Silicon. ~15% faster prompt processing than Ollama, LoRA adapter hot-loading (no merge required), benchmarking scripts, GGUF conversion pipeline, and OpenAI-compatible API server. Shares GGUF model files with Ollama (no duplication). Scripts: `llama_bench.sh`, `llama_serve.sh`, `llama_lora.sh`, `ollama_model_path.sh`, `convert_lora_to_gguf.py`
- **beautiful-mermaid** ⭐ NEW - Render Mermaid diagrams as ASCII/Unicode art for terminal or SVG files. Supports flowcharts, state diagrams, sequence diagrams, class diagrams, and ER diagrams. 15 built-in themes (tokyo-night, catppuccin, nord, dracula, etc.). Based on beautiful-mermaid npm package by Craft.
- **mcp-server-manager** - Configure and manage MCP servers in Claude Code
- **netlify-integration** - Deploy and manage Netlify projects with Next.js serverless functions, environment variables, and continuous deployment
- **parakeet** - Local speech-to-text using NVIDIA Parakeet TDT 0.6B (~600MB, 100% offline). 3,386x realtime speed, 6.05% WER. Transcribe audio files (.wav, .mp3, .m4a, .flac, .ogg, .aac) or dictate from microphone. Apple Silicon MPS acceleration. Commands: `/parakeet <file>`, `/parakeet dictate`, `/parakeet check`
- **rlama** ⭐ - Local RAG system for semantic document search. Create knowledge bases from PDFs, markdown, code files. Query documents with natural language. Runs 100% locally with Ollama (default: qwen2.5:7b). Includes resilient indexing that skips context overflow errors, management scripts for create/add/remove/query operations, and `--legacy` flag for llama3.2 compatibility. **NEW**: Progress monitoring with `tail -f ~/.rlama/logs/rlama.log` and `rlama_status.py` for real-time operation tracking with ETA
- **supabase-skill** - Configure and manage Supabase projects using MCP. Database design, migrations, RLS policies
- **telnyx-api** - SMS/MMS messaging, voice calls, phone numbers, webhooks, and telephony integration
- **twilio-api** - Twilio SMS/Voice API integration with provider-agnostic patterns, webhook security, E.164 validation, and error handling

### Design & Media (`skills/design-media/`)

- **frontend-design** - Create distinctive, production-grade frontend interfaces with high design quality. Generates creative, polished code that avoids generic AI aesthetics. Bold typography, unexpected layouts, atmospheric backgrounds
- **gemini-claude-resonance** - Cross-model dialogue between Claude and Gemini with shared visual memory. Multiple daimones (Flash, Pro, Dreamer, Director, Opus, Resonator) with dynamic verb selection and WorkingMemory-style transcripts. Includes Daimon Chamber UI and Resonance Field protocol for persistent visual narratives
- **nano-banana-pro** - Generate and edit high-quality images using Google's Nano Banana Pro (Gemini 3 Pro Image) AI model. Supports up to 4K resolution, multiple aspect ratios, and advanced prompting
- **photo-to-slack-emoji** - Transform photos into Slack-optimized emojis using Nano Banana Pro AI (10 styles, auto-optimization for 64KB limit)
- **rocaille-shader** - Generate Rocaille-style domain warping shaders with sinusoidal displacement. Creates organic swirling light effects for WebGL/GLSL visualizations, shader art, and procedural backgrounds. Outputs to Shadertoy, Three.js, P5.js, or vanilla WebGL
- **smolvlm** ⭐ NEW - Local vision-language model using SmolVLM-2B via mlx-vlm. Analyze images locally on Apple Silicon at 87 tok/s with 5.8GB peak memory. Supports image description, OCR, UI analysis, VQA, and code screenshot reading. Commands: `python scripts/view_image.py <image> [prompt]`
- **speak-response** - Local text-to-speech using Qwen3-TTS. Default Oracle voice (deep, prophetic Dune narrator). Supports voice cloning, voice design, and 9 preset speakers with emotion/mood control. Runs entirely on Apple Silicon

### Research (`skills/research/`)

- **academic-research** - Comprehensive academic paper search, literature reviews, and research synthesis. Combines Exa MCP with arxiv-mcp-server for paper discovery, download, and deep analysis
- **atk-ux-research** - Specialized UX research skill for America's Test Kitchen. Gathers user feedback from app stores, Reddit, Trustpilot, BBB, and review sources using Exa Search, Firecrawl, and Perplexity MCP. Outputs structured reports with quantitative metrics and qualitative themes
- **exa-search** - Complete Exa AI search API access with 6 scripts: neural web search, URL content extraction (with RAG context), similar page discovery (with moderation/text filters), AI research with streaming, async research (3 models: fast/standard/pro), and test suite. Full API coverage
- **Firecrawl** - Official Firecrawl CLI (`firecrawl scrape/crawl/map/search`) plus Agent API for autonomous data extraction. Auto-save alias (`fc-save`), Python API script for batch/extract/agent commands. **ALWAYS prefer Firecrawl over WebFetch**

### Planning & Productivity (`skills/planning-productivity/`)

- **claude-tracker-search** ⭐ NEW - Search, browse, and manage Claude Code session history. Find past sessions by topic, detect projects across all sessions, resume crashed VS Code sessions in tmux, bootstrap new `~/.claude/` setups, and update active-projects docs. Includes `detect-projects.js` (scan sessions, check CLAUDE.md coverage, scaffold missing files) and `bootstrap-claude-setup.js` (generate complete config for new machines)
- **crypt-librarian** - Film curator persona for sourcing pre-2016 cinema with literary/gothic sensibility, occult atmosphere, sensual mysticism, and historical grandeur. Uses Perplexity for film discourse, Exa for web searches
- **minoan-swarm** - Orchestrate Claude Code Agent Teams with Minoan-Semitic naming conventions. Auto-discovers project context (CLAUDE.md, roadmaps, plans, issues), provides 5 team templates (Parallel Features, Pipeline, Research Swarm, Phase Completion, Code Review Tribunal), and a naming codex of 30+ teammate names sourced from Ugaritic, Akkadian, Hebrew, and Linear B traditions. Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
- **super-ralph-wiggum** ⭐ - Autonomous iteration loops based on [AI Hero's 11 Tips](https://www.aihero.dev/tips-for-ai-coding-with-ralph-wiggum). Templates for test coverage, PRD features, lint fixing, entropy cleanup, duplication removal, docs generation, and migrations. HITL/AFK modes, progress tracking, Docker sandboxes for safety
- **travel-requirements-expert** - Systematically gather comprehensive travel itinerary requirements through structured discovery questions, MCP-powered research, and expert detail gathering

## VS Code Extension

### Claude Session Tracker

Track and resume Claude Code sessions across crashes, restarts, and multiple VS Code windows.

**Features:**
- **Cross-Window Tracking**: See total Claude sessions across ALL VS Code windows (e.g., "Claude Active (7)")
- **Quick Resume**: `Cmd+Shift+C` to instantly resume your last session
- **Global Session Browser**: Browse sessions across ALL projects
- **Crash Recovery**: Resume work after VS Code crashes

**Installation:**
```bash
cd extensions/claude-session-tracker
npm install
npm run compile
npx @vscode/vsce package --no-dependencies
code --install-extension claude-session-tracker-0.1.0.vsix
```

**Commands:**
| Command | Keybinding | Description |
|---------|------------|-------------|
| Resume Last Claude Session | `Cmd+Shift+C` | Resume most recent session |
| Pick Claude Session | — | Browse and select from recent sessions |
| Browse All Claude Sessions | — | Browse sessions across ALL projects |

See [`extensions/claude-session-tracker/readme.md`](extensions/claude-session-tracker/readme.md) for full documentation.

## CLI Tools (`bin/` + `lib/`)

Copy to your PATH and Claude lib directory:

```bash
cp bin/* ~/.local/bin/
mkdir -p ~/.claude/lib && cp lib/* ~/.claude/lib/
```

### Session Management

| Tool | Description |
|------|-------------|
| `claude-tracker` | List recent sessions with summaries, running status, VS Code detection |
| `claude-tracker-search` | Search sessions by summary, content, ID, project, or date range |
| `claude-tracker-resume` | Find crashed sessions and print resume commands (or auto-resume in tmux/Terminal.app) |

```bash
# Search sessions by topic
claude-tracker-search "kothar mac mini"

# Search by session ID prefix
claude-tracker-search --id 1da2b718

# Filter by project, limit results
claude-tracker-search --project Aldea --limit 5

# Recent sessions only
claude-tracker-search --since 7d --json

# List crashed sessions with resume commands
claude-tracker-resume

# Auto-resume crashed sessions in tmux windows
claude-tracker-resume --tmux

# Auto-resume crashed sessions in Terminal.app tabs (macOS)
claude-tracker-resume --zsh

# Preview without acting
claude-tracker-resume --dry-run
```

### Quick Launchers

| Tool | Description |
|------|-------------|
| `cc` | Quick Claude Code launcher |
| `cckill` | Kill Claude Code processes by name or PID |
| `ccls` | List running Claude Code sessions |
| `ccpick` | Interactive session picker (fzf-based) |
| `claude-tmux-status` | Claude Code status for tmux statusline |

### Shared Library (`lib/tracker-utils.js`)

All tracker CLIs share `tracker-utils.js` for:
- `loadSessionsIndex()` — Load all sessions-index.json into flat array
- `decodeProjectPath()` — Resolve encoded dir names to real paths (with filesystem validation)
- `buildSessionStatus()` — Detect running sessions, VS Code workspace membership
- `parseSession()` — Parse individual JSONL session files
- `formatAge()` — Human-readable time formatting

## MCP Servers

> **Note: We've shifted away from heavy MCP usage.** Claude Code now includes [MCP Tool Search](https://www.atcyrus.com/stories/mcp-tool-search-claude-code-context-pollution-guide), which loads tools on-demand rather than all upfront—reducing context pollution by ~85%. This means large MCP setups no longer exhaust the context window. However, we've found that **skills often provide better ergonomics** than MCPs for most workflows, with clearer documentation and simpler invocation patterns. The MCPs below are kept for reference but are not actively maintained.

### Configured in `.mcp.json`

| Server | Type | Purpose |
|--------|------|---------|
| **supabase** | stdio | PostgreSQL database operations |
| **netlify** | stdio | Deployment and site management |
| **playwright** | stdio | Browser automation and testing |
| **context7** | HTTP | Up-to-date library documentation |
| **shadcn** | HTTP | shadcn/ui component library |
| **figma** | HTTP | Figma design integration |
| **arxiv** | stdio | Academic paper search and analysis |
| **perplexity** | stdio | AI-powered search (requires API key) |
| **telnyx** | stdio | Telephony, messaging, voice calls |
| **twilio** | stdio | SMS and voice operations |
| **mcp-google-sheets** | stdio | Google Sheets integration |
| **chrome-devtools** | stdio | Browser debugging integration |
| **filesystem** | stdio | Enhanced filesystem access |

See `.mcp.json` for full configuration details and setup instructions.

## All Slash Commands

### Development Workflow
- `/commit` - Create standardized git commits
- `/refactor` - Refactor code with best practices
- `/implement` - Implement features from specifications
- `/test` - Generate comprehensive tests

### Code Quality
- `/workflows:review` - Comprehensive code review with 12+ parallel subagents (token-intensive)
- `/security-scan` - Security vulnerability analysis
- `/fix-imports` - Fix import statements
- `/cleanproject` - Clean up project structure

### Documentation
- `/docs` - Generate documentation
- `/explain-like-senior` - Senior-level code explanations
- `/understand` - Deep dive into codebase understanding

### Planning & Requirements
- `/requirements-start` - Extensive project planning workflow
- `/requirements-continue` - Resume interrupted requirements session
- `/requirements-review` - Review and refine existing requirements
- `/requirements-implement` - Begin implementation from specification
- `/audit-plans` - Audit plans for completeness, interview to fill gaps
- `/interview` - Generate clarifying questions about a plan
- `/create-todos` - Generate TODO lists from requirements
- `/find-todos` - Find TODO comments in codebase
- `/fix-todos` - Address existing TODOs

### Code Review
- `/code-review` - Comprehensive PR code review with structured JSON output. *Created by the inventor of Claude Code*

### Workflow Commands
- `/workflows:review` - Exhaustive code review using 12+ parallel agents
- `/workflows:work` - Execute work plans with quality checks
- `/workflows:plan` - Transform descriptions into project plans
- `/workflows:plan_review` - Parallel plan review by multiple agents

### Official Plugins
- **`feature-dev`** - Claude Code team's arsenal: `code-architect`, `code-explorer`, `code-reviewer` agents

## Hooks

Hooks are scripts that run in response to Claude Code events. Copy to `~/.claude/hooks/` and configure in `~/.claude/settings.json`.

### Available Hooks

| Hook | Trigger | Description |
|------|---------|-------------|
| `multi-response-prompt.py` | `/5x` in message | Generates 5 alternative responses sampled from distribution tails. Useful for exploring creative options |
| `terminal-title.sh` | Claude state changes | Dynamic terminal tab indicators: 🔴 thinking, 🟢 ready. Desktop notifications with click-to-focus VS Code. Duration tracking. Sound alerts |
| `session-handoff.sh` | PreCompact, 5% remaining | Creates/updates session handoff notes before context compaction. Logs to `~/.claude/handoffs/YYYY-MM-DD.md` with project, session ID, git status, and structured placeholders |
| `statusline-monitor.sh` | Every turn (StatusLine) | Monitors context percentage, triggers handoff at 5% remaining. Chains with existing statusline command |

### Terminal Title Hook Features

- **Visual tab indicators**: 🔴 when Claude is thinking/generating, 🟢 when ready for input
- **Desktop notifications**: macOS notification when Claude finishes (click to focus VS Code)
- **Duration tracking**: Shows how long Claude took (e.g., "Ready for input (2m 34s)")
- **Sound notification**: Plays `sounds/soft-ui.mp3` when ready
- **Multi-session support**: Each terminal tab shows project name

**Requirements**: `brew install terminal-notifier` for desktop notifications

### Session Handoff Hook

Automatically creates structured handoff notes before context compaction:

- **Triggers at 5% remaining** via StatusLine monitor
- **Updates entry at PreCompact** changing `[5%]` to `[COMPACTED]`
- **Logs to** `~/.claude/handoffs/YYYY-MM-DD.md`

Each entry includes:
- Session ID and directory
- Git branch and status
- Recent commits
- Placeholders for: Current Objective, What Was Done, Decisions Made, Blockers, Next Steps

**Setup**: Add to `~/.claude/settings.json`:
```json
{
  "hooks": {
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/session-handoff.sh"
          }
        ]
      }
    ]
  },
  "statusLine": {
    "type": "command",
    "command": "~/.claude/hooks/statusline-monitor.sh",
    "padding": 0
  }
}
```

### Setup

1. Copy hooks and sounds to your Claude directory:
   ```bash
   cp -r hooks/* ~/.claude/hooks/
   cp -r sounds ~/.claude/sounds/
   chmod +x ~/.claude/hooks/*.py ~/.claude/hooks/*.sh
   ```

2. Configure in `~/.claude/settings.json`:
   ```json
   {
     "hooks": {
       "UserPromptSubmit": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "~/.claude/hooks/multi-response-prompt.py"
             },
             {
               "type": "command",
               "command": "~/.claude/hooks/on-thinking.sh"
             }
           ]
         }
       ],
       "Stop": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "~/.claude/hooks/on-ready.sh"
             }
           ]
         }
       ]
     }
   }
   ```

3. Enable dynamic terminal titles in VS Code settings (`settings.json`):
   ```json
   {
     "terminal.integrated.tabs.title": "${sequence}"
   }
   ```

4. Use `/5x` by adding it to any message:
   ```
   How should I structure this component? /5x
   ```

## Recommended Plugins

### `feature-dev` - Claude Code Team's Arsenal

The official plugin from the Claude Code team. Provides specialized agents for feature development:

```bash
/plugin marketplace add anthropics/claude-code
/plugin install feature-dev
```

- **`code-architect`** - Design feature architectures with implementation blueprints
- **`code-explorer`** - Trace execution paths and map codebase structure
- **`code-reviewer`** - Confidence-based code review for high-priority issues

## Terminal & Editor Theme

Recommended setup: **Victor Mono** font, **Catppuccin Mocha** theme, and **ccstatusline** for Claude Code.

### 1. Install Victor Mono Font

```bash
brew install --cask font-victor-mono
```

### 2. Install Catppuccin Theme for VS Code

Install the [Catppuccin for VS Code](https://github.com/catppuccin/vscode) extension:

1. Open VS Code
2. `Cmd + Shift + X` → Search "Catppuccin"
3. Install **Catppuccin for VSCode**
4. `Cmd + Shift + P` → "Preferences: Color Theme" → Select **Catppuccin Mocha**

### 3. Install ccstatusline for Claude Code

Beautiful customizable statusline with powerline support, themes, and metrics:

```bash
npm install -g ccstatusline
```

Configure with the interactive TUI:
```bash
ccstatusline
```

Features: model info, git branch, token usage, session cost, context percentage, and more.

See: [github.com/sirmalloc/ccstatusline](https://github.com/sirmalloc/ccstatusline)

### 4. VS Code Terminal Settings

Add to your VS Code `settings.json` (`Cmd + Shift + P` → "Preferences: Open User Settings (JSON)"):

```json
{
    "terminal.integrated.fontFamily": "'Victor Mono', monospace",
    "terminal.integrated.fontSize": 14,
    "terminal.integrated.fontLigatures": true,

    "workbench.colorCustomizations": {
        "terminal.background": "#1e1e2e",
        "terminal.foreground": "#cdd6f4",
        "terminalCursor.foreground": "#f5e0dc",
        "terminal.selectionBackground": "#585b70",
        "terminal.ansiBlack": "#45475a",
        "terminal.ansiRed": "#f38ba8",
        "terminal.ansiGreen": "#a6e3a1",
        "terminal.ansiYellow": "#f9e2af",
        "terminal.ansiBlue": "#89b4fa",
        "terminal.ansiMagenta": "#f5c2e7",
        "terminal.ansiCyan": "#94e2d5",
        "terminal.ansiWhite": "#bac2de",
        "terminal.ansiBrightBlack": "#585b70",
        "terminal.ansiBrightRed": "#f38ba8",
        "terminal.ansiBrightGreen": "#a6e3a1",
        "terminal.ansiBrightYellow": "#f9e2af",
        "terminal.ansiBrightBlue": "#89b4fa",
        "terminal.ansiBrightMagenta": "#f5c2e7",
        "terminal.ansiBrightCyan": "#94e2d5",
        "terminal.ansiBrightWhite": "#a6adc8"
    },
    "terminal.integrated.minimumContrastRatio": 1
}
```

Reload VS Code (`Cmd + Shift + P` → "Developer: Reload Window") to apply.

### 5. Markdown Editor Settings (Workspace)

This repo includes `.vscode/settings.json` with optimized Markdown editing:

| Setting | Value | Purpose |
|---------|-------|---------|
| `editor.wordWrap` | on | Wrap long lines instead of horizontal scrolling |
| `editor.lineHeight` | 1.4 | More breathing room between lines |
| `editor.fontSize` | 13 | Comfortable reading size |
| `editor.minimap.enabled` | true | Show minimap for quick file navigation |

**Markdown Preview** (Cmd+K V):
- Synced scrolling between editor and preview
- 1.5x line spacing for readability
- Cursor position highlighted in preview

**Syntax Highlighting**:
- Headings: Blue (`#58A6FF`)
- Lists: Light cyan (`#7DD3FC`)
- Links: Blue with underline
- Code: Light gray (`#c9d1d9`)

These settings apply automatically when opening this repo in VS Code.

## Security Best Practices

1. **Never commit API keys** - Use placeholders in `.mcp.json`
2. **Use environment variables** - Store secrets in `.env` files
3. **Git ignore sensitive files**:
   ```
   .env
   .env.local
   *_local.json
   ```
4. **Rotate keys regularly** - Especially for shared team accounts
5. **Use scoped tokens** - Minimum permissions required

## Contributing

### Skill Development Guidelines

1. Follow the skill template structure (SKILL.md at minimum)
2. Include comprehensive documentation with usage examples
3. Add reference files for complex workflows
4. Test across different projects
5. Submit PR with description of functionality

### Slash Command Guidelines

1. Keep commands focused and single-purpose
2. Use frontmatter for metadata:
   ```markdown
   ---
   description: Brief command description
   argument-hint: [required-arg] [optional-arg]
   ---
   Your prompt template here
   ```
3. Document expected inputs/outputs
4. Include examples in comments

### MCP Server Guidelines

1. Test server thoroughly before adding
2. Document all required environment variables
3. Include troubleshooting steps
4. Note any system dependencies
5. Specify which scope (user/project/local) is recommended

## Team Setup Checklist

- [ ] Clone repository
- [ ] Copy skills to `~/.claude/skills/`
- [ ] Copy commands to `~/.claude/commands/`
- [ ] **Install Claude Session Tracker extension** (see [VS Code Extension](#vs-code-extension))
- [ ] Install `feature-dev` plugin (`/plugin marketplace add anthropics/claude-code` then `/plugin install feature-dev`)
- [ ] Set up essential MCP servers (supabase, arxiv, perplexity, context7)
- [ ] Configure API keys for perplexity, supabase, netlify
- [ ] Test a slash command (`/docs`)
- [ ] Test a skill (claude-agent-sdk)
- [ ] Verify MCP servers with `claude mcp list`
- [ ] Install Victor Mono font (`brew install --cask font-victor-mono`)
- [ ] Install Catppuccin theme for VS Code
- [ ] Install ccstatusline (`npm install -g ccstatusline`)
- [ ] Configure VS Code terminal settings (see Terminal & Editor Theme section)

## Troubleshooting

### Skills Not Loading

```bash
ls ~/.claude/skills/
ls ~/.claude/skills/skill-name/
# Should contain SKILL.md at minimum
```

### MCP Server Connection Failed

```bash
claude mcp list
claude mcp get server-name
claude mcp remove server-name -s user
claude mcp add server-name ...
```

### Slash Command Not Found

```bash
ls ~/.claude/commands/command-name.md
cat ~/.claude/commands/command-name.md
```

## Documentation Links

- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code)
- [MCP Server Guide](https://docs.claude.com/en/docs/claude-code/mcp)
- [Slash Commands Guide](https://docs.claude.com/en/docs/claude-code/slash-commands)
- [Skills Development](https://docs.claude.com/en/docs/claude-code/skills)

---

**Last Updated**: 2026-02-09

**Highlights**:
- **minoan-swarm** — Native Agent Teams orchestration with Minoan-Semitic naming. 5 team templates, 30+ named teammates from Ugaritic, Akkadian, Hebrew, Egyptian, Linear B, and pre-Islamic Arabian traditions
- **CLI Tools** — Session management CLIs (`claude-tracker-search`, `claude-tracker-resume`, `cc`, `cckill`, `ccls`, `ccpick`) with shared `tracker-utils.js` library
- **Local ML stack** — `llama-cpp` (LoRA hot-loading, 15% faster than Ollama), `rlama` (local RAG with progress monitoring), `parakeet` (STT, 3386x realtime), `smolvlm` (vision-language, 87 tok/s), `speak-response` (TTS, Oracle voice clone)
- **beautiful-mermaid** — Mermaid diagrams as ASCII art or SVG. 15 themes, 5 diagram types
- **Firecrawl** — Official CLI v1.1.1 + Python API, SDK v4.x compatible
- **codex-orchestrator** — Delegate to specialized Codex CLI subagents (reviewer, debugger, architect, security, refactor, docs)
- **super-ralph-wiggum** — Autonomous iteration loops with HITL/AFK modes and Docker sandbox support

**Skills**: 34 across 5 categories | **Commands**: 30+ | **MCP Servers**: 14 configured

---

*"ἀπιστίῃ διαφυγγάνει μὴ γιγνώσκεσθαι."* — "Divine things escape recognition through disbelief." — Heraclitus
