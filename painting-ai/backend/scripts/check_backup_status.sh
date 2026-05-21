#!/bin/bash
#
# Backup Status Check Script
#
# Verifies that recent backups exist and alerts if missing
#
# Usage:
#   ./check_backup_status.sh
#

set -e
set -u

# Configuration
S3_BUCKET="${S3_BACKUP_BUCKET:-painting-ai-backups}"
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL:-}"
ALERT_EMAIL="${ALERT_EMAIL:-}"

# Check for backup in last 24 hours
YESTERDAY=$(date -d "yesterday" +"%Y%m%d")
TODAY=$(date +"%Y%m%d")

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

send_alert() {
    local message=$1

    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"⚠️ BACKUP ALERT: ${message}\"}" \
            "$SLACK_WEBHOOK" > /dev/null 2>&1 || true
    fi

    if [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "🚨 Backup Alert - Painting.ai" "$ALERT_EMAIL" || true
    fi

    log "ALERT: $message"
}

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    send_alert "AWS CLI not found - cannot verify backups"
    exit 1
fi

# List recent daily backups
log "Checking for recent backups..."

RECENT_BACKUPS=$(aws s3 ls "s3://${S3_BUCKET}/database/daily/" \
    | grep -E "${YESTERDAY}|${TODAY}" \
    | wc -l)

if [ "$RECENT_BACKUPS" -eq 0 ]; then
    send_alert "No backups found in last 24 hours! Last backup check: $(date)"
    exit 1
else
    log "✓ Found $RECENT_BACKUPS recent backup(s)"
fi

# Check backup size (should be >1MB)
LATEST_BACKUP=$(aws s3 ls "s3://${S3_BUCKET}/database/daily/" \
    | sort -r \
    | head -n 1 \
    | awk '{print $4}')

if [ -n "$LATEST_BACKUP" ]; then
    BACKUP_SIZE=$(aws s3 ls "s3://${S3_BUCKET}/database/daily/${LATEST_BACKUP}" \
        | awk '{print $3}')

    if [ "$BACKUP_SIZE" -lt 1048576 ]; then  # 1MB
        send_alert "Latest backup is suspiciously small: ${BACKUP_SIZE} bytes"
        exit 1
    fi

    log "✓ Latest backup size: $((BACKUP_SIZE / 1024 / 1024)) MB"
else
    send_alert "Could not determine latest backup size"
    exit 1
fi

log "✓ Backup verification passed"
exit 0
