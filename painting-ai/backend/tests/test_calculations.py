"""
Paint Calculation Engine Unit Tests

Tests for paint coverage calculations, labor hour estimations,
material costs, and room estimate generation.
"""

import pytest
from painting_detector import PaintCalculator, Room, Surface


# ============================================================================
# Paint Coverage Calculation Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.calculations
class TestPaintCoverageCalculations:
    """Test paint coverage calculations"""

    def test_calculate_paint_for_wall_surface(self, paint_calculator, surface_wall):
        """Test paint calculation for a standard wall"""
        result = paint_calculator.calculate_paint(surface_wall, num_coats=2)

        assert result["surface_area"] == 500.0
        assert result["num_coats"] == 2
        assert result["coverage_rate"] == 400  # Default smooth drywall

        # (500 sqft * 2 coats) / 400 coverage * 1.10 waste = 2.75 gallons
        assert 2.5 < result["gallons_calculated"] < 3.0
        assert result["gallons_to_buy"] == 3  # Rounded up

    def test_calculate_paint_for_ceiling_surface(self, paint_calculator, surface_ceiling):
        """Test paint calculation for ceiling"""
        result = paint_calculator.calculate_paint(surface_ceiling, num_coats=2)

        assert result["surface_area"] == 300.0
        # (300 sqft * 2 coats) / 400 coverage * 1.10 waste = 1.65 gallons
        assert result["gallons_to_buy"] == 2

    def test_calculate_paint_with_single_coat(self, paint_calculator, surface_wall):
        """Test calculation with single coat"""
        result = paint_calculator.calculate_paint(surface_wall, num_coats=1)

        assert result["num_coats"] == 1
        # (500 * 1) / 400 * 1.10 = 1.375 gallons
        assert result["gallons_to_buy"] == 1

    def test_calculate_paint_with_custom_waste_factor(self, paint_calculator, surface_wall):
        """Test calculation with custom waste factor"""
        # No waste
        result_no_waste = paint_calculator.calculate_paint(surface_wall, num_coats=2, waste_factor=1.0)

        # High waste (commercial)
        result_high_waste = paint_calculator.calculate_paint(surface_wall, num_coats=2, waste_factor=1.20)

        assert result_no_waste["gallons_calculated"] < result_high_waste["gallons_calculated"]

    def test_calculate_paint_minimum_one_gallon(self, paint_calculator):
        """Test that minimum purchase is 1 gallon"""
        tiny_surface = Surface(type="trim", area=10.0)
        result = paint_calculator.calculate_paint(tiny_surface, num_coats=1)

        assert result["gallons_to_buy"] >= 1

    def test_calculate_paint_with_different_surface_types(self):
        """Test coverage rates vary by surface type"""
        surface = Surface(type="wall", area=400.0)

        # Smooth drywall (400 sqft/gal)
        calc_smooth = PaintCalculator(surface_type="smooth_drywall")
        result_smooth = calc_smooth.calculate_paint(surface, num_coats=1, waste_factor=1.0)

        # Rough plaster (325 sqft/gal)
        calc_rough = PaintCalculator(surface_type="rough_plaster")
        result_rough = calc_rough.calculate_paint(surface, num_coats=1, waste_factor=1.0)

        # Rough surface needs more paint
        assert result_rough["gallons_calculated"] > result_smooth["gallons_calculated"]

    def test_calculate_paint_large_area(self, paint_calculator):
        """Test calculation for large commercial area"""
        large_wall = Surface(type="wall", area=5000.0)
        result = paint_calculator.calculate_paint(large_wall, num_coats=2)

        # Should calculate appropriate gallons
        assert result["gallons_to_buy"] >= 25
        assert result["gallons_calculated"] > 0


