#!/bin/bash
# Invoke Codex CLI as CTO for plan or review phases
# Usage: cto-invoke.sh <plan|review> "<prompt>" [--model MODEL] [--dry-run]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$SCRIPT_DIR/.."
AGENTS_FILE="$SKILL_DIR/agents/cto.md"
TEMPLATES_DIR="$SKILL_DIR/templates"
ORCHESTRATOR_DIR="$HOME/.claude/skills/codex-orchestrator/scripts"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

show_usage() {
    echo "Usage: cto-invoke.sh <plan|review> \"<prompt>\" [options]"
    echo ""
    echo "Phases:"
    echo "  plan    - Analyze codebase and produce structured task plan"
    echo "  review  - Evaluate implementation results and issue verdict"
    echo ""
    echo "Options:"
    echo "  --model <model>   Model ID (default: config default)"
    echo "                    Examples: gpt-5.3-codex, gpt-5.2-codex, gpt-5.3-codex-spark"
    echo "  --dry-run         Print the command without executing"
    echo ""
    echo "Examples:"
    echo "  cto-invoke.sh plan \"Add WebSocket auth to the Express API\""
    echo "  cto-invoke.sh review \"Health check added at /health. Tests pass.\""
    echo "  cto-invoke.sh plan \"Refactor auth module\" --model gpt-5.3-codex-spark"
}

if [ $# -lt 2 ]; then
    show_usage
    exit 1
fi

PHASE="$1"
PROMPT="$2"
shift 2

if [ "$PHASE" != "plan" ] && [ "$PHASE" != "review" ]; then
    echo -e "${RED}Error: Phase must be 'plan' or 'review', got '$PHASE'${NC}"
    exit 1
fi

# Select schema
SCHEMA_FILE="$TEMPLATES_DIR/${PHASE}-schema.json"
if [ ! -f "$SCHEMA_FILE" ]; then
    echo -e "${RED}Error: Schema not found at $SCHEMA_FILE${NC}"
    exit 1
fi

# Parse options
MODEL=""
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --model)
            MODEL="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo -e "${YELLOW}Warning: Unknown option $1${NC}"
            shift
            ;;
    esac
done

# Version check (reuse codex-orchestrator's script)
if [ -f "$ORCHESTRATOR_DIR/codex-version-check.sh" ]; then
    "$ORCHESTRATOR_DIR/codex-version-check.sh" --auto-update --silent || true
fi

WORK_DIR="$(pwd)"

# Create artifact directory (PID-namespaced)
ARTIFACT_DIR="$WORK_DIR/.codex-cto/$$"
mkdir -p "$ARTIFACT_DIR"

# Determine output file with incrementing suffix
EXISTING=$(ls "$ARTIFACT_DIR"/${PHASE}-*.json 2>/dev/null | wc -l | tr -d ' ')
SEQ=$(printf "%03d" $((EXISTING + 1)))
OUTPUT_FILE="$ARTIFACT_DIR/${PHASE}-${SEQ}.json"

# AGENTS.md backup and symlink
AGENTS_BACKUP=""
if [ -f "$WORK_DIR/AGENTS.md" ]; then
    AGENTS_BACKUP="$WORK_DIR/AGENTS.md.backup.$$"
    mv "$WORK_DIR/AGENTS.md" "$AGENTS_BACKUP"
fi
ln -sf "$AGENTS_FILE" "$WORK_DIR/AGENTS.md"

cleanup() {
    rm -f "$WORK_DIR/AGENTS.md"
    if [ -n "$AGENTS_BACKUP" ] && [ -f "$AGENTS_BACKUP" ]; then
        mv "$AGENTS_BACKUP" "$WORK_DIR/AGENTS.md"
    fi
}
trap cleanup EXIT

echo -e "${GREEN}Codex CTO — ${PHASE} phase${NC}"
if [ -n "$MODEL" ]; then
    echo -e "Model: $MODEL"
else
    echo -e "Model: (default from config)"
fi
echo -e "Schema: ${PHASE}-schema.json"
echo -e "Output: $OUTPUT_FILE"
echo -e "Prompt: $PROMPT"
echo ""

# Build command
CODEX_CMD="codex exec --sandbox read-only --skip-git-repo-check"
CODEX_CMD="$CODEX_CMD --output-schema \"$SCHEMA_FILE\""
CODEX_CMD="$CODEX_CMD -o \"$OUTPUT_FILE\""
if [ -n "$MODEL" ]; then
    CODEX_CMD="$CODEX_CMD --model \"$MODEL\""
fi
CODEX_CMD="$CODEX_CMD \"$PROMPT\""

if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}[dry-run] Would execute:${NC}"
    echo "$CODEX_CMD"
    exit 0
fi

# Execute
eval $CODEX_CMD

# Output result to stdout
if [ -f "$OUTPUT_FILE" ]; then
    cat "$OUTPUT_FILE"
else
    echo -e "${RED}Error: No output file generated${NC}"
    exit 1
fi
