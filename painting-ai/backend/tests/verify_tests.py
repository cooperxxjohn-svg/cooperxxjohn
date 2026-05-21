#!/usr/bin/env python
"""
Test Verification Script
Verifies that all test files are properly structured and importable
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

print("=" * 80)
print("PAINTING.AI BACKEND TEST VERIFICATION")
print("=" * 80)
print()

# List of core test files
test_files = [
    'test_auth.py',
    'test_calculations.py',
    'test_materials.py',
    'test_models.py'
]

success_count = 0
total_count = len(test_files)

for test_file in test_files:
    test_path = Path(__file__).parent / test_file

    if not test_path.exists():
        print(f"❌ {test_file:30} NOT FOUND")
        continue

    # Check file size
    file_size = test_path.stat().st_size
    if file_size < 1000:
        print(f"⚠️  {test_file:30} Too small ({file_size} bytes)")
        continue

    # Try to import the module
    try:
        module_name = test_file.replace('.py', '')
        test_module = __import__(f'tests.{module_name}', fromlist=[module_name])
        print(f"✅ {test_file:30} {file_size:6,} bytes - Importable")
        success_count += 1
    except Exception as e:
        print(f"❌ {test_file:30} Import error: {str(e)[:40]}")

print()
print("-" * 80)
print(f"Verification Results: {success_count}/{total_count} test files valid")
print("-" * 80)
print()

# Check for pytest configuration
if Path('pytest.ini').exists():
    print("✅ pytest.ini configuration file present")
else:
    print("⚠️  pytest.ini configuration file missing")

# Check for conftest
if (Path(__file__).parent / 'conftest.py').exists():
    print("✅ conftest.py fixtures file present")
else:
    print("❌ conftest.py fixtures file missing")

# Check for __init__.py
if (Path(__file__).parent / '__init__.py').exists():
    print("✅ tests/__init__.py package file present")
else:
    print("⚠️  tests/__init__.py package file missing")

print()

# Quick functionality test
print("=" * 80)
print("QUICK FUNCTIONALITY TESTS")
print("=" * 80)
print()

try:
    from painting_detector import PaintCalculator, Surface
    calc = PaintCalculator()
    surface = Surface(type='wall', area=500.0, height=9.0, deductions=35.0)
    result = calc.calculate_paint(surface, num_coats=2)
    print(f"✅ PaintCalculator: {result['gallons_to_buy']} gallons for 500 sqft wall")
except Exception as e:
    print(f"❌ PaintCalculator error: {e}")

try:
    from materials import MaterialDatabase
    # Create temp database in memory location
    import tempfile
    temp_dir = tempfile.mkdtemp()
    db = MaterialDatabase(os.path.join(temp_dir, 'test_materials.json'))
    materials = db.search_materials("ProMar")
    print(f"✅ MaterialDatabase: Found {len(materials)} ProMar products")
except Exception as e:
    print(f"❌ MaterialDatabase error: {e}")

try:
    from models import User, Project, Room
    print(f"✅ SQLAlchemy Models: User, Project, Room imported")
except Exception as e:
    print(f"❌ Models import error: {e}")

print()
print("=" * 80)
print("TEST SUITE STATUS: {'READY ✅' if success_count == total_count else 'NEEDS ATTENTION ⚠️'}")
print("=" * 80)
print()
print("Next Steps:")
print("1. Install dependencies: pip install -r requirements.txt")
print("2. Run tests: pytest tests/ -v")
print("3. Check coverage: pytest tests/ --cov=. --cov-report=html")
print("4. View report: open htmlcov/index.html")
print()
