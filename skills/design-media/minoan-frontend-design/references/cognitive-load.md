# Cognitive Load Assessment

Cognitive load is the total mental effort required to use an interface. Overloaded users make mistakes, get frustrated, and leave.

## Three Types of Cognitive Load

### Intrinsic Load — The Task Itself
Complexity inherent to what the user is trying to do. Structure it:
- Break complex tasks into discrete steps
- Provide scaffolding (templates, defaults, examples)
- Progressive disclosure — show what's needed now, hide the rest
- Group related decisions together

### Extraneous Load — Bad Design
Mental effort caused by poor design choices. Eliminate ruthlessly:
- Confusing navigation requiring mental mapping
- Unclear labels forcing users to guess
- Visual clutter competing for attention
- Inconsistent patterns preventing learning
- Unnecessary steps between intent and result

### Germane Load — Learning Effort
Mental effort spent building understanding. This is *good* cognitive load:
- Progressive disclosure revealing complexity gradually
- Consistent patterns rewarding learning
- Feedback confirming correct understanding
- Onboarding teaching through action, not text walls

## Cognitive Load Checklist

Evaluate the interface against these 8 items:

- [ ] **Single focus**: Can the user complete their primary task without distraction from competing elements?
- [ ] **Chunking**: Is information presented in digestible groups (4 items per group or fewer)?
- [ ] **Grouping**: Are related items visually grouped (proximity, borders, shared background)?
- [ ] **Visual hierarchy**: Is it immediately clear what's most important?
- [ ] **One thing at a time**: Can the user focus on a single decision before the next?
- [ ] **Minimal choices**: Are decisions simplified (4 visible options or fewer at any decision point)?
- [ ] **Working memory**: Does the user need to remember information from a previous screen to act on the current one?
- [ ] **Progressive disclosure**: Is complexity revealed only when needed?

**Scoring**: Count failed items. 0-1 = low cognitive load (good). 2-3 = moderate (address soon). 4+ = high (critical fix needed).

## The Working Memory Rule

Humans hold 4 items or fewer in working memory at once (Cowan, 2001). At any decision point, count distinct options/actions/information the user must simultaneously consider:

- **4 or fewer**: Within working memory — manageable
- **5-7**: Pushing the boundary — consider grouping or progressive disclosure
- **8+**: Overloaded — users will skip, misclick, or abandon

**Practical applications**:
- Navigation menus: 5 or fewer top-level items
- Form sections: 4 fields per group before a visual break
- Action buttons: 1 primary, 1-2 secondary, group the rest
- Dashboard widgets: 4 key metrics visible without scrolling
- Pricing tiers: 3 options (more causes analysis paralysis)

## Common Violations

| Violation | Problem | Fix |
|-----------|---------|-----|
| **Wall of Options** | 10+ choices, no hierarchy | Group, highlight recommended, progressive disclosure |
| **Memory Bridge** | Must remember step 1 info at step 3 | Keep context visible or repeat it |
| **Hidden Navigation** | Must build mental map | Show current location (breadcrumbs, active states) |
| **Jargon Barrier** | Technical language forces translation | Plain language; define domain terms inline |
| **Visual Noise Floor** | Every element same visual weight | Clear hierarchy: one primary, 2-3 secondary, rest muted |
| **Inconsistent Pattern** | Same action works differently in different places | Standardize interaction patterns |
| **Multi-Task Demand** | Must process multiple simultaneous inputs | Sequence the steps |
| **Context Switch** | Must jump between screens for one decision | Co-locate information needed for each decision |
