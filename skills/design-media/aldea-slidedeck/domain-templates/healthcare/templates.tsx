/**
 * Healthcare & Clinical Slide Templates
 *
 * Copy these templates into your pages/index.tsx
 */

import React from 'react';
import {
  SlideLayout,
  ChartCard,
  MetricsChart,
  RadarChart,
  FlowDiagram,
  AnimatedSlide,
  AnimatedNumber,
} from '../../assets/scaffold/components';
import { Heart, Activity, Stethoscope, ClipboardList, ShieldCheck, Users } from 'lucide-react';

// ============================================================================
// PATIENT METRICS DASHBOARD
// ============================================================================
export function PatientMetricsSlide({ slideNumber }: { slideNumber: number }) {
  const metrics = [
    { icon: Users, label: 'Active Patients', value: 2847, change: '+156 this month' },
    { icon: Activity, label: 'Avg. Recovery Time', value: 12, suffix: ' days', change: '-2 days vs avg' },
    { icon: ShieldCheck, label: 'Satisfaction Rate', value: 94.2, suffix: '%', change: '+1.3%' },
    { icon: Heart, label: 'Positive Outcomes', value: 89, suffix: '%', change: '+4%' },
  ];

  return (
    <SlideLayout chapter="CLINICAL METRICS" slideNumber={slideNumber}>
      <div className="h-full flex flex-col px-16 pt-16 pb-10">
        <AnimatedSlide animation="slideUp">
          <h2 className="font-display text-3xl text-text-primary mb-2">
            Patient Care Dashboard
          </h2>
          <p className="text-text-secondary text-sm mb-8">Real-time clinical performance metrics</p>
        </AnimatedSlide>

        <div className="grid grid-cols-2 gap-6 flex-1">
          {metrics.map((metric, index) => (
            <AnimatedSlide key={index} animation="slideUp" delay={0.1 * (index + 1)}>
              <div className="h-full bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg p-6 flex items-center gap-6">
                <div className="w-16 h-16 rounded-xl bg-blueprint-cyan/10 flex items-center justify-center flex-shrink-0">
                  <metric.icon className="w-8 h-8 text-blueprint-cyan" />
                </div>
                <div className="flex-1">
                  <div className="font-mono text-xs text-text-muted uppercase tracking-wider mb-1">
                    {metric.label}
                  </div>
                  <div className="font-display text-4xl text-text-primary">
                    <AnimatedNumber
                      value={metric.value}
                      suffix={metric.suffix}
                      decimals={metric.suffix === '%' ? 1 : 0}
                    />
                  </div>
                  <div className="text-sm text-green-400 mt-1">{metric.change}</div>
                </div>
              </div>
            </AnimatedSlide>
          ))}
        </div>
      </div>
    </SlideLayout>
  );
}

// ============================================================================
// PATIENT JOURNEY MAP
// ============================================================================
export function PatientJourneySlide({ slideNumber }: { slideNumber: number }) {
  return (
    <SlideLayout chapter="PATIENT EXPERIENCE" slideNumber={slideNumber}>
      <div className="h-full flex flex-col px-16 pt-16 pb-10">
        <h2 className="font-display text-3xl text-text-primary mb-8">
          Patient Care Journey
        </h2>

        <div className="flex-1 flex items-center">
          <FlowDiagram
            steps={[
              { label: 'Intake', sublabel: 'Initial assessment' },
              { label: 'Diagnosis', sublabel: 'Clinical evaluation' },
              { label: 'Treatment', sublabel: 'Care plan execution' },
              { label: 'Follow-up', sublabel: 'Recovery monitoring' },
            ]}
          />
        </div>

        <div className="grid grid-cols-4 gap-4 mt-8">
          <div className="p-4 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg text-center">
            <div className="font-display text-2xl text-blueprint-cyan mb-1">24h</div>
            <div className="text-xs text-text-muted">Avg. intake time</div>
          </div>
          <div className="p-4 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg text-center">
            <div className="font-display text-2xl text-blueprint-cyan mb-1">98%</div>
            <div className="text-xs text-text-muted">Diagnostic accuracy</div>
          </div>
          <div className="p-4 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg text-center">
            <div className="font-display text-2xl text-blueprint-cyan mb-1">92%</div>
            <div className="text-xs text-text-muted">Treatment adherence</div>
          </div>
          <div className="p-4 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg text-center">
            <div className="font-display text-2xl text-blueprint-cyan mb-1">89%</div>
            <div className="text-xs text-text-muted">Positive outcomes</div>
          </div>
        </div>
      </div>
    </SlideLayout>
  );
}

