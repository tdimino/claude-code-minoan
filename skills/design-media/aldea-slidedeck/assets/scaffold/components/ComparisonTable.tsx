import React from 'react';

interface TableRow {
  label: string;
  values: (string | boolean)[];
}

interface ComparisonTableProps {
  headers: string[];
  rows: TableRow[];
  compact?: boolean;
}

export const ComparisonTable: React.FC<ComparisonTableProps> = ({
  headers,
  rows,
  compact = false,
}) => {
  const renderCell = (value: string | boolean) => {
    if (typeof value === 'boolean') {
      return value ? (
        <span className="text-green-400">✓</span>
      ) : (
        <span className="text-text-muted">—</span>
      );
    }
    return value;
  };

  return (
    <div className="overflow-hidden rounded border border-blueprint-grid/40">
      <table className="w-full">
        <thead>
          <tr className="bg-canvas-700/60">
            {headers.map((header, i) => (
              <th
                key={i}
                className={`
                  text-left font-mono text-blueprint-cyan/80 uppercase tracking-wider
                  ${compact ? 'text-[10px] px-3 py-2' : 'text-xs px-4 py-3'}
                  ${i === 0 ? '' : 'border-l border-blueprint-grid/30'}
                `}
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr
              key={i}
              className={`
                border-t border-blueprint-grid/30
                ${i % 2 === 0 ? 'bg-canvas-800/30' : 'bg-transparent'}
              `}
            >
              <td className={`font-medium text-text-primary ${compact ? 'text-xs px-3 py-2' : 'text-sm px-4 py-3'}`}>
                {row.label}
              </td>
              {row.values.map((value, j) => (
                <td
                  key={j}
                  className={`
                    text-text-secondary border-l border-blueprint-grid/30 text-center
                    ${compact ? 'text-xs px-3 py-2' : 'text-sm px-4 py-3'}
                  `}
                >
                  {renderCell(value)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ComparisonTable;
