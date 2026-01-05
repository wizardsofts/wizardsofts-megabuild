#!/bin/bash
set -euo pipefail

echo "🔒 Configuring firewall rules for Ray cluster..."

# Configure Server 84 (Head Node)
ssh wizardsofts@10.0.0.84 << 'EOF'
# Allow Ray GCS
sudo ufw allow from 10.0.0.0/24 to any port 6379 comment 'Ray GCS'

# Allow Ray Dashboard
sudo ufw allow from 10.0.0.0/24 to any port 8265 comment 'Ray Dashboard'

# Allow Ray Client
sudo ufw allow from 10.0.0.0/24 to any port 10001 comment 'Ray Client'

# Allow Ray Metrics
sudo ufw allow from 10.0.0.0/24 to any port 8080 comment 'Ray Metrics'

# Allow Ray worker ports (dynamic range)
sudo ufw allow from 10.0.0.0/24 to any port 10002:10999 comment 'Ray Workers'

sudo ufw reload
echo "✅ Server 84 firewall configured"
EOF

# Configure Worker Nodes (Server 80, 82)
for SERVER in 80 82; do
    ssh wizardsofts@10.0.0.$SERVER << 'EOF'
    # Allow outbound connections to Ray head
    # (UFW allows outbound by default, but document for reference)

    # Allow Ray worker ports
    sudo ufw allow from 10.0.0.0/24 to any port 10002:10999 comment 'Ray Workers'

    sudo ufw reload
    echo "✅ Server firewall configured"
EOF
done

echo "✅ All firewall rules configured"
