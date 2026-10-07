#!/bin/bash

export SS_PATH="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export SS_DOCKER_IMAGE="${SS_DOCKER_IMAGE:-mlserver}"
export FLASK_ENV="${FLASK_ENV:-production}"
export HOST_PORT="${HOST_PORT:-5000}"
export SS_BIND_ADDRESS="${SS_BIND_ADDRESS:-127.0.0.1}"
