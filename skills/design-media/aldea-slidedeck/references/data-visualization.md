# Data Visualization Reference

Comprehensive guide to chart and data visualization components in Aldea slide decks.

## Libraries

| Library | Use Case | Installation |
|---------|----------|--------------|
| **Recharts** | Primary charts (line, bar, area, radar) | Included |
| **React Flow** | Architecture diagrams, flowcharts | Included |
| **Mermaid** | Markdown-based diagrams | Included |

## Chart Components

### ChartCard

Wrapper component that applies blueprint styling to any chart.

```tsx
import { ChartCard } from '../components';

<ChartCard title="Revenue Growth" subtitle="Q1-Q4 2025">
  <MetricsChart data={data} lines={[{ key: 'revenue', name: 'Revenue' }]} />
</ChartCard>
```

**Props:**
- `title?: string` - Header text (cyan, uppercase)
- `subtitle?: string` - Secondary description
- `children: ReactNode` - Chart content
- `className?: string` - Additional CSS classes

---

### MetricsChart

Line and area charts for time series data.

```tsx
import { MetricsChart } from '../components';

const data = [
  { name: 'Jan', users: 400, sessions: 240 },
  { name: 'Feb', users: 600, sessions: 380 },
  // ...
];

<MetricsChart
  data={data}
  lines={[
    { key: 'users', color: '#00d4ff', name: 'Active Users' },
    { key: 'sessions', color: '#60a5fa', name: 'Sessions' }
  ]}
  type="area"
  height={300}
/>
```

**Props:**
- `data: DataPoint[]` - Array with `name` key and numeric values
- `lines: { key, color?, name? }[]` - Lines to render
- `type?: 'line' | 'area'` - Chart type (default: 'line')
- `height?: number` - Chart height (default: 300)
- `showGrid?: boolean` - Show grid lines (default: true)
- `showLegend?: boolean` - Show legend (default: true)

---

### ComparisonChart

Bar charts for comparing values across categories.

```tsx
import { ComparisonChart } from '../components';

const data = [
  { name: 'Product A', sales: 4000, costs: 2400 },
  { name: 'Product B', sales: 3000, costs: 1398 },
];

<ComparisonChart
  data={data}
  bars={[
    { key: 'sales', color: '#00d4ff', name: 'Sales' },
    { key: 'costs', color: '#f97316', name: 'Costs' }
  ]}
  layout="horizontal"
  stacked={false}
/>
```

**Props:**
- `data: DataPoint[]` - Array with `name` key and numeric values
- `bars: { key, color?, name? }[]` - Bars to render
- `layout?: 'horizontal' | 'vertical'` - Orientation
- `stacked?: boolean` - Stack bars (default: false)
- `height?: number` - Chart height (default: 300)

---

### RadarChart

Multi-dimensional comparison charts.

```tsx
import { RadarChart } from '../components';

const data = [
  { subject: 'Speed', modelA: 85, modelB: 72 },
  { subject: 'Accuracy', modelA: 92, modelB: 88 },
  { subject: 'Efficiency', modelA: 78, modelB: 90 },
  // ...
];

<RadarChart
  data={data}
  series={[
    { key: 'modelA', name: 'Model A', color: '#00d4ff' },
    { key: 'modelB', name: 'Model B', color: '#a78bfa' }
  ]}
  height={300}
/>
```

**Props:**
- `data: { subject: string, [key]: number }[]` - Data points
- `series: { key, color?, name?, fillOpacity? }[]` - Series to render
- `height?: number` - Chart height (default: 300)
- `showLegend?: boolean` - Show legend (default: true)

---

## Color Palette

Blueprint-themed chart colors:

```typescript
const BLUEPRINT_COLORS = [
  '#00d4ff', // Primary cyan
  '#60a5fa', // Blue
  '#a78bfa', // Purple
  '#34d399', // Green
  '#fbbf24', // Amber
];
```

## Best Practices

### Slide Charts

1. **Height**: Use 250-350px for slide charts
2. **Data points**: Limit to 8-12 for readability
3. **Lines/bars**: Maximum 3-4 series per chart
4. **Labels**: Keep axis labels short

### Comparison Charts

```tsx
// Good: Clear, limited categories
const data = [
  { name: 'Q1', value: 4000 },
  { name: 'Q2', value: 3000 },
  { name: 'Q3', value: 5000 },
  { name: 'Q4', value: 4500 },
];

// Avoid: Too many categories
const badData = [
  { name: 'January 2025', value: 1000 },
  // ... 12 months with long labels
];
```

### Time Series

```tsx
// Good: Smooth curves, clear trend
<MetricsChart
  data={monthlyData}
  lines={[{ key: 'users', name: 'Users' }]}
  type="area"
/>

// For multiple metrics, use distinct colors
<MetricsChart
  data={data}
  lines={[
    { key: 'revenue', color: '#00d4ff' },
    { key: 'costs', color: '#f97316' }
  ]}
/>
```

## Responsive Considerations

All chart components use `ResponsiveContainer` and scale to fit their parent. Wrap in a fixed-height container for predictable sizing:

```tsx
<div className="h-[300px]">
  <MetricsChart data={data} lines={lines} />
</div>
```

## Export Notes

When exporting to PDF:
- Charts render as vector graphics (crisp at any zoom)
- Animations are frozen at final state
- Tooltips are not captured (data visible in chart)