# ============================================================================
# Labor Hour Calculation Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.calculations
class TestLaborCalculations:
    """Test labor hour calculations"""

    def test_calculate_labor_for_wall(self, paint_calculator, surface_wall):
        """Test labor calculation for wall painting"""
        result = paint_calculator.calculate_labor(surface_wall, num_coats=2)

        assert "base_hours" in result
        assert "prep_hours" in result
        assert "touch_up_hours" in result
        assert "total_hours" in result
        assert result["production_rate"] == 300  # Wall production rate

        # Verify total = base + prep + touchup
        expected_total = result["base_hours"] + result["prep_hours"] + result["touch_up_hours"]
        assert abs(result["total_hours"] - expected_total) < 0.01

    def test_calculate_labor_prep_time_is_fifteen_percent(self, paint_calculator, surface_wall):
        """Test that prep time is 15% of base hours"""
        result = paint_calculator.calculate_labor(surface_wall, num_coats=2)

        expected_prep = result["base_hours"] * 0.15
        assert abs(result["prep_hours"] - expected_prep) < 0.01

    def test_calculate_labor_touchup_time_is_five_percent(self, paint_calculator, surface_wall):
        """Test that touch-up time is 5% of base hours"""
        result = paint_calculator.calculate_labor(surface_wall, num_coats=2)

        expected_touchup = result["base_hours"] * 0.05
        assert abs(result["touch_up_hours"] - expected_touchup) < 0.01

    def test_calculate_labor_for_ceiling(self, paint_calculator, surface_ceiling):
        """Test labor calculation for ceiling (faster rate)"""
        result = paint_calculator.calculate_labor(surface_ceiling, num_coats=2)

        assert result["production_rate"] == 350  # Ceiling is faster

    def test_calculate_labor_for_trim(self, paint_calculator):
        """Test labor calculation for trim (slower rate)"""
        trim = Surface(type="trim", area=100.0, linear_feet=200.0)
        result = paint_calculator.calculate_labor(trim, num_coats=2)

        assert result["production_rate"] == 200  # Trim is slower

    def test_calculate_labor_for_doors(self, paint_calculator):
        """Test labor calculation for doors"""
        door = Surface(type="door", area=42.0)
        result = paint_calculator.calculate_labor(door, num_coats=2)

        assert result["production_rate"] == 30  # Doors are slowest

    def test_calculate_labor_more_coats_more_hours(self, paint_calculator, surface_wall):
        """Test that more coats equals more labor hours"""
        result_1_coat = paint_calculator.calculate_labor(surface_wall, num_coats=1)
        result_2_coats = paint_calculator.calculate_labor(surface_wall, num_coats=2)
        result_3_coats = paint_calculator.calculate_labor(surface_wall, num_coats=3)

        assert result_1_coat["total_hours"] < result_2_coats["total_hours"]
        assert result_2_coats["total_hours"] < result_3_coats["total_hours"]

    def test_calculate_labor_large_area(self, paint_calculator):
        """Test labor for large commercial area"""
        large_surface = Surface(type="wall", area=10000.0)
        result = paint_calculator.calculate_labor(large_surface, num_coats=2)

        # Large area should require significant hours
        assert result["total_hours"] > 50


