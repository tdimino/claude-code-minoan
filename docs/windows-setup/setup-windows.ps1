# Minoan Claude Code Setup Script (Windows)
# PowerShell equivalent of setup.sh — installs skills, commands, hooks, and MCP servers

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "Minoan Claude Code Setup (Windows)" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# --- Helpers ---

function Write-OK($msg)      { Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Skip($msg)    { Write-Host "  [SKIP] $msg" -ForegroundColor Yellow }
function Write-Info($msg)    { Write-Host "  [..] $msg" -ForegroundColor Blue }
function Write-Warn($msg)    { Write-Host "  [!!] $msg" -ForegroundColor Yellow }

# Resolve repo root (script lives in docs/windows-setup/)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot  = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$ClaudeDir = Join-Path $HOME ".claude"

# --- Prerequisites ---

Write-Host "Checking prerequisites..." -ForegroundColor White
Write-Host ""

# Claude Code
if (Get-Command claude -ErrorAction SilentlyContinue) {
    Write-OK "Claude Code CLI found"
} else {
    Write-Host ""
    Write-Host "  Claude Code is not installed. Install it first:" -ForegroundColor Red
    Write-Host "    irm https://claude.ai/install.ps1 | iex" -ForegroundColor White
    Write-Host ""
    exit 1
}

# Git
if (Get-Command git -ErrorAction SilentlyContinue) {
    Write-OK "Git found"
} else {
    Write-Warn "Git not found. Claude Code will use PowerShell instead of Bash."
    Write-Warn "Recommended: winget install Git.Git"
}

# Python
$PythonCmd = $null
foreach ($candidate in @("python3", "python")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        try {
            $ver = & $candidate --version 2>&1
            if ($ver -match "Python 3\.") {
                $PythonCmd = $candidate
                break
            }
        } catch {
            # Windows App Execution Alias can resolve but not run
        }
    }
}
if ($PythonCmd) {
    Write-OK "Python found ($PythonCmd)"
} else {
    Write-Warn "Python 3 not found. Hooks and some skills won't work."
    Write-Warn "Recommended: winget install Python.Python.3.12"
    Write-Warn "If Python is installed, close and reopen your terminal for PATH changes."
}

Write-Host ""

# --- Skills ---

Write-Host "Setting up Skills..." -ForegroundColor White
Write-Host "--------------------" -ForegroundColor White

$SkillsDest = Join-Path $ClaudeDir "skills"
if (-not (Test-Path $SkillsDest)) { New-Item -ItemType Directory -Path $SkillsDest -Force | Out-Null }

$categories = @("core-development", "design-media", "integration-automation", "planning-productivity", "research")

Write-Host ""
Write-Host "  Which skills would you like to install?"
Write-Host ""
Write-Host "    1. All skills (recommended for exploring everything)"
Write-Host "    2. Core development skills only (claude-md, agent-sdk, autoresearch, etc.)"
Write-Host "    3. Select by category"
Write-Host "    4. Skip skills setup"
Write-Host ""
$skillChoice = Read-Host "  Enter choice (1-4)"

switch ($skillChoice) {
    "1" {
        Write-Info "Installing all skills..."
        foreach ($cat in $categories) {
            $catPath = Join-Path $RepoRoot "skills\$cat"
            if (Test-Path $catPath) {
                Get-ChildItem -Path $catPath -Directory | ForEach-Object {
                    Copy-Item -Path $_.FullName -Destination (Join-Path $SkillsDest $_.Name) -Recurse -Force
                }
            }
        }
        $count = (Get-ChildItem -Path $SkillsDest -Directory).Count
        Write-OK "Installed $count skills to $SkillsDest"
    }
    "2" {
        Write-Info "Installing core development skills..."
        $corePath = Join-Path $RepoRoot "skills\core-development"
        if (Test-Path $corePath) {
            Get-ChildItem -Path $corePath -Directory | ForEach-Object {
                Copy-Item -Path $_.FullName -Destination (Join-Path $SkillsDest $_.Name) -Recurse -Force
            }
        }
        $count = (Get-ChildItem -Path $SkillsDest -Directory).Count
        Write-OK "Installed $count core skills"
    }
    "3" {
        Write-Host ""
        Write-Host "  Available categories:" -ForegroundColor White
        for ($i = 0; $i -lt $categories.Count; $i++) {
            $catPath = Join-Path $RepoRoot "skills\$($categories[$i])"
            $catCount = if (Test-Path $catPath) { (Get-ChildItem -Path $catPath -Directory).Count } else { 0 }
            Write-Host "    $($i+1). $($categories[$i]) ($catCount skills)"
        }
        Write-Host ""
        $catChoices = Read-Host "  Enter category numbers (comma-separated, e.g. 1,3,5)"
        $catChoices -split "," | ForEach-Object {
            $parsed = 0
            if (-not [int]::TryParse($_.Trim(), [ref]$parsed)) { return }
            $idx = $parsed - 1
            if ($idx -ge 0 -and $idx -lt $categories.Count) {
                $catPath = Join-Path $RepoRoot "skills\$($categories[$idx])"
                if (Test-Path $catPath) {
                    Get-ChildItem -Path $catPath -Directory | ForEach-Object {
                        Copy-Item -Path $_.FullName -Destination (Join-Path $SkillsDest $_.Name) -Recurse -Force
                    }
                    Write-OK "Installed $($categories[$idx])"
                }
            }
        }
        $count = (Get-ChildItem -Path $SkillsDest -Directory).Count
        Write-OK "Total: $count skills installed"
    }
    "4" { Write-Skip "Skipping skills setup" }
    default { Write-Skip "Invalid choice. Skipping skills setup" }
}

