# ReactFlow Mind Map Integration Guide

Reference for building a mind map UI on top of @xyflow/react v12 with Zustand state management and Tailwind CSS 3. Covers official ReactFlow mind map patterns, custom node/edge components, D3 layout integration, and performance optimization.

---

## 1. Official ReactFlow Mind Map Patterns

The official ReactFlow mind map tutorial (reactflow.dev/learn/tutorials/mind-map-app-with-react-flow) demonstrates these core patterns:

### Minimal Setup

```tsx
import { ReactFlow, type Node, type Edge } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const nodeTypes = { mindmap: MindMapNode };
const edgeTypes = { mindmap: MindMapEdge };

function MindMapApp() {
  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      edgeTypes={edgeTypes}
      fitView
      // connectionLineStyle and defaultEdgeOptions for consistent edge appearance
    />
  );
}
```

### Key Design Decisions from the Official Tutorial

1. **Custom node types** -- register `MindMapNode` in `nodeTypes` so ReactFlow renders it for `type: 'mindmap'` nodes
2. **Custom edge types** -- register `MindMapEdge` for rounded branch connections
3. **NodeToolbar** -- floating toolbar appears on node selection for add/delete actions
4. **Drag-to-create** -- `onConnectEnd` handler detects drops on empty canvas and spawns a new child node at that position
5. **Zustand store** -- all node/edge state lives in a single store; ReactFlow receives `onNodesChange`/`onEdgesChange` callbacks that update the store

---

## 2. Custom MindMapNode Component

### contentEditable Text Editing

Mind map nodes need inline text editing without a separate input modal. Use `contentEditable` on a `<div>` or `<input>` element inside the node:

```tsx
import { memo, useCallback, useRef, useEffect, type KeyboardEvent } from 'react';
import { Handle, Position, NodeToolbar, type NodeProps } from '@xyflow/react';

export interface MindMapNodeData {
  id: string;
  label: string;
  shape: MindNodeShape;
  color: string;        // CSS custom property key, e.g. 'ocean'
  collapsed: boolean;
  depth: number;
}

export const MindMapNode = memo(({ id, data, selected }: NodeProps) => {
  const nodeData = data as unknown as MindMapNodeData;
  const inputRef = useRef<HTMLInputElement>(null);
  const updateNodeData = useStore((s) => s.updateMindMapNodeData);

  // Auto-focus when node is first created (label is empty)
  useEffect(() => {
    if (nodeData.label === '' && inputRef.current) {
      inputRef.current.focus();
    }
  }, [nodeData.label]);

  const handleBlur = useCallback(() => {
    const value = inputRef.current?.value ?? '';
    updateNodeData(id, { label: value });
  }, [id, updateNodeData]);

  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLInputElement>) => {
    // Enter commits the edit
    if (e.key === 'Enter') {
      e.preventDefault();
      inputRef.current?.blur();
    }
    // Tab creates a child node
    if (e.key === 'Tab') {
      e.preventDefault();
      inputRef.current?.blur();
      useStore.getState().addChildNode(id);
    }
  }, [id]);

  return (
    <>
      {/* Toolbar appears on selection */}
      <NodeToolbar isVisible={selected} position={Position.Top} align="center">
        <MindMapToolbar nodeId={id} />
      </NodeToolbar>

      {/* Node body */}
      <div
        className={clsx(
          'relative flex items-center justify-center',
          'transition-shadow duration-150',
          selected && 'ring-2 ring-[var(--mn-accent)] ring-offset-2 ring-offset-[var(--color-bg-primary)]'
        )}
        style={{
          backgroundColor: `var(--mn-${nodeData.color}-bg)`,
          borderColor: `var(--mn-${nodeData.color}-border)`,
        }}
      >
        <Handle type="target" position={Position.Left} className="w-2 h-2" />

        <input
          ref={inputRef}
          defaultValue={nodeData.label}
          onBlur={handleBlur}
          onKeyDown={handleKeyDown}
          className="bg-transparent text-center outline-none text-[var(--color-text-primary)] text-sm w-full"
          placeholder="Type..."
        />

        <Handle type="source" position={Position.Right} className="w-2 h-2" />
      </div>
    </>
  );
});

MindMapNode.displayName = 'MindMapNode';
```

### Shape Variants via SVG

