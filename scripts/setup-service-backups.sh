#!/bin/bash
################################################################################
# setup-service-backups.sh
#
# Purpose: Automate NFS backup configuration for services
#          Follows AGENT.md Section 9.1 (Service Backup Storage Convention)
#
# Based on: GitLab backup setup (2026-01-08)
#           Standard: /mnt/data/Backups/server/<service-name>/
#
# Usage: ./setup-service-backups.sh <service-name> <service-host> <nfs-server> [options]
#
# Options:
#   --uid <uid>          Service UID (default: auto-detect from container)
#   --gid <gid>          Service GID (default: auto-detect from container)
#   --retention <days>   Backup retention in days (default: 7)
#   --dry-run            Show what would be done without making changes
#
# Examples:
#   ./setup-service-backups.sh gitlab 10.0.0.84 10.0.0.80
#   ./setup-service-backups.sh keycloak 10.0.0.84 10.0.0.80 --uid 1000 --gid 1000
#   ./setup-service-backups.sh nexus 10.0.0.84 10.0.0.80 --dry-run
#
################################################################################

set -e

# Cleanup handler
cleanup() {
    local exit_code="${1:-0}"
    # Cleanup logic if needed
    exit "${exit_code}"
}
trap 'cleanup 130' INT TERM

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SERVICE_NAME="${1}"
SERVICE_HOST="${2}"
NFS_SERVER="${3}"
SSH_USER="${SSH_USER:-agent}"
SERVICE_UID=""
SERVICE_GID=""
RETENTION_DAYS=7
DRY_RUN=false

# Load environment variables from .env if it exists
if [[ -f ".env" ]]; then
    # shellcheck disable=SC1091
    source .env
fi

# Parse options
shift 3 2>/dev/null || true
while [[ $# -gt 0 ]]; do
    case $1 in
        --uid)
            SERVICE_UID="$2"
            shift 2
            ;;
        --gid)
            SERVICE_GID="$2"
            shift 2
            ;;
        --retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            exit 1
            ;;
    esac
done

# Validate inputs
if [[ -z "$SERVICE_NAME" ]] || [[ -z "$SERVICE_HOST" ]] || [[ -z "$NFS_SERVER" ]]; then
    echo "Usage: $0 <service-name> <service-host> <nfs-server> [options]"
    echo ""
    echo "Options:"
    echo "  --uid <uid>          Service UID (default: auto-detect)"
    echo "  --gid <gid>          Service GID (default: auto-detect)"
    echo "  --retention <days>   Backup retention in days (default: 7)"
    echo "  --dry-run            Show what would be done"
    exit 1
fi

# Banner
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Backup Setup: $SERVICE_NAME${NC}"
echo -e "${BLUE}  Service Host: $SERVICE_HOST${NC}"
echo -e "${BLUE}  NFS Server: $NFS_SERVER${NC}"
if [[ "$DRY_RUN" == true ]]; then
    echo -e "${YELLOW}  Mode: DRY RUN (no changes)${NC}"
fi
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Auto-detect UID/GID if not provided
if [[ -z "$SERVICE_UID" ]] || [[ -z "$SERVICE_GID" ]]; then
    echo -e "${BLUE}[1/6] Auto-detecting service UID/GID...${NC}"
    
    # Try to get UID/GID from running container
    CONTAINER_USER=$(ssh "${SSH_USER}@${SERVICE_HOST}" "docker exec \"${SERVICE_NAME}\" id -u 2>/dev/null || echo ''" 2>&1)
    CONTAINER_GROUP=$(ssh "${SSH_USER}@${SERVICE_HOST}" "docker exec \"${SERVICE_NAME}\" id -g 2>/dev/null || echo ''" 2>&1)
    
    if [[ -n "$CONTAINER_USER" ]] && [[ -n "$CONTAINER_GROUP" ]]; then
        SERVICE_UID="${SERVICE_UID:-$CONTAINER_USER}"
        SERVICE_GID="${SERVICE_GID:-$CONTAINER_GROUP}"
        echo -e "  ${GREEN}✅${NC} Detected UID: $SERVICE_UID, GID: $SERVICE_GID"
    else
        echo -e "  ${YELLOW}⚠️${NC}  Could not auto-detect UID/GID. Please provide --uid and --gid"
        exit 1
    fi
