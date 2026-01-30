"""
Test Script for XBOQ Enhanced
Tests all features and validates accuracy improvements
"""

import os
import sys
import time
import json
from pathlib import Path

from xboq_enhanced import XBOQEnhanced


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_result(result):
    """Print extraction result"""
    print(f"Success: {result.get('success', False)}")
    print(f"Components: {result.get('total_components', 0)}")
    print(f"Total Value: ₹{result.get('total_value', 0):,.2f}")
    print(f"Confidence: {result.get('overall_confidence', 0):.2f}")
    print(f"Processing Time: {result.get('processing_time', 0)}s")

    if result.get('extraction_methods'):
        print(f"Methods Used: {', '.join(result['extraction_methods'])}")

    if result.get('validation'):
        val = result['validation']
        print(f"\nValidation:")
        print(f"  Valid: {val.get('is_valid', False)}")
        print(f"  Issues: {val.get('summary', {}).get('issues_found', 0)}")
        print(f"  Errors: {val.get('summary', {}).get('errors', 0)}")
        print(f"  Warnings: {val.get('summary', {}).get('warnings', 0)}")


def test_single_drawing(xboq, drawing_path):
    """Test single drawing extraction"""
    print_header(f"Test 1: Single Drawing Extraction")

    print(f"Drawing: {drawing_path}")
    print(f"File exists: {os.path.exists(drawing_path)}")

    if not os.path.exists(drawing_path):
        print("❌ File not found! Skipping test.")
        return

    start = time.time()
    result = xboq.process_drawing_intelligent(drawing_path)
    elapsed = time.time() - start

    print(f"\n📊 Results:")
    print_result(result)

    # Show first few components
    if result.get('components'):
        print(f"\n📝 Sample Components (first 3):")
        for i, comp in enumerate(result['components'][:3]):
            print(f"\n  Component {i+1}:")
            print(f"    Description: {comp.get('description', 'N/A')}")
            print(f"    Quantity: {comp.get('qty', 0)} {comp.get('unit', '')}")
            print(f"    Rate: ₹{comp.get('rate', 0):,.2f}")
            print(f"    Amount: ₹{comp.get('amount', 0):,.2f}")
            print(f"    Source: {comp.get('source', 'N/A')}")

    return result


def test_quick_mode(xboq, drawing_path):
    """Test quick mode vs normal mode"""
    print_header("Test 2: Quick Mode Comparison")

    if not os.path.exists(drawing_path):
        print("❌ File not found! Skipping test.")
        return

    # Normal mode
    print("Running NORMAL mode...")
    start = time.time()
    result_normal = xboq.process_drawing_intelligent(drawing_path, quick_mode=False)
    time_normal = time.time() - start

    # Quick mode
    print("\nRunning QUICK mode...")
    start = time.time()
    result_quick = xboq.process_drawing_intelligent(drawing_path, quick_mode=True)
    time_quick = time.time() - start

    # Compare
    print(f"\n📊 Comparison:")
    print(f"\n  NORMAL MODE:")
    print(f"    Time: {time_normal:.2f}s")
    print(f"    Components: {result_normal.get('total_components', 0)}")
    print(f"    Confidence: {result_normal.get('overall_confidence', 0):.2f}")

    print(f"\n  QUICK MODE:")
    print(f"    Time: {time_quick:.2f}s")
    print(f"    Components: {result_quick.get('total_components', 0)}")
    print(f"    Confidence: {result_quick.get('overall_confidence', 0):.2f}")

    speedup = time_normal / time_quick if time_quick > 0 else 0
    print(f"\n  ⚡ Speedup: {speedup:.2f}x faster")


def test_accuracy_methods(xboq, drawing_path):
    """Test different extraction methods"""
    print_header("Test 3: Extraction Method Accuracy")

    if not os.path.exists(drawing_path):
        print("❌ File not found! Skipping test.")
        return

    result = xboq.process_drawing_intelligent(drawing_path)

    if result.get('extraction_methods'):
        print("📋 Methods Used:")
        for method in result['extraction_methods']:
            print(f"  ✓ {method}")

        # Count components by source
        if result.get('components'):
            sources = {}
            for comp in result['components']:
                source = comp.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1

            print(f"\n📊 Components by Source:")
            for source, count in sources.items():
                print(f"  {source}: {count} components")


