# Project Pilot Porting Guide -- MindNode UI

Specific guide for adding mind map capabilities to the Project Pilot codebase. Covers the current architecture, migration path for each existing component, new files needed, and a phased rollout.

---

## 1. Current Architecture Summary

### Stack
- React 18 + TypeScript + Vite (port 3000)
- @xyflow/react v12 -- graph canvas with 3 custom node types
- Zustand -- single store with 6 slices (graph, project, session, panel, selection, theme)
- Framer Motion (motion/react) -- LazyMotion with shared variants in `src/lib/motion.ts`
- Tailwind CSS 3 -- dark/light via `.dark` class + CSS custom properties in `src/index.css`
- Radix UI -- ScrollArea, Tabs, Collapsible
- react-resizable-panels -- collapsible sidebar in canvas mode

### Existing Files

| File | Purpose |
|------|---------|
| `src/App.tsx` | Entry: header, ReactFlow canvas, FocusPanel overlay. Registers `nodeTypes` (bucket, project, unknown). Builds graph from projects via `useEffect`. |
| `src/lib/store.ts` | Zustand store: 6 slices (graph, project, session, panel, selection, theme). No middleware (no immer, no persist). Uses `applyNodeChanges`/`applyEdgeChanges` from ReactFlow. |
| `src/lib/types.ts` | All TypeScript types: `Project`, `Dashboard`, `Session`, `ViewMode`, plus color constants (`PHASE_COLORS`, `BUCKET_COLORS`, `SESSION_STATUS_COLORS`). |
| `src/lib/graphBuilder.ts` | `buildNodesAndEdges()` -- converts projects + dashboard into ReactFlow nodes/edges. Static layout: buckets at fixed x positions, projects stacked vertically below. |
| `src/lib/useForceLayout.ts` | D3-force simulation for node positioning. **Currently commented out** in App.tsx (`// import { useForceLayout }`). Uses `forceSimulation`, `forceCollide`, `forceManyBody`, `forceLink`, `forceX`, `forceY`. Has drag pin/unpin handlers. |
| `src/lib/motion.ts` | Shared Framer Motion variants: `fadeVariants`, `modalPanelVariants`, `backdropVariants`, `slideLeftVariants`, `slideRightVariants`, `staggerContainerVariants`, `staggerItemVariants`, `expandVariants`. Also `DURATION` and `EASE` constants. |
| `src/components/nodes/BucketNode.tsx` | `memo()` component. Renders bucket label (TODAY/SOON/EVENTUALLY) with color + count badge. Source handle at bottom. |
| `src/components/nodes/ProjectNode.tsx` | `memo()` component. Renders project card with phase badge, status, next action clarity, unknowns count. Target handle at top, source handle at right. Uses `PHASE_COLORS`, highlights via `highlightedProjectIds` from store. |
| `src/components/nodes/UnknownNode.tsx` | `memo()` component. Renders unknown question text with HelpCircle/Beaker icon. Target handle at left, source handle at right. |
| `src/components/panels/FocusPanel.tsx` | Modal overlay for project detail. Uses Framer Motion (`modalPanelVariants`, `backdropVariants`). Shows description, next action, gate, unknowns, key areas, action buttons. Centered via `inset-x-0 mx-auto`. |
| `src/components/layout/AppShell.tsx` | View mode switching (canvas/panel). Canvas mode: PanelGroup with collapsible sidebar. Panel mode: two-column dashboard. Keyboard handler for `Cmd+B` toggle. |
| `src/index.css` | CSS custom properties for light/dark themes. ReactFlow customization (`.react-flow__*`). Custom scrollbar, selection color, reduced motion media query. |

### Key Conventions (from CLAUDE.md)

1. **No Framer Motion on ReactFlow nodes** -- RF manages `transform: translate()` on node wrappers; FM would override it
2. **All colors via CSS custom properties** -- `var(--color-*)`, never hardcode hex in components
3. **Single Zustand store** -- no prop drilling, all global state in `src/lib/store.ts`
4. **FocusPanel centering** -- `inset-x-0 mx-auto`, not `translate-x` (FM conflicts)
5. **Shadows via tokens** -- `var(--shadow-sm)`, `var(--shadow-md)`, etc.
6. **`memo()` on all node components** -- prevents unnecessary re-renders on viewport changes

