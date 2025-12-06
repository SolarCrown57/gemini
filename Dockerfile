# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Prevent Playwright from complaining about root user
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Set work directory
WORKDIR /app

# Install system dependencies required for building Python packages
# and basic tools
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and system dependencies
# We install only chromium to save space/time as it's the default for this app
RUN playwright install chromium \
    && playwright install-deps chromium

# Copy the rest of the application code
COPY . .

# Create a directory for default configs to support volume initialization
# We copy the local config folder to a defaults location
RUN mkdir -p /app/config_defaults && \
    cp -r config/* /app/config_defaults/ || true

# Copy and setup entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose the API and WebSocket ports
EXPOSE 28880 28881

# Define the entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]