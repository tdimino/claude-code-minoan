# Animated ASCII Art Components

Reference for generating frame-based ASCII animation React components. Based on analysis of ASCII Studio (github.com/vansh-nagar/ascii-studio, asciistudio.space).

## Concept

Unlike Pipeline 4's static image-to-ASCII conversion, animated ASCII components are pre-rendered frame sequences displayed in a React component with configurable FPS, color effects, and responsive scaling. Think of it as a flipbook made of character frames.

## Architecture

Each animated ASCII component consists of:

1. **Frame array** — array of multi-line strings, each representing one animation frame
2. **Animation loop** — `useEffect` + `setInterval` cycling through frames at target FPS
3. **APPEARANCE config** — visual rendering options (colors, text effects, character set)
4. **Responsive scaling** — `ResizeObserver` adjusting font size to fit container
5. **Interactive trigger** (optional) — hover/click to play special effects

### Component Structure

```tsx
"use client";
import { useState, useEffect, useRef, useCallback } from "react";

interface AnimationConfig {
  useColors: boolean;
  textEffectThreshold: number;
  textEffect: "video" | "gradient" | "burn";
}

const APPEARANCE: AnimationConfig = {
  useColors: true,
  textEffectThreshold: 0.6,
  textEffect: "video",
};

const CHARS = "·•●⬤";  // density ramp for visual weight
const FPS = 30;

const FRAMES: string[] = [
  // Each frame is a multi-line string of ASCII art
  `  frame 1 content  `,
  `  frame 2 content  `,
  // ...
];

export default function AsciiAnimation() {
  const [frameIndex, setFrameIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const interval = setInterval(() => {
      setFrameIndex(prev => (prev + 1) % FRAMES.length);
    }, 1000 / FPS);
    return () => clearInterval(interval);
  }, []);

  // ResizeObserver for responsive font scaling
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver(entries => {
      for (const entry of entries) {
        const width = entry.contentRect.width;
        const fontSize = Math.max(4, Math.min(12, width / 80));
        if (containerRef.current) {
          containerRef.current.style.fontSize = `${fontSize}px`;
        }
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div ref={containerRef} style={{ fontFamily: "monospace", whiteSpace: "pre", lineHeight: 1.2 }}>
      {FRAMES[frameIndex]}
    </div>
  );
}
```

## Available Animations (ASCII Studio Catalog)

Install via shadcn registry: `npx shadcn@latest add https://asciistudio.space/r/<name>.json`

| Name | Type | Lines | Description |
|------|------|-------|-------------|
| Lightning | Regular | ~300 | Animated lightning bolt |
| Skull | Regular | ~500 | Rotating skull |
| Pitstop | Regular | ~9000 | F1 pit stop scene |
| Red Fire | Regular | ~400 | Flame animation |
| CD Animation | Regular | ~200 | Spinning CD |
| Balls | Interactive | ~300 | Bouncing balls (hover to play) |
| Star | Interactive | ~250 | Spinning star (hover to play) |
| Rainbow Fire | Interactive | ~500 | Rainbow flame (hover to play) |
| Hand Fire | Interactive | ~400 | Hand with flame (hover to play) |
| Dust | Interactive | ~150 | Particle dust effect (hover to play) |

**Note**: ASCII Studio has no declared license. Reference the patterns and architecture, but do not vendor the frame data. Generate original frame content.

## Text Effects

Three rendering modes for visual variety:

**video** — Scanline effect. Random characters in CHARS set replace some positions each frame based on `textEffectThreshold`. Creates CRT/VHS noise.

**gradient** — Characters transition through the CHARS density ramp based on their position, creating a smooth brightness gradient across the frame.

**burn** — Edge-detection style. Characters at boundaries between filled and empty regions get brighter characters from CHARS, creating a glowing outline effect.

## Character Sets

| Name | Characters | Use |
|------|-----------|-----|
| Standard | ` .:-=+*#%@` | Classic density ramp, grayscale |
| Block | `·•●⬤` | Unicode circles, size-based density |
| Shade | `░▒▓█` | Unicode block shading |
| Braille | Unicode braille range | Ultra-high resolution (2x3 dots per cell) |
| Custom | User-defined | Match the aesthetic of the project |

## Generating New Animations

To create original animated ASCII art (not from ASCII Studio):

1. **Define the concept** — what's being animated (fire, loading bar, character walk, abstract pattern)
2. **Choose frame count** — 10-30 frames for simple loops, 60-120 for complex scenes
3. **Set canvas size** — typically 40-80 chars wide, 20-40 lines tall
4. **Generate frames** — each frame as a multi-line string with consistent dimensions
5. **Add variation** — use CHARS density ramp for visual weight, randomize edge pixels per frame
6. **Wrap in component** — use the template pattern above

For programmatic generation (algorithmic patterns, particles, waves), write a frame generator script rather than hand-crafting each frame.
