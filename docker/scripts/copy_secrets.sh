#!/usr/bin/env bash
set -euo pipefail

echo "[INFO] Running copy_secrets.sh as $(whoami) (id: $(id))"

SECRETS_DIR="/run/secrets"
# The Django app's BASE_DIR is /app/src
APP_DIR="/app/src"
TARGET_USER="${TARGET_USER:-$(id -un)}"
TARGET_GROUP="${TARGET_GROUP:-$(id -gn)}"
TARGET_HOME="${TARGET_HOME:-$(getent passwd "$TARGET_USER" | cut -d: -f6)}"

# Ensure we are in a safe directory
cd "/app"

declare -A FILE_MAP=(
  [".pg_service.conf"]="$TARGET_HOME/.pg_service.conf"
  [".pgpass"]="$TARGET_HOME/.pgpass"
  [".secret"]="$APP_DIR/.secret"
  ["config.json"]="$APP_DIR/config.json"
  ["config.dev.json"]="$APP_DIR/config.dev.json"
)

# Copy secrets if they exist
for src_file in "${!FILE_MAP[@]}"; do
    src_path="$SECRETS_DIR/$src_file"
    dest_path="${FILE_MAP[$src_file]}"

    if [ -f "$src_path" ]; then
        mkdir -p "$(dirname "$dest_path")"
        tmp_dest="${dest_path}.tmp.$RANDOM"
        cp "$src_path" "$tmp_dest"
        # 600 for .pgpass and pg_service, 644 for others
        if [[ "$src_file" == ".pgpass" || "$src_file" == ".pg_service.conf" ]]; then
            chmod 600 "$tmp_dest"
            chown "$TARGET_USER:$TARGET_GROUP" "$tmp_dest"
        else
            chmod 644 "$tmp_dest"
        fi
        mv -f "$tmp_dest" "$dest_path"
        echo "[INFO] Copied $src_file to $dest_path (atomically)"
    else
        echo "[WARN] Secret file $src_path not found; skipping"
    fi
done

echo "[INFO] Done"
