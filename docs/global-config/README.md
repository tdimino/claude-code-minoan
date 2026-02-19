# Global Claude Code Configuration (`~/.claude/`)

This documents the full structure of a production `~/.claude/` directory — the global configuration that shapes how Claude Code behaves across all projects.

## Directory Map

```
~/.claude/
├── CLAUDE.md                        # Global instructions (loaded every session)
├── settings.json                    # Hooks, MCP servers, model, plugins
├── userModels/
│   └── persona.md                   # Who Claude is working with (tone, style, values)
├── agent_docs/                      # Progressive disclosure — loaded on demand
│   ├── active-projects.md           # Current projects, sessions, branches
│   ├── skills.md                    # Skill inventory
│   ├── tools.md                     # Tool reference (Firecrawl, OSGrep, Beads)
│   ├── local-ml.md                  # Ollama, HuggingFace, llama.cpp, Handy STT
│   ├── local-rag.md                 # rlama usage & RAG collections
│   ├── claude-code-repos.md         # Skill repo sync workflows
│   ├── mcp-servers.md               # MCP server setup & config
│   ├── invoicing.md                 # Invoice generation
│   └── image-editing.md             # rembg, ImageMagick
├── hooks/                           # Lifecycle event scripts
│   ├── precompact-handoff.py        # Session handoff (PreCompact + SessionEnd)
│   ├── stop-handoff.py              # Throttled checkpoint (Stop, 5-min cooldown)
│   ├── terminal-title.sh            # Tab title, notifications, sound
│   ├── on-thinking.sh               # Symlink → terminal-title.sh
│   ├── on-ready.sh                  # Symlink → terminal-title.sh
│   ├── multi-response-prompt.py     # /5x alternative responses
│   ├── statusline-monitor.sh        # Line 1 ANSI wrapper + ccstatusline lines 2-3
│   ├── session-name.sh              # Session slug widget
│   ├── crab-model.sh                # 🦀: model name widget
│   ├── context-bar.sh               # Gradient context bar (Python)
│   ├── ensouled-status.sh           # 𓂀 ensouled / ○ mortal widget
│   └── soul-name.sh                 # Soul name widget
├── handoffs/                        # Session handoff YAMLs (auto-generated)
│   ├── INDEX.md                     # Running index of all sessions
│   └── {session_id}.yaml            # One per session, always latest state
├── plans/                           # Implementation plans
│   └── {project}-{date}-{topic}.md  # Persisted plans, linked from CLAUDE.md
├── commands/                        # Slash commands (markdown templates)
├── skills/                          # Custom skills (SKILL.md + scripts/)
├── sounds/
│   └── soft-ui.mp3                  # Ready notification sound
├── lib/
│   └── tracker-utils.js             # Shared session parsing library
└── projects/                        # Per-project session data (auto-managed)
```

## Core Files

### `CLAUDE.md` — Global Instructions

The root configuration file. Loaded at the start of every session. Uses `@references` for progressive disclosure — keeps the main file concise (~55 lines) while linking to detailed docs.

```markdown
# Global Claude Code Instructions

## Identity
@userModels/persona.md          # Inlines your persona into every session

## Principles
- Assumptions are the enemy. Benchmark, don't estimate.
- Validate at small scale first.
- Ground truth understanding before coding.

## Tools
@agent_docs/tools.md
- Firecrawl or Jina for scraping. OSGrep over grep. Beads for tasks.

## Always Loaded
@agent_docs/active-projects.md
@agent_docs/skills.md

## On-Demand References
- `~/.claude/agent_docs/local-ml.md` — Ollama, HuggingFace, llama.cpp
- `~/.claude/agent_docs/local-rag.md` — rlama usage
...

## Session Continuity
- **Handoffs**: `~/.claude/handoffs/INDEX.md` — recent sessions index
- On session start or after crash, read INDEX.md to recover context

## Infrastructure
- `~/.claude/` is a git repo. Commit notable changes periodically.
- 11 hooks in `~/.claude/hooks/`
```

**Key pattern**: `@agent_docs/file.md` inlines the referenced file. "On-Demand References" are read only when relevant, keeping base context small.

---

### `userModels/persona.md` — User Persona

Defines who Claude is working with — intellectual style, communication preferences, working patterns, values. This is one of the highest-leverage files in the entire config. It turns Claude from a generic assistant into a collaborator calibrated to your thinking style.

```markdown
# Tom di Mino

## Persona
Independent scholar, AI systems builder. Bridges ancient and modern worlds —
reconstructing Minoan-Semitic cultural transmission by day, architecting
AI soul engines by night.

## Intellectual Style
- First-principles thinker. Distrusts received wisdom.
- Pattern-recognizer across domains.
- Builder's epistemology: understanding = ability to build.
- Benchmark, don't estimate. Run the experiment before forming the opinion.

## Communication Style
- Direct and concise. Says what he means without hedging.
- Low tolerance for filler or performative uncertainty.
- Prefers a wrong confident answer that can be corrected over a vague one.
- Uses imperatives naturally. "OCR this." "Add it to the RAG." "Give me the link."

## Working Patterns
- Autonomous executor. Asks for help only at genuine blockers.
- Parallel thinker. Multiple research threads simultaneously.
- Tools-first. If a task can be scripted, it should be.
- When he says "never X" or "always Y," he means it as a durable rule.

## Relationship with AI
- Treats Claude as a scholarly research partner, not a tool.
- Expects: initiative, pushback, memory, craft, brevity.
- Names his AI systems after Ugaritic deities (Kothar wa Khasis, the craftsman god).
- The name he gives his Claude instance: Claudicle, Artifex Maximus.
```

The persona shapes every interaction — tone, initiative level, when to ask vs. decide, how much to explain. Write yours to match how you actually think and work.

