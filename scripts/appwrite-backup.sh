#!/bin/bash
# =============================================================================
# Appwrite Automated Backup Script
# =============================================================================
# Usage: ./scripts/appwrite-backup.sh
# Cron:  0 2 * * * /opt/wizardsofts-megabuild/scripts/appwrite-backup.sh
# =============================================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_ROOT="${BACKUP_ROOT:-/opt/backups/appwrite}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"

# Load environment variables
if [ -f "${PROJECT_ROOT}/.env.appwrite" ]; then
    source "${PROJECT_ROOT}/.env.appwrite"
else
    echo "ERROR: .env.appwrite not found"
    exit 1
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory
log_info "Creating backup directory: ${BACKUP_DIR}"
mkdir -p "${BACKUP_DIR}"

# Backup MariaDB
log_info "Backing up MariaDB database..."
docker exec appwrite-mariadb mysqldump \
    -u root \
    -p"${_APP_DB_ROOT_PASS}" \
    --all-databases \
    --single-transaction \
    --quick \
    --lock-tables=false \
    > "${BACKUP_DIR}/appwrite_db.sql"

if [ $? -eq 0 ]; then
    gzip "${BACKUP_DIR}/appwrite_db.sql"
    log_info "Database backup complete: appwrite_db.sql.gz"
else
    log_error "Database backup failed"
    exit 1
fi

# Backup Docker volumes
log_info "Backing up Docker volumes..."

VOLUMES=(
    "wizardsofts-megabuild_appwrite-uploads:appwrite-uploads"
    "wizardsofts-megabuild_appwrite-config:appwrite-config"
    "wizardsofts-megabuild_appwrite-certificates:appwrite-certificates"
    "wizardsofts-megabuild_appwrite-functions:appwrite-functions"
)

for vol_mapping in "${VOLUMES[@]}"; do
    volume_name="${vol_mapping%%:*}"
    backup_name="${vol_mapping##*:}"

    log_info "Backing up volume: ${backup_name}"
    docker run --rm \
        -v "${volume_name}:/data:ro" \
        -v "${BACKUP_DIR}:/backup" \
        alpine tar czf "/backup/${backup_name}.tar.gz" -C /data .
done

log_info "Volume backups complete"

# Create backup manifest
log_info "Creating backup manifest..."
cat > "${BACKUP_DIR}/manifest.json" << EOF
{
    "timestamp": "${TIMESTAMP}",
    "appwrite_version": "1.8.1",
    "backup_type": "full",
    "components": {
        "database": "appwrite_db.sql.gz",
        "volumes": [
            "appwrite-uploads.tar.gz",
            "appwrite-config.tar.gz",
            "appwrite-certificates.tar.gz",
            "appwrite-functions.tar.gz"
        ]
    },
    "retention_days": ${RETENTION_DAYS}
}
EOF

# Calculate backup size
BACKUP_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)
log_info "Backup size: ${BACKUP_SIZE}"

# Create latest symlink
ln -sfn "${BACKUP_DIR}" "${BACKUP_ROOT}/latest"

# Cleanup old backups
log_info "Cleaning up backups older than ${RETENTION_DAYS} days..."
find "${BACKUP_ROOT}" -maxdepth 1 -type d -mtime +${RETENTION_DAYS} -exec rm -rf {} \;

# List remaining backups
BACKUP_COUNT=$(find "${BACKUP_ROOT}" -maxdepth 1 -type d -name "20*" | wc -l)
log_info "Total backups retained: ${BACKUP_COUNT}"

log_info "Backup complete: ${BACKUP_DIR}"
echo ""
echo "============================================="
echo "Backup Summary"
echo "============================================="
echo "Location: ${BACKUP_DIR}"
echo "Size: ${BACKUP_SIZE}"
echo "Retention: ${RETENTION_DAYS} days"
echo "Total Backups: ${BACKUP_COUNT}"
echo "============================================="
