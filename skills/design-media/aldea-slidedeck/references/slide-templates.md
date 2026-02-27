# Slide Templates

Eight reusable slide type templates for Aldea presentations.

---

## 1. Title Slide

Opening slide with logo, title, and subtitle.

### Structure

```
┌─────────────────────────────────────────────────┐
│                                                 │
│              [ALDEA LOGO - large]               │
│                                                 │
│         PROJECT TITLE / JOURNEY NAME            │
│         ─────────────────────────               │
│         Subtitle describing the presentation    │
│                                                 │
│              [Decorative element]               │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Template

```tsx
<SlideLayout slideNumber={1} showGrid={true} showCorners={true}>
  <div className="h-full flex flex-col items-center justify-center relative">
    {/* Large logo */}
    <div className="mb-8">
      <img
        src="/images/large-logo.png"
        alt="Aldea"
        className="h-16"
        style={{ filter: 'brightness(1.4) contrast(1.1)' }}
      />
    </div>

    {/* Title */}
    <h1 className="font-display text-6xl text-text-primary text-center mb-4">
      Project Title
    </h1>

    {/* Divider */}
    <div className="w-32 h-px bg-gradient-to-r from-transparent via-blueprint-cyan/50 to-transparent mb-4" />

    {/* Subtitle */}
    <p className="font-mono text-sm text-text-secondary tracking-wider text-center max-w-2xl">
      Subtitle describing the presentation scope and purpose
    </p>

    {/* Decorative footer */}
    <div className="absolute bottom-12 flex items-center gap-3">
      <div className="w-8 h-px bg-blueprint-grid" />
      <span className="font-mono text-xs text-text-muted uppercase tracking-widest">
        January 2026
      </span>
      <div className="w-8 h-px bg-blueprint-grid" />
    </div>
  </div>
</SlideLayout>
```

---

## 2. Table of Contents

Interactive chapter overview with expandable cards.

### Structure

```
┌─────────────────────────────────────────────────┐
│                 JOURNEY MAP                     │
│                                                 │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐               │
│  │ 01  │ │ 02  │ │ 03  │ │ 04  │               │
│  │     │ │     │ │     │ │     │               │
│  └─────┘ └─────┘ └─────┘ └─────┘               │
│                                                 │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐               │
│  │ 05  │ │ 06  │ │ 07  │ │ 08  │               │
│  │     │ │     │ │     │ │     │               │
│  └─────┘ └─────┘ └─────┘ └─────┘               │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Template

```tsx
const [expandedChapter, setExpandedChapter] = useState<string | null>(null);

const chapters = [
  { id: '01', title: 'Chapter One', slides: ['Slide 1', 'Slide 2'], gradient: 'rgba(239,68,68,0.10)', accent: '#f87171' },
  { id: '02', title: 'Chapter Two', slides: ['Slide 3', 'Slide 4'], gradient: 'rgba(251,146,60,0.10)', accent: '#fb923c' },
  // ... more chapters
];

<SlideLayout slideNumber={2} showGrid={true} showCorners={true}>
  <div className="h-full flex flex-col items-center justify-center px-20">
    <h2 className="font-display text-4xl text-text-primary mb-8">Journey Map</h2>

    <div className="grid grid-cols-4 gap-4 w-full max-w-5xl">
      {chapters.map((chapter) => (
        <div
          key={chapter.id}
          className="relative p-4 rounded-lg cursor-pointer transition-all duration-300"
          style={{ background: chapter.gradient }}
          onClick={() => setExpandedChapter(expandedChapter === chapter.id ? null : chapter.id)}
        >
          {/* Chapter badge */}
          <div
            className="absolute -top-2 -left-2 w-8 h-8 rounded-full flex items-center justify-center text-xs font-mono"
            style={{
              background: chapter.gradient,
              borderColor: `${chapter.accent}80`,
              boxShadow: `0 4px 12px ${chapter.accent}30`
            }}
          >
            {chapter.id}
          </div>

          <h3 className="font-medium text-sm text-text-primary mt-4 mb-2">
            {chapter.title}
          </h3>

          {/* Expandable slide list */}
          {expandedChapter === chapter.id && (
            <ul className="text-xs text-text-secondary space-y-1">
              {chapter.slides.map((slide, i) => (
                <li key={i}>{slide}</li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </div>
  </div>
</SlideLayout>
```

---

## 3. Metrics Grid

KPIs, evaluation criteria, or numbered feature lists.

### Structure

