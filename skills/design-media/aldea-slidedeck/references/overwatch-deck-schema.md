# Overwatch Mode — Data-Driven Deck Authoring

A YAML spec serves as Claude's brief for composing each slide. Claude reads the spec alongside `overwatch-slide-templates.md` to produce each slide `.tsx` file. This is not template codegen—it's structured input that Claude interprets with full creative latitude.

## Top-Level Schema

```yaml
meta:
  title: "Acme Corp Pitch Deck"
  author: "Jane Smith"
  password: ""             # empty = no auth, string = password gate
  date: "2026-03-01"

design:
  primaryColor: "#ff6e41"  # overrides --color-orange
  fontHeading: "Geist"     # optional override
  fontBody: "Inter"        # optional override

slides:
  - type: shader-cover
    id: "01-cover"
    mode: dark
    # ... type-specific fields
```

## Slide Type Schemas

### `shader-cover` (Template #1)

```yaml
- type: shader-cover
  id: "01-cover"
  mode: dark
  shader: "lava-nebula"    # shader name from shaders/ directory, or "custom"
  customShader: null       # path to .wgsl file if shader: "custom"
  dualLayer: false         # render shader both behind and in front of text
  eyebrow: "SERIES A"
  title: "ACME CORP"
  subtitle: "Intelligent Code Review for Engineering Teams"
```

### `social-proof-grid` (Template #2)

```yaml
- type: social-proof-grid
  id: "02-problem"
  mode: dark
  eyebrow: "The Problem"
  title: "Engineers Know"
  socialProof:
    variant: twitter       # twitter | linkedin | testimonial
    author:
      name: "Jane Dev"
      handle: "janedev"
      avatar: "/avatars/jane.jpg"  # optional
      verified: true
    content: "This is the quote text."
    # OR structured content:
    # content:
    #   - text: "This tool is "
    #   - text: "incredible"
    #     bold: true
    #   - text: " for code review."
    metrics:               # optional, twitter/linkedin only
      replies: 12
      retweets: 45
      likes: 312
      views: 8400
  cards:
    - title: "Too Many PRs"
      description: "Teams drown in review queues."
    - title: "No Standards"
      description: "Every reviewer has different expectations."
```

### `split-text-list` (Template #3)

```yaml
- type: split-text-list
  id: "03-individual"
  mode: white
  eyebrow: "For Developers"
  headline: "The Missing Layer"
  callout:
    label: "THE RESULT"
    text: "80% reduction in review cycle time"
  items:
    - title: "Automated Standards"
      description: "Enforce team conventions without manual review."
    - title: "Context-Aware Feedback"
      description: "Understands your codebase, not just syntax."
```

### `interactive-feature-grid` (Template #4)

```yaml
- type: interactive-feature-grid
  id: "04-solution"
  mode: dark
  eyebrow: "Solution"
  title: "How It Works"
  defaultPanel:
    type: text             # text | strikethrough | graphic
    content: "Hover a feature to explore"
    # For strikethrough: oldText + newText
  features:
    - id: "audit"
      label: "Code Audit"
      description: "Comprehensive review of every PR."
      detailPanel:
        type: radar-chart   # radar-chart | timeline | progress | rotator | custom
        # For radar-chart:
        axes:
          - { label: "Speed", max: 10 }
          - { label: "Coverage", max: 10 }
          - { label: "Accuracy", max: 10 }
        series:
          - { values: [8, 7, 9], color: "var(--color-orange)" }
    - id: "daily"
      label: "Daily Cycle"
      description: "Automated daily workflow."
      detailPanel:
        type: rotator
        interval: 4000
        items:
          - "Morning: PR triage"
          - "Midday: Deep reviews"
          - "Evening: Summary report"
```

### `data-visualization-cards` (Template #5)

