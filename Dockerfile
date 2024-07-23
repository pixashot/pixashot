# Use the official Playwright Python base image
FROM mcr.microsoft.com/playwright/python:v1.40.0

# Define environment variable for Playwright
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory inside the container
WORKDIR /usr/src/app

# Install media codecs
RUN apt-get update && apt-get install -y --no-install-recommends \
    libavcodec-extra \
    libavformat-extra \
    && apt-get install -y --no-install-recommends --assume-yes \
    ubuntu-restricted-extras \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt to the container
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code to the container
COPY . .

# Specify the command to run on container start
CMD ["python", "server.py"]