#!/bin/bash
# UFW Firewall Rules for Hadith Knowledge Graph
# Run on Server 84 to restrict services to local network only

set -e

echo "=========================================="
echo "Hadith Knowledge Graph - UFW Configuration"
echo "Server: 10.0.0.84"
echo "=========================================="
echo ""

# Check if running as root/sudo
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run with sudo"
   exit 1
fi

# Neo4j Ports (7474 HTTP, 7687 Bolt)
echo "📝 Configuring Neo4j firewall rules..."
ufw allow from 10.0.0.0/24 to any port 7474 proto tcp comment 'Neo4j HTTP - Local network only'
ufw allow from 10.0.0.0/24 to any port 7687 proto tcp comment 'Neo4j Bolt - Local network only'

# ChromaDB Port (8000)
echo "📝 Configuring ChromaDB firewall rules..."
ufw allow from 10.0.0.0/24 to any port 8000 proto tcp comment 'ChromaDB API - Local network only'

# Ollama Port (11434)
echo "📝 Configuring Ollama firewall rules..."
ufw allow from 10.0.0.0/24 to any port 11434 proto tcp comment 'Ollama LLM API - Local network only'

# Deny all other access to these ports from external networks
echo "🔒 Denying external access..."
ufw deny 7474/tcp comment 'Block Neo4j HTTP from internet'
ufw deny 7687/tcp comment 'Block Neo4j Bolt from internet'
ufw deny 8000/tcp comment 'Block ChromaDB from internet'
ufw deny 11434/tcp comment 'Block Ollama from internet'

# Show current rules
echo ""
echo "✅ Firewall rules configured successfully"
echo ""
echo "Current UFW status:"
ufw status numbered | grep -E '7474|7687|8000|11434'

echo ""
echo "=========================================="
echo "Security Summary"
echo "=========================================="
echo "✅ Neo4j (7474, 7687): Local network only (10.0.0.0/24)"
echo "✅ ChromaDB (8000): Local network only (10.0.0.0/24)"
echo "✅ Ollama (11434): Local network only (10.0.0.0/24)"
echo "❌ External access: BLOCKED"
echo ""
echo "To verify: sudo ufw status | grep -E '7474|7687|8000|11434'"
