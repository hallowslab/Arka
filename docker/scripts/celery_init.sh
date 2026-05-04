#!/usr/bin/env bash
# celery_init.sh
set -euo pipefail

ROLE="${1:-worker}"
APP_DIR="/app"
LOGFILE="$APP_DIR/celery_init.txt"

# Explicitly use the virtualenv binaries
VENV_BIN="$APP_DIR/.venv/bin"
PYTHON_BIN="$VENV_BIN/python"
CELERY_BIN="$VENV_BIN/celery"

{
    echo "--- celery_init.sh started at $(date) as role: $ROLE ---"
    echo "[DEBUG] Current user: $(id)"

    # Copy secrets
    bash "$APP_DIR/scripts/copy_secrets.sh"

    # Wait for migrations to be ready
    echo "Waiting for migrations to be applied..."
    while ! "$PYTHON_BIN" src/manage.py migrate --check; do
      echo "Migrations not ready yet or check failed. Retrying in 5s..."
      # Run once with output to log if it keeps failing
      "$PYTHON_BIN" src/manage.py migrate --check || true
      sleep 5
    done
    echo "Migrations are ready!"

} 2>&1 | tee -a "$LOGFILE"

case "$ROLE" in
  worker)
    echo "Starting Celery worker..." | tee -a "$LOGFILE"

    if [ "${DJANGO_ENV:-development}" = "production" ]; then
      echo "Production worker mode" | tee -a "$LOGFILE"
      exec "$CELERY_BIN" \
        -A forj.celery worker \
        --pool=prefork \
        -c 20 \
        --hostname=worker@%h \
        --max-tasks-per-child=5 \
        --time-limit=14700 \
        --soft-time-limit=14400 \
        --loglevel=info
    else
      echo "Development worker mode" | tee -a "$LOGFILE"
      exec "$CELERY_BIN" \
        -A forj.celery worker \
        --pool=solo \
        --hostname=worker@%h \
        --loglevel=DEBUG
    fi
    ;;

  beat)
    echo "Starting Celery Beat scheduler..." | tee -a "$LOGFILE"
    if [ "${DJANGO_ENV:-development}" = "production" ]; then
      echo "Production beat mode" | tee -a "$LOGFILE"
      exec "$CELERY_BIN" \
        -A forj.celery beat \
        -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler -f "$ARKA_LOGDIR/beat.log"
    else
      echo "Development beat mode" | tee -a "$LOGFILE"
      exec "$CELERY_BIN" \
        -A forj.celery beat \
        -l DEBUG --scheduler django_celery_beat.schedulers:DatabaseScheduler -f "$ARKA_LOGDIR/beat.log"
    fi
    ;;

  *)
    echo "ERROR: Unknown role '$ROLE'. Expected 'worker' or 'beat'." | tee -a "$LOGFILE"
    exit 1
    ;;
esac