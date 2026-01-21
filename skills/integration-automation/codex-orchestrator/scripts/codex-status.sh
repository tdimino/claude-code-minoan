#!/bin/bash
# Check Codex CLI installation and configuration status
# Usage: codex-status.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Codex CLI Status ===${NC}\n"

# Check if codex is installed
if command -v codex &> /dev/null; then
    CODEX_PATH=$(which codex)
    CODEX_VERSION=$(codex --version 2>&1)
    echo -e "${GREEN}✓ Codex CLI installed${NC}"
    echo "  Path: $CODEX_PATH"
    echo "  Version: $CODEX_VERSION"
else
    echo -e "${RED}✗ Codex CLI not found${NC}"
    echo "  Install with: npm install -g @openai/codex"
    exit 1
fi

echo ""

# Check OpenAI API key
if [ -n "$OPENAI_API_KEY" ]; then
    # Mask the key for display
    MASKED_KEY="${OPENAI_API_KEY:0:7}...${OPENAI_API_KEY: -4}"
    echo -e "${GREEN}✓ OPENAI_API_KEY set${NC}"
    echo "  Key: $MASKED_KEY"
else
    echo -e "${YELLOW}⚠ OPENAI_API_KEY not set${NC}"
    echo "  Set with: export OPENAI_API_KEY=sk-..."
fi

echo ""

# Check Codex config
CODEX_CONFIG="$HOME/.codex/config.toml"
if [ -f "$CODEX_CONFIG" ]; then
    echo -e "${GREEN}✓ Codex config exists${NC}"
    echo "  Path: $CODEX_CONFIG"
else
    echo -e "${YELLOW}⚠ No Codex config found${NC}"
    echo "  Default config will be used"
fi

echo ""

# Check agent profiles
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_DIR="$SCRIPT_DIR/../agents"

echo -e "${BLUE}Agent Profiles:${NC}"
for profile in reviewer debugger architect security refactor docs; do
    if [ -f "$AGENTS_DIR/$profile.md" ]; then
        echo -e "  ${GREEN}✓${NC} $profile"
    else
        echo -e "  ${RED}✗${NC} $profile (missing)"
    fi
done

echo ""

# Test Codex connectivity (quick check)
echo -e "${BLUE}Testing Codex connectivity...${NC}"
if timeout 10 codex exec --model o3-mini "echo 'test'" &> /dev/null; then
    echo -e "${GREEN}✓ Codex API connection successful${NC}"
else
    echo -e "${YELLOW}⚠ Could not verify Codex API connection${NC}"
    echo "  This may be due to network issues or API key problems"
fi

echo ""
echo -e "${BLUE}=== Status Check Complete ===${NC}"
