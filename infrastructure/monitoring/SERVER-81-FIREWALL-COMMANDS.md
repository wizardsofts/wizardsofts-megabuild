# Server 81 UFW Firewall Configuration Commands

**Run these commands on Server 81 as root or with sudo**

## Option 1: Run the Script (Easiest)

```bash
ssh wizardsofts@10.0.0.81
sudo bash ~/configure-firewall.sh
```

## Option 2: Manual Commands (If script doesn't work)

```bash
# SSH into Server 81
ssh wizardsofts@10.0.0.81

# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (CRITICAL - don't skip this!)
sudo ufw allow 22/tcp comment 'SSH access'

# Allow monitoring services from local network only
sudo ufw allow from 10.0.0.0/24 to any port 9090 proto tcp comment 'Prometheus'
sudo ufw allow from 10.0.0.0/24 to any port 3002 proto tcp comment 'Grafana'
sudo ufw allow from 10.0.0.0/24 to any port 3100 proto tcp comment 'Loki'
sudo ufw allow from 10.0.0.0/24 to any port 9093 proto tcp comment 'AlertManager'
sudo ufw allow from 10.0.0.0/24 to any port 9100 proto tcp comment 'Node Exporter'
sudo ufw allow from 10.0.0.0/24 to any port 9101 proto tcp comment 'Security Metrics'

# Docker Swarm ports (local network only)
sudo ufw allow from 10.0.0.0/24 to any port 2377 proto tcp comment 'Swarm management'
sudo ufw allow from 10.0.0.0/24 to any port 7946 proto tcp comment 'Swarm node TCP'
sudo ufw allow from 10.0.0.0/24 to any port 7946 proto udp comment 'Swarm node UDP'
sudo ufw allow from 10.0.0.0/24 to any port 4789 proto udp comment 'Swarm overlay'

# Enable firewall
sudo ufw --force enable

# Verify configuration
sudo ufw status verbose
sudo ufw status numbered
```

## Option 3: One-Liner (Copy-paste all at once)

```bash
ssh wizardsofts@10.0.0.81 "sudo bash -c '
ufw default deny incoming && \
ufw default allow outgoing && \
ufw allow 22/tcp && \
ufw allow from 10.0.0.0/24 to any port 9090 proto tcp && \
ufw allow from 10.0.0.0/24 to any port 3002 proto tcp && \
ufw allow from 10.0.0.0/24 to any port 3100 proto tcp && \
ufw allow from 10.0.0.0/24 to any port 9093 proto tcp && \
ufw allow from 10.0.0.0/24 to any port 9100 proto tcp && \
ufw allow from 10.0.0.0/24 to any port 9101 proto tcp && \
ufw allow from 10.0.0.0/24 to any port 2377 proto tcp && \
ufw allow from 10.0.0.0/24 to any port 7946 proto tcp && \
ufw allow from 10.0.0.0/24 to any port 7946 proto udp && \
ufw allow from 10.0.0.0/24 to any port 4789 proto udp && \
ufw --force enable && \
ufw status verbose
'"
```

## Expected Output

You should see:

```
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), disabled (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    Anywhere
9090/tcp                   ALLOW IN    10.0.0.0/24         # Prometheus
3002/tcp                   ALLOW IN    10.0.0.0/24         # Grafana
3100/tcp                   ALLOW IN    10.0.0.0/24         # Loki
9093/tcp                   ALLOW IN    10.0.0.0/24         # AlertManager
9100/tcp                   ALLOW IN    10.0.0.0/24         # Node Exporter
9101/tcp                   ALLOW IN    10.0.0.0/24         # Security Metrics
2377/tcp                   ALLOW IN    10.0.0.0/24         # Swarm management
7946/tcp                   ALLOW IN    10.0.0.0/24         # Swarm node TCP
7946/udp                   ALLOW IN    10.0.0.0/24         # Swarm node UDP
4789/udp                   ALLOW IN    10.0.0.0/24         # Swarm overlay
```

## Verification

After enabling, test from another local server:

```bash
# From Server 84, test Grafana access
curl -I http://10.0.0.81:3002

# From Server 84, test Prometheus access
curl -I http://10.0.0.81:9090
```

## Security Summary

- ✅ SSH: Accessible from anywhere (port 22)
- ✅ Monitoring: Accessible only from local network (10.0.0.0/24)
- ✅ Docker Swarm: Accessible only from local network
- ❌ Public internet: DENIED (all other ports)
