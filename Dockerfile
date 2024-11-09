# Use the official Playwright Python base image
FROM mcr.microsoft.com/playwright/python:v1.35.0-focal

# Define environment variables
ENV PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PORT=8080 \
    PYTHONDONTWRITEBYTECODE=1 \
    WORKERS=4 \
    KEEP_ALIVE=300 \
    TIMEOUT=300 \
    MAX_REQUESTS=1000 \
    MEMORY_LIMIT=2048 \
    # Set this to true in Cloud Run
    CLOUD_RUN=false

# Create non-root user with same uid as Cloud Run (1000)
RUN groupadd -g 1000 pixashot && \
    useradd -r -u 1000 -g pixashot -d /app pixashot

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies including video codecs and security updates
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    libavcodec-extra \
    libavformat-dev \
    ffmpeg \
    gstreamer1.0-libav \
    xvfb \
    psutil \
    dumb-init \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and download browsers with video support
RUN playwright install --with-deps chromium
RUN playwright install-deps

# Copy the application code and entry script
COPY src/ .
COPY entry.sh .
RUN chmod +x ./entry.sh

# Set permissions for both root and non-root operation
RUN mkdir -p /tmp/screenshots && \
    chmod 777 /tmp/screenshots && \
    chown -R pixashot:pixashot /app && \
    chmod -R 755 /app

# Create required directories with appropriate permissions
RUN mkdir -p /app/data /app/logs && \
    chown -R pixashot:pixashot /app/data /app/logs && \
    chmod 777 /app/data /app/logs

# Expose the port the app runs on
EXPOSE ${PORT}

# Set security options
LABEL security.alpha.kubernetes.io/seccomp=runtime/default
LABEL security.alpha.kubernetes.io/unsafe-sysctls=""

# Set resource limits
ENV PLAYWRIGHT_BROWSERS_PATH=/app/ms-playwright
ENV NODE_OPTIONS="--max-old-space-size=2048"

# Use dumb-init as the entrypoint to handle signals properly
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Run the entry script which will handle user switching if needed
CMD ["./entry.sh"]