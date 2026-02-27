import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from 'recharts';
import { blueprintTooltipStyle, blueprintReferenceLineProps } from '../charts/chart-styles';

interface TrainingDataPoint {
  epoch: number;
  trainLoss?: number;
  valLoss?: number;
  trainAcc?: number;
  valAcc?: number;
  lr?: number;
  [key: string]: number | undefined;
}

interface TrainingMetricsProps {
  data: TrainingDataPoint[];
  metrics?: ('loss' | 'accuracy' | 'learning_rate')[];
  height?: number;
  showBestEpoch?: boolean;
  title?: string;
}

export function TrainingMetrics({
  data,
  metrics = ['loss', 'accuracy'],
  height = 280,
  showBestEpoch = true,
  title,
}: TrainingMetricsProps) {
  // Find best epoch (lowest val loss)
  const bestEpoch = data.reduce((best, point, idx) => {
    if (point.valLoss !== undefined && (best === -1 || point.valLoss < (data[best].valLoss ?? Infinity))) {
      return idx;
    }
    return best;
  }, -1);

  const showLoss = metrics.includes('loss');
  const showAcc = metrics.includes('accuracy');
  const showLR = metrics.includes('learning_rate');

  return (
    <div className="w-full">
      {title && (
        <h4 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-3">
          {title}
        </h4>
      )}

      <div className="flex gap-4">
        {/* Loss Chart */}
        {showLoss && (
          <div className="flex-1 bg-canvas-700/30 rounded-lg p-4 border border-blueprint-grid/30">
            <div className="font-mono text-xs text-text-muted mb-2">Loss</div>
            <ResponsiveContainer width="100%" height={height}>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 180, 216, 0.1)" />
                <XAxis
                  dataKey="epoch"
                  stroke="#6b7a8c"
                  tick={{ fill: '#6b7a8c', fontSize: 10 }}
                  label={{ value: 'Epoch', position: 'bottom', fill: '#6b7a8c', fontSize: 10 }}
                />
                <YAxis
                  stroke="#6b7a8c"
                  tick={{ fill: '#6b7a8c', fontSize: 10 }}
                  domain={['auto', 'auto']}
                />
                <Tooltip contentStyle={{ ...blueprintTooltipStyle, fontSize: 11 }} />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {showBestEpoch && bestEpoch >= 0 && (
                  <ReferenceLine
                    x={data[bestEpoch].epoch}
                    {...blueprintReferenceLineProps}
                    label={{ value: 'Best', fill: '#34d399', fontSize: 9 }}
                  />
                )}
                <Line
                  type="monotone"
                  dataKey="trainLoss"
                  name="Train"
                  stroke="#60a5fa"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="valLoss"
                  name="Validation"
                  stroke="#f97316"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Accuracy Chart */}
        {showAcc && (
          <div className="flex-1 bg-canvas-700/30 rounded-lg p-4 border border-blueprint-grid/30">
            <div className="font-mono text-xs text-text-muted mb-2">Accuracy</div>
            <ResponsiveContainer width="100%" height={height}>
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 180, 216, 0.1)" />
                <XAxis
                  dataKey="epoch"
                  stroke="#6b7a8c"
                  tick={{ fill: '#6b7a8c', fontSize: 10 }}
                  label={{ value: 'Epoch', position: 'bottom', fill: '#6b7a8c', fontSize: 10 }}
                />
                <YAxis
                  stroke="#6b7a8c"
                  tick={{ fill: '#6b7a8c', fontSize: 10 }}
                  domain={[0, 1]}
                  tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
                />
                <Tooltip
                  contentStyle={{ ...blueprintTooltipStyle, fontSize: 11 }}
                  formatter={(value: number) => `${(value * 100).toFixed(1)}%`}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                {showBestEpoch && bestEpoch >= 0 && (
                  <ReferenceLine x={data[bestEpoch].epoch} {...blueprintReferenceLineProps} />
                )}
                <Line
                  type="monotone"
                  dataKey="trainAcc"
                  name="Train"
                  stroke="#60a5fa"
                  strokeWidth={2}
                  dot={false}
                />
                <Line
                  type="monotone"
                  dataKey="valAcc"
                  name="Validation"
                  stroke="#f97316"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Learning Rate (optional smaller chart) */}
      {showLR && (
        <div className="mt-4 bg-canvas-700/30 rounded-lg p-4 border border-blueprint-grid/30">
          <div className="font-mono text-xs text-text-muted mb-2">Learning Rate</div>
          <ResponsiveContainer width="100%" height={100}>
            <LineChart data={data}>
              <XAxis dataKey="epoch" hide />
              <YAxis
                stroke="#6b7a8c"
                tick={{ fill: '#6b7a8c', fontSize: 9 }}
                tickFormatter={(v) => v.toExponential(0)}
                width={50}
              />
              <Line
                type="stepAfter"
                dataKey="lr"
                stroke="#a78bfa"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

// Helper to generate sample training data
export function generateSampleTrainingData(epochs: number = 50): TrainingDataPoint[] {
  const data: TrainingDataPoint[] = [];
  for (let i = 1; i <= epochs; i++) {
    const progress = i / epochs;
    data.push({
      epoch: i,
      trainLoss: 2.5 * Math.exp(-3 * progress) + 0.1 + Math.random() * 0.05,
      valLoss: 2.5 * Math.exp(-2.5 * progress) + 0.15 + Math.random() * 0.08,
      trainAcc: 1 - Math.exp(-4 * progress) - 0.05 + Math.random() * 0.02,
      valAcc: 1 - Math.exp(-3.5 * progress) - 0.08 + Math.random() * 0.03,
      lr: 0.001 * Math.pow(0.95, Math.floor(i / 10)),
    });
  }
  return data;
}
