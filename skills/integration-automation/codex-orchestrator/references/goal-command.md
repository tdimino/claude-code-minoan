# Codex /goal Command Reference

## Overview

The `/goal` slash command sets a persistent, high-level objective that Codex works toward autonomously across its session. Unlike one-shot prompts, a goal persists through multiple interactions and checkpoints, enabling multi-hour autonomous work sessions.

## Prerequisites

Enable the goals feature in `~/.codex/config.toml`:

```toml
[features]
goals = true
```

Or pass `--enable goals` when launching the Codex TUI.

## Syntax

| Command | Action |
|---------|--------|
| `/goal <objective>` | Set a new goal (must `/goal clear` first if one is active) |
| `/goal` | View the current goal and its status |
| `/goal pause` | Pause the active goal |
| `/goal resume` | Resume a paused goal |
| `/goal clear` | Remove the current goal |

## Constraints

- **4,000 character limit** on goal content
- **One goal per thread** — must `/goal clear` before setting a different goal
- **TUI-only** — `/goal` does not work in `codex exec` (non-interactive) mode
- **SQLite persistence** — goal state survives TUI restarts within the same thread

## Goal Statuses

| Status | Meaning |
|--------|---------|
| `active` | Codex is working toward the goal |
| `paused` | Goal is paused, can be resumed |
| `budget_limited` | Token/cost budget reached, goal suspended |
| `complete` | Goal achieved (Codex determined stopping condition met) |

## Architecture

- Goals are stored in a local SQLite database managed by Codex
- Each thread has at most one active goal
- Codex periodically checks progress against the goal and adjusts its approach
- The goal persists across TUI restarts within the same session/thread

## Best Practices

### Clear Stopping Conditions

Provide a machine-verifiable way to know the goal is complete:

```
/goal Implement user authentication. Done when: `npm test -- --grep auth` passes
and `curl -s localhost:3000/api/auth/login -d '{"email":"test@test.com","password":"pass"}' | jq .token` returns a JWT.
```

### Validation Loops

Include commands Codex can run to check incremental progress:

```
/goal Add pagination to the API. Validate progress with: `curl -s 'localhost:3000/api/items?page=1&limit=10' | jq '.items | length'` should return 10. `curl -s 'localhost:3000/api/items?page=2&limit=10' | jq .page'` should return 2.
```

### Checkpoint Structure

Break large goals into ordered milestones:

```
/goal Migrate the database from SQLite to PostgreSQL.
Checkpoints:
1. Schema migration files created — verify: ls migrations/*.sql | wc -l
2. Connection pool configured — verify: grep -q "pg" package.json
3. All queries updated — verify: grep -rn "sqlite" src/ | wc -l returns 0
4. Tests pass — verify: npm test
```

### Constraints Section

Explicitly state what NOT to change:

```
/goal Refactor the auth module to use JWT. Do NOT change the public API routes.
Do NOT modify the user model schema. Do NOT remove existing session-based auth
until JWT is verified working.
```

### File References for Long Goals

When the goal needs more context than fits in 4,000 characters, point Codex at a file:

```
/goal Follow the objective in /path/to/goals/goal-01.md: Implement the caching layer
described in the goal specification. Read the file for full context, constraints,
and checkpoints.
```

## Programmatic Launch

To launch a goal from a script, pass it as the initial prompt to the interactive TUI:

```bash
# Inline goal (under 3,500 chars)
codex --enable goals --model gpt-5.5 --sandbox workspace-write "/goal <content>"

# File-referenced goal (over 3,500 chars)
codex --enable goals --model gpt-5.5 --sandbox workspace-write \
  "/goal Follow the objective in $(realpath goals/goal-01.md): <summary>"
```

The TUI processes `/goal` as a slash command in its first turn, then continues interactively.
