# Component Patterns

Reusable components for Aldea slide decks with props, examples, and best practices.

---

## SlideLayout

Universal slide wrapper providing branding, grid overlay, and chrome elements.

### Props

```typescript
interface SlideLayoutProps {
  children: React.ReactNode;
  chapter?: string;        // e.g., "01 — CLINICAL EVALUATIONS"
  slideNumber?: number;    // Current slide number
  totalSlides?: number;    // Total slide count (displays as "01 / NN")
  showGrid?: boolean;      // Blueprint grid overlay (default: true)
  showCorners?: boolean;   // Corner marks (default: true)
}
```

### Structure

```
┌─────────────────────────────────────────────────┐
│ [Chapter Badge]            [Logo] [##/37]       │
│ ┌─────────────────────────────────────────────┐ │
│ │                                             │ │
│ │            CHILDREN CONTENT                 │ │
│ │            (1280 × 720px)                   │ │
│ │                                             │ │
│ └─────────────────────────────────────────────┘ │
│ [Gradient divider line]                         │
└─────────────────────────────────────────────────┘
```

### Example Usage

```tsx
import { SlideLayout } from '../components';

const MySlide = () => (
  <SlideLayout chapter="02 — DATA PIPELINE" slideNumber={5} totalSlides={25}>
    <div className="h-full flex flex-col px-16 pt-16 pb-10">
      <h2 className="font-display text-3xl text-text-primary mb-6">
        Data Processing Overview
      </h2>
      <div className="flex-1">
        {/* Slide content */}
      </div>
    </div>
  </SlideLayout>
);
```

### Features

- **Fixed dimensions**: 1280×720px (16:9)
- **Blueprint grid**: Dual-layer (40px + 10px)
- **Corner marks**: Cyan brackets top-left and bottom-right
- **Chapter badge**: Monospace, cyan border
- **Logo**: Top-right, brightness-adjusted
- **Slide counter**: Format "MM / NN"
- **Bottom line**: Gradient cyan divider

---

## MetricCard

Numbered metric cards for KPIs, evaluation criteria, or feature lists.

### Props

```typescript
interface MetricCardProps {
  number: number;          // Displayed as 01, 02, etc.
  title: string;
  description?: string;
  compact?: boolean;       // Reduces font sizes
}
```

### Layout

```
┌─────────────────────────────────────┐
│ [01] Title Text                     │
│      Description text goes here...  │
└─────────────────────────────────────┘
```

### Example Usage

```tsx
import { MetricCard } from '../components';

// Single metric
<MetricCard
  number={1}
  title="Response Quality"
  description="Measures accuracy and helpfulness"
/>

// Grid of metrics
<div className="grid grid-cols-3 gap-3">
  <MetricCard number={1} title="Accuracy" description="Data correctness" />
  <MetricCard number={2} title="Speed" description="Response time" />
  <MetricCard number={3} title="Clarity" description="Message clarity" />
</div>

// Compact mode
<MetricCard number={1} title="Metric" compact={true} />
```

### Styling Notes

- Number badge: Cyan border, semi-transparent cyan background
- Hover effect: Border becomes full cyan
- Compact mode: Smaller text, reduced padding

---

## FlowDiagram

Sequential workflow visualization with horizontal or vertical orientation.

### Props

```typescript
interface FlowStep {
  label: string;
  sublabel?: string;
}

interface FlowDiagramProps {
  steps: FlowStep[];
  vertical?: boolean;      // Column layout (default: false = horizontal)
  compact?: boolean;       // Smaller sizing
}
```

### Layouts

**Horizontal (default):**
```
[Research] → [Curate] → [Build] → [Ship]
```

**Vertical:**
```
[Research]
    ↓
[Curate]
    ↓
[Build]
    ↓
[Ship]
```

### Example Usage

```tsx
import { FlowDiagram } from '../components';

// Horizontal workflow
<FlowDiagram
  steps={[
    { label: 'Research', sublabel: '1-2 hours' },
    { label: 'Curate', sublabel: 'Clean data' },
    { label: 'Build', sublabel: 'Iterate' },
    { label: 'Ship', sublabel: 'Deploy' }
  ]}
/>

// Vertical workflow
<FlowDiagram
  steps={[
    { label: 'Input', sublabel: 'PDF documents' },
    { label: 'Process', sublabel: 'OCR conversion' },
    { label: 'Output', sublabel: 'Markdown' }
  ]}
  vertical={true}
/>

// Compact mode
<FlowDiagram steps={[...]} compact={true} />
```

