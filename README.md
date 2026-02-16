<p align="center">
  <img src="public/images/tanit.svg" alt="Symbol of Tanit" width="80"/>
</p>

<p align="center">
  <a href="#available-skills"><img src="https://img.shields.io/badge/Skills-40-green.svg" alt="Skills"></a>
  <a href="commands/README.md"><img src="https://img.shields.io/badge/Commands-30+-purple.svg" alt="Commands"></a>
  <a href="hooks/README.md"><img src="https://img.shields.io/badge/Hooks-7-orange.svg" alt="Hooks"></a>
</p>

# Minoan Claude Code Configuration

A curated `~/.claude/` configuration for professional development workflows — skills, hooks, CLI tools, slash commands, MCP servers, and a VS Code extension.

<p align="center">
  <img src="public/images/be_minoan.jpg" alt="Minoan fresco" width="600"/>
</p>

## Repository Map

```
claude-code-minoan/
├── skills/                      # 40 custom skills across 5 categories
│   ├── core-development/        #   Architecture, task tracking, code search
│   ├── integration-automation/  #   Local ML, RAG, browser, telephony
│   ├── design-media/            #   Frontend, image gen, TTS, vision
│   ├── research/                #   Academic, web search, scraping
│   └── planning-productivity/   #   Session tracking, swarms, iteration loops
├── hooks/                       # Lifecycle hooks (handoffs, terminal UX, multi-response)
├── commands/                    # 30+ slash commands (workflows, planning, code review)
├── agents/                      # Custom subagents (librarian, etc.)
├── bin/                         # CLI tools (session tracker, launchers, tmux)
├── tools/                       # Standalone tools (md_preview_and_annotate — canonical: github.com/tdimino/md-preview-and-annotate)
├── lib/                         # Shared libraries (tracker-utils.js)
├── extensions/                  # VS Code Claude Session Tracker extension
├── sounds/                      # Notification audio
└── docs/global-config/          # Full ~/.claude/ structure reference
```

Each folder has its own README with setup instructions, examples, and credits.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/your-org/claude-code-minoan.git
cd claude-code-minoan

