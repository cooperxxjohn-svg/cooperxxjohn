# S3 Integration for Painting.ai

Quick start guide for AWS S3 file storage integration.

## 🚀 Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure AWS
```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your AWS credentials
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_REGION=us-east-1
AWS_S3_BUCKET_UPLOADS=painting-ai-uploads-prod
AWS_S3_BUCKET_EXPORTS=painting-ai-exports-prod
```

### 3. Verify Setup
```bash
python test_s3_setup.py
```

Expected output:
```
✅ All tests passed! S3 is configured correctly.
```

### 4. Run Tests
```bash
pytest tests/test_s3_service.py -v
```

### 5. Integrate into API
See `S3_INTEGRATION_GUIDE.md` for step-by-step instructions.

## 📁 Files

| File | Purpose |
|------|---------|
| `s3_service.py` | Core S3 service module |
| `migrate_local_to_s3.py` | Migration script for existing files |
| `main_s3_updates.py` | API integration code |
| `test_s3_setup.py` | Quick verification script |
| `tests/test_s3_service.py` | Unit tests |

## 📚 Documentation

- **`S3_SETUP.md`** - Complete AWS setup guide (start here!)
- **`S3_INTEGRATION_GUIDE.md`** - How to integrate into main.py
- **`S3_IMPLEMENTATION_SUMMARY.md`** - Technical overview
- **`S3_QUICK_REFERENCE.md`** - Quick command reference
- **`WEEK2_S3_COMPLETION_REPORT.md`** - Full completion report

## 🔧 Common Commands

```bash
# Test S3 configuration
python test_s3_setup.py

# Run unit tests
pytest tests/test_s3_service.py -v

# Preview migration (dry run)
python migrate_local_to_s3.py --dry-run

# Migrate existing files
python migrate_local_to_s3.py

# Test AWS credentials
aws sts get-caller-identity

# List S3 buckets
aws s3 ls
```

## ✅ Features

- ✅ Upload files to S3 (file path or BytesIO)
- ✅ Generate signed URLs (24-hour expiration)
- ✅ Delete files (single or batch)
- ✅ List files with prefix filtering
- ✅ File metadata and existence checks
- ✅ 90-day retention policy
- ✅ Multiple bucket support
- ✅ Comprehensive error handling
- ✅ 35+ unit tests
- ✅ Complete documentation

## 🔒 Security

- Private S3 buckets (no public access)
- Signed URLs only (expire after 24 hours)
- Minimal IAM permissions
- HTTPS enforced
- Encryption enabled (SSE-S3)

## 💰 Cost

Estimated monthly cost:
- Storage (50 GB): $1.15
- Requests: $0.45
- Data transfer: $1.80
- **Total: ~$3.40/month**

## 🆘 Help

**Issues?** Check `S3_SETUP.md` troubleshooting section.

**Questions?** Email cooperxxjohn@gmail.com

**Documentation:** See all S3_*.md files
