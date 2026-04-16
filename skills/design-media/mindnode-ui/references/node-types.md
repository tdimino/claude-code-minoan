# Node Types Reference

## Node Shapes

MindNode supports 8 node shapes. Each shape communicates a different semantic role in the mind map.

| Shape | Description | Use Case | Mermaid Equivalent |
|-------|-------------|----------|--------------------|
| **Rectangle** | Sharp-cornered box | Structured data, definitions, facts | `[text]` |
| **Rounded** | Soft-cornered box (default) | General-purpose ideas, topics | `(text)` |
| **Pill** | Fully rounded ends (stadium) | Tags, labels, short phrases | `([text])` |
| **Cloud** | Organic wavy border | Dreams, brainstorms, fuzzy ideas | `{{text}}` (rough approximation) |
| **Line** | Underline only, no border | Minimal/clean notes, subtitles | `---` (no direct equivalent) |
| **Embedded** | Inset/sunken appearance | Quoted content, references | `>text]` (rough approximation) |
| **Hexagon** | Six-sided polygon | Decision points, processes | `{text}` or `{{text}}` |
| **Octagon** | Eight-sided polygon | Warnings, stops, critical items | `[/text\\]` (rough approximation) |

---

## SVG Path Definitions

Use these path generators for ReactFlow custom node components. All functions accept `width` and `height` and return an SVG path string.

```typescript
/** Generate SVG path for each node shape. */
export const shapePaths = {
  rectangle: (w: number, h: number) =>
    `M 0 0 L ${w} 0 L ${w} ${h} L 0 ${h} Z`,

  rounded: (w: number, h: number, r = 8) =>
    `M ${r} 0 L ${w - r} 0 Q ${w} 0 ${w} ${r} L ${w} ${h - r} Q ${w} ${h} ${w - r} ${h} L ${r} ${h} Q 0 ${h} 0 ${h - r} L 0 ${r} Q 0 0 ${r} 0 Z`,

  pill: (w: number, h: number) => {
    const r = h / 2;
    return `M ${r} 0 L ${w - r} 0 A ${r} ${r} 0 0 1 ${w - r} ${h} L ${r} ${h} A ${r} ${r} 0 0 1 ${r} 0 Z`;
  },

  cloud: (w: number, h: number) => {
    const cx = w / 2, cy = h / 2;
    const rx = w / 2, ry = h / 2;
    // Cloud uses overlapping elliptical arcs to create wavy border
    const bumps = 8;
    const points: string[] = [];
    for (let i = 0; i < bumps; i++) {
      const angle = (i / bumps) * Math.PI * 2;
      const nextAngle = ((i + 1) / bumps) * Math.PI * 2;
      const midAngle = (angle + nextAngle) / 2;
      const bumpRadius = 0.15 * Math.min(w, h);
      const mx = cx + (rx + bumpRadius) * Math.cos(midAngle);
      const my = cy + (ry + bumpRadius) * Math.sin(midAngle);
      const ex = cx + rx * Math.cos(nextAngle);
      const ey = cy + ry * Math.sin(nextAngle);
      if (i === 0) {
        const sx = cx + rx * Math.cos(angle);
        const sy = cy + ry * Math.sin(angle);
        points.push(`M ${sx} ${sy}`);
      }
      points.push(`Q ${mx} ${my} ${ex} ${ey}`);
    }
    points.push('Z');
    return points.join(' ');
  },

  line: (w: number, h: number) =>
    `M 0 ${h} L ${w} ${h}`,

  embedded: (w: number, h: number, inset = 4) =>
    `M ${inset} ${inset} L ${w - inset} ${inset} L ${w - inset} ${h - inset} L ${inset} ${h - inset} Z`,

  hexagon: (w: number, h: number) => {
    const indent = w * 0.2;
    return `M ${indent} 0 L ${w - indent} 0 L ${w} ${h / 2} L ${w - indent} ${h} L ${indent} ${h} L 0 ${h / 2} Z`;
  },

  octagon: (w: number, h: number) => {
    const cx = w * 0.25, cy = h * 0.25;
    return `M ${cx} 0 L ${w - cx} 0 L ${w} ${cy} L ${w} ${h - cy} L ${w - cx} ${h} L ${cx} ${h} L 0 ${h - cy} L 0 ${cy} Z`;
  },
} as const;
```

---

## Node Anatomy

Every mind map node can contain the following content types:

