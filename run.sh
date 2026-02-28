#!/bin/sh

TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S.%3N")

echo "$TIMESTAMP - Starting ONVIF PTZ Stabiliser..."
exec python3 -u /app/ptz_monitor.py
