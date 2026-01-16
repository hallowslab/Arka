#!/usr/bin/env bash
set -euo pipefail

ROLE="${1:-worker}"

USER_HOME=$(eval echo ~"$(whoami)")
CURRENT_USER="$(whoami)"
VENV_PY="$USER_HOME/app/.venv/bin/python"

# Copy secrets
"$USER_HOME/copy_secrets.sh"

LOGFILE="celery_init.txt"
echo "Running init.sh as role: $ROLE" > "$LOGFILE"

# Only install dependencies in development
if [ "$DJANGO_ENV" = "development" ]; then
  echo "Development mode detected, synchronizing dependencies..." >> "$LOGFILE"
  poetry sync >> "$LOGFILE"
fi

case "$ROLE" in
  worker)
    echo "Starting Celery worker..." >> "$LOGFILE"

    if [ "$DJANGO_ENV" = "production" ]; then
      echo "Production worker mode" >> "$LOGFILE"
      exec "$VENV_PY" -m celery \
        -A forj.celery worker \
        --loglevel=INFO \
        -c 100 \
        --pool=gevent
    else
      echo "Development worker mode" >> "$LOGFILE"
      exec "$VENV_PY" -m celery \
        -A forj.celery worker \
        --loglevel=DEBUG \
        --pool=solo
    fi
    ;;

  beat)
    echo "Starting Celery Beat scheduler..." >> "$LOGFILE"
    if [ "$DJANGO_ENV" = "production" ]; then
      echo "Production beat mode" >> "$LOGFILE"
      exec "$VENV_PY" -m celery \
        -A forj.celery beat \
        -l ${FORJ_LOG_LEVEL:-INFO} --scheduler django_celery_beat.schedulers:DatabaseScheduler -f $ARKA_LOGDIR/beat.log
    else
      echo "Development beat mode" >> "$LOGFILE"
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
