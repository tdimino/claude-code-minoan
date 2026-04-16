# Canvas and Views System

Reference for implementing MindNode's dual-view architecture (mind map + outline), canvas rendering, connections, visual annotations, and export pipeline. Adapted for React + ReactFlow + Tailwind CSS 3.

---

## Dual View Architecture

### Overview

MindNode provides two synchronized views of the same data:

| View | Shortcut | Purpose | Primary Interaction |
|------|----------|---------|-------------------|
| **Mind Map** | `Cmd+1` | Spatial/visual thinking — nodes on a 2D canvas | Drag, zoom, pan, connect |
| **Outline** | `Cmd+2` | Linear/hierarchical structure — collapsible tree | Type, indent, reorder |

Both views read from and write to the same underlying data model. Changes in one view reflect immediately in the other.

### Data Model (Single Source of Truth)

```ts
interface MindMapNode {
  id: string;
  parentId: string | null;
  label: string;
  notes?: string;
  /** Position on canvas (mind map view only, not used in outline) */
  position: { x: number; y: number };
  /** Collapsed state (applies to both views) */
  collapsed: boolean;
  /** Visual annotations */
  tags: NodeTag[];
  stickers: NodeSticker[];
  /** Branch index: which Level 1 ancestor does this node descend from?
      Used for theme color resolution. Set automatically. */
  branchIndex: number;
  /** Depth in the tree. 0 = root. Set automatically. */
  depth: number;
  /** Child ordering (index among siblings) */
  sortOrder: number;
}

interface MindMapEdge {
  id: string;
  source: string;
  target: string;
  type: 'parent-child' | 'cross-connection';
  /** Only for cross-connections */
  label?: string;
  style?: {
    stroke?: string;
    strokeDasharray?: string;
    strokeWidth?: number;
  };
}

interface MindMapDocument {
  id: string;
  title: string;
  nodes: Map<string, MindMapNode>;
  edges: MindMapEdge[];
  /** Canvas settings */
  canvas: CanvasSettings;
  /** Active theme ID */
  themeId: string;
}
```

### View Synchronization

Implement bidirectional sync through a shared Zustand store. Both views subscribe to the same node/edge state and dispatch the same actions.

```ts
interface ViewSlice {
  activeView: 'mindmap' | 'outline';
  setActiveView: (view: 'mindmap' | 'outline') => void;

  /** Shared selection — selecting a node in one view highlights it in the other */
  selectedNodeIds: Set<string>;
  selectNodes: (ids: string[]) => void;
  clearSelection: () => void;

  /** Focus a specific node — scrolls/zooms to it in both views */
  focusedNodeId: string | null;
  focusNode: (id: string) => void;
}
```

### View Toggle Component

```tsx
function ViewToggle() {
  const { activeView, setActiveView } = useViewStore();

  return (
    <div className="flex rounded-[var(--mn-radius-md)] border border-[var(--mn-border)]
                    bg-[var(--mn-bg-secondary)] p-0.5">
      <button
        onClick={() => setActiveView('mindmap')}
        className={`flex items-center gap-1.5 rounded-[var(--mn-radius-sm)] px-3 py-1.5
                    text-xs font-medium transition-all duration-150
                    ${activeView === 'mindmap'
                      ? 'bg-white text-[var(--mn-text-primary)] shadow-sm'
                      : 'text-[var(--mn-text-muted)] hover:text-[var(--mn-text-secondary)]'
                    }`}
      >
        <GridIcon className="h-3.5 w-3.5" />
        Mind Map
        <kbd className="ml-1 text-[10px] opacity-50">1</kbd>
      </button>
      <button
        onClick={() => setActiveView('outline')}
        className={`flex items-center gap-1.5 rounded-[var(--mn-radius-sm)] px-3 py-1.5
                    text-xs font-medium transition-all duration-150
                    ${activeView === 'outline'
                      ? 'bg-white text-[var(--mn-text-primary)] shadow-sm'
                      : 'text-[var(--mn-text-muted)] hover:text-[var(--mn-text-secondary)]'
                    }`}
      >
        <ListIcon className="h-3.5 w-3.5" />
        Outline
        <kbd className="ml-1 text-[10px] opacity-50">2</kbd>
      </button>
    </div>
  );
}
```

