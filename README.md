
### Docker:
- Development: `docker compose --env-file .\dev.env -f .\compose.yml -f .\compose.dev.yml up --build -d`
- Production: `docker compose up --build -d`

### DEV:

#### TODO:
- Auto-generate documentation for Tasks using [Sphinx](https://docs.celeryq.dev/en/stable/userguide/sphinx.html)
- If you have a combination of long- and short-running tasks, the best option is to use two worker nodes that are configured separately, and route the tasks according to the run-time (see [Routing Tasks](https://docs.celeryq.dev/en/stable/userguide/routing.html#guide-routing)).