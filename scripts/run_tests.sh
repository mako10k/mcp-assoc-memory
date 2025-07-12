#!/bin/bash
# Test runner script for MCP Associative Memory project

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_OUTPUT_DIR="${PROJECT_ROOT}/.copilot-temp"
COVERAGE_DIR="${PROJECT_ROOT}/htmlcov"

# Ensure output directories exist
mkdir -p "${TEST_OUTPUT_DIR}"
mkdir -p "${COVERAGE_DIR}"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to run tests with specific markers
run_test_category() {
    local category="$1"
    local description="$2"
    local extra_args="${3:-}"
    
    print_status "Running $description..."
    
    if pytest -m "$category" $extra_args --tb=short > "${TEST_OUTPUT_DIR}/test-${category}.log" 2>&1; then
        print_success "$description completed successfully"
        return 0
    else
        print_error "$description failed"
        echo "Log file: ${TEST_OUTPUT_DIR}/test-${category}.log"
        return 1
    fi
}

# Function to generate coverage report
generate_coverage_report() {
    print_status "Generating coverage report..."
    
    if coverage html -d "${COVERAGE_DIR}" > "${TEST_OUTPUT_DIR}/coverage.log" 2>&1; then
        print_success "Coverage report generated in ${COVERAGE_DIR}"
        coverage report --show-missing
    else
        print_warning "Coverage report generation failed"
    fi
}

# Function to run all tests
run_all_tests() {
    print_status "Running complete test suite..."
    
    local failed_categories=()
    
    # Unit tests (fast)
    if ! run_test_category "unit" "Unit tests" "--maxfail=10"; then
        failed_categories+=("unit")
    fi
    
    # Integration tests
    if ! run_test_category "integration" "Integration tests" "--maxfail=5"; then
        failed_categories+=("integration")
    fi
    
    # E2E tests (slower)
    if ! run_test_category "e2e and not slow" "End-to-end tests (fast)" "--maxfail=3"; then
        failed_categories+=("e2e-fast")
    fi
    
    # Generate coverage report
    generate_coverage_report
    
    # Summary
    if [ ${#failed_categories[@]} -eq 0 ]; then
        print_success "All test categories passed!"
        return 0
    else
        print_error "Failed categories: ${failed_categories[*]}"
        return 1
    fi
}

# Function to run quick tests (unit only)
run_quick_tests() {
    print_status "Running quick test suite (unit tests only)..."
    
    if run_test_category "unit" "Unit tests" "--maxfail=10 --tb=line"; then
        print_success "Quick tests passed!"
        return 0
    else
        print_error "Quick tests failed!"
        return 1
    fi
}

# Function to run slow tests
run_slow_tests() {
    print_status "Running slow test suite..."
    
    local failed_categories=()
    
    # Slow E2E tests
    if ! run_test_category "e2e and slow" "Slow end-to-end tests" "--maxfail=2"; then
        failed_categories+=("e2e-slow")
    fi
    
    # Performance tests
    if ! run_test_category "performance" "Performance tests" "--maxfail=2"; then
        failed_categories+=("performance")
    fi
    
    if [ ${#failed_categories[@]} -eq 0 ]; then
        print_success "All slow tests passed!"
        return 0
    else
        print_error "Failed slow test categories: ${failed_categories[*]}"
        return 1
    fi
}

# Function to run specific test file
run_specific_test() {
    local test_file="$1"
    
    if [ ! -f "$test_file" ]; then
        print_error "Test file not found: $test_file"
        return 1
    fi
    
    print_status "Running specific test: $test_file"
    
    if pytest "$test_file" -v --tb=short > "${TEST_OUTPUT_DIR}/test-specific.log" 2>&1; then
        print_success "Test file completed successfully"
        cat "${TEST_OUTPUT_DIR}/test-specific.log"
        return 0
    else
        print_error "Test file failed"
        cat "${TEST_OUTPUT_DIR}/test-specific.log"
        return 1
    fi
}

# Function to check test setup
check_test_setup() {
    print_status "Checking test setup..."
    
    # Check Python environment
    if ! python -c "import pytest, pytest_asyncio, pytest_cov, pytest_mock" 2>/dev/null; then
        print_error "Test dependencies not installed. Run: pip install -e '.[test]'"
        return 1
    fi
    
    # Check test discovery
    local test_count=$(pytest --collect-only -q 2>/dev/null | grep -c "test session starts" || echo "0")
    if [ "$test_count" -eq 0 ]; then
        print_warning "No tests discovered"
        return 1
    fi
    
    print_success "Test setup looks good"
    return 0
}

# Function to clean test artifacts
clean_test_artifacts() {
    print_status "Cleaning test artifacts..."
    
    # Remove test databases and logs
    find "${PROJECT_ROOT}" -name "test_*.db" -delete 2>/dev/null || true
    find "${PROJECT_ROOT}" -name "*.log" -path "*/test*" -delete 2>/dev/null || true
    
    # Remove coverage files
    rm -rf "${PROJECT_ROOT}/.coverage" 2>/dev/null || true
    rm -rf "${COVERAGE_DIR}" 2>/dev/null || true
    
    # Remove pytest cache
    rm -rf "${PROJECT_ROOT}/.pytest_cache" 2>/dev/null || true
    
    # Remove temp test files
    rm -rf "${PROJECT_ROOT}/tests/temp_*" 2>/dev/null || true
    
    print_success "Test artifacts cleaned"
}

# Function to show help
show_help() {
    cat << EOF
Usage: $0 [COMMAND]

Commands:
    all         Run all tests (unit, integration, e2e)
    quick       Run quick tests (unit only)  
    slow        Run slow tests (e2e, performance)
    unit        Run unit tests only
    integration Run integration tests only
    e2e         Run end-to-end tests only
    performance Run performance tests only
    file <path> Run specific test file
    setup       Check test setup
    clean       Clean test artifacts
    help        Show this help message

Examples:
    $0 quick                               # Run unit tests only
    $0 all                                # Run complete test suite
    $0 file tests/unit/test_memory.py     # Run specific test file
    $0 clean                              # Clean up test artifacts

EOF
}

# Main script logic
main() {
    cd "$PROJECT_ROOT"
    
    case "${1:-help}" in
        "all")
            check_test_setup && run_all_tests
            ;;
        "quick")
            check_test_setup && run_quick_tests
            ;;
        "slow")
            check_test_setup && run_slow_tests
            ;;
        "unit")
            check_test_setup && run_test_category "unit" "Unit tests" "--maxfail=10"
            ;;
        "integration")
            check_test_setup && run_test_category "integration" "Integration tests" "--maxfail=5"
            ;;
        "e2e")
            check_test_setup && run_test_category "e2e" "End-to-end tests" "--maxfail=3"
            ;;
        "performance")
            check_test_setup && run_test_category "performance" "Performance tests" "--maxfail=2"
            ;;
        "file")
            if [ -z "$2" ]; then
                print_error "Please specify a test file"
                show_help
                exit 1
            fi
            check_test_setup && run_specific_test "$2"
            ;;
        "setup")
            check_test_setup
            ;;
        "clean")
            clean_test_artifacts
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"
