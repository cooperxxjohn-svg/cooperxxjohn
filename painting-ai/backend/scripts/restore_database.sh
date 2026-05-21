#!/bin/bash
#
# Database Restore Script for Painting.ai
#
# Features:
# - Downloads backup from S3
# - Decompresses backup
# - Restores to PostgreSQL
# - Verifies restoration
# - Safety checks to prevent accidental production overwrites
#
# Usage:
#   ./restore_database.sh <backup_file_or_s3_path>
#
# Examples:
#   ./restore_database.sh paintingai_daily_20260521_120000.sql.gz
#   ./restore_database.sh s3://painting-ai-backups/database/daily/paintingai_daily_20260521_120000.sql.gz
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
BACKUP_DIR="${BACKUP_DIR:-/tmp/db_backups}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# ==============================================================================
# Functions
# ==============================================================================

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo "[ERROR] $1" >&2
}

usage() {
    cat << EOF
Usage: $0 <backup_file_or_s3_path>

Restore database from backup file or S3 location.

Examples:
    $0 paintingai_daily_20260521_120000.sql.gz
    $0 s3://painting-ai-backups/database/daily/paintingai_daily_20260521_120000.sql.gz
    $0 /path/to/backup.sql.gz

Options:
    --skip-confirmation    Skip production safety confirmation
    --target-db <name>     Restore to different database name
    --help                Show this help message

Environment variables:
    DB_HOST               Database host (default: localhost)
    DB_PORT               Database port (default: 5432)
    DB_NAME               Database name (default: paintingai)
    DB_USER               Database user (default: paintingai)
    DB_PASSWORD           Database password
    BACKUP_DIR            Local backup directory (default: /tmp/db_backups)
EOF
    exit 1
}

confirm_restore() {
    local db_name=$1

    # Safety check for production
    if [[ "$DB_HOST" != "localhost" ]] && [[ "$DB_HOST" != "127.0.0.1" ]]; then
        echo ""
        echo "⚠️  WARNING: You are about to restore to a REMOTE database!"
        echo ""
        echo "Database: ${db_name}@${DB_HOST}:${DB_PORT}"
        echo ""
        echo "This will DELETE ALL EXISTING DATA in the database."
        echo ""
        read -p "Type 'yes' to continue: " confirmation

        if [ "$confirmation" != "yes" ]; then
            log "Restore cancelled by user"
            exit 0
        fi
    fi
}

verify_restore() {
    local db_name=$1

    log "Verifying database restoration..."

    export PGPASSWORD="$DB_PASSWORD"

    # Check table count
    local table_count=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$db_name" -t -c \
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';")

    log "Tables found: ${table_count}"

    # Check for key tables
    local expected_tables=("users" "projects" "rooms" "drawings")
    for table in "${expected_tables[@]}"; do
        local exists=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$db_name" -t -c \
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '${table}');")

        if [[ "$exists" =~ "t" ]]; then
            log "✓ Table '${table}' exists"
        else
            error "✗ Table '${table}' missing"
            return 1
        fi
    done

    log "✓ Database verification passed"
    unset PGPASSWORD
}

# ==============================================================================
# Main Restore Process
# ==============================================================================

# Parse arguments
SKIP_CONFIRMATION=false
TARGET_DB=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-confirmation)
            SKIP_CONFIRMATION=true
            shift
            ;;
        --target-db)
            TARGET_DB="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            BACKUP_SOURCE="$1"
            shift
            ;;
    esac
done

# Validate backup source
if [ -z "${BACKUP_SOURCE:-}" ]; then
    error "No backup source specified"
    usage
fi

# Use target DB if specified, otherwise use default
RESTORE_DB="${TARGET_DB:-$DB_NAME}"

log "Starting database restore..."
log "Source: ${BACKUP_SOURCE}"
log "Target: ${RESTORE_DB}@${DB_HOST}:${DB_PORT}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Download from S3 if needed
if [[ "$BACKUP_SOURCE" == s3://* ]]; then
    log "Downloading backup from S3..."

    BACKUP_FILENAME=$(basename "$BACKUP_SOURCE")
    LOCAL_BACKUP="${BACKUP_DIR}/${BACKUP_FILENAME}"

    if ! aws s3 cp "$BACKUP_SOURCE" "$LOCAL_BACKUP"; then
        error "Failed to download backup from S3"
        exit 1
    fi

    log "Downloaded to: ${LOCAL_BACKUP}"
    BACKUP_FILE="$LOCAL_BACKUP"
elif [[ -f "$BACKUP_SOURCE" ]]; then
    BACKUP_FILE="$BACKUP_SOURCE"
else
    # Try to find in backup directory
    BACKUP_FILE="${BACKUP_DIR}/${BACKUP_SOURCE}"

    if [[ ! -f "$BACKUP_FILE" ]]; then
        error "Backup file not found: ${BACKUP_SOURCE}"
        exit 1
    fi
fi

log "Using backup file: ${BACKUP_FILE}"

# Confirm restore
if [ "$SKIP_CONFIRMATION" = false ]; then
    confirm_restore "$RESTORE_DB"
fi

# Decompress if needed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    log "Decompressing backup..."
    DECOMPRESSED_FILE="${BACKUP_FILE%.gz}"

    if ! gunzip -c "$BACKUP_FILE" > "$DECOMPRESSED_FILE"; then
        error "Failed to decompress backup"
        exit 1
    fi

    RESTORE_FILE="$DECOMPRESSED_FILE"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# Set PostgreSQL password
export PGPASSWORD="$DB_PASSWORD"

# Drop and recreate database (safer than restore with --clean)
log "Recreating database ${RESTORE_DB}..."

# Terminate existing connections
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${RESTORE_DB}';" \
    > /dev/null 2>&1 || true

# Drop database
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c \
    "DROP DATABASE IF EXISTS ${RESTORE_DB};" || true

# Create database
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c \
    "CREATE DATABASE ${RESTORE_DB} OWNER ${DB_USER};"

# Restore database
log "Restoring database from backup..."
if ! psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$RESTORE_DB" -f "$RESTORE_FILE"; then
    error "Database restore failed"
    exit 1
fi

# Verify restoration
if ! verify_restore "$RESTORE_DB"; then
    error "Database verification failed"
    exit 1
fi

# Cleanup
if [[ "$RESTORE_FILE" != "$BACKUP_FILE" ]]; then
    log "Cleaning up decompressed file..."
    rm -f "$RESTORE_FILE"
fi

# Unset password
unset PGPASSWORD

log "✓ Database restore completed successfully!"
log "Database: ${RESTORE_DB}@${DB_HOST}:${DB_PORT}"

exit 0
