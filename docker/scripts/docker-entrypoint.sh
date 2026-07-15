#!/usr/bin/env bash
# docker-entrypoint.sh
set -e
umask 0002

# This script runs as root at startup to fix volume permissions
# and then drops privileges to the desired user.

# Get the target user/uid from environment or default to arka
TARGET_USER="${CONTAINER_USER:-arka}"
GROUP_ID="${GID:-10002}"

echo "[ENTRYPOINT] Ensuring permissions for $ARKA_LOGDIR and $STATIC_ROOT..."

# Ensure the directories exist
mkdir -p "$ARKA_LOGDIR" "$STATIC_ROOT"

# Fix permissions on key directories to allow shared group access
# We chown to the shared group, set 2775 (setgid) to ensure new files inherit the group
echo "[ENTRYPOINT] Applying group $GROUP_ID to $ARKA_LOGDIR and $STATIC_ROOT"
chgrp -R "$GROUP_ID" "$ARKA_LOGDIR" "$STATIC_ROOT" || true
chmod 2775 "$ARKA_LOGDIR" "$STATIC_ROOT" || true

# Ensure existing files are group-writable
chmod -R g+w "$ARKA_LOGDIR" "$STATIC_ROOT" || true

# Ensure MIMIR data directories exist and are writable
if [ -n "${MIMIR_INPUT_DIR:-}" ] && [ -n "${MIMIR_REPORT_DIR:-}" ]; then
    echo "[ENTRYPOINT] Ensuring permissions for MIMIR data directories..."
    mkdir -p "$MIMIR_INPUT_DIR" "$MIMIR_REPORT_DIR"
    chgrp -R "$GROUP_ID" "$MIMIR_INPUT_DIR" "$MIMIR_REPORT_DIR" || true
    chmod 2775 "$MIMIR_INPUT_DIR" "$MIMIR_REPORT_DIR" || true
    chmod -R g+w "$MIMIR_INPUT_DIR" "$MIMIR_REPORT_DIR" || true
fi

# Ensure GeoIP database directory exists
if [ -n "${MIMIR_GEOIP_DB_PATH:-/app/data/mimir/dbip-city-lite.mmdb}" ]; then
    GEOIP_DIR=$(dirname "$MIMIR_GEOIP_DB_PATH")
    mkdir -p "$GEOIP_DIR"
    chgrp -R "$GROUP_ID" "$GEOIP_DIR" || true
    chmod 2775 "$GEOIP_DIR" || true
fi

if [ -x /app/scripts/copy_secrets.sh ]; then
    echo "[ENTRYPOINT] Copying secrets before dropping privileges"
    export TARGET_USER
    export TARGET_GROUP="$GROUP_ID"
    export TARGET_HOME="$(getent passwd "$TARGET_USER" | cut -d: -f6)"
    bash /app/scripts/copy_secrets.sh
fi

echo "[ENTRYPOINT] Executing command as $TARGET_USER: $@"

# Use gosu to run the command as the specified user
exec gosu "$TARGET_USER" "$@"
