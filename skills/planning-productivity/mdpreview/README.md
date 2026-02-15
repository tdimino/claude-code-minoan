# mdpreview

Catppuccin-themed live-reloading Markdown viewer with multi-tab support and margin annotations. Extends the idea behind [`mdserve`](https://github.com/jfernandez/mdserve) (a lightweight Go binary for live-reloading Markdown) with a full editorial UI: Catppuccin theme, multi-tab, sidebar TOC, and Google Docs–style annotation bubbles.

![mdpreview with annotations](screenshot.png)

## Install

Copy or symlink the skill into `~/.claude/skills/`:

```bash
ln -s "$(pwd)" ~/.claude/skills/mdpreview
```

## Usage

```bash
# Preview files
python3 -m md_preview_and_annotate file.md [file2.md ...] --port 3031

# Add a file to running server
python3 -m md_preview_and_annotate --add another.md --port 3031

# Add annotation from CLI
python3 -m md_preview_and_annotate --annotate file.md \
  --text "RPL §235-b" --author "Claude" --comment "Cite the specific subsection"
```

## Features

- **Live reload** — 500ms polling, refreshes on save
- **Multi-tab** — open, switch, add/close tabs at runtime
- **Annotations** — right-margin comment bubbles (human + AI authors)
- **Sidecar JSON** — `file.md.annotations.json` persistence
- **Catppuccin** — Mocha (dark) / Latte (light) with 26 CSS vars
- **Typography** — Cormorant Garamond · DM Sans · Victor Mono
- **Sidebar TOC** — collapsible with scroll-spy
- **Chrome --app** — frameless native-feel window
