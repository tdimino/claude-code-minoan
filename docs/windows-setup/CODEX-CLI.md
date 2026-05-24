# Codex CLI Setup on Windows

OpenAI's Codex CLI is a terminal coding agent similar to Claude Code but built around GPT models. This guide covers installing it alongside Claude Code on Windows.

Codex shipped native Windows support on May 13, 2026 — no WSL required.

---

## Prerequisites

### Required

- **Node.js 22+** — Codex CLI installs via npm and requires Node 22 or later.

  ```powershell
  winget install OpenJS.NodeJS.LTS
  ```

  Close and reopen your terminal, then verify you have v22+:

  ```powershell
  node --version
  npm --version
  ```

  If you already have Node installed but it's older than 22, re-run `winget install OpenJS.NodeJS.LTS` to upgrade.

- **Git for Windows** — `winget install Git.Git`

- **Visual C++ Redistributable** — Codex's native binary needs VC++ runtime DLLs (`vcruntime140.dll`, `msvcp140.dll`). Most Windows machines already have these, but on a fresh install they may be missing — Codex will silently fail to launch without them.

  ```powershell
  winget install Microsoft.VCRedist.2015+.x64
  ```

- **An OpenAI account** — ChatGPT Plus ($20/mo) or higher, or an API key.

### What Plan Do You Need?

| Plan | Price | Codex CLI? | Quota |
|------|-------|-----------|-------|
| Free ChatGPT | $0 | Limited trial | Very restricted |
| ChatGPT Plus | $20/mo | Yes | ~30-150 messages per 5-hour window |
| ChatGPT Pro | $100/mo | Yes | 5x Plus quota |
| API key | Pay-per-token | Yes | No quota, pay as you go |

ChatGPT Plus is enough for exploration. The $20/mo plan works for both Claude Code (Anthropic) and Codex CLI (OpenAI).

---

## Install Codex CLI

```powershell
npm install -g @openai/codex
```

**Important:** The package is `@openai/codex`, not `codex`. The unscoped `codex` package is a completely unrelated 2012 project.

Verify the install:

```powershell
codex --version
```

If it prints nothing or exits silently, you're likely missing the VC++ runtime. Install it (see prerequisites above) and try again.

---

## Authentication

Two options:

### Option A: ChatGPT Login (Recommended for Exploration)

```powershell
codex
```

On first launch, Codex opens your browser for ChatGPT authentication. Log in with your ChatGPT Plus/Pro account.

### Option B: API Key

```powershell
$env:OPENAI_API_KEY = "sk-..."
codex
```

To make it permanent, add to your PowerShell profile:

```powershell
notepad $PROFILE
# Add: $env:OPENAI_API_KEY = "sk-your-key-here"
```

Or set it system-wide via Windows Settings > System > About > Advanced system settings > Environment Variables.

---

## Configuration

Codex stores its config at `~/.codex/config.toml`. Key settings:

```toml
# Model selection (default: gpt-5.3-codex)
model = "gpt-5.3-codex"

# Approval mode: "suggest" (default), "auto-edit", "full-auto"
approval_mode = "suggest"

# Sandbox: "read-only", "workspace-write" (default), "danger-full-access"
sandbox = "workspace-write"
```

Create or edit via:

```powershell
notepad "$HOME\.codex\config.toml"
```

---

## Using Codex CLI

### Basic Usage

```powershell
# Start interactive session
codex

# One-shot task
codex "fix the login timeout bug"

# Specific model
codex --model gpt-5.4 "review this PR for security issues"
```

### AGENTS.md

Create an `AGENTS.md` file in your project root to shape Codex's behavior — similar to Claude Code's `CLAUDE.md`. This is the highest-leverage configuration: a short, specific AGENTS.md changes behavior more than any flag.

```markdown
# AGENTS.md

## Project
This is a React + TypeScript web app using Next.js 15.

## Rules
- Use TypeScript strict mode
- Prefer server components
- Run `npm test` before suggesting changes
```

### Key Commands Inside a Session

| Command | What It Does |
|---------|-------------|
| `/model gpt-5.4` | Switch models mid-session |
| `/goal "objective"` | Set a persistent multi-hour objective |
| `/goal clear` | Clear the current goal |
| `/compact` | Compress context to fit more work |
| `/undo` | Undo the last file change |

---

## Codex CLI + Claude Code Together

You can run both tools on the same machine. They don't conflict — they use separate configs, separate accounts, and separate API keys.

The `codex-orchestrator` skill in this repo lets Claude Code spawn Codex subagents for specialized tasks:

```
# Inside a Claude Code session, use the codex-orchestrator skill:
/codex-orchestrator reviewer "Review src/auth.ts for security issues"
/codex-orchestrator researcher "What are the best patterns for error handling here?"
```

This gives you Claude's orchestration with GPT's perspective — a two-model workflow.

---

## Updating

```powershell
npm install -g @openai/codex@latest
```

---

## Troubleshooting

### Codex silently fails to launch

Exit code `-1073741515` means missing VC++ runtime:

```powershell
winget install Microsoft.VCRedist.2015+.x64
```

### `npm install` succeeds but `codex` command not found

Make sure npm's global bin directory is in your PATH:

```powershell
npm config get prefix
# Should show something like C:\Users\YourName\AppData\Roaming\npm
# Verify it's in your PATH:
$env:PATH -split ";" | Select-String "npm"
```

### Wrong `codex` package installed

If `codex --version` shows something unexpected, you may have installed the wrong package:

```powershell
npm uninstall -g codex
npm install -g @openai/codex
```

### Sandbox errors

Codex on Windows uses OS-level sandboxing (restricted tokens + filesystem ACLs). If you get permission errors:

- Make sure you're running from a project directory (not `C:\`)
- Check that `sandbox = "workspace-write"` in `~/.codex/config.toml`
- For operations outside your project, you need `"danger-full-access"` (use with caution)