### Keyboard Shortcut Registration

```ts
useEffect(() => {
  const handler = (e: KeyboardEvent) => {
    if (e.metaKey || e.ctrlKey) {
      if (e.key === '1') { e.preventDefault(); setActiveView('mindmap'); }
      if (e.key === '2') { e.preventDefault(); setActiveView('outline'); }
    }
  };
  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}, [setActiveView]);
```

---

## Canvas System

### Canvas Settings

```ts
interface CanvasSettings {
  /** Background color (from theme or custom override) */
  backgroundColor: string;
  /** Background pattern */
  backgroundPattern: 'none' | 'dots' | 'grid' | 'lines';
  /** Pattern color — typically subtle gray */
  patternColor: string;
  /** Pattern spacing in pixels */
  patternSpacing: number;
  /** Pattern dot/line size */
  patternSize: number;
  /** Show minimap */
  showMinimap: boolean;
  /** Minimap position */
  minimapPosition: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right';
  /** Snap to grid */
  snapToGrid: boolean;
  /** Grid snap size */
  snapSize: number;
}

const DEFAULT_CANVAS: CanvasSettings = {
  backgroundColor: 'var(--mn-canvas-bg)',
  backgroundPattern: 'dots',
  patternColor: 'rgba(0, 0, 0, 0.06)',
  patternSpacing: 24,
  patternSize: 1.5,
  showMinimap: true,
  minimapPosition: 'bottom-right',
  snapToGrid: false,
  snapSize: 16,
};
```

### Background Patterns

Implement canvas backgrounds as SVG patterns within the ReactFlow container.

#### Dot Pattern

```tsx
function DotBackground({ spacing, size, color }: {
  spacing: number; size: number; color: string;
}) {
  return (
    <svg className="absolute inset-0 h-full w-full">
      <defs>
        <pattern
          id="dot-pattern"
          x="0" y="0"
          width={spacing} height={spacing}
          patternUnits="userSpaceOnUse"
        >
          <circle cx={spacing / 2} cy={spacing / 2} r={size} fill={color} />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#dot-pattern)" />
    </svg>
  );
}
```

#### Grid Pattern

```tsx
function GridBackground({ spacing, size, color }: {
  spacing: number; size: number; color: string;
}) {
  return (
    <svg className="absolute inset-0 h-full w-full">
      <defs>
        <pattern
          id="grid-pattern"
          x="0" y="0"
          width={spacing} height={spacing}
          patternUnits="userSpaceOnUse"
        >
          <path
            d={`M ${spacing} 0 L 0 0 0 ${spacing}`}
            fill="none" stroke={color} strokeWidth={size}
          />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#grid-pattern)" />
    </svg>
  );
}
```

#### Lines Pattern (horizontal only)

```tsx
function LinesBackground({ spacing, size, color }: {
  spacing: number; size: number; color: string;
}) {
  return (
    <svg className="absolute inset-0 h-full w-full">
      <defs>
        <pattern
          id="lines-pattern"
          x="0" y="0"
          width="1" height={spacing}
          patternUnits="userSpaceOnUse"
        >
          <line x1="0" y1={spacing} x2="100%" y2={spacing}
                stroke={color} strokeWidth={size} />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill="url(#lines-pattern)" />
    </svg>
  );
}
```

### Zoom and Pan

ReactFlow provides built-in zoom/pan. Configure with MindNode-like defaults:

```tsx
<ReactFlow
  minZoom={0.1}
  maxZoom={4}
  defaultViewport={{ x: 0, y: 0, zoom: 1 }}
  fitView
  fitViewOptions={{ padding: 0.2, maxZoom: 1.5 }}
  panOnScroll
  panOnDrag
  zoomOnScroll
  zoomOnPinch
  selectionOnDrag={false}
>
  {/* Canvas background */}
  <Background
    variant={canvasSettings.backgroundPattern === 'dots' ? BackgroundVariant.Dots : BackgroundVariant.Lines}
    gap={canvasSettings.patternSpacing}
    size={canvasSettings.patternSize}
    color={canvasSettings.patternColor}
    style={{ backgroundColor: canvasSettings.backgroundColor }}
  />

  {/* Minimap */}
  {canvasSettings.showMinimap && (
    <MiniMap
      position={canvasSettings.minimapPosition}
      maskColor="rgba(26, 26, 62, 0.08)"
      className="rounded-[var(--mn-radius-md)] border border-[var(--mn-border)] shadow-mn-node"
      nodeColor={(node) => node.data?.themeColor ?? '#6C63FF'}
      pannable
      zoomable
    />
  )}

  <Controls
    position="bottom-left"
    className="rounded-[var(--mn-radius-md)] border border-[var(--mn-border)]
               bg-white shadow-mn-node [&>button]:border-[var(--mn-border)]"
  />
</ReactFlow>
```

