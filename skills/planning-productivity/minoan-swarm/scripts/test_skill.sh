#!/usr/bin/env bash
# test_skill.sh — Validate all minoan-swarm skill features
# Usage: bash test_skill.sh [project-root]
#
# Runs a comprehensive check of skill structure, references,
# naming codex integrity, template syntax, and context discovery.

set -uo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_ROOT="${1:-}"
PASS=0
FAIL=0
WARN=0

pass() { ((PASS++)); echo "  [PASS] $1"; }
fail() { ((FAIL++)); echo "  [FAIL] $1"; }
warn() { ((WARN++)); echo "  [WARN] $1"; }

echo "=== MINOAN SWARM: SKILL VALIDATION ==="
echo "Skill: $SKILL_DIR"
[[ -n "$PROJECT_ROOT" ]] && echo "Project: $PROJECT_ROOT"
echo ""

# ─── 1. Skill Structure ───
echo "--- 1. Skill Structure ---"

if [[ -f "$SKILL_DIR/SKILL.md" ]]; then
  pass "SKILL.md exists"
  if head -1 "$SKILL_DIR/SKILL.md" | grep -q "^---"; then
    pass "SKILL.md has YAML frontmatter"
  else
    fail "SKILL.md missing YAML frontmatter"
  fi
  if grep -q "^name:" "$SKILL_DIR/SKILL.md"; then
    pass "SKILL.md has name field"
  else
    fail "SKILL.md missing name field"
  fi
  if grep -q "^description:" "$SKILL_DIR/SKILL.md"; then
    pass "SKILL.md has description field"
  else
    fail "SKILL.md missing description field"
  fi
else
  fail "SKILL.md not found"
fi

if [[ -d "$SKILL_DIR/scripts" ]]; then
  pass "scripts/ directory exists"
else
  fail "scripts/ directory missing"
fi

if [[ -d "$SKILL_DIR/references" ]]; then
  pass "references/ directory exists"
else
  fail "references/ directory missing"
fi

echo ""

# ─── 2. Scripts ───
echo "--- 2. Scripts ---"

if [[ -f "$SKILL_DIR/scripts/discover_context.sh" ]]; then
  pass "discover_context.sh exists"
  if [[ -x "$SKILL_DIR/scripts/discover_context.sh" ]]; then
    pass "discover_context.sh is executable"
  else
    fail "discover_context.sh is not executable"
  fi
else
  fail "discover_context.sh not found"
fi

if [[ -f "$SKILL_DIR/scripts/test_skill.sh" ]]; then
  pass "test_skill.sh exists (self-referential!)"
fi

echo ""

# ─── 3. References ───
echo "--- 3. References ---"

for ref in naming-codex.md team-templates.md agent-teams-quickref.md; do
  if [[ -f "$SKILL_DIR/references/$ref" ]]; then
    lines=$(wc -l < "$SKILL_DIR/references/$ref" | tr -d ' ')
    pass "$ref exists ($lines lines)"
  else
    fail "$ref not found"
  fi
done

echo ""

# ─── 4. Naming Codex Integrity (Minoan-Semitic) ───
echo "--- 4. Naming Codex ---"

codex="$SKILL_DIR/references/naming-codex.md"
if [[ -f "$codex" ]]; then
  # Check for all 5 Aspects (team names)
  for aspect in Athirat Qedeshot Tiamat Kaptaru Elat; do
    if grep -q "$aspect" "$codex"; then
      pass "Aspect: $aspect"
    else
      fail "Missing aspect: $aspect"
    fi
  done

  # Check for key Minoan-Semitic archetypes
  for name in athirat-lead qedesha-lead devorah melissa kaptaru mami tehom tip\'eret hestia karme themis sassuratu membliaros; do
    if grep -q "$name" "$codex"; then
      pass "Teammate: $name"
    else
      fail "Missing teammate: $name"
    fi
  done

  # Check for pronunciations
  pron_count=$(grep -c "Pronunciation" "$codex" || echo "0")
  if [[ "$pron_count" -ge 3 ]]; then
    pass "Pronunciation guides present ($pron_count tables)"
  else
    warn "Few pronunciation guides ($pron_count)"
  fi

  # Check for Phoenician script
  if grep -q "𐤁𐤓𐤀𐤔𐤉𐤕" "$codex"; then
    pass "Phoenician Ba'alat script present"
  else
    fail "Missing Phoenician script (𐤁𐤓𐤀𐤔𐤉𐤕)"
  fi

  # Check for Ugaritic script
  if grep -q "𐎀𐎘𐎗𐎚" "$codex"; then
    pass "Ugaritic Athirat script present"
  else
    fail "Missing Ugaritic script (𐎀𐎘𐎗𐎚)"
  fi

  # Check for Etymology Notes section
  if grep -q "Etymology Notes" "$codex"; then
    pass "Etymology Notes section present"
  else
    warn "Missing Etymology Notes section"
  fi

  # Check for scholarly sources
  for source in Astour Gordon Lawler Atrahasis "Enuma Elish"; do
    if grep -q "$source" "$codex"; then
      pass "Source cited: $source"
    else
      warn "Missing source: $source"
    fi
  done
else
  fail "Naming codex not found"
fi

echo ""

# ─── 5. Team Templates ───
echo "--- 5. Team Templates ---"