Write-Host ""

# --- Commands ---

Write-Host "Setting up Slash Commands..." -ForegroundColor White
Write-Host "----------------------------" -ForegroundColor White

$CommandsDest = Join-Path $ClaudeDir "commands"
if (-not (Test-Path $CommandsDest)) { New-Item -ItemType Directory -Path $CommandsDest -Force | Out-Null }

Write-Host ""
Write-Host "  Install slash commands?"
Write-Host ""
Write-Host "    1. Yes, install all commands"
Write-Host "    2. Skip"
Write-Host ""
$cmdChoice = Read-Host "  Enter choice (1-2)"

switch ($cmdChoice) {
    "1" {
        $cmdSrc = Join-Path $RepoRoot "commands"
        Get-ChildItem -Path $cmdSrc -Exclude "_archive", "README.md", "INDEX.md" | ForEach-Object {
            Copy-Item -Path $_.FullName -Destination $CommandsDest -Recurse -Force
        }
        $count = (Get-ChildItem -Path $CommandsDest -File -Filter "*.md").Count
        Write-OK "Installed $count slash commands"
    }
    default { Write-Skip "Skipping commands setup" }
}

Write-Host ""

# --- Hooks ---

Write-Host "Setting up Hooks..." -ForegroundColor White
Write-Host "-------------------" -ForegroundColor White

$HooksDest = Join-Path $ClaudeDir "hooks"
if (-not (Test-Path $HooksDest)) { New-Item -ItemType Directory -Path $HooksDest -Force | Out-Null }

$hooksSrc = Join-Path $RepoRoot "hooks"
$pyHooks  = Get-ChildItem -Path $hooksSrc -Filter "*.py" -File
$shHooks  = Get-ChildItem -Path $hooksSrc -Filter "*.sh" -File

Write-Host ""
Write-Host "  Hooks run automatically at Claude Code lifecycle events (tool use,"
Write-Host "  session start/end, etc.) to provide terminal UX, git tracking, and more."
Write-Host ""
Write-Host "  Python hooks ($($pyHooks.Count) available): work on Windows"
Write-Host "  Bash hooks ($($shHooks.Count) available): need WSL or Git Bash"
Write-Host ""
Write-Host "    1. Install Python hooks only (recommended for Windows)"
Write-Host "    2. Install all hooks (Python + Bash — only choose if you have WSL)"
Write-Host "    3. Skip hooks setup"
Write-Host ""
$hookChoice = Read-Host "  Enter choice (1-3)"

