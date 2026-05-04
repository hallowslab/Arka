#!/usr/bin/env bash
# docker-entrypoint.sh
set -e
umask 0002

# This script runs as root at startup to fix volume permissions
# and then drops privileges to the desired user.

# Get the target user/uid from environment or default to arka
TARGET_USER="${CONTAINER_USER:-arka}"
GROUP_ID="${GID:-1002}"

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

echo "[ENTRYPOINT] Executing command as $TARGET_USER: $@"

# Use gosu to run the command as the specified user
exec gosu "$TARGET_USER" "$@"
