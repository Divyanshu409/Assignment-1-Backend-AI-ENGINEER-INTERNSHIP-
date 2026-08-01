# Task API

A to-do list API with full CRUD, built for **FlyRank Internship — Backend Track**.

- **A1** (Week 2): in-memory Python list, gone on every restart.
- **A2** (Week 3): swapped the list for SQLite (`tasks.db`), but storage code lived
  directly inside the FastAPI routes — no repository, no `.env`, no Docker.
- **A3** (this version): Postgres, a real repository layer so the routes don't
  know or care which database is behind them, and a `docker-compose.yml` for
  running the whole stack with one command.

## Honesty note on A2's layering

The A3 brief assumes A2 already had a repository interface sitting behind an
in-memory store, ready to be swapped for Postgres. A2 actually didn't have
that seam — `main.py` called `sqlite3` directly inside every route handler.
So step 4 of this assignment ("write a Postgres repository implementing the
same interface as your in-memory one, and swap it in") required creating
that interface for the first time, not just adding a second implementation
of an existing one.

What I did:

- `repository.py` — the abstract `TaskRepository` interface (`list`, `get`,
  `create`, `update`, `delete`, `stats`, `reset`, `init`), plus
  `SQLiteTaskRepository`, which is A2's exact old logic moved out of
  `main.py` and made to conform to that interface.
- `postgres_repository.py` — `PostgresTaskRepository`, a second
  implementation of the same interface, using `psycopg2`.
- `main.py` — routes now call `repo.<method>()` only. Zero SQL, zero
  knowledge of which database is running. Which implementation `repo`
  points to is decided once, at startup, from `DB_BACKEND` in `.env`.

So the proof the assignment is after — "switching storage changes only one
file" — is true starting now, even though it wasn't true yet in A2.

## Honesty note on how this was tested

Docker Desktop had trouble starting on my machine while building this. To
still verify the Postgres repository and persistence genuinely worked, I:

1. Signed up for a free [Neon](https://neon.tech) Postgres instance and
   pointed `DATABASE_URL` at it, then ran the app directly with
   `uvicorn main:app --reload` (no Docker).
2. Confirmed `GET /` returned `"backend": "postgres"`, confirmed `GET /tasks`
   returned the seeded rows, and confirmed via Neon's own SQL editor
   (`SELECT * FROM tasks;`) that the rows genuinely existed in Postgres.
3. Created a task, fully stopped and restarted the `uvicorn` process, and
   confirmed the task was still there — proving persistence at the
   repository/database level.

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
cp .env.example .env
docker compose up
```

Starts Postgres (with a named volume `pgdata` so data survives restarts),
Redis, and the app. API at `http://localhost:8000`, docs at
`http://localhost:8000/docs`.

### App only, against a cloud Postgres (no Docker)

```bash
pip install -r requirements.txt
```
Set in `.env`:
```
DB_BACKEND=postgres
DATABASE_URL=<your cloud Postgres connection string>
```
```bash
uvicorn main:app --reload
```

### App only, against local SQLite (the A2 way)

Set `DB_BACKEND=sqlite` in `.env`, then:
```bash
pip install -r requirements.txt
uvicorn main:app --reload
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

## Screenshots

### A1 — in-memory version

![A1 screenshot 1](Screenshot%202026-07-28%20235346.png)
![A1 screenshot 2](Screenshot%202026-07-28%20235816.png)
![A1 screenshot 3](Screenshot%202026-07-29%20000301.png)
![A1 screenshot 4](Screenshot%202026-07-29%20000457.png)
![A1 screenshot 5](Screenshot%202026-07-29%20000609.png)
![A1 screenshot 6](Screenshot%202026-07-29%20000654.png)
![A1 screenshot 7](Screenshot%202026-07-29%20000713.png)
![A1 screenshot 8](Screenshot%202026-07-29%20000954.png)

### A2 — SQLite version

![A2 screenshot 1](Screenshot%202026-07-30%20150329.png)
![A2 screenshot 2](Screenshot%202026-07-30%20150413.png)
![A2 screenshot 3](Screenshot%202026-07-30%20150449.png)
![A2 screenshot 4](Screenshot%202026-07-30%20150651.png)
![A2 screenshot 5](Screenshot%202026-07-30%20150953.png)

### A3 — Postgres version (this assignment)

**GET / — confirms `"backend": "postgres"`:**
![GET root backend check](Screenshot%202026-08-01%20152320.png)

**GET /tasks — seed rows returned from Postgres:**
![GET tasks seed proof](Screenshot%202026-08-01%20152907.png)

**Before restart — task created:**
![Before restart](Screenshot%202026-08-01%20153055.png)

**After restart — task still present (persistence proof):**
![After restart](Screenshot%202026-08-01%20153214.png)

> Note: double-check these four A3 captions match what each screenshot
> actually shows, and reorder/relabel if not — they're my best guess based
> on the testing order we walked through, not something I verified myself.

## Proving persistence

Created a task via `POST /tasks` against the Neon Postgres instance, fully
stopped the `uvicorn` process, restarted it, and re-ran `GET /tasks` — the
task was still there, because it lives in Postgres, not in the app process
or local disk. See the "before/after restart" screenshots above.

Compare with `DB_BACKEND=sqlite` and no persistent volume: kill the process
and the file — and the rows — go with it. That contrast is the actual point
of this assignment.

## .env / secrets

`.env` is gitignored; `.env.example` (committed) documents every variable:
`DB_BACKEND`, `SQLITE_DB_FILE`, `DATABASE_URL`, and the three `POSTGRES_*`
values the `db` service reads.

## Stretch: Redis

`redis` is in `docker-compose.yml` alongside `db`, and `GET /redis-health`
pings it via `REDIS_URL`.

