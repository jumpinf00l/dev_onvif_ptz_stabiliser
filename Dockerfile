ARG BUILD_FROM=ghcr.io/hassio-addons/base:15.0.8
FROM $BUILD_FROM

WORKDIR /app

RUN apk add --no-cache python3 py3-pip coreutils

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir zeep onvif-zeep requests tzdata

COPY onvif_ptz_helper.py .
COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
