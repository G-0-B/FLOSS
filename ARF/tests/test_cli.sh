#!/bin/bash
#
# ARF CLI Integration Tests
#
# Tests all CLI commands to ensure they work correctly.
# Follows Unix conventions: exit 0 on success, non-zero on failure.
#
# Usage:
#     bash tests/test_cli.sh
#     bash tests/test_cli.sh --verbose
#
# Requirements:
#     - ARF CLI installed (pip install -e .)
#     - jq for JSON parsing

set -e  # Exit on error

VERBOSE=false
if [[ "$1" == "--verbose" ]]; then
    VERBOSE=true
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
log() {
    if $VERBOSE; then
        echo -e "${GREEN}[INFO]${NC} $1"
    fi
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

fail() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Test helper
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_exit="$3"  # Expected exit code (default: 0)

    TESTS_RUN=$((TESTS_RUN + 1))

    log "Running test: $test_name"
    log "Command: $test_command"

    if eval "$test_command" > /dev/null 2>&1; then
        actual_exit=0
    else
        actual_exit=$?
    fi

    if [[ $actual_exit -eq ${expected_exit:-0} ]]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        success "$test_name"
        return 0
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        fail "$test_name (exit code: $actual_exit, expected: ${expected_exit:-0})"
        return 1
    fi
}

# Check if arf command exists
if ! command -v arf &> /dev/null; then
    error "arf command not found. Install with: pip install -e ."
    exit 1
fi

# Check if jq exists
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}[WARN]${NC} jq not found. Skipping JSON parsing tests."
    HAS_JQ=false
else
    HAS_JQ=true
fi

echo "======================================"
echo "ARF CLI Integration Tests"
echo "======================================"
echo ""

# ==============================
# Basic CLI Tests
# ==============================

echo "Testing basic CLI functionality..."

run_test "arf --help" "arf --help"
run_test "arf version" "arf version"
run_test "arf info" "arf info"

# ==============================
# Memory Tests
# ==============================

echo ""
echo "Testing memory commands..."

# Create test agent ID
TEST_AGENT="test_cli_agent_$$"

# Clean up old test data
rm -rf "./memory/$TEST_AGENT" 2>/dev/null || true

run_test "memory transmit" \
    "arf memory transmit 'Test understanding' --agent $TEST_AGENT --skip-validation"

run_test "memory transmit with context" \
    "arf memory transmit 'GPT-4 is a large language model' --agent $TEST_AGENT --context 'Testing' --skip-validation"

run_test "memory recall" \
    "arf memory recall 'test' --agent $TEST_AGENT"

run_test "memory stats" \
    "arf memory stats --agent $TEST_AGENT"

run_test "memory export" \
    "arf memory export --agent $TEST_AGENT"

# JSON output tests
if $HAS_JQ; then
    run_test "memory transmit --json" \
        "arf memory transmit 'JSON test' --agent $TEST_AGENT --json --skip-validation | jq -e '.success == true'"

    run_test "memory recall --json" \
        "arf memory recall 'test' --agent $TEST_AGENT --json | jq -e '.success == true'"

    run_test "memory stats --json" \
        "arf memory stats --agent $TEST_AGENT --json | jq -e '.success == true'"
fi

# ==============================
# Ontology Tests
# ==============================

echo ""
echo "Testing ontology commands..."

run_test "ontology validate (valid triple)" \
    "arf ontology validate '(GPT-4, is_a, LLM)'"

run_test "ontology validate (invalid predicate)" \
    "arf ontology validate '(GPT-4, ate, sandwich)'" 1

run_test "ontology list-predicates" \
    "arf ontology list-predicates"

run_test "ontology info" \
    "arf ontology info"

# JSON output tests
if $HAS_JQ; then
    run_test "ontology validate --json (valid)" \
        "arf ontology validate '(GPT-4, is_a, LLM)' --json | jq -e '.valid == true'"

    run_test "ontology list-predicates --json" \
        "arf ontology list-predicates --json | jq -e '.predicates | length > 0'"
fi

# ==============================
# Swarm Tests (if available)
# ==============================

echo ""
echo "Testing swarm commands..."

run_test "swarm info" \
    "arf swarm info"

# Note: Actual swarm query tests skipped in CI (too slow)
# They should be run manually or in dedicated performance tests

# ==============================
# Benchmark Tests
# ==============================

echo ""
echo "Testing benchmark commands..."

run_test "benchmark list-suites" \
    "arf benchmark list-suites"

run_test "benchmark memory (quick)" \
    "arf benchmark run --suite memory --iterations 3"

# JSON output tests
if $HAS_JQ; then
    run_test "benchmark --json" \
        "arf benchmark run --suite memory --iterations 2 --json | jq -e '.success == true'"
fi

# ==============================
# Cleanup
# ==============================

# Clean up test data
rm -rf "./memory/$TEST_AGENT" 2>/dev/null || true

# ==============================
# Summary
# ==============================

echo ""
echo "======================================"
echo "Test Summary"
echo "======================================"
echo "Total tests run: $TESTS_RUN"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
if [[ $TESTS_FAILED -gt 0 ]]; then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
fi
echo "======================================"

# Exit with appropriate code
if [[ $TESTS_FAILED -gt 0 ]]; then
    exit 1
else
    exit 0
fi
