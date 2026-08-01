# Task API

A to-do list API with full CRUD, built for **FlyRank Internship — Backend Track**.

- **A1** (Week 2): in-memory Python list, gone on every restart.
- **A2** (Week 3): swapped the list for SQLite (`tasks.db`), but storage code lived
  directly inside the FastAPI routes — no repository, no `.env`, no Docker.
- **A3** (this version): Postgres running in Docker, `docker compose up` for the
  whole stack, and a real repository layer so the routes don't know or care
  which database is behind them.

## Honesty note on A2's layering

The assignment brief for A3 assumes A2 already had a repository interface
sitting behind an in-memory store, ready to be swapped for Postgres. **A2
actually didn't have that seam** — `main.py` called `sqlite3` directly inside
every route handler. So step 4 of this assignment ("write a Postgres
repository implementing the same interface as your in-memory one, and swap it
in") required creating that interface for the first time, not just adding a
second implementation of an existing one.

What I did:

- `repository.py` — defines the abstract `TaskRepository` interface (`list`,
  `get`, `create`, `update`, `delete`, `stats`, `reset`, `init`), plus
  `SQLiteTaskRepository`, which is A2's exact old logic moved out of
  `main.py` and made to conform to that interface.
- `postgres_repository.py` — `PostgresTaskRepository`, a second
  implementation of the same interface, using `psycopg2`.
- `main.py` — routes now call `repo.<method>()` only. They contain **zero**
  SQL and **zero** knowledge of which database is running. Which
  implementation `repo` points to is decided once, at startup, from
  `DB_BACKEND` in `.env`.

So the proof the assignment is after — "switching storage changes only one
file" — is true starting now, even though it wasn't true yet in A2.
`postgres_repository.py` is the one new file; `main.py`'s route bodies are
identical regardless of backend.

## Architecture

```
main.py                  → FastAPI routes, call repo.* only
repository.py             → TaskRepository interface + SQLiteTaskRepository
postgres_repository.py    → PostgresTaskRepository (same interface)
init.sql                  → creates the tasks table + seeds it, runs once
                             when the Postgres volume is first created
docker-compose.yml         → postgres (+redis) + app, one command
Dockerfile                 → builds the app image
.env.example / .env        → DB_BACKEND, DATABASE_URL, Postgres credentials
```

## How to run it

### Full stack (Postgres in Docker) — the A3 way

```bash
cp .env.example .env      # already has working defaults for compose
docker compose up
```

This starts Postgres (with a named volume `pgdata` so data survives
restarts), Redis, and the app, and runs `init.sql` the first time the
Postgres volume is created. The API is at `http://localhost:8000`, docs at
`http://localhost:8000/docs`. Postgres is also published on `localhost:5432`
if you want to `psql` in directly.

### App only, against local SQLite (the A2 way, no Docker needed)

```bash
pip install -r requirements.txt
DB_BACKEND=sqlite python3 -m uvicorn main:app --reload
```

## Endpoints

| Method | Path              | Description                                                  |
|--------|-------------------|----------------------------------------------------------------|
| GET    | `/`               | API info, including which backend (`sqlite`/`postgres`) is live |
| GET    | `/health`         | Health check                                                  |
| GET    | `/redis-health`   | Stretch: pings Redis via `REDIS_URL`                           |
| GET    | `/tasks`          | List tasks (`?done=`, `?search=` filters)                      |
| GET    | `/tasks/{id}`     | Get one task (404 if missing)                                  |
| POST   | `/tasks`          | Create a task — requires non-empty `title` (400 if missing)    |
| PUT    | `/tasks/{id}`     | Update `title` and/or `done`                                   |
| DELETE | `/tasks/{id}`     | Delete a task (204)                                             |
| GET    | `/stats`          | `{"total", "done", "open"}`                                    |
| POST   | `/reset`          | Restores the 3 seed tasks                                      |

Status codes and error shape (`{"error": "..."}`) are unchanged from A2.

## Proving persistence

Checked with the app running against the Dockerized Postgres:

1. `docker compose up -d`
2. `curl -X POST http://localhost:8000/tasks -d '{"title":"survive me"}' -H 'Content-Type: application/json'`
3. `docker compose restart app db` — both containers restart
4. `curl http://localhost:8000/tasks` → `"survive me"` is still there

I validated the same logic outside Docker too, using a local Postgres
install: created a row through the API, killed the Python process entirely
(simulating an app restart), and confirmed with `psql` that the row was
still in the table. Then restarted the Postgres server itself and confirmed
the row survived that too — because the data lives in Postgres's own
storage (the `pgdata` volume in Docker), not in the app process.

Compare with `DB_BACKEND=sqlite` and no volume mounted for `tasks.db`: kill
the container and the file — and the rows — go with it. That contrast is
the actual point of this assignment.

## .env / secrets

`.env` is gitignored; `.env.example` (committed) documents every variable:
`DB_BACKEND`, `SQLITE_DB_FILE`, `DATABASE_URL`, and the three
`POSTGRES_*` values the `db` service reads. `docker-compose.yml` overrides
`DATABASE_URL` inside the `app` container to point at `db:5432` (the
compose service name) rather than `localhost`, since containers don't share
`localhost` with the host.

## Stretch: Redis

`redis` is in `docker-compose.yml` alongside `db`, and `GET /redis-health`
pings it via `REDIS_URL` (`redis://redis:6379/0` inside compose). Wired up
now so W4 can build on it directly.

*Not done*: the second stretch (add an index + before/after `EXPLAIN
ANALYZE` on a seeded table) — ran out of time budget for this pass, noting
it honestly rather than faking numbers.
