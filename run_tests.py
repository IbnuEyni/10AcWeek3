#!/usr/bin/env python3
"""
Professional Test Runner
Runs tests with proper reporting and organization
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run command and report results"""
    print(f"\n{'='*80}")
    print(f"  {description}")
    print('='*80)
    result = subprocess.run(cmd, shell=True, capture_output=False)
    return result.returncode == 0


def main():
    """Run test suite professionally"""
    
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║              DOCUMENT INTELLIGENCE REFINERY - TEST SUITE                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")
    
    # Check if we're in the right directory
    if not Path("tests").exists():
        print("❌ Error: Must run from project root directory")
        sys.exit(1)
    
    results = {}
    
    # 1. Unit Tests
    results['unit'] = run_command(
        "pytest tests/unit/ -v --tb=short",
        "UNIT TESTS (63 tests)"
    )
    
    # 2. Integration Tests
    results['integration'] = run_command(
        "pytest tests/integration/ -v --tb=short",
        "INTEGRATION TESTS (8 tests)"
    )
    
    # 3. Coverage Report
    results['coverage'] = run_command(
        "pytest tests/ --cov=src --cov-report=term-missing --cov-report=html -q",
        "COVERAGE REPORT"
    )
    
    # Summary
    print(f"\n{'='*80}")
    print("  TEST SUMMARY")
    print('='*80)
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    for test_type, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_type.upper():20} {status}")
    
    print(f"\n  Total: {total_passed}/{total_tests} test suites passed")
    
    if all(results.values()):
        print(f"\n{'='*80}")
        print("  ✅ ALL TESTS PASSED!")
        print('='*80)
        print("\n  📊 Coverage report: htmlcov/index.html")
        print("  📁 Test artifacts: .pytest_cache/")
        return 0
    else:
        print(f"\n{'='*80}")
        print("  ❌ SOME TESTS FAILED")
        print('='*80)
        return 1


if __name__ == "__main__":
    sys.exit(main())
