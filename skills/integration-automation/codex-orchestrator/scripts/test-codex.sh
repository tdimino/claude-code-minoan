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
for profile in reviewer debugger architect security refactor docs planner syseng builder researcher; do
    if [ -f "$SKILL_DIR/agents/$profile.md" ]; then
        test_pass "Profile '$profile' exists"
    else
        test_fail "Profile '$profile' missing"
    fi
done

# Test 3: Check scripts are executable
echo -e "\n${YELLOW}Test 3: Script Permissions${NC}"
for script in codex-exec.sh codex-status.sh test-codex.sh; do
    if [ -x "$SKILL_DIR/scripts/$script" ]; then
        test_pass "Script '$script' is executable"
    else
        test_fail "Script '$script' is not executable"
    fi
done

# Test 4: Check Python script syntax
echo -e "\n${YELLOW}Test 4: Python Syntax${NC}"
if python3 -m py_compile "$SKILL_DIR/scripts/codex-session.py" 2>/dev/null; then
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
for ref in codex-cli.md agents-md-format.md subagent-patterns.md; do
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
if grep -q 'full-auto.*read-only' "$SKILL_DIR/scripts/codex-exec.sh"; then
    test_pass "Researcher guards against --full-auto"
else
    test_fail "Researcher missing --full-auto guard"
fi
# Verify Exa codex-agent-guide exists for web search
EXA_GUIDE="$HOME/.claude/skills/exa-search/codex-agent-guide.md"
if [ -f "$EXA_GUIDE" ]; then
    test_pass "Exa codex-agent-guide.md exists"
else
    test_fail "Exa codex-agent-guide.md missing"
fi

# Test 8: Quick API test (optional, skipped in quick mode)
if [ "$QUICK_MODE" = false ]; then
    echo -e "\n${YELLOW}Test 8: API Connectivity${NC}"
    if [ -n "$OPENAI_API_KEY" ]; then
        if timeout 15 codex exec --model gpt-5.1-codex-mini "print('hello')" &> /dev/null; then
            test_pass "Codex API connection works"
        else
            test_fail "Codex API connection failed"
        fi
    else
        echo -e "${YELLOW}⚠ SKIP${NC}: OPENAI_API_KEY not set"
    fi
else
    echo -e "\n${YELLOW}Test 8: API Connectivity${NC}"
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
