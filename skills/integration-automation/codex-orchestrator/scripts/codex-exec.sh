#!/bin/bash
# Execute Codex CLI with a specific agent profile
# Usage: codex-exec.sh <profile> "<prompt>" [options]
# Example: codex-exec.sh reviewer "Review auth.ts for security issues"
#
# Profiles: reviewer, debugger, architect, security, refactor, docs

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_DIR="$SCRIPT_DIR/../agents"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

show_usage() {
    echo "Usage: codex-exec.sh <profile> \"<prompt>\" [options]"
    echo ""
    echo "Profiles:"
    echo "  reviewer   - Code review specialist"
    echo "  debugger   - Bug hunting and fix specialist"
    echo "  architect  - System design specialist"
    echo "  security   - Security audit specialist"
    echo "  refactor   - Code refactoring specialist"
    echo "  docs       - Documentation specialist"
    echo ""
    echo "Options:"
    echo "  --model <model>     Override model (default: o3-mini)"
    echo "  --sandbox <mode>    Sandbox mode: read-only, workspace-write, danger-full-access"
    echo "  --full-auto         Run in full-auto mode (no approval needed)"
    echo ""
    echo "Examples:"
    echo "  codex-exec.sh reviewer \"Review src/auth.ts for security issues\""
    echo "  codex-exec.sh debugger \"Debug the login failure in auth.ts\" --full-auto"
    echo "  codex-exec.sh architect \"Design a caching layer for the API\""
}

if [ $# -lt 2 ]; then
    show_usage
    exit 1
fi

PROFILE="$1"
PROMPT="$2"
shift 2

# Validate profile exists
AGENTS_FILE="$AGENTS_DIR/$PROFILE.md"
if [ ! -f "$AGENTS_FILE" ]; then
    echo -e "${RED}Error: Profile '$PROFILE' not found${NC}"
    echo "Available profiles: reviewer, debugger, architect, security, refactor, docs"
    exit 1
fi

# Parse additional options
MODEL=""  # Use Codex default (from ~/.codex/config.toml)
SANDBOX="workspace-write"
FULL_AUTO=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --sandbox)
            SANDBOX="$2"
            shift 2
            ;;
        --full-auto)
            FULL_AUTO="--ask-for-approval on-failure"
            shift
            ;;
        *)
            echo -e "${YELLOW}Warning: Unknown option $1${NC}"
            shift
            ;;
    esac
done

# Save current directory
WORK_DIR="$(pwd)"

# Check if AGENTS.md already exists and back it up
AGENTS_BACKUP=""
if [ -f "$WORK_DIR/AGENTS.md" ]; then
    AGENTS_BACKUP="$WORK_DIR/AGENTS.md.backup.$$"
    mv "$WORK_DIR/AGENTS.md" "$AGENTS_BACKUP"
fi

# Create symlink to the profile's AGENTS.md in the current directory
ln -sf "$AGENTS_FILE" "$WORK_DIR/AGENTS.md"

echo -e "${GREEN}Executing Codex with profile: $PROFILE${NC}"
if [ -n "$MODEL" ]; then
    echo -e "Model: $MODEL"
else
    echo -e "Model: (default from config)"
fi
echo -e "Working directory: $WORK_DIR"
echo -e "Prompt: $PROMPT"
echo ""

# Cleanup function
cleanup() {
    rm -f "$WORK_DIR/AGENTS.md"
    if [ -n "$AGENTS_BACKUP" ] && [ -f "$AGENTS_BACKUP" ]; then
        mv "$AGENTS_BACKUP" "$WORK_DIR/AGENTS.md"
    fi
}
trap cleanup EXIT

# Build codex command
CODEX_CMD="codex exec --sandbox $SANDBOX"
if [ -n "$MODEL" ]; then
    CODEX_CMD="$CODEX_CMD --model $MODEL"
fi
if [ -n "$FULL_AUTO" ]; then
    CODEX_CMD="$CODEX_CMD $FULL_AUTO"
fi

# Run Codex with the agent profile
# Codex reads AGENTS.md from the current directory
$CODEX_CMD "$PROMPT"
