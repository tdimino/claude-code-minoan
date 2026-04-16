# Interaction Patterns Reference

## Keyboard Shortcuts

### Node Creation

| Shortcut | Action | Context |
|----------|--------|---------|
| `Tab` | Create child node | Adds child to selected node |
| `Return` | Create sibling node | Adds sibling after selected node |
| `Shift+Return` | Create main node | Adds new root-level branch |
| `Cmd+Return` | Edit node title | Enters contentEditable mode |

### Navigation

| Shortcut | Action | Context |
|----------|--------|---------|
| `Arrow Up` | Select node above | Moves to previous sibling or parent |
| `Arrow Down` | Select node below | Moves to next sibling or first child |
| `Arrow Left` | Select parent node | Moves toward root |
| `Arrow Right` | Select first child | Moves away from root |

### Editing

| Shortcut | Action | Context |
|----------|--------|---------|
| `Delete` / `Backspace` | Delete node | Removes selected node and re-parents children |
| `Option+.` | Fold/unfold subtree | Toggles visibility of children |
| `Cmd+L` | Create cross-connection | Links two non-adjacent nodes |
| `Cmd+Z` | Undo | Reverts last action |
| `Cmd+Shift+Z` | Redo | Reapplies undone action |
| `Cmd+C` | Copy node | Copies node and subtree |
| `Cmd+V` | Paste node | Pastes as child of selected node |

### View

| Shortcut | Action | Context |
|----------|--------|---------|
| `Space` | Zoom to fit | Fits entire mind map in viewport |
| `Cmd+Plus` | Zoom in | Increases zoom level |
| `Cmd+Minus` | Zoom out | Decreases zoom level |
| `Cmd+1` | Mind map view | Switches to visual tree view |
| `Cmd+2` | Outline view | Switches to list/outline view |

### TypeScript Type

```typescript
export interface KeyboardShortcut {
  /** Key combination string (e.g. "Cmd+Return"). */
  keys: string;
  /** Action identifier. */
  action: string;
  /** Human-readable description. */
  description: string;
  /** Category for grouping in help UI. */
  category: 'creation' | 'navigation' | 'editing' | 'view';
  /** Whether the shortcut is active during text editing. */
  activeInEditMode: boolean;
}

export const SHORTCUTS: KeyboardShortcut[] = [
  { keys: 'Tab', action: 'createChild', description: 'Create child node', category: 'creation', activeInEditMode: false },
  { keys: 'Enter', action: 'createSibling', description: 'Create sibling node', category: 'creation', activeInEditMode: false },
  { keys: 'Shift+Enter', action: 'createMainNode', description: 'Create main node', category: 'creation', activeInEditMode: false },
  { keys: 'Meta+Enter', action: 'editTitle', description: 'Edit node title', category: 'editing', activeInEditMode: false },
  { keys: 'ArrowUp', action: 'selectAbove', description: 'Select node above', category: 'navigation', activeInEditMode: false },
  { keys: 'ArrowDown', action: 'selectBelow', description: 'Select node below', category: 'navigation', activeInEditMode: false },
  { keys: 'ArrowLeft', action: 'selectParent', description: 'Select parent', category: 'navigation', activeInEditMode: false },
  { keys: 'ArrowRight', action: 'selectChild', description: 'Select first child', category: 'navigation', activeInEditMode: false },
  { keys: 'Delete', action: 'deleteNode', description: 'Delete selected node', category: 'editing', activeInEditMode: false },
  { keys: 'Backspace', action: 'deleteNode', description: 'Delete selected node', category: 'editing', activeInEditMode: false },
  { keys: 'Alt+.', action: 'toggleFold', description: 'Fold/unfold subtree', category: 'editing', activeInEditMode: false },
  { keys: 'Meta+l', action: 'crossConnect', description: 'Create cross-connection', category: 'editing', activeInEditMode: false },
  { keys: ' ', action: 'fitView', description: 'Zoom to fit', category: 'view', activeInEditMode: false },
  { keys: 'Meta+=', action: 'zoomIn', description: 'Zoom in', category: 'view', activeInEditMode: false },
  { keys: 'Meta+-', action: 'zoomOut', description: 'Zoom out', category: 'view', activeInEditMode: false },
  { keys: 'Meta+1', action: 'mindMapView', description: 'Mind map view', category: 'view', activeInEditMode: false },
  { keys: 'Meta+2', action: 'outlineView', description: 'Outline view', category: 'view', activeInEditMode: false },
];
```

