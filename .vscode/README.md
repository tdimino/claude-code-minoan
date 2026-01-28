# VSCode Configuration

This folder contains VSCode workspace settings, recommended extensions, and reference configurations.

## Quick Setup

When you open this repo in VSCode, you'll be prompted to install recommended extensions. Accept to get the full setup.

**Manual extension install:**
```bash
# Install all recommended extensions
code --install-extension anthropic.claude-code
code --install-extension pkief.material-icon-theme
code --install-extension yzhang.markdown-all-in-one
# ... (see extensions.json for full list)
```

## Files

| File | Purpose |
|------|---------|
| `settings.json` | Workspace settings (auto-applied) |
| `extensions.json` | Recommended extensions (prompts on open) |
| `global-settings-reference.jsonc` | Reference copy of global User settings |

---

## Theme & Appearance

### Icon Theme
**Material Icon Theme** (`pkief.material-icon-theme`)
- File/folder icons based on file type
- Clean, recognizable iconography

### Color Theme
**GitHub Markdown Theme** (`tomdimino.github-markdown-theme`)
- Custom theme optimized for markdown editing
- GitHub-style syntax highlighting

### Terminal: Catppuccin Mocha
Terminal colors use the Catppuccin Mocha palette:

| Color | Hex | Purpose |
|-------|-----|---------|
| Background | `#1e1e2e` | Dark purple-gray |
| Foreground | `#cdd6f4` | Light lavender |
| Red | `#f38ba8` | Errors |
| Green | `#a6e3a1` | Success |
| Yellow | `#f9e2af` | Warnings |
| Blue | `#89b4fa` | Info |
| Magenta | `#f5c2e7` | Special |
| Cyan | `#94e2d5` | Accents |

### Font
**Victor Mono** - Terminal font with ligatures
- Size: 14px
- Ligatures enabled for `=>`, `->`, `!=`, etc.

---

## Extensions by Category

### AI & Claude Code (4)
| Extension | Purpose |
|-----------|---------|
| `anthropic.claude-code` | Claude Code AI pair programming |
| `aldea.claude-session-tracker` | Track Claude sessions |
| `saoudrizwan.claude-dev` | Claude Dev assistant |
| `openai.chatgpt` | ChatGPT integration |

### Markdown (10)
| Extension | Purpose |
|-----------|---------|
| `yzhang.markdown-all-in-one` | Shortcuts, TOC, preview |
| `bierner.markdown-preview-github-styles` | GitHub-flavored preview |
| `shd101wyy.markdown-preview-enhanced` | Enhanced preview with diagrams |
| `davidanson.vscode-markdownlint` | Markdown linting |
| `robole.marky-markdown` | Markdown utilities |
| `robole.marky-dynamic` | Dynamic features |
| `robole.marky-edit` | Editing helpers |
| `robole.marky-stats` | Word/character counts |
| `robole.markdown-snippets` | Snippets |
| `mushan.vscode-paste-image` | Paste images |

### Python (8)
| Extension | Purpose |
|-----------|---------|
| `ms-python.python` | Language support |
| `ms-python.debugpy` | Debugger |
| `ms-python.black-formatter` | Black formatter |
| `ms-python.isort` | Import sorting |
| `ms-python.pylint` | Pylint linting |
| `ms-python.flake8` | Flake8 linting |
| `ms-python.mypy-type-checker` | Type checking |
| `nickmillerdev.pytest-fixtures` | Pytest fixtures |

### Jupyter (4)
| Extension | Purpose |
|-----------|---------|
| `ms-toolsai.jupyter` | Notebook support |
| `ms-toolsai.jupyter-renderers` | Renderers |
| `ms-toolsai.vscode-jupyter-cell-tags` | Cell tags |
| `ms-toolsai.vscode-jupyter-slideshow` | Slideshow mode |

### Git & GitHub (2)
| Extension | Purpose |
|-----------|---------|
| `eamodio.gitlens` | Git supercharged |
| `github.vscode-github-actions` | Actions support |

### Containers & Remote (5)
| Extension | Purpose |
|-----------|---------|
| `ms-azuretools.vscode-docker` | Docker |
| `ms-azuretools.vscode-containers` | Dev containers |
| `anysphere.remote-ssh` | Remote SSH |
| `ms-vscode-remote.remote-ssh-edit` | Edit remote files |
| `ms-vscode.remote-explorer` | Remote explorer |

### Data & Config (3)
| Extension | Purpose |
|-----------|---------|
| `mechatroner.rainbow-csv` | CSV highlighting |
| `tamasfe.even-better-toml` | TOML support |
| `tomoki1207.pdf` | PDF viewer |

### Other (3)
| Extension | Purpose |
|-----------|---------|
| `dbaeumer.vscode-eslint` | ESLint |
| `christian-kohler.path-intellisense` | Path autocomplete |
| `factory.factory-vscode-extension` | Factory integration |

---

## Workspace Settings

Settings in `settings.json` are automatically applied when opening this repo.

### Markdown Editor
| Setting | Value | Purpose |
|---------|-------|---------|
| `editor.wordWrap` | on | Wrap long lines |
| `editor.lineHeight` | 1.4 | Breathing room |
| `editor.fontSize` | 13 | Comfortable reading |
| `editor.renderWhitespace` | boundary | Show leading/trailing only |
| `editor.minimap.enabled` | true | Quick navigation |
| `editor.renderLineHighlight` | gutter | Subtle line highlight |

### Markdown Preview
| Setting | Purpose |
|---------|---------|
| `markdown.preview.fontSize` | 13px font |
| `markdown.preview.lineHeight` | 1.5x spacing |
| `markdown.preview.markEditorSelection` | Highlight matching section |
| `markdown.preview.scrollPreviewWithEditor` | Sync scroll |
| `markdown.preview.scrollEditorWithPreview` | Sync scroll (reverse) |

### Syntax Highlighting
Custom colors for markdown elements:

| Element | Color | Style |
|---------|-------|-------|
| Headings | `#58A6FF` | Bold |
| Lists | `#7DD3FC` | - |
| **Bold** | `#e6edf3` | Bold |
| *Italic* | `#a5d6ff` | Italic |
| Links | `#58a6ff` | Underline |
| Code | `#c9d1d9` | - |
| > Blockquotes | `#d4a5ff` | Italic |
| ~~Strikethrough~~ | `#8b949e` | Strikethrough |

---

## Global Settings

To apply the global settings (terminal theme, fonts, etc.) to your VSCode:

1. Open Command Palette: `Cmd+Shift+P`
2. Type "Preferences: Open User Settings (JSON)"
3. Merge contents from `global-settings-reference.jsonc`

Or copy directly:
```bash
cp global-settings-reference.jsonc ~/Library/Application\ Support/Code/User/settings.json
```

⚠️ **Warning**: This overwrites existing settings. Merge manually if you have custom settings.

---

## Font Installation

**Victor Mono** (terminal font):
```bash
brew tap homebrew/cask-fonts
brew install --cask font-victor-mono
```

Or download from: https://rubjo.github.io/victor-mono/

---

*Last updated: 2026-01-27*
