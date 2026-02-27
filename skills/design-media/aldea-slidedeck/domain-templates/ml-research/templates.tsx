/**
 * AI/ML Research Slide Templates
 *
 * Specialized templates for Aldea Lab presentations on:
 * - STT/TTS systems
 * - Post-Transformers LLM architecture
 * - Training metrics and benchmarks
 * - Model architecture diagrams
 */

import React from 'react';
import {
  SlideLayout,
  ChartCard,
  MetricsChart,
  ComparisonChart,
  RadarChart,
  ArchitectureDiagram,
  MermaidDiagram,
  AttentionHeatmap,
  AudioWaveform,
  TrainingMetrics,
  AnimatedSlide,
  AnimatedNumber,
  generateSampleWaveform,
  generateSampleTrainingData,
} from '../../assets/scaffold/components';
import { Brain, Cpu, Layers, Mic, Volume2, GitBranch, Zap } from 'lucide-react';

// ============================================================================
// MODEL ARCHITECTURE SLIDE
// ============================================================================
export function ModelArchitectureSlide({ slideNumber }: { slideNumber: number }) {
  const nodes = [
    { id: 'input', label: 'Input', sublabel: 'Tokens', icon: '📥', position: { x: 50, y: 150 } },
    { id: 'embed', label: 'Embedding', sublabel: 'd=768', icon: '🔢', position: { x: 200, y: 150 } },
    { id: 'encoder', label: 'Encoder', sublabel: '12 layers', icon: '🔄', position: { x: 400, y: 100 } },
    { id: 'decoder', label: 'Decoder', sublabel: '12 layers', icon: '📝', position: { x: 400, y: 200 } },
    { id: 'head', label: 'LM Head', sublabel: 'Vocab', icon: '🎯', position: { x: 600, y: 150 } },
    { id: 'output', label: 'Output', sublabel: 'Logits', icon: '📤', position: { x: 750, y: 150 } },
  ];

  const edges = [
    { source: 'input', target: 'embed' },
    { source: 'embed', target: 'encoder', animated: true },
    { source: 'embed', target: 'decoder', animated: true },
    { source: 'encoder', target: 'decoder', label: 'Cross-Attn' },
    { source: 'decoder', target: 'head' },
    { source: 'head', target: 'output' },
  ];

  return (
    <SlideLayout chapter="ARCHITECTURE" slideNumber={slideNumber}>
      <div className="h-full flex flex-col px-12 pt-14 pb-8">
        <h2 className="font-display text-3xl text-text-primary mb-2">
          Model Architecture
        </h2>
        <p className="text-text-secondary text-sm mb-6">
          Aldea Foundation Model — Encoder-Decoder Transformer
        </p>

        <div className="flex-1">
          <ArchitectureDiagram nodes={nodes} edges={edges} height={300} />
        </div>

        <div className="grid grid-cols-5 gap-4 mt-6">
          <div className="text-center p-3 bg-canvas-700/40 rounded-lg border border-blueprint-grid/40">
            <div className="font-display text-xl text-blueprint-cyan">12</div>
            <div className="text-xs text-text-muted">Encoder Layers</div>
          </div>
          <div className="text-center p-3 bg-canvas-700/40 rounded-lg border border-blueprint-grid/40">
            <div className="font-display text-xl text-blueprint-cyan">12</div>
            <div className="text-xs text-text-muted">Decoder Layers</div>
          </div>
          <div className="text-center p-3 bg-canvas-700/40 rounded-lg border border-blueprint-grid/40">
            <div className="font-display text-xl text-blueprint-cyan">768</div>
            <div className="text-xs text-text-muted">Hidden Dim</div>
          </div>
          <div className="text-center p-3 bg-canvas-700/40 rounded-lg border border-blueprint-grid/40">
            <div className="font-display text-xl text-blueprint-cyan">12</div>
            <div className="text-xs text-text-muted">Attention Heads</div>
          </div>
          <div className="text-center p-3 bg-canvas-700/40 rounded-lg border border-blueprint-grid/40">
            <div className="font-display text-xl text-blueprint-cyan">125M</div>
            <div className="text-xs text-text-muted">Parameters</div>
          </div>
        </div>
      </div>
    </SlideLayout>
  );
}

