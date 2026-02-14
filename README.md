
### Docker:
- Development: `docker compose --env-file .\dev.env -f .\compose.yml -f .\compose.dev.yml up --build -d`
- Development(W-Monitor): `docker compose --profile monitor --env-file .\dev.env -f .\compose.yml -f .\compose.dev.yml up --build -d --force-recreate`
- Production: `docker compose up --build -d`

### DEV:

#### Makemigrations:

- In order for makemigrations to work a few environment variables must be set():
    `$env:PYTHONPATH=".;modular_apps/Pymap"; $env:DJANGO_ENV="development"; poetry run python manage.py makemigrations pymap`
- After updating the branches on the modular apps the lock file needs to be synced:
    `poetry lock`

**Management commands should always be executed in the src directory**


#### TODO:
- Auto-generate documentation for Tasks using [Sphinx](https://docs.celeryq.dev/en/stable/userguide/sphinx.html)
- If you have a combination of long- and short-running tasks, the best option is to use two worker nodes that are configured separately, and route the tasks according to the run-time (see [Routing Tasks](https://docs.celeryq.dev/en/stable/userguide/routing.html#guide-routing)).