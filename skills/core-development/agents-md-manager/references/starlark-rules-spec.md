# Starlark Rules Specification

## Overview

Codex CLI uses `.rules` files written in Starlark (a Python-like language) to define command approval policies. Rules determine whether a command is allowed, requires user confirmation, or is forbidden before execution.

## File Locations

| Scope | Path | Notes |
|-------|------|-------|
| Global | `~/.codex/rules/default.rules` | Applies to all projects |
| Project | `.codex/rules/*.rules` | Project-scoped rules |

Multiple `.rules` files are loaded and merged. All files in the rules directory are evaluated.

## The `prefix_rule()` Function

Each rule is defined by calling `prefix_rule()` with the following fields:

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `pattern` | Yes | -- | List of strings defining the command prefix to match |
| `decision` | No | `"allow"` | `"allow"`, `"prompt"`, or `"forbidden"` |
| `justification` | No | `""` | Human-readable reason displayed when the rule fires |
| `match` | No | -- | List of commands that SHOULD match (inline unit test) |
| `not_match` | No | -- | List of commands that should NOT match (inline unit test) |

### Decision Precedence

When multiple rules match a command, the **most restrictive** decision wins:

```
forbidden > prompt > allow
```

A single `forbidden` rule overrides any number of `allow` rules for the same prefix.

### Pattern Matching

Each element in `pattern` matches one token in the command. A position can be:
- A single string: matches that exact token
- A list of strings: matches any token in the list (union)

```python
# Matches: git status, git log, git diff, git branch
prefix_rule(
    pattern=["git", ["status", "log", "diff", "branch"]],
    decision="allow",
    justification="Read-only git commands are safe",
    match=["git status", "git log --oneline"],
    not_match=["git push", "git reset --hard"],
)
```

## Shell Splitting Behavior

Codex splits safe linear command chains (`&&`, `||`, `;`, `|`) into individual commands and evaluates each independently against rules.

Codex does **NOT** split commands that use:
- Redirects (`>`, `>>`, `<`, `2>&1`)
- Command substitution (`$(...)`, backticks)
- Environment variable references (`$VAR`)
- Wildcards/globs (`*`, `?`, `[...]`)
- Control flow (`if`, `for`, `while`)

Unsplit commands are evaluated as a single unit against the pattern.

## Testing Rules

Validate rules without executing commands:

```bash
codex execpolicy check --pretty --rules <file> -- <command>
```

The `match` and `not_match` fields in `prefix_rule()` serve as inline unit tests, verified at load time.

## Common Patterns

### Read-Only Git

```python
prefix_rule(
    pattern=["git", ["status", "log", "diff", "branch", "show", "remote", "tag", "stash"]],
    decision="allow",
    justification="Read-only git operations",
)
```

### Block Destructive Git

```python
prefix_rule(
    pattern=["git", "push", "--force"],
    decision="forbidden",
    justification="Force push can destroy remote history",
    match=["git push --force origin main"],
    not_match=["git push origin main"],
)

prefix_rule(
    pattern=["git", ["reset", "clean"], "--hard"],
    decision="forbidden",
    justification="Hard reset/clean destroys uncommitted work",
)
```

### Package Managers

```python
prefix_rule(
    pattern=[["npm", "pnpm", "yarn"], "install"],
    decision="prompt",
    justification="Review dependency changes before installing",
)

prefix_rule(
    pattern=[["npm", "pnpm", "yarn"], "run"],
    decision="allow",
    justification="Running defined scripts is safe",
)

prefix_rule(
    pattern=["pip", "install"],
    decision="prompt",
    justification="Review Python package installations",
)
```

### Build and Test

```python
prefix_rule(
    pattern=["cargo", ["test", "build", "check", "clippy"]],
    decision="allow",
    justification="Rust build and test commands are safe",
)

prefix_rule(
    pattern=[["pytest", "python"], ["-m", "test"]],
    decision="allow",
)
```

### Block Dangerous Commands

```python
prefix_rule(
    pattern=["rm", "-rf"],
    decision="forbidden",
    justification="Recursive force delete is too dangerous for automation",
    match=["rm -rf /tmp/build"],
    not_match=["rm file.txt"],
)

prefix_rule(
    pattern=["sudo"],
    decision="forbidden",
    justification="Agents should not run privileged commands",
)
```
