"""
Test runner for browser automation module tests.

This script runs all unit tests for the browser automation modules
and generates coverage reports.
"""

import unittest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

def discover_and_run_tests(test_type="all"):
    """Discover and run tests in the tests directory."""

    # Get the tests directory
    tests_dir = Path(__file__).parent

    # Define test patterns based on type
    test_patterns = {
        "unit": "test_*.py",
        "integration": "test_integration.py",
        "e2e": "test_end_to_end.py",
        "compatibility": "test_compatibility.py",
        "all": "test_*.py"
    }

    # Get the appropriate pattern
    pattern = test_patterns.get(test_type, "test_*.py")

    # Discover test files
    loader = unittest.TestLoader()

    if test_type == "all":
        # Run all tests
        suite = loader.discover(
            start_dir=str(tests_dir),
            pattern=pattern,
            top_level_dir=str(tests_dir)
        )
    else:
        # Run specific test type
        if test_type == "unit":
            # Load unit tests (exclude integration, e2e, compatibility)
            unit_files = [
                "test_playwright_browser_driver.py",
                "test_dom_page_analyzer.py",
                "test_universal_paginator.py",
                "test_config_manager.py",
                "test_logger_system.py"
            ]
            suite = unittest.TestSuite()
            for test_file in unit_files:
                test_path = tests_dir / test_file
                if test_path.exists():
                    module_suite = loader.discover(
                        start_dir=str(tests_dir),
                        pattern=test_file,
                        top_level_dir=str(tests_dir)
                    )
                    suite.addTest(module_suite)
        else:
            # Load specific test file
            suite = loader.discover(
                start_dir=str(tests_dir),
                pattern=pattern,
                top_level_dir=str(tests_dir)
            )

    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )

    test_type_display = test_type.upper() if test_type != "all" else "ALL"
    print("=" * 70)
    print(f"Running Browser Automation Module {test_type_display} Tests")
    print("=" * 70)

    result = runner.run(suite)

    # Print detailed summary
    print("\n" + "=" * 70)
    print(f"{test_type_display} TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    if result.failures:
        print(f"\nFAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"  - {test}")

    if result.errors:
        print(f"\nERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"  - {test}")

    if result.testsRun > 0:
        success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
        print(f"\nSuccess Rate: {success_rate:.1f}%")
    else:
        print(f"\nNo tests found for pattern: {pattern}")
    
    return result.wasSuccessful()

def run_coverage_analysis(test_type="all"):
    """Run tests with coverage analysis if coverage.py is available."""
    try:
        import coverage

        # Initialize coverage
        cov = coverage.Coverage(
            source=['src_new/rpa/browser/implementations'],
            omit=[
                '*/tests/*',
                '*/test_*',
                '*/__pycache__/*'
            ]
        )

        print(f"Running {test_type} tests with coverage analysis...")
        cov.start()

        # Run tests
        success = discover_and_run_tests(test_type)

        # Stop coverage and generate report
        cov.stop()
        cov.save()

        print("\n" + "=" * 70)
        print(f"COVERAGE REPORT - {test_type.upper()}")
        print("=" * 70)

        # Print coverage report to console
        cov.report(show_missing=True)

        # Generate HTML report if possible
        try:
            html_dir = Path(__file__).parent / f'coverage_html_{test_type}'
            cov.html_report(directory=str(html_dir))
            print(f"\nHTML coverage report generated: {html_dir}/index.html")
        except Exception as e:
            print(f"Could not generate HTML report: {e}")

        return success

    except ImportError:
        print("Coverage.py not available. Running tests without coverage analysis.")
        print("Install with: pip install coverage")
        return discover_and_run_tests(test_type)

def main():
    """Main entry point."""
    print("Browser Automation Module Test Suite")
    print("====================================")
    
    # Parse command line arguments
    test_type = "all"  # default
    run_with_coverage = False

    for arg in sys.argv[1:]:
        if arg in ['--coverage', '-c']:
            run_with_coverage = True
        elif arg in ['--unit', '-u']:
            test_type = "unit"
        elif arg in ['--integration', '-i']:
            test_type = "integration"
        elif arg in ['--e2e', '-e']:
            test_type = "e2e"
        elif arg in ['--compatibility', '--compat']:
            test_type = "compatibility"
        elif arg in ['--all', '-a']:
            test_type = "all"
        elif arg in ['--help', '-h']:
            print_help()
            sys.exit(0)

    print(f"Running {test_type.upper()} tests...")
    if run_with_coverage:
        print("Coverage analysis enabled")

    if run_with_coverage:
        success = run_coverage_analysis(test_type)
    else:
        success = discover_and_run_tests(test_type)

    if success:
        print(f"\n✅ All {test_type} tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ Some {test_type} tests failed!")
        sys.exit(1)

def print_help():
    """Print help information."""
    help_text = """
Browser Automation Module Test Suite

Usage: python run_tests.py [OPTIONS]

Options:
  -h, --help           Show this help message and exit
  -c, --coverage       Run tests with coverage analysis
  -u, --unit           Run only unit tests
  -i, --integration    Run only integration tests
  -e, --e2e            Run only end-to-end tests
  --compatibility      Run only compatibility tests
  --compat             Alias for --compatibility
  -a, --all            Run all tests (default)

Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --unit             # Run only unit tests
  python run_tests.py --integration -c   # Run integration tests with coverage
  python run_tests.py --e2e              # Run only end-to-end tests
  python run_tests.py --coverage         # Run all tests with coverage

Test Types:
  unit         - Individual module tests (fastest)
  integration  - Module interaction tests
  e2e          - Complete workflow tests
  compatibility- Legacy system compatibility tests
  all          - All test types
"""
    print(help_text)

if __name__ == '__main__':
    main()