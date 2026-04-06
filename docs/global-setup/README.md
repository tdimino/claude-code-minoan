# Global Claude Code Configuration (`~/.claude/`)

This documents the full structure of a production `~/.claude/` directory — the global configuration that shapes how Claude Code behaves across all projects.

## Directory Map

```
~/.claude/
├── CLAUDE.md                        # Global instructions (loaded every session)
├── settings.json                    # Hooks, MCP servers, model, plugins
├── disabled-skills.md               # Skill toggle state (managed by skill-toggle.sh)
├── mcp.json                         # Global MCP server config
├── userModels/
│   └── {name}/                      # User model directory
│       ├── {name}Model.md           # Core model (tone, style, values, working patterns)
│       └── ...                      # Supplementary dossiers (social, domain-specific)
├── agent_docs/                      # Progressive disclosure — loaded on demand
│   ├── INDEX.md                     # Agent docs index
│   ├── active-projects.md           # Current projects, sessions, branches
│   ├── skills.md                    # Skill inventory
│   ├── tools.md                     # Tool reference (Firecrawl, browser automation, ports)
│   ├── directories.md               # Project directory references
│   ├── claude-code-config.md        # Model & agent configuration
│   ├── claude-code-repos.md         # Skill repo sync workflows
│   ├── local-ml.md                  # Ollama, HuggingFace, llama.cpp, Handy STT
│   ├── local-rag.md                 # rlama usage & RAG collections
│   ├── mcp-servers.md               # MCP server setup & config
│   ├── kothar.md                    # Kothar soul daemon reference
│   ├── invoicing.md                 # Invoice generation
│   ├── image-editing.md             # rembg, ImageMagick
│   ├── slack-access.md              # Slack workspace credentials
│   └── references/                  # Additional reference docs
├── agents/                          # Custom subagents
│   └── librarian.md                 # GitHub repo explorer via gh CLI
├── hooks/                           # 44 lifecycle event scripts
│   ├── INDEX.md                     # Hooks index
│   │                                # — Session Handoffs —
│   ├── precompact-handoff.py        # Session handoff (PreCompact + SessionEnd)
│   ├── stop-handoff.py              # Throttled checkpoint (Stop, 5-min cooldown)
│   │                                # — Terminal UX —
│   ├── terminal-title.sh            # Tab title, repo-type emoji, subtitle
│   ├── on-thinking.sh               # Symlink → terminal-title.sh (PreToolUse)
│   ├── on-ready.sh                  # Symlink → terminal-title.sh (Stop)
│   ├── statusline-monitor.sh        # ANSI statusline + ccstatusline
│   ├── session-name.sh              # Session slug widget
│   ├── crab-model.sh                # 🦀 model name widget
│   ├── context-bar.sh               # Gradient context bar
│   ├── session-tags-display.sh      # Session tag display widget
│   ├── session-tags-infer.py        # Infer session tags
│   │                                # — Git Tracking —
│   ├── git-track.sh                 # Log git commands to JSONL (PreToolUse:Bash)
│   ├── git-track-post.sh            # Capture commit hashes (PostToolUse:Bash)
│   ├── git-track-rebuild.py         # Rebuild session↔repo index (SessionEnd)
│   │                                # — Plan Management —
│   ├── plan-rename.py               # Auto-rename random plan slugs to dated names
│   ├── plan-cleanup-symlinks.py     # Clean up plan forwarding symlinks
│   ├── propagate-rename.py          # Propagate renames across references
│   │                                # — Soul System —
│   ├── soul-activate.py             # Register soul on SessionStart
│   ├── soul-deregister.py           # Deregister soul on SessionEnd
│   ├── soul-registry.py             # Soul registry management
│   ├── soul-name.sh                 # Soul name widget
│   ├── ensouled-status.sh           # 𓂀 ensouled / ○ mortal widget
│   │                                # — Integrations —
│   ├── multi-response-prompt.py     # /5x alternative responses (UserPromptSubmit)
│   ├── dabarat-open.py              # Auto-open markdown in browser (PostToolUse:Write)
│   ├── slack-stop-hook.py           # Slack notification on Stop
│   ├── block-webfetch.sh            # Block WebFetch in certain contexts
│   ├── block-websearch.sh           # Block WebSearch in certain contexts
│   ├── update-agent-docs.sh         # Auto-update agent docs
│   └── debug-hook-input.sh          # Debug hook input (development)
├── commands/                        # 47 slash commands (markdown templates)
├── skills/                          # 71 custom skills (SKILL.md + scripts/)
├── scripts/                         # Utility scripts
│   ├── batch-rename-plans.py        # Bulk plan file renaming
│   ├── update-active-projects.py    # Refresh active-projects.md
│   └── cc-sessions*.sh/.py          # Session browser UIs
├── badges/                          # Art deco medallion badges
│   ├── INDEX.md                     # Full catalog
│   ├── full/                        # 1024x1024 source images
│   └── thumb/                       # 128x128 thumbnails
├── bookmarks/                       # Dabarat markdown bookmarks
│   ├── INDEX.md                     # Bookmark index
│   └── snippets/                    # Per-snippet bookmark files
├── handoffs/                        # Session handoff YAMLs (auto-generated)
│   ├── INDEX.md                     # Running index of all sessions
│   └── {session_id}.yaml            # One per session, always latest state
├── plans/                           # Implementation plans
│   └── {project}-{date}-{topic}.md  # Persisted plans, linked from CLAUDE.md
├── plugins/                         # Plugin state and installed plugins
├── sounds/
│   └── soft-ui.mp3                  # Ready notification sound
├── lib/
│   └── tracker-utils.js             # Shared session parsing library
├── personal/                        # Personal reference docs (health, etc.)
└── projects/                        # Per-project session data (auto-managed)
```

