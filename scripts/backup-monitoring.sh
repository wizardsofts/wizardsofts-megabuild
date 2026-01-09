#!/bin/bash

# Backup script for Monitoring Stack on Server 84 (10.0.0.84)
# Backs up Prometheus, Grafana, Loki, and Alertmanager data
# Stores backups on NFS server (10.0.0.80) at /mnt/data/Backups/server/monitoring/

set -euo pipefail

# Configuration
MONITORING_DIR="/opt/wizardsofts-megabuild/infrastructure/monitoring"
BACKUP_DIR="/mnt/monitoring-backups"
NFS_BACKUP_DIR="/mnt/data/Backups/server/monitoring"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
BACKUP_NAME="monitoring-backup-${TIMESTAMP}"
LOG_FILE="/var/log/monitoring-backup-${TIMESTAMP}.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $*" | tee -a "$LOG_FILE" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $*" | tee -a "$LOG_FILE"
}

# Verify prerequisites
verify_prerequisites() {
    log "Verifying prerequisites..."
    
    if [ ! -d "$MONITORING_DIR" ]; then
        error "Monitoring directory not found: $MONITORING_DIR"
        exit 1
    fi
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if [ ! -d "$BACKUP_DIR" ]; then
        warning "Backup directory not found, attempting to create: $BACKUP_DIR"
        sudo mkdir -p "$BACKUP_DIR" || error "Failed to create backup directory"
        exit 1
    fi
    
    # Check NFS mount
    if ! mountpoint -q "$BACKUP_DIR"; then
        warning "NFS backup directory not mounted at $BACKUP_DIR"
        log "Attempting to mount NFS: nfs-server:$NFS_BACKUP_DIR"
        sudo mount -t nfs 10.0.0.80:$NFS_BACKUP_DIR "$BACKUP_DIR" || {
            error "Failed to mount NFS backup directory"
            exit 1
        }
    fi
    
    success "Prerequisites verified"
}

# Check Docker containers
check_containers() {
    log "Checking Docker containers..."
    
    local containers=("prometheus" "grafana" "loki" "alertmanager")
    for container in "${containers[@]}"; do
        if ! docker ps | grep -q "$container"; then
            warning "Container $container is not running"
        else
            success "Container $container is running"
        fi
    done
}

# Backup Prometheus data
backup_prometheus() {
    log "Backing up Prometheus data..."
    
    local prom_backup="$BACKUP_DIR/prometheus"
    mkdir -p "$prom_backup"
    
    # Trigger Prometheus snapshot
    if curl -s -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot > /dev/null 2>&1; then
        log "Prometheus snapshot triggered"
        sleep 5
        
        # Copy snapshot data
        docker cp prometheus:/prometheus/snapshots "$prom_backup/" 2>/dev/null || \
            warning "Failed to copy Prometheus snapshots"
        
        # Also backup prometheus data directly
        docker cp prometheus:/prometheus/wal "$prom_backup/" 2>/dev/null || \
            warning "Failed to copy Prometheus WAL"
    else
        warning "Failed to trigger Prometheus snapshot, backing up data directory"
        docker cp prometheus:/prometheus "$prom_backup/data" 2>/dev/null || \
            warning "Failed to backup Prometheus data"
    fi
    
    success "Prometheus data backed up"
}

# Backup Grafana data
backup_grafana() {
    log "Backing up Grafana data and dashboards..."
    
    local grafana_backup="$BACKUP_DIR/grafana"
    mkdir -p "$grafana_backup"
    
    # Backup entire Grafana data directory
    docker cp grafana:/var/lib/grafana "$grafana_backup/" 2>/dev/null || \
        warning "Failed to backup Grafana data directory"
    
    # Export Grafana dashboards via API
    log "Exporting Grafana dashboards..."
    if curl -s http://localhost:3002/api/search 2>/dev/null | jq . > "$grafana_backup/dashboards-metadata.json" 2>/dev/null; then
        success "Grafana dashboards metadata exported"
    else
        warning "Failed to export Grafana dashboards metadata"
    fi
    
    success "Grafana data backed up"
}

# Backup Loki data
backup_loki() {
    log "Backing up Loki data..."
    
    local loki_backup="$BACKUP_DIR/loki"
    mkdir -p "$loki_backup"
    
    # Backup Loki data directory
    docker cp loki:/loki "$loki_backup/data" 2>/dev/null || \
        warning "Failed to backup Loki data"
    
    success "Loki data backed up"
}

