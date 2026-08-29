"""
Example Usage of Drywall Detector
Demonstrates how to use the AI-powered drywall detection system
"""

import os
import json
from drywall_detector import DrywallDetector, DrywallCalculator
from dataclasses import asdict


def example_basic_usage():
    """Basic usage: detect walls from floor plan and calculate estimate"""
    print("=" * 60)
    print("EXAMPLE 1: Basic Drywall Detection")
    print("=" * 60)

    # Initialize detector with API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY environment variable")
        return

    detector = DrywallDetector(api_key)
    calculator = DrywallCalculator(sheet_size="4x8")

    # Analyze a floor plan
    print("\n1. Analyzing floor plan...")
    image_path = "tests/fixtures/simple_residential.png"

    if not os.path.exists(image_path):
        print(f"ERROR: Sample image not found: {image_path}")
        print("Run: cd tests/fixtures && python generate_test_floorplans.py")
        return

    detection = detector.analyze_drawing(image_path)

    # Display detection results
    print(f"\nDrawing Type: {detection.drawing_type}")
    print(f"Scale: {detection.scale or 'Not detected'}")
    print(f"\nDetected {len(detection.walls)} walls and {len(detection.ceilings)} ceilings")

    print("\n--- WALLS ---")
    for wall in detection.walls:
        print(f"{wall.wall_id}: {wall.type} wall, {wall.length_ft}ft × {wall.height_ft}ft = {wall.square_footage} sqft")
        if wall.openings:
            print(f"  Openings: {len(wall.openings)} ({sum(o.quantity for o in wall.openings)} total)")
        print(f"  Corners: {wall.corners.inside_corners} inside, {wall.corners.outside_corners} outside")

    print("\n--- CEILINGS ---")
    for ceiling in detection.ceilings:
        print(f"{ceiling.room}: {ceiling.type} ceiling, {ceiling.square_footage} sqft at {ceiling.height_ft}ft")

    print("\n--- SUMMARY ---")
    for key, value in detection.summary.items():
        print(f"{key}: {value}")

    # Calculate estimate
    print("\n2. Calculating estimate...")
    estimate = calculator.calculate_estimate(
        detection,
        sheet_price=15.00,
        labor_rate=65.00,
        difficulty="standard",
        waste_factor=1.10
    )

    # Display estimate
    print("\n--- MATERIALS ---")
    materials = estimate["materials"]
    print(f"Drywall sheets (4x8): {estimate['material_details']['drywall_sheets']['quantity']} sheets (${materials['drywall_sheets']:,.2f})")
    print(f"Joint compound: {estimate['material_details']['joint_compound']['buckets_5gal']} buckets (${materials['joint_compound']:,.2f})")
    print(f"Tape: {estimate['material_details']['tape']['rolls']} rolls (${materials['tape']:,.2f})")
    print(f"Screws: {estimate['material_details']['screws']['pounds']} lbs (${materials['screws']:,.2f})")
    print(f"Corner bead: {estimate['material_details']['corner_bead']['pieces_10ft']} pieces (${materials['corner_bead']:,.2f})")
    print(f"Sundries: ${materials['sundries']:,.2f}")
    print(f"TOTAL MATERIALS: ${materials['total']:,.2f}")

    print("\n--- LABOR ---")
    labor = estimate["labor"]
    print(f"Hanging: {labor['breakdown']['hanging_hours']:.1f} hrs")
    print(f"Taping: {labor['breakdown']['taping_hours']:.1f} hrs")
    print(f"Finishing: {labor['breakdown']['finishing_hours']:.1f} hrs")
    print(f"Sanding: {labor['breakdown']['sanding_hours']:.1f} hrs")
    print(f"Corners: {labor['breakdown']['corner_hours']:.1f} hrs")
    print(f"TOTAL HOURS: {labor['hours']:.1f} hrs @ ${labor['rate']:.2f}/hr = ${labor['total']:,.2f}")

    print("\n--- PRICING ---")
    pricing = estimate["pricing"]
    print(f"Subtotal: ${pricing['subtotal']:,.2f}")
    print(f"Overhead (15%): ${pricing['overhead']:,.2f}")
    print(f"Profit (20%): ${pricing['profit']:,.2f}")
    print(f"=" * 40)
    print(f"TOTAL: ${pricing['total']:,.2f}")
    print(f"Price per sqft: ${pricing['price_per_sqft']:.2f}")
    print("=" * 40)

    # Validation notes
    if detection.notes:
        print("\n--- VALIDATION NOTES ---")
        for note in detection.notes:
            print(f"• {note}")


