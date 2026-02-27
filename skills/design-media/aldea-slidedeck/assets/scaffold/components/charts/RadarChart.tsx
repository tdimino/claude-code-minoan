import React from 'react';
import {
  RadarChart as RechartsRadar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Legend,
  Tooltip,
} from 'recharts';
import {
  BLUEPRINT_COLORS,
  blueprintTooltipStyle,
  blueprintLegendStyle,
  blueprintPolarGridProps,
  blueprintPolarAngleAxisProps,
  blueprintPolarRadiusAxisProps,
} from './chart-styles';

interface DataPoint {
  subject: string;
  [key: string]: string | number;
}

interface RadarChartProps {
  data: DataPoint[];
  series?: { key: string; color?: string; name?: string; fillOpacity?: number }[];
  height?: number;
  showLegend?: boolean;
}

export function RadarChart({
  data,
  series = [],
  height = 300,
  showLegend = true,
}: RadarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsRadar cx="50%" cy="50%" outerRadius="70%" data={data}>
        <PolarGrid {...blueprintPolarGridProps} />
        <PolarAngleAxis dataKey="subject" {...blueprintPolarAngleAxisProps} />
        <PolarRadiusAxis angle={30} domain={[0, 100]} {...blueprintPolarRadiusAxisProps} />
        <Tooltip contentStyle={blueprintTooltipStyle} />
        {showLegend && series.length > 1 && (
          <Legend wrapperStyle={blueprintLegendStyle} />
        )}
        {series.map((s, index) => (
          <Radar
            key={s.key}
            name={s.name || s.key}
            dataKey={s.key}
            stroke={s.color || BLUEPRINT_COLORS[index % BLUEPRINT_COLORS.length]}
            fill={s.color || BLUEPRINT_COLORS[index % BLUEPRINT_COLORS.length]}
            fillOpacity={s.fillOpacity ?? 0.2}
            strokeWidth={2}
          />
        ))}
      </RechartsRadar>
    </ResponsiveContainer>
  );
}
