#!/bin/sh
# ==============================================================================
# Home Assistant Add-on: ONVIF PTZ Stabiliser
# ==============================================================================

echo "Starting ONVIF PTZ Monitor..."
exec python3 -u /app/ptz_monitor.py