---

## Interaction Modes

```typescript
export type InteractionMode =
  | 'default'        // Normal: select, navigate, create nodes
  | 'editing'        // Inline text editing active
  | 'dragging'       // Node drag in progress
  | 'connecting'     // Cross-connection creation (Cmd+L)
  | 'quickEntry'     // Rapid sequential node creation
  | 'focusMode';     // Subtree isolation view

export interface InteractionState {
  mode: InteractionMode;
  /** Currently selected node IDs. */
  selection: SelectionState;
  /** Node being edited (in 'editing' mode). */
  editingNodeId: string | null;
  /** Source node for cross-connection (in 'connecting' mode). */
  connectingFromId: string | null;
  /** Root of focused subtree (in 'focusMode'). */
  focusRootId: string | null;
}
```

---

## Selection Model

### Selection State

```typescript
export interface SelectionState {
  /** Primary selected node (last clicked). */
  primary: string | null;
  /** All selected node IDs (for multi-select). */
  selected: Set<string>;
}
```

### Selection Behaviors

| Action | Behavior |
|--------|----------|
| **Click** | Select single node, deselect all others |
| **Shift+Click** | Add/remove node from selection (toggle) |
| **Cmd+A** | Select all nodes |
| **Click canvas** | Deselect all |
| **Arrow keys** | Move primary selection, deselect others |
| **Subtree select** | Select a node and all its descendants |

### Implementation

```typescript
import { useCallback, useState } from 'react';

export function useSelection() {
  const [selection, setSelection] = useState<SelectionState>({
    primary: null,
    selected: new Set(),
  });

  const selectNode = useCallback((nodeId: string, multi: boolean) => {
    setSelection((prev) => {
      if (multi) {
        // Toggle in multi-select
        const next = new Set(prev.selected);
        if (next.has(nodeId)) {
          next.delete(nodeId);
        } else {
          next.add(nodeId);
        }
        return { primary: nodeId, selected: next };
      }
      // Single select
      return { primary: nodeId, selected: new Set([nodeId]) };
    });
  }, []);

  const selectSubtree = useCallback(
    (nodeId: string, getDescendants: (id: string) => string[]) => {
      const descendants = getDescendants(nodeId);
      const all = new Set([nodeId, ...descendants]);
      setSelection({ primary: nodeId, selected: all });
    },
    [],
  );

  const clearSelection = useCallback(() => {
    setSelection({ primary: null, selected: new Set() });
  }, []);

  return { selection, selectNode, selectSubtree, clearSelection };
}
```

---

## Focus Mode

Focus mode isolates a subtree by hiding all nodes except the selected node, its descendants, and its ancestor chain back to root.

```
Full tree:                       Focus on "B":

    A                               A (dimmed ancestor)
   / \                              |
  B   C                             B (focus root)
 / \   \                           / \
D   E   F                         D   E
```

### Implementation

