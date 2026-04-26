# Statusline Customization Guide

Step-by-step install for the three-line statusline (gradient context bar on line 1, ensouled/soul on line 2, session/block timers on line 3). See `README.md` for the architecture overview.

## Prerequisites

- Ghostty (or any truecolor terminal — for the line 1 gradient)
- Node.js (for `ccstatusline`)
- Python 3.11+ (for the gradient context bar)
- A Nerd Font in your terminal (for ⎇ branch glyph and ⁂ separator)

## 1. Install ccstatusline

```bash
npm install -g ccstatusline
```

ccstatusline renders lines 2-3. Line 1 is hand-built by a wrapper script because ccstatusline strips inline ANSI escape codes, and the gradient context bar needs truecolor.

## 2. Copy the hook scripts

```bash
mkdir -p ~/.claude/hooks
cp hooks/{statusline-monitor.sh,session-name.sh,crab-model.sh,context-bar.sh,ensouled-status.sh,soul-name.sh} ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.sh
```

| Script | Purpose |
|--------|---------|
| `statusline-monitor.sh` | Wrapper — assembles line 1 + pipes to ccstatusline |
| `session-name.sh` | Extracts session slug from transcript path |
| `crab-model.sh` | Renders 🦀 + model name |
| `context-bar.sh` | Gradient progress bar + token count (Python) |
| `ensouled-status.sh` | 𓂀 ensouled / ○ mortal indicator |
| `soul-name.sh` | Reads soul name from env or file |

## 3. Configure ccstatusline

```bash
mkdir -p ~/.config/ccstatusline
cp docs/global-setup/statusline/config.json ~/.config/ccstatusline/settings.json
```

Then strip the wrapping `ccstatusline` key — the file should be the `ccstatusline` block's contents at the top level. Or use this minimal version:

```json
{
  "version": 3,
  "lines": [
    [
      { "id": "ensouled-widget", "type": "custom-command", "commandPath": "~/.claude/hooks/ensouled-status.sh", "color": "brightBlue", "timeout": 1000 },
      { "id": "soul-name-widget", "type": "custom-command", "commandPath": "~/.claude/hooks/soul-name.sh", "color": "brightMagenta", "timeout": 1000 }
    ],
    [
      { "id": "session-clock", "type": "session-clock", "color": "hex:C9A84C" },
      { "id": "block-timer", "type": "block-timer", "color": "hex:A8884A" }
    ]
  ],
  "flexMode": "full-minus-40",
  "compactThreshold": 60,
  "colorLevel": 3,
  "defaultSeparator": "  "
}
```

`flexMode: full-minus-40` reserves 40 cols for the prompt area. Bump it if your prompt is longer.

## 4. Wire the wrapper into Claude Code settings

Edit `~/.claude/settings.json`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/hooks/statusline-monitor.sh",
    "padding": 0
  }
}
```

Restart Claude Code. The three-line statusline should appear.

## 5. Optional — Light/Dark Theme Switching

The wrapper can swap ccstatusline configs based on macOS appearance. Useful when you toggle between Catppuccin Mocha and Latte (or the Cream theme).

Create two variants:

```bash
cp ~/.config/ccstatusline/settings.json ~/.config/ccstatusline/settings-dark.json
cp ~/.config/ccstatusline/settings.json ~/.config/ccstatusline/settings-light.json
```

Edit `settings-light.json` to use darker, higher-contrast colors against the parchment background (e.g., `hex:8C2D14` instead of `hex:CC5C3A`).

The wrapper detects mode via `defaults read -g AppleInterfaceStyle` and atomically swaps `settings.json` between variants. No Claude Code restart needed.

## 6. Customizing Colors

**Line 1 colors** live in `statusline-monitor.sh`:

```bash
TYRIAN="\033[38;2;204;92;58m"       # Session name (warm copper #CC5C3A)
CRAB_COLOR="\033[38;2;200;128;188m" # Model (pastel Byzantium #C880BC)
BLUE="\033[94m"                      # Git branch (brightBlue)
```

The mode block above lets you set different values for light vs dark.

**Line 2-3 colors** live in `~/.config/ccstatusline/settings.json`. Use `hex:RRGGBB` for truecolor or named ccstatusline colors (`brightBlue`, `green`, etc.).

## 7. Customizing the Context Bar Gradient

Edit `~/.claude/hooks/context-bar.sh` (Python). The gradient stops are defined inline — five color stops mapped to context usage percentages. Swap them for any palette (Cream-theme earth tones, Mocha cool-tones, etc.).

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `⎇` branch glyph shows as tofu/box | Install a Nerd Font in your terminal (e.g., JetBrains Mono Nerd Font) |
| Line 1 gradient not rendering | Terminal must support truecolor; check `colorLevel: 3` in ccstatusline settings |
| `ccstatusline: command not found` | `npm install -g ccstatusline` and verify `npm bin -g` is in `$PATH` |
| Hook scripts time out | Bump `timeout` (ms) in the widget definition |
| Light/dark not switching | Verify `defaults read -g AppleInterfaceStyle` works in your shell |

## Files Reference

| File | Path | Purpose |
|------|------|---------|
| Wrapper | `~/.claude/hooks/statusline-monitor.sh` | Assembles line 1, pipes to ccstatusline |
| ccstatusline config | `~/.config/ccstatusline/settings.json` | Lines 2-3 widget definitions |
| Light variant | `~/.config/ccstatusline/settings-light.json` | Optional, for theme switching |
| Dark variant | `~/.config/ccstatusline/settings-dark.json` | Optional, for theme switching |
| Claude Code settings | `~/.claude/settings.json` | Points `statusLine.command` at the wrapper |
