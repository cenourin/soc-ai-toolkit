import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from app.config import settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS lookups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    indicator TEXT NOT NULL,
    indicator_type TEXT NOT NULL,
    malicious INTEGER NOT NULL,
    score INTEGER NOT NULL,
    source TEXT NOT NULL,
    categories TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lookup_id INTEGER,
    indicator TEXT NOT NULL,
    channel TEXT NOT NULL,
    message TEXT NOT NULL,
    delivered INTEGER NOT NULL,
    created_at TEXT NOT NULL
);
"""


def init_db(db_path: str | None = None) -> None:
    path = db_path or settings.db_path
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(_SCHEMA)


@contextmanager
def get_connection(db_path: str | None = None):
    path = db_path or settings.db_path
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def _row_to_lookup(row: sqlite3.Row) -> dict:
    data = dict(row)
    data["malicious"] = bool(data["malicious"])
    data["categories"] = json.loads(data["categories"])
    return data


def _row_to_notification(row: sqlite3.Row) -> dict:
    data = dict(row)
    data["delivered"] = bool(data["delivered"])
    return data


def insert_lookup(
    indicator: str,
    indicator_type: str,
    malicious: bool,
    score: int,
    source: str,
    categories: list[str],
    db_path: str | None = None,
) -> dict:
    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """INSERT INTO lookups
               (indicator, indicator_type, malicious, score, source, categories, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (indicator, indicator_type, int(malicious), score, source, json.dumps(categories), created_at),
        )
        conn.commit()
        return {
            "id": cursor.lastrowid,
            "indicator": indicator,
            "indicator_type": indicator_type,
            "malicious": malicious,
            "score": score,
            "source": source,
            "categories": categories,
            "created_at": created_at,
        }


def insert_notification(
    lookup_id: int | None,
    indicator: str,
    channel: str,
    message: str,
    delivered: bool,
    db_path: str | None = None,
) -> dict:
    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.execute(
            """INSERT INTO notifications
               (lookup_id, indicator, channel, message, delivered, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (lookup_id, indicator, channel, message, int(delivered), created_at),
        )
        conn.commit()
        return {
            "id": cursor.lastrowid,
            "lookup_id": lookup_id,
            "indicator": indicator,
            "channel": channel,
            "message": message,
            "delivered": delivered,
            "created_at": created_at,
        }


def list_lookups(malicious: bool | None = None, db_path: str | None = None) -> list[dict]:
    query = "SELECT * FROM lookups"
    params: tuple = ()
    if malicious is not None:
        query += " WHERE malicious = ?"
        params = (int(malicious),)
    query += " ORDER BY id DESC"
    with get_connection(db_path) as conn:
        rows = conn.execute(query, params).fetchall()
        return [_row_to_lookup(row) for row in rows]


def get_lookup(lookup_id: int, db_path: str | None = None) -> dict | None:
    with get_connection(db_path) as conn:
        row = conn.execute("SELECT * FROM lookups WHERE id = ?", (lookup_id,)).fetchone()
        return _row_to_lookup(row) if row else None


def indicator_already_looked_up(indicator: str, db_path: str | None = None) -> bool:
    with get_connection(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM lookups WHERE indicator = ? LIMIT 1", (indicator,)
        ).fetchone()
        return row is not None


def list_notifications(db_path: str | None = None) -> list[dict]:
    with get_connection(db_path) as conn:
        rows = conn.execute("SELECT * FROM notifications ORDER BY id DESC").fetchall()
        return [_row_to_notification(row) for row in rows]
