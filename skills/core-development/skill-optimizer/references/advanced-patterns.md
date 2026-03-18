# Advanced Skill Patterns

Source: Thariq (Anthropic), "Lessons from Building Claude Code: How We Use Skills" (March 2026).

These patterns go beyond the basic SKILL.md + scripts/references/assets structure. Use them when a skill needs persistent state, user-specific configuration, safety guardrails, or usage tracking.

## 1. Per-User Configuration (config.json)

Some skills need context from the user before they can operate -- a Slack channel, a database connection string, or an environment name.

**Pattern**: Store setup information in a `config.json` file at the skill root. On first invocation, if the config is absent, run a setup interview.

```json
{
  "slack_channel": "#engineering-standup",
  "timezone": "America/New_York",
  "default_env": "staging"
}
```

**In SKILL.md**:
```markdown
## Setup

Before first use, check for `config.json` in this skill's directory. If absent, ask the user:

1. Which Slack channel should standups be posted to?
2. What timezone should timestamps use?
3. Which environment is the default target?

Save answers to `config.json` and confirm the configuration.
```

For structured onboarding, instruct Claude to ask questions sequentially in the conversation, presenting numbered options for the user to choose from. This creates a clean, guided setup experience.

## 2. Session-Scoped Hooks

Skills can include hooks that are activated only when the skill is called and last for the duration of the session. Use this for opinionated guardrails you don't want running all the time.

**Frontmatter syntax**:
```yaml
hooks:
  PreToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: "echo 'checking command safety...'"
```

**Examples from Thariq**:

- `/careful` -- Blocks `rm -rf`, `DROP TABLE`, `force-push`, `kubectl delete` via PreToolUse matcher on Bash. Only activate when touching prod.
- `/freeze` -- Blocks any Edit/Write that's not in a specific directory. Useful when debugging: "I want to add logs but I keep accidentally 'fixing' unrelated code."

**When to use**:
- Safety guardrails for destructive operations (Infrastructure Operations category)
- Scope restriction during focused work (Code Quality & Review category)
- Audit logging for compliance-sensitive workflows

Session hooks are powerful but opinionated. Reserve them for skills where the guardrail is essential to the skill's purpose, not a nice-to-have.

## 3. Skill Memory / Persistence

Skills can store data within themselves: append-only text logs, JSON files, or even SQLite databases.

**Key insight**: When a skill maintains a running log of its actions, the next invocation can read its own history and tell what's changed since the last run. This makes Business Process and Team Automation skills dramatically more consistent.

**Example**: A standup-post skill saves every standup it's written to `standups.log`. The next time it runs, Claude reads the history and can say "since yesterday, you merged 3 PRs and closed 2 tickets."

**Storage location**: For plugin skills, use `${CLAUDE_PLUGIN_DATA}` if available (a stable per-plugin data directory). For personal and project skills, use an explicit path like `~/.claude/data/<skill-name>/` or store data in a `data/` subdirectory within the skill and add it to `.gitignore`.

```markdown
## Persistence

This skill maintains a log at `~/.claude/data/my-skill/history.jsonl`. After each run, append a JSON line with:
- timestamp
- action taken
- summary of output

Before each run, read the last 10 entries to maintain consistency with previous outputs.
```

**Guidelines**:
- Keep storage lightweight -- memory is for operational continuity, not analytics
- Use append-only formats (JSONL, log files) to avoid corruption from concurrent writes
- Consider SQLite only when you need querying capability (e.g., searching past runs by date)

## 4. Usage Analytics

Track skill usage via PreToolUse hooks to find skills that are undertriggering (the description needs work) or overtriggering (the description is too broad).

**Pattern**: A PreToolUse hook fires on skill invocation and appends to a log file.

```yaml
hooks:
  PreToolUse:
    - matcher: Skill
      hooks:
        - type: command
          command: "echo \"$(date -Iseconds) $SKILL_NAME\" >> ~/.claude/logs/skill-usage.log"
```

**When to review**:
- If a skill is used less than expected, investigate the description -- it may need more trigger phrases
- If a skill fires on unrelated prompts, the description may be too broad
- Periodic portfolio reviews (monthly) help identify dead skills and consolidation opportunities

This is what Anthropic uses internally to understand which skills are working and which need improvement.

## 5. Script-as-Composition

From Thariq: "One of the most powerful tools you can give Claude is code. Giving Claude scripts and libraries lets Claude spend its turns on composition -- deciding what to do next rather than reconstructing boilerplate."

**The architectural benefit**: A 200-line script costs ~20 tokens of context (only the output enters context, not the code itself). If Claude were to write that same logic inline, it would consume 2000+ tokens of output AND multiple tool calls. Scripts are a 100x context efficiency gain.

**Identifying script candidates**:
- Any code that appears in 2+ eval transcripts -- Claude is reconstructing it each time
- Any multi-step operation where the steps are always the same
- Data access patterns that require specific credentials or schemas
- Format conversions or validations that have precise requirements

**Example from Thariq**: A data science skill bundles helper functions for fetching data from the event source. Claude generates scripts on the fly that compose these helpers for prompts like "What happened on Tuesday?"

```python
# scripts/events.py -- bundled with the skill
def get_events(start_date, end_date, event_type=None):
    """Fetch events from the canonical source."""
    # ...implementation...

def get_user_journey(user_id, window_days=30):
    """Reconstruct a user's event timeline."""
    # ...implementation...
```

Claude then writes a short composition script:
```python
from events import get_events, get_user_journey
# Claude writes only the novel logic; the heavy lifting is in the bundled scripts
```

**Rule of thumb**: If Claude would write the same 10+ lines of code in more than one eval scenario, extract it into a bundled script.
