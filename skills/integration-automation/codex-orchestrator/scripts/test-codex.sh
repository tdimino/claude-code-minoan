#!/bin/bash
# Test suite for Codex Orchestrator skill
# Usage: test-codex.sh [--quick]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$SCRIPT_DIR/.."

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TESTS_PASSED=0
TESTS_FAILED=0
QUICK_MODE=false

# Parse arguments
if [ "$1" == "--quick" ]; then
    QUICK_MODE=true
fi

test_pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

test_fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

echo -e "${BLUE}=== Codex Orchestrator Test Suite ===${NC}\n"

# Test 1: Check Codex CLI installation
echo -e "${YELLOW}Test 1: Codex CLI Installation${NC}"
if command -v codex &> /dev/null; then
    test_pass "Codex CLI is installed"
else
    test_fail "Codex CLI not found"
fi

# Test 2: Check all agent profiles exist
echo -e "\n${YELLOW}Test 2: Agent Profiles${NC}"
for profile in reviewer debugger architect security refactor docs planner syseng builder researcher adjudicator chat goal; do
    if [ -f "$SKILL_DIR/agents/$profile.md" ]; then
        test_pass "Profile '$profile' exists"
    else
        test_fail "Profile '$profile' missing"
    fi
done

# Test 3: Check scripts are executable
echo -e "\n${YELLOW}Test 3: Script Permissions${NC}"
for script in codex-exec.sh codex-astra.sh codex-status.sh test-codex.sh codex-goal.sh; do
    if [ -x "$SKILL_DIR/scripts/$script" ]; then
        test_pass "Script '$script' is executable"
    else
        test_fail "Script '$script' is not executable"
    fi
done

# Test 4: Check Python script syntax
echo -e "\n${YELLOW}Test 4: Python Syntax${NC}"
if PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/codex-orchestrator-pycache" python3 -m py_compile "$SKILL_DIR/scripts/codex-session.py" 2>/dev/null; then
    test_pass "codex-session.py has valid syntax"
else
    test_fail "codex-session.py has syntax errors"
fi

# Test 5: Check SKILL.md exists and has frontmatter
echo -e "\n${YELLOW}Test 5: SKILL.md Validation${NC}"
if [ -f "$SKILL_DIR/SKILL.md" ]; then
    if head -1 "$SKILL_DIR/SKILL.md" | grep -q "^---"; then
        test_pass "SKILL.md has YAML frontmatter"
    else
        test_fail "SKILL.md missing YAML frontmatter"
    fi
else
    test_fail "SKILL.md not found"
fi

# Test 6: Check references exist
echo -e "\n${YELLOW}Test 6: Reference Documentation${NC}"
for ref in codex-cli.md agents-md-format.md subagent-patterns.md goal-command.md; do
    if [ -f "$SKILL_DIR/references/$ref" ]; then
        test_pass "Reference '$ref' exists"
    else
        test_fail "Reference '$ref' missing"
    fi
done

# Test 7: Researcher profile specifics
echo -e "\n${YELLOW}Test 7: Researcher Profile${NC}"
# Verify researcher auto-config in codex-exec.sh
if grep -q 'SANDBOX="read-only"' "$SKILL_DIR/scripts/codex-exec.sh"; then
    test_pass "Researcher sets read-only sandbox"
else
    test_fail "Researcher missing read-only sandbox"
fi
if grep -q 'EPHEMERAL="--ephemeral"' "$SKILL_DIR/scripts/codex-exec.sh"; then
    test_pass "Researcher sets ephemeral flag"
else
    test_fail "Researcher missing ephemeral flag"
fi
if grep -q 'SANDBOX="read-only"' "$SKILL_DIR/scripts/codex-exec.sh"; then
    test_pass "Researcher defaults to read-only sandbox"
else
    test_fail "Researcher missing read-only sandbox default"
fi
# Verify Exa codex-agent-guide exists for web search
EXA_GUIDE="$HOME/.claude/skills/exa-search/codex-agent-guide.md"
if [ -f "$EXA_GUIDE" ]; then
    test_pass "Exa codex-agent-guide.md exists"
else
    test_fail "Exa codex-agent-guide.md missing"
fi

# Test 8: Write profiles use workspace-write sandbox (auto-approves in exec mode)
echo -e "\n${YELLOW}Test 8: Write Profile Defaults${NC}"
if grep -q 'SANDBOX="workspace-write"' "$SKILL_DIR/scripts/codex-exec.sh"; then
    test_pass "Write profiles default to workspace-write sandbox"
else
    test_fail "Write profiles missing workspace-write default"
fi
if grep -q 'dev/null' "$SKILL_DIR/scripts/codex-exec.sh"; then
    test_pass "stdin piped from /dev/null to prevent hangs"
else
    test_fail "Missing /dev/null stdin redirect"
fi

# Test 9: Backup/Restore Safety
echo -e "\n${YELLOW}Test 9: Backup/Restore Safety${NC}"

