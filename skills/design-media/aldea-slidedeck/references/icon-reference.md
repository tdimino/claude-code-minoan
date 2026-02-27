# Icon Reference

Guide to icon libraries available in Aldea slide decks.

## Available Libraries

| Library | Icons | Best For | Import |
|---------|-------|----------|--------|
| **Lucide** | 1,500+ | General UI | `lucide-react` |
| **Tabler** | 5,900+ | Comprehensive | `@tabler/icons-react` |
| **Phosphor** | 7,000+ | Flexible weights | `@phosphor-icons/react` |

## Quick Start

```tsx
// Lucide (recommended for most uses)
import { Brain, Cpu, Database, ChartLine } from 'lucide-react';

// Tabler (largest collection)
import { IconBrain, IconCpu, IconDatabase } from '@tabler/icons-react';

// Phosphor (multiple weights)
import { Brain, Cpu } from '@phosphor-icons/react';
```

## Blueprint Styling

Apply consistent styling to match the slide deck theme:

```tsx
// Standard blueprint icon
<Brain className="w-6 h-6 text-blueprint-cyan" />

// Muted icon
<Database className="w-5 h-5 text-text-muted" />

// Icon in circle badge
<div className="w-10 h-10 rounded-full bg-blueprint-cyan/10 flex items-center justify-center">
  <Cpu className="w-5 h-5 text-blueprint-cyan" />
</div>

// Icon with glow effect
<Brain className="w-8 h-8 text-blueprint-cyan drop-shadow-[0_0_8px_rgba(0,212,255,0.5)]" />
```

## Recommended Icons by Domain

### AI/ML Research
```tsx
import {
  Brain,           // Neural networks, AI
  Cpu,             // Processing, compute
  Database,        // Data storage
  GitBranch,       // Version control, training
  Layers,          // Model layers
  Network,         // Architecture
  Sparkles,        // AI/Magic
  Workflow,        // Pipelines
  Mic,             // STT (Speech-to-Text)
  Volume2,         // TTS (Text-to-Speech)
  Waveform,        // Audio processing
} from 'lucide-react';
```

### Business & Finance
```tsx
import {
  TrendingUp,      // Growth
  DollarSign,      // Revenue
  PieChart,        // Analytics
  BarChart3,       // Metrics
  Target,          // Goals
  Users,           // Customers
  Building2,       // Enterprise
  Briefcase,       // Business
  CreditCard,      // Payments
  Wallet,          // Finance
} from 'lucide-react';
```

### Healthcare & Wellness
```tsx
import {
  Heart,           // Health
  Activity,        // Vitals
  Stethoscope,     // Medical
  Pill,            // Medication
  ClipboardList,   // Records
  ShieldCheck,     // Safety
  Smile,           // Wellbeing
  Moon,            // Sleep
  Sun,             // Energy
  Leaf,            // Natural/Organic
} from 'lucide-react';
```

### Spirituality & Coaching
```tsx
import {
  Compass,         // Direction
  Flame,           // Passion
  Mountain,        // Journey
  Sunrise,         // New beginnings
  Star,            // Aspiration
  Lightbulb,       // Insight
  BookOpen,        // Wisdom
  Feather,         // Lightness
  Infinity,        // Continuity
  Sparkle,         // Transformation
} from 'lucide-react';
```

### Parenting & Family
```tsx
import {
  Baby,            // Infant/child
  Users,           // Family unit
  Heart,           // Love/connection
  HandHeart,       // Care/nurturing
  MessageCircle,   // Communication
  Shield,          // Protection/safety
  Home,            // Family home
  Clock,           // Routines/schedules
  Brain,           // Development/cognition
  Smile,           // Emotional wellbeing
  BookOpen,        // Learning/education
  Puzzle,          // Problem-solving
  Target,          // Goals/milestones
  TrendingUp,      // Progress/growth
  Handshake,       // Partnership/collaboration
} from 'lucide-react';

// Phosphor extras for parenting
import {
  Heartbeat,       // Emotional regulation
  HandsClapping,   // Positive reinforcement
  Scales,          // Balance/boundaries
  Butterfly,       // Transformation
  Tree,            // Growth/roots
  SmileyWink,      // Playfulness
  Chats,           // Parent-child dialogue
} from '@phosphor-icons/react';
```

## Icon Sizes

| Context | Size | Class |
|---------|------|-------|
| Inline text | 16px | `w-4 h-4` |
| Standard | 20px | `w-5 h-5` |
| Medium | 24px | `w-6 h-6` |
| Large | 32px | `w-8 h-8` |
| Feature | 40px | `w-10 h-10` |
| Hero | 48-64px | `w-12 h-12` to `w-16 h-16` |

## Common Patterns

### Icon with Label
```tsx
<div className="flex items-center gap-2">
  <Brain className="w-5 h-5 text-blueprint-cyan" />
  <span className="text-text-primary">Neural Network</span>
</div>
```

### Icon Grid
```tsx
<div className="grid grid-cols-4 gap-4">
  {[Brain, Cpu, Database, Network].map((Icon, i) => (
    <div key={i} className="flex flex-col items-center gap-2">
      <div className="w-12 h-12 rounded-lg bg-canvas-700/60 border border-blueprint-grid/40 flex items-center justify-center">
        <Icon className="w-6 h-6 text-blueprint-cyan" />
      </div>
      <span className="font-mono text-xs text-text-muted">Label</span>
    </div>
  ))}
</div>
```

### Numbered Icon List
```tsx
<div className="space-y-3">
  {items.map((item, i) => (
    <div key={i} className="flex items-start gap-3">
      <div className="w-8 h-8 rounded-full bg-blueprint-cyan/10 flex items-center justify-center flex-shrink-0">
        <span className="font-mono text-sm text-blueprint-cyan">{i + 1}</span>
      </div>
      <div>
        <div className="flex items-center gap-2">
          <item.icon className="w-4 h-4 text-blueprint-cyan" />
          <span className="text-text-primary font-medium">{item.title}</span>
        </div>
        <p className="text-sm text-text-secondary mt-1">{item.description}</p>
      </div>
    </div>
  ))}
</div>
```

## Phosphor Weights

Phosphor icons support multiple weights for design flexibility:

```tsx
import { Brain } from '@phosphor-icons/react';

// Available weights: thin, light, regular, bold, fill, duotone
<Brain weight="thin" />
<Brain weight="regular" />
<Brain weight="bold" />
<Brain weight="fill" />
<Brain weight="duotone" />
```

## Finding Icons

- **Lucide**: https://lucide.dev/icons
- **Tabler**: https://tabler.io/icons
- **Phosphor**: https://phosphoricons.com
