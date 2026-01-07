<p align="center">
  <img src="public/images/tanit.svg" alt="Symbol of Tanit" width="80"/>
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/Version-1.0.0-blue.svg" alt="Version"></a>
  <a href="#available-skills"><img src="https://img.shields.io/badge/Skills-21-green.svg" alt="Skills"></a>
  <a href="#all-slash-commands"><img src="https://img.shields.io/badge/Commands-30+-purple.svg" alt="Commands"></a>
</p>

# Minoan Claude Code Configuration

Curated Claude Code configuration including skills, MCP servers, and slash commands for professional development workflows.

<p align="center">
  <img src="public/images/be_minoan.jpg" alt="Minoan fresco - Cross-model resonance" width="600"/>
</p>

## Repository Contents

```
claude-code-minoan/
├── .mcp.json                    # MCP server configurations
├── skills/                      # Custom Claude Code skills
│   ├── core-development/        # Core development tools
│   │   ├── beads-task-tracker/      # Dependency-aware task tracking
│   │   ├── claude-agent-sdk/        # Build AI agents with Claude Agent SDK
│   │   ├── claude-md-manager/       # CLAUDE.md creation and optimization
│   │   ├── osgrep-reference/        # Semantic code search
│   │   └── skill-creator/           # Guide for creating skills
│   ├── integration-automation/  # Infrastructure & integrations
│   │   ├── dev-browser/             # Browser automation with persistent state
│   │   ├── figma-mcp/               # Figma design integration
│   │   ├── mcp-server-manager/      # MCP server configuration
│   │   ├── netlify-integration/     # Netlify deployment management
│   │   ├── supabase-skill/          # Supabase project management
│   │   ├── telnyx-api/              # Telnyx telephony integration
│   │   └── twilio-api/              # Twilio SMS/Voice integration
│   ├── design-media/            # Design & media tools
│   │   ├── frontend-design/         # Distinctive UI creation
│   │   ├── gemini-claude-resonance/ # Cross-model AI dialogue with visual memory
│   │   ├── nano-banana-pro/         # Gemini 3 Pro AI image generation
│   │   └── photo-to-slack-emoji/    # Photo to Slack emoji converter
│   ├── research/                # Research tools
│   │   ├── academic-research/       # Academic paper search with Exa + ArXiv
│   │   ├── exa-search/              # Full Exa AI API access
│   │   └── Firecrawl/               # Web scraping (prefer over WebFetch)
│   └── planning-productivity/   # Planning tools
│       ├── crypt-librarian/         # Film curator persona
│       └── travel-requirements-expert/  # Travel itinerary planning
├── commands/                    # Slash commands
│   ├── workflows/               # Multi-agent workflow commands
│   │   ├── review.md             # 12+ agent code review
│   │   ├── work.md               # Plan execution
│   │   ├── plan.md               # Feature planning
│   │   └── plan_review.md        # Parallel plan review
│   ├── audit-plans.md           # Plan completeness auditing
│   ├── code-review.md           # PR code review
│   ├── interview.md             # Plan clarification questions
│   └── ... (30+ slash commands)
├── hooks/                       # Claude Code hooks
│   └── multi-response-prompt.py  # /5x trigger for 5 alternative responses
└── README.md                    # This file
```

## Quick Start