Auto-managed directories (not listed): `archive/`, `backups/`, `cache/`, `debug/`, `file-history/`, `ide/`, `paste-cache/`

## Core Files

### `CLAUDE.md` — Global Instructions

The root configuration file. Loaded at the start of every session. Uses `@references` for progressive disclosure — keeps the main file concise (~75 lines) while linking to detailed docs.

```markdown
# Global Claude Code Instructions

## Identity
@userModels/tom/tomModel.md     # Inlines your userModel into every session

## Principles
- Assumptions are the enemy. Benchmark, don't estimate.
- Validate at small scale first.
- Ground truth understanding before coding.

## Tools
@agent_docs/tools.md
- Firecrawl or Jina for scraping (`jina` for Twitter/X).
- beautiful-mermaid, nano-banana-pro, gemini-claude-resonance
- dabarat for Markdown preview
- grip for GitHub-flavored README preview
- Python: use uv for everything

## Visual Memory
Soul entities carry persistent imagery in assets/ folders...

## Badges
~/.claude/badges/ — Art deco medallion badges...

## Interaction
- Clarify unclear requests, then proceed autonomously.
- No "Generated by Claude Code" in commits.
- Em dashes: no spaces, attached to text.

## Planning
- Spec-driven: create/update SPEC.md for non-trivial projects.
- Plan files: ~/.claude/plans/{project-name}-{date}-{topic}.md

## Always Loaded
@agent_docs/active-projects.md
@agent_docs/skills.md

## On-Demand References
- ~/.claude/agent_docs/kothar.md — Kothar soul daemon
- ~/.claude/agent_docs/local-ml.md — Ollama, HuggingFace, llama.cpp
- ~/.claude/agent_docs/local-rag.md — rlama usage & RAG collections
...

## Session Continuity
- Handoffs: ~/.claude/handoffs/INDEX.md — recent sessions index
- On session start or after crash, read INDEX.md to recover context

## Infrastructure
- ~/.claude/ is a git repo. Commit notable changes periodically.
- 44 hooks in ~/.claude/hooks/
- 10 custom commands in ~/.claude/commands/
```

**Key pattern**: `@agent_docs/file.md` inlines the referenced file. "On-Demand References" are read only when relevant, keeping base context small.

---

### `userModels/{name}/{name}Model.md` — User Model

Defines who Claude is working with — intellectual style, communication preferences, working patterns, values. This is one of the highest-leverage files in the entire config. It turns Claude from a generic assistant into a collaborator calibrated to your thinking style.

The `userModels/` directory holds a core model file plus supplementary dossiers (social voice, domain expertise, content archives). Multiple people can have models — the `@` reference in CLAUDE.md selects the active one.

