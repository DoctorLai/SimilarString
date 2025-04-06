#!/bin/bash
# Integration tests for the ML server
# This script will build the docker image, start the server, and run the tests
# It will also stop the server after the tests are done
# It will also check if the server is running and if the tests pass.

## required env var SS_PATH
if [ -z "$SS_PATH" ]; then
    echo "SS_PATH is not set"
    exit 1
fi

## build-and-run
if ! pushd $SS_PATH; then
    echo "Failed to pushd to $SS_PATH"
    exit 1
fi

echo "Stopping any existing server..."
./stop.sh || true

echo "Building the docker image..."
if ! ./build.sh; then
    echo "Failed to build the docker image"
    exit 1
fi

echo "Starting the server..."
./run.sh &

## list docker containers
docker ps

MAX_TIMEOUT_SEC=300
while :
do
    echo "Waiting for the server to start..."
    # check $DOCKER_IMAGE status via docker ps
    # check logs for "ML model loaded successfully."
    status=$(docker logs $SS_DOCKER_IMAGE 2>&1 | grep "ML model loaded successfully." | tail -n 1)
    if [ -n "$status" ]; then
        echo "Server is up and running!"
        break
    fi
    echo "Server is not up yet. Sleep for 1 second $status..."
    ## check if timeout
    if [ $MAX_TIMEOUT_SEC -le 0 ]; then
        echo "Timeout: Server did not start"
        exit 1
    fi
    MAX_TIMEOUT_SEC=$((MAX_TIMEOUT_SEC-1))
    sleep 1
done

echo "Server is up and running!"

config_version=$(cat config.yaml | grep version | awk '{print $2}' | tr -d '"' | head -n 1)

send_a_get_request() {
    # Send a get request with JSON data
    resp=$(curl -s -m 10 -X GET -H "Content-Type: application/json" \
        --data '{"s1":"This is a Surface Studio Laptop","s2":"That is a car"}' \
        http://127.0.0.1:5000)

    # {"s1":"This is a Surface Studio Laptop","s2":"That is a car","score":0.08295086771249771,"status":"success"}
    echo "Response: $resp"

    # Check if response is empty
    if [ -z "$resp" ]; then
        echo "Response is empty"
        return 1
    fi

    s1=$(echo $resp | jq -r '.s1')
    s2=$(echo $resp | jq -r '.s2')
    score=$(echo $resp | jq -r '.score')
    status=$(echo $resp | jq -r '.status')

    echo "Response s1: $s1"
    echo "Response s2: $s2"
    echo "Response score: $score"
    echo "Response status: $status"

    # Check if the response contains the expected keys
    if [ "$s1" != "This is a Surface Studio Laptop" ]; then
        echo "Response s1 is not correct"
        return 1
    fi

    if [ "$s2" != "That is a car" ]; then
        echo "Response s2 is not correct"
        return 1
    fi

    # check score is between 0.07 to 0.10
    if ! [[ "$score" =~ ^0\.[0-9]{2,}$ ]]; then
        echo "Response score is not correct"
        return 1
    fi

    if [ "$status" != "success" ]; then
        echo "Response status is not correct"
        return 1
    fi

    echo "send_a_get_request test passed!"
    return 0
}

retry_test() {
    RETRY=60
    INTERVAL=1
    TESTS_PASSING=false
    for i in $(seq 1 $RETRY); do
        echo "Sending a GET request to the server (Counter = $i)..."
        if $1; then
            TESTS_PASSING=true
            break
        fi
        sleep $INTERVAL
    done
    if [ "$TESTS_PASSING" = false ]; then
        echo "$1 failed after $RETRY attempts"
        return 1
    fi
    echo "$1 passed"
    return 0
}

popd

RESULT=true

## Test GET request
if ! retry_test send_a_get_request; then
    RESULT=false
fi

$SS_PATH/stop.sh

if [ "$RESULT" = false ]; then
    echo "Integration tests failed!"
    exit 1
fi
echo "All integration tests passed!"
exit 0