```typescript
import { useCallback, useMemo, useState } from 'react';
import type { MindMapNode } from './types';

export function useFocusMode(nodes: MindMapNode[]) {
  const [focusRootId, setFocusRootId] = useState<string | null>(null);

  const enterFocusMode = useCallback((nodeId: string) => {
    setFocusRootId(nodeId);
  }, []);

  const exitFocusMode = useCallback(() => {
    setFocusRootId(null);
  }, []);

  /** Compute which nodes are visible in focus mode. */
  const visibleNodeIds = useMemo(() => {
    if (!focusRootId) return null; // null = show all

    const nodeMap = new Map(nodes.map((n) => [n.id, n]));
    const visible = new Set<string>();

    // Add ancestors (path to root)
    let current = focusRootId;
    while (current) {
      visible.add(current);
      const node = nodeMap.get(current);
      if (!node?.data.parentId) break;
      current = node.data.parentId;
    }

    // Add all descendants of focus root
    function addDescendants(id: string) {
      visible.add(id);
      for (const node of nodes) {
        if (node.data.parentId === id) {
          addDescendants(node.id);
        }
      }
    }
    addDescendants(focusRootId);

    return visible;
  }, [focusRootId, nodes]);

  /** Filter nodes for rendering. Ancestors are marked as dimmed. */
  const focusedNodes = useMemo(() => {
    if (!visibleNodeIds) return nodes;

    // Find descendant set of focusRootId (not including ancestors)
    const descendants = new Set<string>();
    function collectDescendants(id: string) {
      descendants.add(id);
      for (const node of nodes) {
        if (node.data.parentId === id) {
          collectDescendants(node.id);
        }
      }
    }
    if (focusRootId) collectDescendants(focusRootId);

    return nodes
      .filter((n) => visibleNodeIds.has(n.id))
      .map((n) => ({
        ...n,
        // Mark ancestors as dimmed (not in descendant set, except focus root itself)
        className: descendants.has(n.id) ? '' : 'node--dimmed',
      }));
  }, [nodes, visibleNodeIds, focusRootId]);

  return {
    focusRootId,
    enterFocusMode,
    exitFocusMode,
    focusedNodes,
    isFocusActive: focusRootId !== null,
  };
}
```

**CSS for dimmed ancestor nodes:**

```css
.node--dimmed {
  opacity: 0.3;
  pointer-events: none;
}
```

---

## Drag Interactions

### Move Node (Update Position)

Standard ReactFlow drag behavior with manual position pinning.

```typescript
import { useCallback } from 'react';
import { type NodeDragHandler } from '@xyflow/react';

export function useDragPosition(
  onPinNode: (nodeId: string, position: { x: number; y: number }) => void,
) {
  const onNodeDragStop: NodeDragHandler = useCallback(
    (_event, node) => {
      // Pin node to manual position after drag
      onPinNode(node.id, node.position);
    },
    [onPinNode],
  );

  return { onNodeDragStop };
}
```

### Rewire Parent (Drag Onto New Parent)

Drag a node onto a different node to change its parent in the tree.

```
Before:                     After:
    A                          A
   / \                          \
  B   C       drag B onto C      C
 /                               / \
D                               B   (prev children of C)
                               /
                              D
```

```typescript
import { useCallback, useRef } from 'react';

interface RewireState {
  /** Node being dragged. */
  sourceId: string | null;
  /** Node being hovered over (potential new parent). */
  targetId: string | null;
}

export function useDragRewire(
  onReparent: (nodeId: string, newParentId: string) => void,
) {
  const rewireRef = useRef<RewireState>({ sourceId: null, targetId: null });

  /** Called when drag starts. */
  const onDragStart = useCallback((nodeId: string) => {
    rewireRef.current = { sourceId: nodeId, targetId: null };
  }, []);

  /** Called when dragged node hovers over another node. */
  const onDragOverNode = useCallback((hoveredNodeId: string) => {
    if (rewireRef.current.sourceId && rewireRef.current.sourceId !== hoveredNodeId) {
      rewireRef.current.targetId = hoveredNodeId;
    }
  }, []);

  /** Called when dragged node leaves a node's area. */
  const onDragLeaveNode = useCallback(() => {
    rewireRef.current.targetId = null;
  }, []);

  /** Called when drag ends. If over a valid target, rewire parent. */
  const onDragEnd = useCallback(() => {
    const { sourceId, targetId } = rewireRef.current;
    if (sourceId && targetId) {
      onReparent(sourceId, targetId);
    }
    rewireRef.current = { sourceId: null, targetId: null };
  }, [onReparent]);

  return { onDragStart, onDragOverNode, onDragLeaveNode, onDragEnd };
}
```