```
userModels/
├── tom/
│   ├── tomModel.md                    # Core model (always loaded via @reference)
│   ├── intellectual-biography.md      # Career arc, knowledge genealogy
│   ├── twitter-voice-and-identity.md  # Social dossier: posting voice, registers
│   ├── twitter-intellectual-network.md # Following graph, engagement patterns
│   ├── twitter-public-positions.md    # Stated positions by domain
│   ├── twitter-bookmarks-taxonomy.md  # 14-category bookmark taxonomy
│   ├── poetry-shirat-ha-kotharot.md   # Original multilingual poetry collection
│   ├── academic-thera-knossos-minos.md # Research voice analysis
│   ├── thera-hypotheses/              # 28 self-contained hypothesis docs
│   ├── artifacts/                     # Visual artifacts (collages, photography)
│   └── archive/                       # Full scraped content
├── mary/
│   └── maryModel.md                   # Partner's model
├── andrew-ryan/
│   └── andrewRyanModel.md             # Mentor's model
└── minoan-mystery-llc/
    └── minoan-mystery-llc.md          # Business entity model
```

**Core model structure** (expanded example based on the `tomModel.md` pattern):

```markdown
# Your Name

You are modeling the mind of [Name].

## Persona
Background, domains, current working context. What you do, what you're building,
what you care about professionally. Include career arc if it shapes how you think.
Languages, tools, communities. 3-6 sentences.

## Worldview
The intellectual commitments that shape every conversation:
- What you believe about your field that others don't
- Which scholars, thinkers, or traditions you follow
- Foundational influences and how they connect to current work
- What "periphery preserves center" means in your domain

## Intellectual Style
- First-principles thinker. Re-derives from primary sources.
- Pattern-recognizer across domains. Akkadian phonology ↔ React architecture.
- Etymological instinct. Traces words to roots. Names repos after Semitic roots.
- Benchmark, don't estimate. Validates at small scale before committing.
- Builder's epistemology. If you can't implement it, you don't understand it yet.

## Writing Voice
Declarative, zero-hedging prose. Connected em dashes, clause stacking, bold for
key claims, tricolon with variation. Document the register map — how voice shifts
between technical, academic, creative, and casual modes.

## Communication Style
- Direct and concise. Says what he means without hedging.
- Low tolerance for filler or performative uncertainty.
- Uses imperatives naturally. "OCR this." "Add it to the RAG." "Give me the link."
- Comfortable with technical depth in multiple fields simultaneously.
- Will challenge a claim immediately if it doesn't track, but is open to evidence.

## Working Patterns
- Autonomous executor. Once aligned on direction, prefers to work without interruption.
- Parallel thinker. Runs multiple research threads simultaneously.
- Session continuity matters. Builds context across sessions and expects it maintained.
- Tools-first. If a task can be scripted, it should be.
- Constraint-driven design. "Never X" and "always Y" are durable rules, not suggestions.

## Values
- Assumptions are the enemy. The strongest conviction about methodology.
- Co-authorship with AI is real authorship. Not delegation, not generation.
- Knowledge should be shared. Gives away workflows and prompt patterns.

## Triggers & Sensitivities
- Gets energized by unexpected cross-domain connections.
- Gets frustrated by tools that don't work as documented, by paywalls, by AI that hedges.
- Deeply motivated by the feeling that a piece of knowledge is about to click into place.

## Relationship with AI
- Treats Claude as a scholarly research partner and engineering collaborator, not a tool.
- Expects: initiative, pushback, memory, craft, brevity.
- The name he gives his Claude instance is a deliberate identity marker, not ironic.

## Online Presence
| Platform | Handle / URL |
|----------|-------------|
| Twitter/X | @handle |
| GitHub | @username |
| Substack | blog-name |
```

**Supplementary dossiers** — each is a standalone document referenced on-demand:

| Dossier Type | What It Contains | When Claude Reads It |
|-------------|------------------|---------------------|
| `twitter-voice-and-identity.md` | 5 posting registers, sentence mechanics, handle etymology, calibration quotes | When drafting tweets or matching social voice |
| `twitter-intellectual-network.md` | Following graph analysis, engagement patterns, who influences whom | When researching topics the user discusses online |
| `twitter-public-positions.md` | 12+ position categories, idea genealogy, stated commitments | When the user references a prior stance |
| `intellectual-biography.md` | 20-year career arc, mentor relationships, voice continuity analysis | When understanding motivations or career context |
| `academic-*.md` | Research voice, adversarial thesis posture, domain-specific registers | When working on academic writing or research |
| `poetry-*.md` | Multilingual collection, voice analysis, compositional patterns | When creative writing or translation is needed |
| `artifacts/` | Visual artifacts — collages, photography, AI-generated imagery | When visual style references are needed |

