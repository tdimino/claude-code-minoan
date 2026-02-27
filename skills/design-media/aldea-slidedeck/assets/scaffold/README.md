# Aldea Slide Deck Scaffold

Starter template for creating Aldea-branded slide decks.

## Quick Start

```bash
# Copy this scaffold to your project
cp -r ~/.claude/skills/aldea-slidedeck/assets/scaffold/* ./my-deck/
cd my-deck

# Install dependencies
npm install

# Start dev server
npm run dev
# Opens at http://localhost:3200

# Edit pages/index.tsx to add your slides
```

## Structure

```
├── components/           # Reusable slide components
│   ├── SlideLayout.tsx   # Base slide wrapper
│   ├── MetricCard.tsx    # Numbered key points
│   ├── FlowDiagram.tsx   # Workflow steps
│   ├── ComparisonTable.tsx # Feature matrices
│   └── CodeBlock.tsx     # Syntax-highlighted code
├── pages/
│   ├── _app.tsx          # App wrapper
│   └── index.tsx         # Your slides go here
├── styles/
│   └── globals.css       # Design tokens, utilities
├── scripts/
│   └── export-pdf.js     # PDF generation script
├── public/
│   └── images/           # Place your images here
└── [config files]
```

## Export

```bash
# Static HTML (shareable)
npm run export
# Output: out/

# PDF (requires dev server running)
npm run dev &
npm run pdf
# Output: output/aldea-deck-YYYY-MM-DD.pdf
```

## Customization

1. **Add logo:** Place `aldea-logo.png` in `public/images/`
2. **Update slide count:** Edit SlideLayout.tsx line with "/ 37"
3. **Add slides:** Copy templates from pages/index.tsx

## Resources

- Full documentation: `~/.claude/skills/aldea-slidedeck/SKILL.md`
- Design system: `~/.claude/skills/aldea-slidedeck/references/design-system.md`
- Component docs: `~/.claude/skills/aldea-slidedeck/references/component-patterns.md`
- Slide templates: `~/.claude/skills/aldea-slidedeck/references/slide-templates.md`
