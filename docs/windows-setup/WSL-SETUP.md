# WSL2 Setup for Full Compatibility

WSL2 (Windows Subsystem for Linux) gives you a complete Linux environment inside Windows. This unlocks the 20 bash hooks, 10 CLI tools in `bin/`, and full parity with the macOS setup.

This guide is optional — the native Windows setup covers 90%+ of functionality. Only follow this if you want the bash components.

---

## Install WSL2

Open PowerShell as Administrator and run:

```powershell
wsl --install
```

This installs WSL2 with Ubuntu. Restart your PC when prompted.

After restarting, open "Ubuntu" from the Start menu. It will ask you to create a Linux username and password (these are separate from your Windows login).

---

## Install Claude Code in WSL

Inside the Ubuntu terminal:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Close and reopen the Ubuntu terminal, then verify:

```bash
claude --version
```

---

## Install Minoan Extensions in WSL

The main `setup.sh` has some macOS-specific steps (Homebrew fonts, Ghostty config) that will fail or skip on Linux. The safest approach is to install components directly.

Your Windows files are accessible from WSL at `/mnt/c/`. If you cloned the repo to your Desktop:

```bash
# Auto-detect your Windows username
WIN_USER=$(cmd.exe /c "echo %USERNAME%" 2>/dev/null | tr -d '\r')
REPO="/mnt/c/Users/$WIN_USER/Desktop/claude-code-minoan"

# Skills (flatten from category subdirectories)
mkdir -p ~/.claude/skills
for cat in core-development design-media integration-automation planning-productivity research; do
    cp -r "$REPO/skills/$cat/"*/ ~/.claude/skills/ 2>/dev/null
done

# Commands (skip archive and index files)
mkdir -p ~/.claude/commands
cp "$REPO/commands/"*.md ~/.claude/commands/ 2>/dev/null
cp -r "$REPO/commands/workflows" ~/.claude/commands/ 2>/dev/null

# Hooks (Python + Bash — all work in WSL)
mkdir -p ~/.claude/hooks
cp "$REPO/hooks/"*.py "$REPO/hooks/"*.sh ~/.claude/hooks/
cp "$REPO/hooks/hooks.json" ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.py ~/.claude/hooks/*.sh

# CLI tools
mkdir -p ~/.local/bin
cp "$REPO/bin/"* ~/.local/bin/
chmod +x ~/.local/bin/cc ~/.local/bin/ccls ~/.local/bin/cckill ~/.local/bin/ccpick ~/.local/bin/ccnew ~/.local/bin/ccresume

# Shared libraries
mkdir -p ~/.claude/lib
cp "$REPO/lib/"* ~/.claude/lib/
```

Make sure `~/.local/bin` is in your PATH. Add to `~/.bashrc` if it isn't:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

---

## MCP Servers in WSL

MCP servers work the same way in WSL as on native Linux:

```bash
claude mcp add -s user playwright -- npx @playwright/mcp@latest
claude mcp add -s user chrome-devtools -- npx -y chrome-devtools-mcp
claude mcp add -s user -t http figma https://mcp.figma.com/mcp
claude mcp add -s user -t http shadcn https://www.shadcn.io/api/mcp
```

Node.js is needed for `npx`-based servers. Install in WSL:

```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
```

---

## Working with Files

WSL and Windows share a filesystem, but performance is best when your project files live inside WSL's own filesystem (`~/projects/`) rather than on the Windows mount (`/mnt/c/`).

For new projects, keep them in WSL. For existing Windows projects, access them via `/mnt/c/Users/YourName/...` — it works, just slower for large repos.

---

## Switching Between Native and WSL

You can have Claude Code installed in both places. They share the same Anthropic account but have separate `~/.claude/` directories — one in Windows (`C:\Users\YourName\.claude\`) and one in WSL (`/home/yourname/.claude/`).

Use native Windows Claude Code for quick tasks and Windows-native projects. Use WSL Claude Code when you need bash hooks, CLI tools, or are working on Linux-targeted code.