Wrap node content in a shape component. Define 8 shapes: `rectangle`, `rounded`, `pill`, `diamond`, `hexagon`, `circle`, `parallelogram`, `cloud`.

```tsx
type MindNodeShape =
  | 'rectangle'
  | 'rounded'
  | 'pill'
  | 'diamond'
  | 'hexagon'
  | 'circle'
  | 'parallelogram'
  | 'cloud';

interface ShapeConfig {
  /** SVG viewBox dimensions */
  viewBox: string;
  /** SVG path d attribute */
  path: string;
  /** CSS min-width for readable labels */
  minWidth: number;
  /** CSS min-height */
  minHeight: number;
  /** Content padding inside the shape (px) */
  padding: [number, number, number, number];
}

const SHAPES: Record<MindNodeShape, ShapeConfig> = {
  rectangle: {
    viewBox: '0 0 200 60',
    path: 'M4,4 H196 V56 H4 Z',
    minWidth: 120,
    minHeight: 40,
    padding: [8, 16, 8, 16],
  },
  rounded: {
    viewBox: '0 0 200 60',
    path: 'M12,4 H188 Q196,4 196,12 V48 Q196,56 188,56 H12 Q4,56 4,48 V12 Q4,4 12,4 Z',
    minWidth: 120,
    minHeight: 40,
    padding: [8, 16, 8, 16],
  },
  pill: {
    viewBox: '0 0 200 60',
    path: 'M30,4 H170 Q196,4 196,30 Q196,56 170,56 H30 Q4,56 4,30 Q4,4 30,4 Z',
    minWidth: 100,
    minHeight: 36,
    padding: [6, 20, 6, 20],
  },
  diamond: {
    viewBox: '0 0 200 100',
    path: 'M100,4 L196,50 L100,96 L4,50 Z',
    minWidth: 140,
    minHeight: 70,
    padding: [20, 30, 20, 30],
  },
  hexagon: {
    viewBox: '0 0 200 80',
    path: 'M50,4 H150 L196,40 L150,76 H50 L4,40 Z',
    minWidth: 130,
    minHeight: 50,
    padding: [10, 24, 10, 24],
  },
  circle: {
    viewBox: '0 0 100 100',
    path: 'M50,4 A46,46 0 1,1 50,96 A46,46 0 1,1 50,4 Z',
    minWidth: 80,
    minHeight: 80,
    padding: [16, 16, 16, 16],
  },
  parallelogram: {
    viewBox: '0 0 220 60',
    path: 'M30,4 H216 L190,56 H4 Z',
    minWidth: 140,
    minHeight: 40,
    padding: [8, 24, 8, 24],
  },
  cloud: {
    viewBox: '0 0 200 100',
    path: 'M60,85 Q20,85 20,65 Q5,55 20,40 Q10,20 40,15 Q55,0 80,10 Q100,0 120,10 Q150,0 160,20 Q190,15 190,40 Q200,55 185,65 Q195,85 160,85 Z',
    minWidth: 130,
    minHeight: 65,
    padding: [18, 24, 18, 24],
  },
};
```

Render the shape as an SVG background behind the content:

```tsx
function NodeShape({ shape, color, children }: {
  shape: MindNodeShape;
  color: string;
  children: React.ReactNode;
}) {
  const config = SHAPES[shape];
  const [pt, pr, pb, pl] = config.padding;

  return (
    <div className="relative" style={{ minWidth: config.minWidth, minHeight: config.minHeight }}>
      {/* SVG shape background */}
      <svg
        viewBox={config.viewBox}
        className="absolute inset-0 w-full h-full"
        preserveAspectRatio="none"
      >
        <path
          d={config.path}
          fill={`var(--mn-${color}-bg)`}
          stroke={`var(--mn-${color}-border)`}
          strokeWidth="2"
        />
      </svg>
      {/* Content positioned over the SVG */}
      <div
        className="relative z-10 flex items-center justify-center"
        style={{ padding: `${pt}px ${pr}px ${pb}px ${pl}px` }}
      >
        {children}
      </div>
    </div>
  );
}
```

### Color Theming via CSS Custom Properties

Define MindNode theme colors alongside existing Project Pilot design tokens. Use the `--mn-` prefix to namespace mind map colors:

