# Terminal Greeting — Antediluvian Minoan Style
# Source this file from ~/.zshrc to display a Bronze Age greeting on each new shell.
# Prepopulates the input buffer with "claude" so the user can hit Enter to begin.
#
# Pigments sampled from Knossos frescoes (Dolphin Fresco, Bull-Leaping Fresco,
# Saffron Gatherer, Ladies in Blue) and modern Crete (olive groves, Aegean shallows).
#
# Greeting texts draw from Thera, Knossos & Minos — the cosmogonic Deep (Tehom),
# the Kotharat fate-determining goddesses (KTU 1.24), Athirat/Asherah (qnyt ilm),
# the Xeste 3 saffron rite, Skoteino cave, Linear A tablets, murex purple.
#
# Structural elements:
# - Linear A brackets 𐘀...𐘁 (AB001/AB002) wrap the greeting
# - Wave band ∿· replaces diamond interlace (Aegean for Celtic knot)
# - Moon phase replaces planetary almanac (Minoan lunar calendar)
# - PUA dolphin (U+E503) margin replaces vine ❧ (Knossos Queen's Megaron)
# - Rotating Linear A sigils in the initial box
# - Sun disc ☉ as solar/chthonic separator

_greet_minoan() {
  local greetings=(
    "The forge is lit. The bronze awaits the hammer."
    "Tehom stirs beneath. The deep remembers."
    "Rise, keeper of the tablets. The archive opens."
    "The Kotharat attend. The thread is dyed."
    "Skoteino opens its mouth. You know the way down."
    "The priestess gathers saffron. The rite begins."
    "Athirat walks the shore. The sea is hers."
    "From Kaphtor the craftsman came. The tools are shaped."
    "The murex yields its purple. Beauty from the shell."
    "Nine years pass. Minos descends to the cave."
    "Membliaros — waters without light. Now, light."
    "The horns catch the morning sun. Begin."
    "The seal is pressed. The clay remembers."
    "What Greek conceals, the root reveals."
  )
  local invocations=(
    "The artificer is awake."
    "The forge brightens."
    "The tablet is unsealed."
    "Kothar answers."
    "The Kotharat have set the thread."
    "The bronze remembers your hand."
    "What Linear A conceals, the root restores."
    "The deep gives up its names."
  )
  local msg="${greetings[RANDOM % ${#greetings[@]} + 1]}"
  local inv="${invocations[RANDOM % ${#invocations[@]} + 1]}"

  local sigils=(𐘀 𐙃 𐘠 𐙋 𐙍 𐙰)
  local sigil="${sigils[RANDOM % ${#sigils[@]} + 1]}"

  local moon_phase=$(python3 -c "
from datetime import date
d=(date.today()-date(2000,1,6)).days
p=int((d%29.53059)/29.53059*8)%8
print(['🌑','🌒','🌓','🌔','🌕','🌖','🌗','🌘'][p])
")

  # Knossos fresco pigments — truecolor ANSI
  local saffron='\033[38;2;218;165;32m'
  local blue='\033[38;2;30;75;145m'
  local olive='\033[38;2;90;115;55m'
  local teal='\033[38;2;45;125;140m'
  local ochre='\033[38;2;178;65;40m'
  local purple='\033[38;2;130;45;95m'
  local dim='\033[2m'
  local n='\033[0m'

  # Aegean wave band — alternating blue/teal (replaces diamond interlace)
  local wave="${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿${teal}·${blue}∿"

  # Phaistos Disc signs (Noto Sans Symbols 2) + PUA dolphin (MinoanGlyphs.ttf)
  local rosette=$'\U101F5'
  local bee=$'\U101F1'
  local lily=$'\U101F6'
  local dolphin=$'\UE503'
  local swallow=$'\UE504'

  echo ""
  echo "  ${saffron}  ┌──${rosette}${saffron}──${bee}${saffron}──${wave}${saffron}──${bee}${saffron}──${lily}${saffron}──┐  ${dim}${moon_phase}${n}"
  echo "  ${olive}  ${swallow}${n}"
  echo "  ${olive}  ${dolphin}${n}  ${blue}╔══╗${n}"
  echo "  ${olive}  ${swallow}${n}  ${blue}║${saffron}${sigil}${blue}║${n}  ${saffron}𐘀${n} ${ochre}${msg}${n} ${saffron}𐘁${n}"
  echo "  ${olive}  ${dolphin}${n}  ${blue}╚══╝${n}  ${saffron}☉${n}  ${dim}${purple}${inv}${n}"
  echo "  ${olive}  ${swallow}${n}"
  echo "  ${saffron}  └──${lily}${saffron}──${bee}${saffron}──${wave}${saffron}──${bee}${saffron}──${rosette}${saffron}──┘${n}"
  echo ""
}
_greet_minoan
