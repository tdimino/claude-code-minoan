<p align="center">
  <img src="public/images/tanit.svg" alt="Symbol of Tanit" width="80"/>
</p>

<p align="center">
  <a href="#available-skills"><img src="https://img.shields.io/badge/Skills-45-green.svg" alt="Skills"></a>
  <a href="commands/README.md"><img src="https://img.shields.io/badge/Commands-43-purple.svg" alt="Commands"></a>
  <a href="hooks/README.md"><img src="https://img.shields.io/badge/Hooks-30-orange.svg" alt="Hooks"></a>
</p>

# Minoan Claude Code Configuration

A curated `~/.claude/` configuration for professional development workflows — skills, hooks, CLI tools, slash commands, MCP servers, and a VS Code extension.

<p align="center">
  <img src="public/images/be_minoan.jpg" alt="Minoan fresco" width="600"/>
</p>

## Repository Map

```
claude-code-minoan/
├── skills/                      # 45 custom skills across 5 categories
│   ├── core-development/        #   Architecture, task tracking, code search
│   ├── integration-automation/  #   Local ML, RAG, browser, telephony
│   ├── design-media/            #   Frontend, image gen, TTS, vision
│   ├── research/                #   Academic, web search, scraping
│   └── planning-productivity/   #   Session tracking, swarms, iteration loops
├── hooks/                       # Lifecycle hooks (handoffs, terminal UX, multi-response)
├── commands/                    # 43 slash commands (workflows, planning, code review)
├── agents/                      # Custom subagents (librarian, etc.)
├── bin/                         # CLI tools (session tracker, launchers, tmux)
├── tools/                       # Standalone tools (see github.com/tdimino/dabarat)
├── lib/                         # Shared libraries (tracker-utils.js)
├── extensions/                  # VS Code Claude Session Tracker extension
├── ghostty/                     # Ghostty terminal config for Claude Code
├── sounds/                      # Notification audio
└── docs/global-config/          # Full ~/.claude/ structure reference
```

Each folder has its own README with setup instructions, examples, and credits.

## Quick Start

```bash
# 1. Clone
git clone https://github.com/your-org/claude-code-minoan.git
cd claude-code-minoan

# 2. Start with the global CLAUDE.md template
cp CLAUDE.template.md ~/.claude/CLAUDE.md
# Edit ~/.claude/CLAUDE.md — add your Identity section, uncomment Always Loaded refs

# 3. Install skills
cp -r skills/*/* ~/.claude/skills/

# 4. Install commands
cp -r commands/* ~/.claude/commands/

# 5. Install hooks + sounds
cp -r hooks/* ~/.claude/hooks/
cp -r sounds ~/.claude/sounds/
chmod +x ~/.claude/hooks/*.py ~/.claude/hooks/*.sh

# 6. Install CLI tools
cp bin/* ~/.local/bin/
mkdir -p ~/.claude/lib && cp lib/* ~/.claude/lib/

# 7. Install VS Code extension
cd extensions/claude-session-tracker
npm install && npm run compile
npx @vscode/vsce package --no-dependencies
code --install-extension claude-session-tracker-*.vsix
```

Configure hooks in `~/.claude/settings.json` — see [hooks/README.md](hooks/README.md) for the full settings block.

---

## Deep Dives

### [Skills](skills/README.md) — 45 skills across 5 categories

Custom Claude Code capabilities organized by domain. Each skill has a `SKILL.md` entry point, optional scripts, and reference docs.

**Highlights**:

| Category | Count | Notable Skills |
|----------|-------|---------------|
| Core Development | 8 | `agents-md-manager`, `beads-task-tracker`, `architecture-md-builder`, `claude-agent-sdk`, `skill-optimizer` |
| Integration & Automation | 17 | `llama-cpp`, `rlama`, `classical-887`, `slack`, `Firecrawl`, `codex-orchestrator` |
| Design & Media | 7 | `gemini-claude-resonance`, `nano-banana-pro`, `speak-response` |
| Research | 5 | `academic-research`, `linear-a-decipherment`, `exa-search`, `Firecrawl` |
| Planning & Productivity | 5 | `minoan-swarm`, `super-ralph-wiggum`, `claude-tracker-suite` |

