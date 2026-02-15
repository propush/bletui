#!/usr/bin/env bash
# Convenient test runner for BLE TUI App
# Handles venv setup, dependency installation, and test execution

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}BLE TUI App Test Runner${NC}"
echo "======================================"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Install/upgrade dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q -r requirements-dev.txt

# Load test environment if .env.test exists
if [ -f ".env.test" ]; then
    echo -e "${YELLOW}Loading test configuration from .env.test${NC}"
    export $(cat .env.test | grep -v '^#' | xargs)
fi

# Parse command line arguments
TEST_TYPE="${1:-all}"
EXTRA_ARGS="${@:2}"

echo "======================================"
echo -e "${GREEN}Running tests: ${TEST_TYPE}${NC}"
echo "======================================"

case "$TEST_TYPE" in
    unit)
        echo "Running unit tests only..."
        pytest tests/test_unit.py -m unit -v $EXTRA_ARGS
        ;;
    integration)
        echo "Running integration tests only..."
        pytest tests/test_integration_*.py -v $EXTRA_ARGS
        ;;
    integration-tui)
        echo "Running TUI integration tests only..."
        pytest tests/test_integration_tui.py -m integration_tui -v $EXTRA_ARGS
        ;;
    integration-ble)
        echo "Running BLE integration tests only..."
        pytest tests/test_integration_ble.py -m integration_ble -v $EXTRA_ARGS
        ;;
    e2e)
        echo "Running E2E tests only..."
        if [ "$BLE_RUN_E2E_TESTS" != "true" ]; then
            echo -e "${YELLOW}Warning: BLE_RUN_E2E_TESTS is not set to 'true'${NC}"
            echo -e "${YELLOW}E2E tests will be skipped. Set BLE_RUN_E2E_TESTS=true to enable.${NC}"
        fi
        pytest tests/test_e2e.py -m e2e -v $EXTRA_ARGS
        ;;
    fast)
        echo "Running fast tests (unit + integration, no E2E)..."
        pytest tests/ -m "not e2e and not slow" -v $EXTRA_ARGS
        ;;
    cov|coverage)
        echo "Running all tests with coverage..."
        pytest tests/ --cov=ble_tui --cov-report=html --cov-report=term -v $EXTRA_ARGS
        echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
        ;;
    all)
        echo "Running all tests..."
        pytest tests/ -v $EXTRA_ARGS
        ;;
    *)
        # Assume it's a specific test file or path
        echo "Running specific test: $TEST_TYPE"
        pytest "$TEST_TYPE" -v $EXTRA_ARGS
        ;;
esac

TEST_EXIT_CODE=$?

echo "======================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Tests passed!${NC}"
else
    echo -e "${RED}✗ Tests failed!${NC}"
fi
echo "======================================"

exit $TEST_EXIT_CODE
