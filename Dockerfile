ARG BUILD_FROM=ghcr.io/hassio-addons/base:15.0.8
FROM $BUILD_FROM

# Set work directory
WORKDIR /app

# Copy script and service script
COPY ptz_monitor.py .
COPY run.sh /
RUN chmod a+x /run.sh

# Install Python, pip, and dependencies
RUN apk add --no-cache python3 py3-pip coreutils
RUN pip install --no-cache-dir --break-system-packages zeep onvif-zeep requests

CMD [ "/run.sh" ]
