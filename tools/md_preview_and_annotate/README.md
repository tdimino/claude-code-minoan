# md_preview_and_annotate

Catppuccin-themed live-reloading Markdown viewer with multi-tab support, annotation carousel, bookmarks, and Google Docs–style margin comments.

## Usage

```bash
# Preview one or more files
python3 -m md_preview_and_annotate file.md [file2.md ...] --port 3031 --author Tom

# Add a file to a running server
python3 -m md_preview_and_annotate --add another.md --port 3031

# Add an annotation from CLI (no server needed)
python3 -m md_preview_and_annotate --annotate file.md \
  --text "warranty of habitability" --comment "Core legal claim" --author Tom

# Add a bookmark from CLI
python3 -m md_preview_and_annotate --annotate file.md \
  --text "Section 235-b" --comment "Key statute" --type bookmark --author Tom
```

## Features

| Feature | Details |
|---------|---------|
| **Live reload** | 500ms polling, auto-refreshes on file save |
| **Multi-tab** | Open multiple .md files, switch/add/close tabs at runtime |
| **Annotation carousel** | Select text → choose from 5 types: Comment, Question, Suggest, Flag, Bookmark |
| **Bookmarks** | Saved globally to `~/.claude/bookmarks/` with INDEX.md and per-snippet .md files |
| **Replies** | Thread replies on any annotation |
| **Resolve/archive** | Resolved annotations move to `.annotations.resolved.json` sidecar |
| **Sidecar JSON** | Annotations persisted in `file.md.annotations.json` alongside source |
| **Catppuccin** | Full Mocha (dark) / Latte (light) theme with 26 CSS variables |
| **Typography** | Cormorant Garamond headings, DM Sans body, Victor Mono code |
| **Sidebar TOC** | Collapsible table of contents with scroll-spy |
| **Code highlighting** | highlight.js with Catppuccin syntax theme |
| **Chrome --app** | Opens in frameless Chrome window for native feel |
| **Word count** | Status bar with word count and reading time |
| **Smart scroll** | Click any annotation to scroll to its anchor text, with §↔Section normalization |
| **Auto-cleanup** | Kills stale port processes and clears .pyc cache on startup |

## Annotation Types

| Type | Icon | Color |
|------|------|-------|
| Comment | `ph-chat-dots` | Blue |
| Question | `ph-question` | Peach |
| Suggestion | `ph-lightbulb` | Yellow |
| Flag/Important | `ph-flag` | Red |
| Bookmark | `ph-bookmark-simple` | Mauve |

## Package Structure

```
md_preview_and_annotate/
  __init__.py        # Package marker
  __main__.py        # CLI entry point (serve, --add, --annotate)
  server.py          # HTTP server with tab & annotation API endpoints
  template.py        # HTML shell assembly (injects CSS + JS)
  annotations.py     # Sidecar JSON read/write (active + resolved archive)
  bookmarks.py       # Global bookmark persistence to ~/.claude/bookmarks/
  static/
    styles.css       # Full Catppuccin theme
    app.js           # Client-side rendering, polling, annotation UI
```

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/content?tab=<id>` | GET | Markdown content for a tab |
| `/api/tabs` | GET | List open tabs |
| `/api/annotations?tab=<id>` | GET | Annotations for a tab |
| `/api/add` | POST | Open a new file tab |
| `/api/close` | POST | Close a tab |
| `/api/annotate` | POST | Create an annotation (any type) |
| `/api/resolve` | POST | Toggle resolved state (archives on resolve) |
| `/api/reply` | POST | Add a threaded reply |
| `/api/delete-annotation` | POST | Delete an annotation |

## Sidecar JSON Schema

```json
{
  "version": 1,
  "annotations": [
    {
      "id": "a1b2c3",
      "anchor": { "text": "selected phrase", "heading": "", "offset": 0 },
      "author": { "name": "Claude", "type": "ai" },
      "created": "2026-02-15T15:30:00+00:00",
      "body": "Comment text here",
      "type": "comment",
      "resolved": false,
      "replies": [
        { "author": { "name": "Tom", "type": "human" }, "created": "...", "body": "Reply text" }
      ]
    }
  ]
}
```
