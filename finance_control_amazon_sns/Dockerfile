FROM python:3.12-alpine3.22

ARG BUILD_VERSION=1.0.2
ARG BUILD_ARCH=amd64
LABEL io.hass.version="${BUILD_VERSION}" \
    io.hass.type="app" \
    io.hass.arch="${BUILD_ARCH}"

RUN apk add --no-cache nginx tini \
    && python -m pip install --no-cache-dir cryptography==50.0.1

WORKDIR /app
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY code/finance_control /app/finance_control
COPY addon_entrypoint.py /app/addon_entrypoint.py
COPY nginx.conf /etc/nginx/nginx.conf
COPY run.sh /app/run.sh
RUN chmod 0755 /app/run.sh

EXPOSE 8788
ENTRYPOINT ["/sbin/tini", "--", "/app/run.sh"]
