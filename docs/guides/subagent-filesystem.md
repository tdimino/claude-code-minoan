# Subagent Filesystem Boundary

Subagents spawned via the Agent tool **cannot write files outside the project root directory**, regardless of permission mode. This is a hardcoded sandbox boundary in Claude Code, not a configurable permission. Writes fail silently--the subagent reports success but produces nothing.

This guide documents the restriction, its root causes, and the relay pattern workaround.

## The Problem

When you spawn a subagent from a session rooted at `~/my-project/`, that agent can read and write freely within `~/my-project/`. But if it tries to Write or Edit a file at `~/.claude/plans/`, `~/daimones/`, `/tmp/`, or any path outside the project root, the operation is silently blocked.

This affects:
- Background agents (most severely--they auto-deny permission prompts)
- Foreground agents with `mode: "bypassPermissions"`
- Agents in worktrees (`isolation: "worktree"`)

## Root Causes

Three independent mechanisms combine to create this restriction:

### 1. `additionalDirectories` not inherited

Paths added via `--add-dir` at session launch are visible only to the main context. Subagent sandboxes are built from the primary `cwd` alone. Even if the parent session has `--add-dir ~/.claude/plans`, spawned agents cannot see or write to that path.

**GitHub**: [#31940](https://github.com/anthropics/claude-code/issues/31940) (open)--no `cwd` or `additionalDirectories` parameter exists in the Agent tool definition or frontmatter.

### 2. `bypassPermissions` doesn't propagate

The permission mode (`bypassPermissions`, `acceptEdits`, etc.) controls whether the user is prompted before tool execution. But the filesystem sandbox is a separate, harder boundary that `bypassPermissions` does not override. The sandbox allowlist is computed from the primary CWD before the permission-mode check fires.

**GitHub**: [#29610](https://github.com/anthropics/claude-code/issues/29610), [#37442](https://github.com/anthropics/claude-code/issues/37442) (both open)

### 3. Background subagents auto-deny prompts

When a background subagent (`run_in_background: true`) encounters a permission prompt it cannot surface to the user, it automatically denies the request. The agent continues execution as if the write succeeded, but no file is created.

**GitHub**: [#32402](https://github.com/anthropics/claude-code/issues/32402) (open)

### Bonus: Protected directories

Since v2.1.78, `.claude/`, `.git/`, `.vscode/`, and `.idea/` directories have hardcoded write protection that fires before any permission evaluation. No configuration overrides this for subagents.

## The Relay Pattern

The reliable workaround: subagents write to a staging directory inside the project root, and the main context relays files to the target path.

```
Subagent writes to:     .subdaimon-output/{agent}-{timestamp}.md
Main context reads it:   Read .subdaimon-output/{agent}-{timestamp}.md
Main context writes to:  ~/target/path/file.md
```

### Setup

1. **Subagent prompt**: Instruct the agent to write output to `.subdaimon-output/` in the current working directory:
   ```
   Write your analysis to .subdaimon-output/research-{timestamp}.md
   ```

2. **Main context**: After the subagent completes, read the file and relay it:
   ```
   Read .subdaimon-output/research-1234567890.md
   Write ~/daimones/kothar/research.md   # main context has broader access
   ```

3. **Cleanup**: `.subdaimon-output/` is ephemeral. Add it to `.gitignore` and delete anytime:
   ```bash
   rm -rf .subdaimon-output/
   ```

### Why this works

The main context operates with the full permission scope of the session--including `settings.local.json` rules, `--add-dir` paths, and interactive permission prompts. Only subagents are restricted to the project root sandbox.

## Permission Configuration

To let the **main context** write to paths outside the project root without prompting, add rules to `~/.claude/settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "Write(//Users/you/daimones/**)",
      "Edit(//Users/you/daimones/**)"
    ]
  }
}
```

Note the double-slash prefix (`//`) for absolute paths--this is required by Claude Code's permission matching syntax.

These rules affect the main context only. Subagents ignore `settings.local.json` permission rules for paths outside their sandbox.

## Alternative Workarounds

| Approach | Reliability | Notes |
|----------|-------------|-------|
| **Relay pattern** | High | Recommended. Works today, no hacks. |
| **Return content as text** | High | Subagent returns content in its response; main context writes it. Limited by 32K output cap. |
| **Symlink into project** | Low | `ln -s ~/target project/target`. Symlink traversal was patched as a security fix--may stop working. |
| **Launch from parent dir** | Medium | If `cwd` is `~`, then `~/daimones/` is inside the root. Changes session behavior for everything else. |

## Issues to Watch

| Issue | Status | Impact |
|-------|--------|--------|
| [#31940](https://github.com/anthropics/claude-code/issues/31940) | Open | `cwd`/`additionalDirectories` in Agent tool--would eliminate the need for the relay pattern |
| [#29610](https://github.com/anthropics/claude-code/issues/29610) | Open | `bypassPermissions` for paths outside project root |
| [#37442](https://github.com/anthropics/claude-code/issues/37442) | Open | Permission mode inheritance for subagents |
| [#40076](https://github.com/anthropics/claude-code/issues/40076) | Open | `**` glob rules not matching outside working directory |
| [#39523](https://github.com/anthropics/claude-code/issues/39523) | Open | META issue tracking the full 9-month bypass failure trail |

If #31940 ships, subagents could be scoped to arbitrary directories and the relay pattern becomes unnecessary.