```
┌─────────────────────────────────────────────────┐
│ [Chapter]                                       │
│                                                 │
│         SLIDE TITLE                             │
│         Subtitle with context                   │
│                                                 │
│  ┌────────┐  ┌────────┐  ┌────────┐            │
│  │ 01     │  │ 02     │  │ 03     │            │
│  │ Title  │  │ Title  │  │ Title  │            │
│  │ Desc   │  │ Desc   │  │ Desc   │            │
│  └────────┘  └────────┘  └────────┘            │
│                                                 │
│  ┌────────┐  ┌────────┐  ┌────────┐            │
│  │ 04     │  │ 05     │  │ 06     │            │
│  │ Title  │  │ Title  │  │ Title  │            │
│  │ Desc   │  │ Desc   │  │ Desc   │            │
│  └────────┘  └────────┘  └────────┘            │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Template

```tsx
<SlideLayout chapter="01 — EVALUATION" slideNumber={3}>
  <div className="h-full flex flex-col px-16 pt-16 pb-10">
    {/* Header */}
    <div className="mb-6">
      <h2 className="font-display text-3xl text-text-primary">
        Evaluation Metrics
      </h2>
      <p className="text-text-secondary text-sm mt-2">
        Nine dimensions of advisor quality assessment
      </p>
    </div>

    {/* Metrics grid */}
    <div className="grid grid-cols-3 gap-3 flex-1">
      <MetricCard number={1} title="Response Quality" description="Accuracy and helpfulness" />
      <MetricCard number={2} title="Empathy" description="Emotional intelligence" />
      <MetricCard number={3} title="Domain Expertise" description="Subject knowledge" />
      <MetricCard number={4} title="Communication" description="Clarity and tone" />
      <MetricCard number={5} title="Safety" description="Harm prevention" />
      <MetricCard number={6} title="Consistency" description="Behavioral stability" />
      <MetricCard number={7} title="Engagement" description="Conversation flow" />
      <MetricCard number={8} title="Personalization" description="Context awareness" />
      <MetricCard number={9} title="Authenticity" description="Voice fidelity" />
    </div>
  </div>
</SlideLayout>
```

---

## 4. Workflow Diagram

Process flows with optional info boxes below.

### Structure

```
┌─────────────────────────────────────────────────┐
│ [Chapter]                                       │
│                                                 │
│         PROCESS TITLE                           │
│                                                 │
│    [Step 1] → [Step 2] → [Step 3] → [Step 4]   │
│                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Detail 1 │  │ Detail 2 │  │ Detail 3 │      │
│  │ • Item   │  │ • Item   │  │ • Item   │      │
│  │ • Item   │  │ • Item   │  │ • Item   │      │
│  └──────────┘  └──────────┘  └──────────┘      │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Template

```tsx
<SlideLayout chapter="02 — DATA PIPELINE" slideNumber={5}>
  <div className="h-full flex flex-col px-16 pt-20 pb-12">
    <h2 className="font-display text-3xl text-text-primary mb-8">
      Data Processing Pipeline
    </h2>

    {/* Flow diagram */}
    <div className="flex-1 flex flex-col">
      <div className="flex justify-center mb-8">
        <FlowDiagram
          steps={[
            { label: 'Ingest', sublabel: 'Raw data' },
            { label: 'Transform', sublabel: 'Clean' },
            { label: 'Validate', sublabel: 'QA' },
            { label: 'Store', sublabel: 'Database' }
          ]}
        />
      </div>

      {/* Info boxes */}
      <div className="grid grid-cols-3 gap-6 mt-auto">
        <div className="p-5 bg-canvas-700/40 border border-blueprint-grid/40 rounded">
          <h4 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-3">
            Input Sources
          </h4>
          <ul className="space-y-2 text-sm text-text-secondary">
            <li>• PDFs and documents</li>
            <li>• Audio transcripts</li>
            <li>• Video content</li>
          </ul>
        </div>

        <div className="p-5 bg-canvas-700/40 border border-blueprint-grid/40 rounded">
          <h4 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-3">
            Processing
          </h4>
          <ul className="space-y-2 text-sm text-text-secondary">
            <li>• OCR conversion</li>
            <li>• Chunking</li>
            <li>• Embedding</li>
          </ul>
        </div>

        <div className="p-5 bg-canvas-700/40 border border-blueprint-grid/40 rounded">
          <h4 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-3">
            Output
          </h4>
          <ul className="space-y-2 text-sm text-text-secondary">
            <li>• Training data</li>
            <li>• Vector store</li>
            <li>• Quality report</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</SlideLayout>
```

---

## 5. Technical Deep Dive

Code examples with description sidebar.

### Structure

