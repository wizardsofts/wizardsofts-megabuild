#!/bin/bash
# PostgreSQL Migration - Pre-Migration Verification Script
# This script verifies that both servers are ready for migration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== PostgreSQL Migration Pre-Flight Check ===${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Function to check command existence
check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✓ $1 is installed${NC}"
        return 0
    else
        echo -e "${RED}✗ $1 is NOT installed${NC}"
        ((ERRORS++))
        return 1
    fi
}

# Function to check SSH connectivity
check_ssh() {
    local server=$1
    echo -e "${YELLOW}Checking SSH connection to ${server}...${NC}"

    if ssh -o ConnectTimeout=5 -o BatchMode=yes wizardsofts@${server} "echo connected" 2>/dev/null | grep -q "connected"; then
        echo -e "${GREEN}✓ SSH connection to ${server} successful${NC}"
        return 0
    else
        echo -e "${RED}✗ Cannot connect to ${server} via SSH${NC}"
        echo -e "${YELLOW}  Make sure you have SSH keys set up or password-less access configured${NC}"
        ((ERRORS++))
        return 1
    fi
}

# Function to check PostgreSQL on server
check_postgres() {
    local server=$1
    echo -e "${YELLOW}Checking PostgreSQL on ${server}...${NC}"

    # This is a simplified check - adjust based on your setup
    if ssh wizardsofts@${server} "which psql" &>/dev/null; then
        echo -e "${GREEN}✓ PostgreSQL client found on ${server}${NC}"
    else
        echo -e "${YELLOW}⚠ PostgreSQL client not found on ${server}${NC}"
        echo -e "${YELLOW}  This might be okay if PostgreSQL is running in Docker${NC}"
        ((WARNINGS++))
    fi
}

# Function to check Docker on server
check_docker() {
    local server=$1
    echo -e "${YELLOW}Checking Docker on ${server}...${NC}"

    if ssh wizardsofts@${server} "docker --version" &>/dev/null; then
        echo -e "${GREEN}✓ Docker is installed on ${server}${NC}"

        # Check if user can run docker commands
        if ssh wizardsofts@${server} "docker ps" &>/dev/null; then
            echo -e "${GREEN}✓ Docker is accessible on ${server}${NC}"
        else
            echo -e "${YELLOW}⚠ User cannot run docker commands on ${server}${NC}"
            echo -e "${YELLOW}  May need to use sudo or add user to docker group${NC}"
            ((WARNINGS++))
        fi
    else
        echo -e "${RED}✗ Docker is NOT installed on ${server}${NC}"
        ((ERRORS++))
    fi
}

# Function to check disk space
check_disk_space() {
    local server=$1
    echo -e "${YELLOW}Checking disk space on ${server}...${NC}"

    local available=$(ssh wizardsofts@${server} "df -h /tmp | tail -1 | awk '{print \$4}'" 2>/dev/null)

    if [ -n "$available" ]; then
        echo -e "${GREEN}✓ Available space on ${server} /tmp: ${available}${NC}"
        echo -e "${YELLOW}  Note: Ensure you have at least 5GB free for backups${NC}"
    else
        echo -e "${YELLOW}⚠ Could not check disk space on ${server}${NC}"
        ((WARNINGS++))
    fi
}

echo -e "${GREEN}=== Checking Local Environment ===${NC}"
check_command "ssh"
check_command "scp"
check_command "psql" || echo -e "${YELLOW}  (Optional - can use Docker instead)${NC}"

