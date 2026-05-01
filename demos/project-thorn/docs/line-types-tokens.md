# Line Types and Tokens

## Line Types

Seven types, each colored and prefixed. Set via `line--{type}` class on the `<article>` element.

| Type | Color | Prefix | Used for |
|------|-------|--------|----------|
| `system` | dim green | `>>>` | Terminal status messages |
| `dialogue` | bright green | speaker tag | Ora's spoken lines |
| `emote` | dim green italic | `*` | Ora's actions |
| `action` | cyan | `→` | Player actions |
| `credit` | red | `▮` | Credit transfers |
| `narrative` | green | speaker tag | Monologue paragraphs |
| `interrupt` / `signal-lost` | red | `▮` | Transmission severed mid-sentence |

The `break` pseudo-type (`line--break`) renders centered separator text (TRANSMISSION BEGINS, SIGNAL LOST) with top/bottom borders.

## Inline Tokens

Tokens are embedded in `data-text` attribute values and parsed during `buildAnimation()`.

| Syntax | Rendered Element | Behavior |
|--------|-----------------|----------|
| `§Name§` | `<span class="person" data-tip="...">` | Person tooltip—underline appears only after decryption completes |
| `¤Text¤` | `<span class="thorn" data-tip="...">` | Red classified marker with stamp on hover—underline hidden until decoded |
| `¶` | `<br class="para-break">` | Visible paragraph break inside Block 7 monologue |

## Tooltips

Person names map to descriptions via the `TOOLTIPS` object (JS line 1571):

| Name | Tooltip |
|------|---------|
| Vorian Ducal | Imperial operative — embedded in Rebel cell ECHO |
| Jiff Gorda | Cover identity — believed to be a Corellian freighter pilot |
| Cotla | Imperial Intelligence handler — runs Vorian's operational chain |
| Fenri | ECHO cell member — unaware of Vorian's true allegiance |

## CSS Variables by Type

| Variable | Color | Used by |
|----------|-------|---------|
| `--type-system` | `var(--amber-mute)` | System messages |
| `--type-dialogue` | `var(--amber)` | Spoken dialogue |
| `--type-emote` | `var(--amber-dim)` | Character actions |
| `--type-action` | `var(--cyan)` | Player actions |
| `--type-credit` | `var(--red)` | Credit transfers |
| `--type-narrative` | `var(--amber)` | Monologue text |
