import React from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import {
  BLUEPRINT_COLORS,
  blueprintTooltipStyle,
  blueprintAxisProps,
  blueprintGridProps,
  blueprintLegendStyle,
  blueprintActiveDotProps,
} from './chart-styles';

interface DataPoint {
  name: string;
  [key: string]: string | number;
}

interface MetricsChartProps {
  data: DataPoint[];
  lines?: { key: string; color?: string; name?: string }[];
  type?: 'line' | 'area';
  height?: number;
  showGrid?: boolean;
  showLegend?: boolean;
}

export function MetricsChart({
  data,
  lines = [],
  type = 'line',
  height = 300,
  showGrid = true,
  showLegend = true,
}: MetricsChartProps) {
  const Chart = type === 'area' ? AreaChart : LineChart;
  const DataElement = type === 'area' ? Area : Line;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <Chart data={data}>
        {showGrid && (
          <CartesianGrid {...blueprintGridProps} vertical={false} />
        )}
        <XAxis dataKey="name" {...blueprintAxisProps} />
        <YAxis {...blueprintAxisProps} />
        <Tooltip contentStyle={blueprintTooltipStyle} />
        {showLegend && <Legend wrapperStyle={blueprintLegendStyle} />}
        {lines.map((line, index) => (
          <DataElement
            key={line.key}
            type="monotone"
            dataKey={line.key}
            name={line.name || line.key}
            stroke={line.color || BLUEPRINT_COLORS[index % BLUEPRINT_COLORS.length]}
            fill={type === 'area' ? `${line.color || BLUEPRINT_COLORS[index % BLUEPRINT_COLORS.length]}20` : undefined}
            strokeWidth={2}
            dot={false}
            activeDot={blueprintActiveDotProps}
          />
        ))}
      </Chart>
    </ResponsiveContainer>
  );
}
