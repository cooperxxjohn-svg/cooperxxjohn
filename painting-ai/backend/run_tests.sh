#!/bin/bash
# Test runner script for Painting.ai backend integration tests

set -e

echo "=========================================="
echo "Painting.ai API Integration Test Suite"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}Error: pytest is not installed${NC}"
    echo "Install with: pip install pytest pytest-asyncio httpx"
    exit 1
fi

# Parse command line arguments
TEST_PATH="tests/"
VERBOSE="-v"
COVERAGE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --auth)
            TEST_PATH="tests/test_api_auth.py"
            shift
            ;;
        --projects)
            TEST_PATH="tests/test_api_projects.py"
            shift
            ;;
        --rooms)
            TEST_PATH="tests/test_api_rooms.py"
            shift
            ;;
        --upload)
            TEST_PATH="tests/test_api_upload.py"
            shift
            ;;
        --exports)
            TEST_PATH="tests/test_api_exports.py"
            shift
            ;;
        --public)
            TEST_PATH="tests/test_api_public.py"
            shift
            ;;
        --settings)
            TEST_PATH="tests/test_api_settings.py"
            shift
            ;;
        --coverage)
            COVERAGE="--cov=. --cov-report=html --cov-report=term"
            shift
            ;;
        --quiet)
            VERBOSE=""
            shift
            ;;
        --help)
            echo "Usage: ./run_tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --auth         Run only authentication tests"
            echo "  --projects     Run only project tests"
            echo "  --rooms        Run only room tests"
            echo "  --upload       Run only upload tests"
            echo "  --exports      Run only export tests"
            echo "  --public       Run only public API tests"
            echo "  --settings     Run only settings tests"
            echo "  --coverage     Generate coverage report"
            echo "  --quiet        Run with minimal output"
            echo "  --help         Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_tests.sh                    # Run all tests"
            echo "  ./run_tests.sh --auth             # Run only auth tests"
            echo "  ./run_tests.sh --coverage         # Run with coverage"
            echo "  ./run_tests.sh --projects --quiet # Run project tests quietly"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${YELLOW}Running tests from: ${TEST_PATH}${NC}"
echo ""

# Run pytest
pytest $TEST_PATH $VERBOSE $COVERAGE

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}=========================================="
    echo "✓ All tests passed!"
    echo -e "==========================================${NC}"
else
    echo ""
    echo -e "${RED}=========================================="
    echo "✗ Some tests failed"
    echo -e "==========================================${NC}"
    exit 1
fi

# Show coverage report location if generated
if [ ! -z "$COVERAGE" ]; then
    echo ""
    echo -e "${GREEN}Coverage report generated: htmlcov/index.html${NC}"
fi
