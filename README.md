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

## Swagger UI — full CRUD cycle, tested live

All screenshots below are from `http://localhost:8000/docs`, using "Try it out" for every endpoint.

**1. Overview — all endpoints listed:**

![Swagger UI overview](screenshots/swagger-overview.png)

**2. POST /tasks → 201 Created:**

![POST /tasks 201](screenshots/post-tasks-201.png)

**3. GET /tasks → 200, seed data:**

![GET /tasks 200](screenshots/get-tasks-200.png)

**4. GET /tasks/3 → 200, single task:**

![GET /tasks/3 200](screenshots/get-task-by-id-200.png)

**5. PUT /tasks/3 → 200, title updated:**

![PUT /tasks/3 200](screenshots/put-task-200.png)

**6. DELETE /tasks/3 → 204 No Content:**

![DELETE /tasks/3 204](screenshots/delete-task-204.png)

**7. GET /tasks → 200, confirms task 3 is gone:**

![GET /tasks after delete](screenshots/get-tasks-after-delete-200.png)

## The mortality experiment

Tasks are stored in a plain Python list in memory (`tasks = [...]` at the top of `main.py`). To test this, I created and deleted tasks, then restarted the server (`Ctrl+C` and re-ran `uvicorn`), and called `GET /tasks` again:

![Mortality experiment — server restarted, data reset](screenshots/mortality-experiment.png)

After the restart, only the 3 original seed tasks (`Buy milk`, `Write README`, `Learn FastAPI`) came back — every task I'd created or modified during testing was gone. This confirms the list only exists inside the running process's memory; there's no file or database backing it, so nothing survives a restart. This is exactly why Week 3 introduces a real database — to make data outlive the process.

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
