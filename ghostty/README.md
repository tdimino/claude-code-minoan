# Ghostty Configuration

Ghostty terminal config optimized for Claude Code workflows. Synthesized from Anthropic's official docs, the Claude Code team's recommendations, and popular community setups (Feb 2026).

## Install

```bash
# Install fonts
brew install --cask font-jetbrains-mono-nerd-font

# Copy config
cp ghostty/config ~/Library/Application\ Support/com.mitchellh.ghostty/config
```

Restart Ghostty fully (`Cmd+Q` then reopen) to register new fonts.

## What's Configured

| Category | Settings |
|----------|----------|
| **Theme** | Catppuccin Mocha/Latte, Cream (parchment), Knossot (dark), Akrotiri (light) — follows macOS appearance or manual switch |
| **Font** | JetBrainsMono Nerd Font 15pt, thickened. Codepoint maps: Linear A (U+10600–1077F), Linear B (U+10000–100FF), Phaistos Disc (U+101D0–101FF), Minoan Glyphs PUA (U+E500–E5FF) |
| **macOS** | Option-as-Alt (required for word nav), transparent titlebar |
| **Appearance** | 0.90 opacity, blur, balanced padding, bold-is-bright, unfocused split dimming (0.85) |
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

## Theme Switching

The `theme = dark:...,light:...` line follows macOS system appearance automatically. For manual control, source the theme-switching script:

```bash
# Add to ~/.zshrc
source ~/.claude/scripts/ghostty/theme-switching.zsh
```

Then use the commands:

| Command | Effect |
|---------|--------|
| `dark` | macOS dark mode + Catppuccin Mocha |
| `light` | macOS light mode + Catppuccin Latte |
| `cream` | macOS light mode + Cream (warm parchment) |
| `knossot` | macOS dark mode + Knossot (Minoan palace) |
| `akrotiri` | macOS light mode + Akrotiri (sun-bleached plaster) |

### Custom Themes

Install all custom themes:

```bash
cp ghostty/themes/* ~/Library/Application\ Support/com.mitchellh.ghostty/themes/
```

| Theme | Mode | Inspiration |
|-------|------|-------------|
| **Cream** | Light | Aged vellum and iron gall ink |
| **Knossot** | Dark | Palace interior — obsidian walls, Egyptian blue frescoes, saffron and terracotta |
| **Akrotiri** | Light | Excavated city — sun-bleached plaster, Spring Fresco colors, volcanic earth |

### Codepoint Maps for Ancient Scripts

The config uses `font-codepoint-map` (not `font-family`) to map specific Unicode ranges to their rendering fonts. This avoids proportional font metrics polluting the monospace cell width:

```
font-codepoint-map = U+10600-U+1077F=Noto Sans Linear A
font-codepoint-map = U+10000-U+100FF=Noto Sans Linear B
font-codepoint-map = U+101D0-U+101FF=Noto Sans Symbols 2
font-codepoint-map = U+E500-U+E5FF=Minoan Glyphs
```

Install the fonts:

```bash
brew install --cask font-noto-sans-symbols-2
# Noto Sans Linear A/B — bundled with macOS in /System/Library/Fonts/Supplemental/
# MinoanGlyphs — build and install from scripts/minoan-glyphs/:
python3 scripts/minoan-glyphs/build.py --install
```

Verify: `printf '\U10600 \U101F5'` should render a Linear A sign and a Phaistos Disc rosette (not tofu).

### Terminal Greeting

Pair with `scripts/terminal-greeting/greeting.zsh` for an illuminated-manuscript greeting on each new shell, with `claude` prepopulated in the input buffer. See `scripts/terminal-greeting/README.md`.

## Ghostty Version Note

Ghostty 1.3+ fixes a memory leak triggered by Claude Code's heavy terminal output (up to 37GB RAM on 1.2.x). Use `brew install --cask ghostty@tip` for the nightly build, or wait for 1.3 stable (expected March 2026).

## Sources

- [Daniel San's SAND Keybindings](https://x.com/dani_avila7/status/2023151176758268349) — mnemonic: Split, Arrange, Navigate, Destroy
- [Anthropic Terminal Config Docs](https://code.claude.com/docs/en/terminal-config)
- [Claude Code Team Tips](https://paddo.dev/blog/claude-code-team-tips/) (Feb 2026)
- [awwsillylife/ghostty-claude-code-setup](https://github.com/awwsillylife/ghostty-claude-code-setup) (987+ stars)
- [Eslam Helmy's Setup](https://eslamhelmy.tech/blog/ghostty-claude-code-setup) (Feb 2026)
- [Ghostty 1.3 Memory Leak Fix](https://netfox.space/news/ghostty-13-fixes-massive-memory-leak-caused-claude-code) (Jan 2026)
