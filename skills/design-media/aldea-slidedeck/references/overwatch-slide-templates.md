# Overwatch Mode — Slide Templates

Eight slide type templates for Overwatch Mode presentations. Each template shows the recommended component composition and mode (dark/white/orange).

## 1. Shader Cover (Dark)

Full-bleed WebGPU shader background with staggered title stack.

```tsx
import { SlideWrapper } from "../components/layout/SlideWrapper";
import { CenterLayout } from "../components/layout/CenterLayout";
import { StaggeredAnimation } from "../components/interactions/StaggeredAnimation";
import { AnimatedItem } from "../components/interactions/AnimatedItem";
import { WebGPUCanvas } from "../components/graphics/WebGPUCanvas";
import shaderCode from "../components/graphics/shaders/lava-nebula.wgsl?raw";

<SlideWrapper mode="dark" className="p-0">
  <WebGPUCanvas shaderCode={shaderCode} className="absolute inset-0 w-full h-full" />
  <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#0a0500]/30 to-[#0a0500]/80" />
  <CenterLayout className="relative z-10 px-[64px]">
    <StaggeredAnimation stagger={0.15} delay={0.3}>
      <AnimatedItem variant="slideUp">
        <p style={{ color: "var(--color-orange)" }}>CATEGORY LABEL</p>
      </AnimatedItem>
      <AnimatedItem variant="slideUp">
        <h1 className="text-[140px]">TITLE</h1>
      </AnimatedItem>
      <AnimatedItem variant="fade">
        <p className="text-[24px]">Subtitle text</p>
      </AnimatedItem>
    </StaggeredAnimation>
  </CenterLayout>
</SlideWrapper>
```

## 2. Social Proof + Grid (Dark)

Embedded quote/tweet on left, numbered problem cards on right with hover effects.

```tsx
<SlideWrapper mode="dark">
  <SplitLayout
    ratio="1:1"
    left={
      <StaggeredAnimation>
        <AnimatedItem variant="slideUp">
          {/* Quote or tweet embed */}
          <div className="p-6 border rounded" style={{ borderColor: "var(--color-border-light)" }}>
            <p className="text-[20px] italic">"Quote text here"</p>
            <p className="mt-4 text-[14px]" style={{ color: "var(--color-text-muted)" }}>— Author</p>
          </div>
        </AnimatedItem>
      </StaggeredAnimation>
    }
    right={
      <GridLayout columns={2} gap="md">
        {items.map((item, i) => (
          <HoverLift key={i} lift="sm">
            <div className="p-5 border" style={{ borderColor: "var(--color-border-light)" }}>
              <MonoLabel size="sm">{String(i + 1).padStart(2, "0")}</MonoLabel>
              <p className="mt-2">{item.text}</p>
            </div>
          </HoverLift>
        ))}
      </GridLayout>
    }
  />
</SlideWrapper>
```

## 3. Split: Text + Numbered List (White)

Left narrative column + right numbered items with orange border accent.

```tsx
<SlideWrapper mode="white">
  <SplitLayout
    ratio="2:3"
    left={
      <div>
        <Eyebrow>For Developers</Eyebrow>
        <SubHeadline className="mt-4">The Missing Layer</SubHeadline>
        <div className="mt-8 p-5" style={{ backgroundColor: "var(--color-bg-secondary)" }}>
          <MonoLabel size="sm" style={{ color: "var(--color-orange)" }}>THE RESULT</MonoLabel>
          <BodyText size="sm" className="mt-2">Callout detail text</BodyText>
        </div>
      </div>
    }
    right={
      <div className="space-y-6">
        {items.map((item, i) => (
          <div key={i} className="pl-5" style={{ borderLeft: "3px solid var(--color-orange)" }}>
            <p className="text-[18px] font-medium">{String(i + 1).padStart(2, "0")}. {item.title}</p>
            <BodyText size="sm">{item.description}</BodyText>
          </div>
        ))}
      </div>
    }
  />
</SlideWrapper>
```

## 4. Interactive Feature Grid (Dark)

Hover a feature card on the right to swap the detail panel on the left.

