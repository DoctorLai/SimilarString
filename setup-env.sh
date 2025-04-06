#!/bin/bash

export SS_PATH="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)"
export SS_DOCKER_IMAGE=mlserver
export FLASK_ENV=production
export RETRY_COUNT=20
export HOST_PORT=5000
