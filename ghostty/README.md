# Ghostty Configuration

Ghostty terminal config optimized for Claude Code workflows. Synthesized from Anthropic's official docs, the Claude Code team's recommendations, and popular community setups (Feb 2026).

## Install

```bash
cp ghostty/config ~/Library/Application\ Support/com.mitchellh.ghostty/config
```

Reload with `Cmd+Shift+Comma` or restart Ghostty.

## What's Configured

| Category | Settings |
|----------|----------|
| **Theme** | Catppuccin Mocha (dark) / Latte (light) — follows macOS appearance |
| **Font** | JetBrains Mono 15pt, thickened |
| **macOS** | Option-as-Alt (required for word nav), transparent titlebar |
| **Appearance** | 0.90 opacity, blur, balanced padding, bold-is-bright |
| **Persistence** | Tabs/splits restored on restart |
| **Shell** | Auto-detected integration with prompt jumping, sudo, title |
| **Scrollback** | 100K lines (default 10K fills fast with Claude Code output) |
| **Cursor** | Bar, no blink |

## Keybindings

### Navigation

| Shortcut | Action |
|----------|--------|
| `Cmd+Left/Right` | Beginning/end of line |
| `Option+Left/Right` | Word navigation |
| `Option+Backspace` | Delete word backward |
| `Cmd+Up/Down` | Jump between shell prompts |

### Tabs

| Shortcut | Action |
|----------|--------|
| `Cmd+T` | New tab |
| `Cmd+W` | Close tab |
| `Cmd+[/]` | Previous/next tab |
| `Cmd+1-5` | Direct tab access |

### Split Panes

| Shortcut | Action |
|----------|--------|
| `Cmd+D` | Split right (vertical) |
| `Cmd+Shift+D` | Split down (horizontal) |
| `Cmd+Alt+Arrows` | Navigate between splits |
| `Cmd+Alt+Enter` or `Cmd+Shift+F` | Toggle split zoom (focus one pane) |
| `Cmd+Alt+=` or `Cmd+Shift+E` | Equalize split sizes |

### Quick Actions

| Shortcut | Action |
|----------|--------|
| `Cmd+K` | Clear screen |
| `Cmd+Shift+Comma` | Reload config |
| `Cmd+Comma` | Open config |
| `Cmd++/-/0` | Font size adjust/reset |
| `Cmd+Shift+P` | Command palette |

## Recommended Companion Tools

```bash
brew install lazygit          # TUI git client — run in a side split
brew install terminal-notifier # Desktop notifications (used by hooks)
npm install -g ccstatusline    # Claude Code statusline
```

## Dark/Light Mode

The `theme = dark:...,light:...` line follows macOS system appearance automatically. Toggle via System Settings > Appearance.

## Ghostty Version Note

Ghostty 1.3+ fixes a memory leak triggered by Claude Code's heavy terminal output (up to 37GB RAM on 1.2.x). Use `brew install --cask ghostty@tip` for the nightly build, or wait for 1.3 stable (expected March 2026).

## Sources

- [Daniel San's SAND Keybindings](https://x.com/dani_avila7/status/2023151176758268349) — mnemonic: Split, Arrange, Navigate, Destroy
- [Anthropic Terminal Config Docs](https://code.claude.com/docs/en/terminal-config)
- [Claude Code Team Tips](https://paddo.dev/blog/claude-code-team-tips/) (Feb 2026)
- [awwsillylife/ghostty-claude-code-setup](https://github.com/awwsillylife/ghostty-claude-code-setup) (987+ stars)
- [Eslam Helmy's Setup](https://eslamhelmy.tech/blog/ghostty-claude-code-setup) (Feb 2026)
- [Ghostty 1.3 Memory Leak Fix](https://netfox.space/news/ghostty-13-fixes-massive-memory-leak-caused-claude-code) (Jan 2026)
