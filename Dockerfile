FROM python:3.13-slim AS builder

SHELL ["/bin/bash", "-eo", "pipefail", "-c"]

ARG DJANGO_ENV

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
    DJANGO_ENV=${DJANGO_ENV}

RUN apt-get update && apt-get install --no-install-recommends -y pipx \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*
    
RUN pipx install poetry 

ENV PATH="/root/.local/bin:$PATH"
ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /app

COPY src/pyproject.toml src/poetry.lock* ./

#RUN poetry install --with dev,local_apps --no-root
RUN poetry install --without local_apps $(if [ "$DJANGO_ENV" = 'development' ]; then echo '--with dev'; fi) --no-root

#COPY . .

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
    STATIC_ROOT=${STATIC_ROOT}


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

WORKDIR /home/arka/app

COPY --from=builder /app/.venv /home/arka/app/.venv
ENV PATH="/home/arka/app/.venv/bin:$PATH"

COPY scripts/django_init.sh /home/arka/app/init.sh
COPY scripts/copy_secrets.sh /home/arka/copy_secrets.sh
COPY src/ .

# fix perms
USER root
RUN chown -R arka:$GROUPNAME /home/arka/app
USER arka

EXPOSE 8000
# CMD [ "/home/arka/app/.venv/bin/python", "manage.py", "runserver", "0.0.0.0:8000"]
# CMD ["tail", "-f", "/dev/null"]
# ENTRYPOINT [ "/home/arka/app/init.sh" ]

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
    STATIC_ROOT=${STATIC_ROOT}


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

WORKDIR /home/forj/app

COPY --from=builder /app/.venv /home/forj/app/.venv
ENV PATH="/home/forj/app/.venv/bin:$PATH"

COPY scripts/celery_init.sh /home/forj/app/init.sh
COPY scripts/copy_secrets.sh /home/forj/app/copy_secrets.sh
COPY src/ .

# fix perms
USER root
RUN chown -R forj:$GROUPNAME /home/forj/app
USER forj
