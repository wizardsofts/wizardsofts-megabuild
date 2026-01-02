#!/bin/bash
# Backup script for Auto-Scaling Platform
# Creates backups of configuration and logs

BACKUP_DIR="/opt/autoscaler/backup"
DATE=$(date +%Y%m%d_%H%M%S)

echo "Starting backup process..."

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Backup configuration files
echo "Backing up configuration files..."
cp /opt/autoscaler/config.yaml $BACKUP_DIR/config_$DATE.yaml
cp /opt/autoscaler/haproxy/haproxy.cfg $BACKUP_DIR/haproxy_$DATE.cfg
cp /opt/autoscaler/docker-compose.yml $BACKUP_DIR/docker-compose_$DATE.yml

# Backup application code (source)
echo "Backing up application code..."
TAR_FILE="$BACKUP_DIR/app_source_$DATE.tar.gz"
tar -czf $TAR_FILE -C /opt/autoscaler/app .

# Backup additional config models and tests if they exist
if [ -f "/opt/autoscaler/app/config_model.py" ]; then
    cp /opt/autoscaler/app/config_model.py $BACKUP_DIR/config_model_$DATE.py
fi

if [ -d "/opt/autoscaler/tests" ]; then
    TESTS_TAR="$BACKUP_DIR/tests_$DATE.tar.gz"
    tar -czf $TESTS_TAR -C /opt/autoscaler . --exclude='__pycache__' --exclude='*.pyc'
fi

# Clean up old backups (keep last 7 days)
echo "Cleaning up old backups..."
find $BACKUP_DIR -name "*.yaml" -mtime +7 -delete
find $BACKUP_DIR -name "*.cfg" -mtime +7 -delete
find $BACKUP_DIR -name "app_source_*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "config_model_*.py" -mtime +7 -delete
find $BACKUP_DIR -name "tests_*.tar.gz" -mtime +7 -delete

echo "Backup complete: $DATE"
echo "Backup files saved to: $BACKUP_DIR"