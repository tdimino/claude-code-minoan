import React from 'react';

interface StatsBarProps {
  stats: { value: string; label: string; color: string }[];
}

/** In-flow stats footer. Use mt-auto to push to bottom of flex column.
 *  IMPORTANT: Do NOT use absolute positioning — it will extend beyond card bounds. */
export const StatsBar: React.FC<StatsBarProps> = ({ stats }) => (
  <div className="mt-auto h-14 rounded-lg border border-canvas-700 flex items-center justify-around z-20" style={{ background: 'rgba(30, 40, 60, 0.06)' }}>
    {stats.map(({ value, label, color }) => (
      <div key={label} className="text-center">
        <span className="text-2xl font-bold font-mono" style={{ color }}>{value}</span>
        <span className="text-xs text-text-muted block mt-0.5">{label}</span>
      </div>
    ))}
  </div>
);

export default StatsBar;
