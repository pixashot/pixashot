# Use the official Playwright Python base image
FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

# Define environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PORT=8080

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libavcodec-extra \
    libavformat-extra \
    xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and download browsers
RUN playwright install --with-deps chromium
RUN playwright install-deps

# Copy the application code to the container
COPY src/ .
COPY entry.sh /app/entry.sh
RUN chmod +x /app/entry.sh

# Expose the port the app runs on
EXPOSE ${PORT}

# Specify the command to run on container start with default values
ENTRYPOINT ["/entry.sh", "--workers", "4", "--threads", "1", "--timeout", "300",  "--port", "${PORT}"]