# Task API

A small in-memory to-do list API built for **FlyRank Internship — Backend Track, Week 2, Assignment A1**.

Manages tasks with full CRUD (Create, Read, Update, Delete), built with **Python + FastAPI**. Data lives in memory only — it resets whenever the server restarts (see "The mortality experiment" below).

## How to run it

Requires Python 3.10+.

```bash
pip install -r requirements.txt
python3 -m uvicorn main:app --reload
```

The server starts on `http://localhost:8000`. Interactive docs (Swagger UI) are available at `http://localhost:8000/docs`.

## Endpoints

| Method | Path            | Description                              |
|--------|-----------------|-------------------------------------------|
| GET    | `/`             | API info (name, version, endpoints)       |
| GET    | `/health`       | Health check — `{"status": "ok"}`         |
| GET    | `/tasks`        | List all tasks (supports `?done=` and `?search=` filters) |
| GET    | `/tasks/{id}`   | Get a single task by id (404 if missing)  |
| POST   | `/tasks`        | Create a task — requires non-empty `title` (400 if missing) |
| PUT    | `/tasks/{id}`   | Update a task's `title` and/or `done`     |
| DELETE | `/tasks/{id}`   | Delete a task (204 on success)            |
| GET    | `/stats`        | Task counts — `{"total", "done", "open"}` |
| POST   | `/reset`        | Restores the 3 example seed tasks         |

Status codes used: `200` reads, `201` create, `204` delete, `400` invalid body, `404` unknown id — each error returns `{"error": "..."}`.

## Example request

```
$ curl -i -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title":"Buy milk"}'

HTTP/1.1 201 Created
date: Tue, 28 Jul 2026 18:03:46 GMT
server: uvicorn
content-length: 40
content-type: application/json

{"id":4,"title":"Buy milk","done":false}
```

## Screenshots

Checkpoints from building and testing the API (Swagger UI, curl requests, and status codes):

![Screenshot 1](screenshots/Screenshot%202026-07-28%20235346.png)
![Screenshot 2](screenshots/Screenshot%202026-07-28%20235816.png)
![Screenshot 3](screenshots/Screenshot%202026-07-29%20000301.png)
![Screenshot 4](screenshots/Screenshot%202026-07-29%20000457.png)
![Screenshot 5](screenshots/Screenshot%202026-07-29%20000609.png)
![Screenshot 6](screenshots/Screenshot%202026-07-29%20000654.png)
![Screenshot 7](screenshots/Screenshot%202026-07-29%20000713.png)
![Screenshot 8](screenshots/Screenshot%202026-07-29%20000954.png)

## The mortality experiment

Tasks are stored in a plain Python list in memory (`tasks = [...]` at the top of `main.py`). If you create new tasks and then restart the server (`Ctrl+C` and re-run `uvicorn`), every task you added is gone — only the 3 hardcoded seed tasks come back. This happens because the list only exists inside the running process's memory; there's no file or database backing it, so nothing survives a restart. This is exactly why Week 3 introduces a real database — to make data outlive the process.

## Extras built

- Filtering: `GET /tasks?done=true`
- Search: `GET /tasks?search=milk`
- Stats endpoint: `GET /stats`
- Seed & reset: `POST /reset`

## Stage 7 — AI rematch

See [`ai-version/AI_VS_ME.md`](ai-version/AI_VS_ME.md) for the full writeup: the prompt I gave
an AI assistant, what it got right, two real bugs I found by running my Stage 4 checkpoint curls
against its output (wrong status code on invalid input, whitespace-only titles slipping through),
and the improved prompt + rematch that fixed both.

---

# Assignment 2

**FlyRank Internship — Backend Track, Week 3, Assignment A2: Connecting your CRUD to the database.**

This is the direct sequel to Assignment 1 above, in the same repo. Same API, same endpoints, same
request/response shapes — the only thing that changed is where the data lives.

## Why SQLite