```
┌─────────────────────────────────────────────────┐
│ [Chapter]                                       │
│                                                 │
│         TECHNICAL TITLE                         │
│                                                 │
│  ┌─────────────────────┐  ┌──────────────────┐ │
│  │ CODE BLOCK          │  │ Description      │ │
│  │                     │  │                  │ │
│  │ const example = {   │  │ • Key point 1   │ │
│  │   prop: 'value'     │  │ • Key point 2   │ │
│  │ };                  │  │ • Key point 3   │ │
│  │                     │  │                  │ │
│  └─────────────────────┘  └──────────────────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Template

```tsx
<SlideLayout chapter="03 — ARCHITECTURE" slideNumber={8}>
  <div className="h-full flex px-16 pt-20 pb-12 gap-8">
    {/* Code section */}
    <div className="flex-1">
      <h2 className="font-display text-3xl text-text-primary mb-6">
        Soul Engine Core
      </h2>
      <CodeBlock
        code={`const soul = new Advisor({
  name: 'Emily',
  persona: 'wellness guide',
  workingMemory: [],
  mentalProcess: 'engaged'
});

await soul.respond(userMessage);`}
        language="typescript"
        title="Advisor Initialization"
      />
    </div>

    {/* Description sidebar */}
    <div className="w-80">
      <div className="p-5 bg-canvas-700/40 border border-blueprint-grid/40 rounded">
        <h4 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-4">
          Key Concepts
        </h4>
        <ul className="space-y-3 text-sm text-text-secondary">
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 mt-2 bg-blueprint-cyan/60 rounded-full flex-shrink-0" />
            <span><strong className="text-text-primary">Persona</strong> — defines the advisor's identity and expertise</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 mt-2 bg-blueprint-cyan/60 rounded-full flex-shrink-0" />
            <span><strong className="text-text-primary">Working Memory</strong> — maintains conversation context</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 mt-2 bg-blueprint-cyan/60 rounded-full flex-shrink-0" />
            <span><strong className="text-text-primary">Mental Process</strong> — governs response behavior</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</SlideLayout>
```

---

## 6. Comparison View

Side-by-side or table-based feature comparison.

### Structure (Side-by-Side)

```
┌─────────────────────────────────────────────────┐
│ [Chapter]                                       │
│                                                 │
│         COMPARISON TITLE                        │
│                                                 │
│  ┌────────────────────┐  ┌────────────────────┐│
│  │ OPTION A           │  │ OPTION B           ││
│  │                    │  │                    ││
│  │ • Feature 1        │  │ • Feature 1        ││
│  │ • Feature 2        │  │ • Feature 2        ││
│  │ • Feature 3        │  │ • Feature 3        ││
│  │                    │  │                    ││
│  └────────────────────┘  └────────────────────┘│
│                                                 │
└─────────────────────────────────────────────────┘
```

### Template (Side-by-Side)

```tsx
<SlideLayout chapter="04 — COMPARISON" slideNumber={12}>
  <div className="h-full flex flex-col px-16 pt-16 pb-10">
    <h2 className="font-display text-3xl text-text-primary mb-8">
      Architecture Comparison
    </h2>

    <div className="flex-1 grid grid-cols-2 gap-8">
      {/* Option A */}
      <div className="p-6 bg-red-500/5 border border-red-500/20 rounded-lg">
        <h3 className="font-mono text-red-400 text-sm uppercase tracking-wider mb-4">
          Traditional Approach
        </h3>
        <ul className="space-y-3 text-sm text-text-secondary">
          <li>• Stateless request/response</li>
          <li>• No memory between sessions</li>
          <li>• Generic responses</li>
          <li>• Limited personalization</li>
        </ul>
      </div>

      {/* Option B */}
      <div className="p-6 bg-green-500/5 border border-green-500/20 rounded-lg">
        <h3 className="font-mono text-green-400 text-sm uppercase tracking-wider mb-4">
          Soul Engine
        </h3>
        <ul className="space-y-3 text-sm text-text-secondary">
          <li>• Persistent working memory</li>
          <li>• Cross-session context</li>
          <li>• Persona-driven responses</li>
          <li>• Deep personalization</li>
        </ul>
      </div>
    </div>
  </div>
</SlideLayout>
```

### Template (Table)

```tsx
<SlideLayout chapter="04 — COMPARISON" slideNumber={13}>
  <div className="h-full flex flex-col px-16 pt-16 pb-10">
    <h2 className="font-display text-3xl text-text-primary mb-6">
      Feature Comparison
    </h2>

    <div className="flex-1 flex items-center justify-center">
      <ComparisonTable
        headers={['Feature', 'Basic', 'Advanced', 'Enterprise']}
        rows={[
          { label: 'API Access', values: [true, true, true] },
          { label: 'Custom Personas', values: [false, true, true] },
          { label: 'Analytics', values: ['Basic', 'Detailed', 'Custom'] },
          { label: 'Support', values: ['Email', '24/7', 'Dedicated'] },
          { label: 'SLA', values: [false, '99.9%', '99.99%'] }
        ]}
      />
    </div>
  </div>
