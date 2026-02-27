import React, { useMemo } from 'react';

interface AudioWaveformProps {
  data: number[]; // Amplitude values between -1 and 1
  width?: number;
  height?: number;
  color?: string;
  backgroundColor?: string;
  showAxis?: boolean;
  label?: string;
  timestamps?: { time: string; label: string }[];
}

export function AudioWaveform({
  data,
  width = 600,
  height = 120,
  color = '#00d4ff',
  backgroundColor = 'transparent',
  showAxis = true,
  label,
  timestamps = [],
}: AudioWaveformProps) {
  const pathData = useMemo(() => {
    if (data.length === 0) return '';

    const xStep = data.length > 1 ? width / (data.length - 1) : 0;
    const yCenter = height / 2;
    const yScale = (height / 2) * 0.9;

    let path = `M 0 ${yCenter + data[0] * yScale}`;

    for (let i = 1; i < data.length; i++) {
      const x = i * xStep;
      const y = yCenter - data[i] * yScale;
      path += ` L ${x} ${y}`;
    }

    return path;
  }, [data, width, height]);

  // Mirror path for filled waveform
  const filledPath = useMemo(() => {
    if (data.length === 0) return '';

    const xStep = data.length > 1 ? width / (data.length - 1) : 0;
    const yCenter = height / 2;
    const yScale = (height / 2) * 0.9;

    // Top half
    let path = `M 0 ${yCenter}`;
    for (let i = 0; i < data.length; i++) {
      const x = i * xStep;
      const y = yCenter - Math.abs(data[i]) * yScale;
      path += ` L ${x} ${y}`;
    }
    path += ` L ${width} ${yCenter}`;

    // Bottom half (mirror)
    for (let i = data.length - 1; i >= 0; i--) {
      const x = i * xStep;
      const y = yCenter + Math.abs(data[i]) * yScale;
      path += ` L ${x} ${y}`;
    }
    path += ' Z';

    return path;
  }, [data, width, height]);

  return (
    <div className="inline-block">
      {label && (
        <div className="font-mono text-blueprint-cyan text-xs uppercase tracking-wider mb-2">
          {label}
        </div>
      )}
      <svg
        width={width}
        height={height}
        className="rounded-lg border border-blueprint-grid/30"
        style={{ backgroundColor }}
      >
        <defs>
          <linearGradient id="waveGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor={color} stopOpacity="0.8" />
            <stop offset="50%" stopColor={color} stopOpacity="0.4" />
            <stop offset="100%" stopColor={color} stopOpacity="0.8" />
          </linearGradient>
        </defs>

        {/* Center axis */}
        {showAxis && (
          <line
            x1="0"
            y1={height / 2}
            x2={width}
            y2={height / 2}
            stroke="rgba(0, 180, 216, 0.3)"
            strokeWidth="1"
            strokeDasharray="4 4"
          />
        )}

        {/* Filled waveform */}
        <path
          d={filledPath}
          fill="url(#waveGradient)"
          opacity="0.6"
        />

        {/* Waveform line */}
        <path
          d={pathData}
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Timestamp markers */}
        {timestamps.map((ts, i) => {
          const x = (parseFloat(ts.time) / 100) * width; // Assuming time is percentage
          return (
            <g key={i}>
              <line
                x1={x}
                y1="0"
                x2={x}
                y2={height}
                stroke="rgba(255, 180, 0, 0.6)"
                strokeWidth="1"
                strokeDasharray="2 2"
              />
              <text
                x={x + 4}
                y="12"
                fill="#fbbf24"
                fontSize="9"
                fontFamily="monospace"
              >
                {ts.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// Helper to generate sample waveform data
export function generateSampleWaveform(length: number = 200): number[] {
  const data: number[] = [];
  for (let i = 0; i < length; i++) {
    const t = i / length;
    // Mix of frequencies for realistic audio look
    const value =
      Math.sin(t * Math.PI * 20) * 0.3 +
      Math.sin(t * Math.PI * 50) * 0.2 +
      Math.sin(t * Math.PI * 120) * 0.15 +
      (Math.random() - 0.5) * 0.3;
    data.push(Math.max(-1, Math.min(1, value)));
  }
  return data;
}
