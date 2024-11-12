#!/bin/bash

# Exit on error
set -e

# Default values
WORKERS="${WORKERS:-4}"
KEEP_ALIVE="${KEEP_ALIVE:-300}"
PORT="${PORT:-8080}"
MAX_REQUESTS="${MAX_REQUESTS:-1000}"

# Create Xvfb socket directory if it doesn't exist
XVFB_DIR="/tmp/.X11-unix"
if [ ! -d "$XVFB_DIR" ]; then
    mkdir -p "$XVFB_DIR"
fi

# Start Xvfb with suppressed warnings
Xvfb :99 -screen 0 1280x1024x24 2>/dev/null &
export DISPLAY=:99

# Wait for Xvfb to be ready
sleep 1

echo "Starting server on port $PORT with $WORKERS workers"

# Set environment variables
export PYTHONPATH=/app
export PYTHONUNBUFFERED=1

# Use hypercorn to run the application
exec hypercorn app:app \
    --bind "0.0.0.0:$PORT" \
    --workers "$WORKERS" \
    --keep-alive "$KEEP_ALIVE" \
    --graceful-timeout 30 \
    --max-requests "$MAX_REQUESTS"