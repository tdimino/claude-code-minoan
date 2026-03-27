# Heuristics Scoring Guide

Score each of Nielsen's 10 Usability Heuristics on a 0-4 scale. A 4 means genuinely excellent, not "good enough."

## Nielsen's 10 Heuristics

### 1. Visibility of System Status
Keep users informed through timely feedback.
- Loading indicators, action confirmations, progress indicators, navigation active states, inline validation.
- **0** = No feedback. **1** = Rare. **2** = Partial. **3** = Good, minor gaps. **4** = Every action confirms.

### 2. Match Between System and Real World
Speak the user's language. Follow real-world conventions.
- Familiar terminology, logical information order, recognizable icons, domain-appropriate language.
- **0** = Pure jargon. **1** = Mostly confusing. **2** = Mixed. **3** = Mostly natural. **4** = Fluent throughout.

### 3. User Control and Freedom
Clear "emergency exit" from unwanted states.
- Undo/redo, cancel buttons, clear navigation back, escape from multi-step processes.
- **0** = Users trapped. **1** = Difficult exits. **2** = Some exits. **3** = Good control. **4** = Full undo/cancel/back everywhere.

### 4. Consistency and Standards
Same words/situations/actions should mean the same thing.
- Consistent terminology, visual consistency, platform conventions, interaction patterns.
- **0** = Different products stitched together. **1** = Many inconsistencies. **2** = Partially consistent. **3** = Mostly consistent. **4** = Fully cohesive.

### 5. Error Prevention
Prevent problems before good error messages.
- Confirmation before destructive actions, constraints on invalid input, smart defaults, autosave.
- **0** = No guardrails. **1** = Few safeguards. **2** = Common errors caught. **3** = Most paths blocked. **4** = Errors nearly impossible.

### 6. Recognition Rather Than Recall
Minimize memory load. Make options visible or retrievable.
- Visible options, contextual help, recent items, autocomplete, labeled icons.
- **0** = Heavy memorization. **1** = Mostly recall. **2** = Some aids. **3** = Good recognition. **4** = Everything discoverable.

### 7. Flexibility and Efficiency of Use
Accelerators speed up expert interaction without slowing novices.
- Keyboard shortcuts, customization, bulk actions, power user features.
- **0** = One rigid path. **1** = Limited flexibility. **2** = Some shortcuts. **3** = Good accelerators. **4** = Highly flexible.

### 8. Aesthetic and Minimalist Design
Every element should serve a purpose.
- Only necessary information visible, clear hierarchy, no decorative clutter.
- **0** = Overwhelming. **1** = Cluttered. **2** = Some clutter. **3** = Mostly clean. **4** = Every element earns its pixel.

### 9. Help Users Recognize, Diagnose, and Recover from Errors
Error messages: plain language, precise problem, constructive solution.
- Specific problem identification, actionable suggestions, errors near the source, non-blocking.
- **0** = Cryptic. **1** = Vague. **2** = Clear but unhelpful. **3** = Clear with suggestions. **4** = Perfect recovery.

### 10. Help and Documentation
Easy to find, task-focused, concise.
- Searchable help, contextual hints, task-focused organization, accessible without leaving context.
- **0** = No help. **1** = Hard to find. **2** = Basic FAQ. **3** = Good, searchable. **4** = Excellent contextual help.

## Score Summary

| Score Range | Rating | Meaning |
|-------------|--------|---------|
| 36-40 | Excellent | Minor polish — ship it |
| 28-35 | Good | Address weak areas, solid foundation |
| 20-27 | Acceptable | Significant improvements needed |
| 12-19 | Poor | Major UX overhaul required |
| 0-11 | Critical | Redesign needed |

## Issue Severity (P0-P3)

| Priority | Name | Description | Action |
|----------|------|-------------|--------|
| **P0** | Blocking | Prevents task completion | Fix immediately |
| **P1** | Major | Significant difficulty or WCAG AA violation | Fix before release |
| **P2** | Minor | Annoyance, workaround exists | Fix in next pass |
| **P3** | Polish | Nice-to-fix, no real user impact | Fix if time permits |

**Tip**: If unsure between levels, ask: "Would a user contact support about this?" If yes, at least P1.

## Audit Health Score (5 Technical Dimensions)

For the Post-Build Audit step, score these 5 dimensions 0-4 each (total /20):

| # | Dimension | 0 | 1 | 2 | 3 | 4 |
|---|-----------|---|---|---|---|---|
| 1 | **Accessibility** | Fails WCAG A | Few ARIA labels, no keyboard nav | Some a11y effort, significant gaps | WCAG AA mostly met, minor gaps | WCAG AA fully met |
| 2 | **Performance** | Layout thrash, unoptimized | No lazy loading, expensive animations | Some optimization, gaps remain | Mostly optimized, minor improvements | Fast, lean, well-optimized |
| 3 | **Responsive** | Desktop-only, breaks on mobile | Some breakpoints, many failures | Works on mobile, rough edges | Responsive, minor touch/overflow issues | Fluid, all viewports, proper touch targets |
| 4 | **Theming** | Hard-coded everything | Minimal tokens, mostly hard-coded | Tokens exist, inconsistently used | Tokens used, minor hard-coded values | Full token system, dark mode works |
| 5 | **Anti-Patterns** | 5+ AI slop tells | 3-4 tells | 1-2 noticeable | Subtle issues only | Distinctive, intentional design |

**Rating bands**: 18-20 Excellent, 14-17 Good, 10-13 Acceptable, 6-9 Poor, 0-5 Critical.
