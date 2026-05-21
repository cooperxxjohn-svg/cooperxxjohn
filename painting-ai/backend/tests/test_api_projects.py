"""
Integration tests for project endpoints
Tests: GET/POST/DELETE /projects, GET /projects/{id}, POST /projects/{id}/estimate
"""

import pytest
import uuid
from fastapi.testclient import TestClient


class TestProjectCreate:
    """Test POST /projects endpoint"""

    def test_create_project_success(self, test_client, test_project_data):
        """Test successful project creation"""
        response = test_client.post("/projects", json=test_project_data)

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == test_project_data["name"]
        assert data["customer"] == test_project_data["customer"]
        assert "id" in data
        assert data["status"] == "created"
        assert data["total_rooms"] == 0
        assert data["total_sqft"] == 0.0

    def test_create_project_minimal(self, test_client):
        """Test creating project with only required fields"""
        project_data = {
            "name": "Minimal Project"
        }

        response = test_client.post("/projects", json=project_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Minimal Project"
        assert data["customer"] is None

    def test_create_project_missing_name(self, test_client):
        """Test creating project without name returns 422"""
        project_data = {
            "customer": "Test Customer"
        }

        response = test_client.post("/projects", json=project_data)

        assert response.status_code == 422

    def test_create_project_empty_name(self, test_client):
        """Test creating project with empty name"""
        project_data = {
            "name": "",
            "customer": "Test Customer"
        }

        response = test_client.post("/projects", json=project_data)

        # Should either validate or accept empty string
        assert response.status_code in [200, 400, 422]


class TestProjectList:
    """Test GET /projects endpoint"""

    def test_list_projects_empty(self, test_client, db):
        """Test listing projects when none exist"""
        response = test_client.get("/projects")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_list_projects_with_data(self, test_client, test_project):
        """Test listing projects returns created projects"""
        response = test_client.get("/projects")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

        # Find our test project
        project_ids = [p["id"] for p in data]
        assert test_project["id"] in project_ids

    def test_list_projects_multiple(self, test_client):
        """Test listing multiple projects"""
        # Create multiple projects
        for i in range(3):
            project_data = {
                "name": f"Project {i}",
                "customer": f"Customer {i}"
            }
            test_client.post("/projects", json=project_data)

        response = test_client.get("/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3


class TestProjectGet:
    """Test GET /projects/{id} endpoint"""

    def test_get_project_success(self, test_client, test_project):
        """Test getting a specific project"""
        project_id = test_project["id"]
        response = test_client.get(f"/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == project_id
        assert data["name"] == test_project["name"]
        assert data["customer"] == test_project["customer"]

    def test_get_project_not_found(self, test_client):
        """Test getting non-existent project returns 404"""
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/projects/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_project_invalid_id(self, test_client):
        """Test getting project with invalid ID format"""
        response = test_client.get("/projects/invalid-id-format")

        assert response.status_code == 404


class TestProjectStatus:
    """Test GET /projects/{id}/status endpoint"""

    def test_get_project_status(self, test_client, test_project):
        """Test getting project processing status"""
        project_id = test_project["id"]
        response = test_client.get(f"/projects/{project_id}/status")

        assert response.status_code == 200
        data = response.json()

        assert data["project_id"] == project_id
        assert "status" in data
        assert "total_rooms" in data
        assert "total_sqft" in data
        assert "uploads" in data

    def test_get_status_not_found(self, test_client):
        """Test getting status for non-existent project"""
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/projects/{fake_id}/status")

        assert response.status_code == 404


class TestProjectEstimate:
    """Test POST /projects/{id}/estimate endpoint"""

    def test_generate_estimate_no_rooms(self, test_client, test_project):
        """Test generating estimate for project without rooms"""
        project_id = test_project["id"]
        estimate_params = {
            "paint_price": 55.0,
            "labor_rate": 50.0,
            "surface_type": "smooth_drywall"
        }

        response = test_client.post(
            f"/projects/{project_id}/estimate",
            json=estimate_params
        )

        assert response.status_code == 200
        data = response.json()

        assert data["project_id"] == project_id
        assert "estimates" in data
        assert "totals" in data
        assert data["totals"]["paint_gallons"] == 0.0
        assert data["totals"]["labor_hours"] == 0.0
        assert data["totals"]["total_cost"] == 0.0

    def test_generate_estimate_with_rooms(self, test_client, test_project, db, sample_room_with_surfaces):
        """Test generating estimate for project with rooms"""
        project_id = test_project["id"]

        # Add a room to the project
        sample_room_with_surfaces["project_id"] = project_id
        db.save_room(sample_room_with_surfaces)

        # Update project with room count
        db.update_project(project_id, {
            "total_rooms": 1,
            "total_sqft": sample_room_with_surfaces["total_area"]
        })

        estimate_params = {
            "paint_price": 55.0,
            "labor_rate": 50.0,
            "surface_type": "smooth_drywall"
        }

        response = test_client.post(
            f"/projects/{project_id}/estimate",
            json=estimate_params
        )

        assert response.status_code == 200
        data = response.json()

        assert data["project_id"] == project_id
        assert len(data["estimates"]) == 1
        assert data["totals"]["paint_gallons"] > 0
        assert data["totals"]["labor_hours"] > 0
        assert data["totals"]["total_cost"] > 0

    def test_estimate_project_not_found(self, test_client):
        """Test generating estimate for non-existent project"""
        fake_id = str(uuid.uuid4())
        estimate_params = {
            "paint_price": 55.0,
            "labor_rate": 50.0,
            "surface_type": "smooth_drywall"
        }

        response = test_client.post(
            f"/projects/{fake_id}/estimate",
            json=estimate_params
        )

        assert response.status_code == 404

    def test_estimate_custom_params(self, test_client, test_project, db, sample_room_with_surfaces):
        """Test estimate with custom pricing parameters"""
        project_id = test_project["id"]

        # Add a room
        sample_room_with_surfaces["project_id"] = project_id
        db.save_room(sample_room_with_surfaces)
        db.update_project(project_id, {
            "total_rooms": 1,
            "total_sqft": sample_room_with_surfaces["total_area"]
        })

        # Custom high-end params
        estimate_params = {
            "paint_price": 85.0,
            "labor_rate": 75.0,
            "surface_type": "textured_drywall"
        }

        response = test_client.post(
            f"/projects/{project_id}/estimate",
            json=estimate_params
        )

        assert response.status_code == 200
        data = response.json()

        # Cost should be higher with premium params
        assert data["totals"]["total_cost"] > 0


class TestProjectDelete:
    """Test DELETE /projects/{id} endpoint"""

    def test_delete_project_success(self, test_client, test_project):
        """Test successful project deletion"""
        project_id = test_project["id"]

        response = test_client.delete(f"/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["project_id"] == project_id
        assert "deleted" in data["message"].lower()

        # Verify project is gone
        get_response = test_client.get(f"/projects/{project_id}")
        assert get_response.status_code == 404

    def test_delete_project_not_found(self, test_client):
        """Test deleting non-existent project returns 404"""
        fake_id = str(uuid.uuid4())
        response = test_client.delete(f"/projects/{fake_id}")

        assert response.status_code == 404

    def test_delete_project_cascades_to_rooms(self, test_client, test_project, db, sample_room_with_surfaces):
        """Test deleting project also deletes associated rooms"""
        project_id = test_project["id"]

        # Add rooms to project
        sample_room_with_surfaces["project_id"] = project_id
        db.save_room(sample_room_with_surfaces)

        # Verify room exists
        rooms = db.get_project_rooms(project_id)
        assert len(rooms) > 0

        # Delete project
        response = test_client.delete(f"/projects/{project_id}")
        assert response.status_code == 200

        # Verify rooms are deleted
        rooms_after = db.get_project_rooms(project_id)
        assert len(rooms_after) == 0


class TestProjectRooms:
    """Test GET /projects/{id}/rooms endpoint"""

    def test_get_project_rooms_empty(self, test_client, test_project):
        """Test getting rooms for project with no rooms"""
        project_id = test_project["id"]
        response = test_client.get(f"/projects/{project_id}/rooms")

        assert response.status_code == 200
        data = response.json()
        assert "rooms" in data
        assert isinstance(data["rooms"], list)
        assert len(data["rooms"]) == 0

    def test_get_project_rooms_with_data(self, test_client, test_project, db, sample_room_with_surfaces):
        """Test getting rooms for project with rooms"""
        project_id = test_project["id"]

        # Add room to project
        sample_room_with_surfaces["project_id"] = project_id
        db.save_room(sample_room_with_surfaces)

        response = test_client.get(f"/projects/{project_id}/rooms")

        assert response.status_code == 200
        data = response.json()
        assert len(data["rooms"]) == 1
        assert data["rooms"][0]["name"] == sample_room_with_surfaces["name"]


class TestAssemblyExpansion:
    """Test POST /projects/{id}/assembly-expansion endpoint"""

    def test_assembly_expansion_no_rooms(self, test_client, test_project):
        """Test assembly expansion fails when no rooms exist"""
        project_id = test_project["id"]

        response = test_client.post(
            f"/projects/{project_id}/assembly-expansion",
            params={"paint_type": "commercial", "labor_rate": 50.0}
        )

        assert response.status_code == 400
        assert "no rooms" in response.json()["detail"].lower()

    def test_assembly_expansion_with_rooms(self, test_client, test_project, db, sample_room_with_surfaces):
        """Test successful assembly expansion"""
        project_id = test_project["id"]

        # Add room to project
        sample_room_with_surfaces["project_id"] = project_id
        db.save_room(sample_room_with_surfaces)

        response = test_client.post(
            f"/projects/{project_id}/assembly-expansion",
            params={"paint_type": "commercial", "labor_rate": 50.0}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["project_id"] == project_id
        assert data["paint_type"] == "commercial"
        assert "rooms" in data
        assert "summary" in data
        assert data["summary"]["total_line_items"] > 0

    def test_assembly_expansion_project_not_found(self, test_client):
        """Test assembly expansion for non-existent project"""
        fake_id = str(uuid.uuid4())

        response = test_client.post(
            f"/projects/{fake_id}/assembly-expansion",
            params={"paint_type": "commercial", "labor_rate": 50.0}
        )

        assert response.status_code == 404
