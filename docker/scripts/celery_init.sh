#!/usr/bin/env bash
set -euo pipefail

ROLE="${1:-worker}"

USER_HOME=$(eval echo ~"$(whoami)")
CURRENT_USER="$(whoami)"
VENV_PY="$USER_HOME/app/.venv/bin/python"
DJANGO_ENV="${DJANGO_ENV:-development}"

# Copy secrets
"$USER_HOME/copy_secrets.sh"

LOGFILE="celery_init.txt"
echo "Running init.sh as role: $ROLE" | tee "$LOGFILE"

# Only install dependencies in development
if [ "$DJANGO_ENV" = "development" ]; then
  echo "Development mode detected, synchronizing dependencies..." | tee -a "$LOGFILE"
  poetry sync >> "$LOGFILE" 2>&1
fi

# Handle editable modules in development
if [ "$DJANGO_ENV" = "development" ] && [ -n "${ARKA_EDITABLE_MODULES:-}" ]; then
    echo "Development mode detected, installing editable modules: $ARKA_EDITABLE_MODULES" | tee -a "$LOGFILE"
    IFS=',' read -ra ADDR <<< "$ARKA_EDITABLE_MODULES"
    for module in "${ADDR[@]}"; do
        if [ -d "/modules/$module" ]; then
            echo "Installing editable module: $module" | tee -a "$LOGFILE"
            "$VENV_PY" -m pip install -e "/modules/$module" >> "$LOGFILE" 2>&1
        else
            echo "Warning: Module directory /modules/$module not found" | tee -a "$LOGFILE"
        fi
    done
fi

# Wait for migrations to be ready
echo "Waiting for migrations to be applied..." | tee -a "$LOGFILE"
until "$VENV_PY" manage.py migrate --check >> "$LOGFILE" 2>&1; do
  echo "Migrations not ready yet. Waiting 5 seconds..." | tee -a "$LOGFILE"
  sleep 5
done
echo "Migrations are ready!" | tee -a "$LOGFILE"

case "$ROLE" in
  worker)
    echo "Starting Celery worker..." | tee -a "$LOGFILE"

    if [ "$DJANGO_ENV" = "production" ]; then
      echo "Production worker mode" | tee -a "$LOGFILE"
      exec "$VENV_PY" -m celery \
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
      exec "$VENV_PY" -m celery \
        -A forj.celery worker \
        --pool=solo \
        --hostname=worker@%h \
        --loglevel=DEBUG
    fi
    ;;

  beat)
    echo "Starting Celery Beat scheduler..." | tee -a "$LOGFILE"
    if [ "$DJANGO_ENV" = "production" ]; then
      echo "Production beat mode" | tee -a "$LOGFILE"
      exec "$VENV_PY" -m celery \
        -A forj.celery beat \
        -l ${FORJ_LOG_LEVEL:-INFO} --scheduler django_celery_beat.schedulers:DatabaseScheduler -f $ARKA_LOGDIR/beat.log
    else
      echo "Development beat mode" | tee -a "$LOGFILE"
      exec "$VENV_PY" -m celery \
        -A forj.celery beat \
        -l ${FORJ_LOG_LEVEL:-DEBUG} --scheduler django_celery_beat.schedulers:DatabaseScheduler -f $ARKA_LOGDIR/beat.log
    fi
    ;;

  *)
    echo "ERROR: Unknown role '$ROLE'. Expected 'worker' or 'beat'." | tee -a "$LOGFILE"
    exit 1
    ;;
esac