echo ""
echo -e "${GREEN}=== Checking Server 10.0.0.80 (Source) ===${NC}"
if check_ssh "10.0.0.80"; then
    check_postgres "10.0.0.80"
    check_docker "10.0.0.80"
    check_disk_space "10.0.0.80"

    # Check if PostgreSQL is actually accessible
    echo -e "${YELLOW}Checking PostgreSQL accessibility on 10.0.0.80...${NC}"
    if ssh wizardsofts@10.0.0.80 "psql -h localhost -U postgres -c 'SELECT 1;' &>/dev/null" || \
       ssh wizardsofts@10.0.0.80 "docker exec -i \$(docker ps -q -f name=postgres) psql -U postgres -c 'SELECT 1;' &>/dev/null"; then
        echo -e "${GREEN}✓ PostgreSQL is accessible on 10.0.0.80${NC}"
    else
        echo -e "${RED}✗ Cannot access PostgreSQL on 10.0.0.80${NC}"
        ((ERRORS++))
    fi
fi

echo ""
echo -e "${GREEN}=== Checking Server 10.0.0.84 (Destination) ===${NC}"
if check_ssh "10.0.0.84"; then
    check_docker "10.0.0.84"
    check_disk_space "10.0.0.84"

    # Check if project directory exists
    echo -e "${YELLOW}Checking project directory on 10.0.0.84...${NC}"
    if ssh wizardsofts@10.0.0.84 "test -d /opt/wizardsofts-megabuild"; then
        echo -e "${GREEN}✓ Project directory exists on 10.0.0.84${NC}"
    else
        echo -e "${RED}✗ Project directory not found on 10.0.0.84${NC}"
        echo -e "${YELLOW}  Expected: /opt/wizardsofts-megabuild${NC}"
        ((ERRORS++))
    fi

    # Check if PostgreSQL docker-compose exists
    echo -e "${YELLOW}Checking PostgreSQL setup on 10.0.0.84...${NC}"
    if ssh wizardsofts@10.0.0.84 "test -f /opt/wizardsofts-megabuild/infrastructure/postgresql/docker-compose.yml"; then
        echo -e "${GREEN}✓ PostgreSQL docker-compose.yml found${NC}"
    else
        echo -e "${RED}✗ PostgreSQL docker-compose.yml not found${NC}"
        ((ERRORS++))
    fi
fi

echo ""
echo -e "${GREEN}=== Checking Local Scripts ===${NC}"

SCRIPT_DIR="/Users/mashfiqurrahman/Workspace/wizardsofts-megabuild/scripts"
REQUIRED_SCRIPTS=(
    "migrate-postgres-backup.sh"
    "migrate-postgres-restore.sh"
    "migrate-postgres-update-configs.sh"
)

for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [ -f "${SCRIPT_DIR}/${script}" ] && [ -x "${SCRIPT_DIR}/${script}" ]; then
        echo -e "${GREEN}✓ ${script} exists and is executable${NC}"
    elif [ -f "${SCRIPT_DIR}/${script}" ]; then
        echo -e "${YELLOW}⚠ ${script} exists but is not executable${NC}"
        echo -e "${YELLOW}  Run: chmod +x ${SCRIPT_DIR}/${script}${NC}"
        ((WARNINGS++))
    else
        echo -e "${RED}✗ ${script} not found${NC}"
        ((ERRORS++))
    fi
done

# Summary
echo ""
echo -e "${GREEN}=== Pre-Flight Check Summary ===${NC}"
echo -e "Errors: ${RED}${ERRORS}${NC}"
echo -e "Warnings: ${YELLOW}${WARNINGS}${NC}"
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ All critical checks passed!${NC}"
    echo -e "${GREEN}You are ready to proceed with the migration.${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "1. Review the migration plan: ${GREEN}cat POSTGRESQL_MIGRATION_PLAN.md${NC}"
    echo -e "2. Follow the quick start guide: ${GREEN}cat POSTGRESQL_MIGRATION_QUICKSTART.md${NC}"
    echo -e "3. Begin with backup: ${GREEN}./scripts/migrate-postgres-backup.sh${NC}"
    exit 0
else
    echo -e "${RED}✗ ${ERRORS} critical issue(s) found!${NC}"
    echo -e "${RED}Please resolve the errors before proceeding with migration.${NC}"
    exit 1
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠ ${WARNINGS} warning(s) found - review before proceeding${NC}"
fi
