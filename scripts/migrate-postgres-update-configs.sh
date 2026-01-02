#!/bin/bash
# PostgreSQL Migration - Configuration Update Script
# This script updates all application configuration files to point to the new server

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
OLD_SERVER="10.0.0.80"
NEW_SERVER="10.0.0.84"
PROJECT_ROOT="/opt/wizardsofts-megabuild"

echo -e "${GREEN}=== PostgreSQL Migration - Configuration Update ===${NC}"
echo -e "${YELLOW}Updating configurations from ${OLD_SERVER} to ${NEW_SERVER}${NC}"
echo ""

# Confirm action
read -p "This will update configuration files. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo -e "${YELLOW}Update cancelled.${NC}"
    exit 0
fi

# Change to project root
cd "$PROJECT_ROOT"

# Backup configurations before updating
BACKUP_DIR="/tmp/config-backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo -e "${GREEN}Creating backup of configurations in ${BACKUP_DIR}${NC}"

# Files to update
CONFIG_FILES=(
    "apps/ws-company/src/main/resources/application-hp.properties"
    "apps/ws-trades/src/main/resources/application-hp.properties"
    "apps/ws-company/src/main/resources/application.properties"
    "apps/ws-trades/src/main/resources/application.properties"
)

# Backup each file
for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        cp "$file" "$BACKUP_DIR/"
        echo -e "${GREEN}✓ Backed up: ${file}${NC}"
    fi
done

echo ""
echo -e "${GREEN}Updating configuration files...${NC}"

# Update ws-company application-hp.properties
FILE="apps/ws-company/src/main/resources/application-hp.properties"
if [ -f "$FILE" ]; then
    echo -e "${YELLOW}Updating ${FILE}...${NC}"
    sed -i.bak "s|jdbc:postgresql://${OLD_SERVER}|jdbc:postgresql://${NEW_SERVER}|g" "$FILE"
    echo -e "${GREEN}✓ Updated ${FILE}${NC}"
    rm -f "${FILE}.bak"
fi

# Update ws-trades application-hp.properties
FILE="apps/ws-trades/src/main/resources/application-hp.properties"
if [ -f "$FILE" ]; then
    echo -e "${YELLOW}Updating ${FILE}...${NC}"
    sed -i.bak "s|jdbc:postgresql://${OLD_SERVER}|jdbc:postgresql://${NEW_SERVER}|g" "$FILE"
    echo -e "${GREEN}✓ Updated ${FILE}${NC}"
    rm -f "${FILE}.bak"
fi

# Update Spring Cloud Config Server references
FILE="apps/ws-company/src/main/resources/application.properties"
if [ -f "$FILE" ]; then
    echo -e "${YELLOW}Updating ${FILE}...${NC}"
    sed -i.bak "s|http://${OLD_SERVER}:8888|http://${NEW_SERVER}:8888|g" "$FILE"
    echo -e "${GREEN}✓ Updated ${FILE}${NC}"
    rm -f "${FILE}.bak"
fi

FILE="apps/ws-trades/src/main/resources/application.properties"
if [ -f "$FILE" ]; then
    echo -e "${YELLOW}Updating ${FILE}...${NC}"
    sed -i.bak "s|http://${OLD_SERVER}:8888|http://${NEW_SERVER}:8888|g" "$FILE"
    echo -e "${GREEN}✓ Updated ${FILE}${NC}"
    rm -f "${FILE}.bak"
fi

# Verify changes
echo ""
echo -e "${GREEN}=== Verification ===${NC}"
echo -e "${YELLOW}Checking for remaining references to ${OLD_SERVER}...${NC}"

REMAINING=$(grep -r "${OLD_SERVER}" apps/ws-company/src/main/resources/ apps/ws-trades/src/main/resources/ 2>/dev/null | grep -v ".bak" || true)

if [ -n "$REMAINING" ]; then
    echo -e "${YELLOW}Warning: Found remaining references to ${OLD_SERVER}:${NC}"
    echo "$REMAINING"
    echo ""
    echo -e "${YELLOW}Please review these manually.${NC}"
else
    echo -e "${GREEN}✓ No remaining references to ${OLD_SERVER} found${NC}"
fi

# Display updated configurations
echo ""
echo -e "${GREEN}=== Updated Configurations ===${NC}"
echo ""
echo -e "${YELLOW}ws-company (application-hp.properties):${NC}"
grep "datasource.url" "apps/ws-company/src/main/resources/application-hp.properties" || true
echo ""
echo -e "${YELLOW}ws-trades (application-hp.properties):${NC}"
grep "datasource.url" "apps/ws-trades/src/main/resources/application-hp.properties" || true

# Summary
echo ""
echo -e "${GREEN}=== Configuration Update Summary ===${NC}"
echo -e "${GREEN}✓ Configuration files updated${NC}"
echo -e "${GREEN}✓ Backup created: ${BACKUP_DIR}${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Review the changes:"
echo -e "   ${GREEN}git diff${NC}"
echo ""
echo -e "2. Rebuild affected services:"
echo -e "   ${GREEN}docker-compose build ws-company ws-trades${NC}"
echo ""
echo -e "3. Restart services:"
echo -e "   ${GREEN}docker-compose up -d ws-company ws-trades${NC}"
echo ""
echo -e "4. Restart Python services that use PostgreSQL:"
echo -e "   ${GREEN}docker-compose restart gibd-quant-signal gibd-quant-nlq gibd-quant-calibration gibd-quant-celery${NC}"
echo ""
echo -e "5. Verify application logs:"
echo -e "   ${GREEN}docker-compose logs -f ws-company${NC}"
echo -e "   ${GREEN}docker-compose logs -f ws-trades${NC}"
echo ""
echo -e "${GREEN}Configuration update completed!${NC}"