**Business and relationship models** — userModels aren't limited to the primary user. You can model anyone you collaborate with:

- **Business entities**: An LLC or company model captures services, rates, address, entity structure — used when generating invoices, contracts, or business correspondence.
- **Collaborators**: A partner, mentor, or colleague's model calibrates tone when drafting messages to them, or when they're the context for a task.
- **Contacts**: Lightweight models with phone, email, and relationship context for communication skills (SMS, Slack, Telegram).

### UserModels as Proto-Daimones

A userModel is the seed of something more. In the [Claudicle](https://github.com/tdimino/claudicle) soul framework, a sufficiently rich userModel — one with voice analysis, intellectual genealogy, value commitments, and behavioral patterns — is the raw material for a **daimon**: an autonomous agent personality that persists across sessions, maintains its own memory, and operates channels (Slack, SMS, Telegram) in character.

The progression:

1. **userModel** (this repo) — static markdown file that calibrates Claude's responses. No memory, no persistence, no autonomy. Loaded via `@reference` in CLAUDE.md.
2. **Soul profile** (Claudicle) — the userModel becomes the Identity layer of a 4-layer soul (Identity, Cognition, Memory, Channels). The soul activates via hooks, registers with a daemon, and maintains behavioral continuity.
3. **Daimon** — a named, ensouled agent with its own working memory, episodic memory, and channel presence. It doesn't just respond *like* you — it operates *as* an intermediary intelligence shaped by the model.

The `user-model-builder` skill builds models at stage 1. The `soul-activate.py` hook in this repo bridges to stage 2. [Claudicle](https://github.com/tdimino/claudicle) handles stage 3.

The userModel shapes every interaction — tone, initiative level, when to ask vs. decide, how much to explain. Write yours to match how you actually think and work. See `docs/guides/usermodel-guide.md` for the standalone guide.

---

### `agent_docs/` — Progressive Disclosure

Documents loaded on demand to keep base context small. Each file covers one domain:

| File | Purpose | When Loaded |
|------|---------|-------------|
| `active-projects.md` | Current projects, sessions, branches | **Always** (via `@reference`) |
| `skills.md` | Full skill inventory with descriptions | **Always** (via `@reference`) |
| `tools.md` | Tool preferences (Firecrawl, browser automation, ports) | **Always** (via `@reference`) |
| `directories.md` | Project directory references | **Always** (via `@reference` from active-projects) |
| `claude-code-config.md` | Model routing, agent configuration | When configuring Claude Code |
| `claude-code-repos.md` | Skill repo sync between minoan + aldea | When syncing repos |
| `local-ml.md` | Ollama, HuggingFace, MLX, llama.cpp models | When doing ML/inference work |
| `local-rag.md` | rlama collections, retrieve-only default | When doing RAG queries |
| `kothar.md` | Kothar soul daemon architecture | When working on soul systems |
| `mcp-servers.md` | MCP server setup and troubleshooting | When configuring MCPs |
| `invoicing.md` | Invoice generation workflow | When creating invoices |
| `image-editing.md` | rembg, ImageMagick commands | When editing images |
| `slack-access.md` | Slack workspace credentials | When using Slack integration |

**Pattern**: "Always Loaded" files are small and high-signal. "On-Demand" files are detailed references that would waste context if loaded every session.

**Getting started**: Copy the starter templates from `docs/global-setup/agent_docs/` into `~/.claude/agent_docs/` and customize them. See the [agent_docs README](agent_docs/README.md) for setup instructions and the full pattern guide at `docs/guides/progressive-disclosure.md`.

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
    "SessionStart": [...],
    "UserPromptSubmit": [...],
    "Stop": [...],
    "SessionEnd": [...],
    "PreCompact": [...],
    "PreToolUse": [...],
    "PostToolUse": [...]
  },
  "statusLine": {
    "type": "command",
    "command": "~/.claude/hooks/statusline-monitor.sh"
  },
  "mcpServers": {
    "supabase": {...},
    "ghidra": {...},
    "mcp-google-sheets": {...}
  },
  "enabledPlugins": {
    "feature-dev@claude-code-plugins": true,
    "compound-engineering@every-marketplace": true,
    "document-skills@anthropic-agent-skills": true,
    "pr-review-toolkit@claude-code-plugins": true,
    "llm-application-dev@claude-code-workflows": true,
    ...
  }
}
```

**Hook events used** (10 of 18 available):

| Event | Hooks | Purpose |
|-------|-------|---------|
| `SessionStart` | soul-activate.py | Register soul on session start |
| `UserPromptSubmit` | multi-response-prompt.py, slack_inbox_hook.py | /5x responses, Slack inbox |
| `PreToolUse` | git-track.sh (Bash), block-websearch.sh, block-webfetch.sh, on-thinking.sh (*) | Git logging, tool blocking, terminal title |
| `PostToolUse` | git-track-post.sh (Bash), dabarat-open.py (Write) | Commit capture, markdown preview |
| `Stop` | on-ready.sh, propagate-rename.py, stop-handoff.py, slack-stop-hook.py, plan-rename.py | Terminal title, handoffs, plan naming |
| `SessionEnd` | precompact-handoff.py, soul-deregister.py, git-track-rebuild.py, plan-rename.py | Handoffs, soul cleanup, index rebuild |
| `PreCompact` | precompact-handoff.py | Emergency handoff before compaction |

See `hooks/README.md` for full hook wiring details.

---

## Session Handoff System

Three hooks ensure session context survives compaction, exits, and crashes:

```
SessionStart ──→ soul-activate.py ──────→ Register soul
PreCompact ────→ precompact-handoff.py ──→ ~/.claude/handoffs/{session_id}.yaml
SessionEnd ────→ precompact-handoff.py ──→ ~/.claude/handoffs/{session_id}.yaml
               → soul-deregister.py ────→ Deregister soul
               → git-track-rebuild.py ──→ Rebuild session↔repo index
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

