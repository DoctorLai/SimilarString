#!/bin/bash

## require env SS_PATH
if [ -z "$SS_PATH" ]; then
  echo "SS_PATH is not set. Please source ./setup-env.sh first."
  exit 1
fi

docker stop $SS_DOCKER_IMAGE || true
docker rm $SS_DOCKER_IMAGE