```css
/* Add to src/index.css -- light mode */
:root {
  --mn-accent: #3B82F6;
  --mn-ocean-bg: rgba(59, 130, 246, 0.08);
  --mn-ocean-border: rgba(59, 130, 246, 0.3);
  --mn-ocean-text: #2563EB;
  --mn-forest-bg: rgba(16, 185, 129, 0.08);
  --mn-forest-border: rgba(16, 185, 129, 0.3);
  --mn-forest-text: #059669;
  --mn-sunset-bg: rgba(245, 158, 11, 0.08);
  --mn-sunset-border: rgba(245, 158, 11, 0.3);
  --mn-sunset-text: #D97706;
  --mn-berry-bg: rgba(139, 92, 246, 0.08);
  --mn-berry-border: rgba(139, 92, 246, 0.3);
  --mn-berry-text: #7C3AED;
  --mn-ember-bg: rgba(239, 68, 68, 0.08);
  --mn-ember-border: rgba(239, 68, 68, 0.3);
  --mn-ember-text: #DC2626;
  --mn-slate-bg: rgba(107, 114, 128, 0.08);
  --mn-slate-border: rgba(107, 114, 128, 0.3);
  --mn-slate-text: #4B5563;
}

/* Dark mode */
.dark {
  --mn-accent: #60A5FA;
  --mn-ocean-bg: rgba(59, 130, 246, 0.15);
  --mn-ocean-border: rgba(96, 165, 250, 0.4);
  --mn-ocean-text: #93C5FD;
  --mn-forest-bg: rgba(16, 185, 129, 0.15);
  --mn-forest-border: rgba(52, 211, 153, 0.4);
  --mn-forest-text: #6EE7B7;
  --mn-sunset-bg: rgba(245, 158, 11, 0.15);
  --mn-sunset-border: rgba(251, 191, 36, 0.4);
  --mn-sunset-text: #FCD34D;
  --mn-berry-bg: rgba(139, 92, 246, 0.15);
  --mn-berry-border: rgba(167, 139, 250, 0.4);
  --mn-berry-text: #C4B5FD;
  --mn-ember-bg: rgba(239, 68, 68, 0.15);
  --mn-ember-border: rgba(248, 113, 113, 0.4);
  --mn-ember-text: #FCA5A5;
  --mn-slate-bg: rgba(107, 114, 128, 0.15);
  --mn-slate-border: rgba(156, 163, 175, 0.4);
  --mn-slate-text: #D1D5DB;
}
```

Available color keys: `ocean`, `forest`, `sunset`, `berry`, `ember`, `slate`. Reference them via `var(--mn-{key}-bg)`, `var(--mn-{key}-border)`, `var(--mn-{key}-text)`.

### Handle Positioning for Edges

ReactFlow handles (connection points) determine where edges attach. For horizontal tree layouts:

```tsx
{/* Target (incoming) handle on the left */}
<Handle type="target" position={Position.Left} className="w-2 h-2" />

{/* Source (outgoing) handle on the right */}
<Handle type="source" position={Position.Right} className="w-2 h-2" />
```

For radial layouts, use dynamic handle positioning based on the node's angle relative to the root:

```tsx
function getHandlePositions(parentPos: XYPosition, childPos: XYPosition) {
  const dx = childPos.x - parentPos.x;
  const dy = childPos.y - parentPos.y;
  const angle = Math.atan2(dy, dx) * (180 / Math.PI);

  // Quadrant-based handle placement
  if (angle >= -45 && angle < 45) return { source: Position.Right, target: Position.Left };
  if (angle >= 45 && angle < 135) return { source: Position.Bottom, target: Position.Top };
  if (angle >= -135 && angle < -45) return { source: Position.Top, target: Position.Bottom };
  return { source: Position.Left, target: Position.Right };
}
```

---

## 3. Custom MindMapEdge

### Rounded (Bezier) vs Angular (Step) Branch Types

