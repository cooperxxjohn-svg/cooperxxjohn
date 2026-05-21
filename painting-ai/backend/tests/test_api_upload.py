"""
Integration tests for file upload endpoint
Tests: POST /projects/{id}/upload
"""

import pytest
import uuid
import io
from fastapi.testclient import TestClient


class TestFileUpload:
    """Test POST /projects/{id}/upload endpoint"""

    def test_upload_pdf_success(self, test_client, test_project):
        """Test successful PDF upload"""
        project_id = test_project["id"]

        # Create a mock PDF file
        pdf_content = b"%PDF-1.4\n%Mock PDF content for testing\n"
        files = {
            "file": ("test_drawing.pdf", io.BytesIO(pdf_content), "application/pdf")
        }

        response = test_client.post(
            f"/projects/{project_id}/upload",
            files=files
        )

        assert response.status_code == 200
        data = response.json()

        assert "file_id" in data
        assert data["filename"] == "test_drawing.pdf"
        assert data["project_id"] == project_id
        assert data["status"] == "queued"
        assert "message" in data

    def test_upload_png_success(self, test_client, test_project):
        """Test successful PNG upload"""
        project_id = test_project["id"]

        # Create a mock PNG file (simplified PNG header)
        png_content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        files = {
            "file": ("floor_plan.png", io.BytesIO(png_content), "image/png")
        }

        response = test_client.post(
            f"/projects/{project_id}/upload",
            files=files
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "floor_plan.png"

    def test_upload_jpg_success(self, test_client, test_project):
        """Test successful JPG upload"""
        project_id = test_project["id"]

        # Create a mock JPG file (simplified JPEG header)
        jpg_content = b"\xFF\xD8\xFF\xE0" + b"\x00" * 100
        files = {
            "file": ("drawing.jpg", io.BytesIO(jpg_content), "image/jpeg")
        }

        response = test_client.post(
            f"/projects/{project_id}/upload",
            files=files
        )

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "drawing.jpg"

    def test_upload_project_not_found(self, test_client):
        """Test upload to non-existent project returns 404"""
        fake_id = str(uuid.uuid4())

        pdf_content = b"%PDF-1.4\ntest content\n"
        files = {
            "file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")
        }

        response = test_client.post(
            f"/projects/{fake_id}/upload",
            files=files
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_upload_invalid_file_type(self, test_client, test_project):
        """Test uploading unsupported file type fails"""
        project_id = test_project["id"]

        # Try to upload a .txt file
        txt_content = b"This is a text file"
        files = {
            "file": ("document.txt", io.BytesIO(txt_content), "text/plain")
        }

        response = test_client.post(
            f"/projects/{project_id}/upload",
            files=files
        )

        assert response.status_code == 400
        assert "invalid file type" in response.json()["detail"].lower()

    def test_upload_empty_file(self, test_client, test_project):
        """Test uploading empty file fails"""
        project_id = test_project["id"]

        files = {
            "file": ("empty.pdf", io.BytesIO(b""), "application/pdf")
        }

        response = test_client.post(
            f"/projects/{project_id}/upload",
            files=files
        )

        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()

    def test_upload_corrupted_pdf(self, test_client, test_project):
        """Test uploading corrupted PDF fails"""
        project_id = test_project["id"]

        # Invalid PDF (doesn't start with %PDF)
        invalid_pdf = b"Not a valid PDF file"
        files = {
            "file": ("corrupted.pdf", io.BytesIO(invalid_pdf), "application/pdf")
        }

        response = test_client.post(
            f"/projects/{project_id}/upload",
            files=files
        )

        assert response.status_code == 400
        assert "corrupted" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()

    def test_upload_file_too_large(self, test_client, test_project):
        """Test uploading file exceeding size limit fails"""
        project_id = test_project["id"]

        # Create a file larger than 50MB
        large_content = b"%PDF-1.4\n" + b"x" * (51 * 1024 * 1024)
        files = {
            "file": ("huge_file.pdf", io.BytesIO(large_content), "application/pdf")
        }

        response = test_client.post(
            f"/projects/{project_id}/upload",
            files=files
        )

        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower()

    def test_upload_no_file_provided(self, test_client, test_project):
        """Test upload request without file fails"""
        project_id = test_project["id"]

        response = test_client.post(f"/projects/{project_id}/upload")

        assert response.status_code == 422

    def test_upload_updates_project_status(self, test_client, test_project, db):
        """Test that upload updates project status to processing"""
        project_id = test_project["id"]

        pdf_content = b"%PDF-1.4\ntest content\n"
        files = {
            "file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")
        }

        response = test_client.post(
            f"/projects/{project_id}/upload",
            files=files
        )

        assert response.status_code == 200

        # Check project status was updated
        project = db.get_project(project_id)
        assert project["status"] == "processing"

    def test_upload_creates_upload_record(self, test_client, test_project, db):
        """Test that upload creates upload record in project"""
        project_id = test_project["id"]

        pdf_content = b"%PDF-1.4\ntest content\n"
        files = {
            "file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")
        }

        response = test_client.post(
            f"/projects/{project_id}/upload",
            files=files
        )

        assert response.status_code == 200
        file_id = response.json()["file_id"]

        # Check upload record exists
        project = db.get_project(project_id)
        assert "uploads" in project
        assert file_id in project["uploads"]
        assert project["uploads"][file_id]["filename"] == "test.pdf"
        assert project["uploads"][file_id]["status"] == "queued"

    def test_upload_multiple_files_same_project(self, test_client, test_project):
        """Test uploading multiple files to same project"""
        project_id = test_project["id"]

        # Upload first file
        pdf_content1 = b"%PDF-1.4\nfirst file\n"
        files1 = {
            "file": ("drawing1.pdf", io.BytesIO(pdf_content1), "application/pdf")
        }
        response1 = test_client.post(
            f"/projects/{project_id}/upload",
            files=files1
        )
        assert response1.status_code == 200
        file_id1 = response1.json()["file_id"]

        # Upload second file
        pdf_content2 = b"%PDF-1.4\nsecond file\n"
        files2 = {
            "file": ("drawing2.pdf", io.BytesIO(pdf_content2), "application/pdf")
        }
        response2 = test_client.post(
            f"/projects/{project_id}/upload",
            files=files2
        )
        assert response2.status_code == 200
        file_id2 = response2.json()["file_id"]

        # Verify both files are tracked
        assert file_id1 != file_id2

    def test_upload_returns_file_metadata(self, test_client, test_project):
        """Test upload response includes file metadata"""
        project_id = test_project["id"]

        pdf_content = b"%PDF-1.4\n" + b"x" * 1000
        files = {
            "file": ("metadata_test.pdf", io.BytesIO(pdf_content), "application/pdf")
        }

        response = test_client.post(
            f"/projects/{project_id}/upload",
            files=files
        )

        assert response.status_code == 200
        data = response.json()

        assert "file_id" in data
        assert "filename" in data
        assert "file_size" in data
        assert data["file_size"] > 0
        assert "status" in data
        assert "project_id" in data


class TestUploadValidation:
    """Test file upload validation edge cases"""

    def test_upload_with_special_characters_in_filename(self, test_client, test_project):
        """Test uploading file with special characters in name"""
        project_id = test_project["id"]

        pdf_content = b"%PDF-1.4\ntest\n"
        files = {
            "file": ("test file (1) [copy].pdf", io.BytesIO(pdf_content), "application/pdf")
        }

        response = test_client.post(
            f"/projects/{project_id}/upload",
            files=files
        )

        # Should handle special characters gracefully
        assert response.status_code == 200

    def test_upload_with_unicode_filename(self, test_client, test_project):
        """Test uploading file with unicode characters in name"""
        project_id = test_project["id"]

        pdf_content = b"%PDF-1.4\ntest\n"
        files = {
            "file": ("建築図面.pdf", io.BytesIO(pdf_content), "application/pdf")
        }

        response = test_client.post(
            f"/projects/{project_id}/upload",
            files=files
        )

        # Should handle unicode filenames
        assert response.status_code in [200, 400]

    def test_upload_case_insensitive_extension(self, test_client, test_project):
        """Test that file extension check is case-insensitive"""
        project_id = test_project["id"]

        pdf_content = b"%PDF-1.4\ntest\n"
        files = {
            "file": ("UPPERCASE.PDF", io.BytesIO(pdf_content), "application/pdf")
        }

        response = test_client.post(
            f"/projects/{project_id}/upload",
            files=files
        )

        assert response.status_code == 200