**Validation rules before reparenting:**
- Cannot reparent a node onto itself.
- Cannot reparent a node onto one of its own descendants (would create a cycle).
- Root node cannot be reparented.

```typescript
/** Check if newParentId is a descendant of nodeId. */
function isDescendant(
  nodeId: string,
  candidateId: string,
  getChildren: (id: string) => string[],
): boolean {
  const children = getChildren(nodeId);
  for (const childId of children) {
    if (childId === candidateId) return true;
    if (isDescendant(childId, candidateId, getChildren)) return true;
  }
  return false;
}

export function canReparent(
  nodeId: string,
  newParentId: string,
  parentId: string | null,
  getChildren: (id: string) => string[],
): boolean {
  if (nodeId === newParentId) return false;
  if (parentId === null) return false; // root
  if (isDescendant(nodeId, newParentId, getChildren)) return false;
  return true;
}
```

### Cross-Connection (Cmd+L)

Cross-connections are non-hierarchical links between any two nodes. They render as dashed curved lines.

```
    A ─── B
    │     │
    C ╌╌╌ D   <-- cross-connection (dashed)
```

```typescript
export interface CrossConnection {
  id: string;
  sourceId: string;
  targetId: string;
  /** Optional label on the connection. */
  label?: string;
}

/** Hook for creating cross-connections via Cmd+L interaction. */
export function useCrossConnect(
  onCreateConnection: (sourceId: string, targetId: string) => void,
) {
  const [connectingFrom, setConnectingFrom] = useState<string | null>(null);

  const startConnect = useCallback((sourceId: string) => {
    setConnectingFrom(sourceId);
  }, []);

  const completeConnect = useCallback(
    (targetId: string) => {
      if (connectingFrom && connectingFrom !== targetId) {
        onCreateConnection(connectingFrom, targetId);
      }
      setConnectingFrom(null);
    },
    [connectingFrom, onCreateConnection],
  );

  const cancelConnect = useCallback(() => {
    setConnectingFrom(null);
  }, []);

  return { connectingFrom, startConnect, completeConnect, cancelConnect };
}
```

**ReactFlow edge for cross-connections:**

```tsx
import { BaseEdge, getStraightPath, type EdgeProps } from '@xyflow/react';

export function CrossConnectionEdge(props: EdgeProps) {
  const [path] = getStraightPath({
    sourceX: props.sourceX,
    sourceY: props.sourceY,
    targetX: props.targetX,
    targetY: props.targetY,
  });

  return (
    <BaseEdge
      path={path}
      style={{ strokeDasharray: '6 4', stroke: 'var(--cross-connection-color)' }}
      {...props}
    />
  );
}
```

---

## Fold/Unfold Subtrees (Option+.)

Toggle visibility of a node's children. Folded nodes show a "..." indicator.

```typescript
export function useFoldToggle(
  nodes: MindMapNode[],
  setNodes: React.Dispatch<React.SetStateAction<MindMapNode[]>>,
) {
  const toggleFold = useCallback(
    (nodeId: string) => {
      setNodes((prev) =>
        prev.map((n) =>
          n.id === nodeId
            ? { ...n, data: { ...n.data, folded: !n.data.folded } }
            : n,
        ),
      );
    },
    [setNodes],
  );

  /** Get visible nodes (exclude children of folded nodes). */
  const visibleNodes = useMemo(() => {
    const foldedIds = new Set(
      nodes.filter((n) => n.data.folded).map((n) => n.id),
    );

    function isHiddenByFold(node: MindMapNode): boolean {
      let currentParentId = node.data.parentId;
      while (currentParentId) {
        if (foldedIds.has(currentParentId)) return true;
        const parent = nodes.find((n) => n.id === currentParentId);
        currentParentId = parent?.data.parentId ?? null;
      }
      return false;
    }

    return nodes.filter((n) => !isHiddenByFold(n));
  }, [nodes]);

  return { toggleFold, visibleNodes };
}
```

---

## Quick Entry Mode

