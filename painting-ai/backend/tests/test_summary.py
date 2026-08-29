"""
Test Summary Script
Counts all test cases defined in the test suite
"""

import ast
import os
from pathlib import Path


def count_test_functions(file_path):
    """Count test functions in a file"""
    with open(file_path, 'r') as f:
        tree = ast.parse(f.read())

    test_count = 0
    test_names = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith('test_'):
                test_count += 1
                test_names.append(node.name)

    return test_count, test_names


def main():
    """Main function to analyze all test files"""
    tests_dir = Path(__file__).parent
    test_files = [
        'test_auth.py',
        'test_calculations.py',
        'test_materials.py',
        'test_models.py'
    ]

    print("=" * 80)
    print("PAINTING.AI BACKEND TEST SUITE SUMMARY")
    print("=" * 80)
    print()

    total_tests = 0
    file_details = []

    for test_file in test_files:
        file_path = tests_dir / test_file
        if file_path.exists():
            count, names = count_test_functions(file_path)
            total_tests += count
            file_details.append((test_file, count, names))
            print(f"📄 {test_file:30} {count:3} tests")
        else:
            print(f"⚠️  {test_file:30} NOT FOUND")

    print()
    print("-" * 80)
    print(f"{'TOTAL TESTS:':30} {total_tests:3} tests")
    print("-" * 80)
    print()

    # Print details for each file
    for file_name, count, names in file_details:
        print(f"\n{file_name} ({count} tests):")
        print("-" * 80)
        for name in names:
            print(f"  • {name}")

    print()
    print("=" * 80)
    print("TEST COVERAGE TARGETS:")
    print("=" * 80)
    print("✓ Auth System: Token generation, validation, registration, login")
    print("✓ Calculations: Paint coverage, labor hours, material costs, estimates")
    print("✓ Materials: Database operations, search, recommendations, supplies")
    print("✓ Models: SQLAlchemy models, validation, relationships, integrity")
    print()
    print(f"Target: 50+ tests  →  Actual: {total_tests} tests ({'✅ PASS' if total_tests >= 50 else '❌ FAIL'})")
    print("Target: 70%+ coverage  →  Run: pytest --cov")
    print()


if __name__ == '__main__':
    main()
