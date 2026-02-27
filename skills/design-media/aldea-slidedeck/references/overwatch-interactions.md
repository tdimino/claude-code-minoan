# Overwatch Mode — Interaction Patterns

All interactions use `motion/react` (Framer Motion). Import from `"motion/react"`, NOT `"framer-motion"`.

## Animation Timing

| Constant | Value | Use |
|----------|-------|-----|
| Duration (slide) | 0.4s | slideUp, slideLeft entrance |
| Duration (short) | 0.3s | fade, scale entrance |
| Ease | `"easeOut"` | All entrance animations |
| Stagger default | 0.1s | Between staggered children |
| Stagger delay | 0.2s | Before first child appears |

## Entrance Animations (`AnimatedItem`)

Four preset variants:

| Variant | Start State | End State |
|---------|-------------|-----------|
| `fade` | `opacity: 0` | `opacity: 1` (0.3s) |
| `slideUp` | `opacity: 0, y: 20` | `opacity: 1, y: 0` (0.4s) |
| `slideLeft` | `opacity: 0, x: 30` | `opacity: 1, x: 0` (0.4s) |
| `scale` | `opacity: 0, scale: 0.9` | `opacity: 1, scale: 1` (0.3s) |

### Usage
```tsx
<StaggeredAnimation stagger={0.1} delay={0.2}>
  <AnimatedItem variant="slideUp">First item</AnimatedItem>
  <AnimatedItem variant="slideUp">Second item (appears 0.1s later)</AnimatedItem>
  <AnimatedItem variant="fade">Third item</AnimatedItem>
</StaggeredAnimation>
```

## Hover Effects

### HoverLift
Lifts element on hover with optional shadow.

| Lift | Y offset |
|------|----------|
| `sm` | -4px |
| `md` | -8px (default) |
| `lg` | -12px |

```tsx
<HoverLift lift="md" shadow>
  <div className="p-6 border">Card content</div>
</HoverLift>
```

### GlowBorder
Mouse-tracking radial gradient that follows cursor.

```tsx
<GlowBorder color="var(--color-orange)" radius={500} borderWidth={3}>
  <div className="p-6">Content with glowing border on hover</div>
</GlowBorder>
```

## Content Swap Patterns

### ExpandableCard
Click to expand with layout animation + click-outside to close.

```tsx
<ExpandableCard
  preview={<div>Card preview</div>}
  detail={<div>Expanded detail content</div>}
/>
```

### Accordion
Collapsible section with animated chevron.

```tsx
<Accordion trigger="Section Title" defaultOpen={false}>
  <p>Hidden content revealed on click</p>
</Accordion>
```

### TabGroup
Tabbed panels with animated transitions.

```tsx
<TabGroup items={[
  { label: "Tab 1", content: <div>Panel 1</div> },
  { label: "Tab 2", content: <div>Panel 2</div> },
]} />
```

## Indicators

### PulseIndicator
Pulsing dot with expanding ring — for "live" or "scanning" states.

```tsx
<PulseIndicator size={24} color="var(--color-orange)" />
```

### Skeleton
Loading placeholder with pulse animation.

```tsx
<Skeleton width={200} height={20} />
```

## Overlay Patterns

### RevealCaption
Hover to slide in a caption overlay from top or bottom.

```tsx
<RevealCaption caption="Image description" position="bottom">
  <img src="photo.jpg" />
</RevealCaption>
```

### Tooltip
Position-aware tooltip on hover.

```tsx
<Tooltip content="Helpful info" position="top">
  <span>Hover me</span>
</Tooltip>
```

## Auto-Cycling

### QuoteRotator
Auto-cycles through quotes with dot navigation.

```tsx
<QuoteRotator
  quotes={[
    { text: "First quote", attribution: "Author One" },
    { text: "Second quote", attribution: "Author Two" },
  ]}
  interval={5000}
/>
```

## Typewriter Effect

Character-by-character text reveal for CLI demos and terminal simulations. Uses the `useTypewriter` hook.

### useTypewriter Hook
```tsx
import { useTypewriter } from "../hooks/useTypewriter";

const { displayText, isComplete } = useTypewriter("npm install acme", 35, 500);
// speed: ms per character (default 35)
// delay: ms before typing starts (default 0)
```

### TerminalTyper Component
Full terminal chrome with sequential line typing:
```tsx
<TerminalTyper
  lines={[
    "acme init my-project",
    "✓ Project created",
    "acme deploy --prod",
  ]}
  typingSpeed={30}
  startDelay={800}
  prompt="$"
  onComplete={() => console.log("done")}
/>
```

### Blinking Cursor
CSS animation for terminal cursor:
```css
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
```

## SVG Path Animation

Animate SVG strokes using `pathLength` for connector lines, chart outlines, and drawing effects.