---

## 2. Migration Path for Each Existing Component

### BucketNode -- Keep As-Is

**File**: `src/components/nodes/BucketNode.tsx`

No changes needed. Bucket nodes are part of the project dashboard canvas view, not the mind map. The mind map will be a separate view mode (or a separate ReactFlow instance).

**Decision**: Keep `BucketNode` in the `nodeTypes` registry alongside the new `MindMapNode`. ReactFlow only instantiates node types that appear in the nodes array; unused types have zero cost.

### ProjectNode -- Can Evolve into Shape-Variant MindMapNode

**File**: `src/components/nodes/ProjectNode.tsx`

The `ProjectNode` is a rich card with phase badge, status icon, unknowns count, and click handler. The `MindMapNode` is a simpler label-in-shape node with inline editing. These serve different purposes.

**Migration path**:
1. Keep `ProjectNode` unchanged for the project dashboard view
2. Create `MindMapNode` as a new component in `src/components/nodes/MindMapNode.tsx`
3. In the future (Phase 3), consider a "project mind map" mode that represents projects as `MindMapNode` instances with shape/color based on phase/status

### graphBuilder.ts -- Extend to Support Mind Map Layout Mode

**File**: `src/lib/graphBuilder.ts`

Currently only builds project dashboard graphs. Extend with a new function for mind map data:

```tsx
// Add to graphBuilder.ts

export function buildMindMapNodesAndEdges(
  mindMapData: MindMapData
): { initialNodes: Node[]; initialEdges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  // Root node
  nodes.push({
    id: mindMapData.root.id,
    type: 'mindmap',
    position: { x: 0, y: 0 }, // Layout will reposition
    data: {
      label: mindMapData.root.label,
      shape: mindMapData.root.shape ?? 'rounded',
      color: mindMapData.root.color ?? 'ocean',
      collapsed: false,
      depth: 0,
      parentId: null,
    },
  });

  // Recursive children
  function addChildren(parentId: string, children: MindMapNodeInput[], depth: number) {
    children.forEach((child, index) => {
      const nodeId = child.id ?? `mn-${parentId}-${index}`;
      nodes.push({
        id: nodeId,
        type: 'mindmap',
        position: { x: depth * 250, y: index * 80 }, // Rough initial position
        data: {
          label: child.label,
          shape: child.shape ?? 'rounded',
          color: child.color ?? 'ocean',
          collapsed: false,
          depth,
          parentId,
        },
      });

      edges.push({
        id: `mne-${parentId}-${nodeId}`,
        source: parentId,
        target: nodeId,
        type: 'mindmap',
      });

      if (child.children?.length) {
        addChildren(nodeId, child.children, depth + 1);
      }
    });
  }

  if (mindMapData.root.children) {
    addChildren(mindMapData.root.id, mindMapData.root.children, 1);
  }

  return { initialNodes: nodes, initialEdges: edges };
}
```

### useForceLayout.ts -- Replace/Extend with D3 Tree Layout

**File**: `src/lib/useForceLayout.ts`

This file is already commented out in `App.tsx`. The force layout is useful for the project dashboard (organic positioning with collision avoidance) but not ideal for mind maps. Mind maps need deterministic hierarchical layouts.

**Migration path**:
1. Keep `useForceLayout.ts` for potential future use with the project dashboard
2. Create `src/lib/useMindMapLayout.ts` -- a new hook that runs D3 `tree()` or `cluster()` layout

