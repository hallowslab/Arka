#!/usr/bin/env bash
# celery_init.sh
# Usage: celery_init.sh <worker|beat> [queue_name]
#   queue_name  — Celery queue to consume (e.g. imapsync, mimir).
#                 Omit or empty to consume the default queue only.
set -euo pipefail

ROLE="${1:-worker}"
QUEUE="${2:-}"
APP_DIR="/app"
LOGFILE="$APP_DIR/celery_init.txt"

# Explicitly use the virtualenv binaries
VENV_BIN="$APP_DIR/.venv/bin"
PYTHON_BIN="$VENV_BIN/python"
CELERY_BIN="$VENV_BIN/celery"

{
    echo "--- celery_init.sh started at $(date) as role: $ROLE queue: ${QUEUE:-default} ---"
    echo "[DEBUG] Current user: $(id)"

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
    echo "Pool type: $CELERY_POOL" | tee -a "$LOGFILE"

    # Build queue argument if specified
    QUEUE_ARGS=""
    if [ -n "$QUEUE" ]; then
      QUEUE_ARGS="-Q $QUEUE"
      echo "Consuming queue: $QUEUE" | tee -a "$LOGFILE"
    fi

    if [ "${DJANGO_ENV:-development}" = "production" ]; then
      echo "Production worker mode" | tee -a "$LOGFILE"
      exec "$CELERY_BIN" \
        -A forj.celery worker $QUEUE_ARGS \
        --pool=${CELERY_POOL} \
        -c 25 \
        --hostname=worker@%h \
        --max-tasks-per-child=5 \
        --time-limit=14700 \
        --soft-time-limit=14400 \
        --without-gossip --without-mingle --without-heartbeat \
        --loglevel=info
    else
      echo "Development worker mode" | tee -a "$LOGFILE"
      exec "$CELERY_BIN" \
        -A forj.celery worker $QUEUE_ARGS \
        --pool=${CELERY_POOL} \
        --hostname=worker@%h \
        --without-gossip --without-mingle --without-heartbeat \
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
