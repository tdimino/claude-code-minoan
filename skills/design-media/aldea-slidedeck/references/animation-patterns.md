# Animation Patterns

Guide to motion and animation components in Aldea slide decks.

## Library

Uses **Motion** (formerly Framer Motion) for declarative React animations.

```bash
npm install motion
```

## Components

### AnimatedSlide

Animate slide content on viewport entry.

```tsx
import { AnimatedSlide } from '../components';

<AnimatedSlide animation="slideUp" delay={0.2}>
  <h2>This content animates in</h2>
</AnimatedSlide>
```

**Animation Types:**
- `fade` - Simple opacity fade
- `slideUp` - Fade + slide from bottom
- `slideLeft` - Fade + slide from right
- `scale` - Fade + scale up
- `blur` - Fade with blur clear

**Props:**
- `animation?: AnimationType` - Animation style (default: 'fade')
- `delay?: number` - Delay in seconds (default: 0)
- `duration?: number` - Duration in seconds (default: 0.6)
- `className?: string` - Additional CSS classes

---

### AnimatedList

Stagger animations for list items.

```tsx
import { AnimatedList } from '../components';

<AnimatedList staggerDelay={0.1} initialDelay={0.3}>
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
</AnimatedList>
```

**Props:**
- `children: ReactNode[]` - Array of items to animate
- `staggerDelay?: number` - Delay between items (default: 0.1)
- `initialDelay?: number` - Initial delay before first item (default: 0)
- `className?: string` - Wrapper CSS classes

---

### AnimatedNumber

Counter animation for numeric values.

```tsx
import { AnimatedNumber } from '../components';

<div className="text-4xl font-display text-blueprint-cyan">
  <AnimatedNumber value={1234567} prefix="$" duration={2} />
</div>

<AnimatedNumber
  value={98.7}
  suffix="%"
  decimals={1}
  delay={0.5}
/>
```

**Props:**
- `value: number` - Target number
- `duration?: number` - Animation duration (default: 1.5)
- `delay?: number` - Start delay in seconds (default: 0)
- `prefix?: string` - Text before number (e.g., '$')
- `suffix?: string` - Text after number (e.g., '%')
- `decimals?: number` - Decimal places (default: 0)
- `className?: string` - Text styling

---

## Raw Motion Usage

For custom animations, use Motion directly:

```tsx
import { motion } from 'motion/react';

// Basic animation
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.5 }}
>
  Content
</motion.div>

// Viewport-triggered
<motion.div
  initial={{ opacity: 0 }}
  whileInView={{ opacity: 1 }}
  viewport={{ once: true }}
>
  Animates when scrolled into view
</motion.div>

// Hover effects
<motion.button
  whileHover={{ scale: 1.05 }}
  whileTap={{ scale: 0.95 }}
>
  Interactive Button
</motion.button>
```

## Animation Patterns

### Staggered Grid

```tsx
const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};

<motion.div
  className="grid grid-cols-3 gap-4"
  variants={container}
  initial="hidden"
  whileInView="show"
>
  {items.map((i) => (
    <motion.div key={i} variants={item}>
      Card {i}
    </motion.div>
  ))}
</motion.div>
```

### Orchestrated Reveal

```tsx
<AnimatedSlide animation="fade" delay={0}>
  <h1>Title appears first</h1>
</AnimatedSlide>

<AnimatedSlide animation="slideUp" delay={0.3}>
  <p>Subtitle follows</p>
</AnimatedSlide>

<AnimatedList staggerDelay={0.15} initialDelay={0.6}>
  <div>Point 1</div>
  <div>Point 2</div>
  <div>Point 3</div>
</AnimatedList>
```

### Chart Animation

Charts animate automatically with Recharts. For custom timing:

```tsx
<AnimatedSlide animation="fade" delay={0.2}>
  <ChartCard title="Performance">
    <MetricsChart data={data} lines={lines} />
  </ChartCard>
</AnimatedSlide>
```

## Timing Guidelines

| Element | Delay | Duration |
|---------|-------|----------|
| Title | 0s | 0.6s |
| Subtitle | 0.2s | 0.5s |
| First content block | 0.4s | 0.5s |
| List items | 0.1s stagger | 0.4s each |
| Charts | 0.3-0.5s | 0.6s |
| Secondary elements | 0.5-0.8s | 0.4s |

## Easing

Default easing: `[0.25, 0.4, 0.25, 1]` (smooth deceleration)

For different feels:
```tsx
// Bouncy
transition={{ ease: [0.34, 1.56, 0.64, 1] }}

// Snappy
transition={{ ease: [0.4, 0, 0.2, 1] }}

// Gentle
transition={{ ease: [0.25, 0.1, 0.25, 1] }}
```

## PDF Export Notes

- Animations complete before PDF capture
- All animated elements appear in final state
- No motion in exported PDF (static image)

For reliable PDF export, ensure animations don't depend on user interaction (hover, click).