if grep -q '.AGENTS.md.codex-orchestrator-backup' "$SKILL_DIR/scripts/codex-exec.sh"; then
    test_pass "codex-exec.sh uses deterministic backup name"
else
    test_fail "codex-exec.sh missing deterministic backup name"
fi
if grep -q '.AGENTS.md.codex-orchestrator-backup' "$SKILL_DIR/scripts/codex-session.py"; then
    test_pass "codex-session.py uses deterministic backup name"
else
    test_fail "codex-session.py missing deterministic backup name"
fi
if grep -q 'trap cleanup EXIT INT TERM HUP' "$SKILL_DIR/scripts/codex-exec.sh"; then
    test_pass "codex-exec.sh traps EXIT INT TERM HUP"
else
    test_fail "codex-exec.sh missing extended signal traps"
fi
if grep -q 'crash recovery' "$SKILL_DIR/scripts/codex-exec.sh"; then
    test_pass "codex-exec.sh has crash recovery logic"
else
    test_fail "codex-exec.sh missing crash recovery logic"
fi
if grep -q 'AGENTS.md.backup\.\*' "$SKILL_DIR/scripts/codex-exec.sh"; then
    test_pass "codex-exec.sh migrates old PID-based backups"
else
    test_fail "codex-exec.sh missing PID-based backup migration"
fi

# Test 10: PTY Wrapper
echo -e "\n${YELLOW}Test 10: PTY Wrapper${NC}"
if grep -q '_with_pty' "$SKILL_DIR/scripts/codex-exec.sh"; then
    test_pass "codex-exec.sh has PTY wrapper function"
else
    test_fail "codex-exec.sh missing PTY wrapper function"
fi
if grep -q 'script.*-q' "$SKILL_DIR/scripts/codex-exec.sh"; then
    test_pass "codex-exec.sh uses script(1) for PTY re-attachment"
else
    test_fail "codex-exec.sh missing script(1) PTY wrapper"
fi
if grep -q '_with_pty' "$SKILL_DIR/scripts/codex-goal.sh"; then
    test_pass "codex-goal.sh has PTY wrapper function"
else
    test_fail "codex-goal.sh missing PTY wrapper function"
fi
if grep -q 'codex-backup.*os.getpid' "$SKILL_DIR/scripts/codex-session.py"; then
    test_pass "codex-session.py uses PID-scoped backup name"
else
    test_fail "codex-session.py missing PID-scoped backup name"
fi

# Test 11: GPT-6-Astra permutations
echo -e "\n${YELLOW}Test 11: GPT-6-Astra Permutations${NC}"
if bash -n "$SKILL_DIR/scripts/codex-astra.sh" && bash -n "$SKILL_DIR/scripts/codex-exec.sh"; then
    test_pass "Astra launch scripts have valid shell syntax"
else
    test_fail "Astra launch scripts have shell syntax errors"
fi
if grep -q 'ASTRA_MODEL="gpt-6-astra"' "$SKILL_DIR/scripts/codex-astra.sh"; then
    test_pass "Astra launcher pins the GPT-6-Astra model ID"
else
    test_fail "Astra launcher is missing the GPT-6-Astra model ID"
fi
astra_permutations=$("$SKILL_DIR/scripts/codex-astra.sh" list | grep -Ec '^(low|medium|high|xhigh|max|ultra)[[:space:]]+(default|priority)[[:space:]]*$' || true)
if [ "$astra_permutations" -eq 12 ]; then
    test_pass "Astra launcher exposes all 12 effort/tier permutations"
else
    test_fail "Astra launcher exposed $astra_permutations permutations instead of 12"
fi
if "$SKILL_DIR/scripts/codex-astra.sh" reviewer "test" --reasoning minimal >/dev/null 2>&1; then
    test_fail "Astra launcher accepted an unsupported reasoning effort"
else
    test_pass "Astra launcher rejects unsupported reasoning efforts before launch"
fi
if "$SKILL_DIR/scripts/codex-astra.sh" reviewer "test" --service-tier flex >/dev/null 2>&1; then
    test_fail "Astra launcher accepted an unsupported service tier"
else
    test_pass "Astra launcher rejects unsupported service tiers before launch"
fi

# Stub Codex so accepted permutations can be checked at the argv boundary
# without network access or model usage.
astra_test_root=$(mktemp -d "${TMPDIR:-/tmp}/codex-astra-test.XXXXXX")
astra_fake_bin="$astra_test_root/bin"
astra_work_dir="$astra_test_root/work"
astra_capture="$astra_test_root/argv.txt"
mkdir -p "$astra_fake_bin" "$astra_work_dir"
printf '%s\n' '#!/bin/bash' 'printf '\''%s\n'\'' "$@" > "$ASTRA_CAPTURE_FILE"' > "$astra_fake_bin/codex"
chmod +x "$astra_fake_bin/codex"