```tsx
import { memo } from 'react';
import { getBezierPath, getSmoothStepPath, type EdgeProps } from '@xyflow/react';

export type MindMapEdgeStyle = 'bezier' | 'step' | 'straight';

export const MindMapEdge = memo(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style,
  data,
}: EdgeProps) => {
  const edgeStyle = (data?.edgeStyle as MindMapEdgeStyle) ?? 'bezier';

  let edgePath: string;
  let labelX: number;
  let labelY: number;

  switch (edgeStyle) {
    case 'bezier': {
      const [path, lx, ly] = getBezierPath({
        sourceX, sourceY, targetX, targetY,
        sourcePosition, targetPosition,
        curvature: 0.25,
      });
      edgePath = path;
      labelX = lx;
      labelY = ly;
      break;
    }
    case 'step': {
      const [path, lx, ly] = getSmoothStepPath({
        sourceX, sourceY, targetX, targetY,
        sourcePosition, targetPosition,
        borderRadius: 8,
      });
      edgePath = path;
      labelX = lx;
      labelY = ly;
      break;
    }
    case 'straight': {
      edgePath = `M ${sourceX} ${sourceY} L ${targetX} ${targetY}`;
      labelX = (sourceX + targetX) / 2;
      labelY = (sourceY + targetY) / 2;
      break;
    }
  }

  return (
    <g>
      <path
        id={id}
        d={edgePath}
        fill="none"
        stroke={style?.stroke ?? 'var(--rf-edge)'}
        strokeWidth={style?.strokeWidth ?? 2}
        className="react-flow__edge-path"
      />
    </g>
  );
});

MindMapEdge.displayName = 'MindMapEdge';
```

### Animated Edges for Active Connections

Use CSS `stroke-dashoffset` animation for edges connected to the selected node:

```css
/* Add to index.css */
.react-flow__edge-path--animated {
  stroke-dasharray: 5;
  animation: edge-flow 0.5s linear infinite;
}

@keyframes edge-flow {
  to { stroke-dashoffset: -10; }
}
```

Apply the class conditionally:

```tsx
<path
  className={clsx(
    'react-flow__edge-path',
    data?.animated && 'react-flow__edge-path--animated'
  )}
/>
```

---

## 4. NodeToolbar Integration

```tsx
import { NodeToolbar, Position } from '@xyflow/react';
import { Plus, Trash2, Palette, Shapes } from 'lucide-react';

interface MindMapToolbarProps {
  nodeId: string;
}

function MindMapToolbar({ nodeId }: MindMapToolbarProps) {
  const addChild = useStore((s) => s.addChildNode);
  const deleteNode = useStore((s) => s.deleteMindMapNode);
  const cycleShape = useStore((s) => s.cycleMindMapNodeShape);
  const cycleColor = useStore((s) => s.cycleMindMapNodeColor);

  return (
    <div className="flex gap-1 bg-[var(--color-bg-primary)] border border-[var(--color-border)] rounded-lg p-1 shadow-md">
      <button
        onClick={() => addChild(nodeId)}
        className="p-1.5 rounded hover:bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)]"
        title="Add child (Tab)"
      >
        <Plus size={14} />
      </button>
      <button
        onClick={() => cycleShape(nodeId)}
        className="p-1.5 rounded hover:bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)]"
        title="Change shape (S)"
      >
        <Shapes size={14} />
      </button>
      <button
        onClick={() => cycleColor(nodeId)}
        className="p-1.5 rounded hover:bg-[var(--color-bg-tertiary)] text-[var(--color-text-secondary)]"
        title="Change color (C)"
      >
        <Palette size={14} />
      </button>
      <div className="w-px bg-[var(--color-border)]" />
      <button
        onClick={() => deleteNode(nodeId)}
        className="p-1.5 rounded hover:bg-red-500/10 text-[var(--color-text-secondary)] hover:text-red-500"
        title="Delete (Backspace)"
      >
        <Trash2 size={14} />
      </button>
    </div>
  );
}
```

---

## 5. Zustand Store Pattern

### Mind Map Slice

Add a `mindMap` slice to the existing Zustand store. Follow the same pattern as the existing graph, project, session, panel, selection, and theme slices.

