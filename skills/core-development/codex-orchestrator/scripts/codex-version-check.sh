#!/bin/bash
# Check Codex CLI version and auto-update if outdated
# Usage: codex-version-check.sh [--auto-update]
# Returns: 0 if up-to-date or updated, 1 if update needed but not performed

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

AUTO_UPDATE=false
SILENT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --auto-update)
            AUTO_UPDATE=true
            shift
            ;;
        --silent)
            SILENT=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

log() {
    if [ "$SILENT" = false ]; then
        echo -e "$1"
    fi
}

# Check if codex is installed
if ! command -v codex &> /dev/null; then
    log "${RED}Codex CLI not installed${NC}"
    log "Install with: npm install -g @openai/codex"
    exit 1
fi

# Get current version
CURRENT_VERSION=$(codex --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
if [ -z "$CURRENT_VERSION" ]; then
    log "${YELLOW}Could not determine current Codex version${NC}"
    exit 0
fi

# Get latest version from npm
LATEST_VERSION=$(npm view @openai/codex version 2>/dev/null)
if [ -z "$LATEST_VERSION" ]; then
    log "${YELLOW}Could not fetch latest Codex version from npm${NC}"
    exit 0
fi

log "${BLUE}Codex CLI Version Check${NC}"
log "  Current: $CURRENT_VERSION"
log "  Latest:  $LATEST_VERSION"

# Compare versions using sort -V
if [ "$CURRENT_VERSION" = "$LATEST_VERSION" ]; then
    log "${GREEN}✓ Codex CLI is up-to-date${NC}"
    exit 0
fi

# Check if current version is older
OLDER=$(printf '%s\n' "$CURRENT_VERSION" "$LATEST_VERSION" | sort -V | head -n1)
if [ "$OLDER" = "$CURRENT_VERSION" ] && [ "$CURRENT_VERSION" != "$LATEST_VERSION" ]; then
    log "${YELLOW}⚠ Update available: $CURRENT_VERSION → $LATEST_VERSION${NC}"

    if [ "$AUTO_UPDATE" = true ]; then
        log "${BLUE}Auto-updating Codex CLI...${NC}"
        if npm update -g @openai/codex 2>&1; then
            NEW_VERSION=$(codex --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
            log "${GREEN}✓ Updated to $NEW_VERSION${NC}"
            exit 0
        else
            log "${RED}Update failed${NC}"
            exit 1
        fi
    else
        log "Run with --auto-update to update automatically"
        log "Or manually: npm update -g @openai/codex"
        exit 1
    fi
else
    log "${GREEN}✓ Codex CLI is up-to-date${NC}"
    exit 0
fi
