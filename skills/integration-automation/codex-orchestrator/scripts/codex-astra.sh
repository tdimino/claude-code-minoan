#!/bin/bash
# Launch GPT-6-Astra through any codex-orchestrator persona.
# Usage: codex-astra.sh <profile> "<prompt>" [options]
#        codex-astra.sh list

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASTRA_MODEL="gpt-6-astra"
DEFAULT_REASONING="medium"
DEFAULT_SERVICE_TIER="default"

show_usage() {
    echo "Usage: codex-astra.sh <profile> \"<prompt>\" [options]"
    echo "       codex-astra.sh list"
    echo ""
    echo "Astra options:"
    echo "  --reasoning <level>   low, medium, high, xhigh, max, ultra (default: medium)"
    echo "  --service-tier <tier> default, priority (default: default)"
    echo ""
    echo "All remaining options are forwarded to codex-exec.sh."
    echo ""
    echo "Examples:"
    echo "  codex-astra.sh reviewer \"Review the transaction boundary\" --reasoning high"
    echo "  codex-astra.sh architect \"Design the migration\" --reasoning max --service-tier priority"
    echo "  codex-astra.sh builder \"Implement the approved plan\" --reasoning ultra"
}

list_permutations() {
    echo "GPT-6-Astra permutations (available with every orchestrator profile):"
    echo ""
    printf '%-10s %-10s\n' "REASONING" "TIER"
    for reasoning in low medium high xhigh max ultra; do
        for tier in default priority; do
            printf '%-10s %-10s\n' "$reasoning" "$tier"
        done
    done
}

if [ "${1:-}" = "list" ]; then
    list_permutations
    exit 0
fi

if [ $# -lt 2 ]; then
    show_usage
    exit 1
fi

PROFILE="$1"
PROMPT="$2"
shift 2

HAS_REASONING=""
HAS_SERVICE_TIER=""
FORWARD_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --reasoning)
            if [[ $# -lt 2 || "$2" == --* ]]; then
                echo "Error: --reasoning requires a value" >&2
                exit 1
            fi
            case "$2" in
                low|medium|high|xhigh|max|ultra) ;;
                *)
                    echo "Error: GPT-6-Astra reasoning must be one of: low, medium, high, xhigh, max, ultra" >&2
                    exit 1
                    ;;
            esac
            HAS_REASONING="true"
            FORWARD_ARGS+=("$1" "$2")
            shift 2
            ;;
        --service-tier)
            if [[ $# -lt 2 || "$2" == --* ]]; then
                echo "Error: --service-tier requires a value" >&2
                exit 1
            fi
            case "$2" in
                default|priority) ;;
                *)
                    echo "Error: GPT-6-Astra service tier must be one of: default, priority" >&2
                    exit 1
                    ;;
            esac
            HAS_SERVICE_TIER="true"
            FORWARD_ARGS+=("$1" "$2")
            shift 2
            ;;
        --model|--astra)
            echo "Error: codex-astra.sh fixes the model to $ASTRA_MODEL; do not pass $1" >&2
            exit 1
            ;;
        --api)
            echo "Error: codex-astra.sh launches Codex CLI subagents; direct API mode is not supported" >&2
            exit 1
            ;;
        *)
            FORWARD_ARGS+=("$1")
            shift
            ;;
    esac
done

if [ -z "$HAS_REASONING" ]; then
    FORWARD_ARGS+=(--reasoning "$DEFAULT_REASONING")
fi
if [ -z "$HAS_SERVICE_TIER" ]; then
    FORWARD_ARGS+=(--service-tier "$DEFAULT_SERVICE_TIER")
fi

exec "$SCRIPT_DIR/codex-exec.sh" \
    "$PROFILE" \
    "$PROMPT" \
    --model "$ASTRA_MODEL" \
    "${FORWARD_ARGS[@]}"
