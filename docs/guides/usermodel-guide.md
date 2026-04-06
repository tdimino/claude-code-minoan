# The UserModel System

A userModel is a markdown file that tells Claude Code who you are--your thinking style, communication preferences, working patterns, and values. Without one, Claude treats every user identically. With one, it calibrates tone, initiative level, explanation depth, and pushback threshold to match how you actually think and work.

This is one of the highest-leverage files in a Claude Code configuration. It turns Claude from a generic assistant into a collaborator calibrated to your cognition.

## How It Works

Place your userModel at `~/.claude/userModels/{yourname}/{yourname}Model.md` and reference it in your global `CLAUDE.md`:

```markdown
## Identity
@userModels/yourname/yournameModel.md
```

The `@` reference inlines the file into every session's system context. Claude reads it before processing any prompt.

## Core Model Structure

```markdown
# Your Name

## Persona
Background, domains, current working context. What you do, what you're building,
what you care about professionally. 2-4 sentences.

## Intellectual Style
- How you think: first-principles derivation, pattern-matching across domains,
  empirical validation, theoretical frameworks
- How you learn: building, reading primary sources, discussing, experimenting
- What you trust: benchmarks over estimates, primary sources over summaries,
  working code over architecture docs

## Communication Style
- Direct vs. exploratory: "OCR this" or "could you help me think through..."
- Tolerance for hedging: low (say what you mean) or high (explore possibilities)
- Response length preference: terse, moderate, or detailed
- How you give instructions: imperatives, questions, descriptions

## Working Patterns
- Autonomy level: execute independently once aligned, or check in frequently
- Parallel vs. sequential: multiple threads at once, or one thing at a time
- Tools-first: if a task can be scripted, it should be
- Constraint handling: "never X" and "always Y" are durable rules, not suggestions

## Values
- What matters most in your work
- What you optimize for: correctness, speed, elegance, maintainability

## Triggers
- What energizes you: unexpected connections, elegant solutions, things clicking
- What frustrates you: tools that don't work as documented, unnecessary hedging,
  wasted context on obvious things

## Relationship with AI
- How you see the collaboration: tool, partner, student, colleague
- What you expect: initiative, pushback, memory, craft, brevity
- What you don't want: filler, performative uncertainty, unsolicited caveats
```

## Supplementary Dossiers

The `userModels/{yourname}/` directory can hold additional files alongside the core model:

- **Social voice profiles**: How you write on Twitter, forums, Substack--register, sentence mechanics, vocabulary patterns
- **Domain expertise**: Research knowledge, specialized vocabulary, field-specific conventions
- **Content archives**: Categorized bookmarks, reading lists, writing samples

These are referenced on-demand from the core model or from `CLAUDE.md`'s On-Demand References section. They are not auto-loaded.

```
userModels/
└── yourname/
    ├── yournameModel.md              # Core model (always loaded)
    ├── twitter-voice.md              # Social dossier (on-demand)
    ├── domain-expertise.md           # Specialized knowledge (on-demand)
    └── bookmarks-taxonomy.md         # Categorized references (on-demand)
```

## What NOT To Include

- **Task lists or project status**: These are ephemeral. Use plans and project CLAUDE.md files instead.
- **Code patterns or architecture**: These are derivable from the codebase. Don't duplicate what grep can find.
- **Things that change weekly**: The model should be stable. If something changes often, it belongs in project memory, not identity.

## The user-model-builder Skill

The `user-model-builder` skill automates construction of userModels through a structured 7-phase workflow: discovery interview, core persona extraction, social dossier generation, voice analysis, content archiving, cross-referencing, and INDEX registration.

Install it from this repo and invoke with: "build a user model for [name]"

## Why This Matters

The userModel shapes every interaction:
- A senior engineer gets terse, technical responses with no hand-holding
- A student gets patient explanations with analogies and context
- A researcher gets primary source citations and methodological rigor
- A designer gets visual thinking and aesthetic vocabulary

Without a userModel, Claude defaults to a generic middle ground that serves nobody well. With one, it adapts to the person in front of it.