# 2. Install skills
cp -r skills/*/* ~/.claude/skills/

# 3. Install commands
cp -r commands/* ~/.claude/commands/

# 4. Install hooks + sounds
cp -r hooks/* ~/.claude/hooks/
cp -r sounds ~/.claude/sounds/
chmod +x ~/.claude/hooks/*.py ~/.claude/hooks/*.sh

# 5. Install CLI tools
cp bin/* ~/.local/bin/
mkdir -p ~/.claude/lib && cp lib/* ~/.claude/lib/

# 6. Install VS Code extension
cd extensions/claude-session-tracker
npm install && npm run compile
npx @vscode/vsce package --no-dependencies
code --install-extension claude-session-tracker-*.vsix
```

Configure hooks in `~/.claude/settings.json` — see [hooks/README.md](hooks/README.md) for the full settings block.

---

## Deep Dives

### [Skills](skills/README.md) — 40 skills across 5 categories

Custom Claude Code capabilities organized by domain. Each skill has a `SKILL.md` entry point, optional scripts, and reference docs.

**Highlights**:

| Category | Count | Notable Skills |
|----------|-------|---------------|
| Core Development | 7 | `beads-task-tracker`, `architecture-md-builder`, `claude-agent-sdk` |
| Integration & Automation | 14 | `llama-cpp`, `rlama`, `parakeet`, `Firecrawl`, `codex-orchestrator` |
| Design & Media | 7 | `gemini-claude-resonance`, `nano-banana-pro`, `speak-response` |
| Research | 4 | `academic-research`, `exa-search`, `Firecrawl` |
| Planning & Productivity | 5 | `minoan-swarm`, `super-ralph-wiggum`, `claude-tracker-suite` |

Toggle skills on/off: `./skills/skill-toggle.sh`

---

### [Hooks](hooks/README.md) — Lifecycle event scripts

Scripts that run in response to Claude Code events — terminal UX, crash-resilient session handoffs, and multi-response sampling.

```
UserPromptSubmit ──→ multi-response-prompt.py    (/5x trigger)
PreToolUse ────────→ on-thinking.sh              (🔴 tab title)
Stop ──────────────→ on-ready.sh + stop-handoff.py (🟢 title + 5-min checkpoint)
PreCompact ────────→ precompact-handoff.py       (full handoff before compaction)
SessionEnd ────────→ precompact-handoff.py       (handoff on graceful exit)
```

**Session Handoff System**: Three hooks ensure context survives compaction, graceful exits, and crashes. Writes structured YAML to `~/.claude/handoffs/` with objective, decisions, blockers, and next steps. Auto-maintains `INDEX.md`.

---

### [Commands](commands/README.md) — 30+ slash commands

Markdown templates invoked as `/command-name`. Key workflows:

| Command | Purpose |
|---------|---------|
| `/requirements-start` | Structured project planning through discovery questions |
| `/workflows:review` | 12+ parallel agent code review |
| `/code-review` | PR review with structured output |
| `/audit-plans` | Plan completeness auditing |
| `/workflows:plan` | Transform descriptions into implementation plans |

---

### [Agents](agents/) — Custom subagents

Read-only research subagents invoked via the Task tool with `subagent_type: "Bash"` and the agent instructions in the prompt.

| Agent | Model | Purpose |
|-------|-------|---------|
| `librarian` | sonnet | GitHub repo exploration via `gh` CLI. Caches to `/tmp/claude-librarian/`. |

---

### [CLI Tools](bin/README.md) — Session management & launchers

| Tool | Purpose |
|------|---------|
| `claude-tracker` | List recent sessions with summaries and status |
| `claude-tracker-search` | Search sessions by topic, ID, project, date |
| `claude-tracker-resume` | Find crashed sessions, auto-resume in tmux |
| `cc` / `cckill` / `ccls` / `ccpick` | Quick launchers and session management |

All CLIs share `lib/tracker-utils.js` for session parsing and status detection.

---

### [VS Code Extension](extensions/README.md) — Claude Session Tracker

Track and resume Claude Code sessions across crashes, restarts, and multiple VS Code windows.

- Cross-window tracking ("Claude Active (7)")
- Quick resume: `Cmd+Shift+C`
- Crash recovery with one-click resume
- Session browser with AI-generated titles, model info, turn counts, cost

---

### [Global Config Reference](docs/global-config/README.md) — Full `~/.claude/` structure

Complete reference for the `~/.claude/` directory: CLAUDE.md patterns, user persona models, progressive disclosure with `agent_docs/`, settings.json hooks/MCP/plugins, session handoff system, plans, and design principles.

---

## Recommended Plugins

### `feature-dev` — Claude Code Team's Arsenal

The official plugin from the Claude Code team:

```bash
/plugin marketplace add anthropics/claude-code
/plugin install feature-dev
```

Three specialized agents: `code-architect` (implementation blueprints), `code-explorer` (trace execution paths), `code-reviewer` (confidence-based review).

### `compound-engineering` — Multi-Agent Review Workflows

By [Every AI Labs](https://github.com/every-ai-labs/compound-engineering). Provides 12+ specialized review agents (security-sentinel, performance-oracle, architecture-strategist, etc.) and workflow orchestration commands.

---

## MCP Servers

> We've shifted toward skills over MCPs for most workflows. Claude Code's [MCP Tool Search](https://www.atcyrus.com/stories/mcp-tool-search-claude-code-context-pollution-guide) loads tools on-demand, reducing context pollution by ~85%.

Configured in `.mcp.json`: supabase, playwright, context7, shadcn, figma, arxiv, perplexity, telnyx, twilio, and more. See the file for full configuration.

---

## Terminal & Editor Theme

Recommended: **Victor Mono** font + **Catppuccin Mocha** theme + **ccstatusline**.

```bash
brew install --cask font-victor-mono    # Font
npm install -g ccstatusline             # Claude Code statusline
```

Install [Catppuccin for VS Code](https://github.com/catppuccin/vscode), then set terminal colors — see `.vscode/settings.json` in this repo for the full color block.

See [github.com/sirmalloc/ccstatusline](https://github.com/sirmalloc/ccstatusline) for statusline configuration.

---

## Contributing

1. **Skills**: Follow the `SKILL.md` + `scripts/` + `references/` structure. Test across projects.
2. **Commands**: Use frontmatter (`description`, `argument-hint`). Keep single-purpose.
3. **Hooks**: Test with piped JSON input before wiring into `settings.json`.

---

## Credits & Inspiration

- **[Claude Code](https://github.com/anthropics/claude-code)** by Anthropic — the terminal-first AI coding tool
- **[compound-engineering](https://github.com/every-ai-labs/compound-engineering)** by Every AI Labs — multi-agent review workflows
- **[feature-dev plugin](https://github.com/anthropics/claude-code)** by the Claude Code team — code-architect, code-explorer, code-reviewer
- **[super-ralph-wiggum](https://www.aihero.dev/tips-for-ai-coding-with-ralph-wiggum)** by AI Hero — autonomous iteration loop pattern
- **[ccstatusline](https://github.com/sirmalloc/ccstatusline)** by sirmalloc — terminal statusline for Claude Code
- **[beautiful-mermaid](https://github.com/nicepkg/beautiful-mermaid)** by Craft — Mermaid diagram rendering
- **[llama.cpp](https://github.com/ggerganov/llama.cpp)** by Georgi Gerganov — local LLM inference
- **[RLAMA](https://github.com/dontizi/rlama)** by dontizi — local RAG system
- **[Firecrawl](https://firecrawl.dev/)** by Mendable — web scraping and content extraction
- **[Exa](https://exa.ai/)** — neural web search API
- **[Handy](https://github.com/cjpais/Handy)** by CJ Pais — push-to-talk speech-to-text
- **[matklad's ARCHITECTURE.md](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html)** — codebase documentation guide
- **[Open Souls](https://docs.souls.chat/)** — the AI souls paradigm

---

**Skills**: 40 | **Commands**: 30+ | **Hooks**: 7 | **CLI Tools**: 8

---

*"ἀπιστίῃ διαφυγγάνει μὴ γιγνώσκεσθαι."* — "Divine things escape recognition through disbelief." — Heraclitus
