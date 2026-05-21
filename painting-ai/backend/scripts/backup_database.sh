#!/bin/bash
#
# Database Backup Script for Painting.ai
#
# Features:
# - Creates PostgreSQL dump with pg_dump
# - Compresses with gzip
# - Uploads to S3 backup bucket
# - Rotates old backups (7 daily, 4 weekly, 12 monthly)
# - Sends notifications on failure
#
# Usage:
#   ./backup_database.sh [backup_type]
#
# backup_type: daily (default), weekly, monthly
#

set -e  # Exit on error
set -u  # Exit on undefined variable

# ==============================================================================
# Configuration
# ==============================================================================

# Load environment variables
if [ -f .env ]; then
    source .env
fi

# Database configuration
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-paintingai}"
DB_USER="${DB_USER:-paintingai}"
DB_PASSWORD="${DB_PASSWORD:-changeme123}"

# Backup configuration
BACKUP_TYPE="${1:-daily}"  # daily, weekly, monthly
BACKUP_DIR="${BACKUP_DIR:-/tmp/db_backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILENAME="paintingai_${BACKUP_TYPE}_${TIMESTAMP}.sql"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_FILENAME}"
COMPRESSED_BACKUP="${BACKUP_PATH}.gz"

# S3 configuration
S3_BUCKET="${S3_BACKUP_BUCKET:-painting-ai-backups}"
S3_PREFIX="database/${BACKUP_TYPE}"

# Retention policy
DAILY_RETENTION=7      # Keep 7 daily backups
WEEKLY_RETENTION=4     # Keep 4 weekly backups
MONTHLY_RETENTION=12   # Keep 12 monthly backups

# Notification
SLACK_WEBHOOK="${SLACK_WEBHOOK_URL:-}"
ALERT_EMAIL="${ALERT_EMAIL:-}"

# ==============================================================================
# Functions
# ==============================================================================

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo "[ERROR] $1" >&2
}

send_notification() {
    local status=$1
    local message=$2

    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"Database Backup ${status}: ${message}\"}" \
            "$SLACK_WEBHOOK" > /dev/null 2>&1 || true
    fi

    if [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "Database Backup ${status}" "$ALERT_EMAIL" || true
    fi
}

cleanup_local_backups() {
    log "Cleaning up old local backup files..."
    find "$BACKUP_DIR" -name "paintingai_*.sql.gz" -mtime +1 -delete
}

rotate_s3_backups() {
    local backup_type=$1
    local retention=$2

    log "Rotating S3 backups for ${backup_type} (keep ${retention})..."

    # List and delete old backups
    aws s3 ls "s3://${S3_BUCKET}/${S3_PREFIX}/" \
        | sort -r \
        | tail -n +$((retention + 1)) \
        | awk '{print $4}' \
        | while read -r file; do
            if [ -n "$file" ]; then
                log "Deleting old backup: ${file}"
                aws s3 rm "s3://${S3_BUCKET}/${S3_PREFIX}/${file}"
            fi
        done
}

# ==============================================================================
# Main Backup Process
# ==============================================================================

log "Starting ${BACKUP_TYPE} database backup..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Set PostgreSQL password
export PGPASSWORD="$DB_PASSWORD"

# Create database dump
log "Creating database dump..."
if ! pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --format=plain \
    --no-owner \
    --no-acl \
    --clean \
    --if-exists \
    -f "$BACKUP_PATH"; then
    error "pg_dump failed"
    send_notification "FAILED" "Database dump failed for ${DB_NAME}"
    exit 1
fi

# Get backup size
BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
log "Backup created: ${BACKUP_PATH} (${BACKUP_SIZE})"

# Compress backup
log "Compressing backup..."
if ! gzip -f "$BACKUP_PATH"; then
    error "Compression failed"
    send_notification "FAILED" "Backup compression failed"
    exit 1
fi

COMPRESSED_SIZE=$(du -h "$COMPRESSED_BACKUP" | cut -f1)
log "Backup compressed: ${COMPRESSED_BACKUP} (${COMPRESSED_SIZE})"

# Upload to S3
if command -v aws &> /dev/null; then
    log "Uploading to S3..."

    if aws s3 cp "$COMPRESSED_BACKUP" \
        "s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_FILENAME}.gz" \
        --storage-class STANDARD_IA; then
        log "Upload successful: s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_FILENAME}.gz"

        # Rotate old backups based on type
        case $BACKUP_TYPE in
            daily)
                rotate_s3_backups "daily" $DAILY_RETENTION
                ;;
            weekly)
                rotate_s3_backups "weekly" $WEEKLY_RETENTION
                ;;
            monthly)
                rotate_s3_backups "monthly" $MONTHLY_RETENTION
                ;;
        esac
    else
        error "S3 upload failed"
        send_notification "WARNING" "S3 upload failed, backup only stored locally"
    fi
else
    log "AWS CLI not found, skipping S3 upload"
    send_notification "WARNING" "AWS CLI not available, backup only stored locally"
fi

# Cleanup local backups older than 1 day
cleanup_local_backups

# Final status
log "Backup completed successfully!"
log "Local: ${COMPRESSED_BACKUP}"
log "S3: s3://${S3_BUCKET}/${S3_PREFIX}/${BACKUP_FILENAME}.gz"

send_notification "SUCCESS" "Database backup completed: ${COMPRESSED_SIZE} (${BACKUP_TYPE})"

# Unset password
unset PGPASSWORD

exit 0
