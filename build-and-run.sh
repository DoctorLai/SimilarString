#!/bin/bash
set -x
DOCKER_IMAGE=mlserer

## listen to port 5000
HOST_PORT=5000

# stop existing deployment (remove container by name)
docker stop $DOCKER_IMAGE || true
docker rm $DOCKER_IMAGE || true

# Build the Docker image
docker build -t $DOCKER_IMAGE .

# Run the server with restart policy
docker run --name $DOCKER_IMAGE --restart always -p $HOST_PORT:5000 $DOCKER_IMAGE &

