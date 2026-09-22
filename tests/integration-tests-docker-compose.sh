#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT_NAME="similarstring-compose-test-${RANDOM}"
STARTUP_TIMEOUT="${SS_STARTUP_TIMEOUT:-300}"
if [[ ! "$STARTUP_TIMEOUT" =~ ^[1-9][0-9]*$ ]]; then
  echo "SS_STARTUP_TIMEOUT must be a positive number of seconds." >&2
  exit 1
fi
export HOST_PORT=0

compose() {
  docker compose --file "$ROOT_DIR/docker-compose.yml" --project-name "$PROJECT_NAME" "$@"
}

cleanup() {
  result=$?
  if [[ "$result" -ne 0 ]]; then
    compose logs --no-color || true
  fi
  compose down --volumes || true
}
trap cleanup EXIT

compose up --build --detach --wait --wait-timeout "$STARTUP_TIMEOUT"
CONTAINER_ID="$(compose ps --quiet flask-app)"
PORT="$(docker inspect --format '{{(index (index .NetworkSettings.Ports "5000/tcp") 0).HostPort}}' "$CONTAINER_ID")"
SS_URL="http://127.0.0.1:$PORT" "$ROOT_DIR/test_ml_server.sh"
