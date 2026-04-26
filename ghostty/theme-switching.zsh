# Ghostty Theme Switching
# Source this file from ~/.zshrc to get dark/light/cream commands.
# Requires Ghostty and macOS.

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
}

dark() {
  osascript -e 'tell application "System Events" to tell appearance preferences to set dark mode to true'
  _ghostty_set_theme "dark:Catppuccin Mocha,light:Catppuccin Latte"
}

light() {
  osascript -e 'tell application "System Events" to tell appearance preferences to set dark mode to false'
  _ghostty_set_theme "dark:Catppuccin Mocha,light:Catppuccin Latte"
}

cream() {
  osascript -e 'tell application "System Events" to tell appearance preferences to set dark mode to false'
  _ghostty_set_theme "Cream"
}
