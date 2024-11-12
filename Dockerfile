# Use Playwright image
FROM mcr.microsoft.com/playwright/python:v1.47.0

# Set environment variables
ENV PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore

# Set the working directory
WORKDIR /app

# Install required system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user with the next available UID
RUN useradd -m appuser && \
    mkdir -p /tmp/screenshots /app/data /app/logs && \
    chown -R appuser:appuser /app /tmp/screenshots /app/data /app/logs

# Update pip and install requirements as non-root user
COPY --chown=appuser:appuser requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browser
RUN playwright install --with-deps chromium

# Copy application code
COPY --chown=appuser:appuser src/ /app
COPY --chown=appuser:appuser entry.sh .

# Prepare the entry script
RUN chmod +x entry.sh

# Switch to non-root user
USER appuser

# Expose the port
EXPOSE ${PORT}

# Run the entry script
CMD ["./entry.sh"]