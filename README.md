# New 



## Docker:

- Development: `docker compose --env-file .\dev.env -f .\compose.yml -f .\compose.dev.yml up --build -d`
- Development(W-Monitor): `docker compose --profile monitor --env-file .\dev.env -f .\compose.yml -f .\compose.dev.yml up --build -d`
- Production: `docker compose --env-file .\.env up --build -d`


### Side notes
What it is: A "build-system + environment specification" that happens to use Docker
Not: A container registry product pipeline
So:
- Compose = deployment manifest
- Dockerfile = deterministic environment builder
- build args = compile-time feature selection
- images = reproducible runtime artifacts, not distributable products

#### Reproducibility
- same dependencies everywhere
- same installed modules everywhere
- no “it works on my machine”

#### Deterministic feature composition
- AERA exists or it does not exist
- DBTOOL exists or it does not exist
- no runtime ambiguity

### DEV:

#### Makemigrations:

- In order for makemigrations to apply to modular_apps, edit the dev.env file and use the [Script](scripts\dev_migrate.py):
    `uv run python .\scripts\dev_migrate.py`
    * All enabled modular apps should be installed in the environment so they can be loaded:
        `uv pip install -e .\src\modular_apps\AERA\ -e .\src\modular_apps\BIFROST\ -e .\src\modular_apps\DBTOOL\ -e .\src\modular_apps\MIMIR\ -e .\src\modular_apps\MXR\ -e .\src\modular_apps\NETTOOLS\ -e .\src\modular_apps\Pymap\`

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