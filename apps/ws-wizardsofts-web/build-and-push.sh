#!/bin/bash

# Build and push script for WizardSofts website Docker image
# Usage: ./build-and-push.sh [tag]

set -e

# Change to script directory
cd "$(dirname "$0")"

# Default values
REGISTRY="localhost:5050"
IMAGE_NAME="wizardsofts/www.wizardsofts.com"
TAG=${1:-"latest"}

# Full image name
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"

echo "Building Docker image: ${FULL_IMAGE}"
echo "Working directory: $(pwd)"

# Build multi-platform image (for both Mac and Linux servers)
# Create builder if it doesn't exist
docker buildx inspect multiplatform >/dev/null 2>&1 || \
  docker buildx create --name multiplatform --use

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag "${FULL_IMAGE}" \
  --build-arg BUILDKIT_INLINE_CACHE=1 \
  --build-arg NODE_ENV=production \
  --push \
  .

echo "Successfully built and pushed image: ${FULL_IMAGE}"
echo "Image supports both linux/amd64 and linux/arm64 platforms"

echo "Build complete!"
echo "To run locally: docker run -p 3000:3000 ${FULL_IMAGE}"