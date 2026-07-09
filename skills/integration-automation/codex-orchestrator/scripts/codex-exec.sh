#!/bin/bash
# Execute Codex CLI with a specific agent profile
# Usage: codex-exec.sh <profile> "<prompt>" [options]
# Example: codex-exec.sh reviewer "Review auth.ts for security issues"
#
# Profiles: reviewer, debugger, architect, security, refactor, docs, planner, syseng, builder, researcher, adjudicator, chat, goal

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_DIR="$(cd "$SCRIPT_DIR/../agents" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# PTY wrapper: Codex CLI v0.124.0+ silently crashes when stdio is detached
# from a controlling TTY (e.g., shell &, run_in_background, setsid).
# Wraps the command with script(1) to re-attach a pseudo-TTY when needed.
_with_pty() {
    if [ -t 1 ]; then
        "$@"
    elif ! command -v script >/dev/null 2>&1; then
        echo -e "${YELLOW}Warning: 'script' not found — PTY wrapper unavailable, Codex may fail in background${NC}" >&2
        "$@"
    else
        case "$(uname -s)" in
            Darwin)
                script -q /dev/null "$@"
                ;;
            *)
                script -qfc "$(printf '%q ' "$@")" /dev/null
                ;;
        esac
    fi
}

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
    echo "  adjudicator - Read-only comparative evidence weighing and hypothesis ranking"
    echo "  chat       - Open-ended conversation (read-only, ephemeral)"
    echo "  goal       - Goal specification writer for /goal autonomous runs"
    echo ""
    echo "Options:"
    echo "  --model <model>       Override model (default: per-profile, see below)"
    echo "  --reasoning <level>   Override reasoning effort: minimal, low, medium, high, xhigh"
    echo "  --sandbox <mode>      Sandbox mode: read-only, workspace-write, danger-full-access"
    echo "  --no-approve          Force read-only sandbox (no file writes)"
    echo "  --web-search          Enable Exa web search (injects guide into AGENTS.md)"
    echo "  --search              Enable native Codex web search (works in all sandboxes)"
    echo "  --json                Output JSONL event stream (pipe to jq, logs, etc.)"
    echo "  --image <file>        Attach image to prompt (vision input)"
    echo "  --resume              Resume previous exec session (builder \"continue\" workflow)"
    echo "  --with-mcp            (no-op, kept for compatibility; manage MCPs in ~/.codex/config.toml)"
    echo "  --api                 Use OpenAI API directly (API billing, not Codex subscription)"
    echo "  --session <file>      Session file for multi-turn API chat (requires --api)"
    echo "  --system <prompt>     System prompt for API chat (requires --api)"
    echo "  --stream              Stream API response tokens (requires --api)"
    echo ""
    echo "Profile defaults:"
    echo "  Coding   (builder,reviewer,debugger,refactor,syseng,security,docs): gpt-5.6-sol + high"
    echo "  Planning (planner,architect,goal):                                   gpt-5.6-sol + high"
    echo "  Research (researcher):                                              gpt-5.6-sol + medium"
    echo "  Adjudication (adjudicator):                                         gpt-5.6-sol + high"
    echo "  Chat     (chat):                                                    gpt-5.6-terra + medium"
    echo ""
    echo "Examples:"
    echo "  codex-exec.sh reviewer \"Review src/auth.ts for security issues\""
    echo "  codex-exec.sh debugger \"Debug the login failure in auth.ts\""
    echo "  codex-exec.sh architect \"Design a caching layer for the API\""
    echo "  codex-exec.sh researcher \"Explain the authentication flow in this project\""
    echo "  codex-exec.sh adjudicator \"Weigh the competing readings for this ambiguous evidence\""
    echo "  codex-exec.sh researcher \"What are the latest React patterns?\" --search"
    echo "  codex-exec.sh reviewer \"Review this mockup\" --image screenshot.png"
    echo "  codex-exec.sh builder \"continue\" --resume"
}

