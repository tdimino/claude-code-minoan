/**
 * Shared chart styling constants for Aldea blueprint aesthetic.
 *
 * Import these in chart components to maintain consistency
 * and reduce duplication across MetricsChart, ComparisonChart,
 * RadarChart, and TrainingMetrics.
 */

// Standard color palette for data visualization
export const BLUEPRINT_COLORS = [
  '#00d4ff', // cyan - primary
  '#60a5fa', // blue - secondary
  '#a78bfa', // purple - tertiary
  '#34d399', // green - positive/success
  '#fbbf24', // amber - warning/accent
  '#f97316', // orange - validation/alternate
];

// Tooltip styling for all Recharts tooltips
export const blueprintTooltipStyle = {
  backgroundColor: '#0d1420',
  border: '1px solid rgba(0, 180, 216, 0.4)',
  borderRadius: '4px',
  color: '#e2e8f0',
};

// Common axis styling props
export const blueprintAxisProps = {
  stroke: '#6b7a8c',
  tick: { fill: '#6b7a8c', fontSize: 11 },
  axisLine: { stroke: 'rgba(0, 180, 216, 0.3)' },
};

// Grid styling for CartesianGrid
export const blueprintGridProps = {
  strokeDasharray: '3 3',
  stroke: 'rgba(0, 180, 216, 0.15)',
};

// Legend styling
export const blueprintLegendStyle = {
  color: '#a0aec0',
  fontSize: 12,
};

// Polar grid styling (for RadarChart)
export const blueprintPolarGridProps = {
  stroke: 'rgba(0, 180, 216, 0.2)',
  gridType: 'polygon' as const,
};

// Polar angle axis styling
export const blueprintPolarAngleAxisProps = {
  tick: { fill: '#a0aec0', fontSize: 11 },
};

// Polar radius axis styling
export const blueprintPolarRadiusAxisProps = {
  tick: { fill: '#6b7a8c', fontSize: 10 },
  axisLine: false,
};

// Default active dot styling for line/area charts
export const blueprintActiveDotProps = {
  r: 4,
  strokeWidth: 2,
};

// Reference line styling (for markers like "best epoch")
export const blueprintReferenceLineProps = {
  stroke: '#34d399',
  strokeDasharray: '3 3',
};
