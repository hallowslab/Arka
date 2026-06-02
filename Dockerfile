# Base image for imapsync binary
FROM hallowtechlab/imapsync:debian_trixie-2.229 AS imapsync_binary

# Stage 1: Base image with system dependencies and users
FROM python:3.13-slim AS base

SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

ARG GID=1002
ARG GROUPNAME=arka

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    ARKA_LOGDIR=${ARKA_LOGDIR:-/app/ARKA_LOGS} \
    STATIC_ROOT=${STATIC_ROOT:-/var/www/static} \
    PATH="/uv/bin:${PATH}"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    ca-certificates \
    git \
    gosu \
    procps \
    postgresql-client \
    libauthen-ntlm-perl \
    libcgi-pm-perl libcrypt-openssl-rsa-perl libdata-uniqid-perl libencode-imaputf7-perl libfile-copy-recursive-perl libfile-tail-perl \
    libio-socket-inet6-perl libio-socket-ssl-perl libio-tee-perl libhtml-parser-perl libjson-webtoken-perl libmail-imapclient-perl \
    libparse-recdescent-perl libproc-processtable-perl libmodule-scandeps-perl libreadonly-perl libregexp-common-perl libsys-meminfo-perl \
    libterm-readkey-perl libtest-mockobject-perl libtest-pod-perl libunicode-string-perl liburi-perl libwww-perl libtest-nowarnings-perl \
    libtest-deep-perl libtest-warn-perl \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create users
RUN addgroup --gid $GID $GROUPNAME && \
    adduser --disabled-password --gecos '' --uid 1001 --gid $GID arka && \
    adduser --disabled-password --gecos '' --uid 1002 --gid $GID forj

# Copy imapsync from binary image
COPY --from=imapsync_binary /usr/bin/imapsync /usr/bin/imapsync

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uv/bin/uv

# Create required directories and set ownership
# Using 777 for logs and static to ensure compatibility with named volumes on all platforms
RUN mkdir -p /app/scripts /app/src "$ARKA_LOGDIR" "$STATIC_ROOT" && \
    chown -R arka:$GROUPNAME /app "$ARKA_LOGDIR" "$STATIC_ROOT" && \
    chmod -R 775 /app "$ARKA_LOGDIR" "$STATIC_ROOT"

# Copy entrypoint script
COPY docker/scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]

# Stage 2: Development
FROM base AS development
ARG ENABLED_APPS=""
ARG MODULE_SOURCE=git
ARG CELERY_POOL=solo
ARG DJANGO_ENV=development
ENV DJANGO_ENV=${DJANGO_ENV} \
    CELERY_POOL=${CELERY_POOL} \
    ENABLED_APPS=${ENABLED_APPS}
COPY pyproject.toml uv.lock* README.md ./
# We don't copy modular apps yet to ensure uv sync can fetch git versions first
RUN uv sync --frozen && \
    chown -R arka:$GROUPNAME /app/.venv && \
    chmod -R 775 /app/.venv
# Now copy Everything including modular apps
COPY src/ ./src/
# Perform editable installs for modular apps to override git versions
RUN uv pip install -e src/modular_apps/AERA \
    -e src/modular_apps/Pymap \
    -e src/modular_apps/DBTOOL \
    -e src/modular_apps/NETTOOLS \
    -e src/modular_apps/MXR \
    -e src/modular_apps/BIFROST

COPY docker/scripts/ /app/scripts/
RUN chmod +x /app/scripts/*.sh && chown -R arka:$GROUPNAME /app

CMD ["/app/scripts/django_init.sh"]

# Stage 3: Builder - Resolve dependencies for production
FROM base AS production-builder
ARG ENABLED_APPS=""
ARG MODULE_SOURCE=git
COPY pyproject.toml uv.lock* README.md ./
# Copy core source
COPY src/arka /app/src/arka
COPY src/forj /app/src/forj
# Conditionally copy local module sources (only used when MODULE_SOURCE=local)
COPY src/modular_apps/ /tmp/modular_apps/

# Install core deps, then conditionally install enabled modules
RUN if [ "$MODULE_SOURCE" = "local" ]; then \
    uv sync --frozen --no-dev --no-editable; \
    if echo "$ENABLED_APPS" | grep -iq "AERA"; then uv pip install /tmp/modular_apps/AERA; fi; \
    if echo "$ENABLED_APPS" | grep -iq "PYMAP"; then uv pip install /tmp/modular_apps/Pymap; fi; \
    if echo "$ENABLED_APPS" | grep -iq "DBTOOL"; then uv pip install /tmp/modular_apps/DBTOOL; fi; \
    if echo "$ENABLED_APPS" | grep -iq "NETTOOLS"; then uv pip install /tmp/modular_apps/NETTOOLS; fi; \
    if echo "$ENABLED_APPS" | grep -iq "MXR"; then uv pip install /tmp/modular_apps/MXR; fi; \
    if echo "$ENABLED_APPS" | grep -iq "BIFROST"; then uv pip install /tmp/modular_apps/BIFROST; fi; \
    else \
    EXTRAS=""; \
    if echo "$ENABLED_APPS" | grep -iq "AERA"; then EXTRAS="$EXTRAS --extra aera"; fi; \
    if echo "$ENABLED_APPS" | grep -iq "PYMAP"; then EXTRAS="$EXTRAS --extra pymap"; fi; \
    if echo "$ENABLED_APPS" | grep -iq "DBTOOL"; then EXTRAS="$EXTRAS --extra dbtool"; fi; \
    if echo "$ENABLED_APPS" | grep -iq "NETTOOLS"; then EXTRAS="$EXTRAS --extra nettools"; fi; \
    if echo "$ENABLED_APPS" | grep -iq "MXR"; then EXTRAS="$EXTRAS --extra mxr"; fi; \
    if echo "$ENABLED_APPS" | grep -iq "BIFROST"; then EXTRAS="$EXTRAS --extra bifrost"; fi; \
    uv sync --frozen --no-dev --no-editable $EXTRAS; \
    fi; \
    rm -rf /tmp/modular_apps

# Stage 4: Production Base (Common for Arka and Forj)
FROM base AS production-base

ARG ENABLED_APPS=""
ARG DJANGO_ENV=production
ARG CELERY_POOL=gevent

ENV DJANGO_ENV=${DJANGO_ENV} \
    CELERY_POOL=${CELERY_POOL} \
    ENABLED_APPS=${ENABLED_APPS} \
    POSTGRES_DB=${POSTGRES_DB} \
    POSTGRES_USER=${POSTGRES_USER} \
    POSTGRES_HOST=${POSTGRES_HOST} \
    POSTGRES_PORT=${POSTGRES_PORT}

COPY --from=production-builder /app/.venv /app/.venv
COPY src/arka /app/src/arka
COPY src/forj /app/src/forj
COPY src/static /app/src/static
COPY src/templates /app/src/templates
COPY src/manage.py /app/src/manage.py
COPY docker/scripts/ /app/scripts/
RUN chmod +x /app/scripts/*.sh && \
    chown -R arka:$GROUPNAME /app
ENV PATH="/app/.venv/bin:$PATH"

# Stage 5: Production Arka (Django)
FROM production-base AS final-production
EXPOSE 8000
CMD ["/app/scripts/django_init.sh"]

# Stage 6: Production Forj (Worker)
FROM production-base AS final-production-worker
CMD ["/app/scripts/celery_init.sh", "worker"]

