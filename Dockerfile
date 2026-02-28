ARG BUILD_FROM=ghcr.io/hassio-addons/base:15.0.0
FROM ${BUILD_FROM}

# Set work directory
WORKDIR /app

# Install Python, pip, and dependencies via apk
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-requests \
    py3-zeep

# Install onvif-zeep via pip (this should not conflict now)
RUN pip install --no-cache-dir onvif-zeep

# Copy script
COPY ptz_monitor.py .

# Run the script
CMD [ "python3", "-u", "ptz_monitor.py" ]
