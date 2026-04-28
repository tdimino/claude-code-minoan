#!/bin/bash

# Minoan Claude Code Setup Script
# Automates installation of skills, commands, and MCP servers

set -e

echo "🚀 Minoan Claude Code Setup"
echo "==========================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Function to print colored output
print_green() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_yellow() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_blue() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Check if Claude Code CLI is installed
if ! command -v claude &> /dev/null; then
    print_yellow "Claude Code CLI not found. Please install Claude Code first."
    exit 1
fi

print_green "Claude Code CLI found"
echo ""

# Setup Fonts
echo "🔤 Setting up Fonts..."
echo "----------------------"

if fc-list | grep -qi "JetBrainsMono Nerd Font"; then
    print_green "JetBrainsMono Nerd Font already installed"
else
    print_blue "Installing JetBrainsMono Nerd Font..."
    brew install --cask font-jetbrains-mono-nerd-font
    print_green "JetBrainsMono Nerd Font installed"
fi

echo ""

# Setup Skills
echo "📚 Setting up Skills..."
echo "----------------------"

# Create skills directory if it doesn't exist
mkdir -p ~/.claude/skills

# Ask user which skills to install
echo "Which skills would you like to install?"
echo ""
echo "Available skills:"
echo "  1. All skills (recommended for full team setup)"
echo "  2. Core development skills only (osgrep, beads, claude-md)"
echo "  3. Select individual skills"
echo "  4. Skip skills setup"
echo ""
read -p "Enter choice (1-4): " skill_choice

case $skill_choice in
    1)
        print_blue "Installing all skills..."
        cp -r "$SCRIPT_DIR/skills/"* ~/.claude/skills/
        print_green "All skills installed to ~/.claude/skills/"
        ;;
    2)
        print_blue "Installing core development skills..."
        cp -r "$SCRIPT_DIR/skills/core-development/osgrep-reference" ~/.claude/skills/
        cp -r "$SCRIPT_DIR/skills/core-development/beads-task-tracker" ~/.claude/skills/
        cp -r "$SCRIPT_DIR/skills/core-development/claude-md-manager" ~/.claude/skills/
        cp -r "$SCRIPT_DIR/skills/core-development/claude-agent-sdk" ~/.claude/skills/
        print_green "Core skills installed"
        ;;
    3)
        print_blue "Available skills:"
        for skill in "$SCRIPT_DIR/skills/"*; do
            if [ -d "$skill" ]; then
                echo "  - $(basename "$skill")"
            fi
        done
        echo ""
        read -p "Enter skill names (space-separated): " selected_skills
        for skill in $selected_skills; do
            if [ -d "$SCRIPT_DIR/skills/$skill" ]; then
                cp -r "$SCRIPT_DIR/skills/$skill" ~/.claude/skills/
                print_green "Installed: $skill"
            else
                print_yellow "Skill not found: $skill"
            fi
        done
        ;;
    4)
        print_yellow "Skipping skills setup"
        ;;
    *)
        print_yellow "Invalid choice. Skipping skills setup"
        ;;
esac

echo ""

# Setup Slash Commands
echo "⚡ Setting up Slash Commands..."
echo "------------------------------"

mkdir -p ~/.claude/commands

echo "Would you like to install slash commands?"
echo "  1. Yes, install all commands to ~/.claude/commands/"
echo "  2. No, skip commands"
echo ""
read -p "Enter choice (1-2): " command_choice

case $command_choice in
    1)
        cp -r "$SCRIPT_DIR/commands/"* ~/.claude/commands/
        command_count=$(ls "$SCRIPT_DIR/commands/" | wc -l | tr -d ' ')
        print_green "Installed $command_count slash commands"
        ;;
    2)
        print_yellow "Skipping commands setup"
        ;;
    *)
        print_yellow "Invalid choice. Skipping commands setup"
        ;;
esac

echo ""

# Setup MCP Servers
echo "🔧 Setting up MCP Servers..."
echo "---------------------------"

echo "MCP servers require additional configuration (API keys, etc.)"
echo "Would you like to:"
echo "  1. Install essential MCP servers (playwright, chrome-devtools, figma, shadcn)"
echo "  2. View the .mcp.json file to manually configure servers"
echo "  3. Skip MCP setup"
echo ""
read -p "Enter choice (1-3): " mcp_choice

