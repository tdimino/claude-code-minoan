# design-polish

Final quality pass fixing alignment, spacing, consistency, interaction states, and micro-details before shipping. Executes changes (unlike `/design-audit` and `/design-critique` which are report-only).

## Structure

```
design-polish/
├── SKILL.md                              — Checklist (what to check)
└── references/
    └── interface-craft-techniques.md     — Implementation details (how to fix)
```

## Credits

The checklist principles in SKILL.md draw from [pbakaus/impeccable](https://github.com/pbakaus/impeccable) (v1.6.0) by [Paul Bakaus](https://github.com/pbakaus)—a comprehensive frontend quality standard covering typography, color, motion, interaction, responsive, and spatial design.

The `references/interface-craft-techniques.md` file integrates techniques from [jakubkrehel/make-interfaces-feel-better](https://github.com/jakubkrehel/make-interfaces-feel-better) by [Jakub Krehel](https://github.com/jakubkrehel), based on the "Details that make interfaces feel better" article. Techniques include concentric border radius, shadow-as-border patterns, image outlines, scale-on-press, text-wrap balance/pretty, font smoothing, transition specificity, staggered animations, and hit area expansion.