else
    echo -e "${BLUE}[1/6] Using provided UID/GID...${NC}"
    echo -e "  ${GREEN}✅${NC} UID: $SERVICE_UID, GID: $SERVICE_GID"
fi

# Step 2: Create backup directory on NFS server
echo ""
echo -e "${BLUE}[2/6] Creating backup directory on NFS server...${NC}"
BACKUP_PATH="/mnt/data/Backups/server/${SERVICE_NAME}"

if [[ "$DRY_RUN" == true ]]; then
    echo -e "  ${YELLOW}[DRY RUN]${NC} Would create: $BACKUP_PATH"
    echo -e "  ${YELLOW}[DRY RUN]${NC} Would run: ssh ${SSH_USER}@${NFS_SERVER} \"sudo mkdir -p ${BACKUP_PATH}\""
    echo -e "  ${YELLOW}[DRY RUN]${NC} Would run: ssh ${SSH_USER}@${NFS_SERVER} \"sudo chown ${SERVICE_UID}:${SERVICE_GID} ${BACKUP_PATH}\""
else
    ssh "${SSH_USER}@${NFS_SERVER}" "sudo mkdir -p \"${BACKUP_PATH}\""
    ssh "${SSH_USER}@${NFS_SERVER}" "sudo chown \"${SERVICE_UID}:${SERVICE_GID}\" \"${BACKUP_PATH}\""
    echo -e "  ${GREEN}✅${NC} Created and configured: $BACKUP_PATH"
fi

# Step 3: Verify NFS export configuration
echo ""
echo -e "${BLUE}[3/6] Verifying NFS export configuration...${NC}"

NFS_EXPORT_CHECK=$(ssh "${SSH_USER}@${NFS_SERVER}" "grep '/mnt/data' /etc/exports 2>/dev/null || echo 'not-found'" 2>&1)

if [[ "$NFS_EXPORT_CHECK" == "not-found" ]]; then
    echo -e "  ${RED}❌${NC} /mnt/data not found in /etc/exports"
    echo -e "  ${YELLOW}⚠️${NC}  Please add the following to /etc/exports on $NFS_SERVER:"
    echo ""
    echo "  /mnt/data 10.0.0.0/24(rw,sync,no_root_squash,no_all_squash,no_subtree_check)"
    echo ""
    exit 1
else
    echo -e "  ${GREEN}✅${NC} /mnt/data is exported"
    echo "     Export config:"
    echo "$NFS_EXPORT_CHECK" | head -1 | sed 's/^/     /'
    
    # Check for no_root_squash
    if echo "$NFS_EXPORT_CHECK" | grep -q "no_root_squash"; then
        echo -e "  ${GREEN}✅${NC} no_root_squash is enabled (correct)"
    else
        echo -e "  ${YELLOW}⚠️${NC}  no_root_squash not found - this may cause permission issues"
        echo -e "     Recommendation: Add no_root_squash to the export options"
    fi
fi

# Step 4: Create mount point on service host
echo ""
echo -e "${BLUE}[4/6] Creating mount point on service host...${NC}"
MOUNT_POINT="/mnt/${SERVICE_NAME}-backups"

if [[ "$DRY_RUN" == true ]]; then
    echo -e "  ${YELLOW}[DRY RUN]${NC} Would create: $MOUNT_POINT"
    echo -e "  ${YELLOW}[DRY RUN]${NC} Would run: ssh ${SSH_USER}@${SERVICE_HOST} \"sudo mkdir -p ${MOUNT_POINT}\""
else
    ssh "${SSH_USER}@${SERVICE_HOST}" "sudo mkdir -p \"${MOUNT_POINT}\""
    echo -e "  ${GREEN}✅${NC} Created mount point: $MOUNT_POINT"
fi

# Step 5: Mount NFS and add to fstab
echo ""
echo -e "${BLUE}[5/6] Configuring NFS mount...${NC}"

