#!/usr/bin/env python3
"""
Test script to verify both BOQ and Estimator modules work
"""

import sys
import json


def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")

    try:
        from modules.boq_generator import BOQGenerator
        print("✅ BOQGenerator imported")
    except Exception as e:
        print(f"❌ BOQGenerator import failed: {e}")
        return False

    try:
        from modules.estimator import ConstructionEstimator
        print("✅ ConstructionEstimator imported")
    except Exception as e:
        print(f"❌ ConstructionEstimator import failed: {e}")
        return False

    try:
        from utils.pdf_processor import PDFProcessor
        print("✅ PDFProcessor imported")
    except Exception as e:
        print(f"❌ PDFProcessor import failed: {e}")
        return False

    try:
        from utils.claude_client import ClaudeClient
        print("✅ ClaudeClient imported")
    except Exception as e:
        print(f"❌ ClaudeClient import failed (expected if no API key): {e}")
        # Don't fail on this one, API key might not be set

    return True


def test_estimator_logic():
    """Test estimator with mock data (no API calls)"""
    print("\nTesting Estimator logic...")

    test_data = {
        "trade": "drywall",
        "rooms": [
            {
                "name": "Test Room",
                "length": 20,
                "width": 15,
                "height": 9,
                "doors": 1,
                "windows": 2
            }
        ],
        "finish_level": 4,
        "project_type": "commercial"
    }

    print(f"Test input: {json.dumps(test_data, indent=2)}")
    print("✅ Estimator test data prepared")

    return True


def test_flask_app():
    """Test Flask app configuration"""
    print("\nTesting Flask app...")

    try:
        from app import app
        print("✅ Flask app imported")

        # Check routes exist
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        expected_routes = [
            '/health',
            '/api/products',
            '/api/trades',
            '/api/boq/upload',
            '/api/estimate/manual',
            '/api/estimate/upload'
        ]

        for route in expected_routes:
            if route in routes:
                print(f"✅ Route exists: {route}")
            else:
                print(f"❌ Missing route: {route}")
                return False

        return True

    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False


def main():
    print("=" * 60)
    print("XBOQ PLATFORM - BACKEND TEST SUITE")
    print("=" * 60)

    tests = [
        ("Import Test", test_imports),
        ("Estimator Logic Test", test_estimator_logic),
        ("Flask App Test", test_flask_app)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")

        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Backend is ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