```tsx
// New file: src/lib/useMindMapLayout.ts

import { useCallback, useEffect } from 'react';
import { tree, hierarchy } from 'd3-hierarchy';
import type { Node, Edge } from '@xyflow/react';
import { useReactFlow } from '@xyflow/react';

interface UseMindMapLayoutOptions {
  direction: 'horizontal' | 'radial';
  nodeWidth?: number;
  nodeHeight?: number;
  enabled?: boolean;
}

export function useMindMapLayout(
  nodes: Node[],
  edges: Edge[],
  setNodes: (nodes: Node[]) => void,
  options: UseMindMapLayoutOptions
) {
  const { fitView } = useReactFlow();
  const { direction, nodeWidth = 220, nodeHeight = 80, enabled = true } = options;

  const recalculate = useCallback(() => {
    if (!enabled || nodes.length === 0) return;

    // Build parent-child adjacency
    const childMap = new Map<string, string[]>();
    for (const edge of edges) {
      const children = childMap.get(edge.source) ?? [];
      children.push(edge.target);
      childMap.set(edge.source, children);
    }

    // Find root
    const targets = new Set(edges.map((e) => e.target));
    const rootNode = nodes.find((n) => !targets.has(n.id));
    if (!rootNode) return;

    // Build hierarchy
    type TreeDatum = { id: string; children?: TreeDatum[] };
    function buildTree(id: string): TreeDatum {
      const children = childMap.get(id);
      return {
        id,
        children: children?.map((cid) => buildTree(cid)),
      };
    }

    const root = hierarchy(buildTree(rootNode.id));
    const layout = tree<TreeDatum>()
      .nodeSize([nodeHeight, nodeWidth])
      .separation((a, b) => (a.parent === b.parent ? 1 : 1.5));

    layout(root);

    // Map positions
    const updated = nodes.map((node) => {
      let match: { x: number; y: number } | null = null;
      root.each((d) => {
        if (d.data.id === node.id) {
          match = direction === 'horizontal'
            ? { x: d.y!, y: d.x! }  // Swap for left-to-right
            : { x: d.x!, y: d.y! };
        }
      });
      if (!match) return node;
      return { ...node, position: match };
    });

    setNodes(updated);

    requestAnimationFrame(() => {
      fitView({ padding: 0.2, duration: 400 });
    });
  }, [nodes.length, edges.length, direction, enabled, nodeWidth, nodeHeight, fitView, setNodes]);

  // Recalculate when topology changes
  useEffect(() => {
    recalculate();
  }, [recalculate]);

  return { recalculate };
}
```

### store.ts -- Add Mind Map Slice

**File**: `src/lib/store.ts`

Add a new mind map slice to the existing store. Follow the same pattern as the existing slices (graph, project, session, panel, selection, theme).

```tsx
// Add to the AppStore interface in store.ts

interface AppStore {
  // ... existing slices ...

  // Mind map slice
  mindMapNodes: Node[];
  mindMapEdges: Edge[];
  selectedMindMapNodeId: string | null;
  mindMapUndoStack: Array<{ nodes: Node[]; edges: Edge[] }>;
  mindMapRedoStack: Array<{ nodes: Node[]; edges: Edge[] }>;
  layoutDirection: 'horizontal' | 'radial';
  edgeStyle: 'bezier' | 'step' | 'straight';

  // Mind map actions
  setMindMapNodes: (nodes: Node[]) => void;
  setMindMapEdges: (edges: Edge[]) => void;
  onMindMapNodesChange: OnNodesChange;
  onMindMapEdgesChange: OnEdgesChange;
  selectMindMapNode: (id: string | null) => void;
  addChildNode: (parentId: string) => void;
  addSiblingNode: (siblingId: string) => void;
  deleteMindMapNode: (id: string) => void;
  updateMindMapNodeData: (id: string, updates: Partial<MindMapNodeData>) => void;
  cycleMindMapNodeShape: (id: string) => void;
  cycleMindMapNodeColor: (id: string) => void;
  toggleCollapse: (id: string) => void;
  setLayoutDirection: (dir: 'horizontal' | 'radial') => void;
  setEdgeStyle: (style: 'bezier' | 'step' | 'straight') => void;
  mindMapUndo: () => void;
  mindMapRedo: () => void;
}
```

**Implementation notes**:
- The existing store does **not** use `immer` middleware. Use spread-based immutable updates (same as `updateProject`, `moveProjectToBucket`, etc.)
- The existing store does **not** use `persist` middleware. Add `persist` wrapping only for the mind map slice if localStorage persistence is needed. Use `partialize` to select only mind map data for serialization.
- Prefix mind map actions to avoid name collisions with existing graph slice (e.g., `setMindMapNodes` vs `setNodes`)
- The mind map uses its own `onMindMapNodesChange` / `onMindMapEdgesChange` callbacks, separate from the project graph's `onNodesChange` / `onEdgesChange`

### index.css -- Add MindNode Theme CSS Custom Properties

**File**: `src/index.css`

Add the `--mn-*` custom properties documented in `reactflow-integration.md` Section 2 (Color Theming). Place them after the existing `--rf-*` variables in both `:root` and `.dark` blocks.

Also add mind map edge styling:

```css
/* Add to index.css */

/* MindMap edge animation */
.react-flow__edge-path--animated {
  stroke-dasharray: 5;
  animation: edge-flow 0.5s linear infinite;
}

@keyframes edge-flow {
  to { stroke-dashoffset: -10; }
}

/* MindMap node focus ring */
.mindmap-node--selected {
  box-shadow: 0 0 0 2px var(--mn-accent), var(--shadow-sm);
}
```

### FocusPanel -- Adapt for Mind Map Node Detail Editing

**File**: `src/components/panels/FocusPanel.tsx`

The current `FocusPanel` is tightly coupled to the `Project` type. For mind map nodes, create a separate `MindMapDetailPanel`:

```tsx
// New file: src/components/panels/MindMapDetailPanel.tsx

import { X } from 'lucide-react';
import { motion, useReducedMotion } from 'motion/react';
import { backdropVariants, modalPanelVariants } from '../../lib/motion';

interface MindMapDetailPanelProps {
  nodeId: string;
  onClose: () => void;
}

export function MindMapDetailPanel({ nodeId, onClose }: MindMapDetailPanelProps) {
  const nodeData = useStore((s) => {
    const node = s.mindMapNodes.find((n) => n.id === nodeId);
    return node?.data as MindMapNodeData | undefined;
  });
  const updateNodeData = useStore((s) => s.updateMindMapNodeData);
  const shouldReduceMotion = useReducedMotion();

  if (!nodeData) return null;

  return (
    <>
      <motion.div
        className="fixed inset-0 bg-black/30 backdrop-blur-[2px] z-40"
        onClick={onClose}
        {...(shouldReduceMotion ? {} : {
          variants: backdropVariants,
          initial: 'initial',
          animate: 'animate',
          exit: 'exit',
        })}
      />
      <motion.div
        className="fixed bottom-5 inset-x-0 mx-auto w-[500px] max-w-[90vw] bg-[var(--color-bg-primary)] rounded-2xl p-6 z-50 border border-[var(--color-border)]"
        style={{ boxShadow: 'var(--shadow-lg)' }}
        {...(shouldReduceMotion ? {} : {
          variants: modalPanelVariants,
          initial: 'initial',
          animate: 'animate',
          exit: 'exit',
        })}
      >
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <input
            defaultValue={nodeData.label}
            onBlur={(e) => updateNodeData(nodeId, { label: e.target.value })}
            className="text-xl font-bold text-[var(--color-text-primary)] bg-transparent outline-none w-full"
          />
          <button
            onClick={onClose}
            className="text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] transition-colors ml-2"
          >
            <X size={20} />
          </button>
        </div>

        {/* Shape and color selectors, notes, etc. */}
      </motion.div>
    </>
  );
}
```

**Key pattern**: Reuse `backdropVariants` and `modalPanelVariants` from `motion.ts`. Use `inset-x-0 mx-auto` centering (not translate-x). Use `useReducedMotion()` for accessibility.

### AppShell -- Extend Keyboard Handler

**File**: `src/components/layout/AppShell.tsx`

The current `handleKeyDown` only handles `Cmd+B` for sidebar toggle. Extend it to include mind map shortcuts when the mind map view is active:

```tsx
// In AppShell.tsx handleKeyDown callback

const handleKeyDown = useCallback(
  (e: KeyboardEvent) => {
    // Existing: Cmd+B to toggle panel
    if ((e.metaKey || e.ctrlKey) && e.key === 'b') {
      e.preventDefault();
      togglePanel();
      return;
    }

    // Mind map shortcuts (only when mind map view is active)
    if (viewMode !== 'mindmap') return;

    // Skip if user is typing in an input
    const tag = (e.target as HTMLElement)?.tagName;
    if (tag === 'INPUT' || tag === 'TEXTAREA') return;

    const selectedId = useStore.getState().selectedMindMapNodeId;
    if (!selectedId) return;

    // Delegate to mind map keyboard handler
    handleMindMapKeyDown(e, selectedId);
  },
  [togglePanel, viewMode]
);
```

**Note**: The `ViewMode` type in `types.ts` will need to be extended from `'canvas' | 'panel'` to `'canvas' | 'panel' | 'mindmap'`.

---

## 3. New Files Needed

### Core Components

| File | Description |
|------|-------------|
| `src/components/nodes/MindMapNode.tsx` | Custom ReactFlow node with shape variants, inline label editing, color theming, NodeToolbar. Must use `memo()`. Must NOT use Framer Motion. |
| `src/components/nodes/MindMapEdge.tsx` | Custom ReactFlow edge with bezier/step/straight modes and optional animation. Must use `memo()`. |
| `src/components/panels/MindMapDetailPanel.tsx` | Modal overlay for editing mind map node details (label, notes, attachments). Follows FocusPanel pattern with `backdropVariants` + `modalPanelVariants`. |
| `src/components/layout/MindMapToolbar.tsx` | NodeToolbar content: add child, change shape, change color, delete. Rendered inside `MindMapNode` via `<NodeToolbar>`. |
| `src/components/layout/MindMapControls.tsx` | Canvas-level controls: layout direction toggle (horizontal/radial), edge style selector, zoom-to-fit, export. Positioned as an overlay on the ReactFlow canvas. |

### Library / Hooks

| File | Description |
|------|-------------|
| `src/lib/useMindMapLayout.ts` | Hook that computes D3 tree/radial layout and applies positions to ReactFlow nodes. Replaces `useForceLayout` for mind map mode. |
| `src/lib/mindMapKeyboard.ts` | Keyboard handler function for mind map shortcuts (Tab, Enter, Backspace, arrows, S, C, Space, Cmd+Z). Called from `AppShell`. |
| `src/lib/mindMapShapes.ts` | Shape definitions: SVG path data, dimensions, padding for all 8 shapes (rectangle, rounded, pill, diamond, hexagon, circle, parallelogram, cloud). |

### Types (add to existing files)

| Location | Additions |
|----------|-----------|
| `src/lib/types.ts` | `MindNodeShape` type, `MindMapNodeData` interface, `MindMapEdgeStyle` type, `MindMapData` and `MindMapNodeInput` interfaces for serialization, extend `ViewMode` to include `'mindmap'` |

---

## 4. Zustand Store Additions

### New Slice: Mind Map

Add to the `AppStore` interface and the `create<AppStore>()` implementation in `store.ts`:

**State fields**:

```tsx
// Mind map slice state
mindMapNodes: Node[];               // ReactFlow nodes for the mind map
mindMapEdges: Edge[];               // ReactFlow edges for the mind map
selectedMindMapNodeId: string | null;
mindMapUndoStack: Array<{ nodes: Node[]; edges: Edge[] }>;
mindMapRedoStack: Array<{ nodes: Node[]; edges: Edge[] }>;
layoutDirection: 'horizontal' | 'radial';
edgeStyle: 'bezier' | 'step' | 'straight';
```

**Action fields**:

```tsx
// Mind map slice actions
setMindMapNodes: (nodes: Node[]) => void;
setMindMapEdges: (edges: Edge[]) => void;
onMindMapNodesChange: OnNodesChange;
onMindMapEdgesChange: OnEdgesChange;
selectMindMapNode: (id: string | null) => void;
addChildNode: (parentId: string) => void;
addSiblingNode: (siblingId: string) => void;
deleteMindMapNode: (id: string) => void;
updateMindMapNodeData: (id: string, updates: Record<string, unknown>) => void;
cycleMindMapNodeShape: (id: string) => void;
cycleMindMapNodeColor: (id: string) => void;
toggleCollapse: (id: string) => void;
setLayoutDirection: (dir: 'horizontal' | 'radial') => void;
setEdgeStyle: (style: 'bezier' | 'step' | 'straight') => void;
mindMapUndo: () => void;
mindMapRedo: () => void;
```

**Implementation pattern** -- follow existing store conventions:

```tsx
// In create<AppStore>((set, get) => ({ ... }))

// Mind map slice defaults
mindMapNodes: [],
mindMapEdges: [],
selectedMindMapNodeId: null,
mindMapUndoStack: [],
mindMapRedoStack: [],
layoutDirection: 'horizontal' as const,
edgeStyle: 'bezier' as const,

onMindMapNodesChange: (changes) => {
  set({ mindMapNodes: applyNodeChanges(changes, get().mindMapNodes) });
},

onMindMapEdgesChange: (changes) => {
  set({ mindMapEdges: applyEdgeChanges(changes, get().mindMapEdges) });
},

setMindMapNodes: (nodes) => set({ mindMapNodes: nodes }),
setMindMapEdges: (edges) => set({ mindMapEdges: edges }),

selectMindMapNode: (id) => set({ selectedMindMapNodeId: id }),

addChildNode: (parentId) => {
  const state = get();
  // Push undo snapshot
  const snapshot = {
    nodes: structuredClone(state.mindMapNodes),
    edges: structuredClone(state.mindMapEdges),
  };
  const undoStack = [...state.mindMapUndoStack, snapshot].slice(-50);

  const parent = state.mindMapNodes.find((n) => n.id === parentId);
  if (!parent) return;

  const parentData = parent.data as unknown as MindMapNodeData;
  const newId = `mn-${Date.now()}`;
  const siblingCount = state.mindMapEdges.filter((e) => e.source === parentId).length;

  set({
    mindMapNodes: [
      ...state.mindMapNodes,
      {
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
          depth: (parentData.depth ?? 0) + 1,
          parentId,
        },
      },
    ],
    mindMapEdges: [
      ...state.mindMapEdges,
      {
        id: `mne-${parentId}-${newId}`,
        source: parentId,
        target: newId,
        type: 'mindmap',
      },
    ],
    selectedMindMapNodeId: newId,
    mindMapUndoStack: undoStack,
    mindMapRedoStack: [],
  });
},

// deleteMindMapNode, updateMindMapNodeData, cycleMindMapNodeShape,
// cycleMindMapNodeColor, toggleCollapse, mindMapUndo, mindMapRedo
// follow the same snapshot-then-mutate pattern
```

### Extend ViewMode

In `types.ts`, update the `ViewMode` type:

```tsx
// Current
export type ViewMode = 'canvas' | 'panel';

// Updated
export type ViewMode = 'canvas' | 'panel' | 'mindmap';
```

Update `AppShell.tsx` and `ViewToggle` to handle the third mode.

---

## 5. CSS Custom Property Additions

Add to `src/index.css` in both `:root` and `.dark` blocks. Use the `--mn-` prefix to namespace mind map colors separately from existing `--color-*` and `--rf-*` tokens.

### Light Mode (:root)

```css
/* MindNode theme colors -- light mode */
--mn-accent: #3B82F6;

/* 6 named color palettes */
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
```

### Dark Mode (.dark)

```css
/* MindNode theme colors -- dark mode */
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
```

### Edge + Node CSS

```css
/* MindMap edge animation */
.react-flow__edge-path--animated {
  stroke-dasharray: 5;
  animation: edge-flow 0.5s linear infinite;
}

@keyframes edge-flow {
  to { stroke-dashoffset: -10; }
}

/* MindMap node shape SVG fills use the CSS custom properties above */
```

---

## 6. Animation Considerations

### Patterns to Reuse from motion.ts

| Variant | Mind Map Usage |
|---------|----------------|
| `backdropVariants` | MindMapDetailPanel backdrop |
| `modalPanelVariants` | MindMapDetailPanel entrance/exit |
| `fadeVariants` | View mode crossfade when switching to/from mind map mode |
| `staggerContainerVariants` + `staggerItemVariants` | Mind map controls panel items |
| `expandVariants` | Collapsible sections in MindMapDetailPanel |

### Framer Motion Gotchas to Avoid

1. **Never use FM on MindMapNode** -- ReactFlow positions nodes via `transform: translate(x, y)` on a wrapper div. Framer Motion's `animate`, `initial`, or `layout` props override the `transform` CSS property, breaking node positioning. Use CSS transitions for node hover effects instead.

2. **Never use FM on MindMapEdge** -- same reason. Edge paths are positioned by ReactFlow's internal SVG coordinate system.

3. **NodeToolbar is safe for FM** -- the `<NodeToolbar>` component renders outside the node's transform context, so Framer Motion animations (e.g., fade in/out) are safe there. However, the toolbar is already visibility-toggled by ReactFlow's `isVisible` prop, so FM is typically unnecessary.

4. **MindMapDetailPanel is safe for FM** -- it's a fixed-position overlay, not a ReactFlow node. Use the same pattern as `FocusPanel`: `inset-x-0 mx-auto` centering, `modalPanelVariants` for entrance, `backdropVariants` for the backdrop.

5. **MindMapControls is safe for FM** -- positioned as a fixed/absolute overlay on the canvas. Use `fadeVariants` or `slideLeftVariants` for entrance.

### CSS Transitions for Nodes (Instead of FM)

Use plain CSS transitions for node hover effects:

```css
/* In MindMapNode component -- className-based, not FM-based */
.mindmap-node {
  transition: box-shadow 150ms ease-out, transform 150ms ease-out;
}

.mindmap-node:hover {
  box-shadow: var(--shadow-md);
}
```

Or use Tailwind classes directly:

```tsx
<div className="transition-shadow duration-150 hover:shadow-md">
  {/* node content */}
</div>
```

---

## 7. Phased Migration

### Phase 1: Basic Mind Map Mode

**Goal**: Standalone mind map view with core interactions.

| Task | Files | Notes |
|------|-------|-------|
| Add `MindNodeShape` and `MindMapNodeData` types | `src/lib/types.ts` | Extend existing types file |
| Extend `ViewMode` to `'canvas' \| 'panel' \| 'mindmap'` | `src/lib/types.ts` | One-line change |
| Create `MindMapNode` component | `src/components/nodes/MindMapNode.tsx` | `memo()`, no FM, inline editing, shape SVG |
| Create `MindMapEdge` component | `src/components/nodes/MindMapEdge.tsx` | `memo()`, bezier/step/straight modes |
| Create shape definitions | `src/lib/mindMapShapes.ts` | SVG paths for 8 shapes |
| Add mind map slice to store | `src/lib/store.ts` | New state + actions (see section 4) |
| Add `--mn-*` CSS custom properties | `src/index.css` | Light + dark mode (see section 5) |
| Update `ViewToggle` for 3 modes | `src/components/layout/ViewToggle.tsx` | Add mind map icon |
| Update `AppShell` for mind map view | `src/components/layout/AppShell.tsx` | Third branch in `AnimatePresence`, mind map keyboard handler |
| Register mind map node/edge types in `App.tsx` | `src/App.tsx` | Add to `nodeTypes` and `edgeTypes` maps |
| Basic mind map canvas in `App.tsx` | `src/App.tsx` | Second `<ReactFlow>` instance or conditional rendering |

**New dependencies**: None (d3-hierarchy is already available via d3-force which is already installed).

**Verification**:
- `npx tsc --noEmit` passes
- Mind map view renders with a sample root node
- Tab creates children, Enter creates siblings, Backspace deletes
- Inline label editing works (click, type, blur to save)
- Shapes render via SVG, colors use CSS custom properties
- Dark/light theme works with `--mn-*` tokens

### Phase 2: Themes + Layout

**Goal**: Auto-layout, multiple edge styles, shape/color cycling, undo/redo.

| Task | Files | Notes |
|------|-------|-------|
| Create `useMindMapLayout` hook | `src/lib/useMindMapLayout.ts` | D3 tree + radial layout |
| Add `MindMapControls` overlay | `src/components/layout/MindMapControls.tsx` | Layout direction toggle, edge style selector, fit view |
| Implement undo/redo in store | `src/lib/store.ts` | Snapshot stack, Cmd+Z / Cmd+Shift+Z |
| Implement shape/color cycling | `src/lib/store.ts` | `S` and `C` keyboard shortcuts |
| Implement collapse/expand | `src/lib/store.ts` + `MindMapNode.tsx` | Space to toggle, hide descendants |
| Create `MindMapToolbar` component | `src/components/layout/MindMapToolbar.tsx` | NodeToolbar content (add, shape, color, delete) |
| Add arrow key navigation | `src/lib/mindMapKeyboard.ts` | Parent/child/sibling navigation |
| localStorage persistence | `src/lib/store.ts` | Persist mind map data across reloads |

**New dependencies**: `zustand/middleware` (immer + persist) -- or continue with spread-based updates.

**Verification**:
- Horizontal tree layout positions nodes correctly
- Radial layout positions nodes in a radial pattern
- Undo/redo works for all mutations (add, delete, edit, move)
- Shape cycling rotates through all 8 shapes
- Color cycling rotates through all 6 colors
- Collapse hides descendants, expand reveals them
- Arrow keys navigate the tree
- Mind map data survives page reload

### Phase 3: Full Interaction

**Goal**: Drag-to-create, MindMapDetailPanel, export, integration with project data.

| Task | Files | Notes |
|------|-------|-------|
| Drag-to-create child nodes | `App.tsx` (onConnectEnd handler) | Drag from source handle to empty canvas |
| Create `MindMapDetailPanel` | `src/components/panels/MindMapDetailPanel.tsx` | Modal overlay for rich editing (notes, attachments) |
| Export mind map as JSON / markdown | `src/lib/mindMapExport.ts` | Serialize tree to outline format |
| Import from markdown outline | `src/lib/mindMapImport.ts` | Parse indented text into tree |
| Link mind map nodes to projects | `src/lib/store.ts` | `projectId` field on `MindMapNodeData`, bidirectional navigation |
| Multi-select and bulk operations | `src/lib/store.ts` + `MindMapNode.tsx` | Shift+click multi-select, bulk delete/color/shape |
| Touch gesture support | `App.tsx` | Pinch-to-zoom, two-finger pan (ReactFlow handles this natively) |

**Verification**:
- Drag from handle to canvas creates a connected child
- Detail panel opens on double-click, supports rich editing
- Export produces valid JSON and readable markdown outline
- Import from markdown creates correct tree structure
- Linked nodes navigate between mind map and project canvas views

---

## 8. Integration Architecture

### Separate ReactFlow Instances

The mind map view should use its own `<ReactFlow>` instance, separate from the project dashboard canvas. This avoids conflicts between the two node type registries and state management:

```tsx
// In App.tsx -- conditional rendering based on viewMode

const projectNodeTypes = { bucket: BucketNode, project: ProjectNode, unknown: UnknownNode };
const mindMapNodeTypes = { mindmap: MindMapNode };
const mindMapEdgeTypes = { mindmap: MindMapEdge };

// Inside the AppShell children:
{viewMode === 'canvas' && (
  <ReactFlow
    nodes={nodes}
    edges={edges}
    nodeTypes={projectNodeTypes}
    onNodesChange={onNodesChange}
    onEdgesChange={onEdgesChange}
    onConnect={onConnect}
    onInit={onInit}
    fitView
  >
    <Background variant={BackgroundVariant.Dots} />
    <Controls />
    <MiniMap />
  </ReactFlow>
)}

{viewMode === 'mindmap' && (
  <ReactFlow
    nodes={mindMapNodes}
    edges={mindMapEdges}
    nodeTypes={mindMapNodeTypes}
    edgeTypes={mindMapEdgeTypes}
    onNodesChange={onMindMapNodesChange}
    onEdgesChange={onMindMapEdgesChange}
    onConnect={onMindMapConnect}
    fitView
  >
    <Background variant={BackgroundVariant.Dots} />
    <Controls />
    <MindMapControls />
  </ReactFlow>
)}
```

### State Isolation

Mind map state is isolated from project graph state. They share the same Zustand store but use separate state fields:

- **Project graph**: `nodes`, `edges`, `reactFlowInstance`, `onNodesChange`, `onEdgesChange`
- **Mind map**: `mindMapNodes`, `mindMapEdges`, `selectedMindMapNodeId`, `onMindMapNodesChange`, `onMindMapEdgesChange`

This prevents mind map mutations from triggering project graph re-renders and vice versa.

### Shared Infrastructure

Both views share:
- Theme (dark/light) via `theme` slice
- Panel collapse state via `panel` slice
- CSS custom properties in `index.css`
- Animation variants in `motion.ts`
- Keyboard handler infrastructure in `AppShell`
