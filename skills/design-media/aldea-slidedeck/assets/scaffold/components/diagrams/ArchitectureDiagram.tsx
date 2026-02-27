import React from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  Position,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// Custom node component with blueprint styling
function BlueprintNode({ data }: { data: { label: string; sublabel?: string; icon?: string } }) {
  return (
    <div className="px-4 py-3 bg-canvas-700/80 border border-blueprint-cyan/40 rounded-lg shadow-lg backdrop-blur-sm min-w-[120px]">
      <div className="flex items-center gap-2">
        {data.icon && <span className="text-lg">{data.icon}</span>}
        <div>
          <div className="font-mono text-sm text-text-primary font-medium">
            {data.label}
          </div>
          {data.sublabel && (
            <div className="font-mono text-xs text-text-muted mt-0.5">
              {data.sublabel}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const nodeTypes = {
  blueprint: BlueprintNode,
};

export interface ArchitectureNode {
  id: string;
  label: string;
  sublabel?: string;
  icon?: string;
  position: { x: number; y: number };
}

export interface ArchitectureEdge {
  source: string;
  target: string;
  label?: string;
  animated?: boolean;
}

interface ArchitectureDiagramProps {
  nodes: ArchitectureNode[];
  edges: ArchitectureEdge[];
  height?: number;
  showControls?: boolean;
  showMinimap?: boolean;
  fitView?: boolean;
}

export function ArchitectureDiagram({
  nodes: inputNodes,
  edges: inputEdges,
  height = 400,
  showControls = true,
  showMinimap = false,
  fitView = true,
}: ArchitectureDiagramProps) {
  const nodes: Node[] = inputNodes.map((node) => ({
    id: node.id,
    type: 'blueprint',
    position: node.position,
    data: {
      label: node.label,
      sublabel: node.sublabel,
      icon: node.icon,
    },
    sourcePosition: Position.Right,
    targetPosition: Position.Left,
  }));

  const edges: Edge[] = inputEdges.map((edge, index) => ({
    id: `e-${edge.source}-${edge.target}-${index}`,
    source: edge.source,
    target: edge.target,
    label: edge.label,
    animated: edge.animated ?? false,
    style: { stroke: '#00b4d8', strokeWidth: 2 },
    labelStyle: { fill: '#a0aec0', fontSize: 10 },
    labelBgStyle: { fill: '#0d1420', fillOpacity: 0.8 },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: '#00b4d8',
    },
  }));

  return (
    <div style={{ height }} className="w-full rounded-lg overflow-hidden border border-blueprint-grid/30">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView={fitView}
        attributionPosition="bottom-left"
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#00b4d820" gap={20} size={1} />
        {showControls && (
          <Controls
            style={{
              backgroundColor: '#0d1420',
              borderColor: '#00b4d840',
            }}
          />
        )}
        {showMinimap && (
          <MiniMap
            nodeColor="#00b4d840"
            maskColor="#0a0f1a90"
            style={{ backgroundColor: '#0d1420' }}
          />
        )}
      </ReactFlow>
    </div>
  );
}
