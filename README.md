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

## Swagger UI

Screenshot of `/docs` with "Try it out" working for the full CRUD cycle:

`[insert screenshot here — screenshots.png]`

*(Note: take this yourself by running the server locally and visiting `/docs` in your browser — screenshot tooling wasn't available in the build environment.)*

## The mortality experiment

Tasks are stored in a plain Python list in memory (`tasks = [...]` at the top of `main.py`). If you create new tasks and then restart the server (`Ctrl+C` and re-run `uvicorn`), every task you added is gone — only the 3 hardcoded seed tasks come back. This happens because the list only exists inside the running process's memory; there's no file or database backing it, so nothing survives a restart. This is exactly why Week 3 introduces a real database — to make data outlive the process.

## Extras built

- Filtering: `GET /tasks?done=true`
- Search: `GET /tasks?search=milk`
- Stats endpoint: `GET /stats`
- Seed & reset: `POST /reset`