| Content | Description | Required | Rendering |
|---------|-------------|----------|-----------|
| **Title** | Primary text, inline-editable | Yes | `contentEditable` div |
| **Note** | Rich text attachment (Markdown) | No | Expandable panel below node |
| **Image** | Embedded image/thumbnail | No | Rendered above title |
| **Link** | URL attachment | No | Icon + truncated URL below title |
| **Sticker** | Emoji overlay | No | Large emoji in top-right corner |
| **Visual Tag** | Colored badge/label | No | Colored pill below title |

### Content Type Definition

```typescript
interface NodeContent {
  /** Primary node text, always present. */
  title: string;
  /** Markdown note attachment. */
  note?: string;
  /** Image URL or data URI. */
  image?: string;
  /** External link URL. */
  link?: string;
  /** Emoji sticker (single emoji character). */
  sticker?: string;
  /** Visual tag with label and color. */
  tag?: {
    label: string;
    color: string; // hex color
  };
}
```

---

## TypeScript Types

```typescript
/** All 8 supported node shapes. */
export type NodeShape =
  | 'rectangle'
  | 'rounded'
  | 'pill'
  | 'cloud'
  | 'line'
  | 'embedded'
  | 'hexagon'
  | 'octagon';

/** Data payload for a mind map node in ReactFlow. */
export interface MindMapNodeData {
  /** Unique stable ID (used as ReactFlow node id). */
  id: string;
  /** Node content (title, note, image, etc.). */
  content: NodeContent;
  /** Visual shape of the node border. */
  shape: NodeShape;
  /** Theme color override (hex). Inherits from branch if unset. */
  color?: string;
  /** Whether this node's subtree is folded (children hidden). */
  folded: boolean;
  /** Whether this node has manual position override. */
  manualPosition: boolean;
  /** Depth in tree (0 = root). Used for font sizing and styling. */
  depth: number;
  /** Parent node ID. Null for root. */
  parentId: string | null;
}

/** Full ReactFlow node with MindMapNodeData. */
export type MindMapNode = Node<MindMapNodeData>;
```

---

## contentEditable Implementation

Implement inline text editing directly on the node title. Double-click or press Cmd+Return to enter edit mode.

```tsx
import { useState, useRef, useCallback, useEffect } from 'react';

interface InlineEditProps {
  value: string;
  onChange: (value: string) => void;
  /** Externally trigger edit mode (e.g. from Cmd+Return). */
  editRequested?: boolean;
  onEditComplete?: () => void;
}

export function InlineEdit({
  value,
  onChange,
  editRequested,
  onEditComplete,
}: InlineEditProps) {
  const [editing, setEditing] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Enter edit mode on double-click or external trigger
  const startEditing = useCallback(() => {
    setEditing(true);
  }, []);

  useEffect(() => {
    if (editRequested) startEditing();
  }, [editRequested, startEditing]);

  // Focus and select all text when entering edit mode
  useEffect(() => {
    if (editing && ref.current) {
      ref.current.focus();
      const range = document.createRange();
      range.selectNodeContents(ref.current);
      const sel = window.getSelection();
      sel?.removeAllRanges();
      sel?.addRange(range);
    }
  }, [editing]);

  const commitEdit = useCallback(() => {
    if (ref.current) {
      const newValue = ref.current.textContent ?? '';
      if (newValue !== value) {
        onChange(newValue);
      }
    }
    setEditing(false);
    onEditComplete?.();
  }, [value, onChange, onEditComplete]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        commitEdit();
      }
      if (e.key === 'Escape') {
        // Revert
        if (ref.current) ref.current.textContent = value;
        setEditing(false);
        onEditComplete?.();
      }
      // Stop propagation so keyboard shortcuts don't fire during editing
      e.stopPropagation();
    },
    [commitEdit, value, onEditComplete],
  );

  return (
    <div
      ref={ref}
      contentEditable={editing}
      suppressContentEditableWarning
      onDoubleClick={startEditing}
      onBlur={commitEdit}
      onKeyDown={editing ? handleKeyDown : undefined}
      className={`node-title ${editing ? 'node-title--editing' : ''}`}
      // Prevent ReactFlow drag while editing
      data-no-drag={editing ? 'true' : undefined}
    >
      {value}
    </div>
  );
}
```

**Key considerations:**
- Set `data-no-drag` during editing to prevent ReactFlow from intercepting mouse events.
- `stopPropagation()` on keydown events to prevent mind map keyboard shortcuts from firing.
- Commit on Enter (single line), revert on Escape, commit on blur.

---

## Node Well Interaction

The Node Well is a plus button that appears on hover or selection, providing one-click child node creation.