### pathLength Technique
```tsx
<motion.path
  d="M0,0 L100,0"
  stroke="var(--color-orange)"
  strokeWidth="2"
  initial={{ pathLength: 0, opacity: 0 }}
  animate={{ pathLength: 1, opacity: 1 }}
  transition={{ duration: 0.8, delay: 0.5 }}
/>
```

### Animated Dashed Lines
Combine `strokeDasharray` with offset animation for "traveling" dashes:
```tsx
<motion.line
  x1={0} y1={0} x2={200} y2={0}
  stroke="var(--color-border-light)"
  strokeWidth="1"
  strokeDasharray="6 4"
  initial={{ strokeDashoffset: 40 }}
  animate={{ strokeDashoffset: 0 }}
  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
/>
```

### SVG Radar Chart
Zero-dependency radar using polar coordinates and pathLength animation:
```tsx
<SVGRadarChart
  axes={[
    { label: "Speed", max: 10 },
    { label: "Quality", max: 10 },
    { label: "Coverage", max: 10 },
  ]}
  series={[{ values: [8, 6, 9], color: "var(--color-orange)" }]}
  size={200}
  delay={0.5}
/>
```

## Infinite Scroll / Marquee

Vertical ticker effect for live feeds, activity streams, or scrolling lists. Content is duplicated for seamless looping.

```tsx
<InfiniteScrollTicker speed={8} direction="up" height={300}>
  <div className="space-y-3">
    {items.map((item) => (
      <div key={item.id} className="p-3 border" style={{ borderColor: "var(--color-border-light)" }}>
        {item.text}
      </div>
    ))}
  </div>
</InfiniteScrollTicker>
```

Gradient masks at top and bottom fade content edges. Uses `motion.div` with `animate={{ y: ["0%", "-50%"] }}` and `repeat: Infinity`.

## Progress Bars

Animated horizontal fill for metrics, adoption rates, and scores.

```tsx
<ProgressBar
  value={72}
  max={100}
  color="var(--color-orange)"
  label="Adoption"
  animate={true}
  delay={0.3}
  height="6px"
/>
```

Uses Framer Motion width transition from 0 → target percentage. Optional label shows metric name + percentage.

## Content Auto-Cycling

Generalized auto-rotation for arbitrary content using the `useAutoCycle` hook.

### useAutoCycle Hook
```tsx
import { useAutoCycle } from "../hooks/useAutoCycle";

const [currentItem, index, setIndex] = useAutoCycle(items, 5000);
// items: array to cycle through
// interval: ms between advances
// setIndex: manual navigation
```

### ContentRotator Component
```tsx
<ContentRotator interval={5000} showDots={true} dotColor="var(--color-orange)">
  <div>First panel content</div>
  <div>Second panel content</div>
  <div>Third panel content</div>
</ContentRotator>
```

AnimatePresence mode="wait" cross-fades between children. Dot indicators allow manual navigation.

## Hover-to-Swap (Advanced)

Building on the basic Interactive Feature Grid (Template #4), advanced hover-swap patterns support complex detail panels with embedded diagrams, charts, and animations.

### Default State Pattern
Show an engaging default when nothing is hovered — animated text transformations, placeholder graphics, or intro content:
```tsx
<AnimatePresence mode="wait">
  <motion.div
    key={hoveredId ?? "default"}
    initial={{ opacity: 0, x: 10 }}
    animate={{ opacity: 1, x: 0 }}
    exit={{ opacity: 0, x: -10 }}
    transition={{ duration: 0.25 }}
  >
    {hoveredId ? <DetailPanel data={items.find(i => i.id === hoveredId)} /> : <DefaultPanel />}
  </motion.div>
</AnimatePresence>
```

### Complex Detail Panels
Each swap target can contain full interactive content — radar charts, timelines, progress bars, auto-cycling content:
```tsx
function DetailPanel({ data }) {
  return (
    <div className="p-8">
      <SubHeadline>{data.title}</SubHeadline>
      <SVGRadarChart axes={data.axes} series={data.series} size={180} />
      <ProgressBar value={data.score} label={data.metric} delay={0.2} />
      <ContentRotator interval={4000}>
        {data.rotatingContent.map((c, i) => <div key={i}>{c}</div>)}
      </ContentRotator>
    </div>
  );
}
```

### Social Proof Cards
Platform-styled testimonial cards for twitter/linkedin integrations:
```tsx
<SocialProofCard
  variant="twitter"
  author={{ name: "Jane Dev", handle: "janedev", avatar: "/avatars/jane.jpg", verified: true }}
  content={[
    { text: "This tool is " },
    { text: "incredible", bold: true },
    { text: " for code review." },
  ]}
  metrics={{ replies: 12, retweets: 45, likes: 312, views: 8400 }}
/>
```

## Spring Physics (Sidebar)

The sidebar uses spring animations for organic feel:
```tsx
transition={{ type: "spring", stiffness: 400, damping: 30, mass: 0.8 }}
```

Active slide indicator uses `layoutId` for smooth position transitions:
```tsx
<motion.div layoutId="nav-indicator" />
```
