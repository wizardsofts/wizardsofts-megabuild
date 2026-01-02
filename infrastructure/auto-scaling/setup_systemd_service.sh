#!/bin/bash
# Set up auto-start systemd service for the control plane

set -e  # Exit on any error

echo "=================================="
echo "Setting up Auto-Start Systemd Service"
echo "=================================="
echo

# Function to log messages
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Check if we're running as root (required for systemd service)
if [ "$EUID" -ne 0 ]; then
    log "Switching to root to set up systemd service..."
    # Re-run the script as root
    exec sudo "$0" "$@"
fi

# Create the systemd service file
SERVICE_FILE="/etc/systemd/system/autoscaler.service"

log "Creating systemd service file at $SERVICE_FILE..."

cat > $SERVICE_FILE << 'EOF'
[Unit]
Description=Docker Auto-Scaler Control Plane
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/autoscaler
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
ExecReload=/usr/bin/docker compose down && /usr/bin/docker compose up -d
User=wizardsofts
Group=wizardsofts
TimeoutStartSec=120
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

log "Systemd service file created"
echo

# Handle potential issue with docker-compose command location
log "Checking for docker-compose command..."
if ! command -v docker-compose &> /dev/null && command -v docker &> /dev/null; then
    # If docker-compose is not available, create an alias or update the service file
    log "docker-compose not found, checking for 'docker compose' (newer Docker versions)..."
    
    if docker compose version &> /dev/null; then
        log "Found 'docker compose', updating service file..."
        # Update the service file to use 'docker compose' instead
        sed -i.bak 's|/usr/local/bin/docker-compose|docker compose|g' $SERVICE_FILE
        log "Service file updated to use 'docker compose'"
    else
        log "ERROR: Neither 'docker-compose' nor 'docker compose' is available"
        log "Please install Docker Compose or update Docker to a newer version"
        exit 1
    fi
fi

# Reload systemd to recognize the new service
log "Reloading systemd daemon..."
systemctl daemon-reload
log "Systemd daemon reloaded"
echo

# Enable the service to start on boot
log "Enabling autoscaler service to start on boot..."
systemctl enable autoscaler.service
log "Service enabled"
echo

# Test the service
log "Testing the service start..."
systemctl start autoscaler.service

log "Waiting 15 seconds for services to start..."
sleep 15

# Check the service status
log "Checking service status..."
systemctl status autoscaler.service --no-pager -l

echo
log "Testing if services are responding..."
if curl -f -s http://localhost:8000/ &> /dev/null; then
    log "✓ Autoscaler API is responding after service start"
else
    log "✗ Autoscaler API is not responding - check service logs"
    log "Check with: journalctl -u autoscaler.service -f"
fi

echo
log "=================================="
log "Auto-Start Systemd Service Setup Summary:"
log "✓ Service file created: /etc/systemd/system/autoscaler.service"
log "✓ Service enabled to start at boot time"
log "✓ Service started and tested"
log ""
log "Service Management Commands:"
log "  Start:     sudo systemctl start autoscaler.service"
log "  Stop:      sudo systemctl stop autoscaler.service"
log "  Restart:   sudo systemctl restart autoscaler.service"
log "  Status:    sudo systemctl status autoscaler.service"
log "  Logs:      sudo journalctl -u autoscaler.service -f"
log "  Disable:   sudo systemctl disable autoscaler.service"
log ""
log "The control plane will now automatically start after system reboot."
log "Verify with: sudo systemctl status autoscaler.service"
log "=================================="