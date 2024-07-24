# Use the official Playwright Python base image
FROM mcr.microsoft.com/playwright/python:v1.45.0-jammy

# Define environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libavcodec-extra \
    libavformat-extra \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code to the container
COPY src/ .
COPY js/ ./js/

# Expose the port the app runs on
EXPOSE 8080

# Specify the command to run on container start
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--threads", "1", "app:app"]