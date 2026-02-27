import { motion } from "motion/react";

interface Axis {
  label: string;
  max: number;
}

interface Series {
  values: number[];
  color: string;
  label?: string;
}

interface SVGRadarChartProps {
  axes: Axis[];
  series: Series[];
  /** Chart size in pixels. Default 200. */
  size?: number;
  /** Animation delay in seconds. Default 0.5. */
  delay?: number;
  className?: string;
}

function polarToCartesian(cx: number, cy: number, radius: number, angle: number) {
  return {
    x: cx + radius * Math.cos(angle),
    y: cy + radius * Math.sin(angle),
  };
}

export function SVGRadarChart({
  axes,
  series,
  size = 200,
  delay = 0.5,
  className,
}: SVGRadarChartProps) {
  const n = axes.length;
  const cx = size / 2;
  const cy = size / 2;
  const maxRadius = size * 0.3;
  const labelRadius = size * 0.42;

  // Build outer boundary path
  const outerPoints = axes.map((_, i) => {
    const angle = (i * Math.PI * 2) / n - Math.PI / 2;
    return polarToCartesian(cx, cy, maxRadius, angle);
  });
  const outerPath =
    outerPoints.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z";

  return (
    <div className={className}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Outer boundary */}
        <path
          d={outerPath}
          fill="rgba(255,255,255,0.02)"
          stroke="var(--color-border-light)"
          strokeWidth="1"
        />

        {/* Axis lines from center */}
        {outerPoints.map((p, i) => (
          <line
            key={`axis-${i}`}
            x1={cx}
            y1={cy}
            x2={p.x}
            y2={p.y}
            stroke="var(--color-border-light)"
            strokeWidth="0.5"
          />
        ))}

        {/* Data series */}
        {series.map((s, si) => {
          const dataPoints = s.values.slice(0, n).map((val, i) => {
            const angle = (i * Math.PI * 2) / n - Math.PI / 2;
            const max = axes[i].max || 1;
            const r = (val / max) * maxRadius;
            return polarToCartesian(cx, cy, r, angle);
          });
          const dataPath =
            dataPoints.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ") + " Z";

          return (
            <g key={`series-${si}`}>
              <motion.path
                d={dataPath}
                fill={`${s.color}25`}
                stroke={s.color}
                strokeWidth="1.5"
                strokeLinejoin="round"
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 0.8, delay: delay + si * 0.2 }}
              />
              {/* Data point dots */}
              {dataPoints.map((p, i) => {
                const pct = s.values[i] / (axes[i].max || 1);
                const dotColor = pct >= 0.7 ? "#4ade80" : pct >= 0.4 ? s.color : "#f87171";
                return (
                  <circle key={`dot-${i}`} cx={p.x} cy={p.y} r="3" fill={dotColor} />
                );
              })}
            </g>
          );
        })}

        {/* Axis labels */}
        {axes.map((axis, i) => {
          const angle = (i * Math.PI * 2) / n - Math.PI / 2;
          const { x, y } = polarToCartesian(cx, cy, labelRadius, angle);
          return (
            <text
              key={`label-${i}`}
              x={x}
              y={y}
              textAnchor="middle"
              dominantBaseline="central"
              fill="var(--color-text-secondary)"
              fontSize="12"
              fontFamily="var(--font-mono)"
            >
              {axis.label}
            </text>
          );
        })}
      </svg>
    </div>
  );
}
