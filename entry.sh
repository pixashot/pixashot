#!/bin/bash

# Default values
WORKERS=4
THREADS=1
TIMEOUT=300

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -w|--workers)
      WORKERS="$2"
      shift
      shift
      ;;
    -t|--threads)
      THREADS="$2"
      shift
      shift
      ;;
    --timeout)
      TIMEOUT="$2"
      shift
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Use PORT environment variable, defaulting to 8080 if not set
PORT="${PORT:-8080}"

# Start Xvfb
Xvfb :99 -ac -screen 0 1280x1024x16 &

# Wait for Xvfb to be ready
sleep 1

echo "Starting server on port $PORT with $WORKERS workers and $THREADS threads"

# Run the Flask application
exec gunicorn --bind 0.0.0.0:$PORT \
              --workers $WORKERS \
              --threads $THREADS \
              --timeout $TIMEOUT \
              app:app