### Styling Notes

- Step boxes: `bg-canvas-700/60`, `border-blueprint-grid/50`
- Arrows: Cyan color, 50% opacity
- Sublabels: Smaller text, muted color

---

## ComparisonTable

Feature comparison matrices with boolean and text cell support.

### Props

```typescript
interface TableRow {
  label: string;
  values: (string | boolean)[];
}

interface ComparisonTableProps {
  headers: string[];
  rows: TableRow[];
  compact?: boolean;
}
```

### Cell Rendering

- `true` → Green checkmark ✓
- `false` → Muted dash —
- String → Rendered as-is

### Example Usage

```tsx
import { ComparisonTable } from '../components';

<ComparisonTable
  headers={['Feature', 'Basic', 'Pro', 'Enterprise']}
  rows={[
    { label: 'API Access', values: [true, true, true] },
    { label: 'Support', values: ['Email', '24/7 Chat', 'Dedicated'] },
    { label: 'Custom Models', values: [false, true, true] },
    { label: 'SLA', values: [false, false, true] }
  ]}
/>

// Compact mode for smaller tables
<ComparisonTable
  headers={['Metric', 'Before', 'After']}
  rows={[
    { label: 'Response Time', values: ['2.5s', '0.3s'] },
    { label: 'Accuracy', values: ['78%', '94%'] }
  ]}
  compact={true}
/>
```

### Styling Notes

- Headers: Monospace, uppercase, cyan color
- Rows: Alternating backgrounds (even rows darker)
- Borders: Subtle `blueprint-grid/30` dividers
- Boolean cells: Center-aligned

---

## CodeBlock

Syntax-highlighted code snippets with language-aware coloring.

### Props

```typescript
interface CodeBlockProps {
  code: string;
  language?: string;       // Default: "typescript"
  title?: string;          // Label above code
  compact?: boolean;       // Smaller font (11px)
}
```

### Syntax Highlighting

| Token Type | Color | Examples |
|------------|-------|----------|
| Keywords | Cyan `#22d3ee` | `const`, `async`, `return`, `import` |
| Strings | Green `#86efac` | `'text'`, `"text"`, `` `text` `` |
| Functions | Amber `#fbbf24` | `functionName(` |
| Comments | Gray `#64748b` | `// comment` |
| Types | Violet `#c4b5fd` | `: Type`, `<Type>` |

### Example Usage

```tsx
import { CodeBlock } from '../components';

// Basic code block
<CodeBlock
  code={`const soul = new Advisor({
  name: 'Emily',
  persona: 'wellness guide'
});`}
  language="typescript"
  title="Soul Engine Core"
/>

// Compact mode for inline examples
<CodeBlock
  code={`npm install @aldea/soul-engine`}
  compact={true}
/>

// Without title
<CodeBlock
  code={`export default function handler(req, res) {
  return res.json({ status: 'ok' });
}`}
  language="typescript"
/>
```

### Styling Notes

- Background: `rgba(15, 23, 41, 0.9)`
- Title: Small dot + label above code
- Line height: 1.6
- Padding: 16px 20px

---

## ImageLightbox

Full-screen image viewer for screenshots and diagrams with zoom support.

### Props

```typescript
interface ImageLightboxProps {
  src: string;
  alt: string;
  caption?: string;
  className?: string;
  thumbnailClassName?: string;
}
```

### Example Usage

```tsx
import { ImageLightbox, ImageGallery } from '../components';

// Single image with lightbox
<ImageLightbox
  src="/images/screenshot.png"
  alt="Screenshot"
  caption="Optional caption text"
  className="rounded-lg overflow-hidden"
/>

// Gallery of multiple images
<ImageGallery
  images={[
    { src: '/img1.png', alt: 'Image 1', caption: 'First image' },
    { src: '/img2.png', alt: 'Image 2', caption: 'Second image' },
    { src: '/img3.png', alt: 'Image 3' },
  ]}
  columns={3}
  gap="md"
/>
```

### Features

- **Click to open**: Thumbnail expands to full-screen lightbox
- **Zoom toggle**: Click image or zoom button to enlarge
- **Caption support**: Optional caption shown below image
- **Keyboard/click to close**: Click backdrop or X button to close
- **Motion animations**: Smooth fade and scale transitions

---

## Common Patterns

### Info Box