// ============================================================================
// TRAINING PROGRESS SLIDE
// ============================================================================
export function TrainingProgressSlide({ slideNumber }: { slideNumber: number }) {
  const trainingData = generateSampleTrainingData(50);

  return (
    <SlideLayout chapter="TRAINING" slideNumber={slideNumber}>
      <div className="h-full flex flex-col px-12 pt-14 pb-8">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className="font-display text-3xl text-text-primary">
              Training Convergence
            </h2>
            <p className="text-text-secondary text-sm mt-1">
              50 epochs, batch size 32, AdamW optimizer
            </p>
          </div>
          <div className="flex gap-4">
            <div className="text-right">
              <div className="font-mono text-xs text-text-muted">Best Val Loss</div>
              <div className="font-display text-lg text-green-400">0.142</div>
            </div>
            <div className="text-right">
              <div className="font-mono text-xs text-text-muted">Best Accuracy</div>
              <div className="font-display text-lg text-green-400">94.2%</div>
            </div>
          </div>
        </div>

        <TrainingMetrics
          data={trainingData}
          metrics={['loss', 'accuracy']}
          height={240}
          showBestEpoch
        />
      </div>
    </SlideLayout>
  );
}

// ============================================================================
// STT/TTS PIPELINE SLIDE
// ============================================================================
export function SpeechPipelineSlide({ slideNumber }: { slideNumber: number }) {
  const waveformData = generateSampleWaveform(150);

  return (
    <SlideLayout chapter="SPEECH SYSTEMS" slideNumber={slideNumber}>
      <div className="h-full flex flex-col px-12 pt-14 pb-8">
        <h2 className="font-display text-3xl text-text-primary mb-6">
          Speech-to-Text Pipeline
        </h2>

        <div className="flex gap-6 mb-6">
          {/* Input Stage */}
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-3">
              <Mic className="w-5 h-5 text-blueprint-cyan" />
              <span className="font-mono text-xs text-text-muted uppercase">Input Audio</span>
            </div>
            <div className="bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg p-4">
              <AudioWaveform data={waveformData} width={300} height={80} />
            </div>
          </div>

          {/* Arrow */}
          <div className="flex items-center">
            <Zap className="w-6 h-6 text-blueprint-cyan" />
          </div>

          {/* Processing Stage */}
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-3">
              <Brain className="w-5 h-5 text-blueprint-cyan" />
              <span className="font-mono text-xs text-text-muted uppercase">Processing</span>
            </div>
            <div className="bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg p-4 h-[112px] flex items-center justify-center">
              <MermaidDiagram
                chart={`graph LR
                  A[Mel Spec] --> B[Encoder]
                  B --> C[Decoder]
                  C --> D[Tokens]`}
                className="scale-75"
              />
            </div>
          </div>

          {/* Arrow */}
          <div className="flex items-center">
            <Zap className="w-6 h-6 text-blueprint-cyan" />
          </div>

          {/* Output Stage */}
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-3">
              <Volume2 className="w-5 h-5 text-blueprint-cyan" />
              <span className="font-mono text-xs text-text-muted uppercase">Output Text</span>
            </div>
            <div className="bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg p-4 h-[112px]">
              <p className="font-mono text-sm text-text-primary leading-relaxed">
                "The quick brown fox jumps over the lazy dog near the riverbank."
              </p>
              <div className="flex gap-2 mt-3">
                <span className="px-2 py-0.5 bg-blueprint-cyan/20 text-blueprint-cyan text-xs rounded">WER: 2.3%</span>
                <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded">Latency: 45ms</span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-4 gap-4 mt-auto">
          <div className="p-4 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg">
            <div className="font-mono text-xs text-text-muted mb-1">Sample Rate</div>
            <div className="font-display text-lg text-text-primary">16kHz</div>
          </div>
          <div className="p-4 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg">
            <div className="font-mono text-xs text-text-muted mb-1">Mel Bins</div>
            <div className="font-display text-lg text-text-primary">80</div>
          </div>
          <div className="p-4 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg">
            <div className="font-mono text-xs text-text-muted mb-1">Vocab Size</div>
            <div className="font-display text-lg text-text-primary">32K</div>
          </div>
          <div className="p-4 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg">
            <div className="font-mono text-xs text-text-muted mb-1">Real-time Factor</div>
            <div className="font-display text-lg text-text-primary">0.12x</div>
          </div>
        </div>
      </div>
    </SlideLayout>
  );
}

