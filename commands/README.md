# Slash Commands (`commands/`)

Markdown templates invoked as `/command-name` in Claude Code. Each file defines a reusable prompt pattern.

## Installation

```bash
cp -r commands/* ~/.claude/commands/
```

## Command Format

Commands are markdown files with optional frontmatter:

```markdown
---
description: Brief command description
argument-hint: <required-arg> [optional-arg]
---

Your prompt template here. Use $ARGUMENTS for user input.
```

## Available Commands

### Session Management
| Command | Description |
|---------|-------------|
| `/claude-tracker` | List recent sessions with status |
| `/claude-tracker-search` | Search sessions by topic/ID |
| `/claude-tracker-resume` | Find and resume crashed sessions |
| `/claude-tracker-here` | Sessions for current directory |
| `/session-start` | Initialize session with context |
| `/session-end` | Summarize and close session |

### Development Workflow
| Command | Description |
|---------|-------------|
| `/commit` | Create standardized git commits |
| `/implement` | Implement from specifications |
| `/refactor` | Refactor with best practices |
| `/test` | Generate comprehensive tests |
| `/scaffold` | Scaffold project structure |

### Code Quality
| Command | Description |
|---------|-------------|
| `/code-review` | PR code review with structured output |
| `/security-scan` | Security vulnerability analysis |
| `/fix-imports` | Fix import statements |
| `/cleanproject` | Clean up project structure |
| `/remove-comments` | Remove unnecessary comments |

### Planning & Requirements
| Command | Description |
|---------|-------------|
| `/requirements-start` | Begin requirements gathering |
| `/requirements-continue` | Resume requirements session |
| `/requirements-review` | Review existing requirements |
| `/requirements-implement` | Implement from specification |
| `/audit-plans` | Audit plan completeness |
| `/interview` | Clarifying questions about a plan |
| `/create-todos` | Generate TODOs from requirements |
| `/find-todos` | Find TODO comments in codebase |
| `/fix-todos` | Address existing TODOs |

### Documentation & Explanation
| Command | Description |
|---------|-------------|
| `/docs` | Generate documentation |
| `/explain-like-senior` | Senior-level code explanations |
| `/understand` | Deep dive into codebase |

### Workflow Commands (`workflows/`)
| Command | Description |
|---------|-------------|
| `/workflows:review` | 12+ parallel agent code review |
| `/workflows:work` | Execute work plans |
| `/workflows:plan` | Transform descriptions into plans |
| `/workflows:plan_review` | Parallel plan review |

### Creative
| Command | Description |
|---------|-------------|
| `/designer` | Design mode with creative constraints |
| `/resonance` | Cross-model dialogue session |
| `/interview` | Structured interview/Q&A |

## Credits & Inspiration

- **`/code-review`** — inspired by the structured review patterns from the Claude Code team
- **`/requirements-start` series** — based on specification-driven development practices
- **`/workflows:review`** — uses the [compound-engineering](https://github.com/every-ai-labs/compound-engineering) plugin's parallel agent architecture by [Every AI Labs](https://github.com/every-ai-labs)