def example_compare_sheet_sizes():
    """Example: Compare different sheet sizes"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Comparing Sheet Sizes")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY environment variable")
        return

    # Create mock detection for comparison
    from drywall_detector import Wall, Ceiling, Corner, Opening, DrywallDetection

    walls = [
        Wall("W1", "exterior", 30.0, 9.0, 270.0, [Opening("door", 3.0, 6.67, 20.0, 1)], Corner(0, 2), []),
        Wall("W2", "interior", 20.0, 9.0, 180.0, [], Corner(2, 0), []),
    ]
    ceilings = [Ceiling("Office", "flat", 600.0, 9.0)]
    summary = {
        "total_wall_sqft_gross": 450.0,
        "total_wall_sqft_net": 430.0,
        "total_ceiling_sqft": 600.0,
        "total_drywall_sqft": 1030.0,
        "total_linear_ft": 50.0,
        "total_openings": 1,
        "total_opening_sqft": 20.0,
        "total_corners": 4,
        "inside_corners": 2,
        "outside_corners": 2
    }
    detection = DrywallDetection(walls, ceilings, summary, "floor_plan", "1/4\" = 1'-0\"", [])

    print(f"\nTotal drywall: {detection.summary['total_drywall_sqft']} sqft")
    print(f"\nComparing sheet sizes:\n")

    for sheet_size in ["4x8", "4x10", "4x12"]:
        calc = DrywallCalculator(sheet_size=sheet_size)
        materials = calc.calculate_materials(detection, waste_factor=1.10)

        sheets = materials["drywall_sheets"]["quantity"]
        sheet_cost = sheets * (15.00 if sheet_size == "4x8" else 18.00 if sheet_size == "4x10" else 22.00)

        print(f"{sheet_size}: {sheets} sheets @ ${sheet_cost:,.2f}")


def example_difficulty_comparison():
    """Example: Compare different difficulty levels"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Comparing Difficulty Levels")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY environment variable")
        return

    # Create mock detection
    from drywall_detector import Wall, Ceiling, Corner, DrywallDetection

    walls = [Wall("W1", "exterior", 30.0, 8.0, 240.0, [], Corner(0, 4), [])]
    ceilings = [Ceiling("Room", "flat", 600.0, 8.0)]
    summary = {
        "total_wall_sqft_gross": 240.0,
        "total_wall_sqft_net": 240.0,
        "total_ceiling_sqft": 600.0,
        "total_drywall_sqft": 840.0,
        "total_linear_ft": 30.0,
        "total_openings": 0,
        "total_opening_sqft": 0,
        "total_corners": 4,
        "inside_corners": 0,
        "outside_corners": 4
    }
    detection = DrywallDetection(walls, ceilings, summary, "floor_plan", None, [])

    calc = DrywallCalculator()

    print(f"\nTotal drywall: {detection.summary['total_drywall_sqft']} sqft")
    print(f"\nComparing difficulty levels:\n")

    for difficulty in ["easy", "standard", "difficult"]:
        labor = calc.calculate_labor(detection, difficulty=difficulty)
        labor_cost = labor["total_hours"] * 65.00

        print(f"{difficulty.capitalize():12} - {labor['total_hours']:5.1f} hrs @ $65/hr = ${labor_cost:7,.2f}")
        print(f"               (multiplier: {labor['difficulty_multiplier']}×)")


def example_export_json():
    """Example: Export detection results to JSON"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Export to JSON")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: Set ANTHROPIC_API_KEY environment variable")
        return

    # Create simple mock detection
    from drywall_detector import Wall, Ceiling, Corner, Opening, DrywallDetection

    walls = [
        Wall("W1", "exterior", 24.0, 8.0, 192.0,
             [Opening("door", 3.0, 6.67, 20.0, 1)],
             Corner(0, 2), [])
    ]
    ceilings = [Ceiling("Living Room", "flat", 300.0, 8.0)]
    summary = {
        "total_wall_sqft_gross": 192.0,
        "total_wall_sqft_net": 172.0,
        "total_ceiling_sqft": 300.0,
        "total_drywall_sqft": 472.0,
        "total_linear_ft": 24.0,
        "total_openings": 1,
        "total_opening_sqft": 20.0,
        "total_corners": 2,
        "inside_corners": 0,
        "outside_corners": 2
    }
    detection = DrywallDetection(walls, ceilings, summary, "floor_plan", "1/4\" = 1'-0\"", [])

    # Convert to JSON
    detection_dict = {
        "walls": [asdict(w) for w in detection.walls],
        "ceilings": [asdict(c) for c in detection.ceilings],
        "summary": detection.summary,
        "drawing_type": detection.drawing_type,
        "scale": detection.scale,
        "notes": detection.notes
    }

    json_output = json.dumps(detection_dict, indent=2)

    print("\nJSON Output:")
    print(json_output)

    # Save to file
    output_file = "drywall_detection_output.json"
    with open(output_file, 'w') as f:
        f.write(json_output)
    print(f"\nSaved to: {output_file}")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("DRYWALL DETECTOR - EXAMPLE USAGE")
    print("=" * 60)

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\nERROR: ANTHROPIC_API_KEY not set!")
        print("\nSet your API key:")
        print("  export ANTHROPIC_API_KEY='your-key-here'")
        print("\nOr create a .env file in the backend directory")
        return

    # Run examples
    try:
        example_basic_usage()
        example_compare_sheet_sizes()
        example_difficulty_comparison()
        example_export_json()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        print("\nMake sure to generate test fixtures first:")
        print("  cd tests/fixtures")
        print("  python generate_test_floorplans.py")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
