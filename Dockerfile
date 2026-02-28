ARG BUILD_FROM=ghcr.io/hassio-addons/base:15.0.0
FROM ${BUILD_FROM}

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN \
    pip install --no-cache-dir -r requirements.txt

# Copy script
COPY ptz_monitor.py .

# Run the script
CMD [ "python3", "-u", "ptz_monitor.py" ]