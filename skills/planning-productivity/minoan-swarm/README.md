# Minoan Swarm

*Orchestrate Agent Teams named for the Priestesses of Knossos—in the tongue before the Hellenizers got to it.*

Multi-agent orchestration for Claude Code using Minoan-Semitic naming conventions. 7 knesset templates, 30+ named teammates across 7 role archetypes, auto-discovery of project context, and structured task coordination.

**Requires:** `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

---

## Terminology

| Term | Semitic | Root | Meaning |
|------|---------|------|---------|
| **Knesset** | כנסת | K-N-S "to gather" | A single agent team—an assembly of bees |
| **Knossot** | כנוסות | K-N-S plural | A group of knessets—a swarm, evoking Knossos itself |

D-B-R (דבר) is both "bee" and "word/speech." The agents are deborot—bees of the holy word, manifest in LLMs. Each knesset assembles bees who speak; a knossot gathers the assemblies.

---

## Quick Start

```bash
# 1. Discover project context
bash ~/.claude/skills/minoan-swarm/scripts/discover_context.sh .

# 2. Choose a template and launch
#    (see Templates below)
```

Or invoke directly in Claude Code:

```
Use the minoan-swarm skill to create an Athirat team for implementing
[feature A], [feature B], and [feature C] in parallel.
```

---

## Structure

```
minoan-swarm/
  SKILL.md                           # Full skill definition (loaded by Claude Code)
  README.md                          # This file
  references/
    naming-codex.md                  # 30+ names with pronunciations, etymologies, sources
    team-templates.md                # 7 ready-to-use templates with tool calls
    agent-teams-quickref.md          # API quick reference
  scripts/
    discover_context.sh              # Auto-discover planning artifacts
    sync-repos.sh                    # Sync skill across repos
    test_skill.sh                    # Verify skill installation
```

---

## Templates

| Template | Knesset Name | Use When |
|----------|--------------|----------|
| **Parallel Features** | Athirat | Multiple independent features or modules |
| **Pipeline** | Kaptaru | Work with natural sequencing (research → design → build → test) |
| **Research Knossot** | Elat | Bug investigation, competing hypotheses |
| **Phase Completion** | Qedeshot | Finishing a phase—deploy, test, polish |
| **Code Review Tribunal** | Elat | Multi-perspective PR review |
| **Truth & Balance** | Ma'at | Quality assurance, verification |
| **Fate's Reckoning** | Manat | Final audit, release decisions |

Full templates with ready-to-use tool calls: [`references/team-templates.md`](references/team-templates.md)

---

## The Naming Codex

Names are drawn from the Minoan-Semitic divine feminine—Ugaritic, Akkadian, Hebrew, Linear B, Egyptian, and pre-Islamic Arabian. Chosen by role archetype, not randomly.

| Archetype | Names | Model |
|-----------|-------|-------|
| **Leaders** | athirat-lead, qedesha-lead, tiamat-lead, maat-lead, allat-lead | Opus |
| **Builders** | kaptaru, mami, nintu, tehom, tip'eret, yam, al-uzza | Sonnet |
| **Researchers** | deborah, melissa, eileithyia, membliaros | Sonnet/Haiku |
| **Reviewers** | hokhmah, qadeshet, karme, themis, manat, allat | Sonnet |
| **Testers** | sassuratu, phikola, hubur | Sonnet/Haiku |
| **Frontend** | popureja, shalamu, yashar | Sonnet |
| **DevOps** | selene, hestia, dikte | Sonnet |

Full codex with pronunciations, etymologies, and scholarly sources: [`references/naming-codex.md`](references/naming-codex.md)

---

## Key Concepts

**File ownership** — Two teammates editing the same file causes overwrites. Every team launch includes an explicit ownership matrix.

**Model tiering** — Leads use Opus (orchestration), workers use Sonnet (implementation), lightweight research uses Haiku.

**Tool preferences** — Firecrawl over WebFetch for scraping, Exa over WebSearch for neural search. Include in every teammate prompt.

**Graceful shutdown** — `shutdown_request` each teammate, then `TeamDelete` after all confirm.

**Compaction survival** — Leads re-read TaskList and `~/.claude/teams/{team-name}/config.json` to recover state after context compaction.

---

## Context Discovery

The `discover_context.sh` script scans a project root for:

- Identity files (CLAUDE.md, README.md, SPEC.md)
- Planning artifacts (ROADMAP.md, plans/, .beads/, docs/)
- Codebase structure (language detection, source file counts)
- Test infrastructure (frameworks, test directories)
- GitHub issues (via `gh` CLI)
- Git state (branch, commit count, dirty files)

```bash
bash ~/.claude/skills/minoan-swarm/scripts/discover_context.sh ~/Desktop/Programming/my-project
```

---

## Example: Launching a Parallel Features Team

```
TeamCreate({ team_name: "athirat", description: "Parallel feature implementation" })

TaskCreate({ subject: "Implement auth module", ... })
TaskCreate({ subject: "Implement bookmarks", ... })
TaskCreate({ subject: "Implement profiles", ... })

# Spawn all teammates in parallel:
Task({ team_name: "athirat", name: "mami",    model: "sonnet", prompt: "You are Mami..." })
Task({ team_name: "athirat", name: "tip'eret", model: "sonnet", prompt: "You are Tip'eret..." })
Task({ team_name: "athirat", name: "kaptaru",  model: "sonnet", prompt: "You are Kaptaru..." })
```

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)—curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/minoan-swarm ~/.claude/skills/
```

---

*"μνάσεσθαί τινά φαμι καὶ ὕστερον ἀμμέων."* — Sappho

*𐤁𐤓𐤀𐤔𐤉𐤕 𐤁𐤏𐤋𐤕 𐤁𐤓𐤕* — "In the beginning, the Lady created."
