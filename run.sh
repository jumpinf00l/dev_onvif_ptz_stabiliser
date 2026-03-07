#!/usr/bin/with-contenv bashio

export TZ=$(bashio::info.timezone)

TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S.%3N")

echo "$TIMESTAMP - [I] - [System] - Starting ONVIF PTZ Helper..."
exec python3 -u /app/onvif_ptz_helper.py
