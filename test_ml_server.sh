#!/bin/bash
set -euo pipefail

BASE_URL="${SS_URL:-http://127.0.0.1:${HOST_PORT:-5000}}"
STARTUP_TIMEOUT="${SS_STARTUP_TIMEOUT:-300}"

if [[ ! "$STARTUP_TIMEOUT" =~ ^[1-9][0-9]*$ ]]; then
	echo "SS_STARTUP_TIMEOUT must be a positive number of seconds." >&2
	exit 1
fi

STARTUP_LOG="$(mktemp)"
trap 'rm -f "$STARTUP_LOG"' EXIT

echo "Waiting for $BASE_URL/health (startup retry budget: ${STARTUP_TIMEOUT}s)."
echo "The model downloads and loads before HTTP is available; connection resets during this wait are expected."
if ! health_response="$(curl --fail --silent --show-error \
	--retry "$STARTUP_TIMEOUT" --retry-connrefused --retry-all-errors \
	--retry-delay 2 --retry-max-time "$STARTUP_TIMEOUT" --max-time 10 \
	"$BASE_URL/health" 2> "$STARTUP_LOG")"; then
	echo "Server did not become ready within the ${STARTUP_TIMEOUT}s startup retry budget: $BASE_URL/health" >&2
	tail -n 10 "$STARTUP_LOG" >&2
	exit 1
fi

if ! printf '%s\n' "$health_response" | jq -e '.status == "ok" and (.version | type == "string")' > /dev/null; then
	echo "Unexpected health response: $health_response" >&2
	exit 1
fi
echo "Server is ready; checking real-model GET/POST requests."

for method in GET POST; do
	curl --fail-with-body --silent --show-error --max-time 60 \
		--request "$method" --header 'Content-Type: application/json' \
		--data '{"s1":"A laptop","s2":"A laptop"}' "$BASE_URL/" \
		| jq -e '.status == "success" and .s1 == "A laptop" and .s2 == "A laptop"
			and (.score | type == "number") and .score >= 0.99 and .score <= 1.01'
done

curl --fail-with-body --silent --show-error --max-time 60 \
	--header 'Content-Type: application/json' \
	--data '{"s1":"This is a Surface Studio Laptop","s2":"That is a car"}' "$BASE_URL/" \
	| jq -e '.status == "success" and (.score | type == "number")
		and .score >= -1.01 and .score <= 1.01'

echo "Health and real-model GET/POST checks passed."

