#!/usr/bin/env python3
"""
Standalone test script for DrywallCalculator
Validates all core functionality without pytest dependencies
"""

import sys
from backend.drywall_calculator import (
    DrywallCalculator,
    RoomGeometry,
    DrywallSpecifications,
    Opening,
    FinishLevel,
    ProjectType,
    StudSpacing
)


def test_basic_geometry():
    """Test basic room geometry calculations"""
    print("\n=== Test 1: Basic Room Geometry ===")

    room = RoomGeometry(
        length=20.0,
        width=15.0,
        height=9.0
    )

    assert room.perimeter == 70.0, f"Expected 70.0, got {room.perimeter}"
    assert room.wall_sqft == 630.0, f"Expected 630.0, got {room.wall_sqft}"
    assert room.ceiling_sqft == 300.0, f"Expected 300.0, got {room.ceiling_sqft}"

    print("✓ Perimeter: 70 LF")
    print("✓ Wall area: 630 sqft")
    print("✓ Ceiling area: 300 sqft")
    print("PASSED")


def test_openings():
    """Test opening calculations"""
    print("\n=== Test 2: Opening Deductions ===")

    openings = [
        Opening(width=3.0, height=7.0, type="door"),
        Opening(width=4.0, height=5.0, type="window"),
        Opening(width=4.0, height=5.0, type="window")
    ]

    room = RoomGeometry(
        length=20.0,
        width=15.0,
        height=9.0,
        openings=openings
    )

    expected_area = 21.0 + 20.0 + 20.0
    assert room.opening_sqft == expected_area, f"Expected {expected_area}, got {room.opening_sqft}"

    print(f"✓ Total opening area: {room.opening_sqft} sqft")
    print("PASSED")


def test_sheet_calculation():
    """Test drywall sheet calculation"""
    print("\n=== Test 3: Sheet Calculation ===")

    calc = DrywallCalculator()

    room = RoomGeometry(
        length=15.0,
        width=12.0,
        height=8.0,
        openings=[
            Opening(width=3.0, height=7.0, type="door"),
            Opening(width=3.0, height=5.0, type="window")
        ]
    )

    specs = DrywallSpecifications()

    total_sheets, waste_factor = calc.calculate_sheets(room, specs, include_ceiling=True)

    print(f"✓ Sheets needed: {total_sheets}")
    print(f"✓ Waste factor: {waste_factor:.2%}")

    assert total_sheets >= 14, f"Expected at least 14 sheets, got {total_sheets}"
    assert total_sheets <= 18, f"Expected at most 18 sheets, got {total_sheets}"
    assert waste_factor >= 0.15, f"Expected at least 15% waste, got {waste_factor:.2%}"

    print("PASSED")


def test_joint_compound():
    """Test joint compound calculation by level"""
    print("\n=== Test 4: Joint Compound by Level ===")

    calc = DrywallCalculator()
    sqft = 1000.0

    specs_l1 = DrywallSpecifications(finish_level=FinishLevel.LEVEL_1)
    specs_l3 = DrywallSpecifications(finish_level=FinishLevel.LEVEL_3)
    specs_l5 = DrywallSpecifications(finish_level=FinishLevel.LEVEL_5)

    compound_l1 = calc.calculate_joint_compound(sqft, specs_l1)
    compound_l3 = calc.calculate_joint_compound(sqft, specs_l3)
    compound_l5 = calc.calculate_joint_compound(sqft, specs_l5)

    print(f"✓ Level 1: {compound_l1:.1f} lbs")
    print(f"✓ Level 3: {compound_l3:.1f} lbs")
    print(f"✓ Level 5: {compound_l5:.1f} lbs")

    assert compound_l1 < compound_l3 < compound_l5, "Higher levels should use more compound"
    assert 50 <= compound_l3 <= 65, f"Level 3 should be 50-65 lbs, got {compound_l3:.1f}"

    print("PASSED")


def test_corner_calculation():
    """Test corner bead calculation"""
    print("\n=== Test 5: Corner Bead Calculation ===")

    calc = DrywallCalculator()

    room = RoomGeometry(
        length=20.0,
        width=15.0,
        height=9.0,
        inside_corners=4,
        outside_corners=2,
        has_ceiling=True
    )

    inside_lf, outside_lf = calc.calculate_corners(room)

    print(f"✓ Inside corners: {inside_lf} LF")
    print(f"✓ Outside corners: {outside_lf} LF")

    # Inside: (4 × 9) + 70 = 106
    assert inside_lf == 106.0, f"Expected 106 LF inside, got {inside_lf}"
    # Outside: 2 × 9 = 18
    assert outside_lf == 18.0, f"Expected 18 LF outside, got {outside_lf}"

    print("PASSED")


