"""
Tests for Drywall Detection Engine
Tests wall detection, opening detection, corner counting, and material calculations
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock
from dataclasses import asdict

# Import the drywall detector classes
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from drywall_detector import (
    DrywallDetector,
    DrywallCalculator,
    Wall,
    Ceiling,
    Opening,
    Corner,
    DrywallDetection
)


# Mock Claude API response for testing
MOCK_FLOOR_PLAN_RESPONSE = {
    "walls": [
        {
            "wall_id": "W1",
            "type": "exterior",
            "length_ft": 30.0,
            "height_ft": 8.0,
            "square_footage": 240.0,
            "openings": [
                {
                    "type": "door",
                    "width": 3.0,
                    "height": 6.67,
                    "square_footage": 20.0,
                    "quantity": 1
                },
                {
                    "type": "window",
                    "width": 4.0,
                    "height": 3.0,
                    "square_footage": 12.0,
                    "quantity": 2
                }
            ],
            "corners": {
                "inside_corners": 0,
                "outside_corners": 2
            },
            "special_features": []
        },
        {
            "wall_id": "W2",
            "type": "interior",
            "length_ft": 20.0,
            "height_ft": 8.0,
            "square_footage": 160.0,
            "openings": [
                {
                    "type": "door",
                    "width": 3.0,
                    "height": 6.67,
                    "square_footage": 20.0,
                    "quantity": 1
                }
            ],
            "corners": {
                "inside_corners": 2,
                "outside_corners": 0
            },
            "special_features": []
        },
        {
            "wall_id": "W3",
            "type": "exterior",
            "length_ft": 30.0,
            "height_ft": 8.0,
            "square_footage": 240.0,
            "openings": [],
            "corners": {
                "inside_corners": 0,
                "outside_corners": 2
            },
            "special_features": []
        },
        {
            "wall_id": "W4",
            "type": "exterior",
            "length_ft": 20.0,
            "height_ft": 8.0,
            "square_footage": 160.0,
            "openings": [
                {
                    "type": "window",
                    "width": 6.0,
                    "height": 4.0,
                    "square_footage": 24.0,
                    "quantity": 1
                }
            ],
            "corners": {
                "inside_corners": 0,
                "outside_corners": 2
            },
            "special_features": []
        }
    ],
    "ceilings": [
        {
            "room": "Living Room",
            "type": "flat",
            "square_footage": 600.0,
            "height_ft": 8.0,
            "special_notes": null
        }
    ]
}


@pytest.fixture
def mock_api_key():
    """Provide a mock API key for testing"""
    return "test-api-key-12345"


@pytest.fixture
def mock_detection():
    """Create a mock DrywallDetection object for testing calculations"""
    walls = [
        Wall(
            wall_id="W1",
            type="exterior",
            length_ft=30.0,
            height_ft=8.0,
            square_footage=240.0,
            openings=[
                Opening(type="door", width=3.0, height=6.67, square_footage=20.0, quantity=1),
                Opening(type="window", width=4.0, height=3.0, square_footage=12.0, quantity=2)
            ],
            corners=Corner(inside_corners=0, outside_corners=2),
            special_features=[]
        ),
        Wall(
            wall_id="W2",
            type="interior",
            length_ft=20.0,
            height_ft=8.0,
            square_footage=160.0,
            openings=[
                Opening(type="door", width=3.0, height=6.67, square_footage=20.0, quantity=1)
            ],
            corners=Corner(inside_corners=2, outside_corners=0),
            special_features=[]
        )
    ]

    ceilings = [
        Ceiling(room="Living Room", type="flat", square_footage=600.0, height_ft=8.0)
    ]

    summary = {
        "total_wall_sqft_gross": 400.0,
        "total_wall_sqft_net": 336.0,  # 400 - (20 + 24 + 20)
        "total_ceiling_sqft": 600.0,
        "total_drywall_sqft": 936.0,
        "total_linear_ft": 50.0,
        "total_openings": 4,
        "total_opening_sqft": 64.0,
        "total_corners": 4,
        "inside_corners": 2,
        "outside_corners": 2
    }

    return DrywallDetection(
        walls=walls,
        ceilings=ceilings,
        summary=summary,
        drawing_type="floor_plan",
        scale="1/4\" = 1'-0\"",
        notes=[]
    )


class TestDrywallDetector:
    """Test the DrywallDetector AI detection functionality"""

    def test_detector_initialization(self, mock_api_key):
        """Test that detector initializes correctly"""
        detector = DrywallDetector(mock_api_key)
        assert detector.model == "claude-sonnet-4-20250514"
        assert detector.client is not None

    @patch('drywall_detector.DrywallDetector._encode_image')
    @patch('drywall_detector.DrywallDetector._classify_drawing')
    @patch('drywall_detector.DrywallDetector._extract_from_floor_plan')
    def test_analyze_drawing_floor_plan(self, mock_extract, mock_classify, mock_encode, mock_api_key):
        """Test analyzing a floor plan drawing"""
        # Setup mocks
        mock_encode.return_value = "base64_encoded_image"
        mock_classify.return_value = {"type": "floor_plan", "scale": "1/4\" = 1'-0\""}

        # Create mock walls and ceilings
        mock_walls = [
            Wall("W1", "exterior", 30.0, 8.0, 240.0, [], Corner(0, 2), [])
        ]
        mock_ceilings = [
            Ceiling("Living Room", "flat", 600.0, 8.0)
        ]
        mock_extract.return_value = (mock_walls, mock_ceilings)

        detector = DrywallDetector(mock_api_key)
        result = detector.analyze_drawing("test_floorplan.png")

        assert isinstance(result, DrywallDetection)
        assert result.drawing_type == "floor_plan"
        assert len(result.walls) == 1
        assert len(result.ceilings) == 1
        assert result.summary["total_wall_sqft_gross"] == 240.0

    def test_parse_walls(self, mock_api_key):
        """Test parsing wall data from API response"""
        detector = DrywallDetector(mock_api_key)

        wall_data = [{
            "wall_id": "W1",
            "type": "interior",
            "length_ft": 24.5,
            "height_ft": 8.0,
            "square_footage": 196.0,
            "openings": [
                {
                    "type": "door",
                    "width": 3.0,
                    "height": 6.67,
                    "square_footage": 20.0,
                    "quantity": 1
                }
            ],
            "corners": {
                "inside_corners": 1,
                "outside_corners": 1
            },
            "special_features": ["soffit"]
        }]

        walls = detector._parse_walls(wall_data)

        assert len(walls) == 1
        wall = walls[0]
        assert wall.wall_id == "W1"
        assert wall.type == "interior"
        assert wall.length_ft == 24.5
        assert wall.height_ft == 8.0
        assert len(wall.openings) == 1
        assert wall.openings[0].type == "door"
        assert wall.corners.inside_corners == 1
        assert wall.corners.outside_corners == 1
        assert "soffit" in wall.special_features

    def test_parse_ceilings(self, mock_api_key):
        """Test parsing ceiling data from API response"""
        detector = DrywallDetector(mock_api_key)

        ceiling_data = [{
            "room": "Master Bedroom",
            "type": "tray",
            "square_footage": 320.0,
            "height_ft": 9.0,
            "special_notes": "Two-level tray ceiling"
        }]

        ceilings = detector._parse_ceilings(ceiling_data)

        assert len(ceilings) == 1
        ceiling = ceilings[0]
        assert ceiling.room == "Master Bedroom"
        assert ceiling.type == "tray"
        assert ceiling.square_footage == 320.0
        assert ceiling.height_ft == 9.0
        assert ceiling.special_notes == "Two-level tray ceiling"

    def test_calculate_summary(self, mock_api_key):
        """Test summary calculation from walls and ceilings"""
        detector = DrywallDetector(mock_api_key)

        walls = [
            Wall("W1", "exterior", 30.0, 8.0, 240.0,
                 [Opening("door", 3.0, 6.67, 20.0, 1)],
                 Corner(0, 2), []),
            Wall("W2", "interior", 20.0, 8.0, 160.0,
                 [Opening("window", 4.0, 3.0, 12.0, 2)],
                 Corner(2, 0), [])
        ]

        ceilings = [
            Ceiling("Living Room", "flat", 600.0, 8.0)
        ]

        summary = detector._calculate_summary(walls, ceilings)

        assert summary["total_wall_sqft_gross"] == 400.0  # 240 + 160
        assert summary["total_wall_sqft_net"] == 356.0    # 400 - 20 - (12*2)
        assert summary["total_ceiling_sqft"] == 600.0
        assert summary["total_drywall_sqft"] == 956.0    # 356 + 600
        assert summary["total_linear_ft"] == 50.0        # 30 + 20
        assert summary["total_openings"] == 3            # 1 door + 2 windows
        assert summary["total_corners"] == 4             # 2 outside + 2 inside
        assert summary["inside_corners"] == 2
        assert summary["outside_corners"] == 2

    def test_validate_detection_high_walls(self, mock_api_key):
        """Test validation flags unusual wall heights"""
        detector = DrywallDetector(mock_api_key)

        walls = [
            Wall("W1", "interior", 30.0, 15.0, 450.0, [], Corner(0, 0), [])  # 15ft height
        ]
        ceilings = []
        summary = {"total_wall_sqft_net": 450.0, "total_linear_ft": 30.0}

        notes = detector._validate_detection(walls, ceilings, summary)

        assert any("unusual height" in note.lower() for note in notes)

    def test_validate_detection_long_walls(self, mock_api_key):
        """Test validation flags very long walls"""
        detector = DrywallDetector(mock_api_key)

        walls = [
            Wall("W1", "interior", 75.0, 8.0, 600.0, [], Corner(0, 0), [])  # 75ft length
        ]
        ceilings = []
        summary = {"total_wall_sqft_net": 600.0, "total_linear_ft": 75.0}

        notes = detector._validate_detection(walls, ceilings, summary)

        assert any("expansion joint" in note.lower() for note in notes)

    def test_validate_detection_no_data(self, mock_api_key):
        """Test validation flags when no data detected"""
        detector = DrywallDetector(mock_api_key)

        walls = []
        ceilings = []
        summary = {}

        notes = detector._validate_detection(walls, ceilings, summary)

        assert any("error" in note.lower() for note in notes)


class TestDrywallCalculator:
    """Test the DrywallCalculator material and labor calculations"""

    def test_calculator_initialization(self):
        """Test calculator initializes with correct sheet size"""
        calc = DrywallCalculator(sheet_size="4x8")
        assert calc.sheet_size == "4x8"
        assert calc.sheet_sqft == 32

        calc_large = DrywallCalculator(sheet_size="4x12")
        assert calc_large.sheet_sqft == 48

    def test_calculate_materials_basic(self, mock_detection):
        """Test basic material calculations"""
        calc = DrywallCalculator(sheet_size="4x8")
        materials = calc.calculate_materials(mock_detection, waste_factor=1.10)

        # 936 total sqft * 1.10 waste / 32 sqft per sheet = 32.175 -> 33 sheets
        assert materials["drywall_sheets"]["quantity"] == 33
        assert materials["drywall_sheets"]["size"] == "4x8"

        # Joint compound: 936 / 400 = 2.34 -> 3 buckets
        assert materials["joint_compound"]["buckets_5gal"] == 3

        # Tape: 936 * 1.1 = 1029.6 ft -> 3 rolls (500ft each)
        assert materials["tape"]["rolls"] >= 2

        # Corner bead: 2 outside corners * 8ft each = 16ft -> 2 pieces (10ft each)
        assert materials["corner_bead"]["linear_ft"] == 16

    def test_calculate_materials_waste_factor(self, mock_detection):
        """Test waste factor affects sheet count"""
        calc = DrywallCalculator(sheet_size="4x8")

        materials_low_waste = calc.calculate_materials(mock_detection, waste_factor=1.05)
        materials_high_waste = calc.calculate_materials(mock_detection, waste_factor=1.15)

        assert materials_high_waste["drywall_sheets"]["quantity"] >= materials_low_waste["drywall_sheets"]["quantity"]

    def test_calculate_labor_standard(self, mock_detection):
        """Test labor calculation with standard difficulty"""
        calc = DrywallCalculator()
        labor = calc.calculate_labor(mock_detection, difficulty="standard")

        assert labor["total_hours"] > 0
        assert labor["hanging_hours"] > 0
        assert labor["taping_hours"] > 0
        assert labor["finishing_hours"] > 0
        assert labor["sanding_hours"] > 0
        assert labor["difficulty"] == "standard"
        assert labor["difficulty_multiplier"] == 1.00

        # Total should be sum of phases plus corner time
        expected_base = (labor["hanging_hours"] + labor["taping_hours"] +
                        labor["finishing_hours"] + labor["sanding_hours"])
        assert labor["base_hours"] == pytest.approx(expected_base, rel=0.01)

    def test_calculate_labor_difficulty_levels(self, mock_detection):
        """Test different difficulty levels affect labor hours"""
        calc = DrywallCalculator()

        labor_easy = calc.calculate_labor(mock_detection, difficulty="easy")
        labor_standard = calc.calculate_labor(mock_detection, difficulty="standard")
        labor_difficult = calc.calculate_labor(mock_detection, difficulty="difficult")

        assert labor_easy["total_hours"] < labor_standard["total_hours"]
        assert labor_difficult["total_hours"] > labor_standard["total_hours"]
        assert labor_easy["difficulty_multiplier"] == 0.85
        assert labor_difficult["difficulty_multiplier"] == 1.30

    def test_calculate_labor_production_rates(self, mock_detection):
        """Test labor uses correct production rates"""
        calc = DrywallCalculator()
        labor = calc.calculate_labor(mock_detection, difficulty="standard")

        total_sqft = mock_detection.summary["total_drywall_sqft"]  # 936 sqft

        # Hanging: 936 / 40 = 23.4 hours
        expected_hanging = total_sqft / calc.PRODUCTION_RATES["hanging"]
        assert labor["hanging_hours"] == pytest.approx(expected_hanging, rel=0.01)

        # Taping: 936 / 150 = 6.24 hours
        expected_taping = total_sqft / calc.PRODUCTION_RATES["taping"]
        assert labor["taping_hours"] == pytest.approx(expected_taping, rel=0.01)

    def test_calculate_estimate_complete(self, mock_detection):
        """Test complete estimate calculation"""
        calc = DrywallCalculator()
        estimate = calc.calculate_estimate(
            mock_detection,
            sheet_price=15.00,
            labor_rate=65.00,
            difficulty="standard",
            waste_factor=1.10
        )

        # Check structure
        assert "materials" in estimate
        assert "material_details" in estimate
        assert "labor" in estimate
        assert "pricing" in estimate
        assert "summary" in estimate

        # Check materials
        assert estimate["materials"]["drywall_sheets"] > 0
        assert estimate["materials"]["joint_compound"] > 0
        assert estimate["materials"]["total"] > 0

        # Check labor
        assert estimate["labor"]["hours"] > 0
        assert estimate["labor"]["rate"] == 65.00
        assert estimate["labor"]["total"] > 0

        # Check pricing
        pricing = estimate["pricing"]
        assert pricing["subtotal"] > 0
        assert pricing["overhead"] > 0
        assert pricing["profit"] > 0
        assert pricing["total"] > 0
        assert pricing["price_per_sqft"] > 0

        # Verify overhead is 15% of subtotal
        assert pricing["overhead"] == pytest.approx(pricing["subtotal"] * 0.15, rel=0.01)

        # Verify profit is 20% of subtotal
        assert pricing["profit"] == pytest.approx(pricing["subtotal"] * 0.20, rel=0.01)

        # Verify total = subtotal + overhead + profit
        assert pricing["total"] == pytest.approx(
            pricing["subtotal"] + pricing["overhead"] + pricing["profit"],
            rel=0.01
        )

    def test_calculate_estimate_price_per_sqft(self, mock_detection):
        """Test price per square foot calculation"""
        calc = DrywallCalculator()
        estimate = calc.calculate_estimate(mock_detection)

        total_sqft = mock_detection.summary["total_drywall_sqft"]
        expected_price_per_sqft = estimate["pricing"]["total"] / total_sqft

        assert estimate["pricing"]["price_per_sqft"] == pytest.approx(expected_price_per_sqft, rel=0.01)

    def test_calculate_estimate_different_sheet_sizes(self, mock_detection):
        """Test estimates with different sheet sizes"""
        calc_8ft = DrywallCalculator(sheet_size="4x8")
        calc_12ft = DrywallCalculator(sheet_size="4x12")

        estimate_8ft = calc_8ft.calculate_estimate(mock_detection)
        estimate_12ft = calc_12ft.calculate_estimate(mock_detection)

        # 4x12 sheets should need fewer sheets
        sheets_8ft = estimate_8ft["material_details"]["drywall_sheets"]["quantity"]
        sheets_12ft = estimate_12ft["material_details"]["drywall_sheets"]["quantity"]

        assert sheets_12ft < sheets_8ft

    def test_corner_bead_calculation(self, mock_detection):
        """Test corner bead calculation based on outside corners"""
        calc = DrywallCalculator()
        materials = calc.calculate_materials(mock_detection)

        outside_corners = mock_detection.summary["outside_corners"]  # 2
        expected_linear_ft = outside_corners * calc.CORNER_BEAD_PER_CORNER  # 2 * 8 = 16

        assert materials["corner_bead"]["linear_ft"] == expected_linear_ft
        assert materials["corner_bead"]["corners"] == outside_corners


class TestDataClasses:
    """Test the dataclass structures"""

    def test_opening_creation(self):
        """Test Opening dataclass"""
        opening = Opening(
            type="door",
            width=3.0,
            height=6.67,
            square_footage=20.0,
            quantity=2
        )
        assert opening.type == "door"
        assert opening.width == 3.0
        assert opening.square_footage == 20.0
        assert opening.quantity == 2

    def test_corner_creation(self):
        """Test Corner dataclass"""
        corner = Corner(inside_corners=4, outside_corners=2)
        assert corner.inside_corners == 4
        assert corner.outside_corners == 2

    def test_wall_creation(self):
        """Test Wall dataclass"""
        openings = [Opening("door", 3.0, 6.67, 20.0, 1)]
        corners = Corner(inside_corners=2, outside_corners=0)

        wall = Wall(
            wall_id="W1",
            type="interior",
            length_ft=24.5,
            height_ft=8.0,
            square_footage=196.0,
            openings=openings,
            corners=corners,
            special_features=["soffit"]
        )

        assert wall.wall_id == "W1"
        assert wall.type == "interior"
        assert len(wall.openings) == 1
        assert wall.corners.inside_corners == 2
        assert "soffit" in wall.special_features

    def test_ceiling_creation(self):
        """Test Ceiling dataclass"""
        ceiling = Ceiling(
            room="Living Room",
            type="vaulted",
            square_footage=400.0,
            height_ft=12.0,
            special_notes="14ft peak"
        )

        assert ceiling.room == "Living Room"
        assert ceiling.type == "vaulted"
        assert ceiling.special_notes == "14ft peak"

    def test_drywall_detection_creation(self, mock_detection):
        """Test DrywallDetection dataclass"""
        assert isinstance(mock_detection, DrywallDetection)
        assert len(mock_detection.walls) == 2
        assert len(mock_detection.ceilings) == 1
        assert mock_detection.drawing_type == "floor_plan"
        assert "total_drywall_sqft" in mock_detection.summary


class TestIntegration:
    """Integration tests combining detection and calculation"""

    def test_full_workflow_mock(self, mock_detection):
        """Test complete workflow from detection to estimate"""
        # Detection already created by fixture

        # Calculate materials
        calc = DrywallCalculator(sheet_size="4x8")
        estimate = calc.calculate_estimate(
            mock_detection,
            sheet_price=15.00,
            labor_rate=65.00,
            difficulty="standard"
        )

        # Verify estimate is reasonable
        assert estimate["pricing"]["total"] > 0
        assert estimate["pricing"]["price_per_sqft"] > 0

        # Typical drywall pricing: $1.50 - $3.50 per sqft installed
        # With materials, should be around $2-5/sqft
        price_per_sqft = estimate["pricing"]["price_per_sqft"]
        assert 1.5 <= price_per_sqft <= 8.0, f"Price ${price_per_sqft:.2f}/sqft outside expected range"

    def test_summary_accuracy(self, mock_detection):
        """Test that summary calculations are accurate"""
        summary = mock_detection.summary

        # Manually verify totals
        total_wall_gross = sum(w.square_footage for w in mock_detection.walls)
        assert summary["total_wall_sqft_gross"] == total_wall_gross

        total_ceiling = sum(c.square_footage for c in mock_detection.ceilings)
        assert summary["total_ceiling_sqft"] == total_ceiling

        total_linear = sum(w.length_ft for w in mock_detection.walls)
        assert summary["total_linear_ft"] == total_linear


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
