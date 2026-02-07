# Agent Teams Quick Reference

Distilled from the official Claude Code Agent Teams documentation and the orchestrating-swarms skill.

---

## Prerequisites

Enable Agent Teams (experimental):

```json
// ~/.claude/settings.json  OR  .claude/settings.json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

Or set in shell: `export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`

---

## Agent Teams vs Subagents

| | Subagents | Agent Teams |
|---|---|---|
| **Context** | Own window; results return to caller | Own window; fully independent |
| **Communication** | One-way: report back | Bi-directional: teammates message each other |
| **Coordination** | Parent manages all | Shared task list, self-claiming |
| **Lifetime** | Ephemeral | Persistent until shutdown |
| **Token cost** | Lower (results summarized) | Higher (each teammate = separate instance) |
| **Best for** | Focused tasks, quick results | Complex work needing discussion and collaboration |

**Rule of thumb:** Use subagents when only the result matters. Use teams when workers need to share findings, challenge each other, or coordinate on their own.

---

## Core Tools

### TeamCreate — Create a team

```javascript
TeamCreate({
  team_name: "my-project",
  description: "Working on feature X"
})
```

Creates `~/.claude/teams/{name}/config.json` and `~/.claude/tasks/{name}/`.

### Task (with team_name + name) — Spawn a teammate

```javascript
Task({
  team_name: "my-project",
  name: "researcher",
  subagent_type: "general-purpose",  // or Explore, Plan, any plugin agent
  model: "sonnet",                    // optional: haiku, sonnet, opus
  mode: "plan",                       // optional: require plan approval
  prompt: "Your task instructions here",
  run_in_background: true
})
```

### SendMessage — Communicate

```javascript
// Direct message to one teammate
SendMessage({
  type: "message",
  recipient: "researcher",
  content: "Focus on the auth module first",
  summary: "Prioritize auth module"
})

// Broadcast to ALL (use sparingly — expensive)
SendMessage({
  type: "broadcast",
  content: "Critical: stop work, blocking bug found",
  summary: "Blocking bug found"
})

// Request shutdown
SendMessage({
  type: "shutdown_request",
  recipient: "researcher",
  content: "All tasks complete"
})

// Respond to shutdown (as a teammate)
SendMessage({
  type: "shutdown_response",
  request_id: "abc-123",   // from the shutdown_request message
  approve: true
})

// Approve a teammate's plan
SendMessage({
  type: "plan_approval_response",
  request_id: "plan-456",
  recipient: "architect",
  approve: true
})
```

### TaskCreate — Create work items

```javascript
TaskCreate({
  subject: "Implement auth routes",
  description: "Create src/routes/auth.ts with login/signup endpoints",
  activeForm: "Implementing auth routes"  // shown in spinner
})
```

### TaskList — See all tasks

```javascript
TaskList()
// Returns: id, subject, status, owner, blockedBy
```

### TaskUpdate — Update tasks

```javascript
// Claim a task
TaskUpdate({ taskId: "1", owner: "researcher" })

// Start work
TaskUpdate({ taskId: "1", status: "in_progress" })

// Mark complete
TaskUpdate({ taskId: "1", status: "completed" })

// Set dependencies
TaskUpdate({ taskId: "3", addBlockedBy: ["1", "2"] })
```

### TeamDelete — Clean up

```javascript
TeamDelete()
// Removes team and task directories
// MUST shutdown all teammates first
```

---

## Key Patterns

### Delegate Mode

Press `Shift+Tab` to cycle the lead into delegate mode. Restricts the lead to coordination-only tools — prevents the lead from implementing tasks itself.

### Plan Approval

Spawn a teammate with `mode: "plan"`. They plan in read-only mode, then send a plan approval request. The lead reviews and approves/rejects.

### Self-Claiming Swarm

Create many independent tasks (no dependencies). Spawn workers with instructions to check TaskList, claim unassigned tasks, complete them, and repeat. File locking prevents race conditions.

### Pipeline (Sequential)

Create tasks with dependencies using `addBlockedBy`. When a blocking task completes, blocked tasks auto-unblock.

---

## Display Modes

| Mode | How | Best For |
|------|-----|----------|
| **in-process** (default) | All in main terminal. `Shift+Up/Down` to select teammates. | Any terminal |
| **split panes** | Each teammate in own pane. Requires tmux or iTerm2. | Monitoring all activity |
| **auto** (default setting) | Uses split panes if already in tmux, in-process otherwise. | Most users |

Configure in settings.json: `"teammateMode": "in-process"` or `"tmux"`

---

## File Locations

| What | Where |
|------|-------|
| Team config | `~/.claude/teams/{name}/config.json` |
| Task files | `~/.claude/tasks/{name}/{id}.json` |
| Inboxes | `~/.claude/teams/{name}/inboxes/{agent}.json` |

---

## Limitations

- No session resumption for in-process teammates
- One team per session
- No nested teams (teammates cannot spawn teams)
- Lead is fixed (cannot transfer leadership)
- Permissions set at spawn for all teammates
- Split panes require tmux or iTerm2

---

## Token Cost Awareness

Each teammate is a separate Claude instance with its own context window. Token usage scales linearly with team size. For routine tasks, a single session is more cost-effective. Reserve teams for work that genuinely benefits from parallel exploration and inter-agent coordination.
