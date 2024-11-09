#!/bin/bash

# Exit on error
set -e

# Default values
WORKERS="${WORKERS:-4}"
KEEP_ALIVE="${KEEP_ALIVE:-300}"
PORT="${PORT:-8080}"
TIMEOUT="${TIMEOUT:-300}"
MAX_REQUESTS="${MAX_REQUESTS:-1000}"

# Start Xvfb
Xvfb :99 -screen 0 1280x1024x24 &
export DISPLAY=:99

# Wait for Xvfb to be ready
sleep 1

echo "Starting server on port $PORT with $WORKERS workers"

# Set environment variables
export PYTHONPATH=/app
export PYTHONUNBUFFERED=1

# Use hypercorn to run the application
exec hypercorn src.app:app \
    --bind 0.0.0.0:$PORT \
    --workers $WORKERS \
    --keep-alive $KEEP_ALIVE \
    --graceful-timeout 30 \
    --timeout $TIMEOUT \
    --max-requests $MAX_REQUESTS