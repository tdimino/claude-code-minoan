/**
 * Business & Finance Slide Templates
 *
 * Copy these templates into your pages/index.tsx
 */

import React from 'react';
import {
  SlideLayout,
  ChartCard,
  MetricsChart,
  ComparisonChart,
  AnimatedSlide,
  AnimatedNumber,
} from '../../assets/scaffold/components';
import { TrendingUp, DollarSign, Users, Target } from 'lucide-react';

// ============================================================================
// KPI DASHBOARD SLIDE
// ============================================================================
export function KPIDashboardSlide({ slideNumber }: { slideNumber: number }) {
  const kpis = [
    { icon: DollarSign, label: 'Revenue', value: 2450000, prefix: '$', change: '+12%' },
    { icon: Users, label: 'Customers', value: 15420, change: '+8%' },
    { icon: Target, label: 'Conversion', value: 4.2, suffix: '%', change: '+0.5%' },
    { icon: TrendingUp, label: 'Growth', value: 23, suffix: '%', change: '+3%' },
  ];

  return (
    <SlideLayout chapter="BUSINESS METRICS" slideNumber={slideNumber}>
      <div className="h-full flex flex-col px-16 pt-16 pb-10">
        <AnimatedSlide animation="slideUp">
          <h2 className="font-display text-3xl text-text-primary mb-8">
            Key Performance Indicators
          </h2>
        </AnimatedSlide>

        <div className="grid grid-cols-4 gap-6 flex-1">
          {kpis.map((kpi, index) => (
            <AnimatedSlide key={index} animation="slideUp" delay={0.1 * (index + 1)}>
              <div className="h-full bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg p-6 flex flex-col">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-blueprint-cyan/10 flex items-center justify-center">
                    <kpi.icon className="w-5 h-5 text-blueprint-cyan" />
                  </div>
                  <span className="font-mono text-xs text-text-muted uppercase tracking-wider">
                    {kpi.label}
                  </span>
                </div>
                <div className="flex-1 flex flex-col justify-center">
                  <div className="font-display text-3xl text-text-primary">
                    <AnimatedNumber
                      value={kpi.value}
                      prefix={kpi.prefix}
                      suffix={kpi.suffix}
                      decimals={kpi.suffix === '%' ? 1 : 0}
                    />
                  </div>
                  <div className="text-sm text-green-400 mt-2">{kpi.change}</div>
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
// REVENUE CHART SLIDE
// ============================================================================
export function RevenueChartSlide({ slideNumber }: { slideNumber: number }) {
  const revenueData = [
    { name: 'Q1', revenue: 1200000, costs: 800000 },
    { name: 'Q2', revenue: 1500000, costs: 900000 },
    { name: 'Q3', revenue: 1800000, costs: 950000 },
    { name: 'Q4', revenue: 2450000, costs: 1100000 },
  ];

  return (
    <SlideLayout chapter="FINANCIAL PERFORMANCE" slideNumber={slideNumber}>
      <div className="h-full flex flex-col px-16 pt-16 pb-10">
        <h2 className="font-display text-3xl text-text-primary mb-2">
          Revenue vs Costs
        </h2>
        <p className="text-text-secondary text-sm mb-6">Quarterly comparison FY2025</p>

        <div className="flex-1">
          <ChartCard>
            <ComparisonChart
              data={revenueData}
              bars={[
                { key: 'revenue', color: '#00d4ff', name: 'Revenue' },
                { key: 'costs', color: '#f97316', name: 'Costs' },
              ]}
              height={320}
            />
          </ChartCard>
        </div>

        <div className="grid grid-cols-3 gap-6 mt-6">
          <div className="text-center p-4 bg-canvas-700/30 rounded-lg">
            <div className="font-display text-xl text-blueprint-cyan">$6.95M</div>
            <div className="text-xs text-text-muted mt-1">Total Revenue</div>
          </div>
          <div className="text-center p-4 bg-canvas-700/30 rounded-lg">
            <div className="font-display text-xl text-green-400">$3.2M</div>
            <div className="text-xs text-text-muted mt-1">Net Profit</div>
          </div>
          <div className="text-center p-4 bg-canvas-700/30 rounded-lg">
            <div className="font-display text-xl text-text-primary">46%</div>
            <div className="text-xs text-text-muted mt-1">Margin</div>
          </div>
        </div>
      </div>
    </SlideLayout>
  );
}

// ============================================================================
// GROWTH TRENDS SLIDE
// ============================================================================
export function GrowthTrendsSlide({ slideNumber }: { slideNumber: number }) {
  const growthData = [
    { name: 'Jan', users: 10200, arr: 1.2 },
    { name: 'Feb', users: 11500, arr: 1.35 },
    { name: 'Mar', users: 12800, arr: 1.5 },
    { name: 'Apr', users: 14200, arr: 1.7 },
    { name: 'May', users: 15000, arr: 1.85 },
    { name: 'Jun', users: 15420, arr: 2.0 },
  ];

  return (
    <SlideLayout chapter="GROWTH ANALYSIS" slideNumber={slideNumber}>
      <div className="h-full flex px-16 pt-16 pb-10 gap-8">
        <div className="flex-1">
          <h2 className="font-display text-3xl text-text-primary mb-6">
            User Growth Trajectory
          </h2>
          <ChartCard title="Active Users">
            <MetricsChart
              data={growthData}
              lines={[{ key: 'users', name: 'Active Users' }]}
              type="area"
              height={280}
            />
          </ChartCard>
        </div>

        <div className="w-80 flex flex-col gap-4">
          <div className="p-5 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg">
            <h4 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-3">
              Growth Metrics
            </h4>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-text-secondary">MoM Growth</span>
                <span className="text-text-primary font-medium">+8.2%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-text-secondary">Retention</span>
                <span className="text-text-primary font-medium">94%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-text-secondary">NPS</span>
                <span className="text-text-primary font-medium">72</span>
              </div>
            </div>
          </div>

          <div className="p-5 bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg flex-1">
            <h4 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-3">
              Milestones
            </h4>
            <ul className="space-y-3 text-sm">
              <li className="flex items-center gap-2 text-text-secondary">
                <span className="w-2 h-2 bg-green-400 rounded-full" />
                10K users (Jan)
              </li>
              <li className="flex items-center gap-2 text-text-secondary">
                <span className="w-2 h-2 bg-green-400 rounded-full" />
                $1M ARR (Feb)
              </li>
              <li className="flex items-center gap-2 text-text-secondary">
                <span className="w-2 h-2 bg-green-400 rounded-full" />
                15K users (May)
              </li>
              <li className="flex items-center gap-2 text-blueprint-cyan">
                <span className="w-2 h-2 bg-blueprint-cyan rounded-full" />
                $2M ARR (Jun)
              </li>
            </ul>
          </div>
        </div>
      </div>
    </SlideLayout>
  );
}

// ============================================================================
// PRICING COMPARISON SLIDE
// ============================================================================
export function PricingComparisonSlide({ slideNumber }: { slideNumber: number }) {
  return (
    <SlideLayout chapter="PRICING" slideNumber={slideNumber}>
      <div className="h-full flex flex-col px-16 pt-16 pb-10">
        <h2 className="font-display text-3xl text-text-primary text-center mb-8">
          Choose Your Plan
        </h2>

        <div className="flex-1 grid grid-cols-3 gap-6">
          {/* Starter */}
          <div className="bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg p-6 flex flex-col">
            <div className="text-center mb-6">
              <h3 className="font-display text-xl text-text-primary mb-2">Starter</h3>
              <div className="font-display text-4xl text-blueprint-cyan">
                $29<span className="text-lg text-text-muted">/mo</span>
              </div>
            </div>
            <ul className="space-y-3 text-sm text-text-secondary flex-1">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blueprint-cyan rounded-full" />
                Up to 5 users
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blueprint-cyan rounded-full" />
                10GB storage
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blueprint-cyan rounded-full" />
                Email support
              </li>
            </ul>
          </div>

          {/* Professional (featured) */}
          <div className="bg-blueprint-cyan/10 border-2 border-blueprint-cyan rounded-lg p-6 flex flex-col relative">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-blueprint-cyan text-blueprint-dark text-xs font-bold rounded">
              POPULAR
            </div>
            <div className="text-center mb-6">
              <h3 className="font-display text-xl text-text-primary mb-2">Professional</h3>
              <div className="font-display text-4xl text-blueprint-cyan">
                $99<span className="text-lg text-text-muted">/mo</span>
              </div>
            </div>
            <ul className="space-y-3 text-sm text-text-secondary flex-1">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blueprint-cyan rounded-full" />
                Up to 25 users
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blueprint-cyan rounded-full" />
                100GB storage
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blueprint-cyan rounded-full" />
                Priority support
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blueprint-cyan rounded-full" />
                Analytics dashboard
              </li>
            </ul>
          </div>

          {/* Enterprise */}
          <div className="bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg p-6 flex flex-col">
            <div className="text-center mb-6">
              <h3 className="font-display text-xl text-text-primary mb-2">Enterprise</h3>
              <div className="font-display text-4xl text-blueprint-cyan">
                Custom
              </div>
            </div>
            <ul className="space-y-3 text-sm text-text-secondary flex-1">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blueprint-cyan rounded-full" />
                Unlimited users
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blueprint-cyan rounded-full" />
                Unlimited storage
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blueprint-cyan rounded-full" />
                Dedicated support
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blueprint-cyan rounded-full" />
                Custom integrations
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-blueprint-cyan rounded-full" />
                SLA guarantee
              </li>
            </ul>
          </div>
        </div>
      </div>
    </SlideLayout>
  );
}