```tsx
<div className="p-5 bg-canvas-700/40 border border-blueprint-grid/40 rounded">
  <h4 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-3">
    Section Title
  </h4>
  <ul className="space-y-2 text-sm text-text-secondary">
    <li className="flex items-start gap-2">
      <span className="w-1.5 h-1.5 mt-2 bg-blueprint-cyan/60 rounded-full flex-shrink-0" />
      <span>Item one</span>
    </li>
    <li className="flex items-start gap-2">
      <span className="w-1.5 h-1.5 mt-2 bg-blueprint-cyan/60 rounded-full flex-shrink-0" />
      <span>Item two</span>
    </li>
  </ul>
</div>
```

### Tech Label

```tsx
<span className="font-mono text-[10px] text-blueprint-cyan uppercase tracking-wider opacity-70">
  TECHNICAL LABEL
</span>
```

### Numbered Step Badge

```tsx
<span className="w-6 h-6 rounded-full bg-blueprint-cyan/10 border border-blueprint-cyan/40 flex items-center justify-center text-xs font-mono text-blueprint-cyan">
  01
</span>
```

### Gradient Divider

```tsx
<div className="h-px bg-gradient-to-r from-transparent via-blueprint-cyan/30 to-transparent" />
```

---

## Component Composition

### Metrics Grid Slide

```tsx
<SlideLayout chapter="01 — METRICS" slideNumber={3}>
  <div className="h-full flex flex-col px-16 pt-16 pb-10">
    <h2 className="font-display text-3xl text-text-primary mb-6">
      Evaluation Metrics
    </h2>
    <div className="grid grid-cols-3 gap-3 flex-1">
      <MetricCard number={1} title="Accuracy" description="Data correctness" />
      <MetricCard number={2} title="Speed" description="Response time" />
      <MetricCard number={3} title="Clarity" description="Message clarity" />
      <MetricCard number={4} title="Empathy" description="Emotional intelligence" />
      <MetricCard number={5} title="Safety" description="Harm prevention" />
      <MetricCard number={6} title="Consistency" description="Behavioral stability" />
    </div>
  </div>
</SlideLayout>
```

### Workflow Slide

```tsx
<SlideLayout chapter="02 — PROCESS" slideNumber={5}>
  <div className="h-full flex flex-col px-16 pt-20 pb-12">
    <h2 className="font-display text-3xl text-text-primary mb-8">
      Data Processing Pipeline
    </h2>
    <div className="flex-1 flex flex-col items-center justify-center">
      <FlowDiagram
        steps={[
          { label: 'Ingest', sublabel: 'Raw data' },
          { label: 'Transform', sublabel: 'Clean & normalize' },
          { label: 'Validate', sublabel: 'Quality checks' },
          { label: 'Store', sublabel: 'Database' }
        ]}
      />
      <div className="mt-8 grid grid-cols-3 gap-8 w-full max-w-4xl">
        {/* Info boxes */}
      </div>
    </div>
  </div>
</SlideLayout>
```

### Comparison Slide

```tsx
<SlideLayout chapter="03 — COMPARISON" slideNumber={10}>
  <div className="h-full flex flex-col px-16 pt-16 pb-10">
    <h2 className="font-display text-3xl text-text-primary mb-6">
      Feature Comparison
    </h2>
    <div className="flex-1 flex items-center justify-center">
      <ComparisonTable
        headers={['Feature', 'Option A', 'Option B', 'Option C']}
        rows={[
          { label: 'Speed', values: ['Fast', 'Medium', 'Slow'] },
          { label: 'Cost', values: ['$10', '$25', '$50'] },
          { label: 'Support', values: [true, true, false] }
        ]}
      />
    </div>
  </div>
</SlideLayout>
```

---

## SectionHeader

Centered icon with decorative gradient lines flanking it, plus a heading. Used at the top of content slides.

### Props

```typescript
interface SectionHeaderProps {
  icon: React.ComponentType<any>;  // Phosphor icon component
  color: string;                    // Chapter accent color
  children: React.ReactNode;        // Heading text
}
```

### Structure

```
        ─────── [icon] ───────
          Section Heading
```

### Example

```tsx
import { SectionHeader } from '../components';
import { Funnel } from '@phosphor-icons/react';

<SectionHeader icon={Funnel} color="#78350F">
  95% of AI Deployments Show No ROI
</SectionHeader>
```

---

## GradientCard

Rounded card with subtle gradient background, left accent bar, and optional icon container. The workhorse component for content grouping.

### Props

```typescript
interface GradientCardProps {
  color: string;                     // Accent color (border, gradient, icon bg)
  icon?: React.ComponentType<any>;   // Optional Phosphor icon
  children: React.ReactNode;
  className?: string;                // Additional classes (e.g., "flex-1")
}
```

