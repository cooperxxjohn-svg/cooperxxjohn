"""
Tests for S3 Service
Uses moto library to mock AWS S3 operations
"""

import pytest
import os
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from io import BytesIO

# Mock AWS with moto
from moto import mock_aws
import boto3

from s3_service import S3Service


@pytest.fixture
def aws_credentials():
    """Mock AWS credentials for testing"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_REGION'] = 'us-east-1'
    os.environ['AWS_S3_BUCKET_UPLOADS'] = 'test-uploads'
    os.environ['AWS_S3_BUCKET_EXPORTS'] = 'test-exports'
    os.environ['S3_SIGNED_URL_EXPIRY'] = '3600'


@pytest.fixture
def s3_buckets(aws_credentials):
    """Create mock S3 buckets"""
    with mock_aws():
        # Create S3 client
        s3_client = boto3.client('s3', region_name='us-east-1')

        # Create test buckets
        s3_client.create_bucket(Bucket='test-uploads')
        s3_client.create_bucket(Bucket='test-exports')

        yield s3_client


@pytest.fixture
def s3_service(s3_buckets):
    """Get S3 service instance with mocked S3"""
    service = S3Service()
    return service


@pytest.fixture
def temp_file():
    """Create temporary test file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Test file content\n" * 100)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def temp_pdf():
    """Create temporary PDF file"""
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.pdf', delete=False) as f:
        # Write minimal PDF header
        f.write(b'%PDF-1.4\n')
        f.write(b'Test PDF content\n')
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


class TestS3ServiceInitialization:
    """Test S3 service initialization"""

    def test_initialization_success(self, s3_buckets):
        """Test successful S3 service initialization"""
        service = S3Service()

        assert service.aws_region == 'us-east-1'
        assert service.bucket_uploads == 'test-uploads'
        assert service.bucket_exports == 'test-exports'
        assert service.signed_url_expiry == 3600
        assert service.s3_client is not None

    def test_initialization_without_credentials(self):
        """Test initialization fails without credentials"""
        # Remove credentials
        old_key = os.environ.pop('AWS_ACCESS_KEY_ID', None)
        old_secret = os.environ.pop('AWS_SECRET_ACCESS_KEY', None)

        with pytest.raises(ValueError, match="AWS credentials not configured"):
            S3Service()

        # Restore
        if old_key:
            os.environ['AWS_ACCESS_KEY_ID'] = old_key
        if old_secret:
            os.environ['AWS_SECRET_ACCESS_KEY'] = old_secret

    def test_initialization_without_bucket(self, aws_credentials):
        """Test initialization fails without bucket configuration"""
        old_bucket = os.environ.pop('AWS_S3_BUCKET_UPLOADS', None)

        with pytest.raises(ValueError, match="Upload bucket not configured"):
            S3Service()

        # Restore
        if old_bucket:
            os.environ['AWS_S3_BUCKET_UPLOADS'] = old_bucket


class TestS3FileUpload:
    """Test file upload operations"""

    def test_upload_file_success(self, s3_service, temp_file):
        """Test successful file upload"""
        s3_key = "test-project/test-file.txt"

        result = s3_service.upload_file(
            file_path=temp_file,
            s3_key=s3_key
        )

        assert result['s3_key'] == s3_key
        assert result['bucket'] == 'test-uploads'
        assert result['size'] > 0
        assert result['content_type'] == 'text/plain'
        assert 'uploaded_at' in result

    def test_upload_pdf_file(self, s3_service, temp_pdf):
        """Test PDF file upload with correct content type"""
        s3_key = "test-project/floor-plan.pdf"

        result = s3_service.upload_file(
            file_path=temp_pdf,
            s3_key=s3_key
        )

        assert result['s3_key'] == s3_key
        assert result['content_type'] == 'application/pdf'

    def test_upload_file_with_metadata(self, s3_service, temp_file):
        """Test file upload with custom metadata"""
        s3_key = "test-project/test-file.txt"
        metadata = {
            'project_id': 'test-123',
            'user_id': 'user-456',
            'original_filename': 'floor-plan.pdf'
        }

        result = s3_service.upload_file(
            file_path=temp_file,
            s3_key=s3_key,
            metadata=metadata
        )

        assert result['s3_key'] == s3_key

        # Verify metadata was stored
        file_metadata = s3_service.get_file_metadata(s3_key)
        assert file_metadata['metadata'] == metadata

    def test_upload_file_not_found(self, s3_service):
        """Test upload fails for non-existent file"""
        with pytest.raises(FileNotFoundError):
            s3_service.upload_file(
                file_path="/nonexistent/file.txt",
                s3_key="test/file.txt"
            )

    def test_upload_to_exports_bucket(self, s3_service, temp_file):
        """Test upload to exports bucket"""
        s3_key = "test-project/export.xlsx"

        result = s3_service.upload_file(
            file_path=temp_file,
            s3_key=s3_key,
            bucket='test-exports'
        )

        assert result['bucket'] == 'test-exports'

    def test_upload_file_object(self, s3_service):
        """Test upload from file-like object"""
        file_obj = BytesIO(b"Test content from BytesIO")
        s3_key = "test-project/bytes-file.txt"

        result = s3_service.upload_file_obj(
            file_obj=file_obj,
            s3_key=s3_key,
            content_type='text/plain'
        )

        assert result['s3_key'] == s3_key
        assert result['content_type'] == 'text/plain'


