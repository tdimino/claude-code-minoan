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
        case "${CODEX_ORCHESTRATOR_PLATFORM:-$(uname -s)}" in
            Darwin)
                script -q /dev/null "$@"
                ;;
            *)
                # util-linux script passes -c through /bin/sh on some systems.
                # Serialize argv with POSIX single quotes; Bash printf %q emits
                # $'...' for multiline personas, which dash cannot interpret.
                local command_string=""
                local argument escaped_argument
                for argument in "$@"; do
                    escaped_argument="$(printf '%s' "$argument" | sed "s/'/'\\\\''/g")"
                    command_string="${command_string}${command_string:+ }'${escaped_argument}'"
                done
                script -qfc "$command_string" /dev/null
                ;;
        esac
    fi
}

# Auto-update check: run version check with auto-update enabled
if [ "${CODEX_ORCHESTRATOR_SKIP_UPDATE:-}" != "1" ]; then
    echo -e "${BLUE}Checking Codex CLI version...${NC}"
    if ! "$SCRIPT_DIR/codex-version-check.sh" --auto-update; then
        echo -e "${YELLOW}Warning: Could not verify/update Codex CLI version${NC}"
    fi
    echo ""
fi

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
    echo "  --astra               Shortcut for --model gpt-6-astra"
    echo "  --reasoning <level>   Override reasoning effort: none, minimal, low, medium, high, xhigh, max, ultra"
    echo "  --service-tier <tier> Override service tier: default, priority"
    echo "  --sandbox <mode>      Sandbox mode: read-only, workspace-write, danger-full-access"
    echo "  --no-approve          Force read-only sandbox (no file writes)"
    echo "  --web-search          Enable Exa web search (appends guide to this process's persona)"
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
    echo "  codex-exec.sh architect \"Design a fault-tolerant queue\" --astra --reasoning max --service-tier priority"
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
SERVICE_TIER=""
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
            if [[ $# -lt 2 || "$2" == --* ]]; then
                echo -e "${RED}Error: --model requires a value${NC}"
                exit 1
            fi
            MODEL="$2"
            shift 2
            ;;
        --astra)
            MODEL="gpt-6-astra"
            shift
            ;;
        --reasoning)
            if [[ $# -lt 2 || "$2" == --* ]]; then
                echo -e "${RED}Error: --reasoning requires a value${NC}"
                exit 1
            fi
            REASONING="$2"
            shift 2
            ;;
        --service-tier)
            if [[ $# -lt 2 || "$2" == --* ]]; then
                echo -e "${RED}Error: --service-tier requires a value${NC}"
                exit 1
            fi
            SERVICE_TIER="$2"
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

# Validate Astra's model-specific permutations. Keeping the matrix explicit
# catches typos before Codex starts and makes future capability changes local.
if [ "$MODEL" = "gpt-6-astra" ]; then
    case "$REASONING" in
        low|medium|high|xhigh|max|ultra) ;;
        *)
            echo -e "${RED}Error: GPT-6-Astra reasoning must be one of: low, medium, high, xhigh, max, ultra${NC}"
            exit 1
            ;;
    esac
fi

case "$SERVICE_TIER" in
    ""|default|priority) ;;
    *)
        echo -e "${RED}Error: Service tier must be one of: default, priority${NC}"
        exit 1
        ;;
esac

if [ -n "$API_MODE" ] && [ -n "$SERVICE_TIER" ]; then
    echo -e "${RED}Error: --service-tier configures Codex CLI subagents and cannot be combined with --api${NC}"
    exit 1
fi
if [ -n "$API_MODE" ] && [ "$MODEL" = "gpt-6-astra" ]; then
    echo -e "${RED}Error: GPT-6-Astra is exposed here as a Codex CLI subagent and cannot be combined with --api${NC}"
    exit 1
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

# Save current directory. Project AGENTS.md files stay in place and Codex
# discovers their normal root-to-cwd instruction chain independently per run.
WORK_DIR="$(pwd)"

# Compose a per-process persona. Passing it as developer_instructions keeps the
# profile isolated from sibling launches and preserves every project AGENTS.md.
EXA_GUIDE="$HOME/.claude/skills/exa-search/codex-agent-guide.md"
if [ -n "$WEB_SEARCH" ] && [ -f "$EXA_GUIDE" ]; then
    PROFILE_INSTRUCTIONS="$(printf '%s\n\n' "$(cat "$AGENTS_FILE")"; cat "$EXA_GUIDE")"
else
    PROFILE_INSTRUCTIONS="$(cat "$AGENTS_FILE")"
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
if [ -n "$SERVICE_TIER" ]; then
    echo -e "Service tier: $SERVICE_TIER"
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

# Cleanup captured output only; project instructions are never mutated.
CLEANUP_DONE=""
cleanup() {
    [ -n "$CLEANUP_DONE" ] && return
    CLEANUP_DONE=1

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
# Codex parses -c values as TOML and falls back to the raw string for Markdown.
# This is process-local, so concurrent personas cannot overwrite one another.
CODEX_ARGS+=(-c "developer_instructions=$PROFILE_INSTRUCTIONS")
case "$MODEL" in
    gpt-4*) REASONING="" ;;
esac
if [ -n "$REASONING" ]; then
    CODEX_ARGS+=(-c "model_reasoning_effort=\"$REASONING\"")
fi
case "$SERVICE_TIER" in
    default) CODEX_ARGS+=(-c 'service_tier="default"') ;;
    priority) CODEX_ARGS+=(-c 'service_tier="fast"') ;;
esac
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
# Exa guidance is appended to the per-process developer instructions; built-in
# web search remains the transport/fallback.
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

# Run Codex with the per-process profile plus the untouched project AGENTS chain.
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
        echo -e "${YELLOW}Possible causes: TTY detachment (background execution), empty model response, or session too short.${NC}"
        echo -e "${YELLOW}If backgrounded, codex-exec.sh auto-wraps with script(1) — check Codex CLI version (v0.124.0+ required).${NC}"
        exit 1
    fi
fi

exit $CODEX_EXIT
