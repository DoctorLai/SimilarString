#!/bin/bash

## require env SS_PATH
if [ -z "$SS_PATH" ]; then
  echo "SS_PATH is not set. Please source ./setup-env.sh first."
  exit 1
fi

# Run the server with restart policy
docker run \
    -e FLASK_ENV=$FLASK_ENV\
    --name $SS_DOCKER_IMAGE\
    --restart always \
    -p $HOST_PORT:5000\
    -v `pwd`/config.yaml:/app/config.yaml \
    $SS_DOCKER_IMAGE