```tsx
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { persist } from 'zustand/middleware';
import type { Node, Edge } from '@xyflow/react';

// --- Types ---

interface MindMapNodeData {
  label: string;
  shape: MindNodeShape;
  color: string;
  collapsed: boolean;
  depth: number;
  parentId: string | null;
}

interface MindMapState {
  // Node/edge state
  mindMapNodes: Node[];
  mindMapEdges: Edge[];
  selectedMindMapNodeId: string | null;

  // Undo/redo stacks
  undoStack: Array<{ nodes: Node[]; edges: Edge[] }>;
  redoStack: Array<{ nodes: Node[]; edges: Edge[] }>;

  // Layout config
  layoutDirection: 'horizontal' | 'radial';
  edgeStyle: MindMapEdgeStyle;

  // Actions
  setMindMapNodes: (nodes: Node[]) => void;
  setMindMapEdges: (edges: Edge[]) => void;
  selectMindMapNode: (id: string | null) => void;
  addChildNode: (parentId: string) => void;
  addSiblingNode: (siblingId: string) => void;
  deleteMindMapNode: (id: string) => void;
  updateMindMapNodeData: (id: string, updates: Partial<MindMapNodeData>) => void;
  cycleMindMapNodeShape: (id: string) => void;
  cycleMindMapNodeColor: (id: string) => void;
  toggleCollapse: (id: string) => void;
  setLayoutDirection: (dir: 'horizontal' | 'radial') => void;
  setEdgeStyle: (style: MindMapEdgeStyle) => void;
  undo: () => void;
  redo: () => void;
}
```

### Undo/Redo with Snapshot Stack

Push a snapshot before every mutation. Cap stack at 50 entries:

```tsx
const MAX_UNDO = 50;

function pushUndo(state: MindMapState) {
  const snapshot = {
    nodes: structuredClone(state.mindMapNodes),
    edges: structuredClone(state.mindMapEdges),
  };
  state.undoStack.push(snapshot);
  if (state.undoStack.length > MAX_UNDO) state.undoStack.shift();
  state.redoStack = []; // Clear redo on new action
}
```

### Action Implementations

```tsx
addChildNode: (parentId) => set((state) => {
  pushUndo(state);

  const parent = state.mindMapNodes.find((n) => n.id === parentId);
  if (!parent) return;

  const parentData = parent.data as unknown as MindMapNodeData;
  const newId = `mn-${Date.now()}`;

  // Position child to the right and slightly below parent
  const siblingCount = state.mindMapEdges.filter(
    (e) => e.source === parentId
  ).length;

  const newNode: Node = {
    id: newId,
    type: 'mindmap',
    position: {
      x: parent.position.x + 250,
      y: parent.position.y + siblingCount * 80,
    },
    data: {
      label: '',
      shape: parentData.shape,
      color: parentData.color,
      collapsed: false,
      depth: parentData.depth + 1,
      parentId,
    },
  };

  const newEdge: Edge = {
    id: `mne-${parentId}-${newId}`,
    source: parentId,
    target: newId,
    type: 'mindmap',
  };

  state.mindMapNodes.push(newNode);
  state.mindMapEdges.push(newEdge);
  state.selectedMindMapNodeId = newId;
}),

deleteMindMapNode: (id) => set((state) => {
  pushUndo(state);

  // Collect all descendants (BFS)
  const toDelete = new Set<string>([id]);
  const queue = [id];
  while (queue.length > 0) {
    const current = queue.shift()!;
    for (const edge of state.mindMapEdges) {
      if (edge.source === current && !toDelete.has(edge.target)) {
        toDelete.add(edge.target);
        queue.push(edge.target);
      }
    }
  }

  state.mindMapNodes = state.mindMapNodes.filter((n) => !toDelete.has(n.id));
  state.mindMapEdges = state.mindMapEdges.filter(
    (e) => !toDelete.has(e.source) && !toDelete.has(e.target)
  );

  if (toDelete.has(state.selectedMindMapNodeId ?? '')) {
    state.selectedMindMapNodeId = null;
  }
}),

undo: () => set((state) => {
  const prev = state.undoStack.pop();
  if (!prev) return;

  state.redoStack.push({
    nodes: structuredClone(state.mindMapNodes),
    edges: structuredClone(state.mindMapEdges),
  });

  state.mindMapNodes = prev.nodes;
  state.mindMapEdges = prev.edges;
}),

redo: () => set((state) => {
  const next = state.redoStack.pop();
  if (!next) return;

  state.undoStack.push({
    nodes: structuredClone(state.mindMapNodes),
    edges: structuredClone(state.mindMapEdges),
  });

  state.mindMapNodes = next.nodes;
  state.mindMapEdges = next.edges;
}),
```

### Middleware Stack

```tsx
import { create } from 'zustand';
import { immer } from 'zustand/middleware/immer';
import { persist } from 'zustand/middleware';

export const useMindMapStore = create<MindMapState>()(
  persist(
    immer((set, get) => ({
      // ... state + actions
    })),
    {
      name: 'mindnode-mind-map',
      partialize: (state) => ({
        mindMapNodes: state.mindMapNodes,
        mindMapEdges: state.mindMapEdges,
        layoutDirection: state.layoutDirection,
        edgeStyle: state.edgeStyle,
      }),
    }
  )
);
```

