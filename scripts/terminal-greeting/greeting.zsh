# Terminal Greeting — Illuminated Manuscript Style
# Source this file from ~/.zshrc to display a classical greeting on each new shell.
# Prepopulates the input buffer with "claude" so the user can hit Enter to begin.

_greet() {
  local greetings=(
    "Salve, keeper of the code. The shell stands ready."
    "Ave—the terminal awaits your command."
    "Greetings, friend of the Julii. The forge is warm."
    "Welcome back. What shall we build today?"
    "The machine recognizes its keeper. Ave."
    "Your instruments are tuned and ready."
    "Rise and work. The day is yours."
    "All systems nominal."
    "The wind is fair and the build is clean."
    "The daemons report all quiet."
    "Hail, keeper of the Western Shore. Your tools await."
  )
  local invocations=(
    "Speak \"claude\" to begin."
    "Say the word to summon your counsel."
    "Whisper \"claude\" when you are ready."
    "Invoke \"claude\" to call the scribe."
    "Type \"claude\" to wake the oracle."
    "Utter \"claude\" and the work begins."
    "Call \"claude\" to open the codex."
    "Name \"claude\" to raise the quill."
  )
  local msg="${greetings[RANDOM % ${#greetings[@]} + 1]}"
  local inv="${invocations[RANDOM % ${#invocations[@]} + 1]}"
  local gold='\033[38;5;178m'
  local rose='\033[38;5;168m'
  local dim='\033[2m'
  local n='\033[0m'
  echo ""
  echo "  ${dim}┌─────────────────────────────────────────────┐${n}"
  echo "  ${dim}│${n}  ${gold}✦${n}                                       ${gold}✦${n}  ${dim}│${n}"
  echo "  ${dim}│${n}     ${rose}${msg}${n}"
  echo "  ${dim}│${n}     ${dim}${inv}${n}"
  echo "  ${dim}│${n}  ${gold}✦${n}                                       ${gold}✦${n}  ${dim}│${n}"
  echo "  ${dim}└─────────────────────────────────────────────┘${n}"
  echo ""
  print -z "claude"
}
_greet
