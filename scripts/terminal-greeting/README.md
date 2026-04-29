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

---

# Minoan Greeting

An Antediluvian-Minoan greeting for new shell sessions. Each launch displays a random scholarly salutation framed by a Bronze Age tablet rendered in truecolor ANSI, with `claude` prepopulated in the input buffer.

```
  ┌──𐇵──𐇱──∿·∿·∿·∿·∿·∿·∿·∿·∿·∿·∿·∿·∿·∿·∿·∿·∿──𐇱──𐇶──┐  🌓
  (swallow)
  (dolphin)  ╔══╗
  (swallow)  ║𐘀║  𐘀 The forge is lit. The bronze awaits the hammer. 𐘁
  (dolphin)  ╚══╝  ☉  Speak "claude" to wake the artificer.
  (swallow)
  └──𐇶──𐇱──∿·∿·∿·∿·∿·∿·∿·∿·∿·∿·∿·∿·∿·∿·∿·∿·∿──𐇱──𐇵──┘
```

Corner ornaments are Phaistos Disc signs (𐇵 ROSETTE, 𐇶 LILY, 𐇱 BEE) rendered by Noto Sans Symbols 2. The margin alternates swallow (U+E504) and dolphin (U+E503) PUA glyphs from MinoanGlyphs.ttf.

## Install

Add to `~/.zshrc` (replaces or supplements the Illuminated Manuscript greeting):

```bash
source ~/.claude/scripts/terminal-greeting/greeting-minoan.zsh
```

Requires: JetBrains Mono Nerd Font, Noto Sans Linear A, Noto Sans Symbols 2 (Phaistos Disc signs), and MinoanGlyphs.ttf (custom PUA dolphin + swallow). All are configured in the Ghostty font cascade — see `ghostty/config`.

## Pigments

Colors sampled from Knossos frescoes (Dolphin Fresco, Bull-Leaping Fresco, Saffron Gatherer, Ladies in Blue) and modern Crete:

| Pigment | Source | RGB | Used for |
|---------|--------|-----|----------|
| Egyptian Blue | Dolphin Fresco, Ladies in Blue | `30,75,145` | Borders, wave band, initial box |
| Red Ochre | Bull-Leaping Fresco | `178,65,40` | Greeting text |
| Saffron | Saffron Gatherer, crocus fields | `218,165,32` | Gold borders, sigil, sun disc, Linear A brackets |
| Olive Green | Cretan hillsides | `90,115,55` | Dolphin margin |
| Tyrian Purple | Murex dye trade | `130,45,95` | Invocation text |
| Aegean Teal | Shallow Cretan sea | `45,125,140` | Wave band accent (alternates with Egyptian blue) |

## Structural Elements

| Element | Character(s) | Source |
|---------|-------------|--------|
| Linear A brackets | 𐘀...𐘁 (U+10600, U+10601) | AB001/AB002 — frame the greeting like Ogham ᚛...᚜ |
| Wave band | ∿· alternating blue/teal | Aegean sea — replaces diamond interlace ◇⋄ |
| Margin glyphs | Alternating swallow (U+E504) and dolphin (U+E503) | Spring Fresco + Queen's Megaron |
| Rotating sigils | 𐘀 𐙃 𐘠 𐙋 𐙍 𐙰 | Linear A syllabograms in the initial box |
| Moon phase | 🌑🌒🌓🌔🌕🌖🌗🌘 | Computed live — Minoan lunar calendar |
| Sun disc | ☉ (U+2609) | Solar/chthonic separator |
| Corner ornaments | 𐇵 ROSETTE / 𐇶 LILY (Phaistos Disc) | Noto Sans Symbols 2 |
| Border bees | 𐇱 BEE (Phaistos Disc) | Malia bee pendant motif |

## Required Fonts

| Font | Provides | Install |
|------|----------|---------|
| JetBrains Mono Nerd Font | Primary terminal font + Nerd Font glyphs | `brew install --cask font-jetbrains-mono-nerd-font` |
| Noto Sans Linear A | Linear A brackets (𐘀𐘁) + sigils | [Google Fonts](https://fonts.google.com/noto/specimen/Noto+Sans+Linear+A) |
| Noto Sans Symbols 2 | Phaistos Disc signs (𐇵𐇱𐇶) | `brew install --cask font-noto-sans-symbols-2` |
| MinoanGlyphs.ttf | PUA dolphin (U+E503), swallow (U+E504) + 12 other Minoan glyphs | `python3 scripts/minoan-glyphs/build.py --install` |

## Greeting Texts

Each greeting draws from *Thera, Knossos & Minos* — the cosmogonic Deep, the priestess cult, the forge of Kothar, the undeciphered tablets.

### Glossary

| Term | Meaning |
|------|---------|
| *Tehom* | Hebrew "the Deep" (תְּהוֹם), cognate of Babylonian Tiamat — primordial waters |
| *Kotharat* | *kṯrt* — seven fate-determining goddesses (KTU 1.24), feminine form of Kothar. *bnt hll* (Daughters of the Crescent Moon), *snnt* (the Swallows). They dye the thread before it is cut. Cognate of Greek *Kythereia* via López-Ruiz |
| *Skoteino* | "Dark" — Minoan cave system as sacred labyrinth-womb |
| *Athirat* | Ugaritic sea-goddess (*rabbatu ʾAṯiratu yammi*), creatress of the gods (*qnyt ilm*) |
| *Kaphtor* | Bronze Age name for Crete (Hebrew כַּפְתּוֹר, Ugaritic *Kaptaru*) |
| *Membliaros* | Astour's etymology: מם־בלי־אר, "waters without light" (Orphic/Sethian cosmogony) |
| *p-ʿ-r* | Semitic root connecting Hebrew *tipʿeret* (beauty/glory) → Greek *porphyra* (purple) |
| *Nine years* | Minos consulted Zeus at the Dictaean cave every nine years (Odyssey 19.178–179) |

## Customize

Edit `greeting-minoan.zsh` to add personal greetings to the `greetings` array. The pigments, sigils, and rendering tier are all defined in single variables near the top of the function — easy to swap.

## Design Philosophy

The Illuminated Manuscript greeting (above) is a medieval codex — gold leaf, lapis lazuli, Ogham brackets, Celtic interlace. The Minoan greeting is a seal impression pressed into wet clay — Egyptian blue, red ochre, saffron, olive green. Where one speaks Latin, the other speaks in the language of *Thera, Knossos & Minos*: the forge of Kothar, the deep of Tehom, the priestess at Xeste 3, the undeciphered tablets. Linear A brackets frame the greeting like Ogham but whose phonetic values remain disputed — a visual reminder that the Minoan world resists easy translation.