Rapid sequential node creation mode. Each keystroke of Enter creates a new sibling or child, keeping the user in a flow state.

```
Quick Entry Mode:
┌──────────────────────────┐
│  > Enter ideas...        │  <-- auto-focused input
│  - First idea            │
│  - Second idea           │
│  - Third idea            │
│  [Tab to indent]         │
│  [Enter to add]          │
│  [Esc to exit]           │
└──────────────────────────┘
```

```typescript
import { useCallback, useState } from 'react';

interface QuickEntryItem {
  title: string;
  depth: number; // relative indentation level
}

export function useQuickEntry(
  onCommit: (items: QuickEntryItem[], parentId: string) => void,
) {
  const [active, setActive] = useState(false);
  const [parentId, setParentId] = useState<string | null>(null);
  const [items, setItems] = useState<QuickEntryItem[]>([]);
  const [currentDepth, setCurrentDepth] = useState(0);

  const startQuickEntry = useCallback((nodeId: string) => {
    setActive(true);
    setParentId(nodeId);
    setItems([]);
    setCurrentDepth(0);
  }, []);

  const addItem = useCallback(
    (title: string) => {
      if (!title.trim()) return;
      setItems((prev) => [...prev, { title: title.trim(), depth: currentDepth }]);
    },
    [currentDepth],
  );

  const indent = useCallback(() => {
    setCurrentDepth((d) => d + 1);
  }, []);

  const outdent = useCallback(() => {
    setCurrentDepth((d) => Math.max(0, d - 1));
  }, []);

  const commitAndExit = useCallback(() => {
    if (parentId && items.length > 0) {
      onCommit(items, parentId);
    }
    setActive(false);
    setParentId(null);
    setItems([]);
    setCurrentDepth(0);
  }, [parentId, items, onCommit]);

  const cancel = useCallback(() => {
    setActive(false);
    setParentId(null);
    setItems([]);
    setCurrentDepth(0);
  }, []);

  return {
    active,
    items,
    currentDepth,
    startQuickEntry,
    addItem,
    indent,
    outdent,
    commitAndExit,
    cancel,
  };
}
```

**Quick Entry keyboard handling:**

| Key | Action |
|-----|--------|
| `Enter` | Commit current text, create new line |
| `Tab` | Indent (increase depth) |
| `Shift+Tab` | Outdent (decrease depth) |
| `Escape` | Commit all items and exit quick entry |

---

## AI Thoughts (Brainstorming Suggestions)

Overlay UI that suggests related ideas for a selected node. The suggestions appear as ghost nodes that the user can accept or dismiss.

```
               ┌──────────┐
         ┌─────┤  Design  │
         │     └──────────┘
         │
    ╭─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─╮
    ╎     │     AI Suggestions   ╎
    ╎  ┌──┴───────┐              ╎
    ╎  │ Colors?  │  [+] [-]    ╎
    ╎  ├──────────┤              ╎
    ╎  │ Layout?  │  [+] [-]    ╎
    ╎  ├──────────┤              ╎
    ╎  │ Typography│ [+] [-]    ╎
    ╎  └──────────┘              ╎
    ╰─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─╯
```

