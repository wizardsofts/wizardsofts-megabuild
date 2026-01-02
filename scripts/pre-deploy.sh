#!/bin/bash
# Pre-Deployment Script
# Creates backups and prepares the environment for safe deployment
# Usage: ./pre-deploy.sh <server-ip> [service-name]

set -e

SERVER_IP=$1
SERVICE_NAME=${2:-"all"}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_step() {
    echo ""
    echo -e "${GREEN}===${NC} $1"
}

# Function to backup Traefik configuration
backup_traefik_config() {
    local server=$1

    log_step "Backing up Traefik Configuration"

    # Create backup via SSH
    ssh "wizardsofts@${server}" << 'EOF'
cd /home/wizardsofts/traefik
if [ -f traefik.yml ]; then
    BACKUP_NAME="traefik.yml.backup.$(date +%Y%m%d_%H%M%S)"
    cp traefik.yml "$BACKUP_NAME"
    echo "Created backup: $BACKUP_NAME"

    # Keep only last 10 backups
    ls -t traefik.yml.backup.* 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
    echo "Cleaned up old backups (keeping last 10)"
else
    echo "Warning: traefik.yml not found"
    exit 1
fi
EOF

    if [ $? -eq 0 ]; then
        log_success "Traefik configuration backed up"
        return 0
    else
        log_error "Failed to backup Traefik configuration"
        return 1
    fi
}

# Function to backup Docker Compose files
backup_compose_files() {
    local server=$1
    local service_dir=$2

    log_info "Backing up Docker Compose files in: $service_dir"

    ssh "wizardsofts@${server}" << EOF
if [ -d "$service_dir" ]; then
    cd "$service_dir"

    for file in docker-compose*.yml; do
        if [ -f "\$file" ]; then
            BACKUP_NAME="\${file}.backup.${TIMESTAMP}"
            cp "\$file" "\$BACKUP_NAME"
            echo "Created backup: \$BACKUP_NAME"
        fi
    done

    # Keep only last 10 backups per file
    for file in docker-compose*.yml; do
        ls -t "\${file}.backup."* 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true
    done
    echo "Cleaned up old backups"
else
    echo "Warning: Directory not found: $service_dir"
    exit 1
fi
EOF

    if [ $? -eq 0 ]; then
        log_success "Docker Compose files backed up"
        return 0
    else
        log_warn "Could not backup Docker Compose files in $service_dir"
        return 1
    fi
}

# Function to check disk space
check_disk_space() {
    local server=$1

    log_step "Checking Disk Space"

    local disk_usage=$(ssh "wizardsofts@${server}" "df -h / | tail -1 | awk '{print \$5}' | sed 's/%//'" 2>/dev/null || echo "100")

    log_info "Disk usage: ${disk_usage}%"

    if [ "$disk_usage" -ge 90 ]; then
        log_error "Disk usage critical: ${disk_usage}%"
        return 1
    elif [ "$disk_usage" -ge 80 ]; then
        log_warn "Disk usage high: ${disk_usage}%"
        return 0
    else
        log_success "Disk space available: $((100 - disk_usage))%"
        return 0
    fi
}

# Function to check running containers
check_running_containers() {
    local server=$1

    log_step "Checking Running Containers"

    local container_count=$(ssh "wizardsofts@${server}" "docker ps -q | wc -l" 2>/dev/null || echo "0")

    log_info "Running containers: $container_count"

    if [ "$container_count" -eq 0 ]; then
        log_warn "No containers are running!"
        return 1
    else
        ssh "wizardsofts@${server}" "docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -E 'traefik|wizardsofts|padmafoods|gibd-quant' || true"
        return 0
    fi
}

# Function to verify connectivity to Docker daemon
check_docker_daemon() {
    local server=$1

    log_info "Checking Docker daemon"

    if ssh "wizardsofts@${server}" "docker info > /dev/null 2>&1"; then
        log_success "Docker daemon is accessible"
        return 0
    else
        log_error "Cannot connect to Docker daemon"
        return 1
    fi
}

# Function to clean up old Docker resources
cleanup_docker() {
    local server=$1

    log_step "Cleaning Up Docker Resources"

    log_info "Removing dangling images..."
    ssh "wizardsofts@${server}" "docker image prune -f 2>&1" || true

    log_info "Removing unused networks..."
    ssh "wizardsofts@${server}" "docker network prune -f 2>&1" || true

    log_success "Docker cleanup completed"
}