```yaml
- type: data-visualization-cards
  id: "05-enterprise"
  mode: dark
  eyebrow: "Enterprise"
  title: "The Problem at Scale"
  columns:
    - label: "PR FLOOD"
      graphicType: infinite-scroll  # infinite-scroll | carousel | waterfall | progress | custom
      graphicConfig:
        speed: 6
        direction: "up"
      items:
        - "PR #4521 — Auth refactor"
        - "PR #4522 — DB migration"
    - label: "REVIEW QUALITY"
      graphicType: carousel
      items:
        - "Inconsistent feedback"
        - "Missed edge cases"
    - label: "TIME COST"
      graphicType: waterfall
      spans:
        - { label: "Open", startMs: 0, durationMs: 200, status: "ok" }
        - { label: "Review", startMs: 200, durationMs: 1400, status: "slow" }
        - { label: "Merge", startMs: 1600, durationMs: 100, status: "ok" }
```

### `product-demo` (Template #6)

```yaml
- type: product-demo
  id: "06-git-plugin"
  mode: dark
  eyebrow: "Product"
  title: "PR Scanner"
  mockup:
    type: scanner          # scanner | dashboard | terminal | custom
    items:
      - { name: "auth-refactor.ts", status: "analyzed" }
      - { name: "db-migration.sql", status: "scanning" }
      - { name: "api-routes.ts", status: "pending" }
  insights:
    - type: "CRITICAL"
      color: "#f87171"
      text: "SQL injection risk in query builder"
    - type: "WARNING"
      color: "#fbbf24"
      text: "Unused import on line 42"
    - type: "STYLE"
      color: "var(--color-orange)"
      text: "Consider extracting to helper"
```

### `two-column-gtm` (Template #7)

```yaml
- type: two-column-gtm
  id: "07-gtm"
  mode: white
  eyebrow: "Go to Market"
  title: "How We Win"
  leftColumn:
    subtitle: "Distribution"
    graphic: network-graph  # network-graph | custom-svg
    points:
      - "Open source CLI with 10K stars"
      - "VS Code extension marketplace"
  rightColumn:
    subtitle: "Moat"
    points:
      - "Proprietary codebase understanding"
      - "Fine-tuned models per team"
```

### `full-bleed-quote` (Template #8)

```yaml
- type: full-bleed-quote
  id: "08-quote"
  mode: orange
  quote: "Code review should make you better, not just correct."
  attribution: "CTO, Acme Corp"
```

### `cli-product-demo` (Template #9)

```yaml
- type: cli-product-demo
  id: "09-mvp"
  mode: dark
  eyebrow: "Product"
  title: "Try It Now"
  terminal:
    lines:
      - "npm install @acme/cli"
      - "acme init my-project"
      - "✓ Project scaffolded in 1.2s"
    typingSpeed: 30
    startDelay: 800
    prompt: "$"
  commands:
    - name: "acme init"
      description: "Scaffold a new project"
    - name: "acme scan"
      description: "Analyze your codebase"
  compatibility:           # optional footer
    - "macOS"
    - "Linux"
    - "WSL"
```

### `horizontal-timeline` (Template #10)

```yaml
- type: horizontal-timeline
  id: "10-timeline"
  mode: dark
  eyebrow: "Roadmap"
  title: "What's Next"
  phases:
    - label: "Foundation"
      subtitle: "Q1 2026"
      description: "Core platform launch."
      status: complete
    - label: "Scale"
      subtitle: "Q2 2026"
      description: "Enterprise features."
      status: current
    - label: "Intelligence"
      subtitle: "Q3 2026"
      description: "AI-powered insights."
      status: upcoming
```

### `three-audience-gtm` (Template #11)