```typescript
interface AISuggestion {
  id: string;
  title: string;
  /** Confidence score 0-1. */
  confidence: number;
}

interface AIThoughtsProps {
  nodeId: string;
  suggestions: AISuggestion[];
  onAccept: (nodeId: string, suggestion: AISuggestion) => void;
  onDismiss: (suggestionId: string) => void;
  onDismissAll: () => void;
}

export function AIThoughts({
  nodeId,
  suggestions,
  onAccept,
  onDismiss,
  onDismissAll,
}: AIThoughtsProps) {
  if (suggestions.length === 0) return null;

  return (
    <div className="ai-thoughts-overlay">
      <div className="ai-thoughts-header">
        <span>AI Suggestions</span>
        <button onClick={onDismissAll} aria-label="Dismiss all">x</button>
      </div>
      <ul className="ai-thoughts-list">
        {suggestions.map((s) => (
          <li key={s.id} className="ai-thought-item">
            <span className="ai-thought-title">{s.title}</span>
            <div className="ai-thought-actions">
              <button onClick={() => onAccept(nodeId, s)} aria-label="Accept">+</button>
              <button onClick={() => onDismiss(s.id)} aria-label="Dismiss">-</button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## Outline Synchronization

Bidirectional data binding between the mind map tree view and the outline list view. Changes in either view update the shared data model.

```
Mind Map View:              Outline View:

  ┌───────┐                 - Project
  │Project│                   - Research
  └───┬───┘                     - Interviews
      │                         - Surveys
  ┌───┴───┐                   - Design
  │Research│ ┌──────┐           - Wireframes
  └───┬───┘ │Design│
      │     └──┬───┘        [Changes sync both ways]
  ┌───┴──────┐ │
  │Interviews│ │
  └──────────┘ ┌──────────┐
               │Wireframes│
               └──────────┘
```

### Shared Data Model

```typescript
/** Single source of truth for mind map data. Both views read from and write to this. */
export interface MindMapModel {
  nodes: MindMapNodeData[];
  /** Get ordered children of a node (respects sibling order). */
  getChildren(parentId: string): MindMapNodeData[];
  /** Add a node as child of parent. */
  addNode(parentId: string, content: NodeContent): string;
  /** Remove a node and optionally re-parent its children. */
  removeNode(nodeId: string): void;
  /** Move a node to a new parent at a specific index. */
  moveNode(nodeId: string, newParentId: string, index: number): void;
  /** Update node content. */
  updateContent(nodeId: string, content: Partial<NodeContent>): void;
  /** Subscribe to changes. */
  subscribe(listener: () => void): () => void;
}
```

### Outline View Component

```tsx
import { useCallback } from 'react';
import type { MindMapModel, MindMapNodeData } from './types';

interface OutlineNodeProps {
  node: MindMapNodeData;
  model: MindMapModel;
  depth: number;
  onSelect: (nodeId: string) => void;
  selectedId: string | null;
}

function OutlineNode({ node, model, depth, onSelect, selectedId }: OutlineNodeProps) {
  const children = model.getChildren(node.id);
  const isSelected = node.id === selectedId;

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Tab' && !e.shiftKey) {
        e.preventDefault();
        // Indent: make this node a child of the previous sibling
        // Handled by model.moveNode
      }
      if (e.key === 'Tab' && e.shiftKey) {
        e.preventDefault();
        // Outdent: move this node up one level
      }
      if (e.key === 'Enter') {
        e.preventDefault();
        // Create sibling after this node
        model.addNode(node.parentId!, { title: '' });
      }
    },
    [model, node],
  );

  return (
    <div className="outline-node" style={{ paddingLeft: depth * 20 }}>
      <div
        className={`outline-item ${isSelected ? 'outline-item--selected' : ''}`}
        onClick={() => onSelect(node.id)}
        onKeyDown={handleKeyDown}
        tabIndex={0}
      >
        {children.length > 0 && (
          <button className="outline-toggle" aria-label="Toggle children">
            {node.folded ? '>' : 'v'}
          </button>
        )}
        <span className="outline-title">{node.content.title || 'Untitled'}</span>
      </div>
      {!node.folded &&
        children.map((child) => (
          <OutlineNode
            key={child.id}
            node={child}
            model={model}
            depth={depth + 1}
            onSelect={onSelect}
            selectedId={selectedId}
          />
        ))}
    </div>
  );
}
```

### Synchronization Hook

```typescript
import { useSyncExternalStore, useCallback } from 'react';

