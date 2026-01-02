#!/bin/bash

# This script sets up the entire microservice infrastructure.
# It should be run on the main server that will act as the Docker Swarm manager.

# Exit on any error
set -e

# 1. Build the sample-service
echo "Building the sample-service with Maven..."
(cd sample-service && mvn clean package)

# 2. Start the local Docker registry
echo "Starting the local Docker registry..."
docker-compose up -d registry

# 3. Build and push the sample-service image
echo "Building and pushing the sample-service image to the local registry..."
docker-compose build sample-service
docker-compose push sample-service

# 4. Initialize Docker Swarm
if ! docker info | grep -q "Swarm: active"; then
  echo "Initializing Docker Swarm..."
  docker swarm init
else
  echo "Docker Swarm is already initialized."
fi

# 5. Deploy the stack
echo "Deploying the stack..."
docker stack deploy -c docker-compose.yml microservices

echo "Deployment complete."
echo "You can now join other nodes to the swarm."
echo "To get the join token, run: docker swarm join-token worker"
echo ""
echo "Access the services:"
echo " - Traefik Dashboard: http://traefik.localhost"
echo " - Sample Service: http://hello.localhost"
