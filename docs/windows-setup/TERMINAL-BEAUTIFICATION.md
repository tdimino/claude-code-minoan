# Terminal Beautification on Windows

Oh My Posh is the Windows equivalent of oh-my-zsh—prompt themes, git status coloring, and segment-based customization for PowerShell and Windows Terminal. Combined with PSReadLine (predictive IntelliSense), Terminal-Icons (file icons in directory listings), and ccstatusline (Claude Code status line), you get a fully customized development terminal.

This guide assumes you've already completed the main [Windows setup](README.md). Everything here is optional—Claude Code works fine without it.

---

## 1. Nerd Fonts

Both Oh My Posh and ccstatusline use Nerd Fonts for icons and Powerline glyphs. Install one before configuring anything else.

### Install a Nerd Font

**Option A — via Oh My Posh** (easiest, after installing Oh My Posh in step 2):

```powershell
oh-my-posh font install meslo
```

This installs MesloLGS Nerd Font, the Oh My Posh default.

**Option B — via winget** (if you prefer JetBrains Mono):

```powershell
winget install DEVCOM.JetBrainsMonoNerdFont
```

Both fonts work with Oh My Posh and ccstatusline. MesloLGS is the Oh My Posh recommendation; JetBrains Mono is the ccstatusline recommendation. Pick whichever you prefer—the glyphs are identical.

### Configure Windows Terminal

Open Windows Terminal settings (`Ctrl+Shift+,`) and edit `settings.json`:

```json
{
  "profiles": {
    "defaults": {
      "font": {
        "face": "MesloLGS Nerd Font",
        "size": 12
      }
    }
  }
}
```

Replace `"MesloLGS Nerd Font"` with `"JetBrainsMono Nerd Font"` if you installed that one instead.

### Configure VS Code Terminal

In VS Code settings (`Ctrl+,`), set `terminal.integrated.fontFamily` to your Nerd Font name (e.g., `MesloLGS Nerd Font`).

---

## 2. Oh My Posh

### Install

```powershell
winget install JanDeDobbeleer.OhMyPosh --source winget
```

Close and reopen your terminal after installing.

### Set Up Your PowerShell Profile

Open your profile for editing:

```powershell
notepad $PROFILE
```

If PowerShell says the file doesn't exist, create it first:

```powershell
New-Item -Path $PROFILE -Type File -Force
notepad $PROFILE
```

Add this line:

```powershell
oh-my-posh init pwsh | Invoke-Expression
```

Save the file, then reload:

```powershell
. $PROFILE
```

If you get an execution policy error:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Choose a Theme

Browse all built-in themes:

```powershell
Get-PoshThemes
```

This renders every theme in your terminal so you can see what they look like. Once you find one you like, set it in your `$PROFILE`:

```powershell
oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH\jandedobbeleer.omp.json" | Invoke-Expression
```

Replace `jandedobbeleer` with the theme name you want. Popular choices:

| Theme | Style |
|-------|-------|
| `jandedobbeleer` | Default, clean with git info |
| `agnoster` | Classic Powerline look |
| `paradox` | Two-line with lots of context |
| `atomic` | Minimal with color accents |
| `night-owl` | Dark theme, developer-focused |
| `pure` | Minimal, fast |

### Useful Segments

Oh My Posh themes are JSON config files with segments. The most useful segments for development:

- **git** — branch name, ahead/behind, staged/modified counts
- **python** — active virtualenv and Python version
- **node** — Node.js version
- **executiontime** — how long the last command took
- **path** — current directory with truncation options
- **os** — OS icon

You can customize any theme by copying it to a local file and editing the segments. See the [Oh My Posh segment docs](https://ohmyposh.dev/docs/segments/scm/git) for the full list.

### Update

```powershell
winget upgrade JanDeDobbeleer.OhMyPosh --source winget
```

---

## 3. PSReadLine

PSReadLine ships with PowerShell—no installation needed. It adds readline-style keybindings, syntax highlighting, and predictive IntelliSense.

Add these lines to your `$PROFILE` (open with `notepad $PROFILE`):

```powershell
# Predictive IntelliSense based on command history
Set-PSReadLineOption -PredictionSource History

# Show predictions as a dropdown list instead of inline ghost text
Set-PSReadLineOption -PredictionViewStyle ListView

# Ctrl+D exits the shell (like bash/zsh)
Set-PSReadLineKeyHandler -Key Ctrl+d -Function DeleteCharOrExit
```

PowerShell 7+ enables syntax highlighting by default. If you're on Windows PowerShell 5.1, consider upgrading:

```powershell
winget install Microsoft.PowerShell
```

---

## 4. posh-git

Oh My Posh has its own git segment that shows branch, status, and ahead/behind counts. You only need posh-git if you want:

- Git tab completion (branch names, remote names, commands)
- A standalone git prompt without Oh My Posh

If you want it:

```powershell
Install-Module posh-git -Scope CurrentUser -Force
```

Add to your `$PROFILE`:

```powershell
Import-Module posh-git
```

If you're using Oh My Posh, posh-git's prompt is overridden by Oh My Posh's git segment—but the tab completion still works.

---

## 5. Terminal-Icons

Adds file and folder icons to `Get-ChildItem` / `ls` output. Microsoft recommends this alongside Oh My Posh.

```powershell
Install-Module Terminal-Icons -Repository PSGallery -Scope CurrentUser -Force
```

Add to your `$PROFILE`:

```powershell
Import-Module Terminal-Icons
```

Now `ls` shows icons next to filenames based on file type.

---

## 6. ccstatusline (Claude Code Status Line)

ccstatusline displays model info, git branch, token usage, context window metrics, session cost, and more in your Claude Code status line. It works on Windows.

### Install

**Option A — Bun** (recommended, faster):

```powershell
# Install Bun if you don't have it
irm bun.sh/install.ps1 | iex

# Run ccstatusline
bunx ccstatusline@latest
```

**Option B — Node.js**:

```powershell
npx ccstatusline@latest
```

Running the command with no piped input launches the interactive TUI configurator, which writes settings to your Claude Code `settings.json`.

### Windows Notes

- **Paths**: ccstatusline handles Windows-style paths (`C:\Users\...`) and UNC paths automatically
- **Custom commands**: If you add Custom Command widgets, use PowerShell-compatible commands instead of bash. For example, use `Split-Path -Leaf (Get-Location)` instead of `pwd | xargs basename`
- **Settings location**: `%USERPROFILE%\.claude\settings.json`
- **Nerd Fonts**: Required for Powerline mode. If you installed a Nerd Font in step 1, you're set

---

## Complete `$PROFILE` Example

Here's a ready-to-paste PowerShell profile that wires everything together. This replaces the simple init line from step 2—open with `notepad $PROFILE` and paste:

```powershell
# --- Oh My Posh ---
oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH\jandedobbeleer.omp.json" | Invoke-Expression

# --- PSReadLine ---
Set-PSReadLineOption -PredictionSource History
Set-PSReadLineOption -PredictionViewStyle ListView
Set-PSReadLineKeyHandler -Key Ctrl+d -Function DeleteCharOrExit

# --- posh-git (optional — tab completion for git) ---
# Import-Module posh-git

# --- Terminal-Icons (optional — file icons in ls) ---
# Import-Module Terminal-Icons
```

Uncomment the `Import-Module` lines for any optional modules you installed.

After saving, reload with `. $PROFILE` or restart your terminal.

---

## Troubleshooting

### Glyphs show as boxes or question marks

Your terminal isn't using the Nerd Font. Check:
1. Windows Terminal: `Ctrl+Shift+,` → verify `font.face` is set to your Nerd Font
2. VS Code: check `terminal.integrated.fontFamily` in settings

### Oh My Posh prompt doesn't appear

Make sure the init line is in your `$PROFILE` and that you reloaded it:

```powershell
. $PROFILE
```

Check which profile file PowerShell is using:

```powershell
$PROFILE
```

### PSReadLine predictions don't show

Requires PowerShell 7.2+ for `ListView` mode. Check your version:

```powershell
$PSVersionTable.PSVersion
```

If you're on 5.1, upgrade: `winget install Microsoft.PowerShell`

### ccstatusline Powerline arrows broken

Same fix as Oh My Posh glyphs—set your terminal font to a Nerd Font. Both tools use the same Powerline glyph range.
