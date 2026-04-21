# Planning with Files

Manus-style file-based planning for complex tasks. Creates persistent `task_plan.md`, `findings.md`, and `progress.md` in your project directory as working memory on disk---survives context compaction, session crashes, and `/clear`. Includes session recovery, hooks for automatic plan checking, and a completion verifier.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

AI coding agents lose context during long tasks---compaction drops details, `/clear` wipes state, sessions crash. File-based planning treats the filesystem as persistent memory: write the plan, findings, and progress to disk, re-read before decisions. Based on the [Manus-style pattern](https://github.com/othmanadi/planning-with-files).

---

## Structure

```
planning-with-files/
  SKILL.md                          # Full workflow with rules and anti-patterns
  README.md                         # This file
  scripts/
    init-session.sh                 # Initialize all planning files
    init-session.ps1                # Windows equivalent
    check-complete.sh               # Verify all phases complete
    check-complete.ps1              # Windows equivalent
    session-catchup.py              # Recover context from previous session
  templates/
    task_plan.md                    # Phase tracking template
    findings.md                     # Research storage template
    progress.md                     # Session logging template
```

---

## Core Pattern

```
Context Window = RAM (volatile, limited)
Filesystem = Disk (persistent, unlimited)

→ Anything important gets written to disk.
```

---

## Files

| File | Purpose | When to Update |
|------|---------|----------------|
| `task_plan.md` | Phases, progress, decisions | After each phase |
| `findings.md` | Research, discoveries | After any discovery |
| `progress.md` | Session log, test results | Throughout session |

All files go in **your project directory**, not the skill directory.

---

## Usage

```bash
# Initialize planning files from templates
bash init-session.sh

# Recover context from a previous session
python3 session-catchup.py "$(pwd)"

# Verify all phases are complete
bash check-complete.sh
```

---

## Critical Rules

1. **Create plan first** --- Never start complex work without `task_plan.md`
2. **2-Action Rule** --- After every 2 operations, save findings to disk
3. **Read before decide** --- Re-read the plan before major decisions
4. **Update after act** --- Mark phases complete, log errors
5. **Never repeat failures** --- Track attempts, mutate approach
6. **3-Strike Protocol** --- After 3 failures on the same step, escalate to user

---

## When to Use

**Use for**: Multi-step tasks (3+ steps), research projects, anything requiring >5 tool calls.

**Skip for**: Simple questions, single-file edits, quick lookups.

---

## Setup

### Prerequisites

- Bash (macOS/Linux) or PowerShell (Windows)
- Python 3.9+ (for `session-catchup.py`)
- No additional dependencies

---

## Related Skills

- **`agents-md-manager`**: Generates `.agents.md` files---complements planning with agent-level configuration.

---

## Requirements

- Bash or PowerShell
- Python 3.9+ (session recovery only)

---

## Attribution

Based on [planning-with-files](https://github.com/othmanadi/planning-with-files) by Othman Adi (MIT license).

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/planning-productivity/planning-with-files ~/.claude/skills/
```
