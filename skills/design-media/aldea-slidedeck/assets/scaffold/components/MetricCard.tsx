import React from 'react';

interface MetricCardProps {
  number: number;
  title: string;
  description?: string;
  compact?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  number,
  title,
  description,
  compact = false,
}) => {
  return (
    <div className="metric-card flex gap-3 items-start">
      <div className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-blueprint-cyan/10 border border-blueprint-cyan/30 rounded-sm">
        <span className="font-mono text-blueprint-cyan text-sm font-semibold">
          {String(number).padStart(2, '0')}
        </span>
      </div>
      <div className="flex-1 min-w-0">
        <h4 className={`font-medium text-text-primary ${compact ? 'text-xs' : 'text-sm'}`}>
          {title}
        </h4>
        {description && (
          <p className={`text-text-muted mt-0.5 ${compact ? 'text-[10px]' : 'text-xs'}`}>
            {description}
          </p>
        )}
      </div>
    </div>
  );
};

export default MetricCard;
