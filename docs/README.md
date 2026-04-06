# Documentation

Reference documentation for the Minoan Claude Code configuration.

| Document | Description |
|----------|-------------|
| [global-setup/](global-setup/README.md) | Full `~/.claude/` directory structure reference — CLAUDE.md patterns, user persona models, `agent_docs/` progressive disclosure, settings.json configuration, session handoff system, and design principles |
| [global-setup/agent_docs/](global-setup/agent_docs/README.md) | Starter templates for `~/.claude/agent_docs/` — active-projects, skills, tools, MCP servers |
| [guides/usermodel-guide.md](guides/usermodel-guide.md) | The userModel persona system — core model template, supplementary dossiers, anti-patterns |
| [guides/progressive-disclosure.md](guides/progressive-disclosure.md) | The `agent_docs/` pattern — decision matrix, 6-tier memory hierarchy, design principles |
| [guides/session-continuity.md](guides/session-continuity.md) | Triple-handoff system — PreCompact, SessionEnd, Stop hooks, handoff YAML, resume workflow |
| [guides/subagent-filesystem.md](guides/subagent-filesystem.md) | Subagent filesystem boundary — why agents can't write outside project root, relay pattern workaround, permission configuration |
| [ecosystem.md](ecosystem.md) | Companion projects — Claudicle, Dabarat, ClipLog, claude-peers |
| [tmux-claude-workflow.md](tmux-claude-workflow.md) | Tmux-based multi-session workflow for Claude Code — split panes, session naming, and parallel development patterns |
