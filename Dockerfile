FROM python:3.13-slim AS builder

SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

ARG DJANGO_ENV \
    PYMAP_ENABLED \
    AERA_ENABLED

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1 \
    # Poetry
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_HOME='/opt/pypoetry' \
    POETRY_VIRTUALENVS_PREFER_ACTIVE_PYTHON=true \
    POETRY_INSTALLER_MAX_WORKERS=10 \
    # App
    DJANGO_ENV=${DJANGO_ENV} \
    PYMAP_ENABLED=${PYMAP_ENABLED} \
    AERA_ENABLED=${AERA_ENABLED}

RUN apt-get update && apt-get install --no-install-recommends -y pipx \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

RUN pipx install poetry

ENV PATH="/root/.local/bin:$PATH"
ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /app

# For logging dependency management
RUN mkdir -p /tmp/dependency_logs

#COPY src/modular_apps ./modular_apps
#RUN poetry install --with dev,local_apps --no-root

COPY src/pyproject.toml src/poetry.lock* ./
COPY src/select_modular_branches.py ./

# Run branch selector (Sets the branches in pyproject.toml)
RUN if [ "$DJANGO_ENV" = "development" ]; then \
    pip install toml; \
    python select_modular_branches.py 2>&1 | tee -a /tmp/dependency_logs/select_modular_branches.log; \
    poetry lock; \
    fi

# Install dependencies, log operations to file
RUN LOGFILE="/tmp/dependency_logs/dependency_install.log" && \
    echo "Starting dependency installation..." | tee -a "$LOGFILE" && \
    poetry install --only main --no-root 2>&1 | tee -a "$LOGFILE" && \
    echo "Checking modular apps dependencies" | tee -a "$LOGFILE" && \
    [ "$PYMAP_ENABLED" = 'True' ] && echo "Installing pymap dependencies" | tee -a "$LOGFILE" && poetry install --only pymap --no-root 2>&1 | tee -a "$LOGFILE"; \
    [ "$AERA_ENABLED" = 'True' ] && echo "Installing aera dependencies" | tee -a "$LOGFILE" && poetry install --only aera --no-root 2>&1 | tee -a "$LOGFILE"; \
    if [ "$DJANGO_ENV" = "development" ]; then \
    echo "Development environment detected" | tee -a "$LOGFILE"; \
    poetry install --only dev --no-root 2>&1 | tee -a "$LOGFILE"; \
    echo "Active modular apps: pymap: $PYMAP_ENABLED, aera: $AERA_ENABLED" | tee -a "$LOGFILE"; \
    echo "Finished installing dev dependencies" | tee -a "$LOGFILE"; \
    fi

