# @chenglou/pretext API Reference

## Package Info

- **npm**: `@chenglou/pretext`
- **Version**: `0.0.2`
- **License**: MIT
- **Import**: `import { ... } from 'https://esm.sh/@chenglou/pretext@0.0.2'`
- **Environment**: Browser-only (uses canvas `measureText` internally)

---

## Use-case 1: Height Prediction

### `prepare(text, font, options?) → PreparedText`

```ts
prepare(text: string, font: string, options?: { whiteSpace?: 'normal' | 'pre-wrap' }): PreparedText
```

One-time text analysis + measurement pass, returns an opaque handle.

- `font` must match CSS font shorthand (size, weight, style, family)—same format as `canvas.font`
- Examples: `'16px Inter'`, `'700 24px Georgia'`
- ~19ms for 500-text batch

### `layout(prepared, maxWidth, lineHeight) → { height, lineCount }`

```ts
layout(prepared: PreparedText, maxWidth: number, lineHeight: number): { height: number, lineCount: number }
```

Pure arithmetic—no DOM reads, no canvas calls.

- ~0.09ms for 500-text batch
- `lineHeight` must match CSS `line-height`

---

## Use-case 2: Manual Line Layout

### `prepareWithSegments(text, font, options?) → PreparedTextWithSegments`

```ts
prepareWithSegments(text: string, font: string, options?: { whiteSpace?: 'normal' | 'pre-wrap' }): PreparedTextWithSegments
```

Same as `prepare()` but returns a richer structure with segment data. Has a `.widths` array for per-segment widths.

### `layoutWithLines(prepared, maxWidth, lineHeight) → { height, lineCount, lines }`

```ts
layoutWithLines(prepared: PreparedTextWithSegments, maxWidth: number, lineHeight: number): { height: number, lineCount: number, lines: LayoutLine[] }
```

High-level API, fixed max width for all lines.

### `walkLineRanges(prepared, maxWidth, onLine) → number`

```ts
walkLineRanges(prepared: PreparedTextWithSegments, maxWidth: number, onLine: (line: LayoutLineRange) => void): number
```

Low-level, no string materialization. Calls `onLine` per line with width and cursors.

- Returns total line count
- Great for binary search (shrinkwrap) and aggregate geometry

### `layoutNextLine(prepared, start, maxWidth) → LayoutLine | null`

```ts
layoutNextLine(prepared: PreparedTextWithSegments, start: LayoutCursor, maxWidth: number): LayoutLine | null
```

Iterator API—variable width per line.

- Pass previous line's `end` as next `start`
- Returns `null` when text is exhausted

---

## Types

```ts
type LayoutLine = {
  text: string
  width: number
  start: LayoutCursor
  end: LayoutCursor
}

type LayoutLineRange = {
  width: number
  start: LayoutCursor
  end: LayoutCursor
}

type LayoutCursor = {
  segmentIndex: number
  graphemeIndex: number
}
```

---

## Helpers

```ts
clearCache(): void
```

Clears internal caches. Useful when cycling through many fonts.

```ts
setLocale(locale?: string): void
```

Sets locale for future `prepare()` calls, also clears cache.

---

## Font Format

The `font` parameter follows the CSS font shorthand / `canvas.font` format:

```
'16px Inter'
'700 24px "Iowan Old Style"'
'italic 18px Georgia, Palatino, serif'
'bold italic 14px "Helvetica Neue", Helvetica, Arial, sans-serif'
```

---

## Caveats

- **Target CSS behavior**: `white-space: normal`, `word-break: normal`, `overflow-wrap: break-word`, `line-break: auto`
- **pre-wrap mode**: preserves spaces, tabs (`\t`, tab-size: 8), hard breaks (`\n`)
- **`system-ui` is UNSAFE**—canvas and DOM can resolve different fonts on macOS. Always use named fonts.
- Narrow widths can break inside words at grapheme boundaries (`overflow-wrap: break-word` behavior)

---

## Language Support

- All languages including CJK, Arabic, Hebrew, Thai, Khmer, Myanmar, Korean
- Mixed bidi text
- Emoji and grapheme clusters
- 7680/7680 accuracy on Chrome, Safari, Firefox