SQLite was the right fit here because it's a single file (`tasks.db`) with no server to install, run,
or configure — opening the file *is* creating the database. That's exactly what a small CRUD API
needs: enough persistence to survive a restart, with zero setup overhead. A bigger, multi-user
production app would eventually reach for something like Postgres, but for this project SQLite gives
real, on-disk persistence with none of that extra weight.

## Where the database lives

- The database file is `tasks.db`, created automatically the first time the app runs.
- It's listed in `.gitignore`, so it's never committed — every fresh clone starts with a clean file
  and gets re-seeded with the 3 example tasks on first run.
- The `tasks` table (`id`, `title`, `done`) is also created automatically if it doesn't exist yet.

## Run it

```bash
pip install -r requirements.txt
python3 -m uvicorn main:app --reload
```

That's the same one command as Assignment 1 — no extra install step, since `sqlite3` ships with
Python. On first run this creates `tasks.db`, creates the `tasks` table, and seeds it with 3 example
tasks (only when the table is empty, so restarting never duplicates them).

## What changed vs. Assignment 1

All five CRUD endpoints (`GET /tasks`, `GET /tasks/{id}`, `POST /tasks`, `PUT /tasks/{id}`,
`DELETE /tasks/{id}`) keep the exact same behavior, status codes (`200`/`201`/`204`/`400`/`404`), and
JSON shapes as Assignment 1. Only the storage layer changed:

- `GET` endpoints now run `SELECT` queries instead of reading from a Python list.
- `POST` runs `INSERT INTO tasks (title, done) VALUES (?, ?)` and lets SQLite assign the `id`.
- `PUT` runs `UPDATE tasks SET title = ?, done = ? WHERE id = ?`.
- `DELETE` runs `DELETE FROM tasks WHERE id = ?`.
- Every query uses `?` parameterized placeholders — no user input is ever glued into a SQL string.

## Proof: data survives a restart

```
$ curl -i http://localhost:8000/tasks
[{"id":1,"title":"Buy milk","done":false},
 {"id":2,"title":"Write README","done":false},
 {"id":3,"title":"Learn FastAPI","done":true}]
```

Create a task, restart the server, and it's still there — the first time this project's data has
outlived the process. That's the whole point of Assignment 2.

## Exploring the database by hand (Stage 4)

Opened `tasks.db` directly in **DB Browser for SQLite** and ran queries against it while the API was
still running — same file, no syncing needed, changes show up instantly through the API too.

**`SELECT * FROM tasks;`** — lists every row:

![SELECT * FROM tasks](screenshots/Screenshot%202026-07-30%20150329.png)

**`SELECT COUNT(*) FROM tasks;`** — returned `3`, confirming the table only ever holds the seeded
tasks until new ones are created:

![SELECT COUNT(*) FROM tasks](screenshots/Screenshot%202026-07-30%20150413.png)

**`UPDATE tasks SET done = 1;`** — marks every task complete directly in the database, no code
involved:

![UPDATE tasks SET done = 1](screenshots/Screenshot%202026-07-30%20150449.png)

**Browse Data**, after the update above — all 3 tasks now show `done = 1`:

![Browse Data after update](screenshots/Screenshot%202026-07-30%20150651.png)

**Confirming the API reads the same file** — no server restart needed, the API always reflects
whatever is currently in `tasks.db`:

![curl showing the live API](screenshots/Screenshot%202026-07-30%20150953.png)

## AI vs me (Stage 6)

See [`ai-version/`](ai-version/) for the AI-generated version of this same migration, kept in its own
folder so it never touched the hand-built code above. Prompted an AI assistant to migrate the
in-memory API to SQLite from a spec (table columns, seed-once behavior, identical endpoint behavior,
parameterized queries), then ran the same Stage 2/3 checkpoints against its output and diffed the
storage code against mine to compare.

## Extras built

- Filtering: `GET /tasks?done=true`
- Search: `GET /tasks?search=milk` (using SQL `LIKE`)
- Stats endpoint: `GET /stats`, computed with `SELECT COUNT(*)` in SQL instead of counting in code
- Seed & reset: `POST /reset`, wiping and re-inserting the 3 example tasks in one transaction
