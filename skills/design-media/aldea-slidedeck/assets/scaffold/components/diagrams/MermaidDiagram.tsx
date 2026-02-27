import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

interface MermaidDiagramProps {
  chart: string;
  className?: string;
}

// Initialize mermaid with blueprint theme
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  themeVariables: {
    primaryColor: '#0d1420',
    primaryTextColor: '#e2e8f0',
    primaryBorderColor: '#00b4d8',
    lineColor: '#00b4d8',
    secondaryColor: '#1a2332',
    tertiaryColor: '#0d1420',
    background: '#0a0f1a',
    mainBkg: '#0d1420',
    nodeBorder: '#00b4d8',
    clusterBkg: '#1a233240',
    clusterBorder: '#00b4d860',
    titleColor: '#e2e8f0',
    edgeLabelBackground: '#0d1420',
    nodeTextColor: '#e2e8f0',
  },
  flowchart: {
    htmlLabels: true,
    curve: 'basis',
    padding: 15,
  },
  sequence: {
    diagramMarginX: 50,
    diagramMarginY: 10,
    actorMargin: 50,
    width: 150,
    height: 65,
    boxMargin: 10,
    boxTextMargin: 5,
    noteMargin: 10,
    messageMargin: 35,
  },
});

export function MermaidDiagram({ chart, className = '' }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const renderChart = async () => {
      if (!containerRef.current) return;

      try {
        const id = `mermaid-${Math.random().toString(36).substring(2, 11)}`;
        const { svg } = await mermaid.render(id, chart);
        setSvg(svg);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to render diagram');
        setSvg('');
      }
    };

    renderChart();
  }, [chart]);

  if (error) {
    return (
      <div className={`p-4 bg-red-900/20 border border-red-500/40 rounded-lg ${className}`}>
        <p className="text-red-400 font-mono text-sm">Diagram error: {error}</p>
        <pre className="mt-2 text-xs text-text-muted overflow-x-auto">{chart}</pre>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`flex items-center justify-center p-4 ${className}`}
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
