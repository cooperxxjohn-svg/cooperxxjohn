#!/usr/bin/env python3
"""
Quick test script to verify S3 setup
Run this to check if S3 is configured correctly
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))


def test_environment_variables():
    """Test if all required environment variables are set"""
    print("🔍 Checking environment variables...")

    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_REGION',
        'AWS_S3_BUCKET_UPLOADS',
        'AWS_S3_BUCKET_EXPORTS'
    ]

    optional_vars = [
        'S3_SIGNED_URL_EXPIRY'
    ]

    all_ok = True

    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'KEY' in var or 'SECRET' in var:
                display_value = value[:8] + '...' if len(value) > 8 else '***'
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: Not set")
            all_ok = False

    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {value}")
        else:
            print(f"  ⚠️  {var}: Not set (using default)")

    return all_ok


def test_boto3_import():
    """Test if boto3 is installed"""
    print("\n🔍 Checking boto3 installation...")

    try:
        import boto3
        print(f"  ✅ boto3 version: {boto3.__version__}")
        return True
    except ImportError:
        print("  ❌ boto3 not installed")
        print("     Run: pip install boto3")
        return False


def test_s3_service_import():
    """Test if S3 service can be imported"""
    print("\n🔍 Checking S3 service import...")

    try:
        from s3_service import S3Service
        print("  ✅ s3_service.py imports successfully")
        return True
    except Exception as e:
        print(f"  ❌ Failed to import s3_service: {e}")
        return False


def test_s3_connection():
    """Test S3 connection"""
    print("\n🔍 Testing S3 connection...")

    try:
        from s3_service import S3Service

        s3 = S3Service()
        print(f"  ✅ S3 client initialized")
        print(f"     Region: {s3.aws_region}")
        print(f"     Uploads bucket: {s3.bucket_uploads}")
        print(f"     Exports bucket: {s3.bucket_exports}")
        print(f"     Signed URL expiry: {s3.signed_url_expiry}s ({s3.signed_url_expiry // 3600}h)")

        return True

    except ValueError as e:
        print(f"  ❌ Configuration error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Connection failed: {e}")
        return False


def test_bucket_access():
    """Test if buckets are accessible"""
    print("\n🔍 Testing bucket access...")

    try:
        from s3_service import S3Service

        s3 = S3Service()

        # Test uploads bucket
        try:
            files = s3.list_files(prefix="", max_keys=1)
            print(f"  ✅ Uploads bucket accessible ({s3.bucket_uploads})")
        except Exception as e:
            print(f"  ❌ Uploads bucket error: {e}")
            return False

        # Test exports bucket
        try:
            files = s3.list_files(prefix="", bucket=s3.bucket_exports, max_keys=1)
            print(f"  ✅ Exports bucket accessible ({s3.bucket_exports})")
        except Exception as e:
            print(f"  ❌ Exports bucket error: {e}")
            return False

        return True

    except Exception as e:
        print(f"  ❌ Bucket access test failed: {e}")
        return False


def test_file_operations():
    """Test basic file operations"""
    print("\n🔍 Testing file operations...")

    try:
        from s3_service import S3Service
        import tempfile

        s3 = S3Service()

        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test file for S3 verification\n")
            test_file = f.name

        try:
            # Test upload
            s3_key = "test/verification-test.txt"
            print(f"  📤 Uploading test file to {s3_key}...")

            result = s3.upload_file(
                file_path=test_file,
                s3_key=s3_key,
                metadata={'test': 'true'}
            )
            print(f"  ✅ Upload successful ({result['size']} bytes)")

            # Test signed URL generation
            print(f"  🔗 Generating signed URL...")
            url = s3.generate_signed_url(s3_key, expiry=3600)
            print(f"  ✅ Signed URL generated (expires in 1 hour)")

            # Test file exists
            if s3.file_exists(s3_key):
                print(f"  ✅ File exists check passed")
            else:
                print(f"  ❌ File exists check failed")
                return False

            # Test metadata
            metadata = s3.get_file_metadata(s3_key)
            if metadata and metadata['metadata'].get('test') == 'true':
                print(f"  ✅ Metadata check passed")
            else:
                print(f"  ❌ Metadata check failed")
                return False

            # Clean up: delete test file
            print(f"  🗑️  Cleaning up test file...")
            s3.delete_file(s3_key)

            if not s3.file_exists(s3_key):
                print(f"  ✅ File deleted successfully")
            else:
                print(f"  ⚠️  File still exists after deletion")

            return True

        finally:
            # Clean up local temp file
            if os.path.exists(test_file):
                os.unlink(test_file)

    except Exception as e:
        print(f"  ❌ File operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("S3 Setup Verification Script")
    print("=" * 70)

    # Load environment variables from .env file
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ Loaded environment from {env_path}\n")
        else:
            print(f"⚠️  No .env file found at {env_path}")
            print("   Make sure to set environment variables!\n")
    except ImportError:
        print("⚠️  python-dotenv not installed, skipping .env file\n")

    results = {
        "Environment Variables": test_environment_variables(),
        "boto3 Installation": test_boto3_import(),
        "S3 Service Import": test_s3_service_import(),
        "S3 Connection": test_s3_connection(),
        "Bucket Access": test_bucket_access(),
        "File Operations": test_file_operations()
    }

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:30s} {status}")
        if not passed:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n🎉 All tests passed! S3 is configured correctly.")
        print("\nNext steps:")
        print("  1. Run pytest tests: pytest tests/test_s3_service.py -v")
        print("  2. Integrate into main.py (see S3_INTEGRATION_GUIDE.md)")
        print("  3. Migrate local files: python migrate_local_to_s3.py")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        print("\nTroubleshooting:")
        print("  1. Check .env file has all AWS credentials")
        print("  2. Verify IAM permissions for S3 access")
        print("  3. Confirm bucket names are correct")
        print("  4. Test with AWS CLI: aws s3 ls s3://your-bucket")
        return 1


if __name__ == "__main__":
    sys.exit(main())
