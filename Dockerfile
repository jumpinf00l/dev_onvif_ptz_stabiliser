ARG BUILD_FROM=ghcr.io/hassio-addons/base:15.0.0
FROM ${BUILD_FROM}

# Set work directory
WORKDIR /app

# Install Python and pip via apk
RUN apk add --no-cache python3 py3-pip

# Install dependencies using --break-system-packages
RUN pip install --no-cache-dir --break-system-packages zeep onvif-zeep requests

# Copy script and service script
COPY ptz_monitor.py .
COPY run.sh /etc/services.d/ptz_monitor/run

# Ensure the service script is executable
RUN chmod +x /etc/services.d/ptz_monitor/run

# The base image already sets ENTRYPOINT ["/init"]