class TestS3SignedURLs:
    """Test signed URL generation"""

    def test_generate_signed_url(self, s3_service, temp_file):
        """Test signed URL generation"""
        s3_key = "test-project/test-file.txt"

        # Upload file first
        s3_service.upload_file(file_path=temp_file, s3_key=s3_key)

        # Generate signed URL
        url = s3_service.generate_signed_url(s3_key=s3_key)

        assert url is not None
        assert 'test-uploads' in url
        assert s3_key in url
        assert 'X-Amz-Signature' in url  # AWS signature present

    def test_generate_signed_url_with_custom_expiry(self, s3_service, temp_file):
        """Test signed URL with custom expiration"""
        s3_key = "test-project/test-file.txt"
        s3_service.upload_file(file_path=temp_file, s3_key=s3_key)

        # Generate URL with 1 hour expiry
        url = s3_service.generate_signed_url(s3_key=s3_key, expiry=3600)

        assert url is not None
        assert 'X-Amz-Expires=3600' in url

    def test_generate_signed_url_with_filename(self, s3_service, temp_file):
        """Test signed URL with custom download filename"""
        s3_key = "test-project/test-file.txt"
        s3_service.upload_file(file_path=temp_file, s3_key=s3_key)

        url = s3_service.generate_signed_url(
            s3_key=s3_key,
            download_filename="Custom-Filename.txt"
        )

        assert url is not None
        assert 'response-content-disposition' in url


class TestS3FileDeletion:
    """Test file deletion operations"""

    def test_delete_file(self, s3_service, temp_file):
        """Test file deletion"""
        s3_key = "test-project/test-file.txt"

        # Upload file
        s3_service.upload_file(file_path=temp_file, s3_key=s3_key)

        # Verify exists
        assert s3_service.file_exists(s3_key)

        # Delete file
        result = s3_service.delete_file(s3_key)

        assert result is True
        assert not s3_service.file_exists(s3_key)

    def test_delete_files_batch(self, s3_service, temp_file):
        """Test batch file deletion"""
        # Upload multiple files
        s3_keys = [
            "test-project/file1.txt",
            "test-project/file2.txt",
            "test-project/file3.txt"
        ]

        for s3_key in s3_keys:
            s3_service.upload_file(file_path=temp_file, s3_key=s3_key)

        # Delete batch
        result = s3_service.delete_files_batch(s3_keys)

        assert len(result['deleted']) == 3
        assert len(result['errors']) == 0

        # Verify all deleted
        for s3_key in s3_keys:
            assert not s3_service.file_exists(s3_key)

    def test_delete_files_batch_empty_list(self, s3_service):
        """Test batch delete with empty list"""
        result = s3_service.delete_files_batch([])

        assert result['deleted'] == []
        assert result['errors'] == []


class TestS3FileOperations:
    """Test file listing and metadata operations"""

    def test_file_exists(self, s3_service, temp_file):
        """Test file existence check"""
        s3_key = "test-project/test-file.txt"

        # Should not exist initially
        assert not s3_service.file_exists(s3_key)

        # Upload file
        s3_service.upload_file(file_path=temp_file, s3_key=s3_key)

        # Should exist now
        assert s3_service.file_exists(s3_key)

    def test_get_file_metadata(self, s3_service, temp_file):
        """Test file metadata retrieval"""
        s3_key = "test-project/test-file.txt"
        metadata = {'project_id': 'test-123'}

        s3_service.upload_file(
            file_path=temp_file,
            s3_key=s3_key,
            metadata=metadata
        )

        file_meta = s3_service.get_file_metadata(s3_key)

        assert file_meta is not None
        assert file_meta['key'] == s3_key
        assert file_meta['bucket'] == 'test-uploads'
        assert file_meta['size'] > 0
        assert file_meta['content_type'] == 'text/plain'
        assert 'last_modified' in file_meta
        assert file_meta['metadata'] == metadata

    def test_get_file_metadata_not_found(self, s3_service):
        """Test metadata retrieval for non-existent file"""
        metadata = s3_service.get_file_metadata("nonexistent/file.txt")
        assert metadata is None

    def test_list_files(self, s3_service, temp_file):
        """Test file listing"""
        # Upload multiple files
        s3_keys = [
            "project-1/file1.txt",
            "project-1/file2.txt",
            "project-2/file3.txt"
        ]

        for s3_key in s3_keys:
            s3_service.upload_file(file_path=temp_file, s3_key=s3_key)

        # List all files
        all_files = s3_service.list_files()
        assert len(all_files) == 3

        # List files with prefix
        project1_files = s3_service.list_files(prefix="project-1/")
        assert len(project1_files) == 2

        # Verify file structure
        for file in project1_files:
            assert 'key' in file
            assert 'size' in file
            assert 'last_modified' in file
            assert file['key'].startswith('project-1/')

    def test_list_files_empty_bucket(self, s3_service):
        """Test listing files in empty bucket"""
        files = s3_service.list_files()
        assert files == []


class TestS3ContentTypes:
    """Test content type detection"""

    def test_content_type_detection(self, s3_service):
        """Test content type detection for various file types"""
        test_cases = [
            ('test.pdf', 'application/pdf'),
            ('test.png', 'image/png'),
            ('test.jpg', 'image/jpeg'),
            ('test.jpeg', 'image/jpeg'),
            ('test.xlsx', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('test.json', 'application/json'),
            ('test.txt', 'text/plain'),
            ('test.unknown', 'application/octet-stream'),  # Fallback
        ]

        for filename, expected_type in test_cases:
            detected = s3_service._get_content_type(filename)
            assert detected == expected_type, f"Failed for {filename}"


class TestS3Cleanup:
    """Test file cleanup and retention policies"""

    def test_cleanup_old_files_dry_run(self, s3_service, temp_file, s3_buckets):
        """Test cleanup old files in dry run mode"""
        # Upload test file
        s3_key = "test-project/old-file.txt"
        s3_service.upload_file(file_path=temp_file, s3_key=s3_key)

        # Modify object's last modified date (simulate old file)
        # Note: In real S3, we'd wait or use lifecycle policies
        # For testing, we check the dry_run logic

        result = s3_service.cleanup_old_files(days=90, dry_run=True)

        assert 'count' in result
        assert 'files' in result
        assert result['dry_run'] is True

    def test_cleanup_old_files_with_prefix(self, s3_service, temp_file):
        """Test cleanup with prefix filter"""
        # Upload files to different projects
        s3_service.upload_file(file_path=temp_file, s3_key="project-1/file.txt")
        s3_service.upload_file(file_path=temp_file, s3_key="project-2/file.txt")

        result = s3_service.cleanup_old_files(
            days=90,
            prefix="project-1/",
            dry_run=True
        )

        # Should only consider project-1 files
        assert all('project-1/' in f for f in result['files'])


class TestS3ErrorHandling:
    """Test error handling"""

    def test_upload_with_invalid_bucket(self, s3_service, temp_file):
        """Test upload to non-existent bucket"""
        with pytest.raises(Exception):  # ClientError from boto3
            s3_service.upload_file(
                file_path=temp_file,
                s3_key="test/file.txt",
                bucket="nonexistent-bucket-12345"
            )

    def test_generate_signed_url_nonexistent_file(self, s3_service):
        """Test signed URL generation for non-existent file"""
        # Should still generate URL (S3 doesn't validate existence)
        url = s3_service.generate_signed_url("nonexistent/file.txt")
        assert url is not None


class TestS3Integration:
    """Integration tests combining multiple operations"""

    def test_complete_file_lifecycle(self, s3_service, temp_file):
        """Test complete file lifecycle: upload, list, get metadata, download URL, delete"""
        s3_key = "test-project/lifecycle-test.txt"

        # 1. Upload
        upload_result = s3_service.upload_file(
            file_path=temp_file,
            s3_key=s3_key,
            metadata={'test': 'lifecycle'}
        )
        assert upload_result['s3_key'] == s3_key

        # 2. Check existence
        assert s3_service.file_exists(s3_key)

        # 3. List files
        files = s3_service.list_files(prefix="test-project/")
        assert len(files) == 1
        assert files[0]['key'] == s3_key

        # 4. Get metadata
        metadata = s3_service.get_file_metadata(s3_key)
        assert metadata['key'] == s3_key
        assert metadata['metadata']['test'] == 'lifecycle'

        # 5. Generate signed URL
        url = s3_service.generate_signed_url(s3_key)
        assert url is not None

        # 6. Delete
        s3_service.delete_file(s3_key)
        assert not s3_service.file_exists(s3_key)

    def test_multi_project_organization(self, s3_service, temp_file):
        """Test file organization across multiple projects"""
        projects = ['project-a', 'project-b', 'project-c']

        # Upload files for each project
        for project in projects:
            for i in range(3):
                s3_key = f"{project}/file-{i}.txt"
                s3_service.upload_file(file_path=temp_file, s3_key=s3_key)

        # Verify each project has 3 files
        for project in projects:
            files = s3_service.list_files(prefix=f"{project}/")
            assert len(files) == 3

        # Verify total files
        all_files = s3_service.list_files()
        assert len(all_files) == 9
