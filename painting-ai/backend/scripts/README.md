# Database Scripts

Production database management scripts for Painting.ai

## Scripts

### backup_database.sh

Automated database backup with S3 upload and rotation.

**Features:**
- PostgreSQL dump with pg_dump
- Gzip compression
- S3 upload (Standard-IA storage)
- Automatic rotation (7 daily, 4 weekly, 12 monthly)
- Slack/email notifications

**Usage:**
```bash
./backup_database.sh [daily|weekly|monthly]
```

**Examples:**
```bash
# Daily backup (default)
./backup_database.sh daily

# Weekly backup
./backup_database.sh weekly

# Monthly backup
./backup_database.sh monthly
```

**Environment Variables:**
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=paintingai
DB_USER=paintingai
DB_PASSWORD=your_password
S3_BACKUP_BUCKET=painting-ai-backups
BACKUP_DIR=/tmp/db_backups
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
ALERT_EMAIL=ops@paintingai.com
```

---

### restore_database.sh

Restore database from backup with safety checks.

**Features:**
- Downloads from S3 or uses local file
- Automatic decompression
- Database recreation (safe drop)
- Verification after restore
- Production safety confirmations

**Usage:**
```bash
./restore_database.sh <backup_file_or_s3_path> [options]
```

**Examples:**
```bash
# From S3
./restore_database.sh s3://painting-ai-backups/database/daily/paintingai_daily_20260521_020000.sql.gz

# From local file
./restore_database.sh /tmp/backups/backup.sql.gz

# To different database
./restore_database.sh --target-db paintingai_staging backup.sql.gz

# Skip confirmation (CI/CD)
./restore_database.sh --skip-confirmation backup.sql.gz
```

**Options:**
- `--skip-confirmation` - Skip production safety prompt
- `--target-db <name>` - Restore to different database
- `--help` - Show help message

---

### check_backup_status.sh

Verify recent backups exist and alert if missing.

**Features:**
- Checks for backups in last 24 hours
- Verifies backup size (>1MB)
- Sends alerts via Slack/email if issues found

**Usage:**
```bash
./check_backup_status.sh
```

**Cron:**
```bash
# Run daily at 2:30 AM (after backup at 2:00 AM)
30 2 * * * /path/to/check_backup_status.sh
```

---

### crontab.example

Example cron configuration for automated tasks.

**Install:**
```bash
crontab crontab.example
```

**Or manually edit:**
```bash
crontab -e
# Copy contents from crontab.example
```

**Verify:**
```bash
crontab -l
```

**Included Jobs:**
- Daily backup (2:00 AM)
- Weekly backup (Sunday 3:00 AM)
- Monthly backup (1st of month 4:00 AM)
- Database monitoring (every 15 minutes)
- Vacuum analyze (Sunday 1:00 AM)
- Backup verification (daily 2:30 AM)
- Log cleanup (weekly)

---

## Setup

### 1. Install Dependencies

```bash
# PostgreSQL client
sudo apt-get install postgresql-client

# AWS CLI
sudo apt-get install awscli

# Configure AWS
aws configure
```

### 2. Set Environment Variables

Create `.env` file:

```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=paintingai
DB_USER=paintingai
DB_PASSWORD=changeme123

# S3
S3_BACKUP_BUCKET=painting-ai-backups
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1

# Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
ALERT_EMAIL=ops@paintingai.com
```

### 3. Create S3 Bucket

```bash
# Create bucket
aws s3 mb s3://painting-ai-backups

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket painting-ai-backups \
    --versioning-configuration Status=Enabled

# Configure lifecycle (move to Glacier after 90 days)
aws s3api put-bucket-lifecycle-configuration \
    --bucket painting-ai-backups \
    --lifecycle-configuration file://lifecycle.json
```

**lifecycle.json:**
```json
{
  "Rules": [
    {
      "Id": "ArchiveOldBackups",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
```

### 4. Test Scripts

```bash
# Test backup
./backup_database.sh daily

# Verify S3 upload
aws s3 ls s3://painting-ai-backups/database/daily/

# Test restore (to test database)
./restore_database.sh --target-db paintingai_test paintingai_daily_20260521_020000.sql.gz

# Test backup verification
./check_backup_status.sh
```

### 5. Set Up Cron

```bash
# Edit crontab
crontab -e

# Add jobs from crontab.example
# Save and exit

# Verify
crontab -l
```

---

## Monitoring

### Check Backup Logs

```bash
# Backup logs
tail -f /tmp/db_backups/backup.log

# Monitor logs
tail -f /tmp/db_backups/monitor.log

# Maintenance logs
tail -f /tmp/db_backups/maintenance.log

# Alert logs
tail -f /tmp/db_backups/alerts.log
```

### List Backups

```bash
# Daily backups
aws s3 ls s3://painting-ai-backups/database/daily/

# Weekly backups
aws s3 ls s3://painting-ai-backups/database/weekly/

# Monthly backups
aws s3 ls s3://painting-ai-backups/database/monthly/
```

### Backup Sizes

```bash
# Total backup size
aws s3 ls s3://painting-ai-backups/database/ --recursive --human-readable --summarize

# Daily backup size
aws s3 ls s3://painting-ai-backups/database/daily/ --recursive --human-readable --summarize
```

---

## Troubleshooting

### Backup Failed

**Check logs:**
```bash
tail -f /tmp/db_backups/backup.log
```

**Common issues:**
- Database credentials incorrect → Check .env
- Disk space full → Clean up /tmp/db_backups
- S3 permissions → Check AWS credentials
- pg_dump not found → Install postgresql-client

### Restore Failed

**Check logs:**
```bash
./restore_database.sh backup.sql.gz 2>&1 | tee restore.log
```

**Common issues:**
- Backup file corrupted → Re-download from S3
- Database in use → Stop application first
- Permissions → Check database user permissions
- Syntax errors → May be from different PostgreSQL version

### S3 Upload Failed

**Test AWS credentials:**
```bash
aws s3 ls s3://painting-ai-backups/
```

**Check permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::painting-ai-backups",
        "arn:aws:s3:::painting-ai-backups/*"
      ]
    }
  ]
}
```

### Cron Not Running

**Check cron service:**
```bash
sudo systemctl status cron
```

**Check cron logs:**
```bash
grep CRON /var/log/syslog
```

**Verify crontab:**
```bash
crontab -l
```

**Test manually:**
```bash
/bin/bash /path/to/backup_database.sh daily
```

---

## Best Practices

### Security

1. **Never commit .env files** to version control
2. **Use IAM roles** instead of access keys (EC2/ECS)
3. **Encrypt backups** with S3 server-side encryption
4. **Rotate credentials** regularly
5. **Restrict S3 bucket** access (private only)

### Reliability

1. **Test restores monthly** - Ensure backups are valid
2. **Monitor backup success** - Set up alerts
3. **Verify backup size** - Catch empty/corrupted backups
4. **Multiple retention policies** - Daily, weekly, monthly
5. **Geographic redundancy** - Use S3 cross-region replication

### Performance

1. **Run backups during low traffic** (2-4 AM)
2. **Compress backups** (gzip saves 90% space)
3. **Use Standard-IA storage** (cheaper for infrequent access)
4. **Archive old backups** to Glacier (even cheaper)
5. **Clean up local backups** to save disk space

---

## Support

**Issues?**
- Check logs first
- Run scripts manually to see errors
- Verify environment variables
- Test AWS/database connectivity

**Contact:**
- Email: ops@paintingai.com
- Slack: #infrastructure
- On-call: PagerDuty escalation
