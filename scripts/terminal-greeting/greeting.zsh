# Terminal Greeting — Illuminated Manuscript Style
# Source this file from ~/.zshrc to display a classical greeting on each new shell.
# Prepopulates the input buffer with "claude" so the user can hit Enter to begin.
#
# Design notes:
# - Truecolor pigments (gold leaf, lapis lazuli, sage green, rose madder)
#   sampled from the Met's 12th-century Manuscript Leaf with Initial M
# - Random sigil rotates through ✦ star, ◉ inner eye, ☥ ankh, ☉ sun, ☽ moon, ⁕ flower
# - Day-of-week planet glyph in top-right corner (☉ Sun, ☽ Mon, ♂ Tue, ☿ Wed, ♃ Thu, ♀ Fri, ♄ Sat)
# - Ogham brackets ᚛...᚜ wrap the greeting (pre-Christian Irish bookend marks)
# - Asterism ⁂ separates greeting from invocation ("and so it is woven")
# - Heraldic ⚜ fleur-de-lis counterpoints the floral ❦ at diagonal corners
# - Diamonds ◇⋄ woven into the gold borders alternate blue/green like manuscript interlace

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
  local sigils=(✦ ◉ ☥ ☉ ☽ ⁕)
  local sigil="${sigils[RANDOM % ${#sigils[@]} + 1]}"
  local planets=(☉ ☽ ♂ ☿ ♃ ♀ ♄)
  local planet="${planets[$(date +%w) + 1]}"
  local gold='\033[38;2;196;153;56m'
  local blue='\033[38;2;45;80;140m'
  local green='\033[38;2;110;140;87m'
  local rose='\033[38;2;204;90;140m'
  local dim='\033[2m'
  local n='\033[0m'
  local woven="${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇${green}⋄${blue}◇"
  echo ""
  echo "  ${gold}  ┌──${blue}❦${gold}──${green}❃${gold}──${woven}${gold}──${green}❃${gold}──${gold}⚜${gold}──┐  ${gold}${planet}${n}"
  echo "  ${green}  ❧${n}"
  echo "  ${green}  ❧${n}  ${blue}╔══╗${n}"
  echo "  ${green}  ❧${n}  ${blue}║${gold}${sigil}${blue}║${n}  ${gold}᚛${n} ${rose}${msg}${n} ${gold}᚜${n}"
  echo "  ${green}  ❧${n}  ${blue}╚══╝${n}  ${gold}⁂${n}  ${dim}${inv}${n}"
  echo "  ${green}  ❧${n}"
  echo "  ${gold}  └──${gold}⚜${gold}──${green}❃${gold}──${woven}${gold}──${green}❃${gold}──${blue}❦${gold}──┘${n}"
  echo ""
  print -z "claude"
}
_greet