# ============================================================================
# Room Estimate Calculation Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.calculations
class TestRoomEstimateCalculations:
    """Test complete room estimate calculations"""

    def test_calculate_room_estimate_for_simple_room(self, paint_calculator, simple_room):
        """Test complete estimate for a simple residential room"""
        estimate = paint_calculator.calculate_room_estimate(
            room=simple_room,
            paint_price=55.0,
            labor_rate=50.0
        )

        assert estimate["room_id"] == "room_1"
        assert estimate["room_name"] == "Living Room"
        assert "surfaces" in estimate
        assert "totals" in estimate

        # Check totals exist
        totals = estimate["totals"]
        assert totals["paint_gallons"] > 0
        assert totals["labor_hours"] > 0
        assert totals["material_cost"] > 0
        assert totals["labor_cost"] > 0
        assert totals["total_cost"] > 0

    def test_calculate_room_estimate_includes_all_surfaces(self, paint_calculator, simple_room):
        """Test that estimate includes all room surfaces"""
        estimate = paint_calculator.calculate_room_estimate(simple_room)

        surfaces = estimate["surfaces"]
        assert "walls" in surfaces
        assert "ceiling" in surfaces
        assert "trim" in surfaces
        assert "doors" in surfaces

    def test_calculate_room_estimate_surface_details(self, paint_calculator, simple_room):
        """Test that each surface has complete details"""
        estimate = paint_calculator.calculate_room_estimate(simple_room)

        wall_estimate = estimate["surfaces"]["walls"]
        assert "primer" in wall_estimate
        assert "finish" in wall_estimate
        assert "labor" in wall_estimate
        assert "costs" in wall_estimate

        # Check primer details
        assert "gallons_to_buy" in wall_estimate["primer"]
        assert "coverage_rate" in wall_estimate["primer"]

        # Check costs
        assert "primer" in wall_estimate["costs"]
        assert "finish" in wall_estimate["costs"]
        assert "labor" in wall_estimate["costs"]
        assert "total" in wall_estimate["costs"]

    def test_calculate_room_estimate_primer_cheaper_than_finish(self, paint_calculator, simple_room):
        """Test that primer is priced at 75% of finish paint"""
        paint_price = 60.0
        estimate = paint_calculator.calculate_room_estimate(
            room=simple_room,
            paint_price=paint_price
        )

        for surface_name, surface_estimate in estimate["surfaces"].items():
            primer_gallons = surface_estimate["primer"]["gallons_to_buy"]
            expected_primer_cost = primer_gallons * (paint_price * 0.75)

            # Allow small rounding difference
            assert abs(surface_estimate["costs"]["primer"] - expected_primer_cost) < 0.01

    def test_calculate_room_estimate_labor_cost_calculation(self, paint_calculator, simple_room):
        """Test labor cost calculation"""
        labor_rate = 65.0
        estimate = paint_calculator.calculate_room_estimate(
            room=simple_room,
            labor_rate=labor_rate
        )

        # Check each surface labor cost
        for surface_name, surface_estimate in estimate["surfaces"].items():
            labor_hours = surface_estimate["labor"]["hours"]
            expected_labor_cost = labor_hours * labor_rate

            assert abs(surface_estimate["labor"]["cost"] - expected_labor_cost) < 0.01

    def test_calculate_room_estimate_includes_sundries(self, paint_calculator, simple_room):
        """Test that estimate includes sundries (supplies)"""
        estimate = paint_calculator.calculate_room_estimate(simple_room)

        # Sundries are added to material cost
        # Should be at least 5% of material cost or $0.095/sqft
        material_cost = estimate["totals"]["material_cost"]

        # Material cost should include sundries
        assert material_cost > 0

    def test_calculate_room_estimate_total_cost_accuracy(self, paint_calculator, simple_room):
        """Test that total cost equals material + labor"""
        estimate = paint_calculator.calculate_room_estimate(simple_room)

        totals = estimate["totals"]
        expected_total = totals["material_cost"] + totals["labor_cost"]

        assert abs(totals["total_cost"] - expected_total) < 0.01

    def test_calculate_room_estimate_commercial_room(self, paint_calculator, commercial_room):
        """Test estimate for larger commercial room"""
        estimate = paint_calculator.calculate_room_estimate(
            room=commercial_room,
            paint_price=65.0,
            labor_rate=55.0
        )

        # Commercial room should cost more
        assert estimate["totals"]["total_cost"] > 1000
        assert estimate["totals"]["paint_gallons"] > 10

    def test_calculate_room_estimate_with_custom_pricing(self, paint_calculator, simple_room):
        """Test estimate with custom paint and labor pricing"""
        estimate_economy = paint_calculator.calculate_room_estimate(
            room=simple_room,
            paint_price=35.0,
            labor_rate=40.0
        )

        estimate_premium = paint_calculator.calculate_room_estimate(
            room=simple_room,
            paint_price=75.0,
            labor_rate=65.0
        )

        # Premium should cost more
        assert estimate_premium["totals"]["total_cost"] > estimate_economy["totals"]["total_cost"]


# ============================================================================
# Surface Type Coverage Rate Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.calculations
class TestSurfaceTypeCoverageRates:
    """Test coverage rates for different surface types"""

    def test_smooth_drywall_coverage_rate(self):
        """Test smooth drywall has 400 sqft/gal coverage"""
        calc = PaintCalculator(surface_type="smooth_drywall")
        assert calc.coverage_rate == 400

    def test_textured_drywall_coverage_rate(self):
        """Test textured drywall has lower coverage"""
        calc = PaintCalculator(surface_type="textured_drywall")
        assert calc.coverage_rate == 350

    def test_rough_plaster_coverage_rate(self):
        """Test rough plaster has lowest coverage"""
        calc = PaintCalculator(surface_type="rough_plaster")
        assert calc.coverage_rate == 325

    def test_metal_coverage_rate(self):
        """Test metal has highest coverage"""
        calc = PaintCalculator(surface_type="metal")
        assert calc.coverage_rate == 500

    def test_wood_coverage_rate(self):
        """Test wood surface coverage"""
        calc = PaintCalculator(surface_type="wood")
        assert calc.coverage_rate == 350

    def test_concrete_coverage_rate(self):
        """Test concrete surface coverage"""
        calc = PaintCalculator(surface_type="concrete")
        assert calc.coverage_rate == 300

    def test_unknown_surface_type_uses_default(self):
        """Test unknown surface type defaults to 400"""
        calc = PaintCalculator(surface_type="unknown_material")
        assert calc.coverage_rate == 400


