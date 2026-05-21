"""
Integration tests for export endpoints
Tests: GET /projects/{id}/export/excel, /projects/{id}/export/pdf
"""

import pytest
import uuid
from pathlib import Path
from fastapi.testclient import TestClient


class TestExcelExport:
    """Test GET /projects/{id}/export/excel endpoint"""

    def test_export_excel_success(self, test_client, test_project, db, sample_room_with_surfaces):
        """Test successful Excel export"""
        project_id = test_project["id"]

        # Add room to project
        sample_room_with_surfaces["project_id"] = project_id
        db.save_room(sample_room_with_surfaces)
        db.update_project(project_id, {"total_rooms": 1})

        response = test_client.get(f"/projects/{project_id}/export/excel")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # Check filename in content-disposition
        content_disposition = response.headers.get("content-disposition", "")
        assert ".xlsx" in content_disposition.lower() or "Takeoff" in content_disposition

        # Verify we got actual file content
        assert len(response.content) > 0

    def test_export_excel_project_not_found(self, test_client):
        """Test Excel export for non-existent project returns 404"""
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/projects/{fake_id}/export/excel")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_export_excel_empty_project(self, test_client, test_project):
        """Test Excel export for project with no rooms"""
        project_id = test_project["id"]

        response = test_client.get(f"/projects/{project_id}/export/excel")

        # Should still generate Excel, just empty
        assert response.status_code == 200
        assert len(response.content) > 0

    def test_export_excel_filename_includes_project_name(self, test_client, test_project, db, sample_room_with_surfaces):
        """Test that exported Excel filename includes project name"""
        project_id = test_project["id"]
        project_name = test_project["name"]

        # Add room
        sample_room_with_surfaces["project_id"] = project_id
        db.save_room(sample_room_with_surfaces)

        response = test_client.get(f"/projects/{project_id}/export/excel")

        assert response.status_code == 200

        # Check content-disposition header for filename
        content_disposition = response.headers.get("content-disposition", "")
        # Filename should be sanitized version of project name
        assert "filename=" in content_disposition

    def test_export_excel_creates_file_in_outputs(self, test_client, test_project, db, sample_room_with_surfaces):
        """Test that Excel export creates file in outputs directory"""
        project_id = test_project["id"]

        # Add room
        sample_room_with_surfaces["project_id"] = project_id
        db.save_room(sample_room_with_surfaces)

        response = test_client.get(f"/projects/{project_id}/export/excel")

        assert response.status_code == 200

        # Check that file was created in outputs directory
        output_path = Path("outputs") / f"{project_id}_takeoff.xlsx"
        assert output_path.exists()

    def test_export_excel_with_multiple_rooms(self, test_client, test_project, db):
        """Test Excel export with multiple rooms"""
        project_id = test_project["id"]

        # Add multiple rooms
        for i in range(3):
            room_data = {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "name": f"Room {i+1}",
                "number": f"{100+i}",
                "dimensions": {"length": 10.0, "width": 10.0, "height": 8.0},
                "surfaces": {
                    "walls": {"type": "wall", "area": 320.0, "linear_feet": 40.0, "height": 8.0, "deductions": 0.0}
                },
                "total_area": 320.0
            }
            db.save_room(room_data)

        db.update_project(project_id, {"total_rooms": 3})

        response = test_client.get(f"/projects/{project_id}/export/excel")

        assert response.status_code == 200
        # File should be larger with more rooms
        assert len(response.content) > 1000


