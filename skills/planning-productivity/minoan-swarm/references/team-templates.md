# Team Templates

Ready-to-use team configurations for common orchestration patterns. Each template includes the full tool calls needed to launch.

---

## Template 1: Parallel Features

**Use when:** Multiple independent features or modules can be built simultaneously. Each teammate owns a separate file domain.

**Team name:** Athirat (establishing new systems)

```javascript
// 1. Create team
TeamCreate({ team_name: "athirat", description: "Parallel feature implementation" })

// 2. Create tasks (independent — no dependencies)
TaskCreate({
  subject: "Implement [Feature A]",
  description: "[Detailed requirements for Feature A]\n\nFile ownership: src/features/a/",
  activeForm: "Implementing Feature A"
})
TaskCreate({
  subject: "Implement [Feature B]",
  description: "[Detailed requirements for Feature B]\n\nFile ownership: src/features/b/",
  activeForm: "Implementing Feature B"
})
TaskCreate({
  subject: "Implement [Feature C]",
  description: "[Detailed requirements for Feature C]\n\nFile ownership: src/features/c/",
  activeForm: "Implementing Feature C"
})

// 3. Spawn teammates (all in parallel, single message)
Task({
  team_name: "athirat", name: "mami",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Mami, midwife of the gods, builder of [Feature A]. Claim task #1 from the task list. Read CLAUDE.md for project conventions. [Specific context about Feature A]. When done, mark the task completed and notify athirat-lead.",
  run_in_background: true
})
Task({
  team_name: "athirat", name: "tip'eret",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Tip'eret, beauty of the craft, builder of [Feature B]. Claim task #2 from the task list. Read CLAUDE.md for project conventions. [Specific context about Feature B]. When done, mark the task completed and notify athirat-lead.",
  run_in_background: true
})
Task({
  team_name: "athirat", name: "kaptaru",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Kaptaru, the bridge between worlds, builder of [Feature C]. Claim task #3 from the task list. Read CLAUDE.md for project conventions. [Specific context about Feature C]. When done, mark the task completed and notify athirat-lead.",
  run_in_background: true
})
```

**File ownership matrix:**

| Teammate | Owns | Must NOT touch |
|----------|------|----------------|
| mami | `src/features/a/`, `__tests__/features/a/` | Features B and C |
| tip'eret | `src/features/b/`, `__tests__/features/b/` | Features A and C |
| kaptaru | `src/features/c/`, `__tests__/features/c/` | Features A and B |

---

## Template 2: Pipeline (Sequential)

**Use when:** Work has natural dependencies — research must complete before design, design before implementation, implementation before testing.

**Team name:** Kaptaru (connecting systems)

```javascript
// 1. Create team
TeamCreate({ team_name: "kaptaru-pipeline", description: "Sequential feature pipeline" })

// 2. Create tasks with dependencies
TaskCreate({ subject: "Research best practices", description: "Research [topic]. Output findings to a summary.", activeForm: "Researching..." })  // #1
TaskCreate({ subject: "Design implementation plan", description: "Based on research findings, create a detailed plan.", activeForm: "Designing..." })  // #2
TaskCreate({ subject: "Implement the feature", description: "Execute the plan. Write clean, tested code.", activeForm: "Implementing..." })  // #3
TaskCreate({ subject: "Write comprehensive tests", description: "Unit + integration tests for the implementation.", activeForm: "Testing..." })  // #4

TaskUpdate({ taskId: "2", addBlockedBy: ["1"] })
TaskUpdate({ taskId: "3", addBlockedBy: ["2"] })
TaskUpdate({ taskId: "4", addBlockedBy: ["3"] })

// 3. Spawn a researcher to start (others wait for unblocking)
Task({
  team_name: "kaptaru-pipeline", name: "melissa",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Melissa, holy bee and researcher. Claim task #1. Research [topic] thoroughly. When done, mark it completed and check TaskList for the next available task. Continue working through unblocked tasks.",
  run_in_background: true
})

// 4. Spawn an implementer (will wait until task #3 unblocks)
Task({
  team_name: "kaptaru-pipeline", name: "nintu",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Nintu, supreme mother of all lands, the builder. Check TaskList periodically. When task #3 unblocks, claim it and implement. Then continue to task #4 if available.",
  run_in_background: true
})
```

---

## Template 3: Research Swarm (Competing Hypotheses)

**Use when:** The root cause is unclear, multiple theories need testing in parallel, or you need comprehensive research from multiple angles.

**Team name:** Elat (divine structural wisdom)

