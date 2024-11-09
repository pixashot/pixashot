# Use the official Playwright Python base image
FROM mcr.microsoft.com/playwright/python:v1.35.0-focal

# Set environment variables
ENV PORT=8080 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Set the working directory
WORKDIR /app

# Install required system packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser
RUN playwright install --with-deps chromium

# Copy application code
COPY src/ /app/src/
COPY entry.sh .

# Prepare the entry script
RUN chmod +x entry.sh

# Create required directories
RUN mkdir -p /tmp/screenshots /app/data /app/logs \
    && chmod 777 /tmp/screenshots /app/data /app/logs

# Expose the port
EXPOSE ${PORT}

# Run the entry script
CMD ["./entry.sh"]