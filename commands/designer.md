# Designer Mode

Use **ultrathink** for deep analysis.

**Tool Preferences (per CLAUDE.md):**
- Use **Firecrawl** over WebFetch for scraping design inspiration
- Use **Exa** over WebSearch for researching UI/UX patterns
- Use **agent-browser** for taking browser snapshots

## Design Baselines (2025-2026)

Audit against these five reference points:

| Company | Learn From |
|---------|------------|
| **Linear** | Quality-as-strategy, keyboard-first, performance IS design, opinionated software, zero-bugs policy |
| **Vercel** | Web Interface Guidelines (read via `frontend-design` skill's `references/vercel-web-interface-guidelines.md`), Geist design system, design engineering |
| **Stripe** | Accessible color systems, light-mode-first premium, documentation-as-design, signature visual elements |
| **Raycast** | Progressive disclosure via action bar, search-centered architecture, Fast > Simple > Delightful priority |
| **Resend** | Code-first design (codebase IS the source of truth, not Figma), polish IN code, design as discipline anyone exercises |

## Guiding Frameworks

- **Novelty budget** (Arc/Dia): Every product has a limited novelty budget. Innovate where it matters, use familiarity everywhere else. "Familiar, but elevated."
- **Workbench over chatbox** (Linear): For AI interfaces, build functional domain-specific tools with traditional UI, then complement with AI—don't default to chat.
- **Quality creates gravity** (Linear): Quality pulls people in rather than requiring push. Ship nothing half-baked.
- **APCA contrast** (Vercel): Use Accessible Perceptual Contrast Algorithm over WCAG 2 for more accurate perceptual contrast measurement.

## Audit Process

Audit desktop UI/UX and mobile UI/UX separately—optimize for each modality's strengths and constraints.

### Desktop
1. Take a browser snapshot of the current page
2. Audit against the Vercel Web Interface Guidelines checklist
3. Check: interactions, animation quality, loading states, all-states-designed, accessibility, color contrast (APCA), typography scale, spatial composition, keyboard navigation
4. Identify the single most impactful improvement
5. Propose changes with specific file paths and line numbers

### Mobile
1. Take a mobile-viewport snapshot (375px width)
2. Check: touch targets (min 44px), thumb-zone reachability, viewport meta, safe area insets, input font >= 16px (prevents iOS auto-zoom), scroll behavior
3. Identify the single most impactful improvement
4. Propose changes with specific file paths and line numbers

### Output Format
Produce a ranked list of issues, each with: (a) what's wrong, (b) which baseline it violates, (c) the specific file and line to change.

The bar: Match the visual polish, interaction quality, and attention to detail of the five baselines above.
