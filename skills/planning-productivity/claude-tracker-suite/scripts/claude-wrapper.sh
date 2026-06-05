#!/usr/bin/env bash
# claude-wrapper.sh — Named Claude Code sessions with Ghostty tab titles
#
# Source this file in ~/.zshrc to get the `cc` function:
#   source ~/.claude/skills/claude-tracker-suite/scripts/claude-wrapper.sh
#
# Usage:
#   cc                            # launch claude, tab titled to cwd basename
#   cc --name "kothar-refactor"   # launch claude with explicit tab title
#   cc --resume <id>              # resume session with tab title
#   cc --resume <id> --name "fix" # resume with explicit title
#
# All other flags pass through to claude unchanged.

cc() {
  local tab_name=""
  local resume_id=""
  local claude_args=()

  # Parse our flags, pass everything else through to claude
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --name)
        [[ $# -lt 2 ]] && { echo "cc: --name requires a value" >&2; return 1; }
        tab_name="$2"
        shift 2
        ;;
      --resume)
        [[ $# -lt 2 ]] && { echo "cc: --resume requires a session ID" >&2; return 1; }
        resume_id="$2"
        claude_args+=(--resume "$2")
        shift 2
        ;;
      *)
        claude_args+=("$1")
        shift
        ;;
    esac
  done

  # Build tab title: explicit name > resume ID prefix > cwd basename
  if [[ -z "$tab_name" ]]; then
    if [[ -n "$resume_id" ]]; then
      tab_name="$(basename "$PWD")—${resume_id:0:8}"
    else
      tab_name="$(basename "$PWD")"
    fi
  fi

  # Set Ghostty tab title via OSC 1
  printf '\e]1;%s\a' "$tab_name"

  # Launch claude with all passthrough args
  claude "${claude_args[@]}"

  # After claude exits, tag the session with the name for searchability
  if [[ -n "$tab_name" && "$tab_name" != "$(basename "$PWD")" ]]; then
    local tag_script="$HOME/.claude/skills/claude-tracker-suite/scripts/tag-session.js"
    if [[ -f "$tag_script" ]]; then
      node "$tag_script" add "name:${tab_name}" 2>/dev/null || true
    fi
  fi

  # Reset tab title to shell default
  printf '\e]1;%s\a' "$(basename "$PWD")"
}
