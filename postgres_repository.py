"""
Postgres implementation of TaskRepository.

Same interface as SQLiteTaskRepository (repository.py). main.py swaps
between them based on DB_BACKEND — service and route code never changes.
"""

from contextlib import contextmanager
from typing import Optional, List

import psycopg2
import psycopg2.extras

from repository import TaskRepository, SEED_TASKS


class PostgresTaskRepository(TaskRepository):
    def __init__(self, dsn: str):
        self.dsn = dsn

    @contextmanager
    def _conn(self):
        conn = psycopg2.connect(self.dsn, cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield conn
        finally:
            conn.close()

    def init(self) -> None:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        done BOOLEAN NOT NULL DEFAULT FALSE
                    )
                    """
                )
                cur.execute("SELECT COUNT(*) AS c FROM tasks")
                count = cur.fetchone()["c"]
                if count == 0:
                    cur.executemany(
                        "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                        [(t, bool(d)) for t, d in SEED_TASKS],
                    )
            conn.commit()

    @staticmethod
    def _row_to_task(row) -> dict:
        return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

    def list(self, done: Optional[bool] = None, search: Optional[str] = None) -> 'List[dict]':
        query = "SELECT * FROM tasks WHERE 1=1"
        params: list = []
        if done is not None:
            query += " AND done = %s"
            params.append(done)
        if search:
            query += " AND title ILIKE %s"
            params.append(f"%{search}%")
        query += " ORDER BY id"
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall()
        return [self._row_to_task(r) for r in rows]

    def get(self, task_id: int) -> Optional[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
                row = cur.fetchone()
        return self._row_to_task(row) if row else None

    def create(self, title: str) -> dict:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *",
                    (title, False),
                )
                row = cur.fetchone()
            conn.commit()
        return self._row_to_task(row)

    def update(self, task_id: int, title: Optional[str], done: Optional[bool]) -> Optional[dict]:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
                existing = cur.fetchone()
                if existing is None:
                    return None
                new_title = title if title is not None else existing["title"]
                new_done = done if done is not None else existing["done"]
                cur.execute(
                    "UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *",
                    (new_title, new_done, task_id),
                )
                row = cur.fetchone()
            conn.commit()
        return self._row_to_task(row)

    def delete(self, task_id: int) -> bool:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM tasks WHERE id = %s", (task_id,))
                if cur.fetchone() is None:
                    return False
                cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            conn.commit()
        return True

    def stats(self) -> dict:
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) AS c FROM tasks")
                total = cur.fetchone()["c"]
                cur.execute("SELECT COUNT(*) AS c FROM tasks WHERE done = TRUE")
                done_count = cur.fetchone()["c"]
        return {"total": total, "done": done_count, "open": total - done_count}

    def reset(self) -> 'List[dict]':
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM tasks")
                cur.executemany(
                    "INSERT INTO tasks (title, done) VALUES (%s, %s)",
                    [(t, bool(d)) for t, d in SEED_TASKS],
                )
                cur.execute("SELECT * FROM tasks ORDER BY id")
                rows = cur.fetchall()
            conn.commit()
        return [self._row_to_task(r) for r in rows]
