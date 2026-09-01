# Overwatch Mode — Advanced Patterns (Reference Only)

These patterns were observed in production Overwatch decks but are too domain-specific to scaffold. Document them here so Claude can implement them inline when a deck requires them.

## Waterfall Trace Diagram

Horizontal timing bars showing sequential operations (API calls, build steps, request traces). Each bar has a start offset and duration. Error bars pulse red.

```tsx
// Each span: { label, startMs, durationMs, status: "ok" | "error" | "slow" }
{spans.map((span, i) => (
  <motion.div
    key={i}
    className="flex items-center gap-3 h-8"
    initial={{ opacity: 0, x: -20 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay: 0.3 + i * 0.08 }}
  >
    <span className="w-24 text-right text-[12px]" style={{ fontFamily: "var(--font-mono)", color: "var(--color-text-muted)" }}>
      {span.label}
    </span>
    <div className="flex-1 relative h-3">
      <motion.div
        className="absolute h-full rounded-sm"
        style={{
          left: `${(span.startMs / totalMs) * 100}%`,
          backgroundColor: span.status === "error" ? "#f87171" : span.status === "slow" ? "#fbbf24" : "var(--color-orange)",
        }}
        initial={{ width: 0 }}
        animate={{ width: `${(span.durationMs / totalMs) * 100}%` }}
        transition={{ delay: 0.5 + i * 0.08, duration: 0.4 }}
      />
    </div>
    <MonoLabel size="sm" style={{ color: "var(--color-text-muted)" }}>{span.durationMs}ms</MonoLabel>
  </motion.div>
))}
```

### Error Pulse Keyframes
```css
@keyframes errorPulse {
  0%, 100% { background-color: #f87171; }
  50% { background-color: #ef4444; box-shadow: 0 0 12px rgba(248, 113, 113, 0.6); }
}
```

## Horizontal Carousel

Horizontally scrolling content strip with gradient masks on left/right edges. For logo grids, partner displays, or feature highlights.

```tsx
<div className="relative overflow-hidden">
  {/* Left mask */}
  <div className="absolute inset-y-0 left-0 w-16 z-10 pointer-events-none"
    style={{ background: "linear-gradient(to right, var(--color-bg-primary), transparent)" }} />
  {/* Right mask */}
  <div className="absolute inset-y-0 right-0 w-16 z-10 pointer-events-none"
    style={{ background: "linear-gradient(to left, var(--color-bg-primary), transparent)" }} />

  <motion.div
    className="flex gap-6"
    animate={{ x: ["0%", "-50%"] }}
    transition={{ duration: 20, ease: "linear", repeat: Infinity }}
  >
    {/* Duplicate children for seamless loop */}
    {items.map((item, i) => <Card key={i} {...item} />)}
    {items.map((item, i) => <Card key={`dup-${i}`} {...item} />)}
  </motion.div>
</div>
```

## Compliance Badge

Inline badge for certifications, standards, or tags. Used in vertical explorer detail panels.

```tsx
<span
  className="inline-block px-2 py-1 text-[11px] uppercase tracking-[0.15em] rounded"
  style={{
    fontFamily: "var(--font-mono)",
    border: "1px solid var(--color-border-light)",
    color: "var(--color-text-muted)",
  }}
>
  SOC 2
</span>
```

For colored variants:
```tsx
style={{
  border: `1px solid ${badgeColor}`,
  color: badgeColor,
  backgroundColor: `${badgeColor}10`, // 6% opacity
}}
```

## Animated Strikethrough

Text transforms from one phrase to another via strikethrough animation. The old text gets a line drawn through it, then fades to new text.

```tsx
const [struck, setStruck] = useState(false);

useEffect(() => {
  const timer = setTimeout(() => setStruck(true), 2000);
  return () => clearTimeout(timer);
}, []);

<div className="relative inline-block">
  <AnimatePresence mode="wait">
    {!struck ? (
      <motion.span key="old" exit={{ opacity: 0 }} className="relative">
        Old phrase
        <motion.div
          className="absolute left-0 top-1/2 h-[2px] bg-red-400"
          initial={{ width: 0 }}
          animate={{ width: "100%" }}
          transition={{ delay: 1.5, duration: 0.4 }}
          onAnimationComplete={() => setStruck(true)}
        />
      </motion.span>
    ) : (
      <motion.span
        key="new"
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        style={{ color: "var(--color-orange)" }}
      >
        New phrase
      </motion.span>
    )}
  </AnimatePresence>
</div>
```

## Dual-Layer Shader

WebGPU shader rendered both behind and in front of text using `mix-blend-mode: screen`. Creates a "text embedded in shader" effect for cover slides.

```tsx
{/* Layer 1: Behind text */}
<WebGPUCanvas shaderCode={shaderCode} className="absolute inset-0 w-full h-full" />

{/* Gradient overlay for readability */}
<div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#0a0500]/30 to-[#0a0500]/80" />

{/* Text layer */}
<div className="relative z-10">
  <h1>Title</h1>
</div>

{/* Layer 2: In front of text with blend mode */}
<WebGPUCanvas
  shaderCode={shaderCode}
  className="absolute inset-0 w-full h-full pointer-events-none"
  style={{ mixBlendMode: "screen", opacity: 0.4 }}
/>
```

The front layer uses `pointer-events-none` so it doesn't block interaction. Opacity and blend mode can be tuned per shader.

## Conductor Ring Diagram

SVG orbit diagram with a central node and satellite nodes on circular paths. Animated with rotating dashed orbits. Domain-specific but shows the SVG orbit pattern.

```tsx
const orbitRadius = 80;
const nodes = [
  { label: "Node A", angle: 0 },
  { label: "Node B", angle: Math.PI / 2 },
  { label: "Node C", angle: Math.PI },
  { label: "Node D", angle: (3 * Math.PI) / 2 },
];

<svg width={200} height={200} viewBox="0 0 200 200">
  {/* Orbit ring */}
  <motion.circle
    cx={100} cy={100} r={orbitRadius}
    fill="none"
    stroke="var(--color-border-light)"
    strokeWidth="1"
    strokeDasharray="4 3"
    initial={{ strokeDashoffset: 28 }}
    animate={{ strokeDashoffset: 0 }}
    transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
  />

  {/* Center node */}
  <circle cx={100} cy={100} r={12} fill="var(--color-orange)" />

  {/* Satellite nodes */}
  {nodes.map((node, i) => {
    const x = 100 + orbitRadius * Math.cos(node.angle);
    const y = 100 + orbitRadius * Math.sin(node.angle);
    return (
      <motion.g key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.5 + i * 0.15 }}>
        <circle cx={x} cy={y} r={8} fill="var(--color-text-muted)" />
        <text x={x} y={y + 20} textAnchor="middle" fontSize="10" fill="var(--color-text-secondary)">
          {node.label}
        </text>
      </motion.g>
    );
  })}
</svg>
```
