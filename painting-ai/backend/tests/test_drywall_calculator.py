"""
Comprehensive tests for DrywallCalculator
Tests all calculation functions against industry benchmarks
"""

import pytest
import math
from backend.drywall_calculator import (
    DrywallCalculator,
    RoomGeometry,
    DrywallSpecifications,
    Opening,
    FinishLevel,
    ProjectType,
    StudSpacing,
    MaterialQuantities,
    LaborHours,
    CostBreakdown
)


class TestRoomGeometry:
    """Test RoomGeometry calculations"""

    def test_basic_room_geometry(self):
        """Test basic rectangular room"""
        room = RoomGeometry(
            length=20.0,
            width=15.0,
            height=9.0
        )

        assert room.perimeter == 70.0  # 2 * (20 + 15)
        assert room.wall_sqft == 630.0  # 70 * 9
        assert room.ceiling_sqft == 300.0  # 20 * 15
        assert room.opening_sqft == 0.0

    def test_room_with_openings(self):
        """Test room with doors and windows"""
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

        expected_opening_area = 21.0 + 20.0 + 20.0  # 61 sqft
        assert room.opening_sqft == expected_opening_area

    def test_vaulted_ceiling(self):
        """Test vaulted ceiling area calculation"""
        room = RoomGeometry(
            length=20.0,
            width=15.0,
            height=12.0,
            ceiling_type="vaulted"
        )

        # Vaulted ceiling should be 30% more than flat
        flat_area = 300.0
        expected_vaulted = flat_area * 1.3
        assert room.ceiling_sqft == expected_vaulted

    def test_cathedral_ceiling(self):
        """Test cathedral ceiling area calculation"""
        room = RoomGeometry(
            length=25.0,
            width=18.0,
            height=14.0,
            ceiling_type="cathedral"
        )

        flat_area = 450.0
        expected_cathedral = flat_area * 1.4
        assert room.ceiling_sqft == expected_cathedral

    def test_no_ceiling(self):
        """Test room without ceiling (open to above)"""
        room = RoomGeometry(
            length=20.0,
            width=15.0,
            height=9.0,
            has_ceiling=False
        )

        assert room.ceiling_sqft == 0.0