# Function to create deployment snapshot
create_deployment_snapshot() {
    local server=$1

    log_step "Creating Deployment Snapshot"

    ssh "wizardsofts@${server}" << 'EOF'
SNAPSHOT_DIR="/home/wizardsofts/deployment-snapshots/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$SNAPSHOT_DIR"

# Save container states
docker ps --format '{{.Names}}\t{{.Status}}\t{{.Image}}' > "$SNAPSHOT_DIR/containers.txt"

# Save network info
docker network ls > "$SNAPSHOT_DIR/networks.txt"

# Save running service versions
docker images --format '{{.Repository}}\t{{.Tag}}\t{{.ID}}' | grep -E 'wizardsofts|padmafoods|gibd-quant|traefik' > "$SNAPSHOT_DIR/images.txt"

echo "Snapshot saved to: $SNAPSHOT_DIR"

# Keep only last 20 snapshots
cd /home/wizardsofts/deployment-snapshots
ls -dt */ | tail -n +21 | xargs rm -rf 2>/dev/null || true
EOF

    if [ $? -eq 0 ]; then
        log_success "Deployment snapshot created"
        return 0
    else
        log_warn "Could not create deployment snapshot"
        return 1
    fi
}

# Main pre-deployment logic
main() {
    local exit_code=0

    echo "========================================="
    echo "  Pre-Deployment Preparation"
    echo "========================================="
    echo ""

    if [[ -z "$SERVER_IP" ]]; then
        log_error "Usage: $0 <server-ip> [service-name]"
        echo "Example: $0 10.0.0.84"
        echo "Example: $0 10.0.0.84 ws-wizardsofts-web"
        exit 1
    fi

    log_info "Target server: $SERVER_IP"
    log_info "Service: $SERVICE_NAME"
    log_info "Timestamp: $TIMESTAMP"
    echo ""

    # Check SSH connectivity
    log_info "Checking SSH connectivity..."
    if ! ssh -o ConnectTimeout=10 "wizardsofts@${SERVER_IP}" "echo 'SSH connection successful'" > /dev/null 2>&1; then
        log_error "Cannot connect to server via SSH"
        exit 1
    fi
    log_success "SSH connection established"

    # Check Docker daemon
    if ! check_docker_daemon "$SERVER_IP"; then
        exit_code=1
    fi

    # Check disk space
    if ! check_disk_space "$SERVER_IP"; then
        exit_code=1
    fi

    # Check running containers
    check_running_containers "$SERVER_IP"

    # Backup Traefik configuration
    if ! backup_traefik_config "$SERVER_IP"; then
        exit_code=1
    fi

    # Backup service-specific configurations
    case "$SERVICE_NAME" in
        "ws-wizardsofts-web")
            backup_compose_files "$SERVER_IP" "/home/wizardsofts/wizardsofts-web"
            ;;
        "pf-padmafoods-web")
            backup_compose_files "$SERVER_IP" "/home/wizardsofts/padmafoods-web"
            ;;
        "gibd-quant-web")
            backup_compose_files "$SERVER_IP" "/home/wizardsofts/gibd-quant-web"
            ;;
        "all")
            log_info "Backing up all services..."
            backup_compose_files "$SERVER_IP" "/home/wizardsofts/wizardsofts-web" || true
            backup_compose_files "$SERVER_IP" "/home/wizardsofts/padmafoods-web" || true
            backup_compose_files "$SERVER_IP" "/home/wizardsofts/gibd-quant-web" || true
            ;;
    esac

    # Create deployment snapshot
    create_deployment_snapshot "$SERVER_IP"

    # Optional: Clean up Docker resources
    read -p "Clean up unused Docker resources? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup_docker "$SERVER_IP"
    fi

    # Summary
    echo ""
    echo "========================================="
    if [[ $exit_code -eq 0 ]]; then
        log_success "Pre-deployment preparation completed!"
        log_info "You can now proceed with deployment"
        echo "========================================="
        exit 0
    else
        log_warn "Pre-deployment completed with warnings"
        log_info "Review warnings above before proceeding"
        echo "========================================="
        exit $exit_code
    fi
}

# Run main function
main