**Note**: If integrating into the existing single `useStore`, add the mind map state as a new slice alongside graph, project, session, panel, selection, and theme. The existing store does not use immer middleware, so either add it or use spread-based immutable updates to match the current pattern.

---

## 6. D3 Layout to ReactFlow Position Mapping

### Horizontal Tree Layout (d3-hierarchy)

```tsx
import { tree, hierarchy, type HierarchyNode } from 'd3-hierarchy';

interface TreeNodeDatum {
  id: string;
  children?: TreeNodeDatum[];
  data: MindMapNodeData;
}

function computeTreeLayout(
  nodes: Node[],
  edges: Edge[],
  direction: 'horizontal' | 'vertical' = 'horizontal'
): Map<string, { x: number; y: number }> {
  // Build adjacency from edges
  const childMap = new Map<string, string[]>();
  for (const edge of edges) {
    const children = childMap.get(edge.source) ?? [];
    children.push(edge.target);
    childMap.set(edge.source, children);
  }

  // Find root (node with no incoming edge)
  const targets = new Set(edges.map((e) => e.target));
  const rootNode = nodes.find((n) => !targets.has(n.id));
  if (!rootNode) return new Map();

  // Build hierarchy data structure
  function buildHierarchy(nodeId: string): TreeNodeDatum {
    const node = nodes.find((n) => n.id === nodeId);
    const children = childMap.get(nodeId) ?? [];
    return {
      id: nodeId,
      data: (node?.data as unknown as MindMapNodeData) ?? {},
      children: children.length > 0
        ? children.map((cid) => buildHierarchy(cid))
        : undefined,
    };
  }

  const root = hierarchy(buildHierarchy(rootNode.id));

  // Configure tree layout
  const NODE_WIDTH = 200;
  const NODE_HEIGHT = 80;
  const treeLayout = tree<TreeNodeDatum>()
    .nodeSize(
      direction === 'horizontal'
        ? [NODE_HEIGHT, NODE_WIDTH]  // [vertical spacing, horizontal spacing]
        : [NODE_WIDTH, NODE_HEIGHT]
    )
    .separation((a, b) => (a.parent === b.parent ? 1 : 1.5));

  treeLayout(root);

  // Map d3 coordinates to ReactFlow positions
  const positions = new Map<string, { x: number; y: number }>();
  root.each((node) => {
    if (direction === 'horizontal') {
      // d3 tree: x = vertical, y = horizontal. Swap for left-to-right layout.
      positions.set(node.data.id, { x: node.y!, y: node.x! });
    } else {
      positions.set(node.data.id, { x: node.x!, y: node.y! });
    }
  });

  return positions;
}
```

### Radial Tree Layout

```tsx
import { tree, hierarchy } from 'd3-hierarchy';

function computeRadialLayout(
  nodes: Node[],
  edges: Edge[],
  radius: number = 300
): Map<string, { x: number; y: number }> {
  // Same hierarchy building as above...
  const root = hierarchy(buildHierarchy(rootNode.id));

  const treeLayout = tree<TreeNodeDatum>()
    .size([2 * Math.PI, radius])
    .separation((a, b) => (a.parent === b.parent ? 1 : 2) / a.depth);

  treeLayout(root);

  const positions = new Map<string, { x: number; y: number }>();
  root.each((node) => {
    // Convert polar to cartesian coordinates
    const angle = node.x! - Math.PI / 2; // Rotate so root is at top
    const r = node.y!;
    positions.set(node.data.id, {
      x: r * Math.cos(angle),
      y: r * Math.sin(angle),
    });
  });

  return positions;
}
```

### Apply Layout to ReactFlow Nodes

```tsx
function applyLayout(direction: 'horizontal' | 'radial') {
  const { mindMapNodes, mindMapEdges, setMindMapNodes } = useStore.getState();

  const positions = direction === 'horizontal'
    ? computeTreeLayout(mindMapNodes, mindMapEdges, 'horizontal')
    : computeRadialLayout(mindMapNodes, mindMapEdges);

  const updated = mindMapNodes.map((node) => {
    const pos = positions.get(node.id);
    if (!pos) return node;
    return { ...node, position: pos };
  });

  setMindMapNodes(updated);
}
```