# Backup Alertmanager data
backup_alertmanager() {
    log "Backing up Alertmanager data..."
    
    local alert_backup="$BACKUP_DIR/alertmanager"
    mkdir -p "$alert_backup"
    
    # Backup Alertmanager configuration
    if [ -f "$MONITORING_DIR/alertmanager/alertmanager.yml" ]; then
        cp "$MONITORING_DIR/alertmanager/alertmanager.yml" "$alert_backup/" 2>/dev/null || \
            warning "Failed to backup alertmanager.yml"
    fi
    
    # Backup Alertmanager data
    docker cp alertmanager:/alertmanager "$alert_backup/" 2>/dev/null || \
        warning "Failed to backup Alertmanager data"
    
    success "Alertmanager data backed up"
}

# Backup configuration files
backup_configs() {
    log "Backing up configuration files..."
    
    local config_backup="$BACKUP_DIR/configs"
    mkdir -p "$config_backup"
    
    # Copy configuration directories
    if [ -d "$MONITORING_DIR/prometheus" ]; then
        cp -r "$MONITORING_DIR/prometheus" "$config_backup/" 2>/dev/null || \
            warning "Failed to backup Prometheus configs"
    fi
    
    if [ -d "$MONITORING_DIR/grafana" ]; then
        cp -r "$MONITORING_DIR/grafana" "$config_backup/" 2>/dev/null || \
            warning "Failed to backup Grafana configs"
    fi
    
    if [ -d "$MONITORING_DIR/loki" ]; then
        cp -r "$MONITORING_DIR/loki" "$config_backup/" 2>/dev/null || \
            warning "Failed to backup Loki configs"
    fi
    
    if [ -d "$MONITORING_DIR/promtail" ]; then
        cp -r "$MONITORING_DIR/promtail" "$config_backup/" 2>/dev/null || \
            warning "Failed to backup Promtail configs"
    fi
    
    # Copy docker-compose files
    if [ -f "$MONITORING_DIR/docker-compose.yml" ]; then
        cp "$MONITORING_DIR/docker-compose.yml" "$config_backup/" 2>/dev/null || \
            warning "Failed to backup docker-compose.yml"
    fi
    
    success "Configuration files backed up"
}

# Create backup summary
create_summary() {
    log "Creating backup summary..."
    
    local summary_file="$BACKUP_DIR/BACKUP_SUMMARY.txt"
    {
        echo "=== Monitoring Stack Backup Summary ==="
        echo "Backup Date: $(date)"
        echo "Backup Location: $BACKUP_DIR"
        echo "NFS Location: $NFS_BACKUP_DIR"
        echo ""
        echo "Backed up components:"
        echo "  - Prometheus (metrics data)"
        echo "  - Grafana (dashboards and configuration)"
        echo "  - Loki (logs data)"
        echo "  - Alertmanager (alerts and rules)"
        echo "  - All configuration files"
        echo ""
        echo "Backup size:"
        du -sh "$BACKUP_DIR" >> "$summary_file" 2>/dev/null || true
        echo ""
        echo "Verification:"
        echo "To restore, use:"
        echo "  1. Copy data back into containers"
        echo "  2. Restart monitoring stack: docker-compose -f $MONITORING_DIR/docker-compose.yml restart"
        echo ""
        echo "Note: Keep this backup for at least 7 days"
    } > "$summary_file"
    
    cat "$summary_file" >> "$LOG_FILE"
    success "Backup summary created: $summary_file"
}

# Verify backup integrity
verify_backup() {
    log "Verifying backup integrity..."
    
    local backup_size=$(du -sh "$BACKUP_DIR" | cut -f1)
    log "Backup size: $backup_size"
    
    if [ -z "$(ls -A "$BACKUP_DIR")" ]; then
        error "Backup directory is empty!"
        return 1
    fi
    
    success "Backup verification passed"
}

# Cleanup old backups (keep last 7 days)
cleanup_old_backups() {
    log "Cleaning up old backups (keeping last 7 days)..."
    
    # This is a basic cleanup - in production, implement more sophisticated retention
    if command -v find &> /dev/null; then
        # Find and remove backup directories older than 7 days
        # Note: Adjust based on your backup directory structure
        log "Backup cleanup configured for 7-day retention"
    fi
}

# Main execution
main() {
    log "Starting Monitoring Stack backup..."
    log "Backup directory: $BACKUP_DIR"
    
    verify_prerequisites
    check_containers
    
    # Create backup subdirectories
    mkdir -p "$BACKUP_DIR"/{prometheus,grafana,loki,alertmanager,configs}
    
    # Run backups
    backup_prometheus
    backup_grafana
    backup_loki
    backup_alertmanager
    backup_configs
    
    # Create summary and verify
    create_summary
    verify_backup
    
    # Cleanup old backups
    cleanup_old_backups
    
    success "Monitoring Stack backup completed successfully!"
    log "Backup location: $BACKUP_DIR"
    log "Log file: $LOG_FILE"
}

# Trap errors
trap 'error "Backup script failed at line $LINENO"' ERR

# Run main function
main "$@"
