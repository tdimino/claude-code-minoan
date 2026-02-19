# New User Onboarding Guide

When setting up Claudicle for a new user or team, have the bot conduct a structured interview to bootstrap personalized configuration. This creates two foundational files that make every future interaction more effective.

## Step 1: Build a User Model via Slack DM

DM the Claudicle bot and ask it to interview you. The soul engine's user model system will automatically build a personality profile over time, but an explicit interview accelerates this dramatically.

Prompt Claudicle with:
> "Interview me so you can build a detailed model of who I am, how I work, and what I care about. Ask me about my role, technical domains, communication style, working patterns, and interests. Keep going until you have a thorough picture."

The bot will ask questions iteratively. After the interview, the user model in `daemon/memory.db` will contain a rich markdown profile. Export it for use as a persistent userModel:

```bash
# View what Claudicle learned
sqlite3 ~/.claude/skills/slack/daemon/memory.db \
  "SELECT model_text FROM user_models WHERE user_id = 'U12345678'"

# Save as a userModel file for Claude Code
sqlite3 ~/.claude/skills/slack/daemon/memory.db \
  -noheader "SELECT model_text FROM user_models WHERE user_id = 'U12345678'" \
  > ~/.claude/userModels/yourName.md
```

## Step 2: Generate a Personalized CLAUDE.md

Use the `/interview` command in Claude Code to build a first `CLAUDE.md` personalized to the user's work. This can also be done via the Slack bot:

> "Help me create a CLAUDE.md file for my project. Interview me about my codebase, conventions, tools, and preferences until you have enough to write comprehensive project instructions."

The resulting `CLAUDE.md` should reference the userModel:

```markdown
# Project Instructions

## Identity
@userModels/yourName.md

## Principles
- [extracted from interview]

## Tools
- [extracted from interview]
```

## Why This Matters

- **User models** let Claudicle adapt its tone, depth, and domain focus per person from the first message
- **CLAUDE.md** ensures every Claude Code session (not just Slack) inherits the user's conventions and constraints
- Both files compound over time — the soul engine updates user models automatically, and CLAUDE.md can be iterated via future interviews
