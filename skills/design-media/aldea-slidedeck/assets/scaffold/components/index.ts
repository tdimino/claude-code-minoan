// Core slide components
export { SlideLayout } from './SlideLayout';
export { MetricCard } from './MetricCard';
export { FlowDiagram } from './FlowDiagram';
export { ComparisonTable } from './ComparisonTable';
export { CodeBlock } from './CodeBlock';
export { ImageLightbox, ImageGallery } from './ImageLightbox';

// Layout & decoration primitives (battle-tested from SubQ deck)
export { SectionHeader } from './SectionHeader';
export { GradientCard } from './GradientCard';
export { StatsBar } from './StatsBar';
export { GlowBadge } from './GlowBadge';

// Charts (Recharts-based)
export { ChartCard, MetricsChart, ComparisonChart, RadarChart } from './charts';

// Animations (Motion/Framer Motion)
export { AnimatedSlide, AnimatedList, AnimatedNumber } from './animations';

// Diagrams (React Flow, Mermaid)
export { ArchitectureDiagram, MermaidDiagram } from './diagrams';
export type { ArchitectureNode, ArchitectureEdge } from './diagrams';

// ML Visualization
export { AttentionHeatmap, AudioWaveform, TrainingMetrics } from './ml';
export { generateSampleWaveform, generateSampleTrainingData } from './ml';
