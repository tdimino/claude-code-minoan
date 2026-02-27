import React from 'react';
import { SlideLayout, MetricCard, FlowDiagram, ComparisonTable, CodeBlock } from '../components';

// ============================================================================
// ALDEA SLIDE DECK TEMPLATE
// ============================================================================
// This is a starter template for creating Aldea-branded slide decks.
// Customize the slides below to match your content.
//
// Structure:
// - Each slide is wrapped in <SlideLayout>
// - Slides are rendered vertically (scroll to navigate)
// - Export to PDF: npm run pdf (with dev server running)
// - Static export: npm run export
// ============================================================================

export default function Presentation() {
  return (
    <div>
      {/* ================================================================== */}
      {/* SLIDE 1: TITLE */}
      {/* ================================================================== */}
      <SlideLayout slideNumber={1} showGrid={true} showCorners={true}>
        <div className="h-full flex flex-col items-center justify-center relative">
          {/* Large logo */}
          <div className="mb-8">
            <img
              src="/images/aldea-logo.png"
              alt="Aldea"
              className="h-16"
              style={{ filter: 'brightness(1.4) contrast(1.1)' }}
            />
          </div>

          {/* Title */}
          <h1 className="font-display text-6xl text-text-primary text-center mb-4">
            Presentation Title
          </h1>

          {/* Divider */}
          <div className="w-32 h-px bg-gradient-to-r from-transparent via-blueprint-cyan/50 to-transparent mb-4" />

          {/* Subtitle */}
          <p className="font-mono text-sm text-text-secondary tracking-wider text-center max-w-2xl">
            Subtitle describing the presentation scope and purpose
          </p>

          {/* Decorative footer */}
          <div className="absolute bottom-12 flex items-center gap-3">
            <div className="w-8 h-px bg-blueprint-grid" />
            <span className="font-mono text-xs text-text-muted uppercase tracking-widest">
              January 2026
            </span>
            <div className="w-8 h-px bg-blueprint-grid" />
          </div>
        </div>
      </SlideLayout>

      {/* ================================================================== */}
      {/* SLIDE 2: METRICS EXAMPLE */}
      {/* ================================================================== */}
      <SlideLayout chapter="01 — EXAMPLE CHAPTER" slideNumber={2}>
        <div className="h-full flex flex-col px-16 pt-16 pb-10">
          <div className="mb-6">
            <h2 className="font-display text-3xl text-text-primary">
              Metrics Grid Example
            </h2>
            <p className="text-text-secondary text-sm mt-2">
              Use MetricCard components to display key points
            </p>
          </div>

          <div className="grid grid-cols-3 gap-3 flex-1">
            <MetricCard number={1} title="First Metric" description="Description of this metric" />
            <MetricCard number={2} title="Second Metric" description="Another description here" />
            <MetricCard number={3} title="Third Metric" description="And another one" />
            <MetricCard number={4} title="Fourth Metric" description="Keep adding as needed" />
            <MetricCard number={5} title="Fifth Metric" description="Up to 9 fits well in 3x3" />
            <MetricCard number={6} title="Sixth Metric" description="Last one in this grid" />
          </div>
        </div>
      </SlideLayout>

      {/* ================================================================== */}
      {/* SLIDE 3: WORKFLOW EXAMPLE */}
      {/* ================================================================== */}
      <SlideLayout chapter="02 — WORKFLOW" slideNumber={3}>
        <div className="h-full flex flex-col px-16 pt-20 pb-12">
          <h2 className="font-display text-3xl text-text-primary mb-8">
            Workflow Diagram Example
          </h2>

          <div className="flex-1 flex flex-col items-center justify-center">
            <FlowDiagram
              steps={[
                { label: 'Step One', sublabel: 'First action' },
                { label: 'Step Two', sublabel: 'Second action' },
                { label: 'Step Three', sublabel: 'Third action' },
                { label: 'Step Four', sublabel: 'Final action' }
              ]}
            />

            <div className="mt-8 grid grid-cols-3 gap-6 w-full max-w-4xl">
              <div className="p-5 bg-canvas-700/40 border border-blueprint-grid/40 rounded">
                <h4 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-3">
                  Info Box 1
                </h4>
                <ul className="space-y-2 text-sm text-text-secondary">
                  <li>• Detail one</li>
                  <li>• Detail two</li>
                </ul>
              </div>

              <div className="p-5 bg-canvas-700/40 border border-blueprint-grid/40 rounded">
                <h4 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-3">
                  Info Box 2
                </h4>
                <ul className="space-y-2 text-sm text-text-secondary">
                  <li>• Detail one</li>
                  <li>• Detail two</li>
                </ul>
              </div>

              <div className="p-5 bg-canvas-700/40 border border-blueprint-grid/40 rounded">
                <h4 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-3">
                  Info Box 3
                </h4>
                <ul className="space-y-2 text-sm text-text-secondary">
                  <li>• Detail one</li>
                  <li>• Detail two</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </SlideLayout>

      {/* ================================================================== */}
      {/* SLIDE 4: CODE EXAMPLE */}
      {/* ================================================================== */}
      <SlideLayout chapter="03 — TECHNICAL" slideNumber={4}>
        <div className="h-full flex px-16 pt-20 pb-12 gap-8">
          <div className="flex-1">
            <h2 className="font-display text-3xl text-text-primary mb-6">
              Code Block Example
            </h2>
            <CodeBlock
              code={`const example = {
  name: 'Aldea',
  type: 'presentation',
  slides: 37
};

async function process(data) {
  // Process the data
  return await transform(data);
}`}
              language="typescript"
              title="Example Code"
            />
          </div>

          <div className="w-80">
            <div className="p-5 bg-canvas-700/40 border border-blueprint-grid/40 rounded">
              <h4 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-4">
                Key Points
              </h4>
              <ul className="space-y-3 text-sm text-text-secondary">
                <li className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 mt-2 bg-blueprint-cyan/60 rounded-full flex-shrink-0" />
                  <span>First important point about this code</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 mt-2 bg-blueprint-cyan/60 rounded-full flex-shrink-0" />
                  <span>Second important point</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-1.5 h-1.5 mt-2 bg-blueprint-cyan/60 rounded-full flex-shrink-0" />
                  <span>Third important point</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </SlideLayout>

      {/* ================================================================== */}
      {/* SLIDE 5: COMPARISON EXAMPLE */}
      {/* ================================================================== */}
      <SlideLayout chapter="04 — COMPARISON" slideNumber={5}>
        <div className="h-full flex flex-col px-16 pt-16 pb-10">
          <h2 className="font-display text-3xl text-text-primary mb-6">
            Comparison Table Example
          </h2>

          <div className="flex-1 flex items-center justify-center">
            <ComparisonTable
              headers={['Feature', 'Option A', 'Option B', 'Option C']}
              rows={[
                { label: 'Feature One', values: [true, true, false] },
                { label: 'Feature Two', values: [true, false, true] },
                { label: 'Feature Three', values: ['Basic', 'Advanced', 'Custom'] },
                { label: 'Feature Four', values: [false, true, true] },
                { label: 'Pricing', values: ['$10', '$25', '$50'] }
              ]}
            />
          </div>
        </div>
      </SlideLayout>

      {/* ================================================================== */}
      {/* ADD MORE SLIDES BELOW */}
      {/* ================================================================== */}
      {/* Copy and customize the slide templates above to create your deck */}

    </div>
  );
}