# Move the logs to .venv so they are copied over to other stages
RUN mkdir -p .venv/logs && \
    mv /tmp/dependency_logs/*.log .venv/logs/

### ARKA
FROM python:3.13-slim AS arka

# Helps track down issues in command execution
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

ARG DJANGO_ENV \
    GROUPNAME \
    GID \
    STATIC_ROOT \
    ARKA_LOGDIR

# python:
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1 \
    # Poetry
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_HOME='/opt/pypoetry' \
    POETRY_VIRTUALENVS_PREFER_ACTIVE_PYTHON=true \
    POETRY_INSTALLER_MAX_WORKERS=10 \
    # APP
    DJANGO_ENV=${DJANGO_ENV} \
    STATIC_ROOT=${STATIC_ROOT} \
    DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-arka.settings} \
    ARKA_LOGDIR=${ARKA_LOGDIR}


RUN if [ "$DJANGO_ENV" = "development" ]; then \
    apt-get update && \
    apt-get install --no-install-recommends -y pipx && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    apt-get clean -y && rm -rf /var/lib/apt/lists/*; \
    fi

# create user+group
RUN addgroup --gid $GID $GROUPNAME \
    && adduser --disabled-password --gecos '' --uid 1001 --gid $GID arka

# Create the log directory and add permissions to user and group
RUN mkdir -p $ARKA_LOGDIR
RUN touch "$ARKA_LOGDIR/arka-dev.log" "$ARKA_LOGDIR/pymap.log"
RUN chown -R arka:$GROUPNAME $ARKA_LOGDIR && chmod -R g+rw $ARKA_LOGDIR
# Fix perms on static root for asset collection
RUN mkdir -p $STATIC_ROOT
RUN chown -R arka:$GROUPNAME $STATIC_ROOT && chmod -R g+rw $STATIC_ROOT

# switch to user
USER arka

RUN if [ "$DJANGO_ENV" = "development" ]; then \
    pipx install poetry && \
    echo 'export PATH="/home/arka/.local/bin:$PATH"' >> /home/arka/.bashrc && \
    echo 'export PATH="$POETRY_HOME/bin:$PATH"' >> /home/arka/.bashrc; \
    fi
ENV PATH="/home/arka/.local/bin:${PATH}"

WORKDIR /home/arka/app

COPY --from=builder /app/.venv /home/arka/app/.venv
ENV PATH="/home/arka/app/.venv/bin:$PATH"

COPY docker/scripts/django_init.sh /home/arka/app/init.sh
COPY docker/scripts/copy_secrets.sh /home/arka/copy_secrets.sh
COPY src/ .

# fix perms
USER root
RUN chown -R arka:$GROUPNAME /home/arka/app
USER arka

EXPOSE 8000

### FORJ
FROM python:3.13-slim AS forj-worker

# Helps track down issues in command execution
SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

ARG DJANGO_ENV \
    GROUPNAME \
    GID \
    STATIC_ROOT \
    ARKA_LOGDIR

# python:
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PYTHONDONTWRITEBYTECODE=1 \
    # Poetry
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_HOME='/opt/pypoetry' \
    POETRY_VIRTUALENVS_PREFER_ACTIVE_PYTHON=true \
    POETRY_INSTALLER_MAX_WORKERS=10 \
    # APP
    DJANGO_ENV=${DJANGO_ENV} \
    DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-arka.settings} \
    STATIC_ROOT=${STATIC_ROOT} \
    ARKA_LOGDIR=${ARKA_LOGDIR}


RUN if [ "$DJANGO_ENV" = "development" ]; then \
    apt-get update && \
    apt-get install --no-install-recommends -y pipx && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    apt-get clean -y && rm -rf /var/lib/apt/lists/*; \
    fi

# create user+group
RUN addgroup --gid $GID $GROUPNAME \
    && adduser --disabled-password --gecos '' --uid 1001 --gid $GID forj

# Create the log directory and add permissions to user and group
RUN mkdir -p $ARKA_LOGDIR
RUN touch "$ARKA_LOGDIR/arka-dev.log" "$ARKA_LOGDIR/pymap.log"
RUN chown -R forj:$GROUPNAME $ARKA_LOGDIR && chmod -R g+rw $ARKA_LOGDIR

# switch to user
USER forj

RUN if [ "$DJANGO_ENV" = "development" ]; then \
    pipx install poetry && \
    echo 'export PATH="/home/forj/.local/bin:$PATH"' >> /home/forj/.bashrc && \
    echo 'export PATH="$POETRY_HOME/bin:$PATH"' >> /home/forj/.bashrc; \
    fi
ENV PATH="/home/forj/.local/bin:${PATH}"


WORKDIR /home/forj/app

COPY --from=builder /app/.venv /home/forj/app/.venv
ENV PATH="/home/forj/app/.venv/bin:$PATH"

COPY docker/scripts/celery_init.sh /home/forj/app/init.sh
COPY docker/scripts/copy_secrets.sh /home/forj/copy_secrets.sh
COPY src/ .

# fix perms
USER root
RUN chown -R forj:$GROUPNAME /home/forj/app
USER forj
