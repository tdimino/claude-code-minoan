# Claude Code + Minoan Extensions — Windows Setup

This guide walks you through setting up Claude Code and the Minoan extension pack on a Windows PC. The Minoan pack adds 96 skills, 19 slash commands, lifecycle hooks, and MCP server integrations on top of the stock Claude Code experience.

Most of the pack works natively on Windows. A few components (bash shell scripts, macOS terminal config) are skipped — the setup script handles this automatically.

---

## Prerequisites

You need four things installed before running the setup script. All install via `winget` from PowerShell.

### 1. Windows Terminal (recommended)

Windows Terminal is a modern terminal that replaces the old `cmd.exe` window. If you're on Windows 11 it's probably already installed.

```powershell
winget install Microsoft.WindowsTerminal
```

### 2. Claude Code

Claude Code's native installer bundles its own Node.js runtime — you don't need to install Node separately for Claude Code itself.

Open **PowerShell** (not CMD) and run:

```powershell
irm https://claude.ai/install.ps1 | iex
```

If you're in **CMD** instead of PowerShell (your prompt shows `C:\>` without a `PS` prefix):

```batch
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

After installation, close and reopen your terminal, then verify:

```powershell
claude --version
```

**If `claude` is still not recognized** after restarting the terminal, the installer didn't add its directory to your PATH (this is a [known issue](https://github.com/anthropics/claude-code/issues/42337)). Fix it:

```powershell
$currentPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
[Environment]::SetEnvironmentVariable('PATH', "$currentPath;$env:USERPROFILE\.local\bin", 'User')
```

Close and reopen the terminal again, then `claude --version` should work.

You'll also need an Anthropic account. Claude Code works on all paid plans:
- **Pro** ($20/mo) — includes Claude Code with a 5-hour rolling quota. Fine for exploring and daily use.
- **Max** ($100 or $200/mo) — 5x or 20x the Pro quota. Only needed if you're using it all day.
- **API** (pay-per-token) — for programmatic use. Set up at [console.anthropic.com](https://console.anthropic.com).

### 3. Git for Windows

Git for Windows is important because it gives Claude Code access to a Bash shell. Without it, Claude Code falls back to PowerShell, which works but limits some tool integrations.

```powershell
winget install Git.Git
```

Close and reopen your terminal after installing. Verify:

```powershell
git --version
```

During installation, if prompted, choose "Git from the command line and also from 3rd-party software" so `git` is available everywhere.

### 4. Python 3.10+

Many Minoan hooks and skill scripts are written in Python. Install Python 3.12:

```powershell
winget install Python.Python.3.12
```

Close and reopen your terminal. Verify:

```powershell
python --version
```

**Important:** Windows uses `python` (not `python3`). Python 3.12+ from the Microsoft Store or python.org also installs a `python3.exe` alias, but if you installed via `winget`, you may only have `python`. Both work — the setup script handles this.

### Optional but Recommended: Node.js

Needed for the SQLite session tracker and for MCP servers that use `npx` (Playwright, Chrome DevTools). The HTTP-based MCP servers (Figma, shadcn) work without it.

```powershell
winget install OpenJS.NodeJS.LTS
```

### Optional: VS Code

The Claude Code VS Code extension gives you Claude inside your editor:

```powershell
winget install Microsoft.VisualStudioCode
```

Then install the "Claude Code" extension from the VS Code marketplace.

---

## Quick Start

### Step 1: Clone the repo

```powershell
cd ~\Desktop
git clone https://github.com/tdimino/claude-code-minoan.git
```

### Step 2: Allow PowerShell scripts

Windows blocks unsigned scripts by default. Allow locally-created scripts:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 3: Run the setup script

```powershell
cd ~\Desktop\claude-code-minoan
.\docs\windows-setup\setup-windows.ps1
```

The script walks you through an interactive menu — you choose which components to install:

- **Skills**: all 96, core development only, or pick individual ones
- **Commands**: 19 slash commands (all pure markdown, all work)
- **Hooks**: Python lifecycle hooks (bash hooks are skipped with a note)
- **MCP Servers**: Playwright, Chrome DevTools, Figma, shadcn
- **SQLite Tracker**: optional, requires Node.js

### Step 4: Log into Claude Code

```powershell
claude
```

Follow the login prompts. You'll authenticate via your browser.

### Step 5: Verify the installation

Inside a Claude Code session, try:

```
What skills do you have available?
```

You should see the installed skills listed in the system context.

---

## What's Installed (and What's Not)

| Component | Status | Details |
|-----------|--------|---------|
| Skills (96) | ~90% work | Markdown + Python scripts, mostly cross-platform |
| Commands (19) | All work | Pure markdown, no OS dependency |
| Python hooks (31) | ~85% work | A few reference Unix-only paths |
| Bash hooks (20) | Skipped | Need WSL or Git Bash — see below |
| MCP servers | All work | `claude mcp add` is cross-platform |
| CLI tools (bin/) | Skipped | All bash scripts (cc, ccls, ccpick, etc.) |
| Ghostty config | Skipped | macOS-only terminal — use Windows Terminal |
| Notification sounds | Skipped | macOS `afplay` command |
| SQLite tracker | Works | Needs Node.js + npm |

### Skills That May Not Work

A handful of skills depend on macOS-specific tools:

- **syspeek** — reads macOS system metrics (`ioreg`, `pmset`)
- **disc-forge** — uses macOS audio tools
- **parakeet** — hotkey is ⌥Space (macOS); Ctrl-Space on Windows but needs separate setup
- **background-computer-use** — Swift/macOS only

These install without errors but won't function. Everything else — research tools, development skills, design utilities, search, planning — works fine.

---

## For Full Compatibility: WSL2

If you want the bash hooks and CLI tools too, WSL2 gives you a full Linux environment inside Windows. See [WSL-SETUP.md](WSL-SETUP.md) for the complete guide.

---

## Also: Codex CLI

OpenAI's Codex CLI is a companion terminal agent that uses GPT models. It runs alongside Claude Code without conflicts, and the `codex-orchestrator` skill lets Claude Code spawn Codex subagents for multi-model workflows.

See [CODEX-CLI.md](CODEX-CLI.md) for the Windows setup guide.

---

## Updating

Pull the latest changes and re-run the setup:

```powershell
cd ~\Desktop\claude-code-minoan
git pull
.\docs\windows-setup\setup-windows.ps1
```

The script overwrites existing files, so you always get the latest versions.

---

## Uninstalling

To remove the Minoan extensions without uninstalling Claude Code:

```powershell
# Remove skills
Remove-Item -Recurse -Force "$HOME\.claude\skills\*"

# Remove commands
Remove-Item -Recurse -Force "$HOME\.claude\commands\*"

# Remove hooks
Remove-Item -Recurse -Force "$HOME\.claude\hooks\*"

# Remove MCP servers (one at a time)
claude mcp remove playwright
claude mcp remove chrome-devtools
claude mcp remove figma
claude mcp remove shadcn
```

To uninstall Claude Code itself:

```powershell
# If installed via native installer, check Add/Remove Programs in Windows Settings
# If installed via npm:
npm uninstall -g @anthropic-ai/claude-code
```

---

## Next Steps

Once you're set up:

1. **Try a slash command** — type `/docs` in a Claude Code session
2. **Check MCP servers** — run `claude mcp list` in your terminal
3. **Customize your terminal** — Oh My Posh, PSReadLine, ccstatusline. See [TERMINAL-BEAUTIFICATION.md](TERMINAL-BEAUTIFICATION.md)
4. **Read the main README** — `claude-code-minoan/README.md` has the full feature reference
5. **Explore skills** — ask Claude "What skills do you have?" in a session

For troubleshooting, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
