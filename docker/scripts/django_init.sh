#!/usr/bin/env bash
set -e


# Add poetry path for non interactive shells (docker command call)
export PATH="$HOME/.local/bin:$PATH"

USER_HOME=$(eval echo ~"$(whoami)")
CURRENT_USER="$(whoami)"

# Copy secrets
"$USER_HOME/copy_secrets.sh"

echo "Running init.sh..." > django_init.txt

# Handle editable modules in development
if [ "$DJANGO_ENV" == "development" ] && [ ! -z "$ARKA_EDITABLE_MODULES" ]; then
    echo "Development mode detected, installing editable modules: $ARKA_EDITABLE_MODULES" >> django_init.txt
    IFS=',' read -ra ADDR <<< "$ARKA_EDITABLE_MODULES"
    for module in "${ADDR[@]}"; do
        if [ -d "/modules/$module" ]; then
            echo "Installing editable module: $module" >> django_init.txt
            "$USER_HOME/app/.venv/bin/python" -m pip install -e "/modules/$module" >> django_init.txt
        else
            echo "Warning: Module directory /modules/$module not found" >> django_init.txt
        fi
    done
fi


echo "Running DB migration check..."
if ! "$USER_HOME/app/.venv/bin/python" manage.py migrate --no-input --check >> django_init.txt; then
    echo "Running migrations" >> django_init.txt
    "$USER_HOME/app/.venv/bin/python" manage.py migrate --no-input >> django_init.txt
else
    echo "No migrations needed" >> django_init.txt
fi

# Run modular plugin migrations
echo "Running modular plugin migrations..." >> django_init.txt
"$USER_HOME/app/.venv/bin/python" manage.py migrate_modules >> django_init.txt


# Run the initadmin command (may fail if users already exist)
echo "Running initadmin command" >> django_init.txt
"$USER_HOME/app/.venv/bin/python" manage.py initadmin >> django_init.txt 2>&1 || true

# Load periodic tasks fixture
echo "Loading periodic tasks..." >> django_init.txt
"$USER_HOME/app/.venv/bin/python" manage.py loaddata periodic_tasks >> django_init.txt 2>&1 || true

# Run the create_management_group command
echo "Running create_management_groups command" >> django_init.txt
"$USER_HOME/app/.venv/bin/python" manage.py create_management_groups >> django_init.txt 2>&1 || true

# Collect static assets 
"$USER_HOME/app/.venv/bin/python" manage.py collectstatic --no-input

# Start the application
echo "Starting app..." >> django_init.txt
if [ "$DJANGO_ENV" == "production" ]; then
    echo "Starting production server" >> django_init.txt
    exec "$USER_HOME/app/.venv/bin/python" -m gunicorn arka.asgi:application -b 0.0.0.0:8000 -k uvicorn_worker.UvicornWorker
else
    echo "Starting development server" >> django_init.txt
    exec poetry run python manage.py runserver 0.0.0.0:8000
fi