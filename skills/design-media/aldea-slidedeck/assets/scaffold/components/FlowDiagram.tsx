import React from 'react';

interface FlowStep {
  label: string;
  sublabel?: string;
}

interface FlowDiagramProps {
  steps: FlowStep[];
  vertical?: boolean;
  compact?: boolean;
}

export const FlowDiagram: React.FC<FlowDiagramProps> = ({
  steps,
  vertical = false,
  compact = false,
}) => {
  if (vertical) {
    return (
      <div className="flex flex-col items-center gap-2">
        {steps.map((step, i) => (
          <React.Fragment key={i}>
            <div className={`
              flex flex-col items-center justify-center text-center
              ${compact ? 'px-3 py-2' : 'px-6 py-3'}
              bg-canvas-700/60 border border-blueprint-grid/50 rounded
              min-w-[160px]
            `}>
              <span className={`font-medium text-text-primary ${compact ? 'text-xs' : 'text-sm'}`}>
                {step.label}
              </span>
              {step.sublabel && (
                <span className="text-[10px] text-text-muted mt-0.5">{step.sublabel}</span>
              )}
            </div>
            {i < steps.length - 1 && (
              <div className="flex flex-col items-center text-blueprint-cyan/50">
                <div className="w-px h-4 bg-blueprint-cyan/30" />
                <span className="text-lg leading-none">↓</span>
                <div className="w-px h-4 bg-blueprint-cyan/30" />
              </div>
            )}
          </React.Fragment>
        ))}
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 flex-wrap">
      {steps.map((step, i) => (
        <React.Fragment key={i}>
          <div className={`
            flex flex-col items-center justify-center text-center
            ${compact ? 'px-3 py-2' : 'px-5 py-3'}
            bg-canvas-700/60 border border-blueprint-grid/50 rounded
          `}>
            <span className={`font-medium text-text-primary ${compact ? 'text-xs' : 'text-sm'}`}>
              {step.label}
            </span>
            {step.sublabel && (
              <span className="text-[10px] text-text-muted mt-0.5">{step.sublabel}</span>
            )}
          </div>
          {i < steps.length - 1 && (
            <span className="text-blueprint-cyan/50 text-xl">→</span>
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

export default FlowDiagram;
