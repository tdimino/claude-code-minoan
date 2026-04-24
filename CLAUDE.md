# Claude-Code-Minoan

Curated `~/.claude/` configuration for Claude Code: 82 skills, 44 hooks, 47 commands, CLI tools, and a VS Code extension.

## Architecture
@ARCHITECTURE.md

## Structure

```
skills/{category}/{name}/  →  installs flat to ~/.claude/skills/{name}/
hooks/                     →  ~/.claude/hooks/ (wire in settings.json)
commands/                  →  ~/.claude/commands/
bin/                       →  ~/.local/bin/
lib/                       →  ~/.claude/lib/
```

## Contributing

- Skills must be self-contained--no cross-skill imports
- Hooks must wrap `json.load` in try/except--malformed input must not crash
- No API keys in the repo--use placeholders
- Flat skill names are authoritative--never reference category paths in code

See `CONTRIBUTING.md` for full guidelines.

## Quick Reference

- Setup: `./setup.sh` or see `README.md` Quick Start
- Sync from private: `./scripts/sync-to-repo.sh [--dry-run]`
- Sync config: `.sync-config.json` (category map, exclusions)
- Skill counts: `find skills -name SKILL.md -not -path '*/_archive/*' | wc -l`

## Guides

- `ARCHITECTURE.md` -- Repo layout, skill anatomy, hook wiring, invariants
- `hooks/README.md` -- All 46 hooks explained, including the SubagentStart/Stop loggers (`subagent-spawn-log.py` + `subagent-stop-log.py`) that catch silent subagent failures (tool errors, 32K output truncation, empty responses). Read when investigating subagent costs or unexplained agent behavior.
- `docs/ecosystem.md` -- Companion projects (Claudicle, Dabarat, ClipLog, claude-peers)
- `docs/guides/usermodel-guide.md` -- The userModel persona system
- `docs/guides/progressive-disclosure.md` -- The agent_docs pattern
- `docs/guides/session-continuity.md` -- Triple-handoff system
- `docs/global-setup/README.md` -- Full `~/.claude/` structure reference
- `CLAUDE.template.md` -- Teammate-ready global CLAUDE.md (no personal details)
