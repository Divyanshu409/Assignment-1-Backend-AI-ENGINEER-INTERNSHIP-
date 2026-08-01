import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from repository import SQLiteTaskRepository

load_dotenv()

app = FastAPI(
    title="Task API",
    version="3.0",
    description="A to-do list API. SQLite for A2, swappable to Postgres for A3 — "
    "same service/routes either way.",
)


class TaskCreate(BaseModel):
    title: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


# --- Repository selection: the ONLY place that knows which backend is running. ---
# Routes below call `repo.*` and never see SQL directly, regardless of backend.

DB_BACKEND = os.getenv("DB_BACKEND", "sqlite")

if DB_BACKEND == "postgres":
    from postgres_repository import PostgresTaskRepository

    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("DB_BACKEND=postgres but DATABASE_URL is not set (check .env)")
    repo = PostgresTaskRepository(DATABASE_URL)
else:
    repo = SQLiteTaskRepository(os.getenv("SQLITE_DB_FILE", "tasks.db"))


@app.on_event("startup")
def on_startup():
    repo.init()


@app.get("/", summary="API info", description="Returns basic metadata about this API.")
def root():
    return {
        "name": "Task API",
        "version": "3.0",
        "backend": DB_BACKEND,
        "endpoints": ["/tasks"],
    }


@app.get("/health", summary="Health check", description="Returns ok if the server is alive.")
def health():
    return {"status": "ok", "backend": DB_BACKEND}


@app.get(
    "/redis-health",
    summary="Redis health check (stretch)",
    description="Pings Redis via REDIS_URL. Returns ok:false if Redis isn't configured or unreachable.",
)
def redis_health():
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return {"ok": False, "detail": "REDIS_URL not set"}
    try:
        import redis

        r = redis.from_url(redis_url, socket_connect_timeout=2)
        r.ping()
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "detail": str(exc)}


@app.get(
    "/tasks",
    summary="List tasks",
    description="Returns all tasks. Supports optional filtering by `done` and `search` query params.",
)
def list_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    return repo.list(done=done, search=search)


@app.get("/stats", summary="Task stats", description="Returns counts of total, done, and open tasks.")
def stats():
    return repo.stats()


@app.post("/reset", summary="Reset tasks", description="Wipes and restores the 3 example tasks. Handy for demos.")
def reset_tasks():
    return repo.reset()


@app.get(
    "/tasks/{task_id}",
    summary="Get one task",
    description="Returns a single task by id, or 404 if it doesn't exist.",
)
def get_task(task_id: int):
    task = repo.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.post(
    "/tasks",
    status_code=201,
    summary="Create a task",
    description="Creates a new task. Requires a non-empty 'title'.",
)
def create_task(payload: TaskCreate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="'title' is required and cannot be empty")
    return repo.create(payload.title.strip())


@app.put(
    "/tasks/{task_id}",
    summary="Update a task",
    description="Replaces a task's title and/or done status.",
)
def update_task(task_id: int, payload: TaskUpdate):
    if payload.title is None and payload.done is None:
        raise HTTPException(status_code=400, detail="Provide at least 'title' or 'done' to update")
    if payload.title is not None and not payload.title.strip():
        raise HTTPException(status_code=400, detail="'title' cannot be empty")

    title = payload.title.strip() if payload.title is not None else None
    task = repo.update(task_id, title=title, done=payload.done)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="Delete a task",
    description="Removes a task by id.",
)
def delete_task(task_id: int):
    if not repo.delete(task_id):
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return None
