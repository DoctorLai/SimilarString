#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${SS_DOCKER_IMAGE:-mlserver}"
CONTAINER_NAME="similarstring-docker-test-${RANDOM}"

cleanup() {
  result=$?
  if [[ "$result" -ne 0 ]]; then
    docker logs "$CONTAINER_NAME" || true
  fi
  docker rm --force "$CONTAINER_NAME" > /dev/null 2>&1 || true
}
trap cleanup EXIT

docker build --tag "$IMAGE" "$ROOT_DIR"
docker run --detach --name "$CONTAINER_NAME" \
  --publish 127.0.0.1::5000 "$IMAGE"
echo "View model startup logs with: docker logs --follow $CONTAINER_NAME"
PORT="$(docker inspect --format '{{(index (index .NetworkSettings.Ports "5000/tcp") 0).HostPort}}' "$CONTAINER_NAME")"
SS_URL="http://127.0.0.1:$PORT" "$ROOT_DIR/test_ml_server.sh"
