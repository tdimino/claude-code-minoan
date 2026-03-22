#!/usr/bin/env bash
# Custom lint rules for project-specific conventions.
# Called by lint-on-write.py: custom-lint.sh <file> <project>
# Output: one violation per line, format: "LINE: [custom] MESSAGE"
# Exit 0 always — violations are stdout, not exit codes.

# No set -e / pipefail — this script must exit 0 always.
# Violations are communicated via stdout, not exit codes.

FILE="${1:-}"
PROJECT="${2:-}"

# Exit gracefully if no file provided
if [[ -z "$FILE" || ! -f "$FILE" ]]; then
    exit 0
fi
EXT="${FILE##*.}"
BASENAME="$(basename "$FILE")"

# Helper: grep with line numbers, reformat to our violation format
# Usage: check_pattern PATTERN MESSAGE [extra_grep_flags]
check_pattern() {
    local pattern="$1"
    local message="$2"
    shift 2
    grep -n "$@" "$pattern" "$FILE" 2>/dev/null | while IFS=: read -r line_num content; do
        echo "${line_num}: [custom] ${message}"
    done || true
}

# Helper: check if file contains a pattern (boolean, no output)
file_contains() {
    grep -q "$1" "$FILE" 2>/dev/null
}

case "$PROJECT" in

worldwarwatcher)
    case "$EXT" in
        tsx|jsx)
            # No hardcoded hex colors in JSX (skip imports, comments, and known exceptions)
            grep -En '#[0-9a-fA-F]{3,8}' "$FILE" 2>/dev/null \
                | grep -v '^\s*//' \
                | grep -v 'import ' \
                | grep -v '// eslint-disable' \
                | grep -v 'constants' \
                | while IFS=: read -r line_num content; do
                    echo "${line_num}: [custom] Hardcoded hex value — use @theme CSS variable instead"
                done || true

            # No non-Phosphor icon imports
            grep -n "from ['\"]react-icons" "$FILE" 2>/dev/null | while IFS=: read -r line_num _; do
                echo "${line_num}: [custom] Import from react-icons — use @phosphor-icons/react instead"
            done || true
            grep -n "from ['\"]lucide-react" "$FILE" 2>/dev/null | while IFS=: read -r line_num _; do
                echo "${line_num}: [custom] Import from lucide-react — use @phosphor-icons/react instead"
            done || true
            grep -n "from ['\"]@heroicons" "$FILE" 2>/dev/null | while IFS=: read -r line_num _; do
                echo "${line_num}: [custom] Import from heroicons — use @phosphor-icons/react instead"
            done || true

            # No backdrop-blur (crashes Chrome GPU compositor over WebGL)
            grep -n 'backdrop-blur\|backdrop-filter.*blur' "$FILE" 2>/dev/null | while IFS=: read -r line_num _; do
                echo "${line_num}: [custom] backdrop-blur over WebGL crashes Chrome GPU compositor — avoid"
            done || true

            # Em dash spacing: catch " — " (space-surrounded em dash)
            grep -n ' — ' "$FILE" 2>/dev/null \
                | grep -v '^\s*//' \
                | grep -v '^\s*\*' \
                | while IFS=: read -r line_num _; do
                    echo "${line_num}: [custom] Em dash has spaces — attach directly to text (e.g. 'word—word')"
                done || true
            ;;

        css|scss)
            # No hardcoded hex in color properties
            grep -n 'color:\s*#\|background.*:\s*#' "$FILE" 2>/dev/null \
                | grep -v '^\s*/\*' \
                | grep -v '^\s*\*' \
                | while IFS=: read -r line_num content; do
                    echo "${line_num}: [custom] Hardcoded hex in color property — use @theme CSS variable"
                done || true

            # No backdrop-blur
            grep -n 'backdrop-blur\|backdrop-filter.*blur' "$FILE" 2>/dev/null | while IFS=: read -r line_num _; do
                echo "${line_num}: [custom] backdrop-blur over WebGL crashes Chrome GPU compositor — avoid"
            done || true
            ;;

        ts)
            # Em dash spacing (ts-only, tsx covered above)
            grep -n ' — ' "$FILE" 2>/dev/null \
                | grep -v '^\s*//' \
                | grep -v '^\s*\*' \
                | while IFS=: read -r line_num _; do
                    echo "${line_num}: [custom] Em dash has spaces — attach directly to text (e.g. 'word—word')"
                done || true
            ;;
    esac
    ;;

open-rebellion)
    case "$EXT" in
        rs)
            # No fieldN names in struct fields or variable bindings (skip DAT header pattern and comments)
            # The entity table pattern uses field1/field4 in headers — exclude dat/ directory
            if [[ "$FILE" != *"/dat/"* ]]; then
                grep -En '\bfield[0-9]+' "$FILE" 2>/dev/null \
                    | grep -v '^\s*//' \
                    | grep -v '^\s*\*' \
                    | grep -v '^\s*#' \
                    | grep -v 'flag_col' \
                    | while IFS=: read -r line_num content; do
                        echo "${line_num}: [custom] fieldN name detected — use a semantic name for known fields"
                    done || true
            fi
            ;;
    esac

    # Check rebellion-core Cargo.toml for rendering deps
    if [[ "$BASENAME" == "Cargo.toml" && "$FILE" == *"rebellion-core"* ]]; then
        grep -n 'macroquad\|egui\|image\s*=' "$FILE" 2>/dev/null | while IFS=: read -r line_num content; do
            echo "${line_num}: [custom] Rendering dependency in rebellion-core — core must remain headless-testable"
        done || true
    fi
    ;;

minoanmystery-astro)
    case "$EXT" in
        css|astro)
            # No transition: all
            grep -n 'transition:\s*all' "$FILE" 2>/dev/null | while IFS=: read -r line_num _; do
                echo "${line_num}: [custom] transition: all — enumerate specific properties instead"
            done || true

            # Hardcoded hex in color properties
            grep -n 'color:\s*#\|background.*:\s*#' "$FILE" 2>/dev/null \
                | grep -v '^\s*/\*' \
                | grep -v '^\s*\*' \
                | grep -v ':root' \
                | grep -v '@theme' \
                | grep -v 'var(' \
                | while IFS=: read -r line_num content; do
                    echo "${line_num}: [custom] Hardcoded hex in color property — use CSS variable (var(--color-*))"
                done || true

            # scroll-behavior: smooth without prefers-reduced-motion gate
            if grep -q 'scroll-behavior:\s*smooth' "$FILE" 2>/dev/null; then
                if ! grep -q 'prefers-reduced-motion' "$FILE" 2>/dev/null; then
                    grep -n 'scroll-behavior:\s*smooth' "$FILE" 2>/dev/null | while IFS=: read -r line_num _; do
                        echo "${line_num}: [custom] scroll-behavior: smooth without prefers-reduced-motion gate"
                    done || true
                fi
            fi
            ;;

        ts|tsx|js|jsx)
            # No GSAP imports (Motion library preferred)
            grep -n "from ['\"]gsap" "$FILE" 2>/dev/null | while IFS=: read -r line_num _; do
                echo "${line_num}: [custom] GSAP import — prefer Motion library instead"
            done || true
            ;;
    esac
    ;;

esac

exit 0