// ============================================================================
// CLINICAL OUTCOMES COMPARISON
// ============================================================================
export function ClinicalOutcomesSlide({ slideNumber }: { slideNumber: number }) {
  const outcomesData = [
    { subject: 'Recovery Speed', current: 85, baseline: 70 },
    { subject: 'Pain Management', current: 90, baseline: 75 },
    { subject: 'Mobility', current: 88, baseline: 72 },
    { subject: 'Quality of Life', current: 92, baseline: 78 },
    { subject: 'Patient Satisfaction', current: 94, baseline: 80 },
    { subject: 'Adherence', current: 87, baseline: 68 },
  ];

  return (
    <SlideLayout chapter="OUTCOMES ANALYSIS" slideNumber={slideNumber}>
      <div className="h-full flex px-16 pt-16 pb-10 gap-8">
        <div className="flex-1">
          <h2 className="font-display text-3xl text-text-primary mb-2">
            Clinical Outcomes Comparison
          </h2>
          <p className="text-text-secondary text-sm mb-6">
            Current protocol vs. baseline (scores out of 100)
          </p>

          <RadarChart
            data={outcomesData}
            series={[
              { key: 'current', name: 'Current Protocol', color: '#00d4ff' },
              { key: 'baseline', name: 'Baseline', color: '#6b7a8c', fillOpacity: 0.1 },
            ]}
            height={350}
          />
        </div>

        <div className="w-72 flex flex-col gap-4">
          <div className="p-5 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg">
            <h4 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-4">
              Key Improvements
            </h4>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-text-secondary">Recovery Speed</span>
                <span className="text-green-400 font-medium">+21%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-text-secondary">Adherence</span>
                <span className="text-green-400 font-medium">+28%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm text-text-secondary">Pain Management</span>
                <span className="text-green-400 font-medium">+20%</span>
              </div>
            </div>
          </div>

          <div className="p-5 bg-green-900/20 border border-green-500/30 rounded-lg flex-1">
            <h4 className="font-mono text-green-400 text-xs uppercase tracking-wider mb-3">
              Summary
            </h4>
            <p className="text-sm text-text-secondary">
              The new protocol shows significant improvement across all measured outcomes,
              with an average increase of <span className="text-green-400 font-medium">+18%</span> compared to baseline.
            </p>
          </div>
        </div>
      </div>
    </SlideLayout>
  );
}

// ============================================================================
// TREATMENT TIMELINE
// ============================================================================
export function TreatmentTimelineSlide({ slideNumber }: { slideNumber: number }) {
  const phases = [
    {
      week: 'Week 1-2',
      phase: 'Assessment',
      activities: ['Initial evaluation', 'Diagnostic tests', 'Care plan development'],
    },
    {
      week: 'Week 3-6',
      phase: 'Active Treatment',
      activities: ['Primary intervention', 'Progress monitoring', 'Adjustments as needed'],
    },
    {
      week: 'Week 7-10',
      phase: 'Recovery',
      activities: ['Rehabilitation', 'Skill building', 'Independence training'],
    },
    {
      week: 'Week 11-12',
      phase: 'Transition',
      activities: ['Final assessment', 'Aftercare planning', 'Follow-up scheduling'],
    },
  ];

  return (
    <SlideLayout chapter="TREATMENT PROTOCOL" slideNumber={slideNumber}>
      <div className="h-full flex flex-col px-16 pt-16 pb-10">
        <h2 className="font-display text-3xl text-text-primary mb-8">
          12-Week Treatment Timeline
        </h2>

        <div className="flex-1 flex items-center">
          <div className="w-full">
            {/* Timeline line */}
            <div className="relative">
              <div className="absolute top-6 left-0 right-0 h-0.5 bg-blueprint-grid" />

              <div className="grid grid-cols-4 gap-4">
                {phases.map((phase, index) => (
                  <div key={index} className="relative">
                    {/* Node */}
                    <div className="w-12 h-12 rounded-full bg-blueprint-cyan/20 border-2 border-blueprint-cyan flex items-center justify-center mx-auto mb-4">
                      <span className="font-mono text-sm text-blueprint-cyan">{index + 1}</span>
                    </div>

                    {/* Content */}
                    <div className="text-center">
                      <div className="font-mono text-xs text-blueprint-cyan mb-1">{phase.week}</div>
                      <div className="font-display text-lg text-text-primary mb-3">{phase.phase}</div>
                      <div className="p-4 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg">
                        <ul className="space-y-2 text-xs text-text-secondary text-left">
                          {phase.activities.map((activity, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <span className="w-1 h-1 mt-1.5 bg-blueprint-cyan/60 rounded-full flex-shrink-0" />
                              {activity}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </SlideLayout>
  );
}