</SlideLayout>
```

---

## 7. Image Showcase

Screenshots, diagrams, or visualizations with lightbox.

### Structure

```
┌─────────────────────────────────────────────────┐
│ [Chapter]                                       │
│                                                 │
│         IMAGE TITLE                             │
│         Brief description                       │
│                                                 │
│  ┌─────────────────────────────────────────┐   │
│  │                                         │   │
│  │           [SCREENSHOT/DIAGRAM]          │   │
│  │                                         │   │
│  │                                         │   │
│  └─────────────────────────────────────────┘   │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Template

```tsx
const [lightboxOpen, setLightboxOpen] = useState(false);

<SlideLayout chapter="05 — DEMO" slideNumber={15}>
  <div className="h-full flex flex-col px-16 pt-16 pb-10">
    <div className="mb-4">
      <h2 className="font-display text-3xl text-text-primary">
        Soul Engine Debugger
      </h2>
      <p className="text-text-secondary text-sm mt-2">
        Real-time visualization of cognitive processes
      </p>
    </div>

    {/* Image container */}
    <div className="flex-1 flex items-center justify-center">
      <div className="relative">
        <img
          src="/images/debugger-ui.png"
          alt="Soul Engine Debugger UI"
          className="max-h-[400px] w-auto rounded-lg border border-blueprint-grid/40 cursor-pointer hover:opacity-90 transition-opacity"
          onClick={() => setLightboxOpen(true)}
        />
        <span className="absolute bottom-2 right-2 text-xs text-text-muted bg-canvas-900/80 px-2 py-1 rounded">
          Click to enlarge
        </span>
      </div>
    </div>
  </div>

  {/* Lightbox */}
  {lightboxOpen && (
    <div
      className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center cursor-pointer"
      onClick={() => setLightboxOpen(false)}
    >
      <img
        src="/images/debugger-ui.png"
        alt="Soul Engine Debugger UI"
        className="max-w-[95vw] max-h-[95vh] object-contain"
      />
    </div>
  )}
</SlideLayout>
```

---

## 8. Timeline

Chronological events or milestones.

### Structure

```
┌─────────────────────────────────────────────────┐
│ [Chapter]                                       │
│                                                 │
│         TIMELINE TITLE                          │
│                                                 │
│  ──●──────────●──────────●──────────●──────    │
│    │          │          │          │          │
│  Q1 2025   Q2 2025    Q3 2025    Q4 2025       │
│  Phase 1   Phase 2    Phase 3    Phase 4       │
│  Details   Details    Details    Details       │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Template

```tsx
const milestones = [
  { date: 'Q1 2025', title: 'Research', description: 'Initial exploration' },
  { date: 'Q2 2025', title: 'Prototype', description: 'First implementation' },
  { date: 'Q3 2025', title: 'Beta', description: 'Limited release' },
  { date: 'Q4 2025', title: 'Launch', description: 'General availability' }
];

<SlideLayout chapter="06 — ROADMAP" slideNumber={18}>
  <div className="h-full flex flex-col px-16 pt-16 pb-10">
    <h2 className="font-display text-3xl text-text-primary mb-8">
      Development Timeline
    </h2>

    <div className="flex-1 flex items-center justify-center">
      <div className="flex items-start gap-0 relative">
        {/* Timeline line */}
        <div className="absolute top-4 left-4 right-4 h-px bg-blueprint-grid" />

        {milestones.map((milestone, i) => (
          <div key={i} className="flex flex-col items-center w-48">
            {/* Dot */}
            <div className="w-3 h-3 rounded-full bg-blueprint-cyan relative z-10 mb-4" />

            {/* Content */}
            <div className="text-center">
              <span className="font-mono text-xs text-blueprint-cyan">
                {milestone.date}
              </span>
              <h4 className="font-medium text-sm text-text-primary mt-1">
                {milestone.title}
              </h4>
              <p className="text-xs text-text-secondary mt-1">
                {milestone.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  </div>
</SlideLayout>
```

---

## Choosing the Right Template

| Content Type | Template |
|--------------|----------|
| Introduction, opening | Title Slide |
| Navigation, overview | TOC |
| KPIs, evaluation criteria, features | Metrics Grid |
| Processes, pipelines, workflows | Workflow Diagram |
| Code examples, architecture | Technical Deep Dive |
| A vs B, feature matrices | Comparison View |
| Screenshots, diagrams | Image Showcase |
| Milestones, roadmaps | Timeline |
