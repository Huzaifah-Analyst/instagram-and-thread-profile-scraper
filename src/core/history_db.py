"""SQLite run history (TSK-303).

Schema follows ``docs/architecture.md`` §5 exactly (``runs`` + ``run_items``).
Tables are created on first use, so a fresh install needs no migration step.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    created_at DATETIME,
    mode TEXT,
    total_accounts INTEGER,
    active_count INTEGER,
    banned_count INTEGER,
    duration_seconds REAL
);
CREATE TABLE IF NOT EXISTS run_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT REFERENCES runs(run_id) ON DELETE CASCADE,
    username TEXT,
    composite_status TEXT,
    ig_country TEXT,
    ig_date_joined TEXT,
    threads_country TEXT,
    threads_date_joined TEXT,
    threads_badge TEXT,
    error_message TEXT
);
CREATE INDEX IF NOT EXISTS idx_run_items_run_id ON run_items(run_id);
"""

ITEM_FIELDS = (
    "username", "composite_status", "ig_country", "ig_date_joined",
    "threads_country", "threads_date_joined", "threads_badge", "error_message",
)
RUN_FIELDS = ("run_id", "created_at", "mode", "total_accounts", "active_count", "banned_count", "duration_seconds")


class HistoryDB:
    """Stores finished runs and their per-account records."""

    def __init__(self, path: Union[str, Path]) -> None:
        """Opens (and if needed creates) the database at ``path``."""
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as conn, conn:
            conn.executescript(SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        """Opens a short-lived connection; one per operation keeps threads safe."""
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def save_run(
        self,
        records: list[dict],
        mode: str,
        total_accounts: int,
        duration_seconds: float,
        created_at: Optional[datetime] = None,
    ) -> str:
        """Persists one run and all its records in a single transaction.

        Args:
            records: Records that were processed (may be fewer than submitted
                when the run was stopped).
            mode: ``ig_only``, ``threads_only`` or ``combined``.
            total_accounts: Number of usernames submitted.
            duration_seconds: Wall-clock run time.
            created_at: Run start time (defaults to now).

        Returns:
            The new ``run_id`` (``RUN_YYYYMMDD_HHMMSS``, suffixed if taken).
        """
        created = (created_at or datetime.now()).replace(microsecond=0)
        active = sum(1 for r in records if r.get("composite_status") == "ACTIVE")
        banned = sum(1 for r in records if r.get("composite_status") == "BANNED")
        with closing(self._connect()) as conn, conn:
            run_id = self._unique_run_id(conn, created)
            conn.execute(
                f"INSERT INTO runs ({', '.join(RUN_FIELDS)}) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (run_id, created.isoformat(sep=" "), mode, total_accounts, active, banned,
                 round(duration_seconds, 2)),
            )
            conn.executemany(
                f"INSERT INTO run_items (run_id, {', '.join(ITEM_FIELDS)}) VALUES ({', '.join('?' * 9)})",
                [(run_id, *(r.get(f) for f in ITEM_FIELDS)) for r in records],
            )
        return run_id

    @staticmethod
    def _unique_run_id(conn: sqlite3.Connection, created: datetime) -> str:
        """Builds ``RUN_<timestamp>``, adding ``_2``, ``_3``... on collision."""
        base = created.strftime("RUN_%Y%m%d_%H%M%S")
        run_id, n = base, 1
        while conn.execute("SELECT 1 FROM runs WHERE run_id = ?", (run_id,)).fetchone():
            n += 1
            run_id = f"{base}_{n}"
        return run_id

    def list_runs(self, limit: int = 500) -> list[dict]:
        """Returns run summaries, newest first."""
        with closing(self._connect()) as conn:
            rows = conn.execute(
                f"SELECT {', '.join(RUN_FIELDS)} FROM runs ORDER BY created_at DESC, run_id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def get_run_items(self, run_id: str) -> list[dict]:
        """Returns a run's records in their original order (``build_record()`` keys)."""
        with closing(self._connect()) as conn:
            rows = conn.execute(
                f"SELECT {', '.join(ITEM_FIELDS)} FROM run_items WHERE run_id = ? ORDER BY id",
                (run_id,),
            ).fetchall()
        return [dict(row) for row in rows]
