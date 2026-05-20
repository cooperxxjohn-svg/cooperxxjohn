"""
Test suite for Painting.ai API
"""

import pytest
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, '.')
from main import app

client = TestClient(app)


def test_health_check():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert data["app"] == "Painting.ai"


def test_create_project():
    """Test project creation"""
    project_data = {
        "name": "Test Office Building",
        "customer": "Test Construction Co"
    }

    response = client.post("/projects", json=project_data)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == project_data["name"]
    assert data["customer"] == project_data["customer"]
    assert "id" in data
    assert data["status"] == "created"


def test_get_projects():
    """Test listing projects"""
    response = client.get("/projects")
    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)


def test_get_project():
    """Test getting single project"""
    # Create a project first
    project_data = {"name": "Test Project", "customer": "Test Customer"}
    create_response = client.post("/projects", json=project_data)
    project_id = create_response.json()["id"]

    # Get the project
    response = client.get(f"/projects/{project_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == project_data["name"]


def test_get_nonexistent_project():
    """Test getting project that doesn't exist"""
    response = client.get("/projects/nonexistent-id")
    assert response.status_code == 404


def test_delete_project():
    """Test project deletion"""
    # Create a project
    project_data = {"name": "To Delete", "customer": "Test"}
    create_response = client.post("/projects", json=project_data)
    project_id = create_response.json()["id"]

    # Delete it
    response = client.delete(f"/projects/{project_id}")
    assert response.status_code == 200

    # Verify it's gone
    get_response = client.get(f"/projects/{project_id}")
    assert get_response.status_code == 404


class TestPaintCalculations:
    """Test paint calculation logic"""

    def test_coverage_rates(self):
        """Test paint coverage rate calculations"""
        from painting_detector import PaintCalculator

        calc = PaintCalculator(surface_type="smooth_drywall")
        assert calc.coverage_rate == 400

        calc_textured = PaintCalculator(surface_type="textured_drywall")
        assert calc_textured.coverage_rate == 350

    def test_paint_calculation(self):
        """Test paint volume calculation"""
        from painting_detector import PaintCalculator, Surface

        calc = PaintCalculator()
        surface = Surface(type="wall", area=400)  # 400 sqft wall

        # 2 coats of paint
        result = calc.calculate_paint(surface, num_coats=2)

        # 400 sqft * 2 coats = 800 sqft
        # 800 / 400 coverage * 1.1 waste = 2.2 gallons
        assert result["gallons_calculated"] == pytest.approx(2.2, rel=0.1)
        assert result["gallons_to_buy"] == 2  # Rounded

    def test_labor_calculation(self):
        """Test labor hour calculation"""
        from painting_detector import PaintCalculator, Surface

        calc = PaintCalculator()
        surface = Surface(type="wall", area=600)  # 600 sqft wall

        # 2 coats
        result = calc.calculate_labor(surface, num_coats=2)

        # 600 sqft / 300 rate * 2 coats = 4 base hours
        # + 15% prep (0.6) + 5% touchup (0.2) = 4.8 total
        assert result["base_hours"] == pytest.approx(4.0, rel=0.1)
        assert result["total_hours"] == pytest.approx(4.8, rel=0.1)


class TestSurfaceCalculations:
    """Test surface area calculations"""

    def test_wall_calculation(self):
        """Test wall surface area calculation"""
        from painting_detector import Room, PaintingDetector

        room = Room(
            id="test-1",
            name="Test Room",
            dimensions={"length": 20, "width": 15, "height": 9}
        )

        # Mock detector to test calculation
        room.doors = [{"width": 3, "height": 7}]
        room.windows = [{"width": 3, "height": 5}, {"width": 3, "height": 5}]

        detector = PaintingDetector(api_key="test")
        detector._calculate_surfaces(room)

        # Perimeter = 2 * (20 + 15) = 70 ft
        # Wall area = 70 * 9 = 630 sqft
        # Deductions = 1 door (21 sqft) + 2 windows (30 sqft) = 51 sqft
        # Net = 630 - 51 = 579 sqft

        assert "walls" in room.surfaces
        assert room.surfaces["walls"].area == pytest.approx(579, rel=1)

    def test_ceiling_calculation(self):
        """Test ceiling calculation"""
        from painting_detector import Room, PaintingDetector

        room = Room(
            id="test-2",
            name="Test Room",
            dimensions={"length": 20, "width": 15, "height": 9}
        )

        detector = PaintingDetector(api_key="test")
        detector._calculate_surfaces(room)

        # Ceiling = length * width = 20 * 15 = 300 sqft
        assert "ceiling" in room.surfaces
        assert room.surfaces["ceiling"].area == 300


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