Toggle skills on/off: `./skills/skill-toggle.sh`

> **Claude 4.6 Prompting Alignment (Feb 2026)**: All agentic skills (`minoan-swarm`, `super-ralph-wiggum`, `Firecrawl`, `osgrep-reference`, `claude-agent-sdk`, `skill-optimizer`) updated to follow [Anthropic's Claude 4.6 prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)—softer tool-use language, factual quality criteria over motivational framing, effort parameter guidance, structured state management.

---

### [Hooks](hooks/README.md) — Lifecycle event scripts

Scripts that run in response to Claude Code events — terminal UX, crash-resilient session handoffs, cross-repo git tracking, and multi-response sampling.

```
UserPromptSubmit ──→ multi-response-prompt.py    (/5x trigger)
PreToolUse ────────→ on-thinking.sh              (🔴 repo-icon + title)
                   → git-track.sh               (Bash: log git commands to JSONL)
PostToolUse ───────→ git-track-post.sh           (Bash: capture commit hashes)
                   → plan-rename.py              (Write/Edit/MultiEdit: random→dated slug)
                   → plan-session-rename.py      (Write: auto-title session from plan H1)
Stop ──────────────→ on-ready.sh + stop-handoff.py (🟢 title:subtitle + 5-min checkpoint)
PreCompact ────────→ precompact-handoff.py       (full handoff before compaction)
SessionEnd ────────→ precompact-handoff.py       (handoff on graceful exit)
                   → git-track-rebuild.py        (rebuild git tracking index)
                   → plan-cleanup-symlinks.py    (remove plan forwarding symlinks)
```

**Terminal Title**: Two-tier format with repo-type emoji icons — `🔴 🐍 claudicle: Building test suite`. Icons auto-detected from CLAUDE.md keywords and project files. Main title persists across events; subtitle updates from transcript.

**Session Handoff System**: Three hooks ensure context survives compaction, graceful exits, and crashes. Writes structured YAML to `~/.claude/handoffs/` with objective, decisions, blockers, and next steps. Auto-maintains `INDEX.md`.

**Git Tracking**: Three hooks intercept git commands across any directory, capturing repos, branches, operations, and commit hashes. Builds a bidirectional session↔repo index. Query with `getSessionsForRepo()` / `getReposForSession()` or generate a dashboard with `/session-report`.

**Plan Auto-Naming**: Renames randomly-named plan files (e.g. `tingly-humming-simon.md`) to dated slugs (e.g. `2026-02-17-auto-rename-plan-files-hook.md`) by extracting the H1 header. Creates forwarding symlinks for mid-session continuity; cleaned up on SessionEnd.

**Session Auto-Titling**: When a plan file is created, `plan-session-rename.py` immediately extracts the H1 header and sets the session's `customTitle` in `sessions-index.json`—no LLM call, pure local, ~10ms. If the session isn't yet in the index (Claude Code writes lazily), a `.pending-title` breadcrumb is saved for `session-tags-infer.py` to apply on next Stop.

---

### [Commands](commands/README.md) — 43 slash commands

Markdown templates invoked as `/command-name`. Key workflows:

| Command | Purpose |
|---------|---------|
| `/requirements-start` | Structured project planning through discovery questions |
| `/workflows:review` | 12+ parallel agent code review |
| `/code-review` | PR review with structured output |
| `/audit-plans` | Plan completeness auditing |
| `/workflows:plan` | Transform descriptions into implementation plans |
| `/session-report` | Markdown dashboard: sessions, git activity, commits, repos |

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
| `resume-in-vscode.sh` | Resume a session in a new Ghostty/VS Code/Cursor terminal |
| `cc` / `cckill` / `ccls` / `ccpick` | Quick launchers and session management |

All CLIs share `lib/tracker-utils.js` for session parsing and status detection. The `resume-in-vscode.sh` script auto-detects the project directory from the session ID (via `decodeProjectPath`) and `cd`s there before resuming — no `--project` flag needed.

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

## [Ghostty Config](ghostty/README.md) — Terminal for Claude Code

Optimized [Ghostty](https://ghostty.org/) config: Catppuccin Mocha/Latte theme, JetBrains Mono, 100K scrollback, split panes for parallel sessions, prompt jumping, and session persistence.

```bash
cp ghostty/config ~/Library/Application\ Support/com.mitchellh.ghostty/config
```

Key bindings: `Cmd+D` split right, `Cmd+Alt+Enter` zoom split, `Cmd+Up/Down` jump prompts. See [ghostty/README.md](ghostty/README.md) for full keybinding reference.

Pair with **ccstatusline** (`npm install -g ccstatusline`) and **lazygit** (`brew install lazygit`) in a side split.

---

## Teammate Onboarding

**[`CLAUDE.template.md`](CLAUDE.template.md)** — A teammate-ready global config with all tooling conventions and no personal details.

```bash
cp CLAUDE.template.md ~/.claude/CLAUDE.md
```

Then customize:
- **Identity**: Create `~/.claude/userModels/{yourname}/{yourname}Model.md` and uncomment the `@reference`
- **Always Loaded**: Uncomment `@agent_docs/` references you want active in every session
- **On-Demand References**: Add paths to docs Claude should read when relevant

See [`docs/global-config/README.md`](docs/global-config/README.md) for the full `~/.claude/` structure reference, including userModel examples.

The template includes: engineering principles, tool preferences (OSGrep, Firecrawl, uv, RLAMA retrieve-only default), interaction conventions, planning patterns, session continuity via handoffs, and infrastructure notes.

---

## Contributing

1. **Skills**: Follow the `SKILL.md` + `scripts/` + `references/` structure. Test across projects.
2. **Commands**: Use frontmatter (`description`, `argument-hint`). Keep single-purpose.
3. **Hooks**: Test with piped JSON input before wiring into `settings.json`.

---

## Companion Projects

### [Claudicle](https://github.com/tdimino/claudicle) — Soul Agent Framework

Open-source 4-layer soul architecture (Identity, Cognition, Memory, Channels) that gives Claude Code sessions persistent personality, memory, and behavioral continuity. The soul hooks in this repo (`soul-activate.py`, `soul-deregister.py`, `soul-registry.py`) register sessions with the Claudicle daemon. Souls like Kothar—the Ugaritic craftsman god—maintain identity across sessions, respond on Slack, and dream in the Daimon Chamber.

```bash
git clone https://github.com/tdimino/claudicle
cd claudicle && ./setup.sh --personal
# then in any Claude Code session: /ensoul
```

### [Dabarat](https://github.com/tdimino/dabarat) — Live Markdown Preview

AI-native markdown previewer with annotations, bookmarks, and live reload. Zero dependencies. The `dabarat-open.py` hook auto-opens new `.md` files in a browser tab as Claude writes them—plans, docs, and READMEs render live. Multi-tab support, margin annotations, and global bookmarks saved to `~/.claude/bookmarks/`.

```bash
git clone https://github.com/tdimino/dabarat
cd dabarat && pip install -e .
dabarat plan.md               # preview in browser
dabarat --add spec.md         # add tab to running instance
```

---

## Credits & Inspiration

- **[Claude Code](https://github.com/anthropics/claude-code)** by Anthropic — the terminal-first AI coding tool
- **[Open Souls](https://github.com/opensouls/opensouls)** — the AI souls paradigm
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

---

**Skills**: 45 | **Commands**: 43 | **Hooks**: 29 | **CLI Tools**: 8

---

*"ἀπιστίῃ διαφυγγάνει μὴ γιγνώσκεσθαι."* — "Divine things escape recognition through disbelief." — Heraclitus
