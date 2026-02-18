#!/bin/bash
# Execute Codex CLI with a specific agent profile
# Usage: codex-exec.sh <profile> "<prompt>" [options]
# Example: codex-exec.sh reviewer "Review auth.ts for security issues"
#
# Profiles: reviewer, debugger, architect, security, refactor, docs, planner, syseng, builder, researcher

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_DIR="$SCRIPT_DIR/../agents"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Auto-update check: run version check with auto-update enabled
echo -e "${BLUE}Checking Codex CLI version...${NC}"
if ! "$SCRIPT_DIR/codex-version-check.sh" --auto-update; then
    echo -e "${YELLOW}Warning: Could not verify/update Codex CLI version${NC}"
fi
echo ""

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
    echo "  planner    - ExecPlan design document specialist"
    echo "  syseng     - Infrastructure/DevOps/CI-CD specialist"
    echo "  builder    - Greenfield implementation specialist"
    echo "  researcher - Read-only Q&A and analysis (no file changes)"
    echo ""
    echo "Options:"
    echo "  --model <model>     Override model (default from config)"
    echo "  --sandbox <mode>    Sandbox mode: read-only, workspace-write, danger-full-access"
    echo "  --full-auto         Run in full-auto mode (no approval needed)"
    echo "  --web-search        Enable Exa web search for research questions"
    echo ""
    echo "Examples:"
    echo "  codex-exec.sh reviewer \"Review src/auth.ts for security issues\""
    echo "  codex-exec.sh debugger \"Debug the login failure in auth.ts\" --full-auto"
    echo "  codex-exec.sh architect \"Design a caching layer for the API\""
    echo "  codex-exec.sh researcher \"Explain the authentication flow in this project\""
    echo "  codex-exec.sh researcher \"What are the latest React patterns?\" --web-search"
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
    echo "Available profiles: reviewer, debugger, architect, security, refactor, docs, planner, syseng, builder, researcher"
    exit 1
fi

# Parse additional options
MODEL=""  # Use Codex default (from ~/.codex/config.toml)
SANDBOX="workspace-write"
FULL_AUTO=""
WEB_SEARCH=""

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
            FULL_AUTO="--full-auto"
            shift
            ;;
        --web-search)
            WEB_SEARCH="true"
            shift
            ;;
        *)
            echo -e "${YELLOW}Warning: Unknown option $1${NC}"
            shift
            ;;
    esac
done

# Auto-configure read-only profiles
EPHEMERAL=""
OUTPUT_FILE=""
if [ "$PROFILE" = "researcher" ]; then
    SANDBOX="read-only"
    EPHEMERAL="--ephemeral"
    OUTPUT_FILE=$(mktemp /tmp/codex-researcher-XXXXXX.md)
    if [ -n "$FULL_AUTO" ]; then
        echo -e "${YELLOW}Warning: --full-auto overrides read-only sandbox. Ignoring --full-auto for researcher profile.${NC}"
        FULL_AUTO=""
    fi
fi

# Save current directory
WORK_DIR="$(pwd)"

# Check if AGENTS.md already exists and back it up
AGENTS_BACKUP=""
if [ -f "$WORK_DIR/AGENTS.md" ]; then
    AGENTS_BACKUP="$WORK_DIR/AGENTS.md.backup.$$"
    mv "$WORK_DIR/AGENTS.md" "$AGENTS_BACKUP"
fi

# Create AGENTS.md in the current directory
# If --web-search, concatenate profile + Exa guide; otherwise symlink
EXA_GUIDE="$HOME/.claude/skills/exa-search/codex-agent-guide.md"
if [ -n "$WEB_SEARCH" ] && [ -f "$EXA_GUIDE" ]; then
    cat "$AGENTS_FILE" "$EXA_GUIDE" > "$WORK_DIR/AGENTS.md"
else
    ln -sf "$AGENTS_FILE" "$WORK_DIR/AGENTS.md"
fi

echo -e "${GREEN}Executing Codex with profile: $PROFILE${NC}"
if [ -n "$MODEL" ]; then
    echo -e "Model: $MODEL"
else
    echo -e "Model: (default from config)"
fi
echo -e "Sandbox: $SANDBOX"
echo -e "Working directory: $WORK_DIR"
echo -e "Prompt: $PROMPT"
if [ -n "$WEB_SEARCH" ]; then
    echo -e "Web search: ${GREEN}enabled (Exa)${NC}"
fi
echo ""

# Cleanup function
cleanup() {
    rm -f "$WORK_DIR/AGENTS.md"
    if [ -n "$AGENTS_BACKUP" ] && [ -f "$AGENTS_BACKUP" ]; then
        mv "$AGENTS_BACKUP" "$WORK_DIR/AGENTS.md"
    fi
    if [ -n "$OUTPUT_FILE" ]; then
        rm -f "$OUTPUT_FILE"
    fi
}
trap cleanup EXIT

# Build codex command
# --skip-git-repo-check allows running in directories not in Codex's trusted list
CODEX_CMD="codex exec --skip-git-repo-check --sandbox $SANDBOX"
if [ -n "$MODEL" ]; then
    CODEX_CMD="$CODEX_CMD --model $MODEL"
fi
if [ -n "$FULL_AUTO" ]; then
    CODEX_CMD="$CODEX_CMD $FULL_AUTO"
fi
if [ -n "$EPHEMERAL" ]; then
    CODEX_CMD="$CODEX_CMD $EPHEMERAL"
fi
if [ -n "$OUTPUT_FILE" ]; then
    CODEX_CMD="$CODEX_CMD -o $OUTPUT_FILE"
fi
# Exa search is injected via AGENTS.md; built-in web search is fallback
if [ -n "$WEB_SEARCH" ]; then
    CODEX_CMD="$CODEX_CMD -c web_search=\"live\""
fi

# Run Codex with the agent profile
# Codex reads AGENTS.md from the current directory
$CODEX_CMD "$PROMPT"

# Display captured response for researcher profile
if [ -n "$OUTPUT_FILE" ] && [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
    echo ""
    echo -e "${GREEN}=== Response ===${NC}"
    cat "$OUTPUT_FILE"
fi
