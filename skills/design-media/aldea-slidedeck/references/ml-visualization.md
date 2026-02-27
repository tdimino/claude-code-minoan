# ML Visualization Reference

Specialized components for AI/ML research presentations.

## Components

### AttentionHeatmap

Visualize transformer attention weights.

```tsx
import { AttentionHeatmap } from '../components';

const tokens = ['The', 'cat', 'sat', 'on', 'the', 'mat'];
const weights = [
  [0.8, 0.1, 0.05, 0.02, 0.02, 0.01],
  [0.2, 0.6, 0.1, 0.05, 0.03, 0.02],
  [0.1, 0.15, 0.5, 0.15, 0.05, 0.05],
  // ... rest of attention matrix
];

<AttentionHeatmap
  tokens={tokens}
  weights={weights}
  title="Self-Attention Layer 6"
  maxCellSize={40}
/>
```

**Props:**
- `tokens: string[]` - Input tokens
- `weights: number[][]` - 2D attention matrix (values 0-1)
- `title?: string` - Header label
- `maxCellSize?: number` - Maximum cell size in pixels (default: 40)

---

### AudioWaveform

Visualize audio signals for STT/TTS presentations.

```tsx
import { AudioWaveform, generateSampleWaveform } from '../components';

// Use sample data
const waveData = generateSampleWaveform(200);

<AudioWaveform
  data={waveData}
  width={600}
  height={120}
  label="Input Speech"
  timestamps={[
    { time: '25', label: 'Word 1' },
    { time: '60', label: 'Word 2' },
  ]}
/>
```

**Props:**
- `data: number[]` - Amplitude values (-1 to 1)
- `width?: number` - SVG width (default: 600)
- `height?: number` - SVG height (default: 120)
- `color?: string` - Waveform color (default: cyan)
- `showAxis?: boolean` - Show center axis (default: true)
- `label?: string` - Component label
- `timestamps?: { time: string, label: string }[]` - Marker annotations

---

### TrainingMetrics

Training loss and accuracy curves.

```tsx
import { TrainingMetrics, generateSampleTrainingData } from '../components';

// Sample data for demo
const trainingData = generateSampleTrainingData(50);

// Or use real data
const realData = [
  { epoch: 1, trainLoss: 2.3, valLoss: 2.5, trainAcc: 0.15, valAcc: 0.12, lr: 0.001 },
  { epoch: 2, trainLoss: 1.8, valLoss: 2.1, trainAcc: 0.35, valAcc: 0.28, lr: 0.001 },
  // ...
];

<TrainingMetrics
  data={realData}
  metrics={['loss', 'accuracy']}
  title="Training Progress"
  showBestEpoch={true}
/>
```

**Props:**
- `data: TrainingDataPoint[]` - Epoch-indexed training data
- `metrics?: ('loss' | 'accuracy' | 'learning_rate')[]` - Charts to show
- `height?: number` - Individual chart height (default: 280)
- `showBestEpoch?: boolean` - Mark best validation epoch (default: true)
- `title?: string` - Section header

**Data Shape:**
```typescript
interface TrainingDataPoint {
  epoch: number;
  trainLoss?: number;
  valLoss?: number;
  trainAcc?: number;
  valAcc?: number;
  lr?: number;
}
```

---

## Architecture Diagrams

For ML model architectures, use the `ArchitectureDiagram` component with domain-specific nodes:

```tsx
import { ArchitectureDiagram } from '../components';

const nodes = [
  { id: 'input', label: 'Input', sublabel: 'Audio', icon: '🎤', position: { x: 0, y: 100 } },
  { id: 'encoder', label: 'Encoder', sublabel: 'Transformer', icon: '🔄', position: { x: 200, y: 100 } },
  { id: 'decoder', label: 'Decoder', sublabel: 'Autoregressive', icon: '📝', position: { x: 400, y: 100 } },
  { id: 'output', label: 'Output', sublabel: 'Text', icon: '📄', position: { x: 600, y: 100 } },
];

const edges = [
  { source: 'input', target: 'encoder', label: 'Mel Spectrogram' },
  { source: 'encoder', target: 'decoder', label: 'Hidden States', animated: true },
  { source: 'decoder', target: 'output', label: 'Tokens' },
];

<ArchitectureDiagram
  nodes={nodes}
  edges={edges}
  height={300}
/>
```

---

## Mermaid for Quick Diagrams

For simpler architecture diagrams:

