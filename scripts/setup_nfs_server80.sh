#!/bin/bash
# NFS Server Setup Script for Server 80
# Run this on Server 80: ssh wizardsofts@10.0.0.80
# Execute as: sudo bash setup_nfs_server80.sh

set -e

echo "=== NFS Server Setup for Ollama Models (Server 80) ==="

# Step 1: Install NFS server
echo "[1/6] Installing NFS kernel server..."
apt update
apt install -y nfs-kernel-server

# Step 2: Create shared directory
echo "[2/6] Creating shared directory /opt/ollama-models..."
mkdir -p /opt/ollama-models
chown -R 1000:1000 /opt/ollama-models
chmod 755 /opt/ollama-models

# Step 3: Configure NFS exports
echo "[3/6] Configuring NFS exports..."
if grep -q "/opt/ollama-models" /etc/exports; then
    echo "NFS export already exists in /etc/exports"
else
    echo "/opt/ollama-models 10.0.0.0/24(rw,sync,no_subtree_check,no_root_squash)" >> /etc/exports
    echo "Added NFS export to /etc/exports"
fi

# Step 4: Apply export changes
echo "[4/6] Applying NFS export changes..."
exportfs -ra

# Step 5: Start and enable NFS server
echo "[5/6] Starting NFS server..."
systemctl restart nfs-kernel-server
systemctl enable nfs-kernel-server

# Step 6: Configure firewall
echo "[6/6] Configuring UFW firewall..."
ufw allow from 10.0.0.0/24 to any port 2049 proto tcp
ufw allow from 10.0.0.0/24 to any port 111 proto tcp

echo ""
echo "✅ NFS server setup complete!"
echo ""
echo "Verify with:"
echo "  exportfs -v"
echo "  showmount -e localhost"
echo ""
