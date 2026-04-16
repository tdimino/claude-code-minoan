# Layout Algorithms Reference

## Layout Directions

Three primary layout directions control how the tree expands from the root node.

### Horizontal (Default)

Root on the left, children expand rightward. Best for wide, shallow trees.

```
                    ┌─────────┐
              ┌─────┤ Child A │
              │     └─────────┘
┌──────────┐  │     ┌─────────┐
│   Root   ├──┼─────┤ Child B │
└──────────┘  │     └─────────┘
              │     ┌─────────┐
              └─────┤ Child C │
                    └─────────┘
```

### Vertical

Root on top, children expand downward. Best for org charts and deep hierarchies.

```
              ┌──────────┐
              │   Root   │
              └────┬─────┘
           ┌───────┼───────┐
     ┌─────┴──┐ ┌──┴────┐ ┌┴────────┐
     │Child A │ │Child B│ │ Child C │
     └────────┘ └───────┘ └─────────┘
```

### Compact (Radial)

Root in the center, children radiate outward in all directions. Best for brainstorming and exploration.

```
                  Child D
                    │
         Child E ── Root ── Child A
                  / │ \
          Child F  Child C  Child B
```

---

## TypeScript Types

```typescript
export type LayoutDirection = 'horizontal' | 'vertical' | 'compact';

export type BranchType = 'rounded' | 'angular';

export type SpacingLevel = 'narrow' | 'default' | 'wide';

export interface LayoutConfig {
  direction: LayoutDirection;
  branchType: BranchType;
  spacing: SpacingLevel;
  /** Enable flexible layout (allow manual node positioning). */
  flexibleLayout: boolean;
}

/** Pixel values for each spacing level, per layout direction. */
export const SPACING: Record<SpacingLevel, { horizontal: number; vertical: number }> = {
  narrow:  { horizontal: 120, vertical: 60 },
  default: { horizontal: 180, vertical: 90 },
  wide:    { horizontal: 260, vertical: 130 },
};

/** Internal computed position for a node. */
export interface LayoutPosition {
  x: number;
  y: number;
  /** Whether this position was computed by auto-layout or set manually. */
  manual: boolean;
}
```

---

## Branch Types

### Rounded (Bezier Curves)

Organic, flowing connections using cubic bezier curves. Default in MindNode.

```
    Source ─────╮
                 ╰──── Target
```

**Edge path formula (horizontal layout):**

```typescript
/** Generate a rounded bezier edge path between two points. */
export function roundedEdgePath(
  sx: number, sy: number,  // source point
  tx: number, ty: number,  // target point
): string {
  const midX = (sx + tx) / 2;
  // Control points create a smooth S-curve
  return `M ${sx} ${sy} C ${midX} ${sy}, ${midX} ${ty}, ${tx} ${ty}`;
}
```

**Visual:**
```
  (sx,sy)                    (tx,ty)
    *                           *
     \                         /
      ╰── control ── control ─╯
         (midX,sy)   (midX,ty)
```

**For vertical layout**, swap the axis:

```typescript
export function roundedEdgePathVertical(
  sx: number, sy: number,
  tx: number, ty: number,
): string {
  const midY = (sy + ty) / 2;
  return `M ${sx} ${sy} C ${sx} ${midY}, ${tx} ${midY}, ${tx} ${ty}`;
}
```

### Angular (Straight Segments)

Sharp-cornered connections using orthogonal line segments.

```
    Source ──────┐
                 │
                 └────── Target
```

**Edge path formula (horizontal layout):**

```typescript
/** Generate an angular (orthogonal) edge path. */
export function angularEdgePath(
  sx: number, sy: number,
  tx: number, ty: number,
): string {
  const midX = (sx + tx) / 2;
  return `M ${sx} ${sy} L ${midX} ${sy} L ${midX} ${ty} L ${tx} ${ty}`;
}
```

**For vertical layout:**

```typescript
export function angularEdgePathVertical(
  sx: number, sy: number,
  tx: number, ty: number,
): string {
  const midY = (sy + ty) / 2;
  return `M ${sx} ${sy} L ${sx} ${midY} L ${tx} ${midY} L ${tx} ${ty}`;
}
```

### Custom Edge Component for ReactFlow

```tsx
import { BaseEdge, type EdgeProps } from '@xyflow/react';

export interface MindMapEdgeData {
  branchType: BranchType;
  direction: LayoutDirection;
}

export function MindMapEdge({
  sourceX, sourceY,
  targetX, targetY,
  data,
  ...rest
}: EdgeProps<MindMapEdgeData>) {
  const isVertical = data?.direction === 'vertical';
  const isRounded = (data?.branchType ?? 'rounded') === 'rounded';

  let path: string;
  if (isRounded) {
    path = isVertical
      ? roundedEdgePathVertical(sourceX, sourceY, targetX, targetY)
      : roundedEdgePath(sourceX, sourceY, targetX, targetY);
  } else {
    path = isVertical
      ? angularEdgePathVertical(sourceX, sourceY, targetX, targetY)
      : angularEdgePath(sourceX, sourceY, targetX, targetY);
  }

  return <BaseEdge path={path} {...rest} />;
}
```

---

## Spacing Levels

| Level | Horizontal Gap | Vertical Gap | Feel |
|-------|---------------|-------------|------|
| **Narrow** | 120px | 60px | Dense, compact, fits more on screen |
| **Default** | 180px | 90px | Balanced readability and density |
| **Wide** | 260px | 130px | Airy, presentation-ready |

Apply spacing by configuring the tree layout algorithm's `nodeSize` or `separation` parameters.

---

## D3 Radial Tree Algorithm

The compact/radial layout uses D3's `d3.tree()` with a polar coordinate transformation. This is the core algorithm for MindNode's radial view.

### Step 1: Build D3 Hierarchy

Convert flat node/edge arrays into a D3 hierarchy.

```typescript
import * as d3 from 'd3-hierarchy';
import type { MindMapNode } from './types';

interface TreeDatum {
  id: string;
  children?: TreeDatum[];
  nodeData: MindMapNodeData;
}

/** Convert flat node list to hierarchical tree datum. */
export function buildHierarchy(
  nodes: MindMapNode[],
  rootId: string,
): d3.HierarchyNode<TreeDatum> {
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));

  function buildSubtree(id: string): TreeDatum {
    const node = nodeMap.get(id)!;
    const childIds = nodes
      .filter((n) => n.data.parentId === id)
      .map((n) => n.id);

    return {
      id,
      nodeData: node.data,
      children: childIds.length > 0
        ? childIds.map((cid) => buildSubtree(cid))
        : undefined,
    };
  }

  return d3.hierarchy(buildSubtree(rootId));
}
```

### Step 2: Compute Tree Layout

```typescript
/** Compute standard (non-radial) tree layout positions. */
export function computeTreeLayout(
  root: d3.HierarchyNode<TreeDatum>,
  direction: 'horizontal' | 'vertical',
  spacing: SpacingLevel,
): Map<string, { x: number; y: number }> {
  const gap = SPACING[spacing];
  const nodeWidth = direction === 'horizontal' ? gap.horizontal : gap.vertical;
  const nodeHeight = direction === 'horizontal' ? gap.vertical : gap.horizontal;

  const treeLayout = d3.tree<TreeDatum>().nodeSize([nodeHeight, nodeWidth]);
  treeLayout(root);

  const positions = new Map<string, { x: number; y: number }>();

  root.each((node) => {
    if (direction === 'horizontal') {
      // d3.tree: x is vertical position, y is horizontal depth
      positions.set(node.data.id, { x: node.y!, y: node.x! });
    } else {
      positions.set(node.data.id, { x: node.x!, y: node.y! });
    }
  });

  return positions;
}
```

### Step 3: Polar Coordinate Transformation (Radial Layout)

Transform Cartesian tree coordinates into radial coordinates.

**Core formula:**
```
x_radial = radius * cos(angle - PI/2)
y_radial = radius * sin(angle - PI/2)
```

Where:
- `angle` = the tree's x-coordinate, scaled to `[0, 2*PI]`
- `radius` = the tree's y-coordinate (depth from root)
- The `- PI/2` rotation places the first branch at the top (12 o'clock)

```typescript
/** Compute radial tree layout positions.
 *
 *  Uses d3.tree() in a virtual space, then transforms coordinates
 *  from Cartesian to polar.
 *
 *  The x-axis of d3.tree maps to angle (theta).
 *  The y-axis of d3.tree maps to radius.
 */
export function computeRadialLayout(
  root: d3.HierarchyNode<TreeDatum>,
  spacing: SpacingLevel,
): Map<string, { x: number; y: number }> {
  const gap = SPACING[spacing];
  const radiusStep = gap.horizontal; // distance between depth levels

  // d3.tree with a circular sweep: nodeSize[0] controls angular spread
  const treeLayout = d3.tree<TreeDatum>()
    .size([2 * Math.PI, 1])          // full circle, unit radius
    .separation((a, b) =>
      (a.parent === b.parent ? 1 : 2) / a.depth
    );

  treeLayout(root);

  const positions = new Map<string, { x: number; y: number }>();

  root.each((node) => {
    if (node.depth === 0) {
      // Root stays at center
      positions.set(node.data.id, { x: 0, y: 0 });
      return;
    }

    const angle: number = node.x!;              // theta in radians [0, 2*PI]
    const radius: number = node.y! * node.depth * radiusStep;

    // Polar to Cartesian with -PI/2 rotation (first branch points up)
    const x = radius * Math.cos(angle - Math.PI / 2);
    const y = radius * Math.sin(angle - Math.PI / 2);

    positions.set(node.data.id, { x, y });
  });

  return positions;
}
```

### ASCII Diagram: Radial Coordinate System

```
                    0 (top)
                    │
                    │  angle = 0
                    │
  3π/2 ────────── ROOT ────────── π/2
  (left)           │              (right)
                   │
                   │  angle = π
                   │
                   π (bottom)

  For a node at depth=2, angle=π/4 (northeast):
    radius = depth * radiusStep = 2 * 180 = 360
    x = 360 * cos(π/4 - π/2) = 360 * cos(-π/4) = 254.6
    y = 360 * sin(π/4 - π/2) = 360 * sin(-π/4) = -254.6
                                                    ↑ negative = above center
```

### Radial Edge Paths

For radial layouts, use smooth curves that follow the radial structure.

```typescript
/** Generate a radial bezier edge path. */
export function radialEdgePath(
  sx: number, sy: number,
  tx: number, ty: number,
): string {
  // Control point at midpoint radius, averaged angle
  const smag = Math.sqrt(sx * sx + sy * sy);
  const tmag = Math.sqrt(tx * tx + ty * ty);
  const midRadius = (smag + tmag) / 2;

  // Midpoint angle
  const sAngle = Math.atan2(sy, sx);
  const tAngle = Math.atan2(ty, tx);
  const midAngle = (sAngle + tAngle) / 2;

  const cx = midRadius * Math.cos(midAngle);
  const cy = midRadius * Math.sin(midAngle);

  return `M ${sx} ${sy} Q ${cx} ${cy} ${tx} ${ty}`;
}
```

---

## Flexible Layout Algorithm

Flexible layout allows manual positioning of individual nodes while auto-layout manages the rest. Drag a node beyond a threshold to "pin" it to a manual position.

### Threshold Detection

```typescript
const MANUAL_THRESHOLD_PX = 30;

/** Determine if a drag displacement should trigger manual positioning. */
export function shouldPinNode(
  autoPosition: { x: number; y: number },
  draggedPosition: { x: number; y: number },
): boolean {
  const dx = draggedPosition.x - autoPosition.x;
  const dy = draggedPosition.y - autoPosition.y;
  return Math.sqrt(dx * dx + dy * dy) > MANUAL_THRESHOLD_PX;
}
```

### Mixed Auto + Manual Layout

```typescript
/** Apply layout to all nodes, respecting manual overrides.
 *
 *  1. Compute auto-layout positions for entire tree.
 *  2. For each node:
 *     - If node.data.manualPosition is true, keep its current position.
 *     - Otherwise, apply the auto-layout position.
 *  3. Edges are recomputed based on final positions.
 */
export function applyFlexibleLayout(
  nodes: MindMapNode[],
  direction: LayoutDirection,
  spacing: SpacingLevel,
  rootId: string,
): MindMapNode[] {
  const hierarchy = buildHierarchy(nodes, rootId);

  const autoPositions = direction === 'compact'
    ? computeRadialLayout(hierarchy, spacing)
    : computeTreeLayout(hierarchy, direction, spacing);

  return nodes.map((node) => {
    if (node.data.manualPosition) {
      // Preserve manually positioned node
      return node;
    }

    const pos = autoPositions.get(node.id);
    if (!pos) return node;

    return {
      ...node,
      position: { x: pos.x, y: pos.y },
    };
  });
}
```

### Auto-Arrange

Recalculate all auto-positioned nodes. Manually pinned nodes remain in place.

```typescript
/** Reset all non-manual nodes to auto-layout positions. */
export function autoArrange(
  nodes: MindMapNode[],
  config: LayoutConfig,
  rootId: string,
): MindMapNode[] {
  return applyFlexibleLayout(nodes, config.direction, config.spacing, rootId);
}

/** Unpin a node (return it to auto-layout). */
export function unpinNode(nodes: MindMapNode[], nodeId: string): MindMapNode[] {
  return nodes.map((n) =>
    n.id === nodeId
      ? { ...n, data: { ...n.data, manualPosition: false } }
      : n,
  );
}

/** Unpin all nodes (full auto-arrange). */
export function unpinAll(nodes: MindMapNode[]): MindMapNode[] {
  return nodes.map((n) => ({
    ...n,
    data: { ...n.data, manualPosition: false },
  }));
}
```

---

## ReactFlow Integration

### Compute Positions and Apply

```typescript
import { useCallback } from 'react';
import { useReactFlow, useNodesState, useEdgesState } from '@xyflow/react';
import type { LayoutConfig, MindMapNode } from './types';

export function useLayoutEngine(config: LayoutConfig, rootId: string) {
  const { fitView } = useReactFlow();
  const [nodes, setNodes] = useNodesState<MindMapNode>([]);
  const [edges, setEdges] = useEdgesState([]);

  /** Recompute layout and animate to new positions. */
  const relayout = useCallback(() => {
    setNodes((currentNodes) => {
      const updated = applyFlexibleLayout(
        currentNodes,
        config.direction,
        config.spacing,
        rootId,
      );
      // Defer fitView to next frame so ReactFlow measures new positions
      requestAnimationFrame(() => {
        fitView({ padding: 0.2, duration: 300 });
      });
      return updated;
    });
  }, [config, rootId, setNodes, fitView]);

  return { nodes, edges, setNodes, setEdges, relayout };
}
```

### Animated Transitions

Animate node positions when layout changes using CSS transitions.

```css
/* Apply to .react-flow__node wrapper */
.react-flow__node {
  transition: transform 300ms ease-in-out;
}

/* Disable transition during drag to avoid lag */
.react-flow__node.dragging {
  transition: none;
}
```

---

## react-d3-tree Integration

For projects using `react-d3-tree` instead of ReactFlow, the library provides built-in tree layouts.

```tsx
import Tree from 'react-d3-tree';

interface MindMapTreeProps {
  data: RawNodeDatum;
  direction: LayoutDirection;
}

export function MindMapTree({ data, direction }: MindMapTreeProps) {
  const orientation = direction === 'vertical' ? 'vertical' : 'horizontal';

  return (
    <div style={{ width: '100%', height: '100vh' }}>
      <Tree
        data={data}
        orientation={orientation}
        pathFunc="step"                  // 'diagonal' | 'elbow' | 'step' | 'straight'
        translate={{ x: 300, y: 50 }}    // initial viewport offset
        separation={{ siblings: 1.5, nonSiblings: 2 }}
        nodeSize={{ x: 200, y: 80 }}
        renderCustomNodeElement={(rd3tProps) => (
          <g>
            <rect
              width={160}
              height={40}
              x={-80}
              y={-20}
              rx={8}
              fill="var(--node-bg)"
              stroke="var(--node-border)"
            />
            <text textAnchor="middle" dy=".3em" fontSize={14}>
              {rd3tProps.nodeDatum.name}
            </text>
          </g>
        )}
      />
    </div>
  );
}
```

**react-d3-tree `pathFunc` options map to branch types:**

| BranchType | pathFunc | Visual |
|-----------|----------|--------|
| `rounded` | `'diagonal'` | Smooth bezier curves |
| `angular` | `'elbow'` or `'step'` | Orthogonal segments |

---

## Layout Algorithm Summary

| Algorithm | When to Use | Complexity | Library |
|-----------|-------------|-----------|---------|
| `d3.tree()` horizontal | Default mind map | O(n) | d3-hierarchy |
| `d3.tree()` vertical | Org charts, deep hierarchies | O(n) | d3-hierarchy |
| `d3.tree()` radial | Brainstorming, exploration | O(n) | d3-hierarchy |
| Flexible layout | User wants manual control | O(n) per relayout | Custom + d3 |
| react-d3-tree | Quick prototyping, simpler needs | Built-in | react-d3-tree |
