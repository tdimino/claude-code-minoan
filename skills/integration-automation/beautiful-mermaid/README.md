# Beautiful Mermaid

Render Mermaid diagrams as ASCII/Unicode art for terminal display or as themed SVG files. Supports flowcharts, state machines, sequence diagrams, class diagrams, and ER diagrams across 15 themes.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

Mermaid diagrams are useful for architecture docs and READMEs, but the standard toolchain renders to PNG/SVG only---not helpful in a terminal conversation. This skill renders Mermaid to Unicode box-drawing art for inline display, and to themed SVGs for file output.

---

## Structure

```
beautiful-mermaid/
  SKILL.md              # Full usage guide with theme list
  README.md             # This file
  package.json          # Node dependencies
  scripts/
    mermaid.mjs         # Renderer CLI
```

---

## Usage

```bash
# ASCII diagram to terminal
node mermaid.mjs "graph LR; A-->B-->C"

# ┌───┐     ┌───┐     ┌───┐
# │ A │────►│ B │────►│ C │
# └───┘     └───┘     └───┘

# SVG with tokyo-night theme
node mermaid.mjs -f svg -t tokyo-night "graph TD; A-->B" -o diagram.svg

# From file
node mermaid.mjs diagram.mmd

# From stdin
echo "graph LR; A-->B" | node mermaid.mjs -
```

### Options

| Option | Description |
|--------|-------------|
| `-f, --format` | `ascii` (default) or `svg` |
| `-t, --theme` | Theme for SVG output (default: zinc-dark) |
| `-o, --output` | Write to file instead of stdout |
| `--ascii` | Pure ASCII instead of Unicode box-drawing |
| `--themes` | List available themes |

---

## Supported Diagrams

Flowchart, State (`stateDiagram-v2`), Sequence, Class, ER.

## Themes (15)

**Dark:** zinc-dark, tokyo-night, tokyo-night-storm, catppuccin-mocha, nord, dracula, github-dark, solarized-dark, one-dark

**Light:** zinc-light, tokyo-night-light, catppuccin-latte, nord-light, github-light, solarized-light

---

## Setup

### Prerequisites

- Node.js 18+
- `cd ~/.claude/skills/beautiful-mermaid && npm install`

---

## Requirements

- Node.js 18+
- npm dependencies (installed via `package.json`)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/beautiful-mermaid ~/.claude/skills/
cd ~/.claude/skills/beautiful-mermaid && npm install
```