/** Hook that keeps both views in sync via the shared model. */
export function useMindMapSync(model: MindMapModel) {
  // React subscribes to model changes
  const nodes = useSyncExternalStore(
    model.subscribe,
    () => model.nodes,
  );

  const addNode = useCallback(
    (parentId: string, title: string) => {
      return model.addNode(parentId, { title });
    },
    [model],
  );

  const moveNode = useCallback(
    (nodeId: string, newParentId: string, index: number) => {
      model.moveNode(nodeId, newParentId, index);
    },
    [model],
  );

  const updateTitle = useCallback(
    (nodeId: string, title: string) => {
      model.updateContent(nodeId, { title });
    },
    [model],
  );

  return { nodes, addNode, moveNode, updateTitle };
}
```

---

## Master Keyboard Hook

Combine all keyboard shortcuts into a single hook that dispatches to the appropriate handler based on current interaction mode.

```typescript
import { useCallback, useEffect } from 'react';

interface MindMapKeyboardHandlers {
  createChild: () => void;
  createSibling: () => void;
  createMainNode: () => void;
  editTitle: () => void;
  deleteNode: () => void;
  selectAbove: () => void;
  selectBelow: () => void;
  selectParent: () => void;
  selectChild: () => void;
  toggleFold: () => void;
  startCrossConnect: () => void;
  fitView: () => void;
  zoomIn: () => void;
  zoomOut: () => void;
  switchToMindMap: () => void;
  switchToOutline: () => void;
}

export function useMindMapKeyboard(
  handlers: MindMapKeyboardHandlers,
  mode: InteractionMode,
) {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      // Skip all shortcuts during text editing (except Escape and Cmd+Return)
      if (mode === 'editing') {
        if (e.key === 'Escape') {
          // Handled by InlineEdit component
          return;
        }
        if (e.key === 'Enter' && e.metaKey) {
          e.preventDefault();
          handlers.editTitle(); // Toggle edit off
          return;
        }
        return;
      }

      const meta = e.metaKey || e.ctrlKey;
      const shift = e.shiftKey;
      const alt = e.altKey;

      // Creation shortcuts
      if (e.key === 'Tab' && !meta && !shift && !alt) {
        e.preventDefault();
        handlers.createChild();
        return;
      }
      if (e.key === 'Enter' && !meta && !shift && !alt) {
        e.preventDefault();
        handlers.createSibling();
        return;
      }
      if (e.key === 'Enter' && shift && !meta && !alt) {
        e.preventDefault();
        handlers.createMainNode();
        return;
      }
      if (e.key === 'Enter' && meta && !shift && !alt) {
        e.preventDefault();
        handlers.editTitle();
        return;
      }

      // Navigation
      if (e.key === 'ArrowUp' && !meta && !shift && !alt) {
        e.preventDefault();
        handlers.selectAbove();
        return;
      }
      if (e.key === 'ArrowDown' && !meta && !shift && !alt) {
        e.preventDefault();
        handlers.selectBelow();
        return;
      }
      if (e.key === 'ArrowLeft' && !meta && !shift && !alt) {
        e.preventDefault();
        handlers.selectParent();
        return;
      }
      if (e.key === 'ArrowRight' && !meta && !shift && !alt) {
        e.preventDefault();
        handlers.selectChild();
        return;
      }

      // Editing
      if ((e.key === 'Delete' || e.key === 'Backspace') && !meta) {
        e.preventDefault();
        handlers.deleteNode();
        return;
      }
      if (e.key === '.' && alt && !meta && !shift) {
        e.preventDefault();
        handlers.toggleFold();
        return;
      }
      if (e.key === 'l' && meta && !shift && !alt) {
        e.preventDefault();
        handlers.startCrossConnect();
        return;
      }

      // View
      if (e.key === ' ' && !meta && !shift && !alt) {
        e.preventDefault();
        handlers.fitView();
        return;
      }
      if ((e.key === '=' || e.key === '+') && meta) {
        e.preventDefault();
        handlers.zoomIn();
        return;
      }
      if (e.key === '-' && meta) {
        e.preventDefault();
        handlers.zoomOut();
        return;
      }
      if (e.key === '1' && meta && !shift && !alt) {
        e.preventDefault();
        handlers.switchToMindMap();
        return;
      }
      if (e.key === '2' && meta && !shift && !alt) {
        e.preventDefault();
        handlers.switchToOutline();
        return;
      }
    },
    [handlers, mode],
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}
```