capture_astra() {
    (
        cd "$astra_work_dir"
        PATH="$astra_fake_bin:$PATH" \
        ASTRA_CAPTURE_FILE="$astra_capture" \
        CODEX_ORCHESTRATOR_SKIP_UPDATE=1 \
            "$SKILL_DIR/scripts/codex-astra.sh" "$@" >/dev/null 2>&1
    )
}

if capture_astra builder "default prompt with spaces" \
    && grep -Fxq 'gpt-6-astra' "$astra_capture" \
    && grep -Fxq 'model_reasoning_effort="medium"' "$astra_capture" \
    && grep -Fxq 'service_tier="default"' "$astra_capture" \
    && grep -Fxq 'default prompt with spaces' "$astra_capture"; then
    test_pass "Astra defaults reach Codex as model + medium + default with prompt quoting intact"
else
    test_fail "Astra default argv forwarding is incorrect"
fi

astra_matrix_ok=true
for effort in low medium high xhigh max ultra; do
    for tier in default priority; do
        expected_cli_tier="$tier"
        if [ "$tier" = "priority" ]; then
            expected_cli_tier="fast"
        fi
        if ! capture_astra architect "matrix-$effort-$tier" --reasoning "$effort" --service-tier "$tier" \
            || ! grep -Fxq 'gpt-6-astra' "$astra_capture" \
            || ! grep -Fxq "model_reasoning_effort=\"$effort\"" "$astra_capture" \
            || ! grep -Fxq "service_tier=\"$expected_cli_tier\"" "$astra_capture" \
            || ! grep -Fxq "matrix-$effort-$tier" "$astra_capture"; then
            astra_matrix_ok=false
            break 2
        fi
    done
done
if [ "$astra_matrix_ok" = true ]; then
    test_pass "All 12 Astra permutations forward exact Codex argv (priority maps to fast)"
else
    test_fail "Astra argv forwarding failed for $effort/$tier"
fi

if (
    cd "$astra_work_dir"
    PATH="$astra_fake_bin:$PATH" ASTRA_CAPTURE_FILE="$astra_capture" CODEX_ORCHESTRATOR_SKIP_UPDATE=1 \
        "$SKILL_DIR/scripts/codex-exec.sh" reviewer "direct shortcut" --astra --reasoning high --service-tier priority >/dev/null 2>&1
) && grep -Fxq 'gpt-6-astra' "$astra_capture" \
    && grep -Fxq 'model_reasoning_effort="high"' "$astra_capture" \
    && grep -Fxq 'service_tier="fast"' "$astra_capture"; then
    test_pass "Generic --astra shortcut forwards model, reasoning, and priority mapping"
else
    test_fail "Generic --astra shortcut argv forwarding is incorrect"
fi

if CODEX_ORCHESTRATOR_SKIP_UPDATE=1 "$SKILL_DIR/scripts/codex-exec.sh" reviewer "test" --api --service-tier priority >/dev/null 2>&1; then
    test_fail "codex-exec.sh accepted --service-tier with --api"
else
    test_pass "codex-exec.sh rejects --service-tier in API mode"
fi
if CODEX_ORCHESTRATOR_SKIP_UPDATE=1 "$SKILL_DIR/scripts/codex-exec.sh" reviewer "test" --astra --api >/dev/null 2>&1; then
    test_fail "codex-exec.sh accepted --astra with --api"
else
    test_pass "codex-exec.sh keeps Astra on the Codex subagent path"
fi
if CODEX_ORCHESTRATOR_SKIP_UPDATE=1 "$SKILL_DIR/scripts/codex-exec.sh" reviewer "test" --reasoning >/dev/null 2>&1; then
    test_fail "codex-exec.sh accepted --reasoning without a value"
else
    test_pass "codex-exec.sh rejects missing --reasoning values cleanly"
fi

rm -rf "$astra_test_root"

# Test 12: Quick API test (optional, skipped in quick mode)
if [ "$QUICK_MODE" = false ]; then
    echo -e "\n${YELLOW}Test 12: API Connectivity${NC}"
    if [ -n "$OPENAI_API_KEY" ]; then
        if timeout 15 codex exec --model gpt-5-mini "print('hello')" &> /dev/null; then
            test_pass "Codex API connection works"
        else
            test_fail "Codex API connection failed"
        fi
    else
        echo -e "${YELLOW}⚠ SKIP${NC}: OPENAI_API_KEY not set"
    fi
else
    echo -e "\n${YELLOW}Test 12: API Connectivity${NC}"
    echo -e "${YELLOW}⚠ SKIP${NC}: Quick mode enabled"
fi

# Summary
echo -e "\n${BLUE}=== Test Summary ===${NC}"
echo -e "Passed: ${GREEN}$TESTS_PASSED${NC}"
echo -e "Failed: ${RED}$TESTS_FAILED${NC}"

if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "\n${RED}Some tests failed!${NC}"
    exit 1
else
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
fi
