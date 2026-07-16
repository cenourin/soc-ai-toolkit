import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from app.config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    log_line TEXT NOT NULL,
    classification TEXT NOT NULL,
    summary TEXT NOT NULL,
    suggested_action TEXT NOT NULL,
    engine TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""


def init_db(db_path: str | None = None) -> None:
    path = db_path or settings.db_path
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute(_SCHEMA)


@contextmanager
def get_connection(db_path: str | None = None):
    path = db_path or settings.db_path
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def insert_event(
    log_line: str,
    classification: str,
    summary: str,
    suggested_action: str,
    engine: str,
    db_path: str | None = None,
) -> dict:
    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """INSERT INTO events (log_line, classification, summary, suggested_action, engine, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (log_line, classification, summary, suggested_action, engine, created_at),
        )
        conn.commit()
        return {
            "id": cursor.lastrowid,
            "log_line": log_line,
            "classification": classification,
            "summary": summary,
            "suggested_action": suggested_action,
            "engine": engine,
            "created_at": created_at,
        }


def list_events(classification: str | None = None, db_path: str | None = None) -> list[dict]:
    query = "SELECT * FROM events"
    params: tuple = ()
    if classification:
        query += " WHERE classification = ?"
        params = (classification,)
    query += " ORDER BY id DESC"
    with get_connection(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def get_event(event_id: int, db_path: str | None = None) -> dict | None:
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        return dict(row) if row else None


def stats(db_path: str | None = None) -> dict:
    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT classification, COUNT(*) as total FROM events GROUP BY classification"
        ).fetchall()
        return {row["classification"]: row["total"] for row in rows}
