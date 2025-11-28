#!/usr/bin/env bash

# Add poetry path for non interactive shells (docker command call)
export PATH="$HOME/.local/bin:$PATH"

USER_HOME=$(eval echo ~"$(whoami)")
CURRENT_USER="$(whoami)"

# Copy secrets
"$USER_HOME/copy_secrets.sh"

echo "Running init.sh..." > django_init.txt

# Only install dependencies in development
if [ "$DJANGO_ENV" = "development" ]; then
  echo "Development mode detected, synchronizing dependencies..." >> django_init.txt
  poetry sync >> django_init.txt
fi

echo "Running DB migration check..."
if ! "$USER_HOME/app/.venv/bin/python" manage.py migrate --no-input --check >> django_init.txt; then
    echo "Running migrations" >> django_init.txt
    "$USER_HOME/app/.venv/bin/python" manage.py migrate --no-input >> django_init.txt
else
    echo "No migrations needed" >> django_init.txt
fi

# Run the initadmin command
echo "Running initadmin command" >> django_init.txt
"$USER_HOME/app/.venv/bin/python" manage.py initadmin >> django_init.txt

# Run the create_management_group command
echo "Running create_management_groups command" >> django_init.txt
"$USER_HOME/app/.venv/bin/python" manage.py create_management_groups >> django_init.txt

# Collect static assets 
"$USER_HOME/app/.venv/bin/python" manage.py collectstatic --no-input

# Start the application
echo "Starting app..." >> django_init.txt
if [ "$DJANGO_ENV" == "production" ]; then
    echo "Starting production server" >> django_init.txt
    "$USER_HOME/app/.venv/bin/python" -m gunicorn arka.asgi:application -b 0.0.0.0:8000 -k uvicorn.workers.UvicornWorker
else
    echo "Starting development server" >> django_init.txt
    poetry run python manage.py runserver 0.0.0.0:8000
fi