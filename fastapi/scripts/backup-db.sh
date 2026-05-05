#!/bin/bash
set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql.gz"

echo "💾 Starting database backup..."

# Create backup
pg_dump $DATABASE_URL | gzip > $BACKUP_FILE

# Upload to S3 (optional)
if [ ! -z "$AWS_S3_BUCKET" ]; then
    echo "☁️  Uploading to S3..."
    aws s3 cp $BACKUP_FILE s3://$AWS_S3_BUCKET/backups/
fi

# Clean old backups (keep last 7 days)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "✅ Backup complete: $BACKUP_FILE"