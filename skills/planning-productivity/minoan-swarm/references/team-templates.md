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

## Template 3: Research Knossot (Competing Hypotheses)

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
  team_name: "elat-research", name: "deborah",
  subagent_type: "Explore", model: "sonnet",
  prompt: "You are Deborah, the prophetess-bee who navigates the labyrinth. Investigate Hypothesis A: [theory]. Explore the codebase for evidence. Message your teammates to challenge their findings. When done, mark task #1 completed.",
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

## Template 6: Truth & Balance

**Use when:** An implementation needs multi-dimensional quality verification — correctness, performance, accessibility, standards compliance. Each reviewer weighs the code against a different standard, as Ma'at's feather weighs against the heart.

**Team name:** Ma'at (truth, cosmic order, the balance that sustains all)

```javascript
// 1. Create team
TeamCreate({ team_name: "maat-balance", description: "Multi-dimensional quality verification" })

// 2. Create tasks — one per quality dimension
TaskCreate({
  subject: "Correctness audit",
  description: "Verify all business logic, data flows, and state transitions behave correctly. Run tests, trace edge cases manually, confirm error handling covers real failure modes. Write findings to a summary.",
  activeForm: "Auditing correctness"
})
TaskCreate({
  subject: "Performance audit",
  description: "Profile render times, bundle size, query counts, memory usage. Identify N+1 queries, unnecessary re-renders, unindexed lookups. Benchmark before/after if changes are warranted.",
  activeForm: "Auditing performance"
})
TaskCreate({
  subject: "Accessibility & standards audit",
  description: "Check WCAG 2.1 AA compliance: keyboard navigation, screen reader labels, color contrast, focus management. Verify semantic HTML, ARIA roles, and form labeling.",
  activeForm: "Auditing accessibility"
})
TaskCreate({
  subject: "Weigh the heart — synthesize verdicts",
  description: "Collect all audit findings. Produce a single verdict: PASS (ship), CONDITIONAL (ship with noted caveats), or FAIL (block until resolved). List every finding by severity (P0-P3).",
  activeForm: "Synthesizing verdicts"
})

TaskUpdate({ taskId: "4", addBlockedBy: ["1", "2", "3"] })

// 3. Spawn auditors (all parallel)
Task({
  team_name: "maat-balance", name: "hokhmah",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Hokhmah, חָכְמָה — Wisdom herself, who was with the Creator before the world was made. You audit for correctness. Claim task #1. Read CLAUDE.md for conventions. Trace every data flow, verify every edge case, run the test suite. Your standard is truth — does the code do what it claims? When done, mark the task completed and send findings to maat-lead.",
  run_in_background: true
})
Task({
  team_name: "maat-balance", name: "al-uzza",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Al-Uzza, العزى — The Mighty One, Venus as morning star. You audit for performance. Claim task #2. Read CLAUDE.md for conventions. Profile, benchmark, measure. Your standard is power — does the code run as fast as it should? Identify bottlenecks, unnecessary work, scaling concerns. When done, mark the task completed and send findings to maat-lead.",
  run_in_background: true
})
Task({
  team_name: "maat-balance", name: "yashar",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Yashar, יָשָׁר — the Straight and Beautiful, uprightness made manifest. You audit for accessibility and standards. Claim task #3. Check WCAG 2.1 AA, semantic HTML, keyboard nav, screen reader compat, color contrast. Your standard is justice — can everyone use this? When done, mark the task completed and send findings to maat-lead.",
  run_in_background: true
})
```

