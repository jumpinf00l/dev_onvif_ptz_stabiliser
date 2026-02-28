ARG BUILD_FROM=ghcr.io/hassio-addons/base:15.0.0
FROM ${BUILD_FROM}

# Set work directory
WORKDIR /app

# Install Python and pip via apk
RUN apk add --no-cache python3 py3-pip

# Create a virtual environment and install dependencies inside it
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir zeep onvif-zeep requests

# Copy script
COPY ptz_monitor.py .

# Set the entrypoint to the s6 init system
ENTRYPOINT [ "/init" ]

# Run the script using the python from the virtual environment
CMD [ "python3", "-u", "ptz_monitor.py" ]
