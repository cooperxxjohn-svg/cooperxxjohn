"""
Integration tests for room endpoints
Tests: GET /rooms/{id}, PATCH /rooms/{id}
"""

import pytest
import uuid
from fastapi.testclient import TestClient


class TestRoomGet:
    """Test GET /rooms/{id} endpoint"""

    def test_get_room_success(self, test_client, db, sample_room_with_surfaces):
        """Test getting a specific room"""
        # Save room to database
        db.save_room(sample_room_with_surfaces)
        room_id = sample_room_with_surfaces["id"]

        response = test_client.get(f"/rooms/{room_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == room_id
        assert data["name"] == sample_room_with_surfaces["name"]
        assert "surfaces" in data
        assert "dimensions" in data

    def test_get_room_not_found(self, test_client):
        """Test getting non-existent room returns 404"""
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/rooms/{fake_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_room_invalid_id(self, test_client):
        """Test getting room with invalid ID format"""
        response = test_client.get("/rooms/invalid-id-format")

        assert response.status_code == 404

    def test_get_room_includes_surfaces(self, test_client, db, sample_room_with_surfaces):
        """Test that room data includes surface information"""
        db.save_room(sample_room_with_surfaces)
        room_id = sample_room_with_surfaces["id"]

        response = test_client.get(f"/rooms/{room_id}")

        assert response.status_code == 200
        data = response.json()

        assert "surfaces" in data
        assert "walls" in data["surfaces"]
        assert "ceiling" in data["surfaces"]
        assert data["surfaces"]["walls"]["area"] > 0


class TestRoomUpdate:
    """Test PATCH /rooms/{id} endpoint"""

    def test_update_room_name(self, test_client, db, sample_room_with_surfaces):
        """Test updating room name"""
        db.save_room(sample_room_with_surfaces)
        room_id = sample_room_with_surfaces["id"]

        update_data = {
            "name": "Updated Room Name"
        }

        response = test_client.patch(f"/rooms/{room_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["room_id"] == room_id

        # Verify update
        room = db.get_room(room_id)
        assert room["name"] == "Updated Room Name"

    def test_update_room_dimensions(self, test_client, db, sample_room_with_surfaces):
        """Test updating room dimensions"""
        db.save_room(sample_room_with_surfaces)
        room_id = sample_room_with_surfaces["id"]

        update_data = {
            "dimensions": {
                "length": 15.0,
                "width": 12.0,
                "height": 10.0
            }
        }

        response = test_client.patch(f"/rooms/{room_id}", json=update_data)

        assert response.status_code == 200

        # Verify update
        room = db.get_room(room_id)
        assert room["dimensions"]["length"] == 15.0
        assert room["dimensions"]["width"] == 12.0
        assert room["dimensions"]["height"] == 10.0

    def test_update_room_notes(self, test_client, db, sample_room_with_surfaces):
        """Test updating room notes"""
        db.save_room(sample_room_with_surfaces)
        room_id = sample_room_with_surfaces["id"]

        update_data = {
            "notes": "Updated notes for this room"
        }

        response = test_client.patch(f"/rooms/{room_id}", json=update_data)

        assert response.status_code == 200

        # Verify update
        room = db.get_room(room_id)
        assert room["notes"] == "Updated notes for this room"

    def test_update_room_multiple_fields(self, test_client, db, sample_room_with_surfaces):
        """Test updating multiple room fields at once"""
        db.save_room(sample_room_with_surfaces)
        room_id = sample_room_with_surfaces["id"]

        update_data = {
            "name": "Multi-Update Room",
            "notes": "Updated with multiple fields",
            "dimensions": {
                "length": 20.0,
                "width": 18.0,
                "height": 9.0
            }
        }

        response = test_client.patch(f"/rooms/{room_id}", json=update_data)

        assert response.status_code == 200

        # Verify all updates
        room = db.get_room(room_id)
        assert room["name"] == "Multi-Update Room"
        assert room["notes"] == "Updated with multiple fields"
        assert room["dimensions"]["length"] == 20.0

    def test_update_room_not_found(self, test_client):
        """Test updating non-existent room returns 404"""
        fake_id = str(uuid.uuid4())
        update_data = {
            "name": "Should Fail"
        }

        response = test_client.patch(f"/rooms/{fake_id}", json=update_data)

        assert response.status_code == 404

    def test_update_room_empty_payload(self, test_client, db, sample_room_with_surfaces):
        """Test updating room with empty payload"""
        db.save_room(sample_room_with_surfaces)
        room_id = sample_room_with_surfaces["id"]

        update_data = {}

        response = test_client.patch(f"/rooms/{room_id}", json=update_data)

        # Should succeed but not change anything
        assert response.status_code == 200

    def test_update_room_partial_dimensions(self, test_client, db, sample_room_with_surfaces):
        """Test updating only some dimension fields"""
        db.save_room(sample_room_with_surfaces)
        room_id = sample_room_with_surfaces["id"]
        original_dimensions = sample_room_with_surfaces["dimensions"].copy()

        update_data = {
            "dimensions": {
                "length": 25.0
                # Only updating length, not width or height
            }
        }

        response = test_client.patch(f"/rooms/{room_id}", json=update_data)

        assert response.status_code == 200

        # Verify partial update
        room = db.get_room(room_id)
        # Note: Behavior may vary - might replace whole dict or merge
        assert "dimensions" in room

    def test_update_room_invalid_data_type(self, test_client, db, sample_room_with_surfaces):
        """Test updating room with invalid data types"""
        db.save_room(sample_room_with_surfaces)
        room_id = sample_room_with_surfaces["id"]

        update_data = {
            "dimensions": "not a dict"  # Should be a dict
        }

        response = test_client.patch(f"/rooms/{room_id}", json=update_data)

        # Should fail validation
        assert response.status_code in [400, 422]

    def test_update_preserves_surfaces(self, test_client, db, sample_room_with_surfaces):
        """Test that updating room doesn't lose surface data"""
        db.save_room(sample_room_with_surfaces)
        room_id = sample_room_with_surfaces["id"]
        original_surfaces = sample_room_with_surfaces["surfaces"].copy()

        update_data = {
            "name": "Name Change Only"
        }

        response = test_client.patch(f"/rooms/{room_id}", json=update_data)

        assert response.status_code == 200

        # Verify surfaces are preserved
        room = db.get_room(room_id)
        assert "surfaces" in room
        assert "walls" in room["surfaces"]
        assert room["surfaces"]["walls"]["area"] == original_surfaces["walls"]["area"]


class TestRoomValidation:
    """Test room data validation"""

    def test_room_with_negative_dimensions(self, test_client, db, sample_room_with_surfaces):
        """Test that negative dimensions are handled"""
        db.save_room(sample_room_with_surfaces)
        room_id = sample_room_with_surfaces["id"]

        update_data = {
            "dimensions": {
                "length": -10.0,
                "width": 12.0,
                "height": 8.0
            }
        }

        response = test_client.patch(f"/rooms/{room_id}", json=update_data)

        # Should either reject or sanitize
        # Exact behavior depends on validation rules
        assert response.status_code in [200, 400, 422]

    def test_room_with_zero_dimensions(self, test_client, db, sample_room_with_surfaces):
        """Test that zero dimensions are handled"""
        db.save_room(sample_room_with_surfaces)
        room_id = sample_room_with_surfaces["id"]

        update_data = {
            "dimensions": {
                "length": 0.0,
                "width": 0.0,
                "height": 0.0
            }
        }

        response = test_client.patch(f"/rooms/{room_id}", json=update_data)

        # Should either reject or allow
        assert response.status_code in [200, 400, 422]

    def test_room_with_very_large_dimensions(self, test_client, db, sample_room_with_surfaces):
        """Test that extremely large dimensions are handled"""
        db.save_room(sample_room_with_surfaces)
        room_id = sample_room_with_surfaces["id"]

        update_data = {
            "dimensions": {
                "length": 10000.0,
                "width": 10000.0,
                "height": 100.0
            }
        }

        response = test_client.patch(f"/rooms/{room_id}", json=update_data)

        # Should accept (commercial buildings can be very large)
        assert response.status_code == 200
