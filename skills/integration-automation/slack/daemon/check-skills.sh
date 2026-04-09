#!/usr/bin/env bash
# Check which skills from claude-code-minoan are installed globally.
# Usage: bash check-skills.sh
# Works with bash 3+ and zsh.

SKILLS_DIR="$HOME/.claude/skills"
REPO_URL="https://github.com/tdimino/claude-code-minoan"

installed=0
missing=0
disabled=0

check_skill() {
  local skill="$1"
  if [ -d "$SKILLS_DIR/$skill" ]; then
    echo "  + $skill"
    ((installed++))
  elif [ -d "$SKILLS_DIR/$skill.disabled" ]; then
    echo "  ~ $skill (disabled)"
    ((disabled++))
  else
    echo "  - $skill (not installed)"
    ((missing++))
  fi
}

echo ""
echo "=== core-development ==="
for s in architecture-md-builder beads-task-tracker claude-agent-sdk claude-md-manager react-best-practices skill-optimizer; do
  check_skill "$s"
done

echo ""
echo "=== design-media ==="
for s in aldea-slidedeck frontend-design gemini-claude-resonance nano-banana-pro photo-to-slack-emoji rocaille-shader; do
  check_skill "$s"
done

echo ""
echo "=== local-ml ==="
for s in smolvlm speak-response parakeet llama-cpp rlama; do
  check_skill "$s"
done

echo ""
echo "=== integration-automation ==="
for s in agent-browser beautiful-mermaid codex-orchestrator figma-mcp mcp-server-manager netlify-integration slack supabase-skill telnyx-api twilio-api twitter; do
  check_skill "$s"
done

echo ""
echo "=== planning-productivity ==="
for s in claude-tracker-suite crypt-librarian mdpreview minoan-swarm planning-with-files super-ralph-wiggum travel-requirements-expert; do
  check_skill "$s"
done

echo ""
echo "=== research ==="
for s in Firecrawl academic-research atk-ux-research exa-search; do
  check_skill "$s"
done

echo ""
echo "--- Summary ---"
echo "Repo skills installed: $installed"
echo "Repo skills missing:   $missing"
echo "Repo skills disabled:  $disabled"
echo ""
echo "Install missing: $REPO_URL"
echo "Toggle: source ~/.claude/skills/skill-toggle.sh && skill-list"