def test_complete_estimate():
    """Test complete estimate generation"""
    print("\n=== Test 6: Complete Estimate (12' × 15' Bedroom) ===")

    calc = DrywallCalculator(labor_rate=65.0, overhead_percent=0.15, profit_percent=0.25)

    room_data = {
        "name": "Bedroom",
        "length": 15.0,
        "width": 12.0,
        "height": 8.0,
        "openings": [
            {"width": 3.0, "height": 7.0, "type": "door"},
            {"width": 3.0, "height": 5.0, "type": "window"}
        ],
        "inside_corners": 4,
        "outside_corners": 0,
        "has_ceiling": True
    }

    estimate = calc.estimate_project(room_data)

    print(f"✓ Room: {estimate.room_name}")
    print(f"✓ Total sqft: {estimate.geometry.wall_sqft + estimate.geometry.ceiling_sqft:.0f}")
    print(f"✓ Sheets: {estimate.materials.total_sheets}")
    print(f"✓ Joint compound: {estimate.materials.joint_compound:.0f} lbs")
    print(f"✓ Labor hours: {estimate.labor.total:.1f}")
    print(f"✓ Total cost: ${estimate.costs.total:,.2f}")
    print(f"✓ Price per sqft: ${estimate.price_per_sqft:.2f}")

    assert estimate.materials.total_sheets > 0, "Should have sheets"
    assert estimate.labor.total > 0, "Should have labor hours"
    assert estimate.costs.total > 0, "Should have total cost"
    assert 2.0 <= estimate.price_per_sqft <= 6.0, f"Price/sqft should be $2-6, got ${estimate.price_per_sqft:.2f}"

    print("PASSED")


def test_commercial_project():
    """Test commercial Level 4 estimate"""
    print("\n=== Test 7: Commercial Level 4 Finish ===")

    calc = DrywallCalculator(labor_rate=75.0)

    room_data = {
        "name": "Conference Room",
        "length": 30.0,
        "width": 20.0,
        "height": 10.0,
        "openings": [
            {"width": 3.0, "height": 7.0, "type": "door"},
            {"width": 3.0, "height": 7.0, "type": "door"}
        ],
        "inside_corners": 4,
        "has_ceiling": True
    }

    specs = {
        "finish_level": FinishLevel.LEVEL_4,
        "project_type": ProjectType.COMMERCIAL
    }

    estimate = calc.estimate_project(room_data, specs)

    print(f"✓ Level 4 finish")
    print(f"✓ Sheets: {estimate.materials.total_sheets}")
    print(f"✓ Joint compound: {estimate.materials.joint_compound:.0f} lbs")
    print(f"✓ Labor hours: {estimate.labor.total:.1f}")
    print(f"✓ Total cost: ${estimate.costs.total:,.2f}")

    assert estimate.labor.taping_first_coat > 0, "Should have first coat"
    assert estimate.labor.taping_second_coat > 0, "Should have second coat"
    assert estimate.labor.taping_third_coat > 0, "Should have third coat"
    assert estimate.materials.joint_compound > 100, "Level 4 needs more compound"

    print("PASSED")


def test_multi_room_project():
    """Test multi-room project estimation"""
    print("\n=== Test 8: Multi-Room Project (2,000 sqft House) ===")

    calc = DrywallCalculator(labor_rate=65.0)

    rooms = [
        {
            "name": "Living Room",
            "length": 20.0,
            "width": 15.0,
            "height": 8.0,
            "openings": [
                {"width": 3.0, "height": 7.0, "type": "door"},
                {"width": 4.0, "height": 5.0, "type": "window"}
            ],
            "inside_corners": 4,
            "has_ceiling": True
        },
        {
            "name": "Master Bedroom",
            "length": 16.0,
            "width": 14.0,
            "height": 8.0,
            "openings": [
                {"width": 3.0, "height": 7.0, "type": "door"},
                {"width": 4.0, "height": 5.0, "type": "window"}
            ],
            "inside_corners": 4,
            "has_ceiling": True
        },
        {
            "name": "Bedroom 2",
            "length": 12.0,
            "width": 11.0,
            "height": 8.0,
            "openings": [
                {"width": 3.0, "height": 7.0, "type": "door"},
                {"width": 3.0, "height": 5.0, "type": "window"}
            ],
            "inside_corners": 4,
            "has_ceiling": True
        }
    ]

    result = calc.estimate_multi_room_project(rooms)

    total_sqft = result["totals"]["total_sqft"]
    total_cost = result["totals"]["costs"]["total"]
    price_per_sqft = result["totals"]["price_per_sqft"]

    print(f"✓ Total rooms: {result['totals']['total_rooms']}")
    print(f"✓ Total sqft: {total_sqft:.0f}")
    print(f"✓ Total sheets: {result['totals']['materials']['total_sheets']}")
    print(f"✓ Total labor hours: {result['totals']['labor']['total']:.1f}")
    print(f"✓ Total cost: ${total_cost:,.2f}")
    print(f"✓ Price per sqft: ${price_per_sqft:.2f}")

    assert result["totals"]["total_rooms"] == 3, "Should have 3 rooms"
    assert total_sqft > 1000, "Should be substantial square footage"
    assert 2.5 <= price_per_sqft <= 6.0, f"Price should be reasonable, got ${price_per_sqft:.2f}"

    print("PASSED")


def test_fire_rated():
    """Test fire-rated Type X drywall"""
    print("\n=== Test 9: Fire-Rated Type X Drywall ===")

    calc = DrywallCalculator()

    room_data = {
        "name": "Garage",
        "length": 20.0,
        "width": 20.0,
        "height": 9.0,
        "openings": [
            {"width": 3.0, "height": 7.0, "type": "door"}
        ],
        "inside_corners": 4,
        "has_ceiling": True
    }

    standard_estimate = calc.estimate_project(room_data)

    specs = {
        "fire_rated": True,
        "sheet_thickness": "5/8"
    }

    fire_estimate = calc.estimate_project(room_data, specs)

    print(f"✓ Standard sheets cost: ${standard_estimate.costs.drywall_sheets:.2f}")
    print(f"✓ Fire-rated sheets cost: ${fire_estimate.costs.drywall_sheets:.2f}")

    assert fire_estimate.costs.drywall_sheets > standard_estimate.costs.drywall_sheets, \
        "Fire-rated should cost more"

    print("PASSED")


def test_edge_cases():
    """Test edge cases"""
    print("\n=== Test 10: Edge Cases ===")

    calc = DrywallCalculator()

    # Very small room
    small_room = {
        "name": "Closet",
        "length": 6.0,
        "width": 4.0,
        "height": 8.0,
        "openings": [],
        "inside_corners": 4,
        "has_ceiling": True
    }

    small_estimate = calc.estimate_project(small_room)
    print(f"✓ Small room (closet): {small_estimate.materials.total_sheets} sheets")
    assert small_estimate.materials.total_sheets >= 3, "Small room should still need sheets"

    # Room with no ceiling
    no_ceiling = {
        "name": "Open Area",
        "length": 15.0,
        "width": 12.0,
        "height": 9.0,
        "openings": [],
        "inside_corners": 4,
        "has_ceiling": False
    }

    no_ceiling_estimate = calc.estimate_project(no_ceiling)
    print(f"✓ Room without ceiling: {no_ceiling_estimate.materials.total_sheets} sheets")
    assert no_ceiling_estimate.geometry.ceiling_sqft == 0.0, "Should have no ceiling area"

    # Many openings
    many_openings = {
        "name": "Sunroom",
        "length": 20.0,
        "width": 15.0,
        "height": 9.0,
        "openings": [
            {"width": 6.0, "height": 6.0, "type": "window"},
            {"width": 6.0, "height": 6.0, "type": "window"},
            {"width": 6.0, "height": 6.0, "type": "window"},
            {"width": 6.0, "height": 6.0, "type": "window"}
        ],
        "inside_corners": 4,
        "has_ceiling": True
    }

    many_estimate = calc.estimate_project(many_openings)
    print(f"✓ Room with many openings: {many_estimate.geometry.opening_sqft:.0f} sqft deductions")
    assert many_estimate.geometry.opening_sqft > 100, "Should have substantial opening area"

    print("PASSED")


def main():
    """Run all tests"""
    print("=" * 60)
    print("DRYWALL CALCULATOR COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    tests = [
        test_basic_geometry,
        test_openings,
        test_sheet_calculation,
        test_joint_compound,
        test_corner_calculation,
        test_complete_estimate,
        test_commercial_project,
        test_multi_room_project,
        test_fire_rated,
        test_edge_cases
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("\n✓ ALL TESTS PASSED!")
        return 0
    else:
        print(f"\n✗ {failed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
