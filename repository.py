import sqlite3
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Optional, List


SEED_TASKS = [
    ("Buy milk", 0),
    ("Write README", 0),
    ("Learn FastAPI", 1),
]


class TaskRepository(ABC):

    @abstractmethod
    def init(self) -> None:
       

    @abstractmethod
    def list(self, done: Optional[bool] = None, search: Optional[str] = None) -> 'List[dict]':
        ...

    @abstractmethod
    def get(self, task_id: int) -> Optional[dict]:
        ...

    @abstractmethod
    def create(self, title: str) -> dict:
        ...

    @abstractmethod
    def update(self, task_id: int, title: Optional[str], done: Optional[bool]) -> Optional[dict]:
        

    @abstractmethod
    def delete(self, task_id: int) -> bool:
        

    @abstractmethod
    def stats(self) -> dict:
        ...

    @abstractmethod
    def reset(self) -> 'List[dict]':
        ...


class SQLiteTaskRepository(TaskRepository):
   

    def __init__(self, db_file: str = "tasks.db"):
        self.db_file = db_file

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init(self) -> None:
        with self._conn() as conn:
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
                conn.executemany(
                    "INSERT INTO tasks (title, done) VALUES (?, ?)", SEED_TASKS
                )
                conn.commit()

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> dict:
        return {"id": row["id"], "title": row["title"], "done": bool(row["done"])}

    def list(self, done: Optional[bool] = None, search: Optional[str] = None) -> 'List[dict]':
        query = "SELECT * FROM tasks WHERE 1=1"
        params: list = []
        if done is not None:
            query += " AND done = ?"
            params.append(1 if done else 0)
        if search:
            query += " AND title LIKE ?"
            params.append(f"%{search}%")
        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_task(r) for r in rows]

    def get(self, task_id: int) -> Optional[dict]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return self._row_to_task(row) if row else None

    def create(self, title: str) -> dict:
        with self._conn() as conn:
            cur = conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (title, 0))
            conn.commit()
            new_id = cur.lastrowid
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (new_id,)).fetchone()
        return self._row_to_task(row)

    def update(self, task_id: int, title: Optional[str], done: Optional[bool]) -> Optional[dict]:
        with self._conn() as conn:
            existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if existing is None:
                return None
            new_title = title if title is not None else existing["title"]
            new_done = int(done) if done is not None else existing["done"]
            conn.execute(
                "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
                (new_title, new_done, task_id),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return self._row_to_task(row)

    def delete(self, task_id: int) -> bool:
        with self._conn() as conn:
            existing = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if existing is None:
                return False
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
        return True

    def stats(self) -> dict:
        with self._conn() as conn:
            total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            done_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE done = 1").fetchone()[0]
        return {"total": total, "done": done_count, "open": total - done_count}

    def reset(self) -> 'List[dict]':
        with self._conn() as conn:
            conn.execute("DELETE FROM tasks")
            conn.executemany("INSERT INTO tasks (title, done) VALUES (?, ?)", SEED_TASKS)
            conn.commit()
            rows = conn.execute("SELECT * FROM tasks").fetchall()
        return [self._row_to_task(r) for r in rows]