```javascript
// 1. Create team
TeamCreate({ team_name: "elat-research", description: "Competing hypothesis investigation" })

// 2. Create tasks (one per hypothesis)
TaskCreate({ subject: "Hypothesis A: [theory]", description: "Investigate whether [theory A] explains the issue. Gather evidence for and against.", activeForm: "Investigating hypothesis A" })
TaskCreate({ subject: "Hypothesis B: [theory]", description: "Investigate whether [theory B] explains the issue. Gather evidence for and against.", activeForm: "Investigating hypothesis B" })
TaskCreate({ subject: "Hypothesis C: [theory]", description: "Investigate whether [theory C] explains the issue. Gather evidence for and against.", activeForm: "Investigating hypothesis C" })
TaskCreate({ subject: "Synthesize findings", description: "Review all hypotheses, identify the winner, write conclusions.", activeForm: "Synthesizing..." })

TaskUpdate({ taskId: "4", addBlockedBy: ["1", "2", "3"] })

// 3. Spawn investigators (adversarial — they challenge each other)
Task({
  team_name: "elat-research", name: "devorah",
  subagent_type: "Explore", model: "sonnet",
  prompt: "You are Devorah, the prophetess-bee who navigates the labyrinth. Investigate Hypothesis A: [theory]. Explore the codebase for evidence. Message your teammates to challenge their findings. When done, mark task #1 completed.",
  run_in_background: true
})
Task({
  team_name: "elat-research", name: "melissa",
  subagent_type: "Explore", model: "sonnet",
  prompt: "You are Melissa, holy bee of the Magna Mater. Investigate Hypothesis B: [theory]. Explore the codebase for evidence. Message your teammates to challenge their findings. When done, mark task #2 completed.",
  run_in_background: true
})
Task({
  team_name: "elat-research", name: "membliaros",
  subagent_type: "Explore", model: "sonnet",
  prompt: "You are Membliaros, waters without light, keeper of deep memory. Investigate Hypothesis C: [theory]. Explore the codebase for evidence. Message your teammates to challenge their findings. When done, mark task #3 completed.",
  run_in_background: true
})
```

---

## Template 4: Phase Completion

**Use when:** A project phase is partially done and needs multiple specialists to finish: deploy, test, polish.

**Team name:** Qedeshot (the priestesses finishing the rite)

```javascript
// 1. Create team
TeamCreate({ team_name: "qedeshot-completion", description: "Complete Phase N" })

// 2. Create tasks from remaining work
TaskCreate({ subject: "Implement cron pipeline", description: "[Details from roadmap/plan]", activeForm: "Building cron pipeline" })
TaskCreate({ subject: "Deploy configuration", description: "[Details from roadmap/plan]", activeForm: "Configuring deploy" })
TaskCreate({ subject: "Integration tests", description: "[Details from roadmap/plan]", activeForm: "Writing integration tests" })
TaskCreate({ subject: "Polish and accessibility", description: "[Details from roadmap/plan]", activeForm: "Polishing UI" })

// 3. Spawn specialists
Task({
  team_name: "qedeshot-completion", name: "kaptaru",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Kaptaru, the bridge between worlds, builder of the pipeline. Claim task #1. Read CLAUDE.md and the relevant plan file for context. Build the cron pipeline according to spec.",
  run_in_background: true
})
Task({
  team_name: "qedeshot-completion", name: "hestia",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Hestia, keeper of the hearth. Claim task #2. Configure deployment according to the project's hosting requirements.",
  run_in_background: true
})
Task({
  team_name: "qedeshot-completion", name: "sassuratu",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Sassuratu, the birth-goddesses who test each creation. Claim task #3. Write comprehensive integration tests for all features built in this phase.",
  run_in_background: true
})
```

---

## Template 5: Code Review Tribunal

**Use when:** A PR or set of changes needs thorough, multi-dimensional review.

**Team name:** Elat (wisdom)

```javascript
// 1. Create team
TeamCreate({ team_name: "elat-review", description: "Multi-perspective code review" })

// 2. Spawn reviewers with different lenses (all parallel)
Task({
  team_name: "elat-review", name: "themis",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Themis, whose name traces to the thmtm — the deep waters of divine law. Review the recent changes for security vulnerabilities: SQL injection, XSS, auth bypass, OWASP top 10. Send findings to elat-lead.",
  run_in_background: true
})
Task({
  team_name: "elat-review", name: "karme",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Karme, daughter of Phoenix — the Phoenician eye. Review the recent changes for code quality: naming, structure, patterns, DRY, SOLID. Send findings to elat-lead.",
  run_in_background: true
})
Task({
  team_name: "elat-review", name: "sassuratu",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Sassuratu, the birth-goddesses who shape and test each creation. Review the recent changes for test coverage: are edge cases handled? Are tests meaningful or just line-count padding? Send findings to elat-lead.",
  run_in_background: true
})
```

---

## Choosing a Template

| Situation | Template | Team Name |
|-----------|----------|-----------|
| Multiple independent features | Parallel Features | Athirat |
| Work with natural ordering | Pipeline | Kaptaru |
| Bug investigation, unclear cause | Research Swarm | Elat |
| Phase nearly done, multiple loose ends | Phase Completion | Qedeshot |
| PR needs thorough review | Code Review Tribunal | Elat |
| New system from scratch | Parallel Features + Pipeline | Tiamat |

---

## Prompt Engineering for Teammates

Every teammate prompt should include:

1. **Identity**: "You are [Name], [role description]."
2. **Task claim**: "Claim task #N from the task list."
3. **Context loading**: "Read CLAUDE.md for project conventions."
4. **Specific instructions**: What to build/investigate/review.
5. **File ownership**: What files they own, what they must not touch.
6. **Completion signal**: "When done, mark the task completed and notify [lead-name]."

```
You are Kaptaru, the bridge between worlds, builder of the data pipeline.
Claim task #1 from the task list. Read CLAUDE.md for project conventions
and the relevant plan file at plans/phase-0/implementation-plan.md for
requirements.

Build the cron pipeline that fetches events from all configured sources
and upserts them into Supabase.

File ownership: scripts/cron-*.ts, src/lib/supabase/ingest.ts
Do NOT modify files outside your ownership.

When done, mark task #1 completed and send a summary to qedesha-lead.
```
