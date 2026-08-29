# AWS S3 Setup Guide for Painting.ai

Complete guide to setting up AWS S3 for secure file storage with signed URLs.

## Table of Contents

- [Overview](#overview)
- [AWS Account Setup](#aws-account-setup)
- [S3 Bucket Creation](#s3-bucket-creation)
- [IAM Permissions](#iam-permissions)
- [Environment Configuration](#environment-configuration)
- [Migration from Local Storage](#migration-from-local-storage)
- [Security Best Practices](#security-best-practices)
- [CloudFront CDN (Optional)](#cloudfront-cdn-optional)
- [Troubleshooting](#troubleshooting)

## Overview

Painting.ai uses AWS S3 for secure, scalable file storage with the following architecture:

```
Bucket Structure:
├── AWS_S3_BUCKET_UPLOADS (e.g., painting-ai-uploads-prod)
│   └── {project_id}/
│       ├── {file_id}.pdf     (uploaded floor plans)
│       ├── {file_id}.png     (uploaded images)
│       └── processed/
│           └── {file_id}_annotated.png
│
└── AWS_S3_BUCKET_EXPORTS (e.g., painting-ai-exports-prod)
    └── {project_id}/
        ├── {export_id}.xlsx  (Excel takeoffs)
        └── {export_id}.pdf   (PDF proposals)
```

**Key Features:**
- Signed URLs for secure downloads (24-hour expiration)
- Organized by project ID
- Separate buckets for uploads and exports
- 90-day file retention policy
- Content-type detection for proper file handling
- Metadata tagging for tracking

## AWS Account Setup

### Step 1: Create AWS Account

1. Go to [aws.amazon.com](https://aws.amazon.com/)
2. Click "Create an AWS Account"
3. Follow registration process (requires credit card)
4. Enable MFA (Multi-Factor Authentication) for security

### Step 2: Choose AWS Region

Select a region close to your users for better performance:
- `us-east-1` (N. Virginia) - Most services, lowest cost
- `us-west-2` (Oregon) - West Coast US
- `eu-west-1` (Ireland) - Europe
- `ap-southeast-1` (Singapore) - Asia Pacific

**Set your region in environment variables:**
```bash
AWS_REGION=us-east-1
```

## S3 Bucket Creation

### Step 3: Create S3 Buckets

You need **two buckets**: one for uploads, one for exports.

#### Option A: Using AWS Console

1. Go to [S3 Console](https://console.aws.amazon.com/s3/)
2. Click "Create bucket"

**Uploads Bucket:**
- Bucket name: `painting-ai-uploads-prod` (must be globally unique)
- Region: Match your AWS_REGION
- Block Public Access: **Enable all blocks** (keep private)
- Bucket Versioning: Disabled (optional: enable for backup)
- Default encryption: Enable SSE-S3
- Click "Create bucket"

**Exports Bucket:**
- Bucket name: `painting-ai-exports-prod`
- Same settings as uploads bucket

#### Option B: Using AWS CLI

```bash
# Create uploads bucket
aws s3 mb s3://painting-ai-uploads-prod --region us-east-1

# Create exports bucket
aws s3 mb s3://painting-ai-exports-prod --region us-east-1

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket painting-ai-uploads-prod \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

aws s3api put-bucket-encryption \
  --bucket painting-ai-exports-prod \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'
```

### Step 4: Configure CORS (for browser uploads)

If allowing direct browser uploads, configure CORS:

```json
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
    "AllowedOrigins": ["https://yourdomain.com"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
```

Apply via AWS Console:
1. Select bucket → Permissions → CORS
2. Paste JSON above
3. Replace `yourdomain.com` with your domain

## IAM Permissions

### Step 5: Create IAM User for Application

Create a dedicated IAM user with minimal permissions (principle of least privilege).

#### Option A: Using AWS Console

1. Go to [IAM Console](https://console.aws.amazon.com/iam/)
2. Users → Add users
3. User name: `painting-ai-app`
4. Access type: **Programmatic access** (not console)
5. Click "Next: Permissions"

#### Attach Policy

Create a custom policy with minimal permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "UploadsAccess",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::painting-ai-uploads-prod",
        "arn:aws:s3:::painting-ai-uploads-prod/*"
      ]
    },
    {
      "Sid": "ExportsAccess",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::painting-ai-exports-prod",
        "arn:aws:s3:::painting-ai-exports-prod/*"
      ]
    }
  ]
}
```

**Steps:**
1. Click "Create policy"
2. Select JSON tab
3. Paste policy above (replace bucket names)
4. Name: `PaintingAI-S3-Access`
5. Create policy
6. Attach to `painting-ai-app` user

#### Option B: Using AWS CLI

```bash
# Create IAM user
aws iam create-user --user-name painting-ai-app

# Create policy
aws iam create-policy \
  --policy-name PaintingAI-S3-Access \
  --policy-document file://iam-policy.json

# Attach policy to user
aws iam attach-user-policy \
  --user-name painting-ai-app \
  --policy-arn arn:aws:iam::YOUR_ACCOUNT_ID:policy/PaintingAI-S3-Access

# Create access keys
aws iam create-access-key --user-name painting-ai-app
```

### Step 6: Generate Access Keys

1. Select user `painting-ai-app`
2. Security credentials → Create access key
3. Use case: Application running on AWS compute service
4. Download CSV with:
   - Access Key ID
   - Secret Access Key

**CRITICAL: Save these credentials securely! You cannot retrieve the secret key later.**

## Environment Configuration

### Step 7: Set Environment Variables

Add to `backend/.env`:

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1

# S3 Buckets
AWS_S3_BUCKET_UPLOADS=painting-ai-uploads-prod
AWS_S3_BUCKET_EXPORTS=painting-ai-exports-prod

# Signed URL Configuration
S3_SIGNED_URL_EXPIRY=86400  # 24 hours in seconds
```

Update `backend/.env.example`:
```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your actual credentials
```

**Security Note:** NEVER commit `.env` to version control! The `.env.example` file should only contain placeholders.

## Migration from Local Storage

### Step 8: Migrate Existing Files

If you have existing files in local `uploads/` directory:

```bash
cd backend

# Dry run first (preview what will be migrated)
python migrate_local_to_s3.py --dry-run

# Actual migration
python migrate_local_to_s3.py

# Migrate and delete local files after upload
python migrate_local_to_s3.py --delete-local
```

**Migration Process:**
1. Scans `uploads/` directory for all files
2. Uploads each file to S3 with proper metadata
3. Updates database records with S3 keys
4. Verifies all files uploaded successfully
5. Optionally deletes local files

**Output Example:**
```
🚀 Starting Local to S3 Migration
============================================================
📁 Found 47 files in uploads
📤 Migrating 47 files...
⬆️  Uploading: uploads/project-123/abc-def.pdf -> s3://painting-ai-uploads-prod/project-123/abc-def.pdf
✅ Verified: s3://painting-ai-uploads-prod/project-123/abc-def.pdf (2.4 MB)
...
📊 Migration Summary
============================================================
Total files:         47
Uploaded:            47
Skipped:             0
Errors:              0
Total size:          124.56 MB
Projects updated:    12
✅ Migration complete!
```

## Security Best Practices

### Bucket Policies

Apply bucket policies to enforce security:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUnencryptedUploads",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::painting-ai-uploads-prod/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "AES256"
        }
      }
    },
    {
      "Sid": "DenyInsecureTransport",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::painting-ai-uploads-prod",
        "arn:aws:s3:::painting-ai-uploads-prod/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

### Lifecycle Rules (90-Day Retention)

Configure automatic deletion of old files:

1. Go to S3 Console → Select bucket
2. Management → Lifecycle rules → Create rule
3. Rule name: `delete-old-files`
4. Choose rule scope: Apply to all objects
5. Add action: **Expire current versions of objects**
6. Days after object creation: **90**
7. Create rule

Or via AWS CLI:
```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket painting-ai-uploads-prod \
  --lifecycle-configuration file://lifecycle.json
```

`lifecycle.json`:
```json
{
  "Rules": [
    {
      "Id": "Delete old uploads",
      "Status": "Enabled",
      "Expiration": {
        "Days": 90
      }
    }
  ]
}
```

### Monitoring and Alerts

Enable S3 access logging and CloudWatch metrics:

```bash
# Enable access logging
aws s3api put-bucket-logging \
  --bucket painting-ai-uploads-prod \
  --bucket-logging-status '{
    "LoggingEnabled": {
      "TargetBucket": "painting-ai-logs",
      "TargetPrefix": "s3-access-logs/"
    }
  }'
```

Create CloudWatch alarms for:
- High request rates (potential abuse)
- Large file uploads (cost control)
- Failed requests (debugging)

## CloudFront CDN (Optional)

For faster global downloads and caching:

### Step 9: Create CloudFront Distribution

1. Go to [CloudFront Console](https://console.aws.amazon.com/cloudfront/)
2. Create distribution
3. Origin domain: `painting-ai-exports-prod.s3.amazonaws.com`
4. Origin access: **Origin access control (OAC)**
5. Default cache behavior:
   - Viewer protocol: Redirect HTTP to HTTPS
   - Allowed methods: GET, HEAD, OPTIONS
   - Cache policy: CachingOptimized
6. Price class: Use all edge locations (or select regions)
7. Create distribution

### Update S3 Bucket Policy

CloudFront needs permission to access S3:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontOAC",
      "Effect": "Allow",
      "Principal": {
        "Service": "cloudfront.amazonaws.com"
      },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::painting-ai-exports-prod/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "arn:aws:cloudfront::YOUR_ACCOUNT_ID:distribution/YOUR_DISTRIBUTION_ID"
        }
      }
    }
  ]
}
```

### Custom Domain (Optional)

1. Request SSL certificate in AWS Certificate Manager (ACM)
2. Add CNAME record in CloudFront distribution
3. Update DNS to point to CloudFront
4. Use domain for signed URLs: `https://files.painting.ai/...`

**Benefits:**
- 50-90% faster downloads globally
- Reduced S3 costs (CloudFront caching)
- Custom domain (files.painting.ai)
- DDoS protection

## Troubleshooting

### Error: "AWS credentials not configured"

**Solution:** Set environment variables in `.env`:
```bash
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
```

### Error: "NoSuchBucket"

**Solution:** Create buckets or verify names match:
```bash
aws s3 ls  # List all buckets
```

### Error: "Access Denied"

**Solution:** Check IAM permissions. User needs `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject` on bucket.

### Signed URLs Expire Too Quickly

**Solution:** Increase expiry time in `.env`:
```bash
S3_SIGNED_URL_EXPIRY=172800  # 48 hours
```

### High S3 Costs

**Solutions:**
1. Enable lifecycle rules to delete old files
2. Use CloudFront CDN for caching (reduce GET requests)
3. Compress files before upload (GZIP for text/JSON)
4. Use S3 Intelligent-Tiering storage class

### Files Not Uploading

**Check:**
1. Bucket exists: `aws s3 ls`
2. Credentials valid: `aws sts get-caller-identity`
3. Region matches: Verify `AWS_REGION` in `.env`
4. File size limits: Default 50MB, increase if needed

## Testing S3 Integration

```bash
# Test S3 service initialization
cd backend
python s3_service.py

# Run S3 tests
pytest tests/test_s3_service.py -v

# Test upload manually
python -c "from s3_service import S3Service; s3 = S3Service(); print(s3.list_files())"
```

## Cost Estimation

**Monthly costs for typical usage:**

| Resource | Usage | Cost |
|----------|-------|------|
| S3 Storage | 50 GB | $1.15 |
| PUT/POST Requests | 10,000 | $0.05 |
| GET Requests | 100,000 | $0.40 |
| Data Transfer Out | 20 GB | $1.80 |
| **Total** | | **~$3.40/month** |

**Cost optimization:**
- Enable S3 Intelligent-Tiering (auto-move to cheaper storage)
- Use CloudFront CDN (reduce GET requests)
- Implement lifecycle rules (delete old files)
- Compress files (reduce storage and transfer)

## Next Steps

1. ✅ Set up AWS account and create buckets
2. ✅ Configure IAM user with minimal permissions
3. ✅ Set environment variables in `.env`
4. ✅ Test S3 service: `python s3_service.py`
5. ✅ Run tests: `pytest tests/test_s3_service.py`
6. ✅ Migrate local files: `python migrate_local_to_s3.py`
7. ✅ Update API endpoints to use S3 (see main.py)
8. ✅ Configure lifecycle rules for 90-day retention
9. ⬜ (Optional) Set up CloudFront CDN
10. ⬜ Monitor costs in AWS Cost Explorer

## Support

**Resources:**
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Boto3 S3 Reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

**Contact:**
- Email: cooperxxjohn@gmail.com
- Documentation: Check project README.md