### Zoom Controls

```tsx
function ZoomControls() {
  const { zoomIn, zoomOut, fitView, getZoom } = useReactFlow();
  const [zoom, setZoom] = useState(1);

  return (
    <div className="flex items-center gap-1 rounded-full border border-[var(--mn-border)]
                    bg-white px-2 py-1 shadow-mn-node">
      <button
        onClick={() => zoomOut()}
        className="rounded-full p-1 text-[var(--mn-text-muted)]
                   hover:bg-[var(--mn-bg-secondary)] hover:text-[var(--mn-text-primary)]"
      >
        <MinusIcon className="h-3.5 w-3.5" />
      </button>
      <span className="min-w-[3rem] text-center text-xs font-medium text-[var(--mn-text-secondary)]">
        {Math.round(zoom * 100)}%
      </span>
      <button
        onClick={() => zoomIn()}
        className="rounded-full p-1 text-[var(--mn-text-muted)]
                   hover:bg-[var(--mn-bg-secondary)] hover:text-[var(--mn-text-primary)]"
      >
        <PlusIcon className="h-3.5 w-3.5" />
      </button>
      <div className="mx-1 h-4 w-px bg-[var(--mn-border)]" />
      <button
        onClick={() => fitView({ padding: 0.2 })}
        className="rounded-full p-1 text-[var(--mn-text-muted)]
                   hover:bg-[var(--mn-bg-secondary)] hover:text-[var(--mn-text-primary)]"
        title="Fit all nodes in view"
      >
        <MaximizeIcon className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}
```

---

## Edges and Connections

### Parent-Child Edges

Standard hierarchical edges connecting parent nodes to child nodes. These are the structural backbone of the mind map.

```ts
const parentChildEdgeDefaults: Partial<Edge> = {
  type: 'smoothstep',
  animated: false,
  style: {
    strokeWidth: 2,
  },
  markerEnd: undefined, // No arrowheads in MindNode style
};
```

Style edges with the branch color from the theme:

```ts
function styleParentChildEdge(
  edge: MindMapEdge,
  variant: ThemeVariant,
  childNode: MindMapNode,
): Edge {
  const colors = getNodeColors(variant, childNode.depth, childNode.branchIndex);
  return {
    ...edge,
    type: 'smoothstep',
    style: {
      stroke: colors.stroke,
      strokeWidth: 2,
    },
  };
}
```

### Cross-Connections

Non-hierarchical links between any two nodes that are not in a direct parent-child relationship. In MindNode, these appear as dashed curved lines, often with a label.

```ts
const crossConnectionDefaults: Partial<Edge> = {
  type: 'default', // Bezier curve
  animated: false,
  style: {
    strokeWidth: 1.5,
    strokeDasharray: '6 4',
  },
  labelStyle: {
    fontSize: 11,
    fontWeight: 500,
    fill: 'var(--mn-text-secondary)',
  },
  labelBgStyle: {
    fill: 'var(--mn-bg-primary)',
    fillOpacity: 0.9,
  },
  labelBgPadding: [4, 8] as [number, number],
  labelBgBorderRadius: 4,
};
```

### Connection Creation UI

Provide a distinct interaction for creating cross-connections vs parent-child edges:

```ts
/** Distinguish edge type by interaction:
 *  - Drag from node handle → parent-child edge (restructure tree)
 *  - Alt+drag or dedicated "connect" mode → cross-connection
 */
interface ConnectionMode {
  type: 'restructure' | 'cross-connect';
}

function onConnect(connection: Connection, mode: ConnectionMode): MindMapEdge {
  return {
    id: `edge-${connection.source}-${connection.target}`,
    source: connection.source!,
    target: connection.target!,
    type: mode.type === 'restructure' ? 'parent-child' : 'cross-connection',
    style: mode.type === 'cross-connection'
      ? { strokeDasharray: '6 4', strokeWidth: 1.5 }
      : undefined,
  };
}
```

### Edge Routing Styles

| Style | ReactFlow Type | When to Use |
|-------|---------------|-------------|
| Smooth Step | `smoothstep` | Parent-child edges (default MindNode look) |
| Bezier | `default` | Cross-connections (graceful curves) |
| Straight | `straight` | Minimalist themes, high-density layouts |
| Step | `step` | Roadmap/flowchart themes |

---

## Visual Tags

Colored badges attached to nodes for categorization. In MindNode, tags appear as small rounded rectangles with a colored background and short text label.

### Tag Data Model

```ts
interface NodeTag {
  id: string;
  label: string;
  color: string; // Hex color for badge background
}

/** Predefined tag palette — users can also create custom colors */
const TAG_PRESETS: NodeTag[] = [
  { id: 'urgent', label: 'Urgent', color: '#FF6B6B' },
  { id: 'idea', label: 'Idea', color: '#FFB74D' },
  { id: 'done', label: 'Done', color: '#68D391' },
  { id: 'question', label: 'Question', color: '#63B3ED' },
  { id: 'important', label: 'Important', color: '#B794F6' },
  { id: 'blocked', label: 'Blocked', color: '#F687B3' },
];
```

### Tag Rendering on Nodes

```tsx
function NodeTags({ tags }: { tags: NodeTag[] }) {
  if (tags.length === 0) return null;

  return (
    <div className="mt-1 flex flex-wrap gap-1">
      {tags.map((tag) => (
        <span
          key={tag.id}
          className="inline-flex items-center rounded-full px-1.5 py-0.5
                     text-[10px] font-medium leading-none"
          style={{
            backgroundColor: `color-mix(in srgb, ${tag.color} 20%, transparent)`,
            color: tag.color,
          }}
        >
          {tag.label}
        </span>
      ))}
    </div>
  );
}
```

---

## Stickers (Emoji/Icon Attachments)

MindNode allows attaching stickers (emoji or small icons) to nodes as visual markers. Stickers appear adjacent to the node label.

### Sticker Data Model

```ts
interface NodeSticker {
  id: string;
  /** Emoji character or icon identifier */
  emoji: string;
  /** Position relative to node: before label, after label, or above */
  position: 'before' | 'after' | 'above';
}
```

### Sticker Rendering

```tsx
function NodeStickers({
  stickers,
  position,
}: {
  stickers: NodeSticker[];
  position: 'before' | 'after' | 'above';
}) {
  const filtered = stickers.filter((s) => s.position === position);
  if (filtered.length === 0) return null;

  return (
    <span className="inline-flex gap-0.5">
      {filtered.map((sticker) => (
        <span
          key={sticker.id}
          className="text-base leading-none"
          role="img"
          aria-label={sticker.emoji}
        >
          {sticker.emoji}
        </span>
      ))}
    </span>
  );
}
```

### Sticker Picker

```tsx
const STICKER_CATEGORIES = {
  status: ['✅', '❌', '⏳', '🔥', '⭐', '💡', '❓', '⚠️'],
  priority: ['🔴', '🟠', '🟡', '🟢', '🔵', '🟣'],
  emotion: ['😊', '🤔', '😎', '🎯', '🚀', '💪', '🎨', '📝'],
  objects: ['📌', '🔗', '📎', '🗂️', '📊', '💬', '🔔', '🏷️'],
};

function StickerPicker({ onSelect }: { onSelect: (emoji: string) => void }) {
  return (
    <div className="rounded-[var(--mn-radius-lg)] border border-[var(--mn-border)]
                    bg-white p-3 shadow-[0_8px_32px_rgba(26,26,62,0.16)]">
      {Object.entries(STICKER_CATEGORIES).map(([category, emojis]) => (
        <div key={category} className="mb-2">
          <span className="mb-1 block text-[10px] font-medium uppercase tracking-wider
                         text-[var(--mn-text-muted)]">
            {category}
          </span>
          <div className="grid grid-cols-8 gap-1">
            {emojis.map((emoji) => (
              <button
                key={emoji}
                onClick={() => onSelect(emoji)}
                className="flex h-8 w-8 items-center justify-center rounded-[var(--mn-radius-sm)]
                           text-lg transition-colors hover:bg-[var(--mn-bg-secondary)]"
              >
                {emoji}
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
```

---

## Outline View

The outline view renders the same tree as a collapsible, editable list.

### Outline Component

```tsx
function OutlineView() {
  const { nodes, selectedNodeIds, selectNodes, focusNode } = useDocumentStore();
  const rootNode = nodes.get('root');
  if (!rootNode) return null;

  return (
    <div
      className="h-full overflow-y-auto px-6 py-4"
      style={{
        backgroundColor: 'var(--mn-outline-bg)',
        color: 'var(--mn-outline-text)',
      }}
    >
      <OutlineNode node={rootNode} depth={0} />
    </div>
  );
}

function OutlineNode({ node, depth }: { node: MindMapNode; depth: number }) {
  const { nodes, toggleCollapse, updateLabel } = useDocumentStore();
  const children = getChildrenSorted(nodes, node.id);
  const hasChildren = children.length > 0;

  return (
    <div style={{ paddingLeft: depth > 0 ? 20 : 0 }}>
      <div
        className={`group flex items-center gap-1.5 rounded-[var(--mn-radius-sm)]
                    py-1 pr-2 transition-colors
                    hover:bg-[color-mix(in_srgb,var(--mn-accent)_5%,transparent)]`}
      >
        {/* Collapse toggle */}
        <button
          onClick={() => hasChildren && toggleCollapse(node.id)}
          className={`flex h-5 w-5 items-center justify-center rounded-sm
                      text-[var(--mn-text-muted)] transition-transform
                      ${node.collapsed ? '' : 'rotate-90'}
                      ${hasChildren ? 'visible' : 'invisible'}`}
        >
          <ChevronRightIcon className="h-3.5 w-3.5" />
        </button>

        {/* Branch color indicator */}
        <span
          className="h-2 w-2 rounded-full"
          style={{ backgroundColor: getBranchColor(node) }}
        />

        {/* Editable label */}
        <span
          contentEditable
          suppressContentEditableWarning
          onBlur={(e) => updateLabel(node.id, e.currentTarget.textContent ?? '')}
          className="flex-1 text-sm outline-none"
        >
          {node.label}
        </span>

        {/* Tags inline */}
        <NodeTags tags={node.tags} />
      </div>

      {/* Children */}
      {!node.collapsed && children.map((child) => (
        <OutlineNode key={child.id} node={child} depth={depth + 1} />
      ))}
    </div>
  );
}
```

### Outline Keyboard Navigation

| Key | Action |
|-----|--------|
| `Enter` | Create sibling node below |
| `Tab` | Indent (make child of previous sibling) |
| `Shift+Tab` | Outdent (make sibling of parent) |
| `ArrowUp` / `ArrowDown` | Navigate between visible nodes |
| `ArrowRight` | Expand collapsed node |
| `ArrowLeft` | Collapse expanded node, or move to parent |
| `Cmd+Shift+ArrowUp` | Move node up among siblings |
| `Cmd+Shift+ArrowDown` | Move node down among siblings |

---

## Export System

### Supported Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| **PNG** | `.png` | Rasterized canvas at configurable DPI |
| **PDF** | `.pdf` | Vector export with text preserved |
| **Markdown** | `.md` | Indented bullet list hierarchy |
| **OPML** | `.opml` | Outline Processor Markup Language (compatible with outliners) |
| **FreeMind** | `.mm` | FreeMind XML format (cross-tool interop) |
| **Plain Text** | `.txt` | Indented text, tab-delimited depth |

### Export TypeScript Interface

```ts
type ExportFormat = 'png' | 'pdf' | 'markdown' | 'opml' | 'freemind' | 'text';

interface ExportOptions {
  format: ExportFormat;
  /** PNG/PDF: scale factor (1 = 1x, 2 = 2x retina) */
  scale?: number;
  /** PNG/PDF: include canvas background */
  includeBackground?: boolean;
  /** PNG/PDF: add padding around content */
  padding?: number;
  /** Markdown/Text: use nodes' notes as body text under each heading */
  includeNotes?: boolean;
  /** Markdown: heading depth for root (default 1, making root an H1) */
  rootHeadingLevel?: 1 | 2 | 3;
}
```

### Markdown Export

```ts
function exportToMarkdown(doc: MindMapDocument, options: ExportOptions): string {
  const lines: string[] = [];
  const rootLevel = options.rootHeadingLevel ?? 1;

  function walk(nodeId: string, depth: number) {
    const node = doc.nodes.get(nodeId);
    if (!node) return;

    if (depth < 6) {
      // Use headings for top levels
      lines.push(`${'#'.repeat(rootLevel + depth)} ${node.label}`);
    } else {
      // Use bullet list for deep levels
      lines.push(`${'  '.repeat(depth - 6)}- ${node.label}`);
    }

    if (options.includeNotes && node.notes) {
      lines.push('');
      lines.push(node.notes);
    }

    lines.push('');

    const children = getChildrenSorted(doc.nodes, nodeId);
    children.forEach((child) => walk(child.id, depth + 1));
  }

  walk('root', 0);
  return lines.join('\n');
}
```

### OPML Export

```ts
function exportToOPML(doc: MindMapDocument): string {
  const rootNode = doc.nodes.get('root');
  if (!rootNode) return '';

  function buildOutline(nodeId: string): string {
    const node = doc.nodes.get(nodeId)!;
    const children = getChildrenSorted(doc.nodes, nodeId);
    const noteAttr = node.notes
      ? ` _note="${escapeXml(node.notes)}"`
      : '';

    if (children.length === 0) {
      return `<outline text="${escapeXml(node.label)}"${noteAttr} />`;
    }

    return [
      `<outline text="${escapeXml(node.label)}"${noteAttr}>`,
      ...children.map((c) => buildOutline(c.id)),
      '</outline>',
    ].join('\n');
  }

  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<opml version="2.0">',
    '<head>',
    `  <title>${escapeXml(doc.title)}</title>`,
    '</head>',
    '<body>',
    buildOutline('root'),
    '</body>',
    '</opml>',
  ].join('\n');
}

function escapeXml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;');
}
```

### PNG Export via Canvas API

```ts
async function exportToPNG(
  reactFlowInstance: ReactFlowInstance,
  options: ExportOptions,
): Promise<Blob> {
  const scale = options.scale ?? 2;
  const padding = options.padding ?? 40;

  // Get the viewport bounding box of all nodes
  const nodesBounds = getNodesBounds(reactFlowInstance.getNodes());

  const width = (nodesBounds.width + padding * 2) * scale;
  const height = (nodesBounds.height + padding * 2) * scale;

  // Use ReactFlow's toObject to serialize, then render to canvas
  // or use html2canvas / @reactflow/node-resizer approach
  const dataUrl = await toPng(
    document.querySelector('.react-flow') as HTMLElement,
    {
      backgroundColor: options.includeBackground
        ? getComputedStyle(document.documentElement).getPropertyValue('--mn-canvas-bg')
        : 'transparent',
      width: width / scale,
      height: height / scale,
      style: { transform: `scale(${scale})`, transformOrigin: 'top left' },
      pixelRatio: scale,
    },
  );

  const response = await fetch(dataUrl);
  return response.blob();
}
```

### Export Dialog Component