> **New here?** Jump to [Recommended Workflow Commands](#recommended-workflow-commands) to see the most powerful commands: `/requirements-start`, `/workflows:review`, `feature-dev` plugin, `/workflows:plan`, and `/code-review`.

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/claude-code-minoan.git
cd claude-code-minoan
```

### 2. Set Up Skills

Skills are custom Claude Code capabilities that extend functionality with specialized workflows.

**Option A: Copy to Personal Skills Directory** (recommended)
```bash
cp -r skills/* ~/.claude/skills/
```

**Option B: Symlink Individual Skills**
```bash
ln -s "$(pwd)/skills/core-development/beads-task-tracker" ~/.claude/skills/beads-task-tracker
ln -s "$(pwd)/skills/integration-automation/dev-browser" ~/.claude/skills/dev-browser
```

### 3. Set Up Slash Commands

```bash
cp -r commands/* ~/.claude/commands/
```

### 4. Set Up MCP Servers

Add servers using the Claude Code CLI:

```bash
# Playwright (browser automation)
claude mcp add playwright -c npx -a "@playwright/mcp@latest" -s user

# Perplexity (AI search)
claude mcp add perplexity -c node -a "/path/to/perplexity-mcp/build/index.js" -s user -e PERPLEXITY_API_KEY=your_key

# shadcn/ui (HTTP)
claude mcp add shadcn --http "https://www.shadcn.io/api/mcp" -s user

# Figma (HTTP)
claude mcp add figma --http "https://mcp.figma.com/mcp" -s user
```

## Recommended Workflow Commands

These are the most powerful commands for professional development workflows:

### `/requirements-start` Series - Extensive Project Planning

**Use when**: Starting any new feature or project that needs careful planning

The requirements workflow creates comprehensive specifications through structured discovery:

1. **`/requirements-start <description>`** - Initiates requirements gathering
   - Asks 5 high-level yes/no questions to understand scope
   - Analyzes codebase context and existing patterns
   - Generates 5 detailed technical questions
   - Creates comprehensive specification document

2. **`/requirements-continue`** - Resume interrupted requirements session
3. **`/requirements-review`** - Review and refine existing requirements
4. **`/requirements-implement`** - Begin implementation from specification

**Why it's powerful**:
- Prevents scope creep through structured discovery
- Documents decisions for future reference
- Catches architectural conflicts early
- Creates implementation-ready specifications
- Saves hours of refactoring later

**Example workflow**:
```bash
/requirements-start Implement user authentication with OAuth
# Answer discovery questions
# Answer technical questions
# Review specification
/requirements-implement
```

### `/workflows:review` - Comprehensive Code Review

**Use when**: Before committing significant changes or reviewing pull requests

> **Note**: This command is token-intensive due to parallel subagents. Use for thorough reviews; for quick checks, use `/code-review`.

Analyzes code for:
- Security vulnerabilities (credential exposure, input validation)
- Performance bottlenecks (inefficient patterns, memory leaks)
- Code quality (complexity, maintainability, best practices)
- Architecture issues (layer separation, dependency direction)

Creates prioritized issues with:
- Exact file locations and line numbers
- Problem explanation and impact assessment
- Specific remediation steps
- Severity and effort estimates

**Why it's powerful**:
- Uses 12+ specialized parallel subagents (security-sentinel, performance-oracle, architecture-strategist, etc.)
- Catches issues before they reach production
- Provides actionable feedback, not just complaints
- Creates GitHub issues automatically if requested

### `feature-dev` Plugin - Claude Code Team's Arsenal

**Use when**: Building features, exploring codebases, or reviewing code with specialized agents

The `feature-dev` plugin is the **official Claude Code team's toolkit** - the same agents they use internally. Install it with:

```bash
/plugin marketplace add anthropics/claude-code
/plugin install feature-dev
```

**Available agents** (invoke via Task tool with `subagent_type`):

| Agent | Purpose |
|-------|---------|
| `feature-dev:code-architect` | Designs feature architectures by analyzing existing patterns, providing implementation blueprints with specific files, component designs, data flows, and build sequences |
| `feature-dev:code-explorer` | Deeply analyzes codebase features by tracing execution paths, mapping architecture layers, understanding patterns/abstractions, and documenting dependencies |
| `feature-dev:code-reviewer` | Reviews code for bugs, logic errors, security vulnerabilities, and quality issues using confidence-based filtering to surface only high-priority findings |

**Why it's powerful**:
- Built by the Claude Code team for their own workflows
- Specialized agents outperform general-purpose prompts
- `code-architect` creates comprehensive blueprints before you write code
- `code-explorer` maps unfamiliar codebases quickly
- `code-reviewer` catches issues with confidence-based prioritization

**Example workflow**:
```bash
# Explore an unfamiliar codebase
# (Claude uses feature-dev:code-explorer agent)
"How does the authentication system work in this codebase?"

# Design a new feature
# (Claude uses feature-dev:code-architect agent)
"Design the architecture for adding OAuth support"

# Review your changes
# (Claude uses feature-dev:code-reviewer agent)
"Review my recent changes for any issues"
```

### `/audit-plans` - Plan Completeness Auditing

**Use when**: Before implementing a plan to ensure nothing is missed

Systematically audits implementation plans:
- Reads phases chronologically
- Evaluates against completeness criteria (acceptance criteria, implementation steps, dependencies, edge cases)
- Invokes `/interview` to fill gaps with structured questions
- Updates plan and related documentation

---

## Available Skills

### Core Development (`skills/core-development/`)

- **beads-task-tracker** - Dependency-aware task tracking with Beads. SQLite + JSONL sync, hash-based IDs, daemon process for cross-session continuity
- **claude-agent-sdk** - Build AI agents using the Claude Agent SDK (Python & TypeScript). Covers query functions, ClaudeSDKClient, custom tools with @tool decorator, MCP servers, hooks, permissions, and subagents. Includes 7 production-ready templates and 9 reference docs
- **claude-md-manager** - Create, audit, and maintain CLAUDE.md documentation files. Uses the WHAT/WHY/HOW framework, progressive disclosure patterns with agent_docs/, conciseness optimization, and anti-pattern detection
- **osgrep-reference** - Semantic code search using natural language queries. Find code by concept rather than keyword matching ("where do we handle authentication?" vs "grep 'auth'")
- **skill-creator** - Guide for creating effective Claude Code skills with templates and best practices

### Integration & Automation (`skills/integration-automation/`)

- **dev-browser** - Browser automation with persistent page state. Write focused scripts to navigate websites, fill forms, take screenshots. Uses Playwright with ARIA snapshots for element discovery
- **figma-mcp** - Convert Figma designs to production code with accurate styling
- **mcp-server-manager** - Configure and manage MCP servers in Claude Code
- **netlify-integration** - Deploy and manage Netlify projects with Next.js serverless functions, environment variables, and continuous deployment
- **supabase-skill** - Configure and manage Supabase projects using MCP. Database design, migrations, RLS policies
- **telnyx-api** - SMS/MMS messaging, voice calls, phone numbers, webhooks, and telephony integration
- **twilio-api** - Twilio SMS/Voice API integration with provider-agnostic patterns, webhook security, E.164 validation, and error handling

### Design & Media (`skills/design-media/`)

- **frontend-design** - Create distinctive, production-grade frontend interfaces with high design quality. Generates creative, polished code that avoids generic AI aesthetics. Bold typography, unexpected layouts, atmospheric backgrounds
- **gemini-claude-resonance** - Cross-model dialogue between Claude and Gemini with shared visual memory. Multiple daimones (Flash, Pro, Dreamer, Director, Opus, Resonator) with dynamic verb selection and WorkingMemory-style transcripts. Includes Daimon Chamber UI and Resonance Field protocol for persistent visual narratives
- **nano-banana-pro** - Generate and edit high-quality images using Google's Nano Banana Pro (Gemini 3 Pro Image) AI model. Supports up to 4K resolution, multiple aspect ratios, and advanced prompting
- **photo-to-slack-emoji** - Transform photos into Slack-optimized emojis using Nano Banana Pro AI (10 styles, auto-optimization for 64KB limit)

### Research (`skills/research/`)

- **academic-research** - Comprehensive academic paper search, literature reviews, and research synthesis. Combines Exa MCP with arxiv-mcp-server for paper discovery, download, and deep analysis
- **exa-search** - Complete Exa AI search API access with 5 specialized scripts: neural web search, URL content extraction, similar page discovery, quick AI research with citations, and async pro research
- **Firecrawl** - Web scraping with Agent API for autonomous data extraction. **ALWAYS prefer Firecrawl over WebFetch** for cleaner output, better JS handling, and no content truncation

### Planning & Productivity (`skills/planning-productivity/`)

- **crypt-librarian** - Film curator persona for sourcing pre-2016 cinema with literary/gothic sensibility, occult atmosphere, sensual mysticism, and historical grandeur. Uses Perplexity for film discourse, Exa for web searches
- **travel-requirements-expert** - Systematically gather comprehensive travel itinerary requirements through structured discovery questions, MCP-powered research, and expert detail gathering

## Available MCP Servers

### AI & Search
- **perplexity** - AI-powered search and chat
- **arxiv** - Academic paper search, download, and analysis
- **context7** - Up-to-date library documentation

### Development Tools
- **playwright** - Browser automation and testing
- **chrome-devtools** - Browser debugging integration
- **codex** - Enhanced code operations
- **filesystem** - Enhanced filesystem access

### Design & UI
- **figma** - Figma design integration
- **shadcn** - shadcn/ui component library

### Infrastructure
- **supabase** - PostgreSQL database operations
- **netlify** - Deployment and site management
- **mcp-google-sheets** - Google Sheets integration

### Telephony & Communication
- **telnyx** - Telephony, messaging, voice calls
- **twilio** - SMS and voice operations

## All Slash Commands

### Development Workflow
- `/commit` - Create standardized git commits
- `/refactor` - Refactor code with best practices
- `/implement` - Implement features from specifications
- `/test` - Generate comprehensive tests

### Code Quality
- `/workflows:review` - Comprehensive code review with 12+ parallel subagents (token-intensive)
- `/security-scan` - Security vulnerability analysis
- `/fix-imports` - Fix import statements
- `/cleanproject` - Clean up project structure

### Documentation
- `/docs` - Generate documentation
- `/explain-like-senior` - Senior-level code explanations
- `/understand` - Deep dive into codebase understanding

### Planning & Requirements
- `/requirements-start` - Extensive project planning workflow
- `/requirements-continue` - Resume interrupted requirements session
- `/requirements-review` - Review and refine existing requirements
- `/requirements-implement` - Begin implementation from specification
- `/audit-plans` - Audit plans for completeness, interview to fill gaps
- `/interview` - Generate clarifying questions about a plan
- `/create-todos` - Generate TODO lists from requirements
- `/find-todos` - Find TODO comments in codebase
- `/fix-todos` - Address existing TODOs

### Code Review
- `/code-review` - Comprehensive PR code review with structured JSON output. *Created by the inventor of Claude Code*

### Workflow Commands
- `/workflows:review` - Exhaustive code review using 12+ parallel agents
- `/workflows:work` - Execute work plans with quality checks
- `/workflows:plan` - Transform descriptions into project plans
- `/workflows:plan_review` - Parallel plan review by multiple agents

### Official Plugins
- **`feature-dev`** - Claude Code team's arsenal: `code-architect`, `code-explorer`, `code-reviewer` agents

## Hooks

Hooks are scripts that run in response to Claude Code events. Copy to `~/.claude/hooks/` and configure in `~/.claude/settings.json`.

### Available Hooks

| Hook | Trigger | Description |
|------|---------|-------------|
| `multi-response-prompt.py` | `/5x` in message | Generates 5 alternative responses sampled from distribution tails. Useful for exploring creative options |

### Setup

1. Copy hooks to your Claude directory:
   ```bash
   cp -r hooks/* ~/.claude/hooks/
   chmod +x ~/.claude/hooks/*.py ~/.claude/hooks/*.sh
   ```

2. Configure in `~/.claude/settings.json`:
   ```json
   {
     "hooks": {
       "UserPromptSubmit": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "~/.claude/hooks/multi-response-prompt.py"
             }
           ]
         }
       ]
     }
   }
   ```

3. Use by adding `/5x` to any message:
   ```
   How should I structure this component? /5x
   ```

## Recommended Plugins

### `feature-dev` - Claude Code Team's Arsenal

The official plugin from the Claude Code team. Provides specialized agents for feature development:

```bash
/plugin marketplace add anthropics/claude-code
/plugin install feature-dev
```

- **`code-architect`** - Design feature architectures with implementation blueprints
- **`code-explorer`** - Trace execution paths and map codebase structure
- **`code-reviewer`** - Confidence-based code review for high-priority issues

### `claude-mem` - Persistent Memory

Persistent memory across sessions with semantic search. Essential for long-running projects.

```bash
claude plugin install claude-mem@thedotmack
```

## Security Best Practices

1. **Never commit API keys** - Use placeholders in `.mcp.json`
2. **Use environment variables** - Store secrets in `.env` files
3. **Git ignore sensitive files**:
   ```
   .env
   .env.local
   *_local.json
   ```
4. **Rotate keys regularly** - Especially for shared team accounts
5. **Use scoped tokens** - Minimum permissions required

## Contributing

### Skill Development Guidelines

1. Follow the skill template structure (SKILL.md at minimum)
2. Include comprehensive documentation with usage examples
3. Add reference files for complex workflows
4. Test across different projects
5. Submit PR with description of functionality

### Slash Command Guidelines

1. Keep commands focused and single-purpose
2. Use frontmatter for metadata:
   ```markdown
   ---
   description: Brief command description
   argument-hint: [required-arg] [optional-arg]
   ---
   Your prompt template here
   ```
3. Document expected inputs/outputs
4. Include examples in comments

### MCP Server Guidelines

1. Test server thoroughly before adding
2. Document all required environment variables
3. Include troubleshooting steps
4. Note any system dependencies
5. Specify which scope (user/project/local) is recommended

## Team Setup Checklist

- [ ] Clone repository
- [ ] Copy skills to `~/.claude/skills/`
- [ ] Copy commands to `~/.claude/commands/`
- [ ] Install `feature-dev` plugin (`/plugin marketplace add anthropics/claude-code` then `/plugin install feature-dev`)
- [ ] Set up essential MCP servers (supabase, arxiv, perplexity, context7)
- [ ] Configure API keys for perplexity, supabase, netlify
- [ ] Test a slash command (`/docs`)
- [ ] Test a skill (claude-agent-sdk)
- [ ] Verify MCP servers with `claude mcp list`
- [ ] Install claude-mem plugin for persistent memory

## Troubleshooting

### Skills Not Loading

```bash
ls ~/.claude/skills/
ls ~/.claude/skills/skill-name/
# Should contain SKILL.md at minimum
```

### MCP Server Connection Failed

```bash
claude mcp list
claude mcp get server-name
claude mcp remove server-name -s user
claude mcp add server-name ...
```

### Slash Command Not Found

```bash
ls ~/.claude/commands/command-name.md
cat ~/.claude/commands/command-name.md
```

## Documentation Links

- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code)
- [MCP Server Guide](https://docs.claude.com/en/docs/claude-code/mcp)
- [Slash Commands Guide](https://docs.claude.com/en/docs/claude-code/slash-commands)
- [Skills Development](https://docs.claude.com/en/docs/claude-code/skills)

---

**Last Updated**: 2026-01-04

**Skills**: 21 skills across 5 categories
**Commands**: 30+ slash commands
**MCP Servers**: 14 configured servers

---

*"ἀπιστίῃ διαφυγγάνει μὴ γιγνώσκεσθαι."* — "Divine things escape recognition through disbelief." — Heraclitus
