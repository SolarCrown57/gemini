#!/bin/bash
set -e

# Define directories
CONFIG_DIR="/app/config"
DEFAULTS_DIR="/app/config_defaults"

# Ensure config directory exists
mkdir -p "$CONFIG_DIR"

# Initialize config files if they are missing
# This handles the case where a new volume is mounted
echo "Checking configuration files..."
if [ -d "$DEFAULTS_DIR" ]; then
    for file in "$DEFAULTS_DIR"/*; do
        [ -e "$file" ] || continue
        filename=$(basename "$file")
        target="$CONFIG_DIR/$filename"
        
        if [ ! -e "$target" ]; then
            echo "Initializing missing config: $filename"
            # Use -r to handle directories like browser_data if they exist in defaults
            cp -r "$file" "$target"
        fi
    done
fi

# Start the application
echo "Starting Vertex AI Proxy..."
exec python main.py
