#!/bin/bash
# PostgreSQL Migration - Restore Script (Run on Server 10.0.0.84)
# This script restores databases to the new server

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration (use environment variables for secrets)
BACKUP_DIR="/tmp"
CONTAINER_NAME="gibd-postgres"
POSTGRES_USER="postgres"
DB_PASSWORD="${DB_PASSWORD:?Error: DB_PASSWORD environment variable must be set}"
DATABASES=("ws_gibd_dse_company_info" "ws_gibd_dse_daily_trades")

echo -e "${GREEN}=== PostgreSQL Migration Restore Script ===${NC}"
echo -e "${YELLOW}Server: 10.0.0.84${NC}"
echo ""

# Check if backup file is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Please provide backup file name${NC}"
    echo -e "Usage: $0 <backup-file.tar.gz>"
    echo ""
    echo "Available backup files in /tmp:"
    ls -lh /tmp/postgres-backup-*.tar.gz 2>/dev/null || echo "No backup files found"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_DIR/$BACKUP_FILE${NC}"
    exit 1
fi

# Extract backup
echo -e "${GREEN}Extracting backup file...${NC}"
cd "$BACKUP_DIR"
tar -xzf "$BACKUP_FILE"
echo -e "${GREEN}✓ Backup extracted${NC}"

# Check if PostgreSQL container is running
echo -e "${GREEN}Checking PostgreSQL container...${NC}"
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}Error: PostgreSQL container is not running${NC}"
    echo -e "Please start it first:"
    echo -e "  ${GREEN}cd /opt/wizardsofts-megabuild/infrastructure/postgresql${NC}"
    echo -e "  ${GREEN}docker-compose up -d${NC}"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL container is running${NC}"

# Wait for PostgreSQL to be ready
echo -e "${GREEN}Waiting for PostgreSQL to be ready...${NC}"
for i in {1..30}; do
    if docker exec "$CONTAINER_NAME" pg_isready -U "$POSTGRES_USER" &>/dev/null; then
        echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Create users
echo -e "${GREEN}Creating database users...${NC}"
docker exec -i "$CONTAINER_NAME" psql -U "$POSTGRES_USER" <<EOF
-- Create users if they don't exist
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'gibd') THEN
        CREATE USER gibd WITH PASSWORD '${DB_PASSWORD}';
    END IF;
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'ws_gibd') THEN
        CREATE USER ws_gibd WITH PASSWORD '${DB_PASSWORD}';
    END IF;
END
\$\$;
EOF
echo -e "${GREEN}✓ Users created/verified${NC}"

# Restore databases
for db in "${DATABASES[@]}"; do
    echo ""
    echo -e "${GREEN}=== Restoring database: ${db} ===${NC}"

    # Drop database if exists (careful!)
    echo -e "${YELLOW}Dropping existing database (if exists)...${NC}"
    docker exec -i "$CONTAINER_NAME" psql -U "$POSTGRES_USER" <<EOF
DROP DATABASE IF EXISTS ${db};
EOF

    # Create database
    echo -e "${GREEN}Creating database...${NC}"
    docker exec -i "$CONTAINER_NAME" psql -U "$POSTGRES_USER" <<EOF
CREATE DATABASE ${db} OWNER gibd;
GRANT ALL PRIVILEGES ON DATABASE ${db} TO gibd;
GRANT ALL PRIVILEGES ON DATABASE ${db} TO ws_gibd;
EOF
    echo -e "${GREEN}✓ Database ${db} created${NC}"

    # Copy SQL file to container
    echo -e "${GREEN}Copying backup files to container...${NC}"
    docker cp "${BACKUP_DIR}/${db}.sql" "${CONTAINER_NAME}:/tmp/${db}.sql"

    # Restore from SQL dump
    echo -e "${GREEN}Restoring data from SQL dump...${NC}"
    docker exec -i "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$db" -f "/tmp/${db}.sql"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ ${db} restored successfully${NC}"
    else
        echo -e "${RED}✗ Failed to restore ${db}${NC}"
        exit 1
    fi

    # Cleanup
    docker exec "$CONTAINER_NAME" rm "/tmp/${db}.sql"

    # Verify restoration
    echo -e "${GREEN}Verifying restoration...${NC}"
    docker exec -i "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$db" <<EOF
\dt
SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema = 'public';
EOF

    # Compare row counts with original
    if [ -f "${db}_table_counts.txt" ]; then
        echo -e "${YELLOW}Original table counts:${NC}"
        cat "${db}_table_counts.txt"

        echo -e "${YELLOW}Current table counts:${NC}"
        docker exec -i "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$db" -c "
        SELECT
            schemaname,
            tablename,
            n_live_tup as row_count
        FROM pg_stat_user_tables
        ORDER BY n_live_tup DESC
        LIMIT 10;
        "
    fi
done

# Set proper permissions
echo -e "${GREEN}Setting database permissions...${NC}"
for db in "${DATABASES[@]}"; do
    docker exec -i "$CONTAINER_NAME" psql -U "$POSTGRES_USER" -d "$db" <<EOF
-- Grant schema permissions
GRANT ALL ON SCHEMA public TO gibd;
GRANT ALL ON SCHEMA public TO ws_gibd;

-- Grant table permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO gibd;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ws_gibd;

-- Grant sequence permissions
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO gibd;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ws_gibd;

-- Set default privileges
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO gibd;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ws_gibd;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO gibd;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ws_gibd;
EOF
done
echo -e "${GREEN}✓ Permissions set${NC}"

# Final verification
echo ""
echo -e "${GREEN}=== Final Verification ===${NC}"
for db in "${DATABASES[@]}"; do
    echo -e "${YELLOW}Testing connection to ${db}...${NC}"
    docker exec -i "$CONTAINER_NAME" psql -U gibd -d "$db" -c "SELECT 'Connection successful to ${db}' as status;"
    echo -e "${GREEN}✓ ${db} connection verified${NC}"
done

# Display summary
echo ""
echo -e "${GREEN}=== Restoration Summary ===${NC}"
echo -e "${GREEN}All databases restored successfully!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Update application configuration files to point to 10.0.0.84"
echo -e "2. Restart affected applications"
echo -e "3. Test application connectivity"
echo -e "4. Monitor for 24-48 hours before removing server 10.0.0.80"
echo ""
echo -e "${GREEN}Restoration completed successfully!${NC}"
