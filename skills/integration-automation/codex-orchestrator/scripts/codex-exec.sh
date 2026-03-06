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
    echo "  --model <model>       Override model (default: per-profile, see below)"
    echo "  --reasoning <level>   Override reasoning effort: minimal, low, medium, high, xhigh"
    echo "  --sandbox <mode>      Sandbox mode: read-only, workspace-write, danger-full-access"
    echo "  --full-auto           Run in full-auto mode (no approval needed)"
    echo "  --web-search          Enable Exa web search (injects guide into AGENTS.md)"
    echo "  --search              Enable native Codex web search (works in all sandboxes)"
    echo "  --json                Output JSONL event stream (pipe to jq, logs, etc.)"
    echo "  --image <file>        Attach image to prompt (vision input)"
    echo "  --resume              Resume previous exec session (builder \"continue\" workflow)"
    echo "  --with-mcp            (no-op, kept for compatibility; manage MCPs in ~/.codex/config.toml)"
    echo ""
    echo "Profile defaults:"
    echo "  Coding   (builder,reviewer,debugger,refactor,syseng,security,docs): gpt-5.4 + high"
    echo "  Planning (planner,architect):                                       gpt-5.4 + high"
    echo "  Research (researcher):                                              gpt-5.4 + medium"
    echo ""
    echo "Examples:"
    echo "  codex-exec.sh reviewer \"Review src/auth.ts for security issues\""
    echo "  codex-exec.sh debugger \"Debug the login failure in auth.ts\" --full-auto"
    echo "  codex-exec.sh architect \"Design a caching layer for the API\""
    echo "  codex-exec.sh researcher \"Explain the authentication flow in this project\""
    echo "  codex-exec.sh researcher \"What are the latest React patterns?\" --search"
    echo "  codex-exec.sh reviewer \"Review this mockup\" --image screenshot.png"
    echo "  codex-exec.sh builder \"continue\" --resume"
}

# Profile-specific defaults for model and reasoning effort
get_profile_defaults() {
    local profile="$1"
    case "$profile" in
        # Planning profiles: gpt-5.4 with high reasoning (gpt-5.4-pro requires API key auth)
        planner|architect)
            DEFAULT_MODEL="gpt-5.4"
            DEFAULT_REASONING="high"
            ;;
        # Research profile: gpt-5.4 with medium reasoning (1M context, read-only)
        researcher)
            DEFAULT_MODEL="gpt-5.4"
            DEFAULT_REASONING="medium"
            ;;
        # Coding profiles: gpt-5.4 with high reasoning (unified coding + reasoning)
        builder|reviewer|debugger|refactor|syseng|security|docs)
            DEFAULT_MODEL="gpt-5.4"
            DEFAULT_REASONING="high"
            ;;
        *)
            DEFAULT_MODEL=""
            DEFAULT_REASONING=""
            ;;
    esac
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

# Get profile-specific defaults
get_profile_defaults "$PROFILE"

# Parse additional options (user overrides take precedence)
MODEL=""
REASONING=""
SANDBOX="workspace-write"
FULL_AUTO=""
WEB_SEARCH=""
NATIVE_SEARCH=""
JSON_OUTPUT=""
IMAGE_FILE=""
RESUME_SESSION=""
WITH_MCP=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --reasoning)
            REASONING="$2"
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
        --search)
            NATIVE_SEARCH="true"
            shift
            ;;
        --json)
            JSON_OUTPUT="true"
            shift
            ;;
        --image)
            IMAGE_FILE="$2"
            shift 2
            ;;
        --resume)
            RESUME_SESSION="true"
            shift
            ;;
        --with-mcp)
            WITH_MCP="true"
            shift
            ;;
        *)
            echo -e "${YELLOW}Warning: Unknown option $1${NC}"
            shift
            ;;
    esac
done

# Apply profile defaults where user didn't override
if [ -z "$MODEL" ] && [ -n "$DEFAULT_MODEL" ]; then
    MODEL="$DEFAULT_MODEL"
fi
if [ -z "$REASONING" ] && [ -n "$DEFAULT_REASONING" ]; then
    REASONING="$DEFAULT_REASONING"
fi

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
if [ -n "$REASONING" ]; then
    echo -e "Reasoning: $REASONING"
fi
echo -e "Sandbox: $SANDBOX"
echo -e "Working directory: $WORK_DIR"
echo -e "Prompt: $PROMPT"
if [ -n "$WEB_SEARCH" ]; then
    echo -e "Web search: ${GREEN}enabled (Exa)${NC}"
fi
if [ -n "$NATIVE_SEARCH" ]; then
    echo -e "Web search: ${GREEN}enabled (native)${NC}"
fi
if [ -n "$JSON_OUTPUT" ]; then
    echo -e "Output: ${GREEN}JSONL${NC}"
fi
if [ -n "$IMAGE_FILE" ]; then
    echo -e "Image: $IMAGE_FILE"
fi
if [ -n "$RESUME_SESSION" ]; then
    echo -e "Mode: ${GREEN}resume last session${NC}"
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

# Build codex command as array to preserve quoting
# --skip-git-repo-check allows running in directories not in Codex's trusted list
if [ -n "$RESUME_SESSION" ]; then
    CODEX_ARGS=(exec resume --last --skip-git-repo-check --sandbox "$SANDBOX")
else
    CODEX_ARGS=(exec --skip-git-repo-check --sandbox "$SANDBOX")
fi
if [ -n "$MODEL" ]; then
    CODEX_ARGS+=(--model "$MODEL")
fi
if [ -n "$REASONING" ]; then
    CODEX_ARGS+=(-c "model_reasoning_effort=\"$REASONING\"")
fi
if [ -n "$FULL_AUTO" ]; then
    CODEX_ARGS+=(--full-auto)
fi
if [ -n "$EPHEMERAL" ]; then
    CODEX_ARGS+=(--ephemeral)
fi
if [ -n "$OUTPUT_FILE" ]; then
    CODEX_ARGS+=(-o "$OUTPUT_FILE")
fi
# Exa search is injected via AGENTS.md; built-in web search is fallback
if [ -n "$WEB_SEARCH" ]; then
    CODEX_ARGS+=(-c 'web_search="live"')
fi
# Native Codex web search (model-level tool, bypasses sandbox network restrictions)
if [ -n "$NATIVE_SEARCH" ]; then
    CODEX_ARGS+=(-c 'web_search="live"')
fi
# JSONL event stream output
if [ -n "$JSON_OUTPUT" ]; then
    CODEX_ARGS+=(--json)
fi
# Vision input (image attachment)
if [ -n "$IMAGE_FILE" ]; then
    CODEX_ARGS+=(-i "$IMAGE_FILE")
fi
# Note: MCP servers from ~/.codex/config.toml always boot (CLI merge semantics
# prevent clearing via -c override). Remove unused servers from config.toml to
# reduce startup latency.

# Run Codex with the agent profile
# Codex reads AGENTS.md from the current directory
if [ -n "$RESUME_SESSION" ]; then
    codex "${CODEX_ARGS[@]}"
else
    codex "${CODEX_ARGS[@]}" "$PROMPT"
fi

# Display captured response for researcher profile
if [ -n "$OUTPUT_FILE" ] && [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
    echo ""
    echo -e "${GREEN}=== Response ===${NC}"
    cat "$OUTPUT_FILE"
fi
