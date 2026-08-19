# Ghostty Theme Switching
# Source this file from ~/.zshrc to get dark/light/cream commands.
# Requires Ghostty and macOS.

# An alias sharing a function's name is a zsh parse error at definition time
# that aborts the rest of this file — clear any before defining.
for _f in dark light cream knossos akrotiri alabaster; do
  unalias "$_f" 2>/dev/null
done
unset _f

_ghostty_set_theme() {
  local config="$HOME/Library/Application Support/com.mitchellh.ghostty/config"
  local new_theme="$1"
  sed -i '' "s/^theme = .*/theme = ${new_theme}/" "$config"
  osascript -e '
    tell application "System Events"
      tell process "Ghostty"
        click menu item "Reload Configuration" of menu "Ghostty" of menu bar item "Ghostty" of menu bar 1
      end tell
    end tell
  ' 2>/dev/null
  _ghostty_warn_stale_tuis
}

# Codex and Claude Code sample the terminal background once at startup (OSC 11 /
# COLORFGBG) and never re-detect — no DEC 2031 support. Sessions carried across
# a theme flip keep stale colors (washed-out dark-styled text on light, or vice
# versa) until restarted. codex keeps history across restarts (codex resume);
# claude resumes with --resume.
_ghostty_warn_stale_tuis() {
  local n_codex
  n_codex=$(pgrep -x codex 2>/dev/null | wc -l | tr -d ' ')
  if [ "${n_codex:-0}" -gt 0 ]; then
    echo "⚠ ${n_codex} codex session(s) still styled for the previous theme — restart them (codex resume) to re-detect."
  fi
}

dark() {
  osascript -e 'tell application "System Events" to tell appearance preferences to set dark mode to true'
  _ghostty_set_theme "dark:Catppuccin Mocha,light:Alabaster"
}

light() {
  osascript -e 'tell application "System Events" to tell appearance preferences to set dark mode to false'
  _ghostty_set_theme "dark:Catppuccin Mocha,light:Alabaster"
}

cream() {
  osascript -e 'tell application "System Events" to tell appearance preferences to set dark mode to false'
  _ghostty_set_theme "Cream"
}

# Named knossos, not knossot — ~/.zshrc aliases knossot to cd into the knossot
# repo, and reusing that name here would be the parse error guarded against above.
knossos() {
  osascript -e 'tell application "System Events" to tell appearance preferences to set dark mode to true'
  _ghostty_set_theme "Knossot"
}

akrotiri() {
  osascript -e 'tell application "System Events" to tell appearance preferences to set dark mode to false'
  _ghostty_set_theme "Akrotiri"
}

alabaster() {
  osascript -e 'tell application "System Events" to tell appearance preferences to set dark mode to false'
  _ghostty_set_theme "Alabaster"
}