switch ($hookChoice) {
    "1" {
        foreach ($hook in $pyHooks) {
            if ($hook.Name -eq "install-hooks.py") { continue }
            Copy-Item -Path $hook.FullName -Destination $HooksDest -Force
        }
        # Also copy hooks.json for reference
        $hooksJson = Join-Path $hooksSrc "hooks.json"
        if (Test-Path $hooksJson) {
            Copy-Item -Path $hooksJson -Destination $HooksDest -Force
        }
        Write-OK "Installed $($pyHooks.Count - 1) Python hooks (copied, not yet registered)"
        Write-Warn "$($shHooks.Count) bash hooks skipped (need WSL or Git Bash)"
        Write-Host ""
        Write-Host "  IMPORTANT: Hooks are copied but NOT active yet." -ForegroundColor Yellow
        Write-Host "  To activate them, you need to register them in Claude Code settings." -ForegroundColor Yellow
        Write-Host "  The hooks.json file has been copied as a reference template." -ForegroundColor Yellow
        Write-Host "  Edit ~/.claude/settings.json and add hook entries from hooks.json." -ForegroundColor Yellow
        Write-Host "  Note: hooks.json references 'python3' — on Windows, change to 'python'." -ForegroundColor Yellow
    }
    "2" {
        Copy-Item -Path "$hooksSrc\*.py" -Destination $HooksDest -Force
        Copy-Item -Path "$hooksSrc\*.sh" -Destination $HooksDest -Force
        $hooksJson = Join-Path $hooksSrc "hooks.json"
        if (Test-Path $hooksJson) {
            Copy-Item -Path $hooksJson -Destination $HooksDest -Force
        }
        $total = $pyHooks.Count + $shHooks.Count
        Write-OK "Installed $total hooks (Python + Bash)"
        Write-Warn "Bash hooks require WSL or Git Bash to execute"
    }
    "3" { Write-Skip "Skipping hooks setup" }
    default { Write-Skip "Invalid choice. Skipping hooks setup" }
}

Write-Host ""

# --- MCP Servers ---

Write-Host "Setting up MCP Servers..." -ForegroundColor White
Write-Host "-------------------------" -ForegroundColor White

Write-Host ""
Write-Host "  MCP servers extend Claude Code with external tool integrations."
Write-Host ""
Write-Host "    1. Install essential servers (Playwright, Chrome DevTools, Figma, shadcn)"
Write-Host "    2. Skip MCP setup"
Write-Host ""
$mcpChoice = Read-Host "  Enter choice (1-2)"

switch ($mcpChoice) {
    "1" {
        if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
            Write-Warn "npx not found. Playwright and Chrome DevTools need Node.js."
            Write-Warn "Install Node.js first: winget install OpenJS.NodeJS.LTS"
            Write-Warn "Skipping npx-based servers. Adding HTTP-only servers..."
        } else {
            Write-Info "Adding Playwright..."
            & claude mcp add -s user playwright -- npx @playwright/mcp@latest
            if ($LASTEXITCODE -eq 0) { Write-OK "Playwright added" } else { Write-Warn "Playwright failed or already installed" }

            Write-Info "Adding Chrome DevTools..."
            & claude mcp add -s user chrome-devtools -- npx -y chrome-devtools-mcp
            if ($LASTEXITCODE -eq 0) { Write-OK "Chrome DevTools added" } else { Write-Warn "Chrome DevTools failed or already installed" }
        }

        Write-Info "Adding Figma..."
        & claude mcp add -s user --transport http figma https://mcp.figma.com/mcp
        if ($LASTEXITCODE -eq 0) { Write-OK "Figma added" } else { Write-Warn "Figma failed or already installed" }

        Write-Info "Adding shadcn..."
        & claude mcp add -s user --transport http shadcn https://www.shadcn.io/api/mcp
        if ($LASTEXITCODE -eq 0) { Write-OK "shadcn added" } else { Write-Warn "shadcn failed or already installed" }

        Write-Host ""
        Write-OK "Essential MCP servers installed"
        Write-Info "For servers needing API keys, see .mcp.json in the repo root"
    }
    default { Write-Skip "Skipping MCP setup" }
}

Write-Host ""

# --- SQLite Tracker (Optional) ---

Write-Host "Optional: SQLite Tracker..." -ForegroundColor White
Write-Host "---------------------------" -ForegroundColor White

Write-Host ""
Write-Host "  The tracker suite can use SQLite for faster session search, checkpoints,"
Write-Host "  and tagged phrase capture. Requires Node.js + npm."
Write-Host ""
Write-Host "    1. Install SQLite tracker"
Write-Host "    2. Skip (JSON-only mode — everything still works)"
Write-Host ""
$sqliteChoice = Read-Host "  Enter choice (1-2)"

