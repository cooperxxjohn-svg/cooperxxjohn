# S3 Integration Guide

This guide explains how to integrate the S3 service into main.py.

## Step 1: Update Imports

Add these imports to the top of `main.py`:

```python
from s3_service import S3Service, get_s3_service
from io import BytesIO
import tempfile
from datetime import timedelta
```

## Step 2: Initialize S3 Service

Add after line 62 (after initializing other services):

```python
# Initialize S3 service (optional - falls back to local storage)
try:
    s3_service = get_s3_service()
    USE_S3 = True
    print(f"✅ S3 storage enabled")
    print(f"   Uploads: {s3_service.bucket_uploads}")
    print(f"   Exports: {s3_service.bucket_exports}")
except Exception as e:
    print(f"⚠️  S3 not configured: {e}")
    print("   Falling back to local storage")
    s3_service = None
    USE_S3 = False
```

## Step 3: Update Upload Endpoint

Replace the `upload_drawing` endpoint (lines 536-566) with the S3-enabled version from `main_s3_updates.py`.

Key changes:
- Upload file to S3 using `s3_service.upload_file_obj()`
- Generate signed URL for download
- Store S3 metadata in database
- Fall back to local storage if S3 not configured

## Step 4: Add S3 Processing Function

Add the new `process_drawing_s3` function after the existing `process_drawing` function:

```python
async def process_drawing_s3(project_id: str, s3_key: str, file_id: str):
    # Function from main_s3_updates.py
```

This function:
1. Downloads file from S3 to temp location
2. Processes with AI
3. Cleans up temp file

## Step 5: Update Export Endpoints

Replace both export endpoints:

### Excel Export (line 856)
```python
@app.get("/projects/{project_id}/export/excel")
async def export_excel(project_id: str):
    # S3-enabled version from main_s3_updates.py
```

### PDF Export (line 877)
```python
@app.get("/projects/{project_id}/export/pdf")
async def export_pdf(project_id: str):
    # S3-enabled version from main_s3_updates.py
```

Key changes:
- Generate export to temp file
- Upload to S3 exports bucket
- Return signed URL instead of FileResponse
- Clean up temp file after upload

## Step 6: Add New Download URL Endpoint

Add this new endpoint (optional but recommended):

```python
@app.get("/projects/{project_id}/uploads/{file_id}/download-url")
async def get_upload_download_url(project_id: str, file_id: str):
    # Refresh expired signed URLs
```

This allows clients to get fresh signed URLs when the original expires (after 24 hours).

## Step 7: Update Health Check

Update the health check endpoint to include S3 status:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "detector": "ready",
        "database": "connected" if db.is_connected() else "disconnected",
        "s3": "enabled" if USE_S3 else "disabled (using local storage)"
    }
```

## Complete Integration Example

Here's how the endpoints work together:

### Upload Flow
```
1. Client uploads file to /projects/{id}/upload
2. API validates file
3. Upload to S3: s3://uploads-bucket/project-id/file-id.pdf
4. Generate 24-hour signed URL
5. Return signed URL to client
6. Process file in background (download from S3, analyze, upload results)
```

### Export Flow
```
1. Client requests /projects/{id}/export/excel
2. API generates Excel file to temp location
3. Upload to S3: s3://exports-bucket/project-id/export-id.xlsx
4. Generate 24-hour signed URL
5. Delete temp file
6. Return signed URL to client
```

### Download Flow
```
1. Client uses signed URL to download directly from S3
2. If URL expires, request fresh URL from /download-url endpoint
3. S3 handles authentication via signed URL
```

## Environment Variables Required

Ensure these are set in `.env`:

```bash
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
AWS_S3_BUCKET_UPLOADS=painting-ai-uploads-prod
AWS_S3_BUCKET_EXPORTS=painting-ai-exports-prod
S3_SIGNED_URL_EXPIRY=86400
```

## Testing the Integration

### 1. Start the API
```bash
cd backend
python main.py
```

Check startup logs for:
```
✅ S3 storage enabled
   Uploads: painting-ai-uploads-prod
   Exports: painting-ai-exports-prod
```

### 2. Test Upload
```bash
curl -X POST http://localhost:8000/projects/{project-id}/upload \
  -F "file=@test-floor-plan.pdf"