# Profile-specific defaults for model and reasoning effort
get_profile_defaults() {
    local profile="$1"
    case "$profile" in
        # Planning profiles: gpt-5.6-sol with high reasoning
        planner|architect|goal)
            DEFAULT_MODEL="gpt-5.6-sol"
            DEFAULT_REASONING="high"
            ;;
        # Chat: gpt-5.6-terra (balanced, cost-efficient) with medium reasoning, read-only
        chat)
            DEFAULT_MODEL="gpt-5.6-terra"
            DEFAULT_REASONING="medium"
            ;;
        # Research: gpt-5.6-sol with medium reasoning, read-only
        researcher)
            DEFAULT_MODEL="gpt-5.6-sol"
            DEFAULT_REASONING="medium"
            ;;
        adjudicator)
            DEFAULT_MODEL="gpt-5.6-sol"
            DEFAULT_REASONING="high"
            ;;
        # Coding profiles: gpt-5.6-sol with high reasoning
        builder|reviewer|debugger|refactor|syseng|security|docs)
            DEFAULT_MODEL="gpt-5.6-sol"
            DEFAULT_REASONING="high"
            ;;
        *)
            DEFAULT_MODEL=""
            DEFAULT_REASONING=""
            ;;
    esac
}

# Detect if an AGENTS.md is one we injected (symlink or sentinel-marked file).
is_our_injection() {
    local file="$1"
    if [ -L "$file" ]; then
        local target
        target="$(readlink "$file")"
        case "$target" in
            */.claude/skills/codex-orchestrator/agents/*) return 0 ;;
        esac
    elif [ -f "$file" ] && head -1 "$file" 2>/dev/null | grep -q "^# CODEX-ORCHESTRATOR-INJECTED"; then
        return 0
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
    echo "Available profiles: reviewer, debugger, architect, security, refactor, docs, planner, syseng, builder, researcher, adjudicator, chat, goal"
    exit 1
fi

# Get profile-specific defaults
get_profile_defaults "$PROFILE"

# Parse additional options (user overrides take precedence)
MODEL=""
REASONING=""
SANDBOX="workspace-write"
WEB_SEARCH=""
NATIVE_SEARCH=""
JSON_OUTPUT=""
IMAGE_FILE=""
RESUME_SESSION=""
WITH_MCP=""
API_MODE=""
API_SESSION=""
API_SYSTEM=""
API_STREAM=""
SKIP_OUTPUT_CLEANUP=""

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
            echo -e "${YELLOW}Warning: --full-auto is deprecated (Codex PR #20133). --sandbox workspace-write already auto-approves in exec mode.${NC}"
            shift
            ;;
        --no-approve|--no-auto)
            SANDBOX="read-only"
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
        --api)
            API_MODE="true"
            shift
            ;;
        --session)
            API_SESSION="$2"
            shift 2
            ;;
        --system)
            API_SYSTEM="$2"
            shift 2
            ;;
        --stream)
            API_STREAM="true"
            shift
            ;;
        --no-cleanup)
            SKIP_OUTPUT_CLEANUP="true"
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
EXTRACT_RESPONSE=""
OUTPUT_DISPLAYED=""
if [ "$PROFILE" = "researcher" ] || [ "$PROFILE" = "adjudicator" ] || [ "$PROFILE" = "chat" ]; then
    SANDBOX="read-only"
    EPHEMERAL="--ephemeral"
    OUTPUT_FILE=$(mktemp /tmp/codex-researcher-XXXXXXXX)
    # Use --json + jq to extract only agent_message text, avoiding the noise
    # from intermediate file reads that -o captures.
    # Skip if user explicitly requested --json (they want raw JSONL).
    if command -v jq >/dev/null 2>&1 && [ -z "$JSON_OUTPUT" ]; then
        EXTRACT_RESPONSE="true"
    fi
fi

# Save current directory
WORK_DIR="$(pwd)"

# --- PID-scoped AGENTS.md backup/restore (parallel-safe) ---
# Each instance manages its own backup. No shared lock state.
BACKUP_PATH="$WORK_DIR/.AGENTS.md.codex-backup.$$"
AGENTS_TARGET="$WORK_DIR/AGENTS.md"
HAD_EXISTING_AGENTS=""

# crash recovery: clean orphan backups from dead processes and stale injections
for orphan in "$WORK_DIR"/.AGENTS.md.codex-backup.* "$WORK_DIR"/AGENTS.md.backup.* "$WORK_DIR"/.AGENTS.md.codex-orchestrator-backup; do
    [ -e "$orphan" ] || continue
    orphan_pid="${orphan##*.}"
    case "$orphan_pid" in
        *codex-orchestrator-backup) orphan_pid="" ;;
    esac
    if [ -z "$orphan_pid" ] || ! kill -0 "$orphan_pid" 2>/dev/null; then
        if ([ ! -e "$AGENTS_TARGET" ] || is_our_injection "$AGENTS_TARGET") && [ ! -L "$orphan" ]; then
            echo -e "${YELLOW}Restoring AGENTS.md from orphaned backup: $orphan${NC}"
            mv "$orphan" "$AGENTS_TARGET"
        else
            rm -f "$orphan"
        fi
    fi
done
rmdir "$WORK_DIR/.codex-orchestrator-locks" 2>/dev/null || true

# Verify working directory is writable
if ! touch "$WORK_DIR/.codex-orchestrator-write-test" 2>/dev/null; then
    echo -e "${RED}Error: Working directory is not writable: $WORK_DIR${NC}"
    exit 1
fi
rm -f "$WORK_DIR/.codex-orchestrator-write-test"

# Backup existing AGENTS.md if it's real user content (not our injection)
if [ -e "$AGENTS_TARGET" ] && ! is_our_injection "$AGENTS_TARGET"; then
    if cp -a "$AGENTS_TARGET" "$BACKUP_PATH"; then
        HAD_EXISTING_AGENTS="true"
    else
        echo -e "${RED}Error: Failed to backup AGENTS.md. Aborting to prevent data loss.${NC}"
        exit 1
    fi
fi

# Inject profile AGENTS.md (sentinel for --web-search concatenated files)
EXA_GUIDE="$HOME/.claude/skills/exa-search/codex-agent-guide.md"
if [ -n "$WEB_SEARCH" ] && [ -f "$EXA_GUIDE" ]; then
    { echo "# CODEX-ORCHESTRATOR-INJECTED"; cat "$AGENTS_FILE" "$EXA_GUIDE"; } > "$AGENTS_TARGET"
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

# Cleanup: PID-scoped restore (no shared lock state)
CLEANUP_DONE=""
cleanup() {
    [ -n "$CLEANUP_DONE" ] && return
    CLEANUP_DONE=1

    # Check if any sibling backups exist from still-running instances
    local has_live_siblings=false
    for sibling in "$WORK_DIR"/.AGENTS.md.codex-backup.*; do
        [ -e "$sibling" ] || continue
        [ "$sibling" = "$BACKUP_PATH" ] && continue
        local sib_pid="${sibling##*.}"
        if kill -0 "$sib_pid" 2>/dev/null; then
            has_live_siblings=true
            break
        else
            rm -f "$sibling"
        fi
    done

    if [ "$has_live_siblings" = false ]; then
        if [ -n "$HAD_EXISTING_AGENTS" ] && [ -e "$BACKUP_PATH" ]; then
            mv "$BACKUP_PATH" "$AGENTS_TARGET"
        else
            rm -f "$BACKUP_PATH"
            if is_our_injection "$AGENTS_TARGET"; then
                rm -f "$AGENTS_TARGET"
            fi
        fi
    else
        rm -f "$BACKUP_PATH"
    fi

    if [ -n "$OUTPUT_FILE" ]; then
        if [ -n "$SKIP_OUTPUT_CLEANUP" ]; then
            echo "OUTPUT_FILE=$OUTPUT_FILE" >&2
        elif [ -n "$OUTPUT_DISPLAYED" ]; then
            rm -f "$OUTPUT_FILE"
        fi
    fi
}
trap cleanup EXIT INT TERM HUP

# Build codex command as array to preserve quoting
# --skip-git-repo-check allows running in directories not in Codex's trusted list
if [ -n "$RESUME_SESSION" ]; then
    CODEX_ARGS=(exec --skip-git-repo-check --sandbox "$SANDBOX")
else
    CODEX_ARGS=(exec --skip-git-repo-check --sandbox "$SANDBOX")
fi
if [ -n "$MODEL" ]; then
    CODEX_ARGS+=(--model "$MODEL")
fi
case "$MODEL" in
    gpt-4*) REASONING="" ;;
esac
if [ -n "$REASONING" ]; then
    CODEX_ARGS+=(-c "model_reasoning_effort=\"$REASONING\"")
fi
if [ -n "$EPHEMERAL" ]; then
    CODEX_ARGS+=(--ephemeral)
fi
if [ -n "$EXTRACT_RESPONSE" ]; then
    # --json gives us structured JSONL events; we extract agent_message text via jq
    CODEX_ARGS+=(--json)
elif [ -n "$OUTPUT_FILE" ]; then
    # Fallback: -o captures last message (may include intermediate content)
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
# JSONL event stream output (skip if EXTRACT_RESPONSE already added --json)
if [ -n "$JSON_OUTPUT" ] && [ -z "$EXTRACT_RESPONSE" ]; then
    CODEX_ARGS+=(--json)
fi
# Vision input (image attachment)
if [ -n "$IMAGE_FILE" ]; then
    CODEX_ARGS+=(-i "$IMAGE_FILE")
fi
# Note: MCP servers from ~/.codex/config.toml always boot (CLI merge semantics
# prevent clearing via -c override). Remove unused servers from config.toml to
# reduce startup latency.

# --- API mode: bypass Codex CLI, call OpenAI API directly ---
if [ -n "$API_MODE" ]; then
    source ~/.config/env/secrets.env 2>/dev/null || true
    API_CHAT_SCRIPT="$SCRIPT_DIR/gpt-api-chat.py"
    API_ARGS=("$PROMPT" --model "${MODEL:-gpt-5.6-sol}")
    if [ -n "$API_SESSION" ]; then
        API_ARGS+=(--session "$API_SESSION")
    fi
    if [ -n "$API_SYSTEM" ]; then
        API_ARGS+=(--system "$API_SYSTEM")
    fi
    if [ -n "$API_STREAM" ]; then
        API_ARGS+=(--stream)
    fi
    if [ -n "$REASONING" ]; then
        API_ARGS+=(--reasoning "$REASONING")
    fi
    if [ -n "$JSON_OUTPUT" ]; then
        API_ARGS+=(--json)
    fi
    echo -e "${GREEN}API mode: calling OpenAI API directly (billed to API key)${NC}"
    echo -e "Model: ${MODEL:-gpt-5.6-sol}"
    if [ -n "$API_SESSION" ]; then
        echo -e "Session: $API_SESSION"
    fi
    echo ""
    python3 "$API_CHAT_SCRIPT" "${API_ARGS[@]}"
    exit $?
fi

# Verify codex is available before running
if ! command -v codex >/dev/null 2>&1; then
    echo -e "${RED}Error: 'codex' CLI not found in PATH. Install with: npm install -g @openai/codex${NC}"
    exit 1
fi

# Run Codex with the agent profile
# Codex reads AGENTS.md from the current directory
set +e
if [ -n "$EXTRACT_RESPONSE" ]; then
    # JSONL mode: pipe through jq to extract only agent_message text.
    # This filters out intermediate tool calls (file reads, command executions)
    # that would otherwise bury the actual response in thousands of lines.
    # grep '^{' filters non-JSON lines (control chars, stderr bleed from script(1) PTY wrapper).
    if [ -n "$RESUME_SESSION" ]; then
        _with_pty codex "${CODEX_ARGS[@]}" resume --last "$PROMPT" </dev/null 2>/dev/null \
            | tr -d '\r' \
            | grep '^{' \
            | jq -r 'select(.type == "item.completed" and .item.type == "agent_message") | .item.text // empty' \
            > "$OUTPUT_FILE"
    else
        _with_pty codex "${CODEX_ARGS[@]}" "$PROMPT" </dev/null 2>/dev/null \
            | tr -d '\r' \
            | grep '^{' \
            | jq -r 'select(.type == "item.completed" and .item.type == "agent_message") | .item.text // empty' \
            > "$OUTPUT_FILE"
    fi
    CODEX_EXIT=${PIPESTATUS[0]}
elif [ -n "$RESUME_SESSION" ]; then
    _with_pty codex "${CODEX_ARGS[@]}" resume --last "$PROMPT" </dev/null
    CODEX_EXIT=$?
else
    _with_pty codex "${CODEX_ARGS[@]}" "$PROMPT" </dev/null
    CODEX_EXIT=$?
fi
set -e

# Handle signal exits cleanly
if [ "$CODEX_EXIT" -eq 130 ] || [ "$CODEX_EXIT" -eq 143 ]; then
    exit "$CODEX_EXIT"
fi

# Display captured response for read-only captured-output profiles
if [ -n "$OUTPUT_FILE" ]; then
    if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
        echo ""
        echo -e "${GREEN}=== Response ===${NC}"
        cat "$OUTPUT_FILE"
        OUTPUT_DISPLAYED=1
    else
        echo ""
        echo -e "${RED}Warning: Codex produced no output (exit code $CODEX_EXIT).${NC}"
        echo -e "${YELLOW}Possible causes: TTY detachment (background execution), AGENTS.md collision, empty model response, or session too short.${NC}"
        echo -e "${YELLOW}If backgrounded, codex-exec.sh auto-wraps with script(1) — check Codex CLI version (v0.124.0+ required).${NC}"
        exit 1
    fi
fi

exit $CODEX_EXIT
