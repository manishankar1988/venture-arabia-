#!/usr/bin/env bash
# Nightly backup of the PostgreSQL database and uploaded media.
# Cron (as the venture user):  0 3 * * * /srv/venture/deploy/backup.sh >> /srv/venture/logs/backup.log 2>&1
# Copy the resulting files off the server (rsync/rclone to object storage) and test a restore regularly:
#   gunzip -c venture-YYYY-MM-DD.sql.gz | psql "$DATABASE_URL"
set -euo pipefail
cd /srv/venture
set -a; source .env; set +a

BACKUP_DIR=${BACKUP_DIR:-/srv/venture/backups}
KEEP_DAYS=${KEEP_DAYS:-30}
STAMP=$(date +%F)
mkdir -p "$BACKUP_DIR"

echo "[$(date)] database"
pg_dump "$DATABASE_URL" --no-owner | gzip > "$BACKUP_DIR/venture-$STAMP.sql.gz"

echo "[$(date)] media"
tar -czf "$BACKUP_DIR/media-$STAMP.tar.gz" media

find "$BACKUP_DIR" -type f -mtime +"$KEEP_DAYS" -delete
echo "[$(date)] done: $(du -sh "$BACKUP_DIR" | cut -f1) in $BACKUP_DIR"
