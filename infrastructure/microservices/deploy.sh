#!/bin/bash

# Deploy microservices stack to Docker Swarm with environment variables
# Usage: ./deploy.sh

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables from .env.microservices
if [ ! -f .env.microservices ]; then
    echo "Error: .env.microservices file not found!"
    exit 1
fi

echo "Loading environment variables from .env.microservices..."
set -a  # Export all variables
source .env.microservices
set +a  # Stop exporting

# Check required environment variables
if [ -z "$DB_PASSWORD" ]; then
    echo "Error: DB_PASSWORD not set in .env.microservices"
    exit 1
fi

echo "Deploying microservices stack to Docker Swarm..."
docker stack deploy -c microservices-stack.yml --with-registry-auth microservices

echo ""
echo "Stack deployed successfully!"
echo ""
echo "To check service status:"
echo "  docker service ls | grep microservices"
echo ""
echo "To view service logs:"
echo "  docker service logs microservices_ws-discovery"
echo "  docker service logs microservices_ws-gateway"
echo "  docker service logs microservices_ws-trades"
echo "  docker service logs microservices_ws-company"
echo "  docker service logs microservices_ws-news"
echo ""
echo "To check Eureka dashboard:"
echo "  http://10.0.0.84:8761"
