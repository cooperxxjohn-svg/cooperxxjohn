"""
AWS S3 Service for File Storage
Handles uploads, downloads, signed URLs, and file management
"""

import os
import boto3
import mimetypes
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from pathlib import Path
from botocore.exceptions import ClientError, NoCredentialsError
import logging

logger = logging.getLogger(__name__)


class S3Service:
    """AWS S3 service for secure file storage and retrieval"""

    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: Optional[str] = None,
        bucket_uploads: Optional[str] = None,
        bucket_exports: Optional[str] = None,
        signed_url_expiry: int = 86400  # 24 hours default
    ):
        """
        Initialize S3 service

        Args:
            aws_access_key_id: AWS access key (defaults to env var)
            aws_secret_access_key: AWS secret key (defaults to env var)
            aws_region: AWS region (defaults to env var)
            bucket_uploads: S3 bucket for uploads (defaults to env var)
            bucket_exports: S3 bucket for exports (defaults to env var)
            signed_url_expiry: Signed URL expiration in seconds (default: 24 hours)
        """
        self.aws_access_key_id = aws_access_key_id or os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = aws_secret_access_key or os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = aws_region or os.getenv("AWS_REGION", "us-east-1")
        self.bucket_uploads = bucket_uploads or os.getenv("AWS_S3_BUCKET_UPLOADS")
        self.bucket_exports = bucket_exports or os.getenv("AWS_S3_BUCKET_EXPORTS")
        self.signed_url_expiry = int(os.getenv("S3_SIGNED_URL_EXPIRY", signed_url_expiry))

        # Validate required configuration
        if not all([self.aws_access_key_id, self.aws_secret_access_key]):
            raise ValueError(
                "AWS credentials not configured. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY"
            )

        if not self.bucket_uploads:
            raise ValueError("Upload bucket not configured. Set AWS_S3_BUCKET_UPLOADS")

        if not self.bucket_exports:
            raise ValueError("Export bucket not configured. Set AWS_S3_BUCKET_EXPORTS")

        # Initialize S3 client
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.aws_region
            )
            logger.info(f"S3 client initialized for region {self.aws_region}")
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            raise

    def _get_content_type(self, file_path: str) -> str:
        """
        Detect content type from file extension

        Args:
            file_path: Path to file

        Returns:
            MIME type string
        """
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type:
            return content_type

        # Fallback for common types
        ext = Path(file_path).suffix.lower()
        content_types = {
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.json': 'application/json',
        }
        return content_types.get(ext, 'application/octet-stream')

    def upload_file(
        self,
        file_path: str,
        s3_key: str,
        bucket: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Upload file to S3

        Args:
            file_path: Local path to file
            s3_key: S3 object key (e.g., "project_id/file_id.pdf")
            bucket: S3 bucket name (defaults to uploads bucket)
            metadata: Optional metadata to attach to file
            content_type: Optional content type (auto-detected if not provided)

        Returns:
            Dict with s3_key, bucket, url, and size

        Raises:
            FileNotFoundError: If local file doesn't exist
            ClientError: If S3 upload fails
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        bucket = bucket or self.bucket_uploads
        content_type = content_type or self._get_content_type(file_path)

        try:
            file_size = os.path.getsize(file_path)

            # Prepare upload arguments
            extra_args = {
                'ContentType': content_type,
            }

            if metadata:
                extra_args['Metadata'] = metadata

            # Upload file
            self.s3_client.upload_file(
                file_path,
                bucket,
                s3_key,
                ExtraArgs=extra_args
            )

            logger.info(f"Uploaded {file_path} to s3://{bucket}/{s3_key}")

            return {
                's3_key': s3_key,
                'bucket': bucket,
                'url': f"s3://{bucket}/{s3_key}",
                'size': file_size,
                'content_type': content_type,
                'uploaded_at': datetime.utcnow().isoformat()
            }

        except ClientError as e:
            logger.error(f"Failed to upload {file_path} to S3: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error uploading to S3: {e}")
            raise

    def upload_file_obj(
        self,
        file_obj,
        s3_key: str,
        bucket: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
        content_type: str = 'application/octet-stream'
    ) -> Dict[str, str]:
        """
        Upload file object (BytesIO, file handle) to S3

        Args:
            file_obj: File-like object
            s3_key: S3 object key
            bucket: S3 bucket name (defaults to uploads bucket)
            metadata: Optional metadata
            content_type: Content type

        Returns:
            Dict with s3_key, bucket, and url
        """
        bucket = bucket or self.bucket_uploads

        try:
            extra_args = {'ContentType': content_type}
            if metadata:
                extra_args['Metadata'] = metadata

            self.s3_client.upload_fileobj(
                file_obj,
                bucket,
                s3_key,
                ExtraArgs=extra_args
            )

            logger.info(f"Uploaded file object to s3://{bucket}/{s3_key}")

            return {
                's3_key': s3_key,
                'bucket': bucket,
                'url': f"s3://{bucket}/{s3_key}",
                'content_type': content_type,
                'uploaded_at': datetime.utcnow().isoformat()
            }

        except ClientError as e:
            logger.error(f"Failed to upload file object to S3: {e}")
            raise

    def generate_signed_url(
        self,
        s3_key: str,
        bucket: Optional[str] = None,
        expiry: Optional[int] = None,
        download_filename: Optional[str] = None
    ) -> str:
        """
        Generate signed URL for secure file download

        Args:
            s3_key: S3 object key
            bucket: S3 bucket name (defaults to uploads bucket)
            expiry: URL expiration in seconds (defaults to 24 hours)
            download_filename: Optional filename for Content-Disposition header

        Returns:
            Signed URL string (valid for expiry seconds)

        Raises:
            ClientError: If URL generation fails
        """
        bucket = bucket or self.bucket_uploads
        expiry = expiry or self.signed_url_expiry

        try:
            params = {
                'Bucket': bucket,
                'Key': s3_key
            }

            # Add Content-Disposition header for custom filename
            if download_filename:
                params['ResponseContentDisposition'] = f'attachment; filename="{download_filename}"'

            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expiry
            )

            logger.info(f"Generated signed URL for s3://{bucket}/{s3_key} (expires in {expiry}s)")
            return url

        except ClientError as e:
            logger.error(f"Failed to generate signed URL: {e}")
            raise

    def delete_file(
        self,
        s3_key: str,
        bucket: Optional[str] = None
    ) -> bool:
        """
        Delete file from S3

        Args:
            s3_key: S3 object key
            bucket: S3 bucket name (defaults to uploads bucket)

        Returns:
            True if successful

        Raises:
            ClientError: If deletion fails
        """
        bucket = bucket or self.bucket_uploads

        try:
            self.s3_client.delete_object(
                Bucket=bucket,
                Key=s3_key
            )

            logger.info(f"Deleted s3://{bucket}/{s3_key}")
            return True

        except ClientError as e:
            logger.error(f"Failed to delete s3://{bucket}/{s3_key}: {e}")
            raise

    def delete_files_batch(
        self,
        s3_keys: List[str],
        bucket: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """
        Delete multiple files from S3 in batch

        Args:
            s3_keys: List of S3 object keys
            bucket: S3 bucket name

        Returns:
            Dict with 'deleted' and 'errors' lists
        """
        bucket = bucket or self.bucket_uploads
        deleted = []
        errors = []

        if not s3_keys:
            return {'deleted': deleted, 'errors': errors}

        try:
            # S3 batch delete (max 1000 objects)
            objects = [{'Key': key} for key in s3_keys[:1000]]

            response = self.s3_client.delete_objects(
                Bucket=bucket,
                Delete={'Objects': objects}
            )

            # Track deleted objects
            if 'Deleted' in response:
                deleted = [obj['Key'] for obj in response['Deleted']]

            # Track errors
            if 'Errors' in response:
                errors = [
                    {'key': err['Key'], 'message': err['Message']}
                    for err in response['Errors']
                ]

            logger.info(f"Batch deleted {len(deleted)} files from s3://{bucket}")

            return {'deleted': deleted, 'errors': errors}

        except ClientError as e:
            logger.error(f"Failed to batch delete files: {e}")
            raise

    def list_files(
        self,
        prefix: str = "",
        bucket: Optional[str] = None,
        max_keys: int = 1000
    ) -> List[Dict[str, any]]:
        """
        List files in S3 bucket with optional prefix

        Args:
            prefix: S3 key prefix (e.g., "project_id/")
            bucket: S3 bucket name (defaults to uploads bucket)
            max_keys: Maximum number of keys to return

        Returns:
            List of file metadata dicts with key, size, last_modified
        """
        bucket = bucket or self.bucket_uploads

        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
                MaxKeys=max_keys
            )

            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    files.append({
                        'key': obj['Key'],
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'].isoformat(),
                        'etag': obj['ETag'].strip('"')
                    })

            logger.info(f"Listed {len(files)} files from s3://{bucket}/{prefix}")
            return files

        except ClientError as e:
            logger.error(f"Failed to list files: {e}")
            raise

    def file_exists(
        self,
        s3_key: str,
        bucket: Optional[str] = None
    ) -> bool:
        """
        Check if file exists in S3

        Args:
            s3_key: S3 object key
            bucket: S3 bucket name

        Returns:
            True if file exists, False otherwise
        """
        bucket = bucket or self.bucket_uploads

        try:
            self.s3_client.head_object(Bucket=bucket, Key=s3_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            raise

    def get_file_metadata(
        self,
        s3_key: str,
        bucket: Optional[str] = None
    ) -> Optional[Dict[str, any]]:
        """
        Get file metadata from S3

        Args:
            s3_key: S3 object key
            bucket: S3 bucket name

        Returns:
            Dict with metadata or None if not found
        """
        bucket = bucket or self.bucket_uploads

        try:
            response = self.s3_client.head_object(Bucket=bucket, Key=s3_key)

            return {
                'key': s3_key,
                'bucket': bucket,
                'size': response['ContentLength'],
                'content_type': response.get('ContentType'),
                'last_modified': response['LastModified'].isoformat(),
                'etag': response['ETag'].strip('"'),
                'metadata': response.get('Metadata', {})
            }

        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"File not found: s3://{bucket}/{s3_key}")
                return None
            logger.error(f"Failed to get file metadata: {e}")
            raise

    def cleanup_old_files(
        self,
        days: int = 90,
        prefix: str = "",
        bucket: Optional[str] = None,
        dry_run: bool = True
    ) -> Dict[str, any]:
        """
        Delete files older than specified days (retention policy)

        Args:
            days: Delete files older than this many days
            prefix: S3 key prefix to filter files
            bucket: S3 bucket name
            dry_run: If True, only list files without deleting

        Returns:
            Dict with count, files, and deleted status
        """
        bucket = bucket or self.bucket_uploads
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        try:
            files = self.list_files(prefix=prefix, bucket=bucket)

            old_files = [
                f for f in files
                if datetime.fromisoformat(f['last_modified'].replace('Z', '+00:00')) < cutoff_date
            ]

            if not old_files:
                logger.info(f"No files older than {days} days found")
                return {
                    'count': 0,
                    'files': [],
                    'dry_run': dry_run,
                    'deleted': False
                }

            result = {
                'count': len(old_files),
                'files': [f['key'] for f in old_files],
                'dry_run': dry_run,
                'total_size': sum(f['size'] for f in old_files)
            }

            if not dry_run:
                # Actually delete files
                delete_result = self.delete_files_batch(
                    s3_keys=[f['key'] for f in old_files],
                    bucket=bucket
                )
                result['deleted'] = len(delete_result['deleted'])
                result['errors'] = delete_result['errors']
                logger.info(f"Deleted {result['deleted']} old files from s3://{bucket}")
            else:
                logger.info(f"Dry run: Would delete {len(old_files)} files older than {days} days")

            return result

        except ClientError as e:
            logger.error(f"Failed to cleanup old files: {e}")
            raise


def get_s3_service() -> S3Service:
    """
    Factory function to get S3 service instance

    Returns:
        Configured S3Service instance
    """
    return S3Service()


if __name__ == "__main__":
    # Test S3 service
    import sys

    logging.basicConfig(level=logging.INFO)

    try:
        s3 = get_s3_service()
        print(f"✅ S3 service initialized")
        print(f"   Region: {s3.aws_region}")
        print(f"   Uploads bucket: {s3.bucket_uploads}")
        print(f"   Exports bucket: {s3.bucket_exports}")
        print(f"   Signed URL expiry: {s3.signed_url_expiry}s")

    except Exception as e:
        print(f"❌ Failed to initialize S3 service: {e}")
        print("\nMake sure to set environment variables:")
        print("  - AWS_ACCESS_KEY_ID")
        print("  - AWS_SECRET_ACCESS_KEY")
        print("  - AWS_REGION")
        print("  - AWS_S3_BUCKET_UPLOADS")
        print("  - AWS_S3_BUCKET_EXPORTS")
        sys.exit(1)
