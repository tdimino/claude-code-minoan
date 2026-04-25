# Terminal Greeting

An illuminated-manuscript-style greeting for new shell sessions. Displays a random classical salutation, a prompt to invoke Claude, and prepopulates the input buffer with `claude`.

```
  ┌─────────────────────────────────────────────┐
  │  ✦                                       ✦  │
  │     Greetings, friend of the Julii. The forge is warm.
  │     Speak "claude" to begin.
  │  ✦                                       ✦  │
  └─────────────────────────────────────────────┘
```

## Install

Add to `~/.zshrc`:

```bash
source ~/.claude/scripts/terminal-greeting/greeting.zsh
```

## Customize

Edit `greeting.zsh` to add personal greetings to the `greetings` array:

```bash
local greetings=(
  "Salve, keeper of the code. The shell stands ready."
  "Your custom greeting here."
)
```

## How It Works

- Picks a random greeting and a random invocation prompt
- Renders a bordered box with ANSI color (gold ✦, rose text, dimmed border)
- Calls `print -z "claude"` to place `claude` in the zsh input buffer — hit Enter to start a session