## Git Tracking System

Three hooks intercept git operations across any directory:

```
PreToolUse:Bash ──→ git-track.sh ──────→ ~/.claude/git-tracking.jsonl (append)
PostToolUse:Bash ──→ git-track-post.sh ──→ Capture commit hashes
SessionEnd ────────→ git-track-rebuild.py → ~/.claude/git-tracking-index.json (rebuild)
```

The JSONL log records repos, branches, operations, and commit hashes. The index provides bidirectional lookup: `getSessionsForRepo()` / `getReposForSession()`. Query with `/session-report` for a Markdown dashboard.

---

## Plans

Implementation plans persisted to `~/.claude/plans/`. Named by project, date, and topic. Referenced from CLAUDE.md and active-projects.md.

```
plans/
├── 2026-02-07-daimonic-radio-stt-openclaw-mac-mini.md
├── 2026-02-03-feat-soul-engine-training-data-pipeline-plan.md
├── 2026-02-12-kothar-mac-mini-soul.md
├── 2026-02-09-pre-islamic-arabian-goddess-research.md
└── zesty-kindling-giraffe.md          # auto-named, will be renamed by plan-rename.py
```

Plans survive session crashes. New sessions read the relevant plan to resume work. The `plan-rename.py` hook auto-renames random slugs (e.g. `zesty-kindling-giraffe.md`) to dated names (e.g. `2026-02-17-claudicle-test-suite.md`) by extracting the H1 header.

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

**Key commands** (51 total, see `commands/README.md` for full list):

| Command | Purpose |
|---------|---------|
| `/claude-tracker` | List recent sessions with summaries |
| `/claude-tracker-search` | Search sessions by topic, ID, date |
| `/claude-tracker-resume` | Find and resume crashed sessions |
| `/claude-tracker-here` | Sessions for current directory |
| `/session-report` | Markdown dashboard: git activity, commits, repos |
| `/designer` | Designer mode |
| `/interview` | Interview about a plan |
| `/resonance` | Launch Daimon Chamber for cross-model resonance |
| `/ensoul` | Activate soul system for current session |
| `/slack-sync` | Sync Slack messages |

