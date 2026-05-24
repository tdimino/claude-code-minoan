# Windows Troubleshooting

Common issues and fixes for Claude Code + Minoan extensions on Windows.

---

## `python3` is not recognized

Windows installs Python as `python`, not `python3`. Three fixes:

**Option A** — Python 3.12+ from python.org or the Microsoft Store installs a `python3.exe` alias automatically. Verify: `python3 --version`

**Option B** — Create an alias in your PowerShell profile:
```powershell
notepad $PROFILE
# Add this line:
Set-Alias python3 python
# Save and restart terminal
```

**Option C** — Use the Python launcher: `py -3 --version`

Hooks that invoke `python3` will fail if none of these work. The setup script checks for both `python3` and `python`.

---

## PowerShell blocks the setup script

If you see "running scripts is disabled on this system":

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

This allows locally-created scripts while still blocking scripts downloaded from the internet that aren't signed.

---

## Am I in PowerShell or CMD?

- **PowerShell**: prompt shows `PS C:\Users\YourName>`
- **CMD**: prompt shows `C:\Users\YourName>`

The Claude Code installer has different commands for each. The setup script requires PowerShell.

To switch to PowerShell from CMD, type `powershell` and press Enter.

---

## `claude` command not found after installing

This is the most common Windows install issue ([#42337](https://github.com/anthropics/claude-code/issues/42337)). The installer puts `claude.exe` at `%USERPROFILE%\.local\bin\` but doesn't always add that directory to your PATH.

**Step 1** — Confirm the binary exists:
```powershell
Test-Path "$env:USERPROFILE\.local\bin\claude.exe"
```

If that returns `True`, the install worked — it's just a PATH problem.

**Step 2** — Add to PATH:
```powershell
$currentPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
[Environment]::SetEnvironmentVariable('PATH', "$currentPath;$env:USERPROFILE\.local\bin", 'User')
```

**Step 3** — Close the terminal completely and open a new one. Then:
```powershell
claude --version
```

If Step 1 returned `False`, the installer didn't finish. Re-run it:
```powershell
irm https://claude.ai/install.ps1 | iex
```

---

## Where is `~/.claude/` on Windows?

`~` in PowerShell expands to `C:\Users\YourName\`. So `~/.claude/` is:

```
C:\Users\YourName\.claude\
```

You can open it in Explorer:
```powershell
explorer $HOME\.claude
```

---

## Bash hooks don't run

The 20 bash hooks (`.sh` files) need a bash interpreter. Two options:

**Option A** — Install Git for Windows (`winget install Git.Git`), which includes Git Bash. Claude Code can use this as its shell.

**Option B** — Install WSL2 (`wsl --install`) and run Claude Code from inside the Ubuntu terminal.

If you chose "Python hooks only" during setup, bash hooks weren't installed and this isn't an issue.

---

## `npm install` fails for SQLite tracker

`better-sqlite3` needs to compile native code. Make sure you have:

1. Node.js LTS installed (`winget install OpenJS.NodeJS.LTS`)
2. `better-sqlite3` usually ships prebuilt binaries, so it should just work. If it tries to compile from source, you need Visual Studio Build Tools with the "Desktop development with C++" workload: `winget install Microsoft.VisualStudio.2022.BuildTools` then select the C++ workload in the installer.

If that's too much trouble, skip the SQLite tracker — the JSON-only mode works for everything.

---

## Git operations fail inside Claude Code

If Claude Code can't find `git`, make sure Git for Windows is on your PATH:

```powershell
git --version
```

If this works in your terminal but not in Claude Code, restart Claude Code — it reads PATH at startup.

---

## MCP servers fail to connect

```powershell
claude mcp list
```

If servers show as disconnected:
- Make sure `npx` works: `npx --version` (comes with Node.js)
- Try removing and re-adding: `claude mcp remove playwright && claude mcp add playwright -c npx -a "@playwright/mcp@latest" -s user`

---

## Claude Code is slow on Windows

This is normal for the first session — it indexes your project. Subsequent sessions are faster.

If it stays slow:
- Make sure you're not running from a network drive
- Exclude your project folder from Windows Defender real-time scanning (Settings > Virus & threat protection > Exclusions)
- Close other resource-heavy apps
