#!/usr/bin/env bash

USER_HOME=$(eval echo ~"$(whoami)")
CURRENT_USER="$(whoami)"

# Copy secrets
"$USER_HOME/copy_secrets.sh"

echo "Running init.sh..." > celery_init.txt

# Only install dependencies in development
if [ "$DJANGO_ENV" = "development" ]; then
  echo "Development mode detected, synchronizing dependencies..." >> celery_init.txt
  poetry sync >> celery_init.txt
fi

# Start the worker
echo "Starting worker..." >> celery_init.txt
if [ "$DJANGO_ENV" == "production" ]; then
    echo "Starting production worker" >> celery_init.txt
    "$USER_HOME/app/.venv/bin/python" -m celery -A forj.celery worker --loglevel=INFO -c 100 --pool=gevent
else
    echo "Starting development worker" >> celery_init.txt
    "$USER_HOME/app/.venv/bin/python" -m celery -A forj.celery worker --loglevel=DEBUG --pool=solo
fi