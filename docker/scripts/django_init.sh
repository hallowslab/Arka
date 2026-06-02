#!/usr/bin/env bash
# django_init.sh
set -e

APP_DIR="/app"
LOGFILE="$APP_DIR/django_init.txt"

# Explicitly use the virtualenv binaries
VENV_BIN="$APP_DIR/.venv/bin"
PYTHON_BIN="$VENV_BIN/python"

echo "[DEBUG] ENABLED_APPS: $ENABLED_APPS"

sleep 13

# Use a subshell and tee to capture everything to the logfile AND stdout
{
    echo "--- django_init.sh started at $(date) ---"
    echo "[DEBUG] Current user: $(id)"
    echo "[DEBUG] APP_DIR: $APP_DIR"
    echo "[DEBUG] ARKA_LOGDIR: $ARKA_LOGDIR"

    echo "[DEBUG] Permissions check:"
    ls -ld "$ARKA_LOGDIR" || echo "[WARN] Log dir not found"
    ls -la "$APP_DIR/src/.secret" "$APP_DIR/src/config.dev.json" || echo "[WARN] Secret files not found"

    echo "Running DB migration check..."
    if ! "$PYTHON_BIN" src/manage.py migrate --no-input --check; then
        echo "Running migrations..."
        "$PYTHON_BIN" src/manage.py migrate --no-input
    else
        echo "No migrations needed."
    fi

    # Run the initadmin command
    echo "Running initadmin command..."
    "$PYTHON_BIN" src/manage.py initadmin || true

    # Load periodic tasks fixture
    echo "Loading periodic tasks..."
    "$PYTHON_BIN" src/manage.py loaddata periodic_tasks || true

    # Run the create_management_group command
    echo "Running create_management_groups command..."
    "$PYTHON_BIN" src/manage.py create_management_groups || true

    # Collect static assets 
    echo "Collecting static assets (STATIC_ROOT: $STATIC_ROOT)..."
    "$PYTHON_BIN" src/manage.py collectstatic --no-input

    echo "--- django_init.sh finished setup at $(date) ---"
} 2>&1 | tee -a "$LOGFILE"

# Start the application (exec replaces the shell, so it must be outside the brace block for signals)
echo "Starting app..." | tee -a "$LOGFILE"
if [ "$DJANGO_ENV" == "production" ]; then
    echo "Starting production server (Gunicorn)" | tee -a "$LOGFILE"
    exec "$VENV_BIN/gunicorn" arka.asgi:application -b 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker
else
    echo "Starting development server (Runserver)" | tee -a "$LOGFILE"
    exec "$PYTHON_BIN" src/manage.py runserver 0.0.0.0:8000
fi
