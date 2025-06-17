#!/bin/bash

# Set default values
GRADIO_PORT="${GRADIO_PORT:-80}"
API_URL="${API_URL:-http://127.0.0.1:9012/websearch}"
DOCKER_IMAGE="tapestry-gradio"
CONTAINER_NAME="tapestry-gradio-demo"

# Stop and remove existing container (ignore errors if not exist)
docker stop "$CONTAINER_NAME" 2>/dev/null || true
docker rm "$CONTAINER_NAME" 2>/dev/null || true

# Remove existing image (ignore errors if not exist)
docker rmi -f "$DOCKER_IMAGE" 2>/dev/null || true

# Build new image
docker build -t "$DOCKER_IMAGE" .

# Run container in background (fixed container name), use host network
docker run -d --name "$CONTAINER_NAME" \
    --network=host \
    -e GRADIO_PORT="$GRADIO_PORT" \
    -e API_URL="$API_URL" \
    "$DOCKER_IMAGE"

# Print completion message
echo "Gradio Docker container started." 