```tsx
<SlideWrapper mode="dark">
  <SplitLayout
    ratio="1:1"
    left={
      <AnimatePresence mode="wait">
        <motion.div key={hoveredFeature ?? "default"} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
          {hoveredFeature ? featureDetails[hoveredFeature] : <DefaultPanel />}
        </motion.div>
      </AnimatePresence>
    }
    right={
      <GridLayout columns={2} gap="sm">
        {features.map((f, i) => (
          <HoverLift key={i} lift="sm">
            <div
              onMouseEnter={() => setHoveredFeature(f.id)}
              onMouseLeave={() => setHoveredFeature(null)}
              className="p-5 border cursor-pointer"
              style={{ borderColor: "var(--color-border-light)" }}
            >
              <MonoLabel size="sm">{f.label}</MonoLabel>
              <BodyText size="sm" className="mt-2">{f.description}</BodyText>
            </div>
          </HoverLift>
        ))}
      </GridLayout>
    }
  />
</SlideWrapper>
```

## 5. Data Visualization Cards (Dark)

Three-column layout with animated inline graphics inside each card.

```tsx
<SlideWrapper mode="dark">
  <Eyebrow>Enterprise Scale</Eyebrow>
  <SubHeadline className="mt-4 mb-8">The Problem at Scale</SubHeadline>
  <GridLayout columns={3} gap="md" className="flex-1">
    <HoverLift lift="md">
      <div className="h-full p-6 border" style={{ borderColor: "var(--color-border-light)" }}>
        <MonoLabel size="sm">PR FLOOD</MonoLabel>
        {/* Animated content: infinite scroll, charts, etc. */}
      </div>
    </HoverLift>
    {/* ... repeat for each column */}
  </GridLayout>
</SlideWrapper>
```

## 6. Product Demo (Dark)

UI mockup on left + insight/feature cards on right.

```tsx
<SlideWrapper mode="dark">
  <SplitLayout
    ratio="3:2"
    left={
      <div className="p-6 rounded" style={{ backgroundColor: "var(--color-bg-secondary)" }}>
        {/* Scanner/dashboard UI mockup */}
        <div className="flex items-center gap-3 mb-4">
          <PulseIndicator size={16} color="var(--color-orange)" />
          <MonoLabel size="sm">SCANNING</MonoLabel>
        </div>
        {/* ... mockup content */}
      </div>
    }
    right={
      <div className="space-y-4">
        {insights.map((insight, i) => (
          <HoverLift key={i} lift="sm">
            <div className="p-4 border-l-4" style={{ borderColor: insight.color }}>
              <MonoLabel size="sm">{insight.type}</MonoLabel>
              <BodyText size="sm" className="mt-1">{insight.text}</BodyText>
            </div>
          </HoverLift>
        ))}
      </div>
    }
  />
</SlideWrapper>
```

## 7. Two-Column GTM (White)

Distribution + Moat columns with animated graphic elements.

```tsx
<SlideWrapper mode="white">
  <Eyebrow>Go to Market</Eyebrow>
  <Headline className="mt-2 mb-8 text-[72px]">How We Win</Headline>
  <SplitLayout
    ratio="1:1"
    gap="xl"
    left={
      <div>
        <SubHeadline className="text-[36px]">Distribution</SubHeadline>
        <NetworkGraph className="my-6 w-48 mx-auto" />
        {/* Numbered points with Tooltips */}
      </div>
    }
    right={
      <div>
        <SubHeadline className="text-[36px]">Moat</SubHeadline>
        {/* Stacked cards or features */}
      </div>
    }
  />
</SlideWrapper>
```

## 8. Full-Bleed Quote (Orange)

Quote on accent background for impact.

```tsx
<SlideWrapper mode="orange">
  <CenterLayout>
    <StaggeredAnimation stagger={0.2} delay={0.3}>
      <AnimatedItem variant="scale">
        <p
          className="text-[52px] leading-[1.2] uppercase max-w-[900px]"
          style={{ fontFamily: "var(--font-heading)" }}
        >
          &ldquo;Your impactful quote goes here.&rdquo;
        </p>
      </AnimatedItem>
      <AnimatedItem variant="fade">
        <p className="mt-6 text-[18px] tracking-[0.15em] uppercase" style={{ fontFamily: "var(--font-body)" }}>
          &mdash; Attribution
        </p>
      </AnimatedItem>
    </StaggeredAnimation>
  </CenterLayout>
</SlideWrapper>
```

