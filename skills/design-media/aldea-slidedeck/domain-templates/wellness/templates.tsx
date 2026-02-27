/**
 * Wellness, Spirituality & Life Coaching Slide Templates
 *
 * Copy these templates into your pages/index.tsx
 */

import React from 'react';
import {
  SlideLayout,
  FlowDiagram,
  AnimatedSlide,
  AnimatedList,
} from '../../assets/scaffold/components';
import { Compass, Flame, Mountain, Sunrise, Star, Heart, Sparkles } from 'lucide-react';

// ============================================================================
// TRANSFORMATION JOURNEY SLIDE
// ============================================================================
export function TransformationJourneySlide({ slideNumber }: { slideNumber: number }) {
  const stages = [
    { icon: Sunrise, label: 'Awakening', description: 'Recognize the need for change' },
    { icon: Compass, label: 'Discovery', description: 'Explore your inner landscape' },
    { icon: Mountain, label: 'Challenge', description: 'Face and overcome obstacles' },
    { icon: Flame, label: 'Integration', description: 'Embody your new self' },
    { icon: Star, label: 'Radiance', description: 'Share your light with others' },
  ];

  return (
    <SlideLayout chapter="THE JOURNEY" slideNumber={slideNumber}>
      <div className="h-full flex flex-col px-16 pt-16 pb-10">
        <AnimatedSlide animation="fade">
          <h2 className="font-display text-4xl text-text-primary text-center mb-2">
            The Path of Transformation
          </h2>
          <p className="text-text-secondary text-center text-lg mb-12">
            Five stages to lasting personal growth
          </p>
        </AnimatedSlide>

        <div className="flex-1 flex items-center justify-center">
          <div className="flex items-center gap-4">
            {stages.map((stage, index) => (
              <React.Fragment key={index}>
                <AnimatedSlide animation="scale" delay={0.15 * index}>
                  <div className="flex flex-col items-center w-40">
                    <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blueprint-cyan/20 to-purple-500/20 border border-blueprint-cyan/40 flex items-center justify-center mb-4">
                      <stage.icon className="w-10 h-10 text-blueprint-cyan" />
                    </div>
                    <div className="font-display text-lg text-text-primary mb-1">
                      {stage.label}
                    </div>
                    <div className="text-xs text-text-secondary text-center">
                      {stage.description}
                    </div>
                  </div>
                </AnimatedSlide>
                {index < stages.length - 1 && (
                  <div className="w-12 h-px bg-gradient-to-r from-blueprint-cyan/60 to-purple-500/40" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>
    </SlideLayout>
  );
}

// ============================================================================
// WISDOM QUOTE SLIDE
// ============================================================================
export function WisdomQuoteSlide({ slideNumber }: { slideNumber: number }) {
  return (
    <SlideLayout slideNumber={slideNumber} showGrid={true}>
      <div className="h-full flex flex-col items-center justify-center px-20">
        <AnimatedSlide animation="fade">
          <Sparkles className="w-12 h-12 text-blueprint-cyan/60 mx-auto mb-8" />
        </AnimatedSlide>

        <AnimatedSlide animation="slideUp" delay={0.2}>
          <blockquote className="text-center max-w-3xl">
            <p className="font-display text-4xl text-text-primary leading-relaxed mb-8">
              "The wound is the place where the Light enters you."
            </p>
            <footer className="font-mono text-sm text-text-secondary tracking-wider">
              — RUMI
            </footer>
          </blockquote>
        </AnimatedSlide>

        <AnimatedSlide animation="fade" delay={0.5}>
          <div className="w-24 h-px bg-gradient-to-r from-transparent via-blueprint-cyan/50 to-transparent mt-12" />
        </AnimatedSlide>
      </div>
    </SlideLayout>
  );
}

// ============================================================================
// BEFORE/AFTER TRANSFORMATION SLIDE
// ============================================================================
export function BeforeAfterSlide({ slideNumber }: { slideNumber: number }) {
  const beforeItems = [
    'Reactive responses',
    'External validation seeking',
    'Fear-based decisions',
    'Limited self-awareness',
    'Unconscious patterns',
  ];

  const afterItems = [
    'Conscious responses',
    'Internal validation',
    'Love-based choices',
    'Deep self-understanding',
    'Intentional living',
  ];

  return (
    <SlideLayout chapter="TRANSFORMATION" slideNumber={slideNumber}>
      <div className="h-full flex flex-col px-16 pt-16 pb-10">
        <AnimatedSlide animation="slideUp">
          <h2 className="font-display text-3xl text-text-primary text-center mb-12">
            The Shift in Consciousness
          </h2>
        </AnimatedSlide>

        <div className="flex-1 grid grid-cols-2 gap-8">
          {/* Before */}
          <AnimatedSlide animation="slideLeft" delay={0.2}>
            <div className="h-full bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-full bg-orange-500/20 flex items-center justify-center">
                  <div className="w-3 h-3 bg-orange-500 rounded-full" />
                </div>
                <h3 className="font-display text-xl text-text-primary">Before</h3>
              </div>
              <ul className="space-y-4">
                {beforeItems.map((item, i) => (
                  <li key={i} className="flex items-center gap-3 text-text-secondary">
                    <span className="w-2 h-2 bg-orange-500/50 rounded-full" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </AnimatedSlide>

          {/* After */}
          <AnimatedSlide animation="slideLeft" delay={0.4}>
            <div className="h-full bg-blueprint-cyan/5 border border-blueprint-cyan/30 rounded-lg p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-full bg-blueprint-cyan/20 flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-blueprint-cyan" />
                </div>
                <h3 className="font-display text-xl text-text-primary">After</h3>
              </div>
              <ul className="space-y-4">
                {afterItems.map((item, i) => (
                  <li key={i} className="flex items-center gap-3 text-text-secondary">
                    <span className="w-2 h-2 bg-blueprint-cyan/70 rounded-full" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </AnimatedSlide>
        </div>

        <AnimatedSlide animation="fade" delay={0.6}>
          <div className="text-center mt-8">
            <p className="text-text-muted italic">
              "Every moment is an opportunity to choose again"
            </p>
          </div>
        </AnimatedSlide>
      </div>
    </SlideLayout>
  );
}

// ============================================================================
// PILLARS OF GROWTH SLIDE
// ============================================================================
export function PillarsOfGrowthSlide({ slideNumber }: { slideNumber: number }) {
  const pillars = [
    {
      icon: Heart,
      title: 'Self-Compassion',
      description: 'Treat yourself with the kindness you would offer a dear friend',
    },
    {
      icon: Compass,
      title: 'Purpose',
      description: 'Align your actions with your deepest values and calling',
    },
    {
      icon: Mountain,
      title: 'Resilience',
      description: 'Develop the strength to navigate life\'s inevitable challenges',
    },
    {
      icon: Star,
      title: 'Connection',
      description: 'Cultivate meaningful relationships and community bonds',
    },
  ];

  return (
    <SlideLayout chapter="FOUNDATIONS" slideNumber={slideNumber}>
      <div className="h-full flex flex-col px-16 pt-16 pb-10">
        <AnimatedSlide animation="slideUp">
          <h2 className="font-display text-3xl text-text-primary text-center mb-4">
            Four Pillars of Conscious Growth
          </h2>
          <p className="text-text-secondary text-center mb-10">
            The foundation for lasting transformation
          </p>
        </AnimatedSlide>

        <div className="flex-1 grid grid-cols-4 gap-6">
          <AnimatedList staggerDelay={0.15} initialDelay={0.3}>
            {pillars.map((pillar) => (
              <div
                key={pillar.title}
                className="bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg p-6 flex flex-col items-center text-center"
              >
                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blueprint-cyan/20 to-purple-500/10 border border-blueprint-cyan/30 flex items-center justify-center mb-4">
                  <pillar.icon className="w-8 h-8 text-blueprint-cyan" />
                </div>
                <h3 className="font-display text-lg text-text-primary mb-3">
                  {pillar.title}
                </h3>
                <p className="text-sm text-text-secondary leading-relaxed">
                  {pillar.description}
                </p>
              </div>
            ))}
          </AnimatedList>
        </div>
      </div>
    </SlideLayout>
  );
}

// ============================================================================
// MILESTONE CELEBRATION SLIDE
// ============================================================================
export function MilestoneCelebrationSlide({ slideNumber }: { slideNumber: number }) {
  return (
    <SlideLayout slideNumber={slideNumber} showGrid={true} showCorners={true}>
      <div className="h-full flex flex-col items-center justify-center px-20">
        <AnimatedSlide animation="scale">
          <div className="w-32 h-32 rounded-full bg-gradient-to-br from-blueprint-cyan/30 to-purple-500/20 border-2 border-blueprint-cyan flex items-center justify-center mb-8">
            <Star className="w-16 h-16 text-blueprint-cyan" />
          </div>
        </AnimatedSlide>

        <AnimatedSlide animation="slideUp" delay={0.2}>
          <h2 className="font-display text-5xl text-text-primary text-center mb-4">
            Congratulations
          </h2>
        </AnimatedSlide>

        <AnimatedSlide animation="slideUp" delay={0.3}>
          <p className="font-mono text-lg text-blueprint-cyan tracking-wider mb-8">
            90-DAY TRANSFORMATION COMPLETE
          </p>
        </AnimatedSlide>

        <AnimatedSlide animation="fade" delay={0.5}>
          <div className="grid grid-cols-3 gap-8 mt-8">
            <div className="text-center">
              <div className="font-display text-4xl text-blueprint-cyan mb-2">12</div>
              <div className="text-sm text-text-muted">Sessions Completed</div>
            </div>
            <div className="text-center">
              <div className="font-display text-4xl text-blueprint-cyan mb-2">8</div>
              <div className="text-sm text-text-muted">Breakthroughs</div>
            </div>
            <div className="text-center">
              <div className="font-display text-4xl text-blueprint-cyan mb-2">∞</div>
              <div className="text-sm text-text-muted">Growth Potential</div>
            </div>
          </div>
        </AnimatedSlide>
      </div>
    </SlideLayout>
  );
}
