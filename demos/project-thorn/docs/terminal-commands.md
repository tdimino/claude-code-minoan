# Terminal Commands

The command prompt at the bottom accepts in-universe commands. A virtual filesystem with directory navigation, 25+ lore-aware responses, and 13 atmospheric error messages for unrecognized input.

## Authentication

| Command | Response |
|---------|----------|
| `auth <passphrase>` | Authenticate for Omega clearance. Passphrase: `alderaan` |

On success: grants Omega clearance, enables clickable dossier cross-links on all `§`-marked person names and `¤`-marked classified names in the transcript. Clicking a linked name opens its dossier modal. Visual indicator on hover: green glow for `.person` spans, red glow for `.thorn` spans. Re-running after authentication returns `ALREADY AUTHENTICATED`. Failed passphrase returns `AUTHENTICATION FAILED` and logs the attempt.

Linked names: Vorian Ducal, Jiff Gorda, Agent Cotla, Fenri, Project Thorn, ECHO.

## Filesystem Commands

The terminal implements a virtual filesystem with three directories (`cotla-directives/`, `signal-archive/`, `dossiers/`) and various intelligence files. The prompt sigil updates to show the current directory.

| Command | Response |
|---------|----------|
| `ls` | List files in current directory (directories shown with trailing `/`) |
| `ls <path>` | List files in a specific directory |
| `cat <file>` | Display file contents; encrypted files (`.enc`) return denial |
| `cat <dir/file>` | Relative paths work from any directory |
| `cd <dir>` | Change directory; supports `..`, `/`, `~` |
| `pwd` | Print current working directory |

## Static Commands

| Command | Response |
|---------|----------|
| `help` | List all available commands |
| `whoami` | IMP-INT operator identity, clearance, handler |
| `ping ora` | Request timeout—host unreachable, signal lost |
| `ping chimera` | ISD Chimaera relay nominal |
| `scan` | Mos Eisley sector bio-signatures, Bothan matches |
| `status` | Channel state, asset cover, project priority |
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

**Static commands** — add to the `TERMINAL_CMDS` object:

```js
TERMINAL_CMDS['newcommand'] = 'Response text here.\nSecond line.';
```

**Function commands** — add to `TERMINAL_FNS` for commands that need arguments or state:

```js
TERMINAL_FNS['newcmd'] = function(args) {
  return 'Response for: ' + args;
};
```

`TERMINAL_FNS` is checked before `TERMINAL_CMDS`. The function receives the command arguments as a trimmed string.

For denied commands, add to the `DENIED_CMDS` Set.

**Filesystem files** — add entries to the `FILESYSTEM` object. String values are file contents, `null` values are encrypted, and nested objects are directories.

## Input Shortcuts

| Key | Action |
|-----|--------|
| `Up` / `Down` | Cycle through command history |
| `Tab` | Autocomplete command or argument |
| `Ctrl+U` | Clear the current input line |

### Command History

Up/Down arrows navigate previous commands (most recent first). No consecutive duplicates stored. Capped at 50 entries. History resets on page reload (not persisted).

### Tab Autocomplete

Tab completes based on cursor context:

| Context | Completes against |
|---------|-------------------|
| Bare input (no space) | All command names (`TERMINAL_FNS` + `TERMINAL_CMDS` + `clear`) |
| `dossier <partial>` | Dossier keys from `DOSSIERS` object |
| `cat <partial>` / `ls <partial>` / `cd <partial>` | Filesystem entries in the current (or specified) directory; `cd` filters to directories only |

Single match: completes inline. Multiple matches: displays all options below the prompt, subsequent Tab presses cycle through them. Tab state resets on any other keypress.