### Call fitView() After Layout

```tsx
import { useReactFlow } from '@xyflow/react';

function useAutoFitView() {
  const { fitView } = useReactFlow();

  const applyLayoutAndFit = useCallback((direction: 'horizontal' | 'radial') => {
    applyLayout(direction);
    // Schedule fitView after React renders the new positions
    requestAnimationFrame(() => {
      fitView({ padding: 0.2, duration: 400 });
    });
  }, [fitView]);

  return applyLayoutAndFit;
}
```

---

## 7. Performance Patterns

### memo() on All Custom Node Components

Every custom node component must be wrapped in `memo()`. ReactFlow re-renders all visible nodes on viewport changes; `memo()` prevents unnecessary re-renders when only position changes.

```tsx
// CORRECT
export const MindMapNode = memo(({ id, data, selected }: NodeProps) => {
  // ...
});
MindMapNode.displayName = 'MindMapNode';

// WRONG -- no memo, will re-render on every viewport pan/zoom
export function MindMapNode({ id, data, selected }: NodeProps) { /* ... */ }
```

### Viewport Culling

ReactFlow automatically culls nodes outside the viewport. No additional implementation needed. For nodes with expensive renders (e.g., embedded markdown), add `onlyRenderVisibleElements` to the `<ReactFlow>` component (enabled by default in v12).

### Large Map Optimizations (100+ Nodes)

1. **Collapse subtrees** -- collapsed nodes hide all descendants, reducing DOM node count
2. **Simple node at low zoom** -- render a compact dot when zoom < 0.5:

```tsx
const MindMapNode = memo(({ id, data, selected }: NodeProps) => {
  const zoom = useStore((s) => s.reactFlowInstance?.getZoom() ?? 1);

  if (zoom < 0.5) {
    return (
      <div
        className="w-4 h-4 rounded-full"
        style={{ backgroundColor: `var(--mn-${data.color}-border)` }}
      />
    );
  }

  // Full render
  return <NodeShape shape={data.shape} color={data.color}>...</NodeShape>;
});
```

3. **Debounced layout recalculation** -- D3 layout is O(n), debounce to avoid running on every keystroke:

```tsx
import { useDebouncedCallback } from 'use-debounce';

function useAutoLayout() {
  const nodes = useStore((s) => s.mindMapNodes);
  const edges = useStore((s) => s.mindMapEdges);
  const direction = useStore((s) => s.layoutDirection);

  const recalculate = useDebouncedCallback(() => {
    applyLayout(direction);
  }, 300);

  useEffect(() => {
    recalculate();
  }, [nodes.length, edges.length, direction]);
}
```

---

## 8. Keyboard Handler

Register global keyboard shortcuts for mind map interactions. Extend the existing `AppShell` `handleKeyDown` pattern:

```tsx
const handleMindMapKeyDown = useCallback((e: KeyboardEvent) => {
  const selectedId = useStore.getState().selectedMindMapNodeId;
  if (!selectedId) return;

  // Skip if user is typing in an input/textarea
  const tag = (e.target as HTMLElement)?.tagName;
  if (tag === 'INPUT' || tag === 'TEXTAREA') return;

  switch (e.key) {
    case 'Tab': {
      e.preventDefault();
      useStore.getState().addChildNode(selectedId);
      break;
    }
    case 'Enter': {
      e.preventDefault();
      useStore.getState().addSiblingNode(selectedId);
      break;
    }
    case 'Backspace':
    case 'Delete': {
      e.preventDefault();
      useStore.getState().deleteMindMapNode(selectedId);
      break;
    }
    case 's': {
      if (!e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        useStore.getState().cycleMindMapNodeShape(selectedId);
      }
      break;
    }
    case 'c': {
      if (!e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        useStore.getState().cycleMindMapNodeColor(selectedId);
      }
      break;
    }
    case 'z': {
      if (e.metaKey || e.ctrlKey) {
        e.preventDefault();
        if (e.shiftKey) {
          useStore.getState().redo();
        } else {
          useStore.getState().undo();
        }
      }
      break;
    }
    case ' ': {
      e.preventDefault();
      useStore.getState().toggleCollapse(selectedId);
      break;
    }
    case 'ArrowRight': {
      e.preventDefault();
      // Navigate to first child
      const edges = useStore.getState().mindMapEdges;
      const childEdge = edges.find((edge) => edge.source === selectedId);
      if (childEdge) useStore.getState().selectMindMapNode(childEdge.target);
      break;
    }
    case 'ArrowLeft': {
      e.preventDefault();
      // Navigate to parent
      const edges = useStore.getState().mindMapEdges;
      const parentEdge = edges.find((edge) => edge.target === selectedId);
      if (parentEdge) useStore.getState().selectMindMapNode(parentEdge.source);
      break;
    }
    case 'ArrowDown': {
      e.preventDefault();
      // Navigate to next sibling
      navigateToSibling(selectedId, 'next');
      break;
    }
    case 'ArrowUp': {
      e.preventDefault();
      // Navigate to previous sibling
      navigateToSibling(selectedId, 'prev');
      break;
    }
  }
}, []);

function navigateToSibling(nodeId: string, direction: 'next' | 'prev') {
  const { mindMapEdges, mindMapNodes, selectMindMapNode } = useStore.getState();
  const parentEdge = mindMapEdges.find((e) => e.target === nodeId);
  if (!parentEdge) return;

  const siblings = mindMapEdges
    .filter((e) => e.source === parentEdge.source)
    .map((e) => e.target);

  const currentIndex = siblings.indexOf(nodeId);
  const nextIndex = direction === 'next'
    ? Math.min(currentIndex + 1, siblings.length - 1)
    : Math.max(currentIndex - 1, 0);

  if (nextIndex !== currentIndex) {
    selectMindMapNode(siblings[nextIndex]);
  }
}
```

### Keyboard Shortcut Summary

| Key | Action |
|-----|--------|
| `Tab` | Add child node |
| `Enter` | Add sibling node |
| `Backspace` / `Delete` | Delete node + descendants |
| `S` | Cycle shape |
| `C` | Cycle color |
| `Space` | Toggle collapse/expand |
| `Cmd+Z` | Undo |
| `Cmd+Shift+Z` | Redo |
| Arrow keys | Navigate tree (Left=parent, Right=child, Up/Down=siblings) |
| `Cmd+B` | Toggle sidebar (existing AppShell shortcut) |

---

## 9. Drag-to-Create Interaction

The official ReactFlow mind map tutorial uses `onConnectEnd` to detect when a user drags from a handle to empty canvas space, creating a new child at the drop position:

```tsx
const onConnectEnd = useCallback(
  (event: MouseEvent | TouchEvent) => {
    const target = event.target as HTMLElement;
    // Only create if dropped on the canvas pane (not on another node)
    if (!target.classList.contains('react-flow__pane')) return;

    const { screenToFlowPosition } = useStore.getState().reactFlowInstance!;

    // Get the source node from the ongoing connection
    const connectionSource = /* extract from ReactFlow internal state */;
    if (!connectionSource) return;

    const position = screenToFlowPosition({
      x: 'clientX' in event ? event.clientX : event.touches[0].clientX,
      y: 'clientY' in event ? event.clientY : event.touches[0].clientY,
    });

    useStore.getState().addChildNode(connectionSource, position);
  },
  []
);
```

Pass `onConnectEnd` to the `<ReactFlow>` component alongside the existing `onConnect` handler.

---

## 10. ReactFlow v12 API Notes

### Import Paths

```tsx
// Core
import { ReactFlow, Background, Controls, MiniMap } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

// Node components
import { Handle, Position, NodeToolbar, type NodeProps } from '@xyflow/react';

// Edge components
import { getBezierPath, getSmoothStepPath, type EdgeProps } from '@xyflow/react';

// Hooks
import { useReactFlow, useNodesState, useEdgesState } from '@xyflow/react';

// Types
import type { Node, Edge, OnNodesChange, OnEdgesChange, Connection, ReactFlowInstance, XYPosition } from '@xyflow/react';

// Utilities
import { applyNodeChanges, applyEdgeChanges, addEdge } from '@xyflow/react';
```

### Key v12 Changes from v11

- Package renamed: `reactflow` -> `@xyflow/react`
- `NodeProps` data is `Record<string, unknown>` by default -- cast via `data as unknown as YourType`
- `fitView()` accepts `{ nodes, padding, duration }` options
- `screenToFlowPosition()` replaces `project()` for coordinate conversion
- `onInit` callback receives `ReactFlowInstance` (same as before but types updated)
