
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
1. Auto-generate documentation for Tasks using [Sphinx](https://docs.celeryq.dev/en/stable/userguide/sphinx.html)
2. If you have a combination of long- and short-running tasks, the best option is to use two worker nodes that are configured separately, and route the tasks according to the run-time (see [Routing Tasks](https://docs.celeryq.dev/en/stable/userguide/routing.html#guide-routing)).

3. Better alternative: use a separate settings/ module

A more “Django-standard” way would be:

project/
├─ settings/
│  ├─ __init__.py
│  ├─ base.py      # defaults
│  ├─ dev.py       # loads dev.json
│  ├─ prod.py      # loads prod.json

Then in __init__.py:
```python
import os

env = os.environ.get("DJANGO_ENV", "dev")
if env == "prod":
    from .prod import *
else:
    from .dev import *
```

Each file (dev.py or prod.py) only loads its JSON once, and you avoid repeatedly hitting the disk in weird import chains.
Makes it explicit which environment is active.
**Key Points About Your Current Approach**
Loading JSON directly in settings.py on import will always run every time Django imports the settings module, which can happen multiple times in manage.py commands, wsgi.py, or even tests.
Disk I/O is minimal but unnecessary; also, if your JSON loading logic is more complex, it can cause subtle bugs (e.g., database connections defined before JSON is loaded).
Using environment variables or modular settings is generally more idiomatic and avoids this repetition.