## 9. CLI Product Demo (Dark)

Terminal typewriter animation with command grid and compatibility footer.

```tsx
import { SlideWrapper } from "../components/layout/SlideWrapper";
import { SplitLayout } from "../components/layout/SplitLayout";
import { GridLayout } from "../components/layout/GridLayout";
import { StaggeredAnimation } from "../components/interactions/StaggeredAnimation";
import { AnimatedItem } from "../components/interactions/AnimatedItem";
import { HoverLift } from "../components/interactions/HoverLift";
import { TerminalTyper } from "../components/interactions/TerminalTyper";

<SlideWrapper mode="dark">
  <SplitLayout
    ratio="3:2"
    left={
      <div>
        <Eyebrow>Product</Eyebrow>
        <SubHeadline className="mt-4 mb-8">Try It Now</SubHeadline>
        <TerminalTyper
          lines={[
            "npm install @acme/cli",
            "acme init my-project",
            "✓ Project scaffolded in 1.2s",
            "acme deploy --prod",
            "✓ Deployed to https://my-project.acme.dev",
          ]}
          typingSpeed={30}
          startDelay={800}
          prompt="$"
        />
      </div>
    }
    right={
      <div>
        <MonoLabel size="sm" className="mb-4">COMMANDS</MonoLabel>
        <GridLayout columns={2} gap="sm">
          {commands.map((cmd, i) => (
            <HoverLift key={i} lift="sm">
              <div className="p-4 border" style={{ borderColor: "var(--color-border-light)" }}>
                <MonoLabel size="sm" style={{ color: "var(--color-orange)" }}>{cmd.name}</MonoLabel>
                <BodyText size="sm" className="mt-1">{cmd.description}</BodyText>
              </div>
            </HoverLift>
          ))}
        </GridLayout>
        {/* Compatibility footer */}
        <div className="mt-6 flex gap-4">
          {platforms.map((p) => (
            <MonoLabel key={p} size="sm" style={{ color: "var(--color-text-muted)" }}>{p}</MonoLabel>
          ))}
        </div>
      </div>
    }
  />
</SlideWrapper>
```

## 10. Horizontal Timeline (Dark)

Roadmap with animated connectors, phase dots, and cards.

```tsx
import { SlideWrapper } from "../components/layout/SlideWrapper";
import { StaggeredAnimation } from "../components/interactions/StaggeredAnimation";
import { AnimatedItem } from "../components/interactions/AnimatedItem";
import { TimelineConnector } from "../components/interactions/TimelineConnector";

<SlideWrapper mode="dark">
  <StaggeredAnimation stagger={0.15} delay={0.2}>
    <AnimatedItem variant="fade">
      <Eyebrow>Roadmap</Eyebrow>
    </AnimatedItem>
    <AnimatedItem variant="slideUp">
      <Headline className="text-[72px] mt-2 mb-10">What's Next</Headline>
    </AnimatedItem>
  </StaggeredAnimation>

  <TimelineConnector
    phases={[
      { label: "Foundation", subtitle: "Q1 2026", description: "Core platform launch with CLI and GitHub integration.", status: "complete" },
      { label: "Scale", subtitle: "Q2 2026", description: "Enterprise features, SSO, team dashboards.", status: "current" },
      { label: "Intelligence", subtitle: "Q3 2026", description: "AI-powered insights and automated remediation.", status: "upcoming" },
      { label: "Platform", subtitle: "Q4 2026", description: "Marketplace, third-party integrations, SDK.", status: "upcoming" },
    ]}
  />
</SlideWrapper>
```

## 11. Three-Audience GTM (White)

Three-column white-mode slide, each column with unique animated graphic.

