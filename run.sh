#!/bin/sh

TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S.%3N")

echo "$TIMESTAMP - Starting ONVIF PTZ Helper..."
exec python3 -u /app/onvif_ptz_helper.py
