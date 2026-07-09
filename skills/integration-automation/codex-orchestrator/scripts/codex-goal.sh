#!/bin/bash
# Goal workflow for Codex /goal autonomous runs
# Usage: codex-goal.sh draft "<objective>" [options]
#        codex-goal.sh run <goal-file> [options]
#        codex-goal.sh list [--dir <path>]
#
# Two-phase workflow:
#   1. draft — uses codex exec with goal profile to generate a goal specification file
#   2. run   — launches interactive Codex TUI with /goal set from the spec file

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_DIR="$(cd "$SCRIPT_DIR/../agents" && pwd)"

# Global state for AGENTS.md injection/cleanup (referenced by trap)
WORK_DIR=""
BACKUP_PATH=""
AGENTS_TARGET=""
HAD_EXISTING_AGENTS=""
CLEANUP_DONE=""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# PTY wrapper: Codex CLI v0.124.0+ requires a controlling TTY.
# Sourced pattern from codex-exec.sh — wraps with script(1) when backgrounded.
_with_pty() {
    if [ -t 1 ]; then
        "$@"
    elif ! command -v script >/dev/null 2>&1; then
        echo -e "${YELLOW}Warning: 'script' not found — PTY wrapper unavailable${NC}" >&2
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

show_usage() {
    echo "Usage: codex-goal.sh <command> [args] [options]"
    echo ""
    echo "Commands:"
    echo "  draft \"<objective>\"   Draft a goal specification file"
    echo "  run <goal-file>       Launch Codex TUI with /goal from spec file"
    echo "  list                  List existing goal files"
    echo ""
    echo "Draft options:"
    echo "  --output <path>       Output file (default: goals/goal-YYYYMMDD-HHMMSS.md)"
    echo "  --model <model>       Override model (default: gpt-5.6-sol)"
    echo "  --reasoning <level>   Override reasoning effort (default: high)"
    echo ""
    echo "Run options:"
    echo "  --model <model>       Override model (default: gpt-5.6-sol)"
    echo "  --sandbox <mode>      Sandbox mode (default: workspace-write)"
    echo ""
    echo "List options:"
    echo "  --dir <path>          Goals directory (default: goals/)"
    echo ""
    echo "Examples:"
    echo "  codex-goal.sh draft \"Add authentication with JWT to the API\""
    echo "  codex-goal.sh draft \"Migrate database to PostgreSQL\" --output goals/pg-migration.md"
    echo "  codex-goal.sh run goals/goal-20260518-143000.md"
    echo "  codex-goal.sh list"
}

# --- Shared: PID-scoped AGENTS.md injection (mirrors codex-exec.sh) ---

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

inject_agents() {
    local profile="$1"

    local agents_file="$AGENTS_DIR/$profile.md"
    if [ ! -f "$agents_file" ]; then
        echo -e "${RED}Error: Profile '$profile' not found at $agents_file${NC}"
        exit 1
    fi

    BACKUP_PATH="$WORK_DIR/.AGENTS.md.codex-backup.$$"
    AGENTS_TARGET="$WORK_DIR/AGENTS.md"
    HAD_EXISTING_AGENTS=""

    # Crash recovery: clean orphan backups from dead processes
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

    # Verify working directory is writable
    if ! touch "$WORK_DIR/.codex-orchestrator-write-test" 2>/dev/null; then
        echo -e "${RED}Error: Working directory is not writable: $WORK_DIR${NC}"
        exit 1
    fi
    rm -f "$WORK_DIR/.codex-orchestrator-write-test"

    # Backup existing AGENTS.md if it's real user content
    if [ -e "$AGENTS_TARGET" ] && ! is_our_injection "$AGENTS_TARGET"; then
        if cp -a "$AGENTS_TARGET" "$BACKUP_PATH"; then
            HAD_EXISTING_AGENTS="true"
        else
            echo -e "${RED}Error: Failed to backup AGENTS.md. Aborting to prevent data loss.${NC}"
            exit 1
        fi
    fi

    # Inject profile
    ln -sf "$agents_file" "$AGENTS_TARGET"
}

cleanup_agents() {
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
}

# --- Command: draft ---

cmd_draft() {
    local objective="$1"
    shift || true

    if [ -z "$objective" ]; then
        echo -e "${RED}Error: Objective is required${NC}"
        echo "Usage: codex-goal.sh draft \"<objective>\" [--output <path>] [--model <model>]"
        exit 1
    fi

    local output_path=""
    local model="gpt-5.6-sol"
    local reasoning="high"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --output)
                if [[ $# -lt 2 || "$2" == --* ]]; then
                    echo -e "${RED}Error: $1 requires a value${NC}"; exit 1
                fi
                output_path="$2"; shift 2 ;;
            --model)
                if [[ $# -lt 2 || "$2" == --* ]]; then
                    echo -e "${RED}Error: $1 requires a value${NC}"; exit 1
                fi
                model="$2"; shift 2 ;;
            --reasoning)
                if [[ $# -lt 2 || "$2" == --* ]]; then
                    echo -e "${RED}Error: $1 requires a value${NC}"; exit 1
                fi
                reasoning="$2"; shift 2 ;;
            *) echo -e "${YELLOW}Warning: Unknown option $1${NC}"; shift ;;
        esac
    done

    # Default output path
    if [ -z "$output_path" ]; then
        local timestamp
        timestamp=$(date +%Y%m%d-%H%M%S)
        output_path="goals/goal-${timestamp}.md"
    fi

    # Ensure goals directory exists
    local goals_dir
    goals_dir=$(dirname "$output_path")
    mkdir -p "$goals_dir"

    WORK_DIR="$(pwd)"

    echo -e "${BLUE}Drafting goal specification...${NC}"
    echo -e "Objective: $objective"
    echo -e "Output: $output_path"
    echo -e "Model: $model"
    echo -e "Reasoning: $reasoning"
    echo ""

    # Auto-update check
    echo -e "${BLUE}Checking Codex CLI version...${NC}"
    if ! "$SCRIPT_DIR/codex-version-check.sh" --auto-update; then
        echo -e "${YELLOW}Warning: Could not verify/update Codex CLI version${NC}"
    fi
    echo ""

    # Inject goal profile AGENTS.md
    inject_agents "goal"
    CLEANUP_DONE=""
    trap 'if [ -z "$CLEANUP_DONE" ]; then CLEANUP_DONE=1; cleanup_agents; fi' EXIT INT TERM HUP

    # Verify codex is available
    if ! command -v codex >/dev/null 2>&1; then
        echo -e "${RED}Error: 'codex' CLI not found. Install with: npm install -g @openai/codex${NC}"
        exit 1
    fi

    local abs_output
    abs_output="$(cd "$goals_dir" && pwd)/$(basename "$output_path")"

    # Run codex exec with goal profile
    set +e
    _with_pty codex exec \
        --skip-git-repo-check \
        --sandbox workspace-write \
        --model "$model" \
        -c "model_reasoning_effort=\"$reasoning\"" \
        "Read the project at $(pwd) and create a goal specification for: $objective. Write the goal file to $abs_output." \
        </dev/null
    local exit_code=$?
    set -e

    # Cleanup AGENTS.md
    CLEANUP_DONE=1
    cleanup_agents

    if [ $exit_code -ne 0 ] && [ $exit_code -ne 130 ] && [ $exit_code -ne 143 ]; then
        echo -e "${RED}Codex exited with code $exit_code${NC}"
        exit $exit_code
    fi

    # Verify goal file was created
    if [ -f "$abs_output" ]; then
        echo ""
        echo -e "${GREEN}Goal specification created: $output_path${NC}"
        echo ""
        # Print summary from frontmatter
        if head -1 "$abs_output" | grep -q "^---"; then
            local obj_line
            obj_line=$(grep "^objective:" "$abs_output" | head -1 | sed 's/^objective: *//' | tr -d '"')
            if [ -n "$obj_line" ]; then
                echo -e "  Objective: $obj_line"
            fi
        fi
        local checkpoint_count
        checkpoint_count=$(grep -c "^[0-9]\+\." "$abs_output" 2>/dev/null || true)
        checkpoint_count="${checkpoint_count:-0}"
        echo -e "  Checkpoints: $checkpoint_count"
        local char_count
        char_count=$(wc -c < "$abs_output" | tr -d ' ')
        echo -e "  Size: ${char_count} chars"
        if [ "$char_count" -le 3500 ]; then
            echo -e "  Inline: ${GREEN}yes (under 3,500 char threshold)${NC}"
        else
            echo -e "  Inline: ${YELLOW}no (over 3,500 chars — will use file reference)${NC}"
        fi
    else
        echo ""
        echo -e "${RED}Warning: Goal file was not created at $output_path${NC}"
        echo -e "${YELLOW}Codex may not have written the file. Check the output above.${NC}"
        exit 1
    fi
}

# --- Command: run ---

cmd_run() {
    local goal_file="$1"
    shift || true

    if [ -z "$goal_file" ]; then
        echo -e "${RED}Error: Goal file path is required${NC}"
        echo "Usage: codex-goal.sh run <goal-file> [--model <model>] [--sandbox <mode>]"
        exit 1
    fi

    if [ ! -f "$goal_file" ]; then
        echo -e "${RED}Error: Goal file not found: $goal_file${NC}"
        exit 1
    fi

    local model="gpt-5.6-sol"
    local sandbox="workspace-write"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --model)
                if [[ $# -lt 2 || "$2" == --* ]]; then
                    echo -e "${RED}Error: $1 requires a value${NC}"; exit 1
                fi
                model="$2"; shift 2 ;;
            --sandbox)
                if [[ $# -lt 2 || "$2" == --* ]]; then
                    echo -e "${RED}Error: $1 requires a value${NC}"; exit 1
                fi
                sandbox="$2"; shift 2 ;;
            *) echo -e "${YELLOW}Warning: Unknown option $1${NC}"; shift ;;
        esac
    done

    # Read goal content
    local content
    content=$(cat "$goal_file")
    local char_count=${#content}

    # Extract objective from frontmatter for summary
    local objective=""
    if echo "$content" | head -1 | grep -q "^---"; then
        objective=$(echo "$content" | grep "^objective:" | head -1 | sed 's/^objective: *//' | tr -d '"')
    fi

    echo -e "${BLUE}Launching Codex TUI with /goal...${NC}"
    echo -e "Goal file: $goal_file"
    echo -e "Objective: ${objective:-<not found in frontmatter>}"
    echo -e "Size: ${char_count} chars"
    echo -e "Model: $model"
    echo -e "Sandbox: $sandbox"
    echo ""

    # Verify codex is available
    if ! command -v codex >/dev/null 2>&1; then
        echo -e "${RED}Error: 'codex' CLI not found. Install with: npm install -g @openai/codex${NC}"
        exit 1
    fi

    # Build the /goal prompt based on content size
    local goal_prompt
    if [ "$char_count" -le 3500 ]; then
        goal_prompt="/goal $content"
    else
        local abs_path
        abs_path="$(cd "$(dirname "$goal_file")" && pwd)/$(basename "$goal_file")"
        local summary="${objective:-Follow the goal specification}"
        goal_prompt="/goal Follow the objective in $abs_path: $summary"
    fi

    echo -e "${GREEN}Launching interactive Codex TUI with goal.${NC}"
    echo -e "${YELLOW}Use /goal to check status. Use /goal pause to pause. Use /goal clear to abort.${NC}"
    echo ""

    # Launch interactive TUI — stdin is NOT redirected (user interacts directly)
    # No AGENTS.md injection: the goal profile is a spec writer, not relevant during TUI execution.
    # Codex uses its own context + the project's existing AGENTS.md (if any) during the goal run.
    set +e
    codex \
        --enable goals \
        --model "$model" \
        --sandbox "$sandbox" \
        "$goal_prompt"
    local exit_code=$?
    set -e

    exit $exit_code
}

# --- Command: list ---

cmd_list() {
    local goals_dir="goals"

    while [[ $# -gt 0 ]]; do
        case $1 in
            --dir) goals_dir="$2"; shift 2 ;;
            *) echo -e "${YELLOW}Warning: Unknown option $1${NC}"; shift ;;
        esac
    done

    if [ ! -d "$goals_dir" ]; then
        echo -e "${YELLOW}No goals directory found at: $goals_dir${NC}"
        echo "Run 'codex-goal.sh draft' to create your first goal."
        exit 0
    fi

    local count=0
    printf "${BLUE}%-40s %-12s %s${NC}\n" "FILE" "STATUS" "OBJECTIVE"
    printf "%-40s %-12s %s\n" "----" "------" "---------"

    for file in "$goals_dir"/*.md; do
        [ -f "$file" ] || continue
        count=$((count + 1))

        local objective=""
        local status=""

        if head -1 "$file" | grep -q "^---"; then
            objective=$(grep "^objective:" "$file" | head -1 | sed 's/^objective: *//' | tr -d '"')
            status=$(grep "^status:" "$file" | head -1 | sed 's/^status: *//' | tr -d '"')
        fi

        # Truncate objective for display
        if [ ${#objective} -gt 50 ]; then
            objective="${objective:0:47}..."
        fi

        printf "%-40s %-12s %s\n" "$(basename "$file")" "${status:-unknown}" "${objective:-<no objective>}"
    done

    if [ $count -eq 0 ]; then
        echo -e "${YELLOW}No goal files found in $goals_dir/${NC}"
        echo "Run 'codex-goal.sh draft' to create your first goal."
    else
        echo ""
        echo -e "${GREEN}$count goal(s) found${NC}"
    fi
}

# --- Main dispatch ---

if [ $# -lt 1 ]; then
    show_usage
    exit 1
fi

COMMAND="$1"
shift

case "$COMMAND" in
    draft) cmd_draft "$@" ;;
    run)   cmd_run "$@" ;;
    list)  cmd_list "$@" ;;
    -h|--help|help) show_usage ;;
    *)
        echo -e "${RED}Error: Unknown command '$COMMAND'${NC}"
        show_usage
        exit 1
        ;;
esac