Invoked as `/command-name` in Claude Code. See the main README for additional workflow commands provided by plugins.

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

Currently 72 skills in the distribution repo. Toggle with `skill-toggle.py`. Disabled skills tracked in `~/.claude/disabled-skills.md`.

---

## Agents

Custom subagents in `~/.claude/agents/`. Read-only research agents invoked via the Task tool:

| Agent | Model | Purpose |
|-------|-------|---------|
| `librarian` | sonnet | GitHub repo exploration via `gh` CLI. Caches to `/tmp/claude-librarian/`. |

---

## Plugins

Managed via `/plugin` commands. State stored in `~/.claude/plugins/`. Currently enabled:

- **feature-dev** — code-architect, code-explorer, code-reviewer
- **compound-engineering** — 12+ review agents, workflow commands
- **document-skills** — PDF, DOCX, PPTX, XLSX, algorithmic art
- **pr-review-toolkit** — PR review, silent failure hunting, type design
- **llm-application-dev** — RAG, embeddings, prompt engineering
- **commit-commands** — commit, push, PR workflows
- **agent-sdk-dev** — Agent SDK app verification
- **model-trainer** — HuggingFace model fine-tuning
- **legal** — NDA triage, contract review, compliance

---

## Memory Hierarchy

Claude Code's configuration follows a 6-tier memory system, from broadest to most specific scope. More specific tiers take precedence.

| Tier | Location | Scope | Shared With |
|------|----------|-------|-------------|
| **Managed policy** | `/Library/Application Support/ClaudeCode/CLAUDE.md` | Organization-wide | All org users |
| **Project memory** | `./CLAUDE.md` | Project-wide | Team (via git) |
| **Project rules** | `.claude/rules/*.md` | Path-scoped | Team (via git) |
| **User memory** | `~/.claude/CLAUDE.md` | All projects | Personal only |
| **Project local** | `./CLAUDE.local.md` | This project | Personal only |
| **Auto memory** | `~/.claude/projects/<project>/memory/` | Per-project | Personal only |

All 6 tiers are individually documented by [Anthropic](https://code.claude.com/docs/en/memory). The numbered hierarchy framing is synthesized from their table.

**Key distinctions:**
- **Advisory vs deterministic**: All CLAUDE.md tiers are advisory—the agent reads them as guidance but may deviate under context pressure. For deterministic enforcement, use hooks (`.claude/hooks/`).
- **`.claude/rules/*.md`**: Path-scoped instructions with YAML frontmatter `paths:` globs. Load conditionally when matching files are in context. Alternative to monolithic CLAUDE.md for large codebases.
- **`CLAUDE.local.md`**: Gitignored personal overrides. Placed alongside `CLAUDE.md`, discovered automatically.

**Complementarity with Claudicle**: The 6-tier system provides the project instruction foundation — what to build, how to build it, what conventions to follow. [Claudicle](https://github.com/tdimino/claudicle) operates orthogonally as an identity superstructure — personality, memory, behavioral continuity. The soul injects via `soul-activate.py` hook into `additionalContext` after 6-tier loading. Soul state lives in `~/.claudicle/daemon/memory/memory.db` (SQLite), separate from auto-memory (tier 6). They compose without conflict: the 6 tiers tell Claude what to do, the soul tells Claude who it is.

See `skills/core-development/claude-md-manager/references/memory-hierarchy.md` for the full reference.

---

## Design Principles

1. **Progressive disclosure** — CLAUDE.md links to agent_docs/. Base context stays small. Details loaded on demand.
2. **One file per concern** — Each agent_doc, each plan, each handoff covers exactly one thing.
3. **Handoffs over history** — Sessions write structured YAMLs, not raw logs. The next soul inherits distilled knowledge.
4. **Git-tracked config** — `~/.claude/` is a git repo. Changes are committed, diffable, recoverable.
5. **Crash resilience** — Triple-hook handoffs (PreCompact + SessionEnd + Stop) minimize context loss.
6. **User model shapes behavior** — `userModels/` defines communication style, not just preferences. Claude adapts tone, initiative, and pushback.
7. **Retrieve-only RAG** — RLAMA queries use `rlama_retrieve.py` by default. Claude synthesizes from raw chunks; local models are fallback only.
