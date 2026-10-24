#!/bin/sh
set -e

# Ensure persistent directories exist
mkdir -p /app/data /app/media/images /app/media/audio /app/static /app/templates

# If persistent SQLite DB doesn't exist, seed it from repository DB if available
if [ ! -f /app/data/cleancity.db ] && [ -f /app/cleancity.db ]; then
    echo "[CleanCity] Seeding initial database to /app/data/cleancity.db..."
    cp /app/cleancity.db /app/data/cleancity.db
fi

# Execute the container command
exec "$@"
