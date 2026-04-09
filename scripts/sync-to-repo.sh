#!/bin/bash
# sync-to-repo.sh
#
# Syncs ~/.claude/ content to this repo checkout.
# Reads category mapping and exclusion lists from .sync-config.json at the repo root.
#
# Usage:
#   ./scripts/sync-to-repo.sh [--dry-run] [--skills-only] [--hooks-only] [--commands-only]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CONFIG_FILE="${REPO_ROOT}/.sync-config.json"

# --- Argument parsing ---

DRY_RUN=false
SKILLS_ONLY=false
HOOKS_ONLY=false
COMMANDS_ONLY=false

for arg in "$@"; do
  case "$arg" in
    --dry-run)       DRY_RUN=true ;;
    --skills-only)   SKILLS_ONLY=true ;;
    --hooks-only)    HOOKS_ONLY=true ;;
    --commands-only) COMMANDS_ONLY=true ;;
    *)
      echo "Unknown flag: $arg"
      echo "Usage: $0 [--dry-run] [--skills-only] [--hooks-only] [--commands-only]"
      exit 1
      ;;
  esac
done

# If no scope flag is set, sync everything.
if ! $SKILLS_ONLY && ! $HOOKS_ONLY && ! $COMMANDS_ONLY; then
  SKILLS_ONLY=true
  HOOKS_ONLY=true
  COMMANDS_ONLY=true
fi

# --- Dependency check ---

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required but not installed. Install with: brew install jq"
  exit 1
fi

if [ ! -f "${CONFIG_FILE}" ]; then
  echo "ERROR: Config file not found: ${CONFIG_FILE}"
  exit 1
fi

# --- Load config ---

SOURCE_DIR="$(jq -r '.source_dir' "${CONFIG_FILE}" | sed "s|~|${HOME}|g")"
EXCLUDED_SKILLS="$(jq -r '.excluded_skills[]' "${CONFIG_FILE}")"

is_skill_excluded() {
  echo "${EXCLUDED_SKILLS}" | grep -qx "$1"
}

# --- Counters ---

SKILLS_SYNCED=0
SKILLS_SKIPPED=0
SKILLS_WARNED=0
HOOKS_SYNCED=0
COMMANDS_SYNCED=0

# --- Sync skills ---

