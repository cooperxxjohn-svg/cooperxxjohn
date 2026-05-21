#!/usr/bin/env python3
"""
Migration Script: Local Storage to AWS S3
Migrates all files from local uploads/ directory to S3 bucket
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
import argparse

from s3_service import S3Service
from database import Database


class LocalToS3Migrator:
    """Migrate local files to S3 and update database records"""

    def __init__(
        self,
        s3_service: S3Service,
        database: Database,
        local_uploads_dir: str = "uploads",
        local_outputs_dir: str = "outputs",
        dry_run: bool = False,
        delete_after_upload: bool = False
    ):
        """
        Initialize migrator

        Args:
            s3_service: Configured S3 service
            database: Database instance
            local_uploads_dir: Path to local uploads directory
            local_outputs_dir: Path to local outputs directory
            dry_run: If True, simulate migration without uploading
            delete_after_upload: If True, delete local files after successful upload
        """
        self.s3 = s3_service
        self.db = database
        self.local_uploads_dir = Path(local_uploads_dir)
        self.local_outputs_dir = Path(local_outputs_dir)
        self.dry_run = dry_run
        self.delete_after_upload = delete_after_upload

        # Statistics
        self.stats = {
            'total_files': 0,
            'uploaded': 0,
            'skipped': 0,
            'errors': 0,
            'total_size': 0,
            'projects_updated': 0,
            'files': []
        }

    def _get_s3_key_from_local_path(self, local_path: Path, project_id: str) -> str:
        """
        Generate S3 key from local file path

        Format: {project_id}/{file_id}.{ext}

        Args:
            local_path: Local file path
            project_id: Project ID

        Returns:
            S3 key string
        """
        file_name = local_path.name
        return f"{project_id}/{file_name}"

    def scan_local_files(self) -> List[Tuple[Path, str, str]]:
        """
        Scan local uploads directory for files

        Returns:
            List of (file_path, project_id, file_type) tuples
        """
        files = []

        # Scan uploads directory (organized by project_id)
        if self.local_uploads_dir.exists():
            for project_dir in self.local_uploads_dir.iterdir():
                if project_dir.is_dir():
                    project_id = project_dir.name

                    for file_path in project_dir.glob("*"):
                        if file_path.is_file():
                            files.append((file_path, project_id, "upload"))

        print(f"📁 Found {len(files)} files in {self.local_uploads_dir}")
        return files

    def migrate_file(
        self,
        file_path: Path,
        project_id: str,
        file_type: str
    ) -> Dict[str, any]:
        """
        Migrate a single file to S3

        Args:
            file_path: Local file path
            project_id: Project ID
            file_type: "upload" or "output"

        Returns:
            Migration result dict
        """
        try:
            # Generate S3 key
            s3_key = self._get_s3_key_from_local_path(file_path, project_id)

            # Determine bucket
            bucket = self.s3.bucket_uploads if file_type == "upload" else self.s3.bucket_exports

            # Check if file already exists in S3
            if self.s3.file_exists(s3_key, bucket=bucket):
                print(f"⏭️  Skipping (already exists): {s3_key}")
                self.stats['skipped'] += 1
                return {
                    'status': 'skipped',
                    'reason': 'already_exists',
                    's3_key': s3_key,
                    'local_path': str(file_path)
                }

            file_size = file_path.stat().st_size

            if self.dry_run:
                print(f"🔍 DRY RUN: Would upload {file_path} -> s3://{bucket}/{s3_key}")
                self.stats['total_files'] += 1
                self.stats['total_size'] += file_size
                return {
                    'status': 'dry_run',
                    's3_key': s3_key,
                    'local_path': str(file_path),
                    'size': file_size
                }

            # Upload to S3
            print(f"⬆️  Uploading: {file_path} -> s3://{bucket}/{s3_key}")

            metadata = {
                'original_filename': file_path.name,
                'project_id': project_id,
                'migrated_at': datetime.utcnow().isoformat(),
                'file_type': file_type
            }

            upload_result = self.s3.upload_file(
                file_path=str(file_path),
                s3_key=s3_key,
                bucket=bucket,
                metadata=metadata
            )

            self.stats['uploaded'] += 1
            self.stats['total_size'] += file_size

            # Delete local file if requested
            if self.delete_after_upload:
                file_path.unlink()
                print(f"🗑️  Deleted local file: {file_path}")

            return {
                'status': 'uploaded',
                's3_key': s3_key,
                'bucket': bucket,
                'local_path': str(file_path),
                'size': file_size,
                'upload_result': upload_result
            }

        except Exception as e:
            print(f"❌ Error uploading {file_path}: {e}")
            self.stats['errors'] += 1
            return {
                'status': 'error',
                'local_path': str(file_path),
                'error': str(e)
            }

    def update_database_records(self, migration_results: List[Dict[str, any]]):
        """
        Update database to point to S3 keys instead of local paths

        Args:
            migration_results: List of migration result dicts
        """
        if self.dry_run:
            print("🔍 DRY RUN: Skipping database updates")
            return

        print("\n📝 Updating database records...")

        # Group files by project
        projects_to_update = {}

        for result in migration_results:
            if result['status'] != 'uploaded':
                continue

            # Extract file_id from s3_key (format: project_id/file_id.ext)
            s3_key = result['s3_key']
            parts = s3_key.split('/')
            if len(parts) != 2:
                continue

            project_id = parts[0]
            file_name = parts[1]
            file_id = file_name.split('.')[0]  # Remove extension

            if project_id not in projects_to_update:
                projects_to_update[project_id] = []

            projects_to_update[project_id].append({
                'file_id': file_id,
                's3_key': s3_key,
                'bucket': result['bucket']
            })

        # Update each project
        for project_id, files in projects_to_update.items():
            try:
                project = self.db.get_project(project_id)
                if not project:
                    print(f"⚠️  Project not found: {project_id}")
                    continue

                # Update upload records with S3 keys
                if 'uploads' in project:
                    for file_info in files:
                        file_id = file_info['file_id']
                        if file_id in project['uploads']:
                            project['uploads'][file_id]['s3_key'] = file_info['s3_key']
                            project['uploads'][file_id]['s3_bucket'] = file_info['bucket']
                            project['uploads'][file_id]['storage'] = 's3'
                            project['uploads'][file_id]['migrated_at'] = datetime.utcnow().isoformat()

                    self.db.update_project(project_id, {'uploads': project['uploads']})
                    self.stats['projects_updated'] += 1
                    print(f"✅ Updated project: {project_id} ({len(files)} files)")

            except Exception as e:
                print(f"❌ Error updating project {project_id}: {e}")

    def verify_migration(self, migration_results: List[Dict[str, any]]) -> bool:
        """
        Verify all files were migrated successfully

        Args:
            migration_results: List of migration results

        Returns:
            True if all files verified successfully
        """
        print("\n🔍 Verifying migration...")

        all_verified = True

        for result in migration_results:
            if result['status'] == 'uploaded':
                s3_key = result['s3_key']
                bucket = result['bucket']

                # Check if file exists in S3
                if not self.s3.file_exists(s3_key, bucket=bucket):
                    print(f"❌ Verification failed: s3://{bucket}/{s3_key} not found")
                    all_verified = False
                else:
                    # Get metadata and verify size
                    metadata = self.s3.get_file_metadata(s3_key, bucket=bucket)
                    if metadata and metadata['size'] == result['size']:
                        print(f"✅ Verified: s3://{bucket}/{s3_key} ({metadata['size']} bytes)")
                    else:
                        print(f"⚠️  Size mismatch: {s3_key}")
                        all_verified = False

        return all_verified

    def run_migration(self) -> Dict[str, any]:
        """
        Run complete migration process

        Returns:
            Migration statistics
        """
        print("🚀 Starting Local to S3 Migration")
        print("=" * 60)

        if self.dry_run:
            print("🔍 DRY RUN MODE - No files will be uploaded")
            print("=" * 60)

        # Scan for files
        files_to_migrate = self.scan_local_files()

        if not files_to_migrate:
            print("✅ No files to migrate")
            return self.stats

        self.stats['total_files'] = len(files_to_migrate)

        # Migrate each file
        print(f"\n📤 Migrating {len(files_to_migrate)} files...")
        migration_results = []

        for file_path, project_id, file_type in files_to_migrate:
            result = self.migrate_file(file_path, project_id, file_type)
            migration_results.append(result)
            self.stats['files'].append(result)

        # Update database
        if not self.dry_run:
            self.update_database_records(migration_results)

            # Verify migration
            all_verified = self.verify_migration(migration_results)

            if all_verified:
                print("\n✅ All files verified successfully!")
            else:
                print("\n⚠️  Some files failed verification")

        # Print summary
        print("\n" + "=" * 60)
        print("📊 Migration Summary")
        print("=" * 60)
        print(f"Total files:         {self.stats['total_files']}")
        print(f"Uploaded:            {self.stats['uploaded']}")
        print(f"Skipped:             {self.stats['skipped']}")
        print(f"Errors:              {self.stats['errors']}")
        print(f"Total size:          {self.stats['total_size'] / (1024*1024):.2f} MB")
        print(f"Projects updated:    {self.stats['projects_updated']}")

        if self.dry_run:
            print("\n🔍 This was a DRY RUN - no files were uploaded")
            print("   Run without --dry-run to perform actual migration")

        return self.stats


def main():
    """Main migration script"""
    parser = argparse.ArgumentParser(
        description="Migrate local files to AWS S3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (preview what will be migrated)
  python migrate_local_to_s3.py --dry-run

  # Migrate files to S3
  python migrate_local_to_s3.py

  # Migrate and delete local files after upload
  python migrate_local_to_s3.py --delete-local

  # Custom directories
  python migrate_local_to_s3.py --uploads-dir custom/uploads --outputs-dir custom/outputs
        """
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate migration without uploading files'
    )

    parser.add_argument(
        '--delete-local',
        action='store_true',
        help='Delete local files after successful upload'
    )

    parser.add_argument(
        '--uploads-dir',
        default='uploads',
        help='Local uploads directory (default: uploads)'
    )

    parser.add_argument(
        '--outputs-dir',
        default='outputs',
        help='Local outputs directory (default: outputs)'
    )

    args = parser.parse_args()

    # Initialize services
    try:
        print("🔧 Initializing services...")
        s3_service = S3Service()
        database = Database()

        print(f"✅ S3 service configured")
        print(f"   Uploads bucket: {s3_service.bucket_uploads}")
        print(f"   Exports bucket: {s3_service.bucket_exports}")
        print(f"   Region: {s3_service.aws_region}")

    except Exception as e:
        print(f"❌ Failed to initialize services: {e}")
        print("\nMake sure environment variables are set:")
        print("  - AWS_ACCESS_KEY_ID")
        print("  - AWS_SECRET_ACCESS_KEY")
        print("  - AWS_REGION")
        print("  - AWS_S3_BUCKET_UPLOADS")
        print("  - AWS_S3_BUCKET_EXPORTS")
        sys.exit(1)

    # Run migration
    migrator = LocalToS3Migrator(
        s3_service=s3_service,
        database=database,
        local_uploads_dir=args.uploads_dir,
        local_outputs_dir=args.outputs_dir,
        dry_run=args.dry_run,
        delete_after_upload=args.delete_local
    )

    stats = migrator.run_migration()

    # Exit with error code if there were errors
    if stats['errors'] > 0:
        sys.exit(1)

    print("\n✅ Migration complete!")


if __name__ == "__main__":
    main()
