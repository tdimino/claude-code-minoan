# Terminal Greeting

An illuminated-manuscript-style greeting for new shell sessions. Each shell launch displays a random classical salutation framed by a hand-crafted Unicode codex page, with `claude` prepopulated in the input buffer.

```
  ┌──❦──❃──◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇──❃──⚜──┐  ☉
  ❧
  ❧  ╔══╗
  ❧  ║✦║  ᚛ Greetings, friend of the Julii. The forge is warm. ᚜
  ❧  ╚══╝  ⁂  Speak "claude" to begin.
  ❧
  └──⚜──❃──◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇⋄◇──❃──❦──┘
```

## Install

Add to `~/.zshrc`:

```bash
source ~/.claude/scripts/terminal-greeting/greeting.zsh
```

Requires a Nerd Font (e.g., JetBrains Mono Nerd Font) for proper glyph rendering.

## Pigments

Colors sampled from the Met's 12th-century *Manuscript Leaf with Initial M* — true ANSI 24-bit color matches the medieval pigment palette:

| Pigment | RGB | Used for |
|---------|-----|----------|
| Gold leaf | `196,153,56` | Borders, sigil, asterism |
| Lapis lazuli | `45,80,140` | Initial box, ❦ florets, even diamonds |
| Sage green | `110,140,87` | ❧ vine, ❃ leaves, odd diamonds |
| Rose madder | `204,90,140` | Greeting text |

## Mystical Vocabulary

Each launch composes a unique manuscript opening from these elements:

- **Random sigil** in the initial box: ✦ star, ◉ inner eye, ☥ ankh, ☉ sun, ☽ moon, ⁕ flower
- **Day-of-week planet** in the top-right corner: ☉ Sun, ☽ Mon, ♂ Tue, ☿ Wed, ♃ Thu, ♀ Fri, ♄ Sat — turns each opening into a small almanac
- **Ogham brackets** ᚛...᚜ wrap the greeting (pre-Christian Irish bookend marks)
- **Asterism** ⁂ separates greeting from invocation ("and so it is woven")
- **Heraldic counterpoint** — ⚜ fleur-de-lis paired with ❦ floral hearts at diagonal corners
- **Woven interlace** — ◇⋄ diamonds in alternating blue/green run through the gold borders like a manuscript chain

## Customize

Edit `greeting.zsh` to add personal greetings to the `greetings` array:

```bash
local greetings=(
  "Salve, keeper of the code. The shell stands ready."
  "Your custom greeting here."
)
```

The pigments, sigils, and planets are easy to swap — they're all defined in single arrays near the top of the function.

## How It Works

- Picks a random greeting, invocation, and sigil
- Looks up today's planetary glyph by `date +%w`
- Renders the manuscript page with truecolor ANSI escapes
- Calls `print -z "claude"` to place `claude` in the zsh input buffer — hit Enter to start a session, or type to replace
