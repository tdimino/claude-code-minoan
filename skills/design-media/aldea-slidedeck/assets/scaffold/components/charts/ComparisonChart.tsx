import React from 'react';
import {
  BarChart,
  Bar,
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
} from './chart-styles';

interface DataPoint {
  name: string;
  [key: string]: string | number;
}

interface ComparisonChartProps {
  data: DataPoint[];
  bars?: { key: string; color?: string; name?: string }[];
  height?: number;
  layout?: 'horizontal' | 'vertical';
  showGrid?: boolean;
  showLegend?: boolean;
  stacked?: boolean;
}

export function ComparisonChart({
  data,
  bars = [],
  height = 300,
  layout = 'horizontal',
  showGrid = true,
  showLegend = true,
  stacked = false,
}: ComparisonChartProps) {
  const isVertical = layout === 'vertical';

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={data}
        layout={isVertical ? 'vertical' : 'horizontal'}
        barCategoryGap="20%"
      >
        {showGrid && (
          <CartesianGrid
            {...blueprintGridProps}
            horizontal={!isVertical}
            vertical={isVertical}
          />
        )}
        {isVertical ? (
          <>
            <XAxis type="number" {...blueprintAxisProps} />
            <YAxis type="category" dataKey="name" {...blueprintAxisProps} width={100} />
          </>
        ) : (
          <>
            <XAxis dataKey="name" {...blueprintAxisProps} />
            <YAxis {...blueprintAxisProps} />
          </>
        )}
        <Tooltip contentStyle={blueprintTooltipStyle} />
        {showLegend && bars.length > 1 && (
          <Legend wrapperStyle={blueprintLegendStyle} />
        )}
        {bars.map((bar, index) => (
          <Bar
            key={bar.key}
            dataKey={bar.key}
            name={bar.name || bar.key}
            fill={bar.color || BLUEPRINT_COLORS[index % BLUEPRINT_COLORS.length]}
            radius={[4, 4, 0, 0]}
            stackId={stacked ? 'stack' : undefined}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
