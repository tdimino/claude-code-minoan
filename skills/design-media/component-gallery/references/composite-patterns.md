# Composite Patterns

Workflow-level patterns that the canonical 60 don't name — each is a composition of atoms, documented here so research queries like "how do others build a command palette" resolve to constituent components with real precedent instead of nothing. Updated 2026-09-01; ingest with `source_kind=curated-pattern` to make these RAG-visible.

Composites reference canonical component IDs. Research each constituent in the RAG first — the atoms carry the accessibility and state conventions; the composite adds orchestration.

## Command Palette

**Composes:** Search input, Combobox, Modal, List, Badge

⌘K-summoned modal combining fuzzy search over commands with keyboard-first navigation. The distinguishing behaviors: global shortcut registration, recency/frequency ranking, grouped results with section headers, per-item shortcut hints (Badge), nested pages (typing into a command opens sub-options), and instant dismiss restoring focus to the invoking context. Precedents: GitHub, Linear, Figma, Vercel — all converge on centered-top placement, ~640px width, results capped near 8 visible with scroll.

## App Shell / Sidebar Navigation

**Composes:** Navigation, Drawer, Tooltip, Avatar, Separator

The persistent application frame: collapsible rail (icon-only ~64px ↔ expanded ~240-280px), active-route indication, grouped nav sections with Separators, user/account block anchored bottom, Tooltips on collapsed icons. Behaviors the atoms don't cover: collapse-state persistence, responsive breakpoint where the rail becomes an overlay Drawer, and keyboard traversal of the whole tree. Public-sector systems (GOV.UK, USWDS) document the accessibility floor; product systems (Polaris, Atlassian) document density.

## Multi-Step Form / Wizard

**Composes:** Stepper, Form, Progress indicator, Alert, Button group

Sequenced form pages with a visible step map. Orchestration beyond the atoms: per-step validation gating the Next control, back-navigation preserving entered state, savable drafts, review-before-submit summary step, and error placement that names the failing step from anywhere. The Stepper atom (18 upstream examples) covers the indicator; this composite covers the state machine around it.

## Filter Bar / Faceted Filtering

**Composes:** Combobox, Badge, Checkbox, Popover, Button

Applied-filters-as-chips above a result set: each active filter renders as a dismissible Badge, adding filters happens through Popover-anchored controls per facet, a clear-all affordance appears past one active filter, and result counts update per facet option. The convergent precedent (commerce and data-heavy systems) keeps applied state visible without opening any menu — filters that hide inside a drawer test worse.

## Agent Console

**Composes:** Card, Tabs, Table, Badge, Progress indicator + the AI overlay's tool-call-card and agent-status patterns

The operational view of autonomous work: run list with live status, per-run detail (steps, tool calls, artifacts), log/timeline toggle via Tabs, and intervention controls (pause, cancel, approve). This is the `composio-agent-console-pattern.md` diorama generalized from marketing mockup to product surface — see that file for the visual treatment, this entry for the structure. Constituent AI behaviors live in `ai-components.md`.

## Notification Center

**Composes:** Popover, List, Badge, Tabs, Empty state

Bell-anchored Popover with unread Badge count, read/unread visual state, grouped-by-time sections, filter Tabs (all/mentions/system), mark-all-read, and a designed Empty state — the atom most systems forget here. Real-time arrival should not steal focus or reorder under the pointer.