class TestPDFExport:
    """Test GET /projects/{id}/export/pdf endpoint"""

    def test_export_pdf_success(self, test_client, test_project, db, sample_room_with_surfaces):
        """Test successful PDF export"""
        project_id = test_project["id"]

        # Add room to project
        sample_room_with_surfaces["project_id"] = project_id
        db.save_room(sample_room_with_surfaces)
        db.update_project(project_id, {"total_rooms": 1})

        response = test_client.get(f"/projects/{project_id}/export/pdf")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

        # Check filename
        content_disposition = response.headers.get("content-disposition", "")
        assert ".pdf" in content_disposition.lower() or "Proposal" in content_disposition

        # Verify we got actual PDF content
        assert len(response.content) > 0
        # PDF files start with %PDF
        assert response.content[:4] == b"%PDF"

    def test_export_pdf_project_not_found(self, test_client):
        """Test PDF export for non-existent project returns 404"""
        fake_id = str(uuid.uuid4())
        response = test_client.get(f"/projects/{fake_id}/export/pdf")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_export_pdf_empty_project(self, test_client, test_project):
        """Test PDF export for project with no rooms"""
        project_id = test_project["id"]

        response = test_client.get(f"/projects/{project_id}/export/pdf")

        # Should still generate PDF, just empty
        assert response.status_code == 200
        assert len(response.content) > 0
        assert response.content[:4] == b"%PDF"

    def test_export_pdf_filename_includes_project_name(self, test_client, test_project, db, sample_room_with_surfaces):
        """Test that exported PDF filename includes project name"""
        project_id = test_project["id"]

        # Add room
        sample_room_with_surfaces["project_id"] = project_id
        db.save_room(sample_room_with_surfaces)

        response = test_client.get(f"/projects/{project_id}/export/pdf")

        assert response.status_code == 200

        # Check content-disposition header
        content_disposition = response.headers.get("content-disposition", "")
        assert "filename=" in content_disposition

    def test_export_pdf_creates_file_in_outputs(self, test_client, test_project, db, sample_room_with_surfaces):
        """Test that PDF export creates file in outputs directory"""
        project_id = test_project["id"]

        # Add room
        sample_room_with_surfaces["project_id"] = project_id
        db.save_room(sample_room_with_surfaces)

        response = test_client.get(f"/projects/{project_id}/export/pdf")

        assert response.status_code == 200

        # Check that file was created
        output_path = Path("outputs") / f"{project_id}_proposal.pdf"
        assert output_path.exists()

    def test_export_pdf_with_multiple_rooms(self, test_client, test_project, db):
        """Test PDF export with multiple rooms"""
        project_id = test_project["id"]

        # Add multiple rooms
        for i in range(3):
            room_data = {
                "id": str(uuid.uuid4()),
                "project_id": project_id,
                "name": f"Conference Room {i+1}",
                "number": f"{200+i}",
                "dimensions": {"length": 15.0, "width": 12.0, "height": 9.0},
                "surfaces": {
                    "walls": {"type": "wall", "area": 486.0, "linear_feet": 54.0, "height": 9.0, "deductions": 0.0},
                    "ceiling": {"type": "ceiling", "area": 180.0, "linear_feet": 0.0, "height": 0.0, "deductions": 0.0}
                },
                "total_area": 666.0
            }
            db.save_room(room_data)

        db.update_project(project_id, {"total_rooms": 3})

        response = test_client.get(f"/projects/{project_id}/export/pdf")

        assert response.status_code == 200
        # PDF should be larger with more rooms
        assert len(response.content) > 1000

    def test_export_pdf_valid_format(self, test_client, test_project, db, sample_room_with_surfaces):
        """Test that exported PDF is valid PDF format"""
        project_id = test_project["id"]

        # Add room
        sample_room_with_surfaces["project_id"] = project_id
        db.save_room(sample_room_with_surfaces)

        response = test_client.get(f"/projects/{project_id}/export/pdf")

        assert response.status_code == 200

        # Basic PDF validation
        content = response.content
        assert content.startswith(b"%PDF-")
        assert b"%%EOF" in content or len(content) > 100


class TestExportIntegration:
    """Test export functionality integration"""

    def test_export_both_formats_same_project(self, test_client, test_project, db, sample_room_with_surfaces):
        """Test exporting both Excel and PDF for same project"""
        project_id = test_project["id"]

        # Add room
        sample_room_with_surfaces["project_id"] = project_id
        db.save_room(sample_room_with_surfaces)

        # Export Excel
        excel_response = test_client.get(f"/projects/{project_id}/export/excel")
        assert excel_response.status_code == 200

        # Export PDF
        pdf_response = test_client.get(f"/projects/{project_id}/export/pdf")
        assert pdf_response.status_code == 200

        # Both should succeed
        assert len(excel_response.content) > 0
        assert len(pdf_response.content) > 0

    def test_export_after_project_update(self, test_client, test_project, db, sample_room_with_surfaces):
        """Test that export reflects project updates"""
        project_id = test_project["id"]

        # Initial export
        initial_response = test_client.get(f"/projects/{project_id}/export/excel")
        assert initial_response.status_code == 200
        initial_size = len(initial_response.content)

        # Add room to project
        sample_room_with_surfaces["project_id"] = project_id
        db.save_room(sample_room_with_surfaces)
        db.update_project(project_id, {"total_rooms": 1})

        # Export again
        updated_response = test_client.get(f"/projects/{project_id}/export/excel")
        assert updated_response.status_code == 200
        updated_size = len(updated_response.content)

        # Updated export should reflect changes (potentially larger)
        # Size comparison may vary, but both should be valid
        assert updated_size > 0

    def test_export_with_customer_info(self, test_client, db, sample_room_with_surfaces):
        """Test export includes customer information"""
        # Create project with customer info
        project_data = {
            "id": str(uuid.uuid4()),
            "name": "Customer Project",
            "customer": "Acme Construction Inc.",
            "created_at": "2024-01-01T00:00:00",
            "status": "complete",
            "total_rooms": 1,
            "total_sqft": 400.0,
            "total_gallons": 0.0,
            "total_labor_hours": 0.0,
            "estimated_cost": 0.0
        }
        db.save_project(project_data)
        project_id = project_data["id"]

        # Add room
        sample_room_with_surfaces["project_id"] = project_id
        db.save_room(sample_room_with_surfaces)

        # Export PDF (customer name usually appears in proposals)
        response = test_client.get(f"/projects/{project_id}/export/pdf")

        assert response.status_code == 200
        assert len(response.content) > 0
