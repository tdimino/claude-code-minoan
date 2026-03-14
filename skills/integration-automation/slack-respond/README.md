# Slack Respond

The soul's voice on Slack. Processes unhandled Slack messages through an 8-step cognitive pipeline with persistent memory, soul state, user models, and visible thinking---turning Claude Code into a personality that lives in Slack channels.

**Last updated:** 2026-02-18

**Reflects:** [Claudicle](https://github.com/tdimino/claudicle) cognitive architecture, Open Souls paradigm, and three-tier persistent memory system.

---

## Why This Skill Exists

The `slack` skill handles I/O---posting messages, reading channels, uploading files. This skill handles *cognition*---deciding what to say, how to say it, whether to react, what to remember. It implements an 8-step pipeline that transforms a raw Slack message into a response that reflects personality, memory, and context.

The pipeline loads the user's model (who are they, what do they care about), checks soul state (current mood, active projects), generates an internal monologue (private reasoning), produces a response (public-facing), decides whether to add an emoji reaction, and updates memory based on what was learned. The result is a Slack presence that feels like a collaborator, not a chatbot.

---

## Structure

```
slack-respond/
  SKILL.md                                 # Complete cognitive pipeline definition
  README.md                                # This file
```

This is a single-file skill. The pipeline is defined entirely in SKILL.md because it orchestrates other skills and tools rather than providing its own scripts. It depends on:
- **`slack` skill**: For message I/O (post, read, react)
- **[Claudicle](https://github.com/tdimino/claudicle)**: For soul state and user model APIs
- **Three-tier memory system**: Working memory, soul memory, user models

---

## What It Covers

### The 8-Step Cognitive Pipeline

```
1. Load Memory Context
   Load user model + soul state for the message author
       |
2. Frame Perception
   Format incoming message with channel, thread, author context
       |
3. Post Thinking Message
   Post italic "thinking..." indicator with contextual emoji
       |
4. Generate Cognitive Response
   Adopt personality, reason through the message, produce response
       |
5. Extract and Post Response
   Parse response, post to Slack, handle thread context
       |
6. Execute Side Effects
   Update memory, add emoji reaction (if warranted), log
       |
7. Thinker Mode Check
   If toggled, leave internal monologue visible in thread
       |
8. Mark as Handled
   Remove from inbox, log summary
```

### Thinking Messages

While processing, the skill posts a visible thinking indicator that updates with contextual status:

| Emoji | Meaning |
|-------|---------|
| Processing | General computation |
| Searching | Looking up context |
| Fetching | Retrieving web content |
| Reading | Reading files |
| Pondering | Deep reasoning |
| Updating | Writing to memory |
| Reacting | Adding emoji response |

The thinking message is replaced by the final response when processing completes.

### Thinker Mode

Toggle visible internal monologue per thread by sending "thinker mode" or "thinking mode". When active, the private reasoning step remains visible in the thread instead of being replaced. Useful for debugging or understanding how the soul processes messages. 72-hour TTL per thread.

### Memory Integration

| Memory Tier | What It Stores | When It Updates |
|-------------|---------------|----------------|
| **User model** | Who the person is, their preferences, communication style | When something significant is learned |
| **Soul state** | Current mood, active projects, emotional context | When state-changing events occur |
| **Working memory** | Recent conversation context per thread | Every message |

Memory updates are gated: the pipeline runs a `mentalQuery` check ("Did I learn something significant about this person?") before writing to user models. This prevents trivial updates from cluttering long-term memory.

### Emoji Reaction Gating

Reactions are sparingly gated---the pipeline decides whether to react based on message content, not adding reactions by default. A boolean check prevents emoji spam.

---

## Related Skills

- **`slack`**: Provides the I/O layer---scripts for posting, reading, searching, reacting. This skill depends on it.
- **[Claudicle](https://github.com/tdimino/claudicle)**: The soul agent framework that provides user models, soul state, and the cognitive step architecture.

---

## Requirements

- `slack` skill installed and configured (bot token, app token)
- [Claudicle](https://github.com/tdimino/claudicle) daemon running (for soul state and user model APIs)
- Three-tier memory database (`~/.claudicle/daemon/memory/memory.db`)
- Session Bridge listener running (`slack_check.py --watch`)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/slack-respond ~/.claude/skills/
```