```

Expected response:
```json
{
  "message": "File uploaded successfully",
  "file_id": "abc-123",
  "download_url": "https://painting-ai-uploads.s3.amazonaws.com/...",
  "url_expires_at": "2026-05-22T12:00:00"
}
```

### 3. Test Export
```bash
curl http://localhost:8000/projects/{project-id}/export/excel
```

Expected response:
```json
{
  "export_type": "excel",
  "download_url": "https://painting-ai-exports.s3.amazonaws.com/...",
  "expires_at": "2026-05-22T12:00:00",
  "filename": "Project_Takeoff.xlsx"
}
```

### 4. Test Download
```bash
# Use download_url from response
curl -o file.pdf "https://painting-ai-uploads.s3.amazonaws.com/..."
```

## Migration Path

You can migrate gradually:

### Phase 1: Keep Local Storage
- Set up S3 but don't configure env vars
- API falls back to local storage
- No code changes needed

### Phase 2: Enable S3 for New Files
- Configure S3 env vars
- New uploads go to S3
- Old files remain local
- Both work simultaneously

### Phase 3: Migrate Old Files
```bash
python migrate_local_to_s3.py --dry-run  # Preview
python migrate_local_to_s3.py            # Migrate
python migrate_local_to_s3.py --delete-local  # Clean up
```

### Phase 4: S3 Only
- All files in S3
- Remove local storage directories
- Simplify deployment

## Rollback Plan

If S3 has issues:

1. Remove S3 env vars from `.env`
2. Restart API
3. API automatically falls back to local storage
4. No code changes needed

## Performance Considerations

### Upload Performance
- S3 upload: ~1-2 seconds for 5MB file
- Parallel uploads supported
- No disk I/O on API server

### Download Performance
- Signed URLs served directly by S3
- No API server load
- CDN-ready (CloudFront optional)

### Cost Considerations
- Storage: $0.023/GB/month
- GET requests: $0.0004 per 1000
- PUT requests: $0.005 per 1000
- Data transfer: $0.09/GB

Estimated monthly cost for 1000 projects:
- Storage (10 GB): $0.23
- Uploads (5000): $0.03
- Downloads (10000): $0.004
- Transfer (50 GB): $4.50
**Total: ~$5/month**

## Monitoring

### CloudWatch Metrics
- S3 request count
- 4xx/5xx errors
- Bytes downloaded
- Bytes uploaded

### Application Logs
```python
import logging
logger = logging.getLogger(__name__)

# S3 service logs all operations:
logger.info(f"Uploaded {file_path} to s3://{bucket}/{key}")
logger.error(f"Failed to upload: {error}")
```

### Alerts
Set up CloudWatch alarms for:
- High error rate (>5%)
- Large uploads (>50MB)
- Unusual request patterns

## Security Checklist

- [ ] S3 buckets are private (no public access)
- [ ] IAM user has minimal permissions (PutObject, GetObject, DeleteObject)
- [ ] Signed URLs expire in 24 hours
- [ ] Encryption enabled (SSE-S3)
- [ ] HTTPS enforced (bucket policy)
- [ ] Lifecycle rules configured (90-day retention)
- [ ] Access logging enabled
- [ ] Credentials not in version control

## Troubleshooting

### "S3 not configured" on startup
- Check `.env` has all required AWS vars
- Verify credentials are valid: `aws sts get-caller-identity`
- Check bucket names are correct: `aws s3 ls`

### "Access Denied" on upload
- Verify IAM permissions include `s3:PutObject`
- Check bucket name matches env var
- Test with AWS CLI: `aws s3 cp test.txt s3://your-bucket/`

### Signed URLs expire too fast
- Increase `S3_SIGNED_URL_EXPIRY` in `.env`
- Default is 86400 (24 hours)
- Maximum is 604800 (7 days)

### High S3 costs
- Enable lifecycle rules to delete old files
- Use CloudFront CDN for caching
- Compress files before upload
- Move to Glacier for archival

## Next Steps

1. ✅ Integrate S3 service into main.py
2. ✅ Set up environment variables
3. ✅ Test upload/export endpoints
4. ✅ Run migration script
5. ⬜ Set up CloudFront (optional)
6. ⬜ Configure CloudWatch alerts
7. ⬜ Enable lifecycle rules
8. ⬜ Update frontend to use signed URLs
