# CONTEXT.md Format

## Structure

```md
# {Project Name} — Domain Language

{One or two sentences: what this project is and why a shared vocabulary matters for it.}

## Language

**Term**:
One-sentence definition of what it IS, not what it does.
_Avoid_: synonym1, synonym2

**Another Term**:
Definition.
_Avoid_: confusable-word

## Relationships

- A **Term** has many **Other Terms**
- An **Other Term** belongs to exactly one **Term**

## Example dialogue

> **Dev:** "When a **Customer** places an **Order**, do we create the **Invoice** immediately?"
> **Domain expert:** "No — an **Invoice** is only generated once a **Fulfillment** is confirmed."

## Flagged ambiguities

- "account" was used to mean both **Customer** and **User** — resolved: these are distinct concepts.
```

## Rules

- **Be opinionated.** When multiple words exist for the same concept, pick the best one and list the others under _Avoid_.
- **Flag conflicts explicitly.** If a term is used ambiguously in the codebase, call it out in "Flagged ambiguities" with a clear resolution.
- **Keep definitions tight.** One sentence max. Define what it IS, not what it does.
- **Show relationships.** Use bold term names and express cardinality where obvious.
- **Only include domain-specific terms.** General programming concepts (timeouts, error types, utility patterns) don't belong. Before adding a term, ask: is this unique to this project's domain? Only the former belongs.
- **Group terms under subheadings** when natural clusters emerge. If all terms belong to a single cohesive area, a flat list is fine.
- **Write an example dialogue.** A short conversation demonstrating how the terms interact naturally and where boundaries lie between related concepts.
- **Track provenance.** If a term originates from an external source (a domain spec, an industry standard, a legacy system's naming), note the source parenthetically after the definition. This prevents future contributors from "correcting" a deliberate naming choice.

## Naming the file

Always `CONTEXT.md` at the project root. One file per project. If the project is a monorepo with distinct bounded contexts, use a `CONTEXT-MAP.md` at the root pointing to per-context `CONTEXT.md` files — but this is rare.
