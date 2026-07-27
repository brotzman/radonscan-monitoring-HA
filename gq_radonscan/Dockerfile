FROM ghcr.io/home-assistant/base:3.24

ARG BUILD_VERSION="5.5.0"
ARG BUILD_ARCH="unknown"

ENV PYTHONPATH="/usr/local/lib"

RUN apk add --no-cache python3 py3-paho-mqtt py3-pyserial py3-reportlab
COPY rootfs /
RUN chmod 0755 /etc/services.d/gq_radonscan/run /usr/local/bin/gq_radonscan_service.py \
    && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/usr/local/lib python3 -m compileall -q /usr/local/lib/radonscan3 \
    && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/usr/local/lib python3 -c \
      'from radonscan3.decoder import decode; from radonscan3.i18n import SUPPORTED, load; assert len(SUPPORTED)==8; [load(x) for x in SUPPORTED]'

LABEL org.opencontainers.image.title="Radon Monitoring Home Assistant App" \
      org.opencontainers.image.description="Local read-only GQ RadonScan monitoring with analysis, GMCMap upload, reports and data management." \
      org.opencontainers.image.licenses="MIT" \
      io.hass.version="${BUILD_VERSION}" \
      io.hass.type="app" \
      io.hass.name="Radon Monitoring" \
      io.hass.arch="${BUILD_ARCH}"
