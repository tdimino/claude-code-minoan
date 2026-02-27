import React from 'react';

interface ChartCardProps {
  title?: string;
  subtitle?: string;
  children: React.ReactNode;
  className?: string;
}

export function ChartCard({ title, subtitle, children, className = '' }: ChartCardProps) {
  return (
    <div className={`bg-canvas-700/40 border border-blueprint-grid/40 rounded-lg p-6 ${className}`}>
      {(title || subtitle) && (
        <div className="mb-4">
          {title && (
            <h3 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-1">
              {title}
            </h3>
          )}
          {subtitle && (
            <p className="text-text-secondary text-sm">{subtitle}</p>
          )}
        </div>
      )}
      <div className="w-full">{children}</div>
    </div>
  );
}
