#!/bin/bash

# Exit on error
set -e

# Default values
WORKERS="${WORKERS:-4}"
KEEP_ALIVE="${KEEP_ALIVE:-300}"
PORT="${PORT:-8080}"
TIMEOUT="${TIMEOUT:-300}"
MAX_REQUESTS="${MAX_REQUESTS:-1000}"
MEMORY_LIMIT="${MEMORY_LIMIT:-2048}"  # in MB
CLOUD_RUN="${CLOUD_RUN:-false}"

# Cleanup function
cleanup() {
    echo "Received shutdown signal, gracefully stopping workers..."
    kill -TERM "$XVFB_PID" 2>/dev/null
    kill -TERM "$HYPERCORN_PID" 2>/dev/null
    wait "$XVFB_PID" "$HYPERCORN_PID"
    exit 0
}

# Set up signal handling
trap cleanup SIGTERM SIGINT

# Function to validate environment variables
validate_env() {
    if ! [[ "$PORT" =~ ^[0-9]+$ ]]; then
        echo "Warning: Invalid PORT value. Using default port 8080."
        PORT=8080
    fi

    if ! [[ "$WORKERS" =~ ^[0-9]+$ ]]; then
        echo "Warning: Invalid WORKERS value. Using default of 4."
        WORKERS=4
    fi

    if ! [[ "$MEMORY_LIMIT" =~ ^[0-9]+$ ]]; then
        echo "Warning: Invalid MEMORY_LIMIT value. Using default of 2048."
        MEMORY_LIMIT=2048
    fi
}

# Function to set up directories and permissions
setup_directories() {
    # Ensure directories exist and have correct permissions
    mkdir -p /app/data /app/logs /tmp/screenshots
    chmod 777 /tmp/screenshots /app/data /app/logs

    # Clear any stale temporary files
    rm -rf /tmp/screenshots/* 2>/dev/null || true
}

# Function to switch user if not running in Cloud Run
switch_user_if_needed() {
    # Only switch user if:
    # 1. We're not in Cloud Run
    # 2. We're currently running as root
    # 3. The pixashot user exists
    if [[ "$CLOUD_RUN" != "true" ]] && [[ $(id -u) -eq 0 ]] && id pixashot >/dev/null 2>&1; then
        echo "Switching to pixashot user..."
        exec gosu pixashot "$0" "$@"
    fi
}

# Main execution
validate_env
setup_directories
switch_user_if_needed

# Start Xvfb with a high-density screen size
Xvfb :99 -ac -screen 0 3840x2160x24 -dpi 192 &
XVFB_PID=$!

# Wait for Xvfb to be ready
sleep 1

echo "Starting server on port $PORT with $WORKERS workers"

# Set the DISPLAY environment variable
export DISPLAY=:99

# Set memory limits
ulimit -v $((MEMORY_LIMIT * 1024)) || true

# Set up environment for the application
export PYTHONPATH=/app
export TEMP=/tmp/screenshots
export TMPDIR=/tmp/screenshots

# Run the Quart application with Hypercorn
hypercorn --bind 0.0.0.0:$PORT \
          --workers $WORKERS \
          --keep-alive $KEEP_ALIVE \
          --graceful-timeout 30 \
          --timeout $TIMEOUT \
          --max-requests $MAX_REQUESTS \
          app:app &
HYPERCORN_PID=$!

# Wait for processes to finish
wait $HYPERCORN_PID