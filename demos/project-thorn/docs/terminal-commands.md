# Terminal Commands

The command prompt at the bottom accepts in-universe commands. 25+ lore-aware responses plus 13 atmospheric error messages for unrecognized input.

## Commands

| Command | Response |
|---------|----------|
| `help` | List all available commands |
| `ls` | File listing: intercept.log, thorn.enc, ora-profile.dat... |
| `whoami` | IMP-INT operator identity, clearance, handler |
| `ping ora` | Request timeout—host unreachable, signal lost |
| `ping chimera` | ISD Chimaera relay nominal |
| `scan` | Mos Eisley sector bio-signatures, Bothan matches |
| `status` | Channel state, asset cover, project priority |
| `cat intercept.log` | Points to transcript above |
| `cat thorn.enc` | Encrypted—clearance required |
| `history` | Session command log with intercept milestones |
| `date` | Imperial standard date/time |
| `uptime` | Channel uptime since establishment |
| `clear` | Clears command output |

## Denied Commands

These commands are recognized but refused with Imperial authority responses. They play a distinct DENY sound (square-wave double-beep).

| Command | Response |
|---------|----------|
| `sudo` | Access denied — Imperial override not authorized |
| `rm` | Deletion prohibited — intercept records are Imperial property |
| `kill` | Process termination denied — active surveillance |
| `exit` | Session cannot be terminated — mandatory monitoring |
| `decrypt` | Decryption not authorized at current clearance |
| `man` | Manual pages restricted — consult your handler |

## Unrecognized Commands

Any input not matching a known command draws from 13 atmospheric error messages. Examples:

- `READ-ONLY TERMINAL · Channel θ-7 sealed for evidence preservation`
- `OPERATOR CLEARANCE REVOKED · Contact AGENT COTLA for reinstatement`
- `SIGNAL DEGRADED · Retransmission buffer full`

The selection is random but never repeats consecutively.

## Audio

Valid commands trigger a 0.4s burst from `01-scifi-computer-terminal-unfa.mp3` at a random offset. Denied and unrecognized commands produce a square-wave double-beep (220Hz → 160Hz). Both respect the mute toggle.

## Adding Commands

Add to the `TERMINAL_CMDS` object (line 2464 in index.html):

```js
TERMINAL_CMDS['newcommand'] = 'Response text here.\nSecond line.';
```

For denied commands, add to the `DENIED_CMDS` Set (line 2522).