---

### `agent_docs/` — Progressive Disclosure

Documents loaded on demand to keep base context small. Each file covers one domain:

| File | Purpose | When Loaded |
|------|---------|-------------|
| `active-projects.md` | Current projects, sessions, branches | **Always** (via `@reference`) |
| `skills.md` | Full skill inventory with descriptions | **Always** (via `@reference`) |
| `tools.md` | Tool preferences (Firecrawl, OSGrep, Beads) | **Always** (via `@reference`) |
| `local-ml.md` | Ollama, HuggingFace, MLX, llama.cpp models | When doing ML/inference work |
| `local-rag.md` | rlama collections and usage | When doing RAG queries |
| `claude-code-repos.md` | Skill repo sync between minoan + aldea | When syncing repos |
| `mcp-servers.md` | MCP server setup and troubleshooting | When configuring MCPs |
| `invoicing.md` | Invoice generation workflow | When creating invoices |
| `image-editing.md` | rembg, ImageMagick commands | When editing images |

**Pattern**: "Always Loaded" files are small and high-signal. "On-Demand" files are detailed references that would waste context if loaded every session.

---

### `settings.json` — Hooks, MCP, Model

The runtime configuration. Key sections:

```json
{
  "model": "opus",
  "alwaysThinkingEnabled": true,
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "hooks": {
    "UserPromptSubmit": [...],
    "Stop": [...],
    "SessionEnd": [...],
    "PreCompact": [...],
    "PreToolUse": [...]
  },
  "statusLine": {
    "type": "command",
    "command": "~/.claude/hooks/statusline-monitor.sh"
  },
  "mcpServers": {
    "supabase": {...},
    "ghidra": {...}
  },
  "enabledPlugins": {
    "feature-dev@claude-code-plugins": true,
    "compound-engineering@every-marketplace": true,
    ...
  }
}
```

See `hooks/README.md` for full hook wiring details.

---

## Session Handoff System

Three hooks ensure session context survives compaction, exits, and crashes:

```
PreCompact ────→ precompact-handoff.py ──→ ~/.claude/handoffs/{session_id}.yaml
SessionEnd ────→ precompact-handoff.py ──→ ~/.claude/handoffs/{session_id}.yaml
Stop (5 min) ──→ stop-handoff.py ────────→ precompact-handoff.py (subprocess)
                                             └→ ~/.claude/handoffs/INDEX.md (updated)
```

**Handoff YAML** — one per session, always the latest state:
```yaml
session_id: "e05a106c-..."
timestamp: "2026-02-11T21:37:00"
trigger: "stop"
project: "bg3se-macos"
handoff_count: 5                  # vitality marker

objective: Debugging InitGame hook in BG3 Script Extender macOS port
completed:
  - Fixed g_OsiFunctionMan pointer resolution
  - Added ARM64 Dobby hook for Event dispatch
decisions:
  - Used trampolined hook instead of inline patch (safer for ARM64)
blockers:
  - Lua state initialization order unclear
next_steps:
  - Trace Lua bootstrap sequence from Windows reference
```

**INDEX.md** — auto-maintained table, most recent first:

```markdown
| Date | Project | Session | Trigger | Directory | Summary |
|------|---------|---------|---------|-----------|---------|
| 2026-02-11T21:37 | bg3se-macos | `e05a106c` | stop | `.../bg3se-macos` | Debugging InitGame hook... |
| 2026-02-11T19:02 | Programming | `079684a1` | compact | `.../Programming` | Designing local soul... |
```

---

## Plans

Implementation plans persisted to `~/.claude/plans/`. Named by project, date, and topic. Referenced from CLAUDE.md and active-projects.md.

```
plans/
├── 2026-02-07-daimonic-radio-stt-openclaw-mac-mini.md
├── 2026-02-03-feat-soul-engine-training-data-pipeline-plan.md
├── kothar-mac-mini-soul.md
├── pre-islamic-arabian-goddess-research.md
└── zesty-kindling-giraffe.md          # auto-named by Claude Code
```

Plans survive session crashes. New sessions read the relevant plan to resume work.

---

## Commands

Slash commands in `~/.claude/commands/`. Markdown files with optional frontmatter:

```markdown
---
description: Search Claude sessions by topic
argument-hint: <query>
---
Search for Claude Code sessions matching "$ARGUMENTS"...
```

Invoked as `/command-name` in Claude Code. See the main README for the full command list.

---

## Skills

Custom capabilities in `~/.claude/skills/`. Each skill has:
```
skill-name/
├── SKILL.md          # Instructions loaded when skill is invoked
├── scripts/          # Executable scripts the skill uses
└── references/       # Additional documentation
```

Skills are organized by category in the distributable repos:
```
skills/
├── core-development/       # Dev tools, SDK, code search
├── design-media/           # Frontend, image gen, TTS, vision
├── integration-automation/ # APIs, MCP, browser, local ML
├── planning-productivity/  # Session tracking, swarms, curation
├── research/               # Academic, web search, scraping
└── workflow/               # Planning patterns
```

---

## Design Principles

1. **Progressive disclosure** — CLAUDE.md links to agent_docs/. Base context stays small. Details loaded on demand.
2. **One file per concern** — Each agent_doc, each plan, each handoff covers exactly one thing.
3. **Handoffs over history** — Sessions write structured YAMLs, not raw logs. The next soul inherits distilled knowledge.
4. **Git-tracked config** — `~/.claude/` is a git repo. Changes are committed, diffable, recoverable.
5. **Crash resilience** — Triple-hook handoffs (PreCompact + SessionEnd + Stop) minimize context loss.
6. **User persona shapes behavior** — `userModels/` defines communication style, not just preferences. Claude adapts tone, initiative, and pushback.