class TestDrywallCalculator:
    """Test DrywallCalculator core functions"""

    @pytest.fixture
    def calculator(self):
        """Standard calculator instance"""
        return DrywallCalculator(
            labor_rate=65.0,
            overhead_percent=0.15,
            profit_percent=0.25
        )

    @pytest.fixture
    def basic_room(self):
        """Basic 12x15 room with standard specs"""
        return RoomGeometry(
            length=15.0,
            width=12.0,
            height=8.0,
            openings=[
                Opening(width=3.0, height=7.0, type="door"),
                Opening(width=3.0, height=5.0, type="window")
            ]
        )

    def test_sheet_calculation_basic(self, calculator, basic_room):
        """Test basic sheet calculation"""
        specs = DrywallSpecifications(
            sheet_width=4.0,
            sheet_length=12.0
        )

        total_sheets, waste_factor = calculator.calculate_sheets(
            basic_room, specs, include_ceiling=True
        )

        # Wall area: 54 * 8 = 432 sqft
        # Ceiling area: 15 * 12 = 180 sqft
        # Total: 612 sqft
        # Deductions: door (21) + window (15) if > 10 sqft each = 36 sqft
        # Net: 576 sqft
        # Sheets: 576 / 48 = 12 base sheets
        # With 15% base + 10% ceiling waste = ~16 sheets

        assert total_sheets >= 15  # Should be around 15-16 sheets
        assert total_sheets <= 17
        assert waste_factor >= 0.15  # At least base waste

    def test_sheet_calculation_no_ceiling(self, calculator, basic_room):
        """Test sheet calculation without ceiling"""
        specs = DrywallSpecifications()

        total_sheets, waste_factor = calculator.calculate_sheets(
            basic_room, specs, include_ceiling=False
        )

        # Wall area only: 54 * 8 = 432 sqft
        # With deductions and waste, should be around 10-11 sheets
        assert total_sheets >= 9
        assert total_sheets <= 12

    def test_high_ceiling_waste(self, calculator):
        """Test that high ceilings add waste factor"""
        high_ceiling_room = RoomGeometry(
            length=20.0,
            width=15.0,
            height=12.0  # High ceiling
        )

        specs = DrywallSpecifications()

        total_sheets, waste_factor = calculator.calculate_sheets(
            high_ceiling_room, specs, include_ceiling=True
        )

        # Should have base (15%) + high ceiling (5%) + ceiling work (10%) = 30%
        assert waste_factor >= 0.25

    def test_opening_reduction(self, calculator):
        """Test opening area reduction logic"""
        # Small openings (< 10 sqft) should not be deducted
        small_openings_room = RoomGeometry(
            length=15.0,
            width=12.0,
            height=8.0,
            openings=[
                Opening(width=2.0, height=4.0, type="window"),  # 8 sqft
                Opening(width=2.0, height=4.0, type="window")   # 8 sqft
            ]
        )

        deductible, labor = calculator.calculate_opening_reduction(small_openings_room)
        assert deductible == 0.0  # No deductions for small openings
        assert labor > 0.0  # But still labor for cutting

        # Large openings (>= 10 sqft) should be deducted
        large_openings_room = RoomGeometry(
            length=15.0,
            width=12.0,
            height=8.0,
            openings=[
                Opening(width=3.0, height=7.0, type="door"),  # 21 sqft
                Opening(width=4.0, height=5.0, type="window")  # 20 sqft
            ]
        )

        deductible, labor = calculator.calculate_opening_reduction(large_openings_room)
        assert deductible == 41.0  # 21 + 20
        assert labor == 0.5  # 0.25 per opening

    def test_corner_calculation(self, calculator):
        """Test corner bead calculation"""
        room = RoomGeometry(
            length=20.0,
            width=15.0,
            height=9.0,
            inside_corners=4,
            outside_corners=2,
            has_ceiling=True
        )

        inside_lf, outside_lf = calculator.calculate_corners(room)

        # Inside corners: 4 * 9 = 36, plus ceiling perimeter (70) = 106
        # Outside corners: 2 * 9 = 18
        assert inside_lf == 106.0
        assert outside_lf == 18.0

    def test_joint_compound_by_level(self, calculator):
        """Test joint compound varies by finish level"""
        sqft = 1000.0

        # Level 1 - minimal compound
        specs_l1 = DrywallSpecifications(finish_level=FinishLevel.LEVEL_1)
        compound_l1 = calculator.calculate_joint_compound(sqft, specs_l1)

        # Level 3 - typical residential
        specs_l3 = DrywallSpecifications(finish_level=FinishLevel.LEVEL_3)
        compound_l3 = calculator.calculate_joint_compound(sqft, specs_l3)

        # Level 5 - skim coat
        specs_l5 = DrywallSpecifications(finish_level=FinishLevel.LEVEL_5)
        compound_l5 = calculator.calculate_joint_compound(sqft, specs_l5)

        # Higher levels should use more compound
        assert compound_l1 < compound_l3 < compound_l5

        # Level 3 should be around 53 lbs per 1000 sqft (with 10% waste)
        assert 50 <= compound_l3 <= 65

    def test_tape_calculation(self, calculator):
        """Test tape calculation includes all seams"""
        room = RoomGeometry(
            length=20.0,
            width=15.0,
            height=9.0,
            inside_corners=4
        )

        tape_lf = calculator.calculate_tape(room)

        # Should account for perimeter, horizontal seams, and corners
        # Rough estimate: perimeter * height + horizontals + corners + waste
        # Should be at least 200 LF for this room
        assert tape_lf >= 200.0

    def test_screw_calculation(self, calculator):
        """Test screw calculation"""
        specs = DrywallSpecifications(sheet_length=12.0)

        # 10 sheets should need ~360-400 screws (36-40 per sheet)
        screws = calculator.calculate_screws(10, specs)
        assert 350 <= screws <= 450

    def test_framing_calculation(self, calculator):
        """Test framing material calculation"""
        room = RoomGeometry(
            length=20.0,
            width=15.0,
            height=9.0,
            openings=[
                Opening(width=3.0, height=7.0, type="door"),
                Opening(width=3.0, height=7.0, type="door")
            ],
            inside_corners=4,
            outside_corners=0
        )

        specs = DrywallSpecifications(
            stud_spacing=StudSpacing.SPACING_16_OC,
            stud_type="metal"
        )

        materials, labor = calculator.calculate_framing(room, specs)

        # Perimeter: 70 feet = 840 inches
        # At 16" OC: 840 / 16 = ~52 studs
        # Plus corners (4 * 2 = 8) and openings (2 * 4 = 8)
        # Total: ~68 studs
        assert materials.studs >= 60
        assert materials.studs <= 75

        # Track should equal perimeter
        assert materials.top_track == 70.0
        assert materials.bottom_track == 70.0

        # Should have headers for each opening
        assert materials.headers == 2

        # Labor should be reasonable (less than 1 hour for framing this room)
        assert 0.5 <= labor <= 1.5


