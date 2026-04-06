# Contributing to Minoan Claude Code Configuration

This guide covers how to add new skills, slash commands, hooks, and MCP servers to the repo.

## Table of Contents

- [Contributing Skills](#contributing-skills)
- [Contributing Hooks](#contributing-hooks)
- [Contributing Slash Commands](#contributing-slash-commands)
- [Contributing MCP Servers](#contributing-mcp-servers)
- [Pull Request Process](#pull-request-process)
- [Code Review Guidelines](#code-review-guidelines)

## Contributing Skills

### Skill Structure

A skill must follow this directory structure:

```
skills/
└── your-skill-name/
    ├── SKILL.md          # Required: Main skill definition
    ├── scripts/          # Optional: Executable scripts
    ├── references/       # Optional: Additional docs loaded on demand
    └── README.md         # Optional: Documentation
```

### Creating a New Skill

1. **Copy an existing skill** as a starting point (e.g. `skills/research/firecrawl/`):

```bash
cp -r skills/research/firecrawl skills/your-category/your-skill-name
```

2. **Edit `SKILL.md`** with this structure:

```markdown
---
description: Brief one-line description of what the skill does
---

# Skill Name

Detailed description of the skill's purpose and when to use it.

## Usage

Explain how and when this skill should be invoked.

## Examples

Provide concrete examples of the skill in action.

## Configuration

If the skill requires any configuration, document it here.

## Dependencies

List any MCP servers, tools, or other skills this depends on.
```

3. **Test the skill**:

```bash
# Copy to your local skills directory
cp -r skills/your-skill-name ~/.claude/skills/

# Test in Claude Code
# The skill should appear automatically and can be invoked
```

4. **Create documentation**:

```bash
# Add README.md with detailed usage instructions
cat > skills/your-skill-name/README.md << EOF
# Your Skill Name

## Purpose
What problem does this skill solve?

## When to Use
Describe scenarios where this skill is most useful.

## Usage Examples
[Provide 2-3 concrete examples]

## Troubleshooting
Common issues and solutions.
EOF
```

5. **Submit PR** (see Pull Request Process below)

### Skill Best Practices

✅ **Do**:
- Keep skills focused on a single purpose
- Provide clear, concise documentation
- Include usage examples
- Test thoroughly across different projects
- Document any dependencies
- Use descriptive names (kebab-case)

❌ **Don't**:
- Create overly broad skills
- Include API keys or secrets
- Duplicate existing skill functionality
- Skip documentation

## Contributing Hooks

### What Are Hooks?

Hooks are scripts that execute in response to Claude Code lifecycle events (SessionStart, Stop, PreToolUse, PostToolUse, etc.). They live in `hooks/` and are configured via `settings.json`. See `hooks/INDEX.md` for the full inventory and architecture diagram.

### Hook Structure

```
hooks/
├── INDEX.md              # Master inventory (auto-maintained)
├── README.md             # Detailed documentation
├── your-hook.py          # Python hooks (preferred)
├── your-hook.sh          # Shell hooks (for simple cases)
└── tests/                # Hook tests
```

### Available Events (18 total, 10 currently used)

| Event | When it fires |
|-------|--------------|
| `SessionStart` | Session begins, resumes, or compacts |
| `UserPromptSubmit` | Before user prompt is sent to model |
| `PermissionRequest` | Tool needs permission (allow/deny/pass) |
| `SubagentStart` | Subagent spawns |
| `PreToolUse` | Before any tool executes |
| `PostToolUse` | After tool succeeds |
| `PostToolUseFailure` | After tool fails |
| `Stop` | Model finishes a response |
| `PreCompact` | Before context compaction |
| `SessionEnd` | Session terminates |

### Creating a New Hook

1. **Write the hook** (Python preferred for complex logic, shell for simple):

```python
#!/usr/bin/env python3
"""Description of what this hook does."""
import json, sys

def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)  # Always fail gracefully

    # Your logic here...

    # To output a decision (PermissionRequest hooks):
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PermissionRequest",
            "permissionDecision": "allow",  # or "deny" or omit to pass
        }
    }
    print(json.dumps(output))
    sys.exit(0)

if __name__ == "__main__":
    main()
```

2. **Register in `settings.json`**:

```json
{
  "hooks": {
    "Stop": [
      {
        "type": "command",
        "command": "python3 ~/.claude/hooks/your-hook.py",
        "async": true
      }
    ]
  }
}
```

3. **Update `hooks/INDEX.md`** with the new hook's event, description, and any matchers.

4. **Test the hook** by triggering its event in a Claude Code session.

### Hook Best Practices

- Always wrap `json.load(sys.stdin)` in try/except
- Use file-based cooldowns in `/tmp/claude-{uid}/` for API-calling hooks
- Guard shell commands against chaining (`; | & \``) before pattern matching
- Use `async: true` for hooks that call external APIs
- Write cooldown timestamps AFTER successful operations, not before
- Keep hooks idempotent—they may fire multiple times

### Key Hooks

| Hook | Event | Purpose |
|------|-------|---------|
| `smart-auto-approve.py` | PermissionRequest | Auto-approve safe Bash commands, deny dangerous ones |
| `error-context-hints.py` | PostToolUseFailure | Pattern-match common errors, inject recovery hints |
| `precompact-handoff.py` | PreCompact/SessionEnd | Generate handoff YAML via OpenRouter |
| `session-tags-infer.py` | Stop (async) | Infer session tags via OpenRouter |
| `soul-subagent-inject.py` | SubagentStart | Inject soul context into subdaimones |

## Contributing Slash Commands

### Command Structure

Slash commands are Markdown files in the `commands/` directory:

```
commands/
└── command-name.md
```

### Creating a New Command

1. **Create the command file**:

```bash
cat > commands/your-command.md << 'EOF'
---
description: Brief description of what this command does
argument-hint: [required-arg] [optional-arg]
allowed-tools: Read, Write, Edit, Bash
model: claude-sonnet-4
---

Your detailed prompt template here.

Use $1, $2, etc. for arguments if using argument-hint.

## Example
If user runs: /your-command myfile.ts
Then $1 = myfile.ts
EOF
```

2. **Test the command**:

```bash
# Copy to your local commands
cp commands/your-command.md ~/.claude/commands/

# Test in Claude Code
/your-command
```

3. **Document in README**:

Add your command to the "Popular Slash Commands" section in README.md.

### Command Best Practices

✅ **Do**:
- Use frontmatter for metadata
- Keep commands single-purpose
- Provide argument hints if applicable
- Use clear, descriptive names
- Include examples in comments

❌ **Don't**:
- Create overly complex commands
- Duplicate existing commands
- Use unclear abbreviations
- Skip the description field

### Command Naming Conventions

- Use kebab-case: `my-command.md`
- Be descriptive: `security-scan.md` not `scan.md`
- Avoid abbreviations unless common: `refactor.md` not `rfctr.md`

## Contributing MCP Servers

### Adding a New MCP Server

1. **Test the server locally**:

```bash
# Add server to your local config first
claude mcp add server-name -c command -a "args" -s user

# Verify it works
claude mcp list
claude mcp get server-name
```

2. **Document in .mcp.json**:

```json
{
  "mcpServers": {
    "your-server-name": {
      "description": "Clear description of what this server provides",
      "type": "stdio" or "http",
      "command": "command-to-run",
      "args": ["arg1", "arg2"],
      "env": {
        "API_KEY": "PLACEHOLDER_FOR_ACTUAL_KEY"
      },
      "setup": {
        "instructions": [
          "Step 1: Install dependencies",
          "Step 2: Get API key from...",
          "Step 3: Replace PLACEHOLDER_FOR_ACTUAL_KEY"
        ]
      }
    }
  }
}
```

3. **Update README.md**:

Add the server to the "Available MCP Servers" section with:
- Server name
- Brief description
- Category (AI & Search, Development Tools, etc.)

### MCP Server Best Practices

✅ **Do**:
- Test thoroughly before adding
- Document all environment variables
- Use placeholders for API keys
- Include troubleshooting steps
- Specify recommended scope (user/project/local)
- Document system dependencies

❌ **Don't**:
- Commit actual API keys
- Add untested servers
- Skip setup instructions
- Assume dependencies are installed

### Security Requirements

⚠️ **Critical**: Never commit actual API keys or secrets

Use placeholders:
- `YOUR_API_KEY_HERE`
- `REPLACE_WITH_YOUR_TOKEN`
- `YOUR_PROJECT_ID_HERE`

## Pull Request Process

### Before Submitting

- [ ] Test your contribution locally
- [ ] Update README.md if applicable
- [ ] Update CONTRIBUTING.md if adding new patterns
- [ ] Ensure no API keys or secrets are included
- [ ] Run spell check on documentation
- [ ] Verify all links work

### PR Template

```markdown
## Description
Brief description of what this PR adds/changes.

## Type of Change
- [ ] New skill
- [ ] New slash command
- [ ] New MCP server
- [ ] Documentation update
- [ ] Bug fix

## Checklist
- [ ] Tested locally
- [ ] Documentation updated
- [ ] No secrets committed
- [ ] Examples provided (if applicable)

## Usage Example
Show how to use the new feature:
```

### PR Title Format

- **Skills**: `feat(skills): add [skill-name]`
- **Commands**: `feat(commands): add /command-name`
- **MCP**: `feat(mcp): add [server-name] integration`
- **Docs**: `docs: update [section] documentation`
- **Fix**: `fix: resolve [issue description]`

## Code Review Guidelines

### What Reviewers Look For

1. **Functionality**
   - Does it work as described?
   - Are there edge cases?

2. **Documentation**
   - Is the purpose clear?
   - Are examples provided?
   - Are setup instructions complete?

3. **Security**
   - No API keys committed?
   - No sensitive data exposed?

4. **Quality**
   - Follows naming conventions?
   - Fits the existing structure?
   - Well-tested?

### Review Process

1. Reviewer tests the contribution locally
2. Checks documentation completeness
3. Verifies no secrets are committed
4. Approves or requests changes
5. Maintainer merges approved PRs

## Versioning

We use semantic versioning for this repository:

- **Major** (1.0.0): Breaking changes to structure
- **Minor** (0.1.0): New skills, commands, or servers
- **Patch** (0.0.1): Bug fixes, documentation updates

## Commit Message Format

Use conventional commits:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types**:
- `feat`: New feature (skill, command, server)
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:
```
feat(skills): add open-souls-paradigm skill
fix(mcp): correct perplexity server configuration
docs: update README with new MCP server setup
```

## Getting Help

- Review existing skills/commands for examples
- Check [Claude Code docs](https://docs.claude.com/en/docs/claude-code)
- Ask in team chat
- Create an issue for discussion

## License

All contributions are licensed under MIT (see [LICENSE](LICENSE)).
