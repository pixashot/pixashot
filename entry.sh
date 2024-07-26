#!/bin/bash

# Default values
WORKERS=4
KEEP_ALIVE=300
PORT="${PORT:-8080}"  # Use the PORT env var if set, otherwise default to 8080

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -w|--workers)
      WORKERS="$2"
      shift
      shift
      ;;
    --keep-alive)
      KEEP_ALIVE="$2"
      shift
      shift
      ;;
    --port)
      PORT="$2"
      shift
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate PORT
if ! [[ "$PORT" =~ ^[0-9]+$ ]] ; then
   echo "Warning: Invalid PORT value. Using default port 8080."
   PORT=8080
fi

# Start Xvfb with a high-density screen size (3840x2160) to simulate a retina display
Xvfb :99 -ac -screen 0 3840x2160x24 -dpi 192 &

# Wait for Xvfb to be ready
sleep 1

echo "Starting server on port $PORT with $WORKERS workers"

# Set the DISPLAY environment variable
export DISPLAY=:99

# Run the Quart application with Hypercorn
exec hypercorn --bind 0.0.0.0:$PORT \
               --workers $WORKERS \
               --keep-alive $KEEP_ALIVE \
               app:app