class TestCompleteEstimates:
    """Test complete estimate generation"""

    @pytest.fixture
    def calculator(self):
        return DrywallCalculator(
            labor_rate=65.0,
            overhead_percent=0.15,
            profit_percent=0.25
        )

    def test_small_room_estimate(self, calculator):
        """Test complete estimate for small room (12x15)"""
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

        estimate = calculator.estimate_project(room_data)

        # Basic validations
        assert estimate.room_name == "Bedroom"
        assert estimate.materials.total_sheets > 0
        assert estimate.labor.total > 0
        assert estimate.costs.total > 0

        # Price per sqft should be in reasonable range ($2-$6/sqft)
        assert 2.0 <= estimate.price_per_sqft <= 6.0

    def test_large_room_estimate(self, calculator):
        """Test estimate for large room (20x25)"""
        room_data = {
            "name": "Living Room",
            "length": 25.0,
            "width": 20.0,
            "height": 10.0,
            "openings": [
                {"width": 3.0, "height": 7.0, "type": "door"},
                {"width": 6.0, "height": 5.0, "type": "window"},
                {"width": 6.0, "height": 5.0, "type": "window"}
            ],
            "inside_corners": 4,
            "outside_corners": 0,
            "has_ceiling": True
        }

        estimate = calculator.estimate_project(room_data)

        # Large room should have more materials
        assert estimate.materials.total_sheets >= 30  # Roughly 1400+ sqft
        assert estimate.labor.total >= 25  # Substantial labor hours

    def test_commercial_level_4_estimate(self, calculator):
        """Test commercial project with Level 4 finish"""
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
            "outside_corners": 0,
            "has_ceiling": True
        }

        specs = {
            "finish_level": FinishLevel.LEVEL_4.value,
            "project_type": ProjectType.COMMERCIAL.value
        }

        estimate = calculator.estimate_project(room_data, specs)

        # Level 4 should have more labor than Level 3
        assert estimate.labor.taping_first_coat > 0
        assert estimate.labor.taping_second_coat > 0
        assert estimate.labor.taping_third_coat > 0

        # More joint compound for Level 4
        assert estimate.materials.joint_compound > 100  # Higher for level 4

    def test_high_end_level_5_estimate(self, calculator):
        """Test high-end project with Level 5 finish"""
        room_data = {
            "name": "Executive Office",
            "length": 20.0,
            "width": 16.0,
            "height": 10.0,
            "openings": [
                {"width": 3.0, "height": 7.0, "type": "door"}
            ],
            "inside_corners": 4,
            "outside_corners": 0,
            "has_ceiling": True
        }

        specs = {
            "finish_level": FinishLevel.LEVEL_5.value
        }

        estimate = calculator.estimate_project(room_data, specs)

        # Level 5 requires skim coat
        assert estimate.labor.skim_coat > 0

        # Much more compound needed
        assert estimate.materials.joint_compound > 100

        # Higher price per sqft
        assert estimate.price_per_sqft > 3.5

    def test_fire_rated_drywall(self, calculator):
        """Test fire-rated Type X drywall pricing"""
        room_data = {
            "name": "Garage",
            "length": 20.0,
            "width": 20.0,
            "height": 9.0,
            "openings": [
                {"width": 3.0, "height": 7.0, "type": "door"}
            ],
            "inside_corners": 4,
            "outside_corners": 0,
            "has_ceiling": True
        }

        specs = {
            "fire_rated": True,
            "sheet_thickness": "5/8"
        }

        standard_estimate = calculator.estimate_project(room_data)
        fire_rated_estimate = calculator.estimate_project(room_data, specs)

        # Fire-rated should cost more than standard
        assert fire_rated_estimate.costs.drywall_sheets > standard_estimate.costs.drywall_sheets


class TestIndustryBenchmarks:
    """Test against known industry benchmarks"""

    @pytest.fixture
    def calculator(self):
        return DrywallCalculator(labor_rate=65.0)

    def test_2000_sqft_house(self, calculator):
        """
        Test typical 2,000 sqft house with 8' ceilings, Level 3 finish
        Industry benchmark: $3.50-$5.00/sqft including materials and labor
        """
        # Typical house: 4 bedrooms, 2 baths, living areas
        rooms = [
            {
                "name": "Living Room",
                "length": 20.0,
                "width": 15.0,
                "height": 8.0,
                "openings": [
                    {"width": 3.0, "height": 7.0, "type": "door"},
                    {"width": 4.0, "height": 5.0, "type": "window"},
                    {"width": 4.0, "height": 5.0, "type": "window"}
                ],
                "inside_corners": 4,
                "has_ceiling": True
            },
            {
                "name": "Kitchen",
                "length": 15.0,
                "width": 12.0,
                "height": 8.0,
                "openings": [
                    {"width": 3.0, "height": 7.0, "type": "door"},
                    {"width": 3.0, "height": 5.0, "type": "window"}
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
            },
            {
                "name": "Bedroom 3",
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

        result = calculator.estimate_multi_room_project(rooms)

        total_sqft = result["totals"]["total_sqft"]
        price_per_sqft = result["totals"]["price_per_sqft"]

        # Should be around 2000-2500 sqft of drywall (walls + ceilings)
        assert 1800 <= total_sqft <= 2800

        # Price should be in industry range
        assert 2.5 <= price_per_sqft <= 6.0

        print(f"\n2,000 sqft House Benchmark:")
        print(f"  Total Drywall Area: {total_sqft:.0f} sqft")
        print(f"  Total Sheets: {result['totals']['materials']['total_sheets']}")
        print(f"  Total Labor Hours: {result['totals']['labor']['total']:.1f}")
        print(f"  Total Cost: ${result['totals']['costs']['total']:,.2f}")
        print(f"  Price per sqft: ${price_per_sqft:.2f}")

    def test_10000_sqft_commercial(self, calculator):
        """
        Test 10,000 sqft commercial space with 9' ceilings, Level 4 finish
        Industry benchmark: $4.00-$6.50/sqft for commercial
        """
        # Simulate large commercial space divided into areas
        rooms = [
            {
                "name": "Open Office Area",
                "length": 100.0,
                "width": 50.0,
                "height": 9.0,
                "openings": [
                    {"width": 3.0, "height": 7.0, "type": "door"},
                    {"width": 3.0, "height": 7.0, "type": "door"},
                    {"width": 3.0, "height": 7.0, "type": "door"}
                ],
                "inside_corners": 4,
                "has_ceiling": True
            },
            {
                "name": "Conference Room 1",
                "length": 30.0,
                "width": 20.0,
                "height": 9.0,
                "openings": [
                    {"width": 3.0, "height": 7.0, "type": "door"}
                ],
                "inside_corners": 4,
                "has_ceiling": True
            },
            {
                "name": "Conference Room 2",
                "length": 25.0,
                "width": 18.0,
                "height": 9.0,
                "openings": [
                    {"width": 3.0, "height": 7.0, "type": "door"}
                ],
                "inside_corners": 4,
                "has_ceiling": True
            }
        ]

        specs = {
            "finish_level": FinishLevel.LEVEL_4.value,
            "project_type": ProjectType.COMMERCIAL.value
        }

        result = calculator.estimate_multi_room_project(rooms, specs)

        total_sqft = result["totals"]["total_sqft"]
        price_per_sqft = result["totals"]["price_per_sqft"]

        # Should be substantial square footage
        assert total_sqft >= 8000

        # Commercial Level 4 should be higher price
        assert 3.0 <= price_per_sqft <= 7.0

        print(f"\n10,000 sqft Commercial Benchmark:")
        print(f"  Total Drywall Area: {total_sqft:.0f} sqft")
        print(f"  Total Sheets: {result['totals']['materials']['total_sheets']}")
        print(f"  Total Labor Hours: {result['totals']['labor']['total']:.1f}")
        print(f"  Total Cost: ${result['totals']['costs']['total']:,.2f}")
        print(f"  Price per sqft: ${price_per_sqft:.2f}")

    def test_single_room_12x15(self, calculator):
        """
        Test single 12x15 room with 8' ceiling
        Industry benchmark: 10-12 sheets, 15-20 hours labor
        """
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
            "has_ceiling": True
        }

        estimate = calculator.estimate_project(room_data)

        # Industry standards for this room size
        assert 9 <= estimate.materials.total_sheets <= 14
        assert 12 <= estimate.labor.total <= 25

        print(f"\n12x15 Room Benchmark:")
        print(f"  Sheets: {estimate.materials.total_sheets}")
        print(f"  Labor Hours: {estimate.labor.total:.1f}")
        print(f"  Total Cost: ${estimate.costs.total:,.2f}")


class TestEdgeCases:
    """Test edge cases and unusual scenarios"""

    @pytest.fixture
    def calculator(self):
        return DrywallCalculator()

    def test_very_small_room(self, calculator):
        """Test tiny room (closet)"""
        room_data = {
            "name": "Closet",
            "length": 6.0,
            "width": 4.0,
            "height": 8.0,
            "openings": [
                {"width": 3.0, "height": 7.0, "type": "door"}
            ],
            "inside_corners": 4,
            "has_ceiling": True
        }

        estimate = calculator.estimate_project(room_data)

        # Should still calculate reasonably
        assert estimate.materials.total_sheets >= 3
        assert estimate.costs.total > 0

    def test_very_large_room(self, calculator):
        """Test huge room (warehouse)"""
        room_data = {
            "name": "Warehouse",
            "length": 100.0,
            "width": 80.0,
            "height": 16.0,
            "openings": [],
            "inside_corners": 4,
            "has_ceiling": False  # Open ceiling
        }

        estimate = calculator.estimate_project(room_data)

        # Should handle large scale
        assert estimate.materials.total_sheets > 200
        assert estimate.labor.total > 100

    def test_room_no_openings(self, calculator):
        """Test room with no doors or windows"""
        room_data = {
            "name": "Safe Room",
            "length": 10.0,
            "width": 10.0,
            "height": 8.0,
            "openings": [],
            "inside_corners": 4,
            "has_ceiling": True
        }

        estimate = calculator.estimate_project(room_data)

        # Should calculate without errors
        assert estimate.materials.total_sheets > 0
        assert estimate.costs.total > 0

    def test_room_many_openings(self, calculator):
        """Test room with many openings (sunroom)"""
        room_data = {
            "name": "Sunroom",
            "length": 20.0,
            "width": 15.0,
            "height": 9.0,
            "openings": [
                {"width": 3.0, "height": 7.0, "type": "door"},
                {"width": 6.0, "height": 6.0, "type": "window"},
                {"width": 6.0, "height": 6.0, "type": "window"},
                {"width": 6.0, "height": 6.0, "type": "window"},
                {"width": 6.0, "height": 6.0, "type": "window"}
            ],
            "inside_corners": 4,
            "has_ceiling": True
        }

        estimate = calculator.estimate_project(room_data)

        # Should deduct large window areas
        total_opening_area = 21 + (4 * 36)  # door + 4 windows
        assert estimate.geometry.opening_sqft == total_opening_area


class TestCostBreakdowns:
    """Test cost calculation details"""

    @pytest.fixture
    def calculator(self):
        return DrywallCalculator(
            labor_rate=65.0,
            overhead_percent=0.15,
            profit_percent=0.25
        )

    def test_overhead_and_profit_calculation(self, calculator):
        """Test overhead and profit are calculated correctly"""
        room_data = {
            "name": "Test Room",
            "length": 15.0,
            "width": 12.0,
            "height": 8.0,
            "openings": [],
            "inside_corners": 4,
            "has_ceiling": True
        }

        estimate = calculator.estimate_project(room_data)

        # Overhead should be 15% of subtotal
        expected_overhead = estimate.costs.subtotal * 0.15
        assert abs(estimate.costs.overhead - expected_overhead) < 0.01

        # Profit should be 25% of subtotal
        expected_profit = estimate.costs.subtotal * 0.25
        assert abs(estimate.costs.profit - expected_profit) < 0.01

        # Total should equal subtotal + overhead + profit
        expected_total = estimate.costs.subtotal + estimate.costs.overhead + estimate.costs.profit
        assert abs(estimate.costs.total - expected_total) < 0.01

    def test_labor_cost_calculation(self, calculator):
        """Test labor cost matches hours × rate"""
        room_data = {
            "name": "Test Room",
            "length": 15.0,
            "width": 12.0,
            "height": 8.0,
            "openings": [],
            "inside_corners": 4,
            "has_ceiling": True
        }

        estimate = calculator.estimate_project(room_data)

        expected_labor_cost = estimate.labor.total * calculator.labor_rate
        assert abs(estimate.costs.labor_cost - expected_labor_cost) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
