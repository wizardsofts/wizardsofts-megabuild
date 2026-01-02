#!/usr/bin/env bash
# Simple smoke test for the frontend Docker image.
# Usage: ./scripts/docker-smoke-test.sh [host-data-dir]
# If host-data-dir is provided, it will be mounted to /app/data in the container

set -euo pipefail

IMAGE_NAME="wizardsofts/frontend:smoke-test"
CONTAINER_NAME="wizard-frontend-smoke"

HOST_DATA_DIR="${1-}"

echo "Building image ${IMAGE_NAME}..."
docker build -t ${IMAGE_NAME} .

if [ -n "${HOST_DATA_DIR}" ]; then
  mkdir -p "${HOST_DATA_DIR}"
  VOLUME_ARG="-v ${HOST_DATA_DIR}:/app/data"
else
  VOLUME_ARG=""
fi

echo "Running container..."
docker run --rm -d --name ${CONTAINER_NAME} -p 3000:3000 ${VOLUME_ARG} ${IMAGE_NAME}

echo "Waiting for server to start..."
sleep 4

echo "Posting test submission..."
curl -s -X POST http://localhost:3000/api/contact \
  -H 'Content-Type: application/json' \
  -d '{"name":"Smoke","email":"smoke@example.com","subject":"smoke","message":"smoke test"}'

sleep 1

echo
echo "Checking submissions file inside container..."
docker exec ${CONTAINER_NAME} cat /app/data/submissions.json || true

echo "Cleaning up..."
docker stop ${CONTAINER_NAME} >/dev/null 2>&1 || true

echo "Done. If you mounted a host directory, check ${HOST_DATA_DIR} for submissions.json"
