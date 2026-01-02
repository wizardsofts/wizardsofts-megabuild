#!/bin/bash
# PostgreSQL Migration - Backup Script (Run on Server 10.0.0.80)
# This script creates backups of all databases from the source server

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="/tmp/postgres-migration-backup"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
POSTGRES_USER="postgres"
DATABASES=("ws_gibd_dse_company_info" "ws_gibd_dse_daily_trades")

echo -e "${GREEN}=== PostgreSQL Migration Backup Script ===${NC}"
echo -e "${YELLOW}Server: 10.0.0.80${NC}"
echo -e "${YELLOW}Timestamp: ${TIMESTAMP}${NC}"
echo ""

# Create backup directory
echo -e "${GREEN}Creating backup directory...${NC}"
mkdir -p "$BACKUP_DIR"
cd "$BACKUP_DIR"

# Backup roles and global objects
echo -e "${GREEN}Backing up roles and global objects...${NC}"
pg_dumpall -h localhost -U "$POSTGRES_USER" --roles-only > roles.sql
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Roles backed up successfully${NC}"
else
    echo -e "${RED}✗ Failed to backup roles${NC}"
    exit 1
fi

# Backup individual databases
for db in "${DATABASES[@]}"; do
    echo -e "${GREEN}Backing up database: ${db}...${NC}"

    # SQL format (more portable)
    pg_dump -h localhost -U "$POSTGRES_USER" -d "$db" > "${db}.sql"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ${db}.sql created${NC}"
    else
        echo -e "${RED}✗ Failed to backup ${db}${NC}"
        exit 1
    fi

    # Custom format (smaller, supports parallel restore)
    pg_dump -h localhost -U "$POSTGRES_USER" -d "$db" -F c -f "${db}.dump"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ${db}.dump created${NC}"
    else
        echo -e "${RED}✗ Failed to create ${db}.dump${NC}"
        exit 1
    fi

    # Get row counts for verification
    echo -e "${YELLOW}Getting row counts for ${db}...${NC}"
    psql -h localhost -U "$POSTGRES_USER" -d "$db" -c "
    SELECT
        schemaname,
        tablename,
        n_live_tup as row_count
    FROM pg_stat_user_tables
    ORDER BY n_live_tup DESC
    LIMIT 10;
    " > "${db}_table_counts.txt"
done

# Create metadata file
echo -e "${GREEN}Creating metadata file...${NC}"
cat > migration_metadata.txt <<EOF
PostgreSQL Migration Backup
===========================
Source Server: 10.0.0.80
Backup Date: $(date)
Timestamp: ${TIMESTAMP}
PostgreSQL Version: $(psql -h localhost -U "$POSTGRES_USER" -t -c "SELECT version();")

Databases Backed Up:
EOF

for db in "${DATABASES[@]}"; do
    echo "  - ${db}" >> migration_metadata.txt
    pg_dump -h localhost -U "$POSTGRES_USER" -d "$db" --schema-only | grep "CREATE TABLE" | wc -l | xargs echo "    Tables:" >> migration_metadata.txt
done

# Compress all backups
echo -e "${GREEN}Compressing backups...${NC}"
BACKUP_FILE="postgres-backup-${TIMESTAMP}.tar.gz"
tar -czf "$BACKUP_FILE" *.sql *.dump *.txt
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backup compressed: ${BACKUP_FILE}${NC}"
else
    echo -e "${RED}✗ Failed to compress backups${NC}"
    exit 1
fi

# Display backup info
echo ""
echo -e "${GREEN}=== Backup Summary ===${NC}"
ls -lh "$BACKUP_FILE"
echo ""
echo -e "${GREEN}Backup location: ${BACKUP_DIR}/${BACKUP_FILE}${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Transfer backup to server 10.0.0.84:"
echo -e "   ${GREEN}scp ${BACKUP_DIR}/${BACKUP_FILE} wizardsofts@10.0.0.84:/tmp/${NC}"
echo ""
echo -e "2. Or copy to local machine first:"
echo -e "   ${GREEN}scp wizardsofts@10.0.0.80:${BACKUP_DIR}/${BACKUP_FILE} ./${NC}"
echo -e "   ${GREEN}scp ${BACKUP_FILE} wizardsofts@10.0.0.84:/tmp/${NC}"
echo ""
echo -e "${GREEN}Backup completed successfully!${NC}"