# Check if already mounted
ALREADY_MOUNTED=$(ssh "${SSH_USER}@${SERVICE_HOST}" "mount | grep \"${MOUNT_POINT}\" || echo ''" 2>&1)

if [[ -n "$ALREADY_MOUNTED" ]]; then
    echo -e "  ${YELLOW}⚠️${NC}  Already mounted:"
    echo "     $ALREADY_MOUNTED"
else
    if [[ "$DRY_RUN" == true ]]; then
        echo -e "  ${YELLOW}[DRY RUN]${NC} Would mount: ${NFS_SERVER}:${BACKUP_PATH} to ${MOUNT_POINT}"
        echo -e "  ${YELLOW}[DRY RUN]${NC} Would run: ssh ${SSH_USER}@${SERVICE_HOST} \"sudo mount -t nfs ${NFS_SERVER}:${BACKUP_PATH} ${MOUNT_POINT}\""
    else
        ssh "${SSH_USER}@${SERVICE_HOST}" "sudo mount -t nfs \"${NFS_SERVER}:${BACKUP_PATH}\" \"${MOUNT_POINT}\""
        echo -e "  ${GREEN}✅${NC} Mounted NFS share"
    fi
fi

# Add to fstab for persistence
FSTAB_ENTRY="${NFS_SERVER}:${BACKUP_PATH} ${MOUNT_POINT} nfs defaults 0 0"
FSTAB_EXISTS=$(ssh "${SSH_USER}@${SERVICE_HOST}" "grep \"^${NFS_SERVER}:${BACKUP_PATH}[[:space:]]\" /etc/fstab || echo ''" 2>&1)

if [[ -n "$FSTAB_EXISTS" ]]; then
    echo -e "  ${YELLOW}⚠️${NC}  fstab entry already exists"
else
    if [[ "$DRY_RUN" == true ]]; then
        echo -e "  ${YELLOW}[DRY RUN]${NC} Would add to /etc/fstab: $FSTAB_ENTRY"
    else
        ssh "${SSH_USER}@${SERVICE_HOST}" "echo '${FSTAB_ENTRY}' | sudo tee -a /etc/fstab > /dev/null"
        echo -e "  ${GREEN}✅${NC} Added to /etc/fstab for persistence"
    fi
fi

# Step 6: Provide docker-compose configuration
echo ""
echo -e "${BLUE}[6/6] Docker Compose configuration${NC}"
echo ""
echo -e "${YELLOW}Add the following to your docker-compose.yml:${NC}"
echo ""
echo "  services:"
echo "    ${SERVICE_NAME}:"
echo "      volumes:"
echo "        - ${MOUNT_POINT}:/var/backups/${SERVICE_NAME}"
echo ""
echo -e "${YELLOW}Configure backup retention (inside service):${NC}"
echo ""
echo "  # For GitLab (gitlab.rb):"
echo "  gitlab_rails['backup_keep_time'] = $((RETENTION_DAYS * 86400))  # ${RETENTION_DAYS} days in seconds"
echo ""
echo "  # For generic backups (cron job):"
echo "  find ${MOUNT_POINT} -type f -mtime +${RETENTION_DAYS} -delete"
echo ""

# Summary
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Setup Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "  Service:        $SERVICE_NAME"
echo "  NFS Path:       ${NFS_SERVER}:${BACKUP_PATH}"
echo "  Mount Point:    ${MOUNT_POINT}"
echo "  UID:GID:        ${SERVICE_UID}:${SERVICE_GID}"
echo "  Retention:      ${RETENTION_DAYS} days"
echo ""

if [[ "$DRY_RUN" == true ]]; then
    echo -e "${YELLOW}⚠️  This was a DRY RUN - no changes were made${NC}"
    echo -e "${YELLOW}   Run without --dry-run to apply changes${NC}"
else
    echo -e "${GREEN}✅ Backup configuration complete${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Update docker-compose.yml with the volume mount"
    echo "  2. Restart the service: docker-compose restart ${SERVICE_NAME}"
    echo "  3. Test backup creation"
    echo "  4. Verify backups appear in: ${MOUNT_POINT}"
fi

echo ""