switch ($sqliteChoice) {
    "1" {
        if (Get-Command npm -ErrorAction SilentlyContinue) {
            $libDir = Join-Path $ClaudeDir "lib"
            if (-not (Test-Path $libDir)) { New-Item -ItemType Directory -Path $libDir -Force | Out-Null }

            Copy-Item -Path (Join-Path $RepoRoot "lib\tracker-db.js") -Destination $libDir -Force
            $pkgJson = Join-Path $RepoRoot "lib\package.json"
            if (Test-Path $pkgJson) {
                Copy-Item -Path $pkgJson -Destination $libDir -Force
            }

            Write-Info "Running npm install..."
            Push-Location $libDir
            & npm install --production 2>&1 | Out-Null
            Pop-Location
            if ($LASTEXITCODE -eq 0) {
                Write-OK "better-sqlite3 installed"
            } else {
                Write-Warn "npm install failed. You may need Visual Studio Build Tools with C++ workload."
                Write-Warn "Or try: npm install --production in $libDir manually."
            }

            $migrationSrc = Join-Path $RepoRoot "scripts\migrate-to-sqlite.js"
            if (Test-Path $migrationSrc) {
                $scriptsDest = Join-Path $ClaudeDir "scripts"
                if (-not (Test-Path $scriptsDest)) { New-Item -ItemType Directory -Path $scriptsDest -Force | Out-Null }
                Copy-Item -Path $migrationSrc -Destination $scriptsDest -Force
                Write-Info "Running migration..."
                & node (Join-Path $scriptsDest "migrate-to-sqlite.js")
                if ($LASTEXITCODE -eq 0) {
                    Write-OK "SQLite migration complete"
                } else {
                    Write-Warn "Migration failed. Run manually: node $scriptsDest\migrate-to-sqlite.js"
                }
            }
        } else {
            Write-Warn "npm not found. Install Node.js first: winget install OpenJS.NodeJS.LTS"
        }
    }
    default { Write-Skip "Skipping SQLite setup" }
}

Write-Host ""

# --- Shared Libraries ---

$libDir = Join-Path $ClaudeDir "lib"
if (-not (Test-Path $libDir)) { New-Item -ItemType Directory -Path $libDir -Force | Out-Null }

$libSrc = Join-Path $RepoRoot "lib"
if (Test-Path $libSrc) {
    Get-ChildItem -Path $libSrc -File | Where-Object { $_.Name -ne "package.json" -or -not (Test-Path (Join-Path $libDir "package.json")) } | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $libDir -Force
    }
    Write-OK "Shared libraries copied to $libDir"
}

Write-Host ""

# --- Summary ---

Write-Host "===================================" -ForegroundColor Cyan
Write-Host "  Setup Complete" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

if (Test-Path $SkillsDest) {
    $sc = (Get-ChildItem -Path $SkillsDest -Directory -ErrorAction SilentlyContinue).Count
    if ($sc -gt 0) { Write-OK "Skills: $sc installed" }
}
if (Test-Path $CommandsDest) {
    $cc = (Get-ChildItem -Path $CommandsDest -File -Filter "*.md" -ErrorAction SilentlyContinue).Count
    if ($cc -gt 0) { Write-OK "Commands: $cc installed" }
}
if (Test-Path $HooksDest) {
    $pyc = (Get-ChildItem -Path $HooksDest -Filter "*.py" -ErrorAction SilentlyContinue).Count
    $shc = (Get-ChildItem -Path $HooksDest -Filter "*.sh" -ErrorAction SilentlyContinue).Count
    if ($pyc -gt 0) {
        $hookMsg = "Hooks: $pyc Python"
        if ($shc -gt 0) { $hookMsg += ", $shc Bash" }
        Write-OK $hookMsg
    }
}

Write-Host ""
Write-Host "  Next steps:" -ForegroundColor White
Write-Host "    1. Run: claude" -ForegroundColor Gray
Write-Host "    2. Log in with your Anthropic account" -ForegroundColor Gray
Write-Host "    3. Try a slash command: /docs" -ForegroundColor Gray
Write-Host "    4. Check MCP servers: claude mcp list" -ForegroundColor Gray
Write-Host "    5. See README.md for the full feature reference" -ForegroundColor Gray
Write-Host ""
Write-Host "  Skipped (macOS-only):" -ForegroundColor Yellow
Write-Host "    - Ghostty terminal config (use Windows Terminal)" -ForegroundColor Yellow
Write-Host "    - CLI tools in bin/ (bash scripts, need WSL)" -ForegroundColor Yellow
Write-Host "    - Notification sounds (macOS afplay)" -ForegroundColor Yellow
Write-Host ""
Write-Host "  For troubleshooting, see docs\windows-setup\TROUBLESHOOTING.md" -ForegroundColor Gray
Write-Host ""
