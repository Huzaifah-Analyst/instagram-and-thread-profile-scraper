"""Tests for the SQLite run history (TSK-303)."""

import sqlite3
from datetime import datetime
from pathlib import Path

from src.core.history_db import HistoryDB

RECORDS = [
    {"username": "elif", "composite_status": "ACTIVE", "ig_country": "Türkiye", "ig_date_joined": "Eylül 2019",
     "threads_country": None, "threads_date_joined": None, "threads_badge": None, "error_message": None,
     "seconds": 7.0},
    {"username": "bad", "composite_status": "BANNED", "error_message": "x"},
    {"username": "ghost", "composite_status": "NOT_FOUND"},
]
WHEN = datetime(2026, 10, 4, 19, 30, 0)


def test_creates_schema_from_architecture_doc(tmp_path: Path) -> None:
    path = tmp_path / "sub" / "history.db"
    HistoryDB(path)
    assert path.exists()
    conn = sqlite3.connect(path)
    runs_cols = [r[1] for r in conn.execute("PRAGMA table_info(runs)")]
    item_cols = [r[1] for r in conn.execute("PRAGMA table_info(run_items)")]
    conn.close()
    assert runs_cols == ["run_id", "created_at", "mode", "total_accounts", "active_count",
                         "banned_count", "duration_seconds"]
    assert item_cols == ["id", "run_id", "username", "composite_status", "ig_country", "ig_date_joined",
                         "threads_country", "threads_date_joined", "threads_badge", "error_message"]


def test_save_and_read_back(tmp_path: Path) -> None:
    db = HistoryDB(tmp_path / "history.db")
    run_id = db.save_run(RECORDS, "combined", total_accounts=5, duration_seconds=31.456, created_at=WHEN)
    assert run_id == "RUN_20261004_193000"

    [run] = db.list_runs()
    assert run == {"run_id": run_id, "created_at": "2026-10-04 19:30:00", "mode": "combined",
                   "total_accounts": 5, "active_count": 1, "banned_count": 1, "duration_seconds": 31.46}

    items = db.get_run_items(run_id)
    assert [i["username"] for i in items] == ["elif", "bad", "ghost"]  # original order kept
    assert items[0]["ig_country"] == "Türkiye"
    assert items[1]["error_message"] == "x"
    assert "seconds" not in items[0]  # not part of the schema


def test_reopening_keeps_data(tmp_path: Path) -> None:
    path = tmp_path / "history.db"
    HistoryDB(path).save_run(RECORDS, "ig_only", 3, 10.0, created_at=WHEN)
    assert len(HistoryDB(path).list_runs()) == 1


def test_same_second_runs_get_unique_ids_and_newest_first(tmp_path: Path) -> None:
    db = HistoryDB(tmp_path / "history.db")
    first = db.save_run(RECORDS[:1], "combined", 1, 1.0, created_at=WHEN)
    second = db.save_run(RECORDS[:2], "combined", 2, 1.0, created_at=WHEN)
    later = db.save_run(RECORDS, "threads_only", 3, 1.0, created_at=datetime(2026, 10, 5, 8, 0, 0))
    assert second == first + "_2"
    assert [r["run_id"] for r in db.list_runs()] == [later, second, first]
    assert len(db.get_run_items(second)) == 2


def test_unknown_run_has_no_items(tmp_path: Path) -> None:
    assert HistoryDB(tmp_path / "history.db").get_run_items("RUN_missing") == []