### Structure

```
┌──────────────────────────────────┐
│▌ [icon]                          │
│▌  Card Title                     │
│▌  Card body text...              │
└──────────────────────────────────┘
```

### Example — Grid of distinct-colored cards

```tsx
<div className="grid grid-cols-3 gap-5 flex-1">
  <GradientCard color="#1E3A8A" icon={MagnifyingGlass}>
    <h3 className="text-xl font-semibold text-text-primary mb-2">Investigative</h3>
    <p className="text-text-secondary text-xs">Cross-reference thousands of documents.</p>
  </GradientCard>
  <GradientCard color="#059669" icon={BookOpen}>
    <h3 className="text-xl font-semibold text-text-primary mb-2">Archive</h3>
    <p className="text-text-secondary text-xs">Decades of content made searchable.</p>
  </GradientCard>
  <GradientCard color="#B45309" icon={ShieldWarning}>
    <h3 className="text-xl font-semibold text-text-primary mb-2">Fact-Check</h3>
    <p className="text-text-secondary text-xs">Verify claims against your archive.</p>
  </GradientCard>
</div>
```

### Gotchas

- In grids of 3+ cards, use **distinct colors** per card (see `design-system.md` > Card Color Strategy)
- Do NOT add `flex-1` to cards unless you want them to stretch vertically to fill remaining space

---

## StatsBar

In-flow stats footer displaying key metrics. Designed to sit at the bottom of a flex column.

### Props

```typescript
interface StatsBarProps {
  stats: { value: string; label: string; color: string }[];
}
```

### Structure

```
┌─────────────────────────────────────────┐
│   95%         52         5%             │
│  No ROI    Executives  Production       │
└─────────────────────────────────────────┘
```

### Example

```tsx
<div className="h-full flex flex-col px-20 pt-16 pb-10">
  <SectionHeader icon={Funnel} color={CH['04'].color}>Title</SectionHeader>
  <div className="flex-1">{/* Main content */}</div>
  <StatsBar stats={[
    { value: '95%', label: 'No ROI', color: '#92400E' },
    { value: '52', label: 'Executives', color: '#78350F' },
    { value: '5%', label: 'Production', color: '#059669' },
  ]} />
</div>
```

### Gotchas

- **CRITICAL**: Use `mt-auto` (in-flow). NEVER use `absolute bottom-0 left-0 right-0` — it extends beyond the card bounds.
- Match StatsBar stat colors to the corresponding GradientCard accent colors on the same slide.

---

## GlowBadge

Inline metric callout with glow shadow. Used for highlighting key numbers within body text or as standalone callouts.

### Props

```typescript
interface GlowBadgeProps {
  color: string;
  children: React.ReactNode;
  size?: 'sm' | 'md';  // 'sm' for inline, 'md' for standalone
}
```

### Example — Inline in body text

```tsx
<p className="text-text-secondary text-xs">
  Media & Telecom is <GlowBadge color="#78350F" size="sm">1 of 2</GlowBadge> sectors showing transformation.
</p>
```

### Example — Standalone callout

```tsx
<GlowBadge color="#92400E">95%</GlowBadge>
<span className="text-text-primary text-lg"> of enterprise AI pilots deliver zero return.</span>
```

### Gotchas

- **CRITICAL**: Use `size="sm"` for inline badges within body text. Default `size="md"` uses `text-base` (16px) which looks disproportionate inside `text-xs` (12px) body text.

---

## TOC Navigation Pattern

Interactive Table of Contents with clickable cards that scroll to target slides.

### Data Structure

```tsx
const descriptions: Record<string, { slides: string; firstSlide: number; desc: string }> = {
  '01': { slides: '3–4', firstSlide: 3, desc: 'Who is building AI' },
  '02': { slides: '5–6', firstSlide: 5, desc: 'Four key AI concepts' },
  // ...
};
```

### Click Handler

```tsx
onClick={() => {
  const slideEl = document.querySelectorAll('.slide')[info.firstSlide - 1];
  if (slideEl) slideEl.scrollIntoView({ behavior: 'smooth' });
}}
```

### Card Centering Pattern

Wrap the title in a flex container to vertically center within variable-height cards:

```tsx
<div className="flex-1 flex flex-col items-center justify-center">
  <h3 className="font-display text-xl font-semibold text-text-primary leading-tight">
    {label}
  </h3>
</div>
```
