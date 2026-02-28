#!/usr/bin/with-contenv bash
# ==============================================================================
# Home Assistant Add-on: ONVIF PTZ Stabiliser
# ==============================================================================
set -e

echo "Starting ONVIF PTZ Monitor..."
exec python3 -u /app/ptz_monitor.py
