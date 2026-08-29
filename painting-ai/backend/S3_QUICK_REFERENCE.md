# S3 Quick Reference Card

Quick commands and code snippets for S3 integration.

## Environment Setup

```bash
# .env file
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
AWS_S3_BUCKET_UPLOADS=painting-ai-uploads-prod
AWS_S3_BUCKET_EXPORTS=painting-ai-exports-prod
S3_SIGNED_URL_EXPIRY=86400
```

## Common Commands

### Test Configuration
```bash
python test_s3_setup.py
```

### Run Tests
```bash
pytest tests/test_s3_service.py -v
```

### Migrate Files
```bash
# Preview
python migrate_local_to_s3.py --dry-run

# Migrate
python migrate_local_to_s3.py

# Migrate and delete local
python migrate_local_to_s3.py --delete-local
```

### AWS CLI Commands
```bash
# List buckets
aws s3 ls

# List files in bucket
aws s3 ls s3://painting-ai-uploads-prod/

# Test credentials
aws sts get-caller-identity

# Create bucket
aws s3 mb s3://painting-ai-uploads-prod --region us-east-1
```

## Python Code Snippets

### Initialize S3 Service
```python
from s3_service import S3Service

s3 = S3Service()
```

### Upload File
```python
# From file path
result = s3.upload_file(
    file_path="local/file.pdf",
    s3_key="project-123/file-456.pdf",
    metadata={'project_id': '123'}
)

# From BytesIO
from io import BytesIO
file_obj = BytesIO(b"content")
result = s3.upload_file_obj(
    file_obj=file_obj,
    s3_key="project-123/file.pdf",
    content_type="application/pdf"
)
```

### Generate Signed URL
```python
# Basic
url = s3.generate_signed_url("project-123/file.pdf")

# With custom filename and expiry
url = s3.generate_signed_url(
    s3_key="project-123/file.pdf",
    expiry=3600,  # 1 hour
    download_filename="Floor-Plan.pdf"
)
```

### Delete Files
```python
# Single file
s3.delete_file("project-123/file.pdf")

# Batch delete
result = s3.delete_files_batch([
    "project-123/file1.pdf",
    "project-123/file2.pdf"
])
```

### List Files
```python
# All files
files = s3.list_files()

# With prefix
files = s3.list_files(prefix="project-123/")

# Specific bucket
files = s3.list_files(
    prefix="project-123/",
    bucket=s3.bucket_exports
)
```

### Check File Exists
```python
if s3.file_exists("project-123/file.pdf"):
    print("File exists")
```

### Get Metadata
```python
metadata = s3.get_file_metadata("project-123/file.pdf")
print(f"Size: {metadata['size']} bytes")
print(f"Type: {metadata['content_type']}")
```

### Cleanup Old Files
```python
# Dry run
result = s3.cleanup_old_files(days=90, dry_run=True)

# Actually delete
result = s3.cleanup_old_files(days=90, dry_run=False)
```

## API Endpoints

### Upload
```bash
curl -X POST http://localhost:8000/projects/{id}/upload \
  -F "file=@floor-plan.pdf"
```

Response:
```json
{
  "file_id": "abc-123",
  "download_url": "https://s3.amazonaws.com/...",
  "url_expires_at": "2026-05-22T12:00:00"
}
```

### Export Excel
```bash
curl http://localhost:8000/projects/{id}/export/excel
```

Response:
```json
{
  "download_url": "https://s3.amazonaws.com/...",
  "expires_at": "2026-05-22T12:00:00",
  "filename": "Project_Takeoff.xlsx"
}
```

### Export PDF
```bash
curl http://localhost:8000/projects/{id}/export/pdf
```

### Refresh Download URL
```bash
curl http://localhost:8000/projects/{id}/uploads/{file_id}/download-url
```

## Error Handling

### Common Errors

**"AWS credentials not configured"**
```python
# Solution: Set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

**"NoSuchBucket"**
```bash
# Solution: Create bucket
aws s3 mb s3://painting-ai-uploads-prod
```

**"Access Denied"**
```bash
# Solution: Check IAM permissions
aws iam get-user-policy --user-name painting-ai-app --policy-name S3Access
```

## IAM Policy Template

```json
{
  "Version": "2012-10-17",
  "Statement": [{
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
  }]
}
```

## Bucket Lifecycle Rule

```json
{
  "Rules": [{
    "Id": "Delete old files",
    "Status": "Enabled",
    "Expiration": {
      "Days": 90
    }
  }]
}
```

Apply:
```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket painting-ai-uploads-prod \
  --lifecycle-configuration file://lifecycle.json
```

## Cost Tracking

### Check Current Month
```bash
aws ce get-cost-and-usage \
  --time-period Start=2026-05-01,End=2026-05-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --filter file://filter.json
```

### Estimate Costs
- Storage: $0.023/GB/month
- PUT: $0.005 per 1,000
- GET: $0.0004 per 1,000
- Transfer: $0.09/GB

## Monitoring

### CloudWatch Metrics
```bash
# Get bucket metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name NumberOfObjects \
  --dimensions Name=BucketName,Value=painting-ai-uploads-prod \
  --start-time 2026-05-01T00:00:00Z \
  --end-time 2026-05-31T23:59:59Z \
  --period 86400 \
  --statistics Average
```

### Enable Access Logging
```bash
aws s3api put-bucket-logging \
  --bucket painting-ai-uploads-prod \
  --bucket-logging-status file://logging.json
```

## CloudFront Setup

### Create Distribution
```bash
aws cloudfront create-distribution \
  --origin-domain-name painting-ai-exports-prod.s3.amazonaws.com \
  --default-root-object index.html
```

### Update S3 Bucket for CloudFront
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "cloudfront.amazonaws.com"
    },
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::painting-ai-exports-prod/*"
  }]
}
```

## Troubleshooting Checklist

- [ ] Environment variables set in `.env`
- [ ] boto3 installed: `pip install boto3`
- [ ] AWS credentials valid: `aws sts get-caller-identity`
- [ ] Buckets exist: `aws s3 ls`
- [ ] IAM permissions correct (PutObject, GetObject, DeleteObject)
- [ ] Region matches: check `AWS_REGION`
- [ ] Test script passes: `python test_s3_setup.py`
- [ ] Tests pass: `pytest tests/test_s3_service.py`

## Files Reference

| File | Purpose |
|------|---------|
| `s3_service.py` | Core S3 service |
| `migrate_local_to_s3.py` | Migration script |
| `main_s3_updates.py` | API integration code |
| `test_s3_service.py` | Unit tests |
| `test_s3_setup.py` | Quick verification |
| `S3_SETUP.md` | Complete setup guide |
| `S3_INTEGRATION_GUIDE.md` | Integration steps |
| `.env.example` | Environment template |

## Links

- [AWS S3 Docs](https://docs.aws.amazon.com/s3/)
- [Boto3 Reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [S3 Pricing](https://aws.amazon.com/s3/pricing/)
- [CloudFront Docs](https://docs.aws.amazon.com/cloudfront/)