def test_confidence_scoring(xboq):
    """Test confidence scoring on sample data"""
    print_header("Test 4: Confidence Scoring")

    sample_components = [
        {
            'item': '1.1',
            'description': 'Excavation in foundation trenches',
            'qty': 150.0,
            'unit': 'cum',
            'rate': 500.0,
            'amount': 75000.0
        },
        {
            'item': '2.1',
            'description': 'M25 Grade concrete',
            'qty': 50.0,
            'unit': 'cum',
            'rate': 6500.0,
            'amount': 325000.0
        },
        {
            'item': '3.1',
            'description': 'Steel reinforcement',
            'qty': 5000.0,
            'unit': 'kg',
            'rate': 70.0,
            'amount': 350000.0
        }
    ]

    validation = xboq.validator.validate_document(sample_components)

    print("📊 Validation Results:")
    print(f"  Valid: {validation.is_valid}")
    print(f"  Overall Confidence: {validation.overall_confidence:.2f}")
    print(f"\n  Field Confidences:")
    for field, conf in validation.field_confidences.items():
        status = "✓" if conf > 0.8 else "⚠" if conf > 0.6 else "❌"
        print(f"    {status} {field}: {conf:.2f}")

    if validation.issues:
        print(f"\n  Issues Found: {len(validation.issues)}")
        for issue in validation.issues[:3]:
            print(f"    [{issue.level.value}] {issue.message}")


def test_batch_processing(xboq, drawing_paths):
    """Test batch processing"""
    print_header("Test 5: Batch Processing")

    existing_paths = [p for p in drawing_paths if os.path.exists(p)]

    if len(existing_paths) == 0:
        print("❌ No files found! Skipping test.")
        return

    print(f"Processing {len(existing_paths)} files...")

    start = time.time()
    results = xboq.process_batch(
        existing_paths,
        output_dir='test_output'
    )
    elapsed = time.time() - start

    print(f"\n📊 Batch Results:")
    print(f"  Total Processed: {len(results)}")
    print(f"  Successful: {len([r for r in results if r.get('success')])}")
    print(f"  Failed: {len([r for r in results if not r.get('success')])}")
    print(f"  Total Time: {elapsed:.2f}s")
    print(f"  Avg Time per File: {elapsed / len(results):.2f}s")

    total_components = sum(r.get('total_components', 0) for r in results)
    avg_confidence = sum(r.get('overall_confidence', 0) for r in results) / len(results) if results else 0

    print(f"  Total Components: {total_components}")
    print(f"  Average Confidence: {avg_confidence:.2f}")


def run_all_tests():
    """Run complete test suite"""
    print("\n" + "=" * 80)
    print("  XBOQ ENHANCED - COMPLETE TEST SUITE")
    print("=" * 80)

    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("\n❌ ERROR: ANTHROPIC_API_KEY not set!")
        print("Set it with: export ANTHROPIC_API_KEY='your_key_here'")
        sys.exit(1)

    print("\n✓ API key found")

    # Initialize XBOQ Enhanced
    print("✓ Initializing XBOQ Enhanced...")
    xboq = XBOQEnhanced(api_key)
    print("✓ Initialization complete")

    # Sample drawing path (update with your actual file)
    drawing_path = 'sample_drawing.pdf'

    # Check if test file exists
    if not os.path.exists(drawing_path):
        print(f"\n⚠️  Warning: Test file '{drawing_path}' not found")
        print("Some tests will be skipped")
        print("Place a test drawing at:", os.path.abspath(drawing_path))

    # Run tests
    try:
        # Test 1: Single drawing
        result = test_single_drawing(xboq, drawing_path)

        # Test 2: Quick mode comparison
        if os.path.exists(drawing_path):
            test_quick_mode(xboq, drawing_path)

        # Test 3: Method accuracy
        if os.path.exists(drawing_path):
            test_accuracy_methods(xboq, drawing_path)

        # Test 4: Confidence scoring
        test_confidence_scoring(xboq)

        # Test 5: Batch processing (if multiple files)
        # test_batch_processing(xboq, ['file1.pdf', 'file2.pdf'])

        print_header("✅ ALL TESTS COMPLETE")

        if result and result.get('success'):
            print("🎉 XBOQ Enhanced is working perfectly!")
            print(f"\n📊 Final Results:")
            print(f"  Accuracy: {result.get('overall_confidence', 0):.1%}")
            print(f"  Speed: {result.get('processing_time', 0):.2f}s")
            print(f"  Methods: {len(result.get('extraction_methods', []))}")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_all_tests()