// ============================================================================
// ATTENTION VISUALIZATION SLIDE
// ============================================================================
export function AttentionVisualizationSlide({ slideNumber }: { slideNumber: number }) {
  const tokens = ['The', 'model', 'learns', 'to', 'attend'];
  const weights = [
    [0.85, 0.05, 0.04, 0.03, 0.03],
    [0.10, 0.70, 0.10, 0.05, 0.05],
    [0.05, 0.15, 0.60, 0.10, 0.10],
    [0.08, 0.08, 0.14, 0.55, 0.15],
    [0.05, 0.10, 0.15, 0.20, 0.50],
  ];

  return (
    <SlideLayout chapter="INTERPRETABILITY" slideNumber={slideNumber}>
      <div className="h-full flex px-12 pt-14 pb-8 gap-8">
        <div className="flex-1">
          <h2 className="font-display text-3xl text-text-primary mb-2">
            Attention Patterns
          </h2>
          <p className="text-text-secondary text-sm mb-6">
            Self-attention visualization — Layer 6, Head 3
          </p>

          <div className="flex justify-center">
            <AttentionHeatmap
              tokens={tokens}
              weights={weights}
              title="Self-Attention Weights"
              maxCellSize={50}
            />
          </div>
        </div>

        <div className="w-72 flex flex-col gap-4">
          <div className="p-5 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg">
            <h4 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-4">
              Observations
            </h4>
            <ul className="space-y-3 text-sm text-text-secondary">
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 mt-2 bg-blueprint-cyan/60 rounded-full flex-shrink-0" />
                Strong diagonal pattern indicates positional awareness
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 mt-2 bg-blueprint-cyan/60 rounded-full flex-shrink-0" />
                "learns" attends broadly to context
              </li>
              <li className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 mt-2 bg-blueprint-cyan/60 rounded-full flex-shrink-0" />
                First token captures global context
              </li>
            </ul>
          </div>

          <div className="p-5 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg flex-1">
            <h4 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-4">
              Layer Analysis
            </h4>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-text-secondary">Entropy</span>
                <span className="font-mono text-text-primary">1.42</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-text-secondary">Sparsity</span>
                <span className="font-mono text-text-primary">0.68</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-text-secondary">Head Type</span>
                <span className="font-mono text-blueprint-cyan">Positional</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </SlideLayout>
  );
}

// ============================================================================
// BENCHMARK COMPARISON SLIDE
// ============================================================================
export function BenchmarkComparisonSlide({ slideNumber }: { slideNumber: number }) {
  const benchmarkData = [
    { name: 'GLUE', ours: 89.2, baseline: 82.1, sota: 91.3 },
    { name: 'SQuAD', ours: 91.5, baseline: 85.4, sota: 93.2 },
    { name: 'MNLI', ours: 87.8, baseline: 79.6, sota: 90.5 },
    { name: 'SST-2', ours: 94.1, baseline: 88.3, sota: 96.4 },
  ];

  return (
    <SlideLayout chapter="BENCHMARKS" slideNumber={slideNumber}>
      <div className="h-full flex flex-col px-12 pt-14 pb-8">
        <h2 className="font-display text-3xl text-text-primary mb-2">
          Benchmark Performance
        </h2>
        <p className="text-text-secondary text-sm mb-6">
          Comparison against baseline and state-of-the-art models
        </p>

        <div className="flex-1">
          <ChartCard>
            <ComparisonChart
              data={benchmarkData}
              bars={[
                { key: 'baseline', color: '#6b7a8c', name: 'Baseline' },
                { key: 'ours', color: '#00d4ff', name: 'Ours' },
                { key: 'sota', color: '#34d399', name: 'SOTA' },
              ]}
              height={280}
            />
          </ChartCard>
        </div>

        <div className="grid grid-cols-4 gap-4 mt-6">
          <div className="p-4 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg text-center">
            <div className="font-display text-2xl text-blueprint-cyan">+7.1</div>
            <div className="text-xs text-text-muted mt-1">Avg. vs Baseline</div>
          </div>
          <div className="p-4 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg text-center">
            <div className="font-display text-2xl text-text-primary">-2.1</div>
            <div className="text-xs text-text-muted mt-1">Avg. vs SOTA</div>
          </div>
          <div className="p-4 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg text-center">
            <div className="font-display text-2xl text-green-400">0.4x</div>
            <div className="text-xs text-text-muted mt-1">Compute Cost</div>
          </div>
          <div className="p-4 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg text-center">
            <div className="font-display text-2xl text-green-400">2.1x</div>
            <div className="text-xs text-text-muted mt-1">Inference Speed</div>
          </div>
        </div>
      </div>
    </SlideLayout>
  );
}