```
                      +-----------+
                      | Main Idea |
                      +-----------+
                            |
                           [+]  <-- Node Well (appears on hover)
                            |
                      +-----------+
                      | New Child |  <-- Created on click
                      +-----------+
```

### Implementation Pattern

```tsx
import { useCallback, useState } from 'react';

interface NodeWellProps {
  nodeId: string;
  /** Position relative to parent node. */
  position: { x: number; y: number };
  onCreateChild: (parentId: string) => void;
}

export function NodeWell({ nodeId, position, onCreateChild }: NodeWellProps) {
  return (
    <button
      className="node-well"
      style={{
        position: 'absolute',
        left: position.x,
        top: position.y,
        transform: 'translate(-50%, -50%)',
      }}
      onClick={() => onCreateChild(nodeId)}
      aria-label="Add child node"
    >
      <svg width="20" height="20" viewBox="0 0 20 20">
        <circle cx="10" cy="10" r="9" fill="var(--well-bg)" stroke="var(--well-border)" />
        <line x1="10" y1="5" x2="10" y2="15" stroke="var(--well-icon)" strokeWidth="2" />
        <line x1="5" y1="10" x2="15" y2="10" stroke="var(--well-icon)" strokeWidth="2" />
      </svg>
    </button>
  );
}

/** Hook to manage Node Well visibility and child creation. */
export function useNodeWell(
  onAddNode: (parentId: string) => void,
) {
  const [activeWellNodeId, setActiveWellNodeId] = useState<string | null>(null);

  const showWell = useCallback((nodeId: string) => {
    setActiveWellNodeId(nodeId);
  }, []);

  const hideWell = useCallback(() => {
    setActiveWellNodeId(null);
  }, []);

  const createChild = useCallback(
    (parentId: string) => {
      onAddNode(parentId);
      // Keep well visible on the newly created node (optional UX choice)
    },
    [onAddNode],
  );

  return { activeWellNodeId, showWell, hideWell, createChild };
}
```

**Trigger logic:**
- Show Node Well when a node is hovered for 300ms or when selected.
- Position it at the bottom center of the node (for vertical layout) or right center (for horizontal layout).
- Hide on mouse leave with a short delay (150ms) to allow clicking the button.

---

## Node Sizing

### Auto-Width Algorithm

Nodes auto-size based on content width. Measure title text, then apply min/max constraints.

```typescript
/** Minimum and maximum node dimensions by depth. */
const SIZE_CONSTRAINTS = {
  root:    { minWidth: 120, maxWidth: 400, minHeight: 40 },
  branch:  { minWidth: 80,  maxWidth: 300, minHeight: 32 },
  leaf:    { minWidth: 60,  maxWidth: 250, minHeight: 28 },
} as const;

type DepthCategory = keyof typeof SIZE_CONSTRAINTS;

function getDepthCategory(depth: number): DepthCategory {
  if (depth === 0) return 'root';
  if (depth <= 2) return 'branch';
  return 'leaf';
}

/** Compute node dimensions from content.
 *  Uses a hidden canvas for text measurement. */
export function computeNodeSize(
  content: NodeContent,
  depth: number,
  fontSize: number,
): { width: number; height: number } {
  const category = getDepthCategory(depth);
  const constraints = SIZE_CONSTRAINTS[category];

  // Measure title width using canvas
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d')!;
  ctx.font = `${fontSize}px -apple-system, BlinkMacSystemFont, sans-serif`;
  const titleMetrics = ctx.measureText(content.title);
  const titleWidth = titleMetrics.width;

  // Horizontal padding: 24px each side
  const padding = 48;
  let width = Math.ceil(titleWidth + padding);

  // Clamp to constraints
  width = Math.max(constraints.minWidth, Math.min(constraints.maxWidth, width));

  // Height: base + optional image + optional tag
  let height = constraints.minHeight;
  if (content.image) height += 60; // thumbnail height
  if (content.tag) height += 22;   // tag badge height
  if (content.link) height += 18;  // link row height

  return { width, height };
}
```

### Manual Resize Handle

Allow users to manually resize nodes by dragging a handle in the bottom-right corner. Set `manualPosition: true` on the node data when the user resizes.