```yaml
- type: three-audience-gtm
  id: "11-gtm"
  mode: white
  eyebrow: "Go to Market"
  title: "Three Audiences"
  audiences:
    - label: "DEVELOPERS"
      title: "Individual"
      graphicType: ring     # ring | progress | checklist
      description: "Free CLI tool drives adoption."
    - label: "TEAMS"
      title: "Team"
      graphicType: progress
      metrics:
        - { label: "Adoption", value: 72 }
        - { label: "Retention", value: 91 }
      description: "Team dashboard with shared rules."
    - label: "ENTERPRISE"
      title: "Organization"
      graphicType: checklist
      items:
        - "SSO integration"
        - "Audit logging"
        - "SLA guarantee"
      description: "Enterprise compliance and scale."
```

### `simple-card-grid` (Template #12)

```yaml
- type: simple-card-grid
  id: "12-other-bets"
  mode: dark
  eyebrow: "Opportunities"
  title: "Other Bets"
  columns: 3              # 2, 3, or 4
  cards:
    - icon: "🔍"
      title: "Code Search"
      description: "Semantic search across your entire codebase."
    - icon: "📊"
      title: "Metrics"
      description: "Engineering velocity dashboard."
    - icon: "🤖"
      title: "Auto-Fix"
      description: "One-click remediation for common issues."
```

### `section-divider` (Template #13)

```yaml
- type: section-divider
  id: "13-appendix"
  mode: dark
  text: "APPENDIX"
  fontSize: 120            # default 120
  opacity: 0.15            # default 0.15
```

### `interactive-vertical-explorer` (Template #14)

```yaml
- type: interactive-vertical-explorer
  id: "14-use-cases"
  mode: dark
  eyebrow: "Use Cases"
  title: "Industry Verticals"
  verticals:
    - id: "fintech"
      label: "FINTECH"
      summary: "Regulatory compliance automation"
      title: "Financial Services"
      detail:
        description: "Automated compliance checking for financial codebases."
        chart:             # optional radar chart
          axes:
            - { label: "Speed", max: 10 }
            - { label: "Compliance", max: 10 }
          series:
            - { values: [8, 9], color: "var(--color-orange)" }
        metrics:           # optional progress bars
          - { label: "Adoption", value: 72 }
        badges:            # optional compliance badges
          - "SOC 2"
          - "PCI DSS"
    - id: "healthcare"
      label: "HEALTHCARE"
      summary: "HIPAA-compliant code review"
      title: "Healthcare & Life Sciences"
      detail:
        description: "PHI detection and compliance enforcement."
        badges:
          - "HIPAA"
          - "HITRUST"
```

## Using the Spec

### For Claude (reading a spec)
1. Parse each slide entry
2. Look up the template code in `overwatch-slide-templates.md` by template number
3. Compose the slide `.tsx` file using scaffold components + the spec's content fields
4. Adjust layout, animations, and interactions based on the content volume and complexity

### For `init-deck-from-spec.mjs` (scaffolding)
The script reads the YAML and:
1. Copies `scaffold-overwatch/` to the target directory
2. Generates `config.ts` slide registry from spec entries
3. Creates empty slide files with correct naming (`{id}.tsx`)
4. Reports which components to import per slide type
5. Applies design overrides to `styles.css` if specified

Claude then fills in each slide file using the spec as its brief.

## Minimal Example

```yaml
meta:
  title: "Acme Pitch"
  author: "Jane"
  password: "demo"

slides:
  - type: shader-cover
    id: "01-cover"
    mode: dark
    shader: "lava-nebula"
    title: "ACME"
    subtitle: "Intelligent Code Review"

  - type: social-proof-grid
    id: "02-problem"
    mode: dark
    eyebrow: "The Problem"
    title: "Engineers Know"
    socialProof:
      variant: twitter
      author: { name: "Jane", handle: "jane" }
      content: "Code review takes forever."
    cards:
      - title: "Slow Reviews"
        description: "3-day average cycle time."

  - type: horizontal-timeline
    id: "03-roadmap"
    mode: dark
    eyebrow: "Roadmap"
    title: "What's Next"
    phases:
      - { label: "MVP", status: complete }
      - { label: "Scale", status: current }
      - { label: "Platform", status: upcoming }
```