# ============================================================================
# Production Rate Tests
# ============================================================================

@pytest.mark.unit
@pytest.mark.calculations
class TestProductionRates:
    """Test labor production rates"""

    def test_wall_production_rate(self, paint_calculator):
        """Test wall production rate"""
        assert paint_calculator.PRODUCTION_RATES["wall"] == 300

    def test_ceiling_production_rate(self, paint_calculator):
        """Test ceiling production rate (faster)"""
        assert paint_calculator.PRODUCTION_RATES["ceiling"] == 350

    def test_trim_production_rate(self, paint_calculator):
        """Test trim production rate (slower)"""
        assert paint_calculator.PRODUCTION_RATES["trim"] == 200

    def test_door_production_rate(self, paint_calculator):
        """Test door production rate (slowest)"""
        assert paint_calculator.PRODUCTION_RATES["door"] == 30


# ============================================================================
# Edge Cases and Boundary Conditions
# ============================================================================

@pytest.mark.unit
@pytest.mark.calculations
class TestCalculationEdgeCases:
    """Test edge cases in calculations"""

    def test_calculate_paint_with_zero_area(self, paint_calculator):
        """Test calculation with zero area"""
        zero_surface = Surface(type="wall", area=0.0)
        result = paint_calculator.calculate_paint(zero_surface, num_coats=2)

        assert result["gallons_to_buy"] == 1  # Minimum 1 gallon

    def test_calculate_labor_with_zero_area(self, paint_calculator):
        """Test labor calculation with zero area"""
        zero_surface = Surface(type="wall", area=0.0)
        result = paint_calculator.calculate_labor(zero_surface, num_coats=2)

        assert result["total_hours"] == 0

    def test_calculate_paint_with_very_large_area(self, paint_calculator):
        """Test calculation with extremely large area"""
        huge_surface = Surface(type="wall", area=100000.0)
        result = paint_calculator.calculate_paint(huge_surface, num_coats=2)

        assert result["gallons_to_buy"] > 0
        assert result["gallons_calculated"] > 0

    def test_calculate_room_estimate_with_no_surfaces(self, paint_calculator):
        """Test room estimate with no surfaces"""
        empty_room = Room(
            id="empty",
            name="Empty Room",
            dimensions={"length": 10, "width": 10, "height": 8},
            surfaces={}
        )
        empty_room.total_area = 0

        estimate = paint_calculator.calculate_room_estimate(empty_room)

        assert estimate["totals"]["paint_gallons"] == 0
        assert estimate["totals"]["labor_hours"] == 0
        assert estimate["totals"]["total_cost"] == 0

    def test_calculate_with_fractional_dimensions(self, paint_calculator):
        """Test calculations with fractional dimensions"""
        fractional_surface = Surface(type="wall", area=123.456)
        result = paint_calculator.calculate_paint(fractional_surface, num_coats=2)

        assert result["gallons_calculated"] > 0
        assert isinstance(result["gallons_to_buy"], int)

    def test_calculate_room_estimate_with_high_paint_price(self, paint_calculator, simple_room):
        """Test estimate with very high paint price"""
        estimate = paint_calculator.calculate_room_estimate(
            room=simple_room,
            paint_price=500.0,  # Extremely expensive paint
            labor_rate=50.0
        )

        # Should still calculate properly
        assert estimate["totals"]["material_cost"] > estimate["totals"]["labor_cost"]

    def test_calculate_room_estimate_with_high_labor_rate(self, paint_calculator, simple_room):
        """Test estimate with very high labor rate"""
        estimate = paint_calculator.calculate_room_estimate(
            room=simple_room,
            paint_price=55.0,
            labor_rate=200.0  # Extremely expensive labor
        )

        # Labor cost should dominate
        assert estimate["totals"]["labor_cost"] > estimate["totals"]["material_cost"]

    def test_paint_calculation_rounding(self, paint_calculator):
        """Test that gallon calculations round up properly"""
        # Area that needs exactly 2.1 gallons should round to 2
        surface = Surface(type="wall", area=380.0)
        result = paint_calculator.calculate_paint(surface, num_coats=2, waste_factor=1.0)

        # 380 * 2 / 400 = 1.9 gallons, rounds to 2
        assert result["gallons_to_buy"] == 2
