import React from 'react';

interface AttentionHeatmapProps {
  tokens: string[];
  weights: number[][]; // 2D matrix of attention weights
  title?: string;
  maxCellSize?: number;
}

function getHeatColor(value: number): string {
  // Blueprint-themed gradient from dark to cyan
  const intensity = Math.max(0, Math.min(1, value));
  if (intensity < 0.2) return 'rgba(13, 20, 32, 0.8)';
  if (intensity < 0.4) return 'rgba(0, 100, 130, 0.6)';
  if (intensity < 0.6) return 'rgba(0, 140, 170, 0.7)';
  if (intensity < 0.8) return 'rgba(0, 180, 216, 0.8)';
  return 'rgba(0, 212, 255, 0.95)';
}

export function AttentionHeatmap({
  tokens,
  weights,
  title,
  maxCellSize = 40,
}: AttentionHeatmapProps) {
  const cellSize = Math.min(maxCellSize, 400 / Math.max(tokens.length, 1));

  return (
    <div className="inline-block">
      {title && (
        <h4 className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-3">
          {title}
        </h4>
      )}
      <div className="overflow-x-auto">
        <div className="inline-block">
          {/* Column headers */}
          <div className="flex" style={{ marginLeft: cellSize * 2.5 }}>
            {tokens.map((token, i) => (
              <div
                key={`col-${i}`}
                className="font-mono text-[10px] text-text-muted truncate"
                style={{
                  width: cellSize,
                  transform: 'rotate(-45deg)',
                  transformOrigin: 'left bottom',
                  whiteSpace: 'nowrap',
                }}
              >
                {token}
              </div>
            ))}
          </div>

          {/* Rows with heatmap */}
          <div className="mt-6">
            {weights.map((row, rowIndex) => (
              <div key={`row-${rowIndex}`} className="flex items-center">
                {/* Row label */}
                <div
                  className="font-mono text-[10px] text-text-muted truncate pr-2 text-right"
                  style={{ width: cellSize * 2.5 }}
                >
                  {tokens[rowIndex]}
                </div>

                {/* Cells */}
                {row.map((weight, colIndex) => (
                  <div
                    key={`cell-${rowIndex}-${colIndex}`}
                    className="border border-blueprint-grid/20 flex items-center justify-center transition-all hover:scale-110 hover:z-10"
                    style={{
                      width: cellSize,
                      height: cellSize,
                      backgroundColor: getHeatColor(weight),
                    }}
                    title={`${tokens[rowIndex]} → ${tokens[colIndex]}: ${weight.toFixed(3)}`}
                  >
                    {cellSize >= 30 && (
                      <span className="font-mono text-[8px] text-text-primary/70">
                        {weight.toFixed(2)}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            ))}
          </div>

          {/* Legend */}
          <div className="flex items-center gap-2 mt-4 ml-auto w-fit">
            <span className="font-mono text-[10px] text-text-muted">0</span>
            <div className="flex h-3">
              {[0, 0.25, 0.5, 0.75, 1].map((v) => (
                <div
                  key={v}
                  className="w-6"
                  style={{ backgroundColor: getHeatColor(v) }}
                />
              ))}
            </div>
            <span className="font-mono text-[10px] text-text-muted">1</span>
          </div>
        </div>
      </div>
    </div>
  );
}