**Verdict format (task #4):**

```
## Verdict: [PASS | CONDITIONAL | FAIL]

### P0 — Must fix before ship
- (none, or list)

### P1 — Should fix before ship
- ...

### P2 — Fix soon after ship
- ...

### P3 — Nice to have
- ...
```

---

## Template 7: Fate's Reckoning

**Use when:** A release candidate needs final audit before shipping. Security, dependency health, migration safety, changelog accuracy. Manat measures fate — this team determines whether the code ships or doesn't.

**Team name:** Manat (She who measures fate — eldest of the Arabian triad)

```javascript
// 1. Create team
TeamCreate({ team_name: "manat-reckoning", description: "Pre-release audit and go/no-go decision" })

// 2. Create tasks — one per audit dimension
TaskCreate({
  subject: "Security audit",
  description: "OWASP top 10 check. Scan for: SQL injection, XSS, auth bypass, CSRF, insecure deserialization, hardcoded secrets, overprivileged endpoints. Check dependency CVEs via `npm audit` / `bundle audit` / equivalent.",
  activeForm: "Security audit"
})
TaskCreate({
  subject: "Dependency & supply chain audit",
  description: "Check for outdated dependencies, known CVEs, unmaintained packages, license conflicts. Verify lockfile integrity. Flag any dependency added since last release.",
  activeForm: "Dependency audit"
})
TaskCreate({
  subject: "Migration & data safety audit",
  description: "Review all database migrations since last release. Check for: irreversible operations without rollback, missing indexes on new columns, data loss risk, transaction safety. Verify migration order is deterministic.",
  activeForm: "Migration audit"
})
TaskCreate({
  subject: "Changelog & release notes",
  description: "Generate or verify CHANGELOG.md entries for all changes since last release. Cross-reference git log. Ensure every user-facing change is documented. Flag breaking changes.",
  activeForm: "Changelog audit"
})
TaskCreate({
  subject: "Fate's verdict — go/no-go",
  description: "Collect all audit results. Produce a GO / NO-GO / CONDITIONAL-GO decision with justification. List every blocker (if any) and every risk accepted (if conditional).",
  activeForm: "Rendering verdict"
})

TaskUpdate({ taskId: "5", addBlockedBy: ["1", "2", "3", "4"] })

// 3. Spawn auditors
Task({
  team_name: "manat-reckoning", name: "themis",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Themis, whose name traces to the thmtm — the deep waters of divine law. You are the security auditor. Claim task #1. Check OWASP top 10, scan for hardcoded secrets, review auth flows, check dependency CVEs. Your standard is inviolability — no vulnerability ships. When done, mark the task completed and send findings to manat-lead.",
  run_in_background: true
})
Task({
  team_name: "manat-reckoning", name: "qadeshet",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Qadeshet, קְדֶשֶׁת — the Holy One who guards boundaries. You audit the supply chain. Claim task #2. Check every dependency for CVEs, license conflicts, maintenance status. Verify the lockfile. Your standard is sanctity — nothing impure enters. When done, mark the task completed and send findings to manat-lead.",
  run_in_background: true
})
Task({
  team_name: "manat-reckoning", name: "tehom",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Tehom, תְּהוֹם — the Deep, the primordial foundation. You audit migrations and data safety. Claim task #3. Review every migration for reversibility, index coverage, transaction safety, data loss risk. Your standard is foundation — the substrate must hold. When done, mark the task completed and send findings to manat-lead.",
  run_in_background: true
})
Task({
  team_name: "manat-reckoning", name: "karme",
  subagent_type: "general-purpose", model: "sonnet",
  prompt: "You are Karme, daughter of Phoenix — the Phoenician eye that reads what others miss. You verify the changelog. Claim task #4. Cross-reference git log against CHANGELOG.md. Every user-facing change must be documented. Flag breaking changes, missing entries, inaccurate descriptions. When done, mark the task completed and send findings to manat-lead.",
  run_in_background: true
})
```

**Go/No-Go format (task #5):**

```
## Decision: [GO | NO-GO | CONDITIONAL-GO]

### Blockers (NO-GO until resolved)
- (none, or list with task owner)

### Risks Accepted (CONDITIONAL-GO)
- (none, or list with justification)

### All Clear
- Security: ✓/✗
- Dependencies: ✓/✗
- Migrations: ✓/✗
- Changelog: ✓/✗
```

---

## Choosing a Template

| Situation | Template | Knesset Name |
|-----------|----------|--------------|
| Multiple independent features | Parallel Features | Athirat |
| Work with natural ordering | Pipeline | Kaptaru |
| Bug investigation, unclear cause | Research Knossot | Elat |
| Phase nearly done, multiple loose ends | Phase Completion | Qedeshot |
| PR needs thorough review | Code Review Tribunal | Elat |
| Quality verification, multi-angle testing | Truth & Balance | Ma'at |
| Pre-release audit, go/no-go | Fate's Reckoning | Manat |
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
