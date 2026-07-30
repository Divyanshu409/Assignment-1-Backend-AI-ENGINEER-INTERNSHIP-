import sqlite3
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

app = FastAPI(
    title="Task API",
    version="2.0",
    description="A to-do list API backed by SQLite, built for FlyRank Internship Week 3, Assignment A2.",
)

DB_FILE = "tasks.db"

SEED_TASKS = [
    ("Buy milk", 0),
    ("Write README", 0),
    ("Learn FastAPI", 1),
]


class TaskCreate(BaseModel):
    title: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


# --- Storage layer: everything below talks to tasks.db. Routes never touch SQL directly. ---

@contextmanager
def get_db():
    """Open a fresh connection per call, always closed afterward."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Create the table if missing, and seed 3 tasks only if the table is empty."""
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if count == 0:
            # Wrapped implicitly in one transaction: all 3 inserts commit together.
            conn.executemany(
                "INSERT INTO tasks (title, done) VALUES (?, ?)", SEED_TASKS
            )
            conn.commit()


def row_to_task(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/", summary="API info", description="Returns basic metadata about this API.")
def root():
    return {
        "name": "Task API",
        "version": "2.0",
        "endpoints": ["/tasks"],
    }


@app.get("/health", summary="Health check", description="Returns ok if the server is alive.")
def health():
    return {"status": "ok"}


@app.get(
    "/tasks",
    summary="List tasks",
    description="Returns all tasks. Supports optional filtering by `done` and `search` query params.",
)
def list_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if done is not None:
        query += " AND done = ?"
        params.append(1 if done else 0)
    if search:
        query += " AND title LIKE ?"
        params.append(f"%{search}%")
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [row_to_task(r) for r in rows]


@app.get("/stats", summary="Task stats", description="Returns counts of total, done, and open tasks.")
def stats():
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        done_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE done = 1").fetchone()[0]
    return {"total": total, "done": done_count, "open": total - done_count}


@app.post("/reset", summary="Reset tasks", description="Wipes and restores the 3 example tasks. Handy for demos.")
def reset_tasks():
    with get_db() as conn:
        conn.execute("DELETE FROM tasks")
        conn.executemany("INSERT INTO tasks (title, done) VALUES (?, ?)", SEED_TASKS)
        conn.commit()
        rows = conn.execute("SELECT * FROM tasks").fetchall()
    return [row_to_task(r) for r in rows]


@app.get(
    "/tasks/{task_id}",
    summary="Get one task",
    description="Returns a single task by id, or 404 if it doesn't exist.",
)
def get_task(task_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return row_to_task(row)


@app.post(
    "/tasks",
    status_code=201,
    summary="Create a task",
    description="Creates a new task. Requires a non-empty 'title'.",
)
def create_task(payload: TaskCreate):
    if not payload.title or not payload.title.strip():
        raise HTTPException(status_code=400, detail="'title' is required and cannot be empty")

    title = payload.title.strip()
    with get_db() as conn:
        cur = conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (title, 0))
        conn.commit()
        new_id = cur.lastrowid
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (new_id,)).fetchone()
    return row_to_task(row)


@app.put(
    "/tasks/{task_id}",
    summary="Update a task",
    description="Replaces a task's title and/or done status.",
)
def update_task(task_id: int, payload: TaskUpdate):
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        if payload.title is None and payload.done is None:
            raise HTTPException(status_code=400, detail="Provide at least 'title' or 'done' to update")
        if payload.title is not None and not payload.title.strip():
            raise HTTPException(status_code=400, detail="'title' cannot be empty")

        new_title = payload.title.strip() if payload.title is not None else existing["title"]
        new_done = int(payload.done) if payload.done is not None else existing["done"]

        conn.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (new_title, new_done, task_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return row_to_task(row)


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    summary="Delete a task",
    description="Removes a task by id.",
)
def delete_task(task_id: int):
    with get_db() as conn:
        existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    return None
