#!/bin/bash
set -eo pipefail

# Lambda function handler function
lambda_handler() {
    event=$1
    context=$2

    # Example: Replace with your actual Python script command
    python3 - <<EOF
import lambda_function

def handler(event, context):
    lambda_function.handler(event, context)

if __name__ == "__main__":
    import json, sys
    input_event = json.load(sys.stdin)
    handler(input_event, None)
EOF
}

# Trap SIGTERM and SIGINT signals to run the cleanup function
cleanup() {
  echo "Caught termination signal. Cleaning up..."
  # Add any cleanup logic here if necessary
  exit 0
}
trap cleanup SIGTERM SIGINT

# Invoke Lambda function handler with input event
lambda_handler "$@"