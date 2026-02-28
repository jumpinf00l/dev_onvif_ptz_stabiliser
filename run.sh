#!/usr/bin/with-contenv bash
# ==============================================================================
# Home Assistant Add-on: ONVIF PTZ Stabiliser
# This script runs the Python application under s6-overlay management.
# ==============================================================================
set -e

# Run the Python script
exec python3 -u /app/ptz_monitor.py