```tsx
import { useCallback, useRef } from 'react';

interface ResizeHandleProps {
  onResize: (width: number, height: number) => void;
  minWidth?: number;
  minHeight?: number;
}

export function ResizeHandle({
  onResize,
  minWidth = 60,
  minHeight = 28,
}: ResizeHandleProps) {
  const startRef = useRef<{ x: number; y: number; w: number; h: number } | null>(null);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      e.preventDefault();
      const parentEl = (e.target as HTMLElement).closest('.mind-map-node') as HTMLElement;
      if (!parentEl) return;
      const rect = parentEl.getBoundingClientRect();
      startRef.current = { x: e.clientX, y: e.clientY, w: rect.width, h: rect.height };

      const handleMouseMove = (ev: MouseEvent) => {
        if (!startRef.current) return;
        const dx = ev.clientX - startRef.current.x;
        const dy = ev.clientY - startRef.current.y;
        const newW = Math.max(minWidth, startRef.current.w + dx);
        const newH = Math.max(minHeight, startRef.current.h + dy);
        onResize(newW, newH);
      };

      const handleMouseUp = () => {
        startRef.current = null;
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };

      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    },
    [onResize, minWidth, minHeight],
  );

  return (
    <div
      className="resize-handle"
      onMouseDown={handleMouseDown}
      style={{
        position: 'absolute',
        right: 0,
        bottom: 0,
        width: 12,
        height: 12,
        cursor: 'nwse-resize',
      }}
    />
  );
}
```

---

## Mermaid Shape Cross-Reference

Map MindNode shapes to Mermaid syntax for diagram export/import.

| MindNode Shape | Mermaid Syntax | Mermaid Name |
|----------------|---------------|--------------|
| Rectangle | `A[text]` | Square/box |
| Rounded | `A(text)` | Rounded box |
| Pill | `A([text])` | Stadium |
| Cloud | `A{{text}}` | Double-brace (closest) |
| Hexagon | `A{text}` | Rhombus / `{{text}}` hexagon |
| Octagon | `A[/text\\]` | Parallelogram (approximate) |
| Line | *No equivalent* | Use `---` styling |
| Embedded | *No equivalent* | Use subgraph |

---

## React Component: Shape-Variant Custom Node

Complete ReactFlow custom node component that renders all 8 shapes.

```tsx
import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { MindMapNodeData, NodeShape } from './types';
import { shapePaths } from './shape-paths';
import { InlineEdit } from './InlineEdit';
import { NodeWell } from './NodeWell';
import { ResizeHandle } from './ResizeHandle';

/** Font size decreases with depth. */
function fontSizeForDepth(depth: number): number {
  if (depth === 0) return 18;
  if (depth === 1) return 15;
  if (depth === 2) return 13;
  return 12;
}

export const MindMapNode = memo(function MindMapNode({
  data,
  selected,
}: NodeProps<MindMapNodeData>) {
  const { content, shape, color, depth, folded } = data;
  const fontSize = fontSizeForDepth(depth);
  const { width, height } = computeNodeSize(content, depth, fontSize);

  return (
    <div
      className={`mind-map-node mind-map-node--${shape} ${selected ? 'selected' : ''}`}
      style={{ width, minHeight: height }}
    >
      {/* Shape background via SVG */}
      <svg
        className="node-shape-bg"
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{ position: 'absolute', top: 0, left: 0 }}
      >
        <path
          d={shapePaths[shape](width, height)}
          fill={color ?? 'var(--node-bg)'}
          stroke="var(--node-border)"
          strokeWidth={selected ? 2 : 1}
        />
      </svg>

      {/* Content layer */}
      <div className="node-content" style={{ position: 'relative', fontSize }}>
        {content.image && (
          <img src={content.image} alt="" className="node-image" />
        )}

        {content.sticker && (
          <span className="node-sticker">{content.sticker}</span>
        )}

        <InlineEdit
          value={content.title}
          onChange={(newTitle) => {
            // Update node data through ReactFlow state
            // Handled by parent via onNodesChange or custom callback
          }}
        />

        {content.link && (
          <a href={content.link} className="node-link" target="_blank" rel="noopener">
            {new URL(content.link).hostname}
          </a>
        )}

        {content.tag && (
          <span
            className="node-tag"
            style={{ backgroundColor: content.tag.color }}
          >
            {content.tag.label}
          </span>
        )}
      </div>

      {/* Folded indicator */}
      {folded && <span className="fold-indicator">...</span>}

      {/* Handles for edges */}
      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />

      {/* Resize handle (visible on selection) */}
      {selected && (
        <ResizeHandle
          onResize={(w, h) => {
            // Update node dimensions through state
          }}
        />
      )}
    </div>
  );
});
```

**Register the custom node type with ReactFlow:**

```tsx
import { ReactFlow } from '@xyflow/react';
import { MindMapNode } from './MindMapNode';

const nodeTypes = { mindmap: MindMapNode };

function MindMap() {
  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      nodeTypes={nodeTypes}
      /* ... */
    />
  );
}
```