```tsx
import { MermaidDiagram } from '../components';

const transformerDiagram = `
graph LR
    A[Input] --> B[Embedding]
    B --> C[Encoder Stack]
    C --> D[Decoder Stack]
    D --> E[Output Layer]

    subgraph Encoder
        C --> |Self-Attention| C1[Multi-Head]
        C1 --> C2[FFN]
    end
`;

<MermaidDiagram chart={transformerDiagram} />
```

---

## Slide Layouts for ML

### Model Overview Slide

```tsx
<SlideLayout chapter="03 — ARCHITECTURE" slideNumber={12}>
  <div className="h-full flex flex-col px-16 pt-16 pb-10">
    <h2 className="font-display text-3xl text-text-primary mb-6">
      Model Architecture
    </h2>

    <div className="flex-1">
      <ArchitectureDiagram
        nodes={architectureNodes}
        edges={architectureEdges}
        height={350}
      />
    </div>

    <div className="grid grid-cols-4 gap-4 mt-6">
      <div className="text-center">
        <div className="font-display text-2xl text-blueprint-cyan">12</div>
        <div className="text-xs text-text-muted">Layers</div>
      </div>
      <div className="text-center">
        <div className="font-display text-2xl text-blueprint-cyan">768</div>
        <div className="text-xs text-text-muted">Hidden Dim</div>
      </div>
      <div className="text-center">
        <div className="font-display text-2xl text-blueprint-cyan">12</div>
        <div className="text-xs text-text-muted">Attention Heads</div>
      </div>
      <div className="text-center">
        <div className="font-display text-2xl text-blueprint-cyan">110M</div>
        <div className="text-xs text-text-muted">Parameters</div>
      </div>
    </div>
  </div>
</SlideLayout>
```

### Training Results Slide

```tsx
<SlideLayout chapter="04 — RESULTS" slideNumber={20}>
  <div className="h-full flex flex-col px-12 pt-14 pb-8">
    <h2 className="font-display text-3xl text-text-primary mb-4">
      Training Convergence
    </h2>

    <TrainingMetrics
      data={trainingHistory}
      metrics={['loss', 'accuracy']}
      height={220}
      showBestEpoch
    />

    <div className="mt-4 p-4 bg-canvas-700/40 border border-blueprint-grid/40 rounded">
      <div className="flex justify-between text-sm">
        <span className="text-text-muted">Best Epoch:</span>
        <span className="text-text-primary">42</span>
      </div>
      <div className="flex justify-between text-sm mt-2">
        <span className="text-text-muted">Val Accuracy:</span>
        <span className="text-blueprint-cyan">94.2%</span>
      </div>
    </div>
  </div>
</SlideLayout>
```

### STT/TTS Pipeline Slide

```tsx
<SlideLayout chapter="02 — PIPELINE" slideNumber={8}>
  <div className="h-full flex flex-col px-16 pt-16 pb-10">
    <h2 className="font-display text-3xl text-text-primary mb-6">
      Speech-to-Text Pipeline
    </h2>

    <div className="flex gap-8">
      <div className="flex-1">
        <AudioWaveform
          data={inputWaveform}
          label="Input Audio"
          height={100}
        />
      </div>

      <div className="flex items-center">
        <div className="w-12 h-px bg-blueprint-cyan" />
        <div className="w-0 h-0 border-t-4 border-b-4 border-l-8 border-transparent border-l-blueprint-cyan" />
      </div>

      <div className="flex-1">
        <AttentionHeatmap
          tokens={['The', 'quick', 'brown', 'fox']}
          weights={attentionWeights}
          title="Attention"
          maxCellSize={30}
        />
      </div>
    </div>

    <div className="mt-6 p-4 bg-canvas-700/40 border border-blueprint-grid/40 rounded font-mono text-sm">
      <span className="text-text-muted">Output: </span>
      <span className="text-text-primary">"The quick brown fox jumps over the lazy dog"</span>
    </div>
  </div>
</SlideLayout>
```

---

## Best Practices

1. **Attention Heatmaps**: Limit to ~10 tokens for readability
2. **Training Curves**: Show 30-100 epochs for clear trends
3. **Architecture Diagrams**: Use icons and sublabels for clarity
4. **Audio Waveforms**: 100-300 data points for smooth appearance

## Sample Data Generators

```tsx
import {
  generateSampleWaveform,
  generateSampleTrainingData,
} from '../components';

// Generate demo audio waveform
const waveform = generateSampleWaveform(200); // 200 points

// Generate demo training history
const history = generateSampleTrainingData(50); // 50 epochs
```