```tsx
import { SlideWrapper } from "../components/layout/SlideWrapper";
import { GridLayout } from "../components/layout/GridLayout";
import { StaggeredAnimation } from "../components/interactions/StaggeredAnimation";
import { AnimatedItem } from "../components/interactions/AnimatedItem";
import { HoverLift } from "../components/interactions/HoverLift";
import { ProgressBar } from "../components/interactions/ProgressBar";
import { PulseIndicator } from "../components/interactions/PulseIndicator";

<SlideWrapper mode="white">
  <Eyebrow>Go to Market</Eyebrow>
  <Headline className="text-[72px] mt-2 mb-10">Three Audiences</Headline>

  <GridLayout columns={3} gap="lg" className="flex-1">
    {audiences.map((aud, i) => (
      <HoverLift key={i} lift="md">
        <div className="h-full p-8 border rounded-lg" style={{ borderColor: "var(--color-border-light)" }}>
          <StaggeredAnimation stagger={0.1} delay={0.3 + i * 0.15}>
            <AnimatedItem variant="slideUp">
              <MonoLabel size="sm" style={{ color: "var(--color-orange)" }}>{aud.label}</MonoLabel>
              <SubHeadline className="text-[28px] mt-2">{aud.title}</SubHeadline>
            </AnimatedItem>

            {/* Unique animated graphic per column */}
            <AnimatedItem variant="fade">
              <div className="my-6">
                {aud.graphicType === "ring" && (
                  <PulseIndicator size={80} color="var(--color-orange)" />
                )}
                {aud.graphicType === "progress" && (
                  <div className="space-y-3">
                    {aud.metrics.map((m, j) => (
                      <ProgressBar key={j} value={m.value} label={m.label} delay={0.5 + j * 0.15} />
                    ))}
                  </div>
                )}
                {aud.graphicType === "checklist" && (
                  <div className="space-y-2">
                    {aud.items.map((item, j) => (
                      <AnimatedItem key={j} variant="slideUp">
                        <div className="flex items-center gap-2">
                          <span style={{ color: "var(--color-orange)" }}>✓</span>
                          <BodyText size="sm">{item}</BodyText>
                        </div>
                      </AnimatedItem>
                    ))}
                  </div>
                )}
              </div>
            </AnimatedItem>

            <AnimatedItem variant="fade">
              <BodyText size="sm">{aud.description}</BodyText>
            </AnimatedItem>
          </StaggeredAnimation>
        </div>
      </HoverLift>
    ))}
  </GridLayout>
</SlideWrapper>
```

## 12. Simple Card Grid (Dark)

Icon + title + divider + description cards with hover lift.

```tsx
import { SlideWrapper } from "../components/layout/SlideWrapper";
import { GridLayout } from "../components/layout/GridLayout";
import { StaggeredAnimation } from "../components/interactions/StaggeredAnimation";
import { AnimatedItem } from "../components/interactions/AnimatedItem";
import { HoverLift } from "../components/interactions/HoverLift";

<SlideWrapper mode="dark">
  <StaggeredAnimation stagger={0.15} delay={0.2}>
    <AnimatedItem variant="fade">
      <Eyebrow>Opportunities</Eyebrow>
    </AnimatedItem>
    <AnimatedItem variant="slideUp">
      <Headline className="text-[72px] mt-2 mb-10">Other Bets</Headline>
    </AnimatedItem>
  </StaggeredAnimation>

  <GridLayout columns={3} gap="md">
    {cards.map((card, i) => (
      <AnimatedItem key={i} variant="slideUp">
        <HoverLift lift="md">
          <div
            className="h-full p-6 border rounded-lg"
            style={{ borderColor: "var(--color-border-light)" }}
          >
            {/* Icon */}
            <div className="text-[36px] mb-4">{card.icon}</div>

            {/* Title */}
            <p
              className="text-[20px] uppercase"
              style={{ fontFamily: "var(--font-heading)", color: "var(--color-text-primary)" }}
            >
              {card.title}
            </p>

            {/* Divider */}
            <div
              className="w-8 h-[2px] my-4"
              style={{ backgroundColor: "var(--color-orange)" }}
            />

            {/* Description */}
            <BodyText size="sm" style={{ color: "var(--color-text-muted)" }}>
              {card.description}
            </BodyText>
          </div>
        </HoverLift>
      </AnimatedItem>
    ))}
  </GridLayout>
</SlideWrapper>
```

## 13. Section Divider (Dark)

Giant text at low opacity for section breaks.

```tsx
import { SlideWrapper } from "../components/layout/SlideWrapper";
import { CenterLayout } from "../components/layout/CenterLayout";
import { AnimatedItem } from "../components/interactions/AnimatedItem";

<SlideWrapper mode="dark">
  <CenterLayout>
    <AnimatedItem variant="scale">
      <p
        className="text-[120px] uppercase"
        style={{
          fontFamily: "var(--font-heading)",
          color: "var(--color-text-primary)",
          opacity: 0.15,
          letterSpacing: "0.05em",
        }}
      >
        APPENDIX
      </p>
    </AnimatedItem>
  </CenterLayout>
</SlideWrapper>
```

