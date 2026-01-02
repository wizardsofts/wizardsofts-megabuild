#!/bin/bash
# Deploy Appwrite Console Fix to Server
# This script deploys the updated docker-compose.appwrite.yml with persistent env.js volume mount

set -e

SERVER="wizardsofts@10.0.0.84"
REMOTE_PATH="/opt/wizardsofts-megabuild"
SUDO_PASS="29Dec2#24"

echo "========================================="
echo "Deploying Appwrite Console Fix"
echo "========================================="
echo ""

# Copy docker-compose file
echo "1. Copying docker-compose.appwrite.yml to server..."
scp docker-compose.appwrite.yml $SERVER:$REMOTE_PATH/
echo "✓ docker-compose.appwrite.yml copied"
echo ""

# Copy console-env.js file
echo "2. Copying traefik/console-env.js to server..."
scp traefik/console-env.js $SERVER:$REMOTE_PATH/traefik/
echo "✓ console-env.js copied"
echo ""

# Restart console container on server
echo "3. Restarting console container on server..."
ssh $SERVER << ENDSSH
cd $REMOTE_PATH
echo "$SUDO_PASS" | sudo -S docker compose -f docker-compose.appwrite.yml up -d --force-recreate appwrite-console
echo ""
echo "Waiting for console to start..."
sleep 10
echo ""
echo "Console container status:"
docker ps --format 'table {{.Names}}\t{{.Status}}' | grep appwrite-console
ENDSSH

echo ""
echo "========================================="
echo "✓ Deployment Complete!"
echo "========================================="
echo ""
echo "Testing console access..."
sleep 5
curl -I https://appwrite.wizardsofts.com/console/ 2>&1 | head -5

echo ""
echo "Next: Verify console signup works"
echo "URL: https://appwrite.wizardsofts.com/console/register"