```tsx
function ExportDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [format, setFormat] = useState<ExportFormat>('png');
  const [scale, setScale] = useState(2);
  const [includeBackground, setIncludeBackground] = useState(true);

  const formats: { value: ExportFormat; label: string; icon: React.ReactNode }[] = [
    { value: 'png', label: 'PNG Image', icon: <ImageIcon /> },
    { value: 'pdf', label: 'PDF Document', icon: <FileIcon /> },
    { value: 'markdown', label: 'Markdown', icon: <MarkdownIcon /> },
    { value: 'opml', label: 'OPML', icon: <CodeIcon /> },
    { value: 'freemind', label: 'FreeMind', icon: <ShareIcon /> },
    { value: 'text', label: 'Plain Text', icon: <AlignLeftIcon /> },
  ];

  return (
    <dialog
      open={open}
      className="rounded-[var(--mn-radius-xl)] border border-[var(--mn-border)]
                 bg-white p-6 shadow-[0_8px_32px_rgba(26,26,62,0.16)]"
    >
      <h3 className="mb-4 text-lg font-semibold text-[var(--mn-text-primary)]">
        Export Mind Map
      </h3>

      {/* Format selector */}
      <div className="mb-4 grid grid-cols-3 gap-2">
        {formats.map((f) => (
          <button
            key={f.value}
            onClick={() => setFormat(f.value)}
            className={`flex flex-col items-center gap-1 rounded-[var(--mn-radius-md)]
                        border-2 p-3 text-xs font-medium transition-all
                        ${format === f.value
                          ? 'border-mn-purple bg-mn-purple-light text-mn-purple'
                          : 'border-transparent bg-[var(--mn-bg-secondary)]
                             text-[var(--mn-text-secondary)]
                             hover:border-[var(--mn-border)]'
                        }`}
          >
            {f.icon}
            {f.label}
          </button>
        ))}
      </div>

      {/* Image options */}
      {(format === 'png' || format === 'pdf') && (
        <div className="mb-4 space-y-3">
          <label className="flex items-center gap-2 text-sm text-[var(--mn-text-secondary)]">
            <input
              type="checkbox"
              checked={includeBackground}
              onChange={(e) => setIncludeBackground(e.target.checked)}
              className="rounded accent-[var(--mn-purple)]"
            />
            Include background
          </label>
          <label className="flex items-center gap-2 text-sm text-[var(--mn-text-secondary)]">
            Scale:
            <select
              value={scale}
              onChange={(e) => setScale(Number(e.target.value))}
              className="rounded-[var(--mn-radius-sm)] border border-[var(--mn-border)] px-2 py-1 text-sm"
            >
              <option value={1}>1x</option>
              <option value={2}>2x (Retina)</option>
              <option value={3}>3x</option>
            </select>
          </label>
        </div>
      )}

      <div className="flex justify-end gap-2">
        <button
          onClick={onClose}
          className="rounded-full px-4 py-2 text-sm font-medium text-[var(--mn-text-secondary)]
                     hover:bg-[var(--mn-bg-secondary)]"
        >
          Cancel
        </button>
        <button
          onClick={() => handleExport(format, { scale, includeBackground })}
          className="rounded-full bg-mn-purple px-5 py-2 text-sm font-semibold text-white
                     hover:bg-mn-purple-hover"
        >
          Export
        </button>
      </div>
    </dialog>
  );
}
```

---

## Minimap

### Configuration and Styling

The minimap provides an overview of the entire canvas at a glance. Position it in a corner with theme-aware styling.

```tsx
<MiniMap
  position="bottom-right"
  className="!rounded-[var(--mn-radius-md)] !border !border-[var(--mn-border)]
             !bg-[var(--mn-bg-primary)] !shadow-mn-node"
  maskColor="color-mix(in srgb, var(--mn-navy) 8%, transparent)"
  nodeColor={(node) => {
    const mn = node.data as MindMapNode;
    const colors = getNodeColors(resolvedVariant, mn.depth, mn.branchIndex);
    return colors.fill;
  }}
  nodeStrokeWidth={0}
  pannable
  zoomable
  style={{ width: 160, height: 120 }}
/>
```

### Minimap Viewport Indicator

ReactFlow's built-in minimap shows the current viewport as a rectangle. Style it to match the accent color:

```css
.react-flow__minimap-mask {
  fill: color-mix(in srgb, var(--mn-navy) 8%, transparent);
}

.react-flow__minimap svg {
  border-radius: var(--mn-radius-md);
}
```

---

## Utility: Get Sorted Children

```ts
function getChildrenSorted(
  nodes: Map<string, MindMapNode>,
  parentId: string,
): MindMapNode[] {
  const children: MindMapNode[] = [];
  for (const node of nodes.values()) {
    if (node.parentId === parentId) children.push(node);
  }
  return children.sort((a, b) => a.sortOrder - b.sortOrder);
}
```
