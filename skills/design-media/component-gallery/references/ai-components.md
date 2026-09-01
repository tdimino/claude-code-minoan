# AI Component Overlay

AI-era interface patterns as an overlay on the 60 canonical component types. component.gallery has no AI category upstream — these patterns crystallized in 2025-2026 across the primary-source libraries (Vercel AI Elements, assistant-ui, CopilotKit, OpenAI Apps SDK) and are documented here as *behaviors composed from existing atoms*, never as restyled duplicates. Updated 2026-09-01; included in the RLAMA collection via curated pattern ingestion.

## Overlay Schema

Each pattern declares what it composes from the canonical 60 and what behavior is genuinely new:

```yaml
id: tool-call-card
category: ai-agent/tooling
composes: [card, badge, progress-indicator, accordion]
unique_behaviors:
  - streaming arguments render as they arrive
  - pending → running → succeeded/failed state progression
  - expandable raw payload
  - optional human approval gate
sources: [ai-elements/tool, assistant-ui/ToolUI, copilotkit/tool-call-rendering]
```

When researching one of these, query the RAG for its constituent atoms first (`Card`, `Badge`, `Accordion` accessibility and state conventions transfer directly), then layer the unique behaviors from the sources below.

## Conversation Patterns

| Pattern | Composes | Unique behaviors |
|---------|----------|------------------|
| **Prompt input / composer** | Textarea, Button, File upload | Auto-grow with max-height, Enter-to-send vs Shift+Enter, attachment chips, model selector slot, disabled-while-streaming with stop affordance, token-count feedback |
| **Message thread** | List, Avatar, Card | Role-differentiated bubbles (user right/accent, assistant flush-left), scroll anchoring that never yanks a scrolled-up reader, day/session separators, virtualized history |
| **Message branching** | Pagination, Button group | Sibling-version navigation per message (`< 2/3 >`), regenerate-creates-branch, edit-user-message-forks-thread |
| **Attachment preview** | Image, Card, Badge | Type-dependent chip vs thumbnail, upload progress state, remove-before-send, paste and drag capture |

## Streaming Patterns

| Pattern | Composes | Unique behaviors |
|---------|----------|------------------|
| **Streaming status** | Spinner, Skeleton | thinking → streaming → done/stopped lifecycle, cursor blink through pauses, chunk-buffered text (word-boundary flushes, not per-character), one polite `aria-live` announcement at completion — never per chunk |
| **Stop / regenerate** | Button | Single control relabeled by state; stop leaves partial text standing; regenerate branches rather than overwrites |
| **Reasoning disclosure** | Accordion | Collapsed-by-default "thinking" section, duration label ("Thought for 12s"), streams independently of the answer, auto-collapses when the answer begins |

## Tooling & Agency Patterns

| Pattern | Composes | Unique behaviors |
|---------|----------|------------------|
| **Tool-call card** | Card, Badge, Progress indicator, Accordion | Streaming arguments, pending/running/succeeded/failed progression, expandable raw input/output payload, error state with retry |
| **Approval card** | Card, Button group, Alert | Blocks the stream pending human decision, explicit approve/deny/always-allow, shows exactly what will run, timeout behavior stated |
| **Agent status / plan** | Progress indicator, Tree view, Badge | Live step list with per-step state, nested sub-agent activity, elapsed time per step, collapsible completed phases |
| **Citation / source card** | Badge, Popover, Card | Inline superscript or chip anchored to the claim, hover/focus preview with title-source-snippet, dedented source list at message end, dead-link state |

## Workspace Patterns

| Pattern | Composes | Unique behaviors |
|---------|----------|------------------|
| **Artifact workspace** | Drawer, Tabs, Card | Side-by-side conversation + generated artifact, version stepper, view/source toggle, per-version diff affordance |
| **Code block with actions** | Badge, Button, Toast | Language label, copy-with-confirmation, run/apply affordances, streaming syntax highlight that never reflows earlier lines |
| **Context / token meter** | Progress bar, Tooltip | Live context-window usage, cost estimate on hover, warning threshold before truncation, per-message token attribution |
| **Model selector** | Select, Combobox, Badge | Capability badges (vision, tools, context size), per-model cost hint, mid-conversation switch semantics stated |
| **Voice I/O** | Button, Progress indicator | Push-to-talk vs open-mic states, live waveform/level feedback, interim vs final transcript rendering, barge-in (interrupt playback by speaking) |

## Accessibility Baseline

The atoms carry their own ARIA conventions — the overlay adds three rules the sources agree on: streaming containers announce completion once via `aria-live="polite"` (assertive interrupts, per-chunk spams); every autonomous process (agent steps, tool calls) is perceivable without color alone (state text, not just a dot); and stop/approval controls are reachable by keyboard while the stream runs, not after.

## Sources

| Library | URL | What it's authoritative for |
|---------|-----|------------------------------|
| Vercel AI Elements | https://elements.ai-sdk.dev/ | shadcn-based registry: chatbot, code, voice, workflow component groups |
| assistant-ui | https://www.assistant-ui.com/ | Composable React primitives: ThreadRoot, ComposerInput, ToolUI, BranchPicker |
| CopilotKit | https://docs.copilotkit.ai/ | Generative-UI primitives, human-in-the-loop approval flows |
| OpenAI Apps SDK | https://developers.openai.com/apps-sdk/ | MCP-app surfaces, embedded app UI architecture |

## Cross-Skill

- **conductor-motion** owns the *animation* of these behaviors — its `streaming-text` mode implements the streaming-status pattern as self-contained HTML; borrow its scroll-anchoring and chunk-flush specifics.
- **minoan-frontend-design** owns the aesthetic once research settles the structure.