// ============================================================================
// POST-TRANSFORMER ARCHITECTURE SLIDE
// ============================================================================
export function PostTransformerSlide({ slideNumber }: { slideNumber: number }) {
  return (
    <SlideLayout chapter="NEXT-GEN ARCHITECTURE" slideNumber={slideNumber}>
      <div className="h-full flex flex-col px-12 pt-14 pb-8">
        <h2 className="font-display text-3xl text-text-primary mb-2">
          Beyond Transformers
        </h2>
        <p className="text-text-secondary text-sm mb-6">
          Aldea's post-Transformer architecture innovations
        </p>

        <div className="flex-1 flex gap-8">
          {/* Architecture comparison */}
          <div className="flex-1">
            <MermaidDiagram
              chart={`graph TB
                subgraph Traditional["Traditional Transformer"]
                  A1[Self-Attention O(n²)] --> B1[FFN]
                  B1 --> C1[LayerNorm]
                end

                subgraph Aldea["Aldea Architecture"]
                  A2[Linear Attention O(n)] --> B2[Gated MLP]
                  B2 --> C2[RMSNorm]
                  C2 --> D2[State Space]
                end`}
            />
          </div>

          {/* Key innovations */}
          <div className="w-80 flex flex-col gap-4">
            <div className="p-5 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg">
              <h4 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-4">
                Key Innovations
              </h4>
              <ul className="space-y-3 text-sm">
                <li className="flex items-start gap-2 text-text-secondary">
                  <Zap className="w-4 h-4 text-blueprint-cyan mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-text-primary">Linear Attention</span>
                    <p className="text-xs mt-0.5">O(n) complexity vs O(n²)</p>
                  </div>
                </li>
                <li className="flex items-start gap-2 text-text-secondary">
                  <Layers className="w-4 h-4 text-blueprint-cyan mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-text-primary">State Space Layers</span>
                    <p className="text-xs mt-0.5">Efficient sequence modeling</p>
                  </div>
                </li>
                <li className="flex items-start gap-2 text-text-secondary">
                  <Cpu className="w-4 h-4 text-blueprint-cyan mt-0.5 flex-shrink-0" />
                  <div>
                    <span className="text-text-primary">Hardware-Optimized</span>
                    <p className="text-xs mt-0.5">Custom CUDA kernels</p>
                  </div>
                </li>
              </ul>
            </div>

            <div className="p-5 bg-green-900/20 border border-green-500/30 rounded-lg">
              <h4 className="font-mono text-green-400 text-xs uppercase tracking-wider mb-3">
                Performance Gains
              </h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-text-secondary">Context Length</span>
                  <span className="text-green-400 font-medium">128K+</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-text-secondary">Training Speed</span>
                  <span className="text-green-400 font-medium">+3.2x</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-text-secondary">Memory Usage</span>
                  <span className="text-green-400 font-medium">-60%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </SlideLayout>
  );
}