sync_skills() {
  local skills_source="${SOURCE_DIR}/skills"

  if [ ! -d "${skills_source}" ]; then
    echo "WARNING: Skills source not found: ${skills_source}"
    return
  fi

  echo ""
  echo "=== Syncing skills ==="
  $DRY_RUN && echo "(dry run)"

  for skill_path in "${skills_source}"/*/; do
    [ -d "${skill_path}" ] || continue
    local skill_name
    skill_name="$(basename "${skill_path}")"

    if is_skill_excluded "${skill_name}"; then
      (( SKILLS_SKIPPED++ )) || true
      continue
    fi

    local category
    category="$(jq -r --arg name "${skill_name}" '.category_map[$name] // empty' "${CONFIG_FILE}")"

    if [ -z "${category}" ]; then
      echo "  WARNING: '${skill_name}' not in category_map -- skipping"
      (( SKILLS_WARNED++ )) || true
      continue
    fi

    local dest_dir="${REPO_ROOT}/skills/${category}/${skill_name}"

    if $DRY_RUN; then
      if [ -d "${dest_dir}" ]; then
        echo "  [update] ${skill_name} -> skills/${category}/${skill_name}"
      else
        echo "  [new]    ${skill_name} -> skills/${category}/${skill_name}"
      fi
    else
      mkdir -p "${dest_dir}"
      # Protect rules (`P`) prevent --delete from wiping files that exist
      # only in the repo. Useful for READMEs and for skills whose canonical
      # source lives outside ~/.claude/skills/ (e.g. claude-peers MCP server
      # in ~/tools/claude-peers-mcp/, qwen3-tts scripts in ~/Desktop/
      # Programming/qwen3-tts/). Files matching these patterns are still
      # copied FROM source TO destination when present — protection only
      # affects --delete behavior.
      rsync -a --checksum --delete \
        --exclude='*.pyc' --exclude='__pycache__' --exclude='.DS_Store' \
        --exclude='*.db' --exclude='*.sqlite' --exclude='node_modules' \
        --exclude='.git' --exclude='.env' --exclude='.env.*' \
        --exclude='*.jsonl' --exclude='*.pid' --exclude='logs/' \
        --exclude='.spotify-cache' --exclude='.syncignore' \
        --filter=':- .syncignore' \
        --filter='P README.md' \
        --filter='P mcp-server/***' \
        --filter='P qwen3-tts/***' \
        --filter='P workflows/***' \
        --filter='P canvas/***' \
        "${skill_path%/}/" "${dest_dir}/"
    fi

    (( SKILLS_SYNCED++ )) || true
  done

  echo "  Synced: ${SKILLS_SYNCED} | Skipped: ${SKILLS_SKIPPED} | Unmapped: ${SKILLS_WARNED}"
}

# --- Sync hooks ---

sync_hooks() {
  local hooks_source="${SOURCE_DIR}/hooks"

  if [ ! -d "${hooks_source}" ]; then
    echo "WARNING: Hooks source not found: ${hooks_source}"
    return
  fi

  echo ""
  echo "=== Syncing hooks ==="
  $DRY_RUN && echo "(dry run)"

  for hook_file in "${hooks_source}"/*.py "${hooks_source}"/*.sh; do
    [ -f "${hook_file}" ] || continue
    local name
    name="$(basename "${hook_file}")"
    local dest="${REPO_ROOT}/hooks/${name}"

    if $DRY_RUN; then
      if [ -f "${dest}" ]; then
        echo "  [update] ${name}"
      else
        echo "  [new]    ${name}"
      fi
    else
      cp "${hook_file}" "${dest}"
    fi

    (( HOOKS_SYNCED++ )) || true
  done

  echo "  Synced: ${HOOKS_SYNCED}"
}

# --- Sync commands ---

sync_commands() {
  local commands_source="${SOURCE_DIR}/commands"

  if [ ! -d "${commands_source}" ]; then
    echo "WARNING: Commands source not found: ${commands_source}"
    return
  fi

  echo ""
  echo "=== Syncing commands ==="
  $DRY_RUN && echo "(dry run)"

  for cmd_file in "${commands_source}"/*.md; do
    [ -f "${cmd_file}" ] || continue
    local name
    name="$(basename "${cmd_file}")"
    local dest="${REPO_ROOT}/commands/${name}"

    if $DRY_RUN; then
      if [ -f "${dest}" ]; then
        echo "  [update] ${name}"
      else
        echo "  [new]    ${name}"
      fi
    else
      cp "${cmd_file}" "${dest}"
    fi

    (( COMMANDS_SYNCED++ )) || true
  done

  echo "  Synced: ${COMMANDS_SYNCED}"
}

# --- Main ---

echo "Source: ${SOURCE_DIR}"
echo "Target: ${REPO_ROOT}"

$SKILLS_ONLY   && sync_skills
$HOOKS_ONLY    && sync_hooks
$COMMANDS_ONLY && sync_commands

# --- Summary ---

echo ""
echo "========================================"
if ! $DRY_RUN; then
  skill_count="$(find "${REPO_ROOT}/skills" -name 'SKILL.md' -not -path '*/\\_archive/*' 2>/dev/null | wc -l | tr -d ' ')"
  hook_count="$(find "${REPO_ROOT}/hooks" -maxdepth 1 \( -name '*.py' -o -name '*.sh' \) 2>/dev/null | wc -l | tr -d ' ')"
  command_count="$(find "${REPO_ROOT}/commands" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
  echo "Skills: ${skill_count} | Hooks: ${hook_count} | Commands: ${command_count}"
else
  echo "Dry run complete. No files were modified."
fi
echo "========================================"
