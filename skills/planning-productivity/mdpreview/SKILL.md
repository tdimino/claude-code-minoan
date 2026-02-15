---
name: mdpreview
description: "Catppuccin-themed live-reloading Markdown viewer with multi-tab support, margin annotations, sidebar TOC, and Chrome --app mode. This skill should be used when previewing .md files in a polished editorial reader, adding AI or human annotations to documents, or launching a collaborative document review session."
argument-hint: <file.md> [file2.md ...] [--port PORT] [--author NAME]
allowed-tools: Bash(python3*), Read, Glob, Write
---

# mdpreview — Markdown Preview & Annotate

Catppuccin Mocha/Latte live-reloading Markdown viewer with multi-tab support and Google Docs–style margin annotations.

## Quick Start

Locate the package directory (it lives under this skill's `scripts/` folder):

```bash
# Preview one or more files
python3 <skill-dir>/scripts/md_preview_and_annotate/__main__.py file.md [file2.md ...] --port 3031

# Or if the package is on PYTHONPATH / in a project's tools/ directory:
python3 -m md_preview_and_annotate file.md [file2.md ...] --port 3031
```

### Add a file to a running server

```bash
python3 -m md_preview_and_annotate --add another.md --port 3031
```

### Add an annotation from CLI (no server needed)

```bash
python3 -m md_preview_and_annotate --annotate file.md \
  --text "RPL §235-b" --author "Claude" --comment "Cite the specific subsection"
```

This writes directly to the sidecar JSON (`file.md.annotations.json`). The live viewer picks it up on the next 500ms poll cycle.

## Features

| Feature | Details |
|---------|---------|
| **Live reload** | 500ms polling, auto-refreshes on file save |
| **Multi-tab** | Open multiple .md files, switch tabs, add/close at runtime |
| **Annotations** | Right-margin comment bubbles with author badges (human/AI) |
| **Sidecar JSON** | Annotations persisted in `file.md.annotations.json` alongside source |
| **Catppuccin** | Full Mocha (dark) / Latte (light) theme with 26 CSS variables |
| **Typography** | Cormorant Garamond headings, DM Sans body, Victor Mono code |
| **Sidebar TOC** | Collapsible table of contents with scroll-spy |
| **Code highlighting** | highlight.js with Catppuccin syntax theme |
| **Chrome --app** | Opens in frameless Chrome window for native feel |
| **Word count** | Status bar with word count and reading time |
| **Cross-file links** | Local `.md` links open in new tabs instead of navigating away |

## Annotation System

To create annotations interactively, select text in the viewer — a floating button appears, then fill in the comment form in the right gutter.

To create annotations programmatically (e.g., from Claude Code), use the `--annotate` CLI flag. This requires no running server — it writes directly to the sidecar JSON.

- **Human authors** — blue name badge
- **AI authors** — mauve name badge with robot icon
- **Actions** — resolve (toggle strikethrough) or delete (trash icon), revealed on hover
- **Persistence** — sidecar JSON file, auto-loaded on viewer refresh or file poll

### Sidecar JSON Schema

```json
{
  "version": 1,
  "annotations": [
    {
      "id": "a1b2c3",
      "anchor": { "text": "selected phrase", "heading": "", "offset": 0 },
      "author": { "name": "Claude", "type": "ai" },
      "created": "2026-02-12T15:30:00+00:00",
      "body": "Comment text here",
      "resolved": false,
      "replies": []
    }
  ]
}
```

## Package Structure

```
md_preview_and_annotate/
  __init__.py        # Package marker
  __main__.py        # CLI entry point (serve, --add, --annotate)
  server.py          # HTTP server with tab & annotation API endpoints
  template.py        # HTML shell assembly (injects CSS + JS)
  annotations.py     # Sidecar JSON read/write
  static/
    styles.css       # Full Catppuccin theme (~1000 lines)
    app.js           # Client-side rendering, polling, annotation UI (~800 lines)
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/content?tab=<id>` | GET | Markdown content for a tab |
| `/api/tabs` | GET | List open tabs |
| `/api/annotations?tab=<id>` | GET | Annotations for a tab |
| `/api/add` | POST | Open a new file tab |
| `/api/close` | POST | Close a tab |
| `/api/annotate` | POST | Create an annotation |
| `/api/resolve` | POST | Toggle annotation resolved state |
| `/api/delete-annotation` | POST | Delete an annotation |
