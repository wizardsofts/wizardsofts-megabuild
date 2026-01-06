#!/bin/bash
# NFS Client Setup Script for Server 82
# Run this on Server 82: ssh wizardsofts@10.0.0.82
# Execute as: sudo bash setup_nfs_client82.sh

set -e

echo "=== NFS Client Setup for Ollama Models (Server 82) ==="

# Step 1: Install NFS client
echo "[1/4] Installing NFS client..."
apt update
apt install -y nfs-common

# Step 2: Create mount point
echo "[2/4] Creating mount point /opt/ollama-models..."
mkdir -p /opt/ollama-models

# Step 3: Add to fstab for persistent mount
echo "[3/4] Configuring persistent mount..."
if grep -q "10.0.0.80:/opt/ollama-models" /etc/fstab; then
    echo "NFS mount already exists in /etc/fstab"
else
    echo "10.0.0.80:/opt/ollama-models /opt/ollama-models nfs defaults,_netdev 0 0" >> /etc/fstab
    echo "Added NFS mount to /etc/fstab"
fi

# Step 4: Mount now
echo "[4/4] Mounting NFS volume..."
mount -a

echo ""
echo "✅ NFS client setup complete!"
echo ""
echo "Verify with:"
echo "  df -h /opt/ollama-models"
echo "  ls -la /opt/ollama-models"
echo ""
