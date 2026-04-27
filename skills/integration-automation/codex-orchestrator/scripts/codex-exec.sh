#!/bin/bash
# Execute Codex CLI with a specific agent profile
# Usage: codex-exec.sh <profile> "<prompt>" [options]
# Example: codex-exec.sh reviewer "Review auth.ts for security issues"
#
# Profiles: reviewer, debugger, architect, security, refactor, docs, planner, syseng, builder, researcher

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_DIR="$(cd "$SCRIPT_DIR/../agents" && pwd)"

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
    echo "  --full-auto           Run in full-auto mode (default for write profiles)"
    echo "  --no-auto             Disable auto --full-auto (require manual approval)"
    echo "  --web-search          Enable Exa web search (injects guide into AGENTS.md)"
    echo "  --search              Enable native Codex web search (works in all sandboxes)"
    echo "  --json                Output JSONL event stream (pipe to jq, logs, etc.)"
    echo "  --image <file>        Attach image to prompt (vision input)"
    echo "  --resume              Resume previous exec session (builder \"continue\" workflow)"
    echo "  --with-mcp            (no-op, kept for compatibility; manage MCPs in ~/.codex/config.toml)"
    echo ""
    echo "Profile defaults:"
    echo "  Coding   (builder,reviewer,debugger,refactor,syseng,security,docs): gpt-5.5 + high"
    echo "  Planning (planner,architect):                                       gpt-5.5 + high"
    echo "  Research (researcher):                                              gpt-5.5 + medium"
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
        # Planning profiles: gpt-5.5 with high reasoning (gpt-5.5-pro requires API key auth)
        planner|architect)
            DEFAULT_MODEL="gpt-5.5"
            DEFAULT_REASONING="high"
            ;;
        # Research profile: gpt-5.5 with medium reasoning (1M context, read-only)
        researcher)
            DEFAULT_MODEL="gpt-5.5"
            DEFAULT_REASONING="medium"
            ;;
        # Coding profiles: gpt-5.5 with high reasoning (unified coding + reasoning)
        builder|reviewer|debugger|refactor|syseng|security|docs)
            DEFAULT_MODEL="gpt-5.5"
            DEFAULT_REASONING="high"
            ;;
        *)
            DEFAULT_MODEL=""
            DEFAULT_REASONING=""
            ;;
    esac
}

# Detect if an AGENTS.md is one we injected (symlink into our agents dir).
is_our_injection() {
    local file="$1"
    if [ -L "$file" ]; then
        local target
        target="$(readlink "$file")"
        case "$target" in
            */.claude/skills/codex-orchestrator/agents/*) return 0 ;;
        esac
    fi
    return 1
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
NO_AUTO=""
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
        --no-auto)
            NO_AUTO="true"
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

# Auto-enable --full-auto for write-capable profiles in non-interactive exec mode.
# Without this, codex exec cannot approve writes (no TUI) and writes fail silently.
# Use --no-auto to opt out if needed.
if [ "$PROFILE" != "researcher" ] && [ -z "$FULL_AUTO" ] && [ -z "$NO_AUTO" ]; then
    FULL_AUTO="--full-auto"
fi

# Save current directory
WORK_DIR="$(pwd)"

# --- Robust AGENTS.md backup/restore ---
BACKUP_NAME=".AGENTS.md.codex-orchestrator-backup"
BACKUP_PATH="$WORK_DIR/$BACKUP_NAME"
AGENTS_TARGET="$WORK_DIR/AGENTS.md"
HAD_EXISTING_AGENTS=""

# Phase 0: Migrate old PID-based backups from previous versions
for old_backup in "$WORK_DIR"/AGENTS.md.backup.*; do
    [ -e "$old_backup" ] || continue
    echo -e "${YELLOW}Warning: Found stale backup from previous run: $old_backup${NC}"
    if [ ! -e "$AGENTS_TARGET" ] && [ ! -L "$AGENTS_TARGET" ]; then
        if [ ! -L "$old_backup" ]; then
            echo -e "${YELLOW}Restoring AGENTS.md from stale backup: $old_backup${NC}"
            mv "$old_backup" "$AGENTS_TARGET"
        else
            echo -e "${YELLOW}Removing stale symlink backup: $old_backup${NC}"
            rm -f "$old_backup"
        fi
    else
        rm -f "$old_backup"
    fi
done

# Phase 1: Startup crash recovery
if [ -e "$BACKUP_PATH" ] || [ -L "$BACKUP_PATH" ]; then
    echo -e "${YELLOW}Warning: Found backup from a previous crashed run.${NC}"
    if [ -e "$AGENTS_TARGET" ] || [ -L "$AGENTS_TARGET" ]; then
        if is_our_injection "$AGENTS_TARGET"; then
            echo -e "${YELLOW}Current AGENTS.md is a stale injection. Restoring original from backup.${NC}"
            rm -f "$AGENTS_TARGET"
            mv "$BACKUP_PATH" "$AGENTS_TARGET"
        else
            echo -e "${YELLOW}Current AGENTS.md appears to be user content. Removing orphaned backup.${NC}"
            rm -f "$BACKUP_PATH"
        fi
    else
        echo -e "${YELLOW}Restoring AGENTS.md from backup after previous crash.${NC}"
        mv "$BACKUP_PATH" "$AGENTS_TARGET"
    fi
fi

# Phase 2: Concurrent-run guard
if [ -e "$BACKUP_PATH" ] || [ -L "$BACKUP_PATH" ]; then
    echo -e "${RED}Error: Backup file still exists after recovery. Another codex-orchestrator may be running in this directory.${NC}"
    echo -e "${RED}If not, manually inspect and remove: $BACKUP_PATH${NC}"
    exit 1
fi

# Phase 3: Verify working directory is writable
if ! touch "$WORK_DIR/.codex-orchestrator-write-test" 2>/dev/null; then
    echo -e "${RED}Error: Working directory is not writable: $WORK_DIR${NC}"
    exit 1
fi
rm -f "$WORK_DIR/.codex-orchestrator-write-test"

# Phase 4: Backup existing AGENTS.md (if any)
if [ -e "$AGENTS_TARGET" ] || [ -L "$AGENTS_TARGET" ]; then
    HAD_EXISTING_AGENTS="true"
    cp -a "$AGENTS_TARGET" "$BACKUP_PATH"
fi

# Phase 5: Create profile AGENTS.md
EXA_GUIDE="$HOME/.claude/skills/exa-search/codex-agent-guide.md"
if [ -n "$WEB_SEARCH" ] && [ -f "$EXA_GUIDE" ]; then
    cat "$AGENTS_FILE" "$EXA_GUIDE" > "$AGENTS_TARGET"
else
    ln -sf "$AGENTS_FILE" "$AGENTS_TARGET"
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
if [ -n "$FULL_AUTO" ]; then
    echo -e "Auto mode: ${GREEN}--full-auto${NC}"
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

# Cleanup function: restore original AGENTS.md
cleanup() {
    rm -f "$AGENTS_TARGET"
    if [ -n "$HAD_EXISTING_AGENTS" ] && [ -e "$BACKUP_PATH" ]; then
        mv "$BACKUP_PATH" "$AGENTS_TARGET"
    elif [ -e "$BACKUP_PATH" ]; then
        rm -f "$BACKUP_PATH"
    fi
    if [ -n "$OUTPUT_FILE" ]; then
        rm -f "$OUTPUT_FILE"
    fi
}
trap cleanup EXIT INT TERM HUP

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