templates="$SKILL_DIR/references/team-templates.md"
if [[ -f "$templates" ]]; then
  for tmpl in "Parallel Features" "Pipeline" "Research Swarm" "Phase Completion" "Code Review Tribunal"; do
    if grep -q "$tmpl" "$templates"; then
      pass "Template: $tmpl"
    else
      fail "Missing template: $tmpl"
    fi
  done

  for call in TeamCreate TaskCreate "run_in_background" addBlockedBy "file ownership"; do
    if grep -qi "$call" "$templates"; then
      pass "Template includes: $call"
    else
      warn "Template may be missing: $call"
    fi
  done

  # Check templates use Minoan-Semitic names
  for name in athirat kaptaru qedeshot elat mami melissa devorah sassuratu; do
    if grep -q "$name" "$templates"; then
      pass "Template uses Semitic name: $name"
    else
      warn "Template missing Semitic name: $name"
    fi
  done
else
  fail "Team templates not found"
fi

echo ""

# ─── 6. API Quick Reference ───
echo "--- 6. API Quick Reference ---"

quickref="$SKILL_DIR/references/agent-teams-quickref.md"
if [[ -f "$quickref" ]]; then
  for tool in TeamCreate TeamDelete SendMessage TaskCreate TaskList TaskUpdate; do
    if grep -q "$tool" "$quickref"; then
      pass "API tool documented: $tool"
    else
      fail "Missing API tool: $tool"
    fi
  done

  if grep -q "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS" "$quickref"; then
    pass "Agent Teams env variable documented"
  else
    fail "Missing env variable documentation"
  fi

  for mtype in "shutdown_request" "shutdown_response" "plan_approval_response" "broadcast"; do
    if grep -q "$mtype" "$quickref"; then
      pass "Message type: $mtype"
    else
      warn "Missing message type: $mtype"
    fi
  done
else
  fail "API quickref not found"
fi

echo ""

# ─── 7. Context Discovery (live test) ───
echo "--- 7. Context Discovery ---"

if [[ -n "$PROJECT_ROOT" ]] && [[ -d "$PROJECT_ROOT" ]]; then
  output=$(bash "$SKILL_DIR/scripts/discover_context.sh" "$PROJECT_ROOT" 2>&1)
  exit_code=$?

  if [[ $exit_code -eq 0 ]]; then
    pass "discover_context.sh exited cleanly (code 0)"
  else
    fail "discover_context.sh exited with code $exit_code"
  fi

  if echo "$output" | grep -q "DISCOVERY COMPLETE"; then
    pass "Discovery completed successfully"
  else
    fail "Discovery did not complete"
  fi

  for section in "Identity" "Planning" "Codebase" "Tests" "Issues" "Git"; do
    if echo "$output" | grep -q "$section"; then
      pass "Section found: $section"
    else
      warn "Section missing: $section"
    fi
  done

  found_count=$(echo "$output" | grep -c "\[found\]" || echo "0")
  if [[ "$found_count" -gt 0 ]]; then
    pass "Discovered $found_count artifacts"
  else
    warn "No artifacts discovered (may be an empty repo)"
  fi
else
  if [[ -z "$PROJECT_ROOT" ]]; then
    warn "No project root provided — skipping live discovery test"
    echo "         (run: bash test_skill.sh /path/to/repo)"
  else
    fail "Project root does not exist: $PROJECT_ROOT"
  fi
fi

echo ""

# ─── 8. Cross-references ───
echo "--- 8. Cross-References ---"

skill_md="$SKILL_DIR/SKILL.md"
if [[ -f "$skill_md" ]]; then
  for ref in naming-codex.md team-templates.md agent-teams-quickref.md; do
    if grep -q "$ref" "$skill_md"; then
      pass "SKILL.md references $ref"
    else
      warn "SKILL.md does not reference $ref"
    fi
  done

  if grep -q "discover_context" "$skill_md"; then
    pass "SKILL.md references discover_context.sh"
  else
    warn "SKILL.md does not reference discover_context.sh"
  fi

  if grep -q "Sappho" "$skill_md"; then
    pass "Sappho signature present"
  else
    warn "Missing Sappho signature"
  fi

  if grep -q "𐤁𐤓𐤀𐤔𐤉𐤕" "$skill_md"; then
    pass "Phoenician Ba'alat in SKILL.md"
  else
    warn "Missing Phoenician in SKILL.md"
  fi

  # Check SKILL.md uses Minoan-Semitic naming
  if grep -q "Minoan-Semitic" "$skill_md"; then
    pass "SKILL.md identifies as Minoan-Semitic tradition"
  else
    warn "SKILL.md does not mention Minoan-Semitic"
  fi
fi

echo ""

# ─── Summary ───
echo "=== VALIDATION SUMMARY ==="
TOTAL=$((PASS + FAIL + WARN))
echo "  Total checks: $TOTAL"
echo "  Passed: $PASS"
echo "  Failed: $FAIL"
echo "  Warnings: $WARN"
echo ""

if [[ $FAIL -eq 0 ]]; then
  echo "  Result: ALL CHECKS PASSED"
  echo ""
  echo "  \"Someone, I tell you, will remember us.\" — Sappho"
  exit 0
else
  echo "  Result: $FAIL FAILURES — please fix before using"
  exit 1
fi