## 14. Interactive Vertical Explorer (Dark)

Vertical list on the left with hover-to-reveal detail panels on the right.

```tsx
import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { SlideWrapper } from "../components/layout/SlideWrapper";
import { SplitLayout } from "../components/layout/SplitLayout";
import { HoverLift } from "../components/interactions/HoverLift";
import { ProgressBar } from "../components/interactions/ProgressBar";
import { SVGRadarChart } from "../components/graphics/SVGRadarChart";

const [hovered, setHovered] = useState<string | null>(null);

<SlideWrapper mode="dark">
  <Eyebrow>Use Cases</Eyebrow>
  <SubHeadline className="mt-4 mb-8">Industry Verticals</SubHeadline>

  <SplitLayout
    ratio="2:3"
    left={
      <div className="space-y-3">
        {verticals.map((v) => (
          <HoverLift key={v.id} lift="sm">
            <div
              onMouseEnter={() => setHovered(v.id)}
              onMouseLeave={() => setHovered(null)}
              className="p-5 border cursor-pointer transition-colors"
              style={{
                borderColor: hovered === v.id ? "var(--color-orange)" : "var(--color-border-light)",
                backgroundColor: hovered === v.id ? "rgba(255, 110, 65, 0.06)" : "transparent",
              }}
            >
              <MonoLabel size="sm" style={{ color: "var(--color-orange)" }}>{v.label}</MonoLabel>
              <BodyText size="sm" className="mt-1">{v.summary}</BodyText>
            </div>
          </HoverLift>
        ))}
      </div>
    }
    right={
      <AnimatePresence mode="wait">
        <motion.div
          key={hovered ?? "default"}
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -10 }}
          transition={{ duration: 0.25 }}
          className="h-full"
        >
          {hovered ? (
            <div className="p-8 h-full border" style={{ borderColor: "var(--color-border-light)" }}>
              <SubHeadline className="text-[28px]">{verticals.find(v => v.id === hovered)!.title}</SubHeadline>

              {/* Detail content — mix of diagrams, charts, badges, progress bars */}
              <div className="mt-6 space-y-4">
                <SVGRadarChart
                  axes={[{ label: "Speed", max: 10 }, { label: "Scale", max: 10 }, { label: "Risk", max: 10 }]}
                  series={[{ values: [8, 6, 4], color: "var(--color-orange)" }]}
                  size={180}
                />
                <ProgressBar value={72} label="Adoption" delay={0.3} />
                {/* Compliance badges */}
                <div className="flex gap-2 mt-4">
                  {verticals.find(v => v.id === hovered)!.badges.map((b) => (
                    <span
                      key={b}
                      className="px-2 py-1 text-[11px] uppercase tracking-wider rounded"
                      style={{
                        fontFamily: "var(--font-mono)",
                        border: "1px solid var(--color-border-light)",
                        color: "var(--color-text-muted)",
                      }}
                    >
                      {b}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center" style={{ color: "var(--color-text-muted)" }}>
              <p className="text-[18px]" style={{ fontFamily: "var(--font-mono)" }}>Hover a vertical to explore</p>
            </div>
          )}
        </motion.div>
      </AnimatePresence>
    }
  />
</SlideWrapper>
```

---

## Mode Selection Guide

| Template | Recommended Mode |
|----------|-----------------|
| Shader Cover | `dark` |
| Social Proof + Grid | `dark` |
| Split: Text + List | `white` |
| Interactive Feature Grid | `dark` |
| Data Visualization | `dark` |
| Product Demo | `dark` |
| Two-Column GTM | `white` |
| Full-Bleed Quote | `orange` |
| CLI Product Demo | `dark` |
| Horizontal Timeline | `dark` |
| Three-Audience GTM | `white` |
| Simple Card Grid | `dark` |
| Section Divider | `dark` |
| Interactive Vertical Explorer | `dark` |

Most slides should be dark. Use white for text-heavy analytical slides and orange sparingly for emphasis.
