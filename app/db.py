from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from app.config import SETTINGS

_DB_LOCK = threading.Lock()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def init_db() -> None:
    _ensure_parent(SETTINGS.db_path)
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                interval_seconds INTEGER NOT NULL,
                mode TEXT NOT NULL,
                webhook_url TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                status TEXT NOT NULL,
                risk_level TEXT,
                flags TEXT,
                evidence TEXT,
                raw_hash TEXT,
                risk_at TEXT,
                error TEXT,
                FOREIGN KEY(job_id) REFERENCES jobs(id)
            );

            CREATE TABLE IF NOT EXISTS job_state (
                job_id TEXT PRIMARY KEY,
                last_hash TEXT,
                last_risk_level TEXT,
                last_flags TEXT,
                last_evidence TEXT,
                last_risk_at TEXT,
                last_notified_at TEXT,
                FOREIGN KEY(job_id) REFERENCES jobs(id)
            );
            """
        )
        _ensure_column(conn, "runs", "risk_at", "TEXT")
        _ensure_column(conn, "job_state", "last_risk_level", "TEXT")
        _ensure_column(conn, "job_state", "last_flags", "TEXT")
        _ensure_column(conn, "job_state", "last_evidence", "TEXT")
        _ensure_column(conn, "job_state", "last_risk_at", "TEXT")


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(SETTINGS.db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, col_type: str) -> None:
    cur = conn.execute(f"PRAGMA table_info({table})")
    columns = {row[1] for row in cur.fetchall()}
    if column not in columns:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")


@contextmanager
def db_cursor() -> Iterable[sqlite3.Cursor]:
    with _DB_LOCK:
        conn = _connect()
        try:
            yield conn.cursor()
            conn.commit()
        finally:
            conn.close()


def fetch_one(query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
    with db_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchone()


def fetch_all(query: str, params: tuple = ()) -> list[sqlite3.Row]:
    with db_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def execute(query: str, params: tuple = ()) -> None:
    with db_cursor() as cur:
        cur.execute(query, params)


def insert_json(value: Any) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def parse_json(value: Optional[str]) -> Any:
    if not value:
        return None
    return json.loads(value)