case $mcp_choice in
    1)
        print_blue "Installing essential MCP servers..."

        # Playwright
        print_blue "Adding playwright..."
        claude mcp add playwright -c npx -a "@playwright/mcp@latest" -s user || print_yellow "Playwright already installed or failed"

        # Chrome DevTools
        print_blue "Adding chrome-devtools..."
        claude mcp add chrome-devtools -c npx -a "-y" -a "chrome-devtools-mcp" -s user || print_yellow "Chrome DevTools already installed or failed"

        # Figma (HTTP)
        print_blue "Adding figma..."
        claude mcp add figma --http "https://mcp.figma.com/mcp" -s user || print_yellow "Figma already installed or failed"

        # shadcn (HTTP)
        print_blue "Adding shadcn..."
        claude mcp add shadcn --http "https://www.shadcn.io/api/mcp" -s user || print_yellow "shadcn already installed or failed"

        print_green "Essential MCP servers installed"
        print_yellow "For servers requiring API keys (perplexity, supabase, netlify), see .mcp.json"
        ;;
    2)
        print_blue "Opening .mcp.json for manual configuration..."
        cat "$SCRIPT_DIR/.mcp.json"
        echo ""
        print_yellow "To add servers manually, use: claude mcp add [name] ..."
        ;;
    3)
        print_yellow "Skipping MCP setup"
        ;;
    *)
        print_yellow "Invalid choice. Skipping MCP setup"
        ;;
esac

echo ""

# Setup Hooks
echo "🪝 Setting up Hooks..."
echo "----------------------"

echo "Hooks run automatically at Claude Code lifecycle events (tool use, session"
echo "start/end, etc.) to provide terminal UX, git tracking, linting, and more."
echo ""
echo "Which hooks would you like to install?"
echo ""
echo "  1. Essential hooks (terminal UX, git tracking, linting, image handling,"
echo "     error hints, auto-approve — no external API keys needed)"
echo "  2. Full hooks (adds soul system, session handoffs, Slack, AI-powered tags"
echo "     — requires OPENROUTER_API_KEY and optionally Claudicle)"
echo "  3. Skip hooks setup"
echo ""
read -p "Enter choice (1-3): " hooks_choice

case $hooks_choice in
    1|2)
        tier="essential"
        [ "$hooks_choice" = "2" ] && tier="full"
        if ! python3 "$SCRIPT_DIR/hooks/install-hooks.py" --tier "$tier" --repo "$SCRIPT_DIR"; then
            print_yellow "Hook installation failed. See errors above."
            print_yellow "You can retry later: python3 $SCRIPT_DIR/hooks/install-hooks.py --tier $tier --repo $SCRIPT_DIR"
        fi
        ;;
    3)
        print_yellow "Skipping hooks setup"
        ;;
    *)
        print_yellow "Invalid choice. Skipping hooks setup"
        ;;
esac

echo ""
echo "=========================="
echo "✅ Setup Complete!"
echo "=========================="
echo ""

# Print summary
echo "📋 Installation Summary:"
echo ""

if [ -d ~/.claude/skills ] && [ "$(ls -A ~/.claude/skills)" ]; then
    skill_count=$(ls ~/.claude/skills/ | wc -l | tr -d ' ')
    print_green "Skills: $skill_count installed in ~/.claude/skills/"
fi

if [ -d ~/.claude/commands ] && [ "$(ls -A ~/.claude/commands)" ]; then
    command_count=$(ls ~/.claude/commands/ | wc -l | tr -d ' ')
    print_green "Commands: $command_count installed in ~/.claude/commands/"
fi

# Check MCP servers
mcp_count=$(claude mcp list 2>/dev/null | grep -c "Connected" || echo "0")
if [ "$mcp_count" -gt 0 ]; then
    print_green "MCP Servers: $mcp_count connected"
fi

if [ -d ~/.claude/hooks ] && [ "$(ls -A ~/.claude/hooks 2>/dev/null)" ]; then
    hook_count=$(ls ~/.claude/hooks/*.py ~/.claude/hooks/*.sh 2>/dev/null | wc -l | tr -d ' ')
    print_green "Hooks: $hook_count scripts installed in ~/.claude/hooks/"
fi

echo ""
echo "📚 Next Steps:"
echo "  1. Test a slash command: /docs"
echo "  2. Verify skills are loaded (they'll appear in Claude Code)"
echo "  3. Check MCP servers: claude mcp list"
echo "  4. Verify hooks: run /hooks in a Claude Code session"
echo "  5. Review README.md for detailed documentation"
echo ""
echo "For API keys and advanced configuration, see:"
echo "  - .mcp.json (MCP server configurations)"
echo "  - hooks/README.md (hook reference and dependencies)"
echo "  - README.md (full setup guide)"
echo ""
echo "Happy coding! 🎉"
