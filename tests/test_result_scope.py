"""Independent status cells, selected columns and truthful field dispatch."""

import asyncio
from copy import deepcopy
from unittest.mock import AsyncMock

import pytest

from src.core.check_plan import CHECK_NAMES
from src.core.scraper import MultiWorkerScraper
from src.gui.components.data_table import COLUMNS, record_to_row
from src.gui.result_scope import platform_status_cell, visible_columns


@pytest.mark.parametrize("status,label", [
    ("active", "ACTIVE"), ("private", "PRIVATE"),
    ("not_found", "NOT FOUND"), ("suspended", "SUSPENDED"),
    ("session_blocked", "CHECKER BLOCKED"), ("error", "CHECK FAILED"),
    ("unknown", "UNKNOWN"), (None, "UNKNOWN"),
    ("skipped", "Not checked"),
    ("skipped_ig_sufficient", "Skipped (IG country)"),
])
def test_threads_status_never_inherits_ig_active(
    status: str | None, label: str,
) -> None:
    """An overall Active result cannot fabricate Threads Alive."""
    record = {
        "composite_status": "ACTIVE", "ig_status": "active",
        "threads_status": status,
        "requested_checks": ["ig_alive", "threads_alive"],
    }
    original = deepcopy(record)
    row = dict(zip((c[0] for c in COLUMNS), record_to_row(1, record)))
    assert row["ig_status"] == "ACTIVE"
    assert row["threads_status"] == label
    assert record == original


@pytest.mark.parametrize("check,column", [
    ("ig_alive", "ig_status"), ("threads_alive", "threads_status"),
    ("ig_country", "ig_country"), ("threads_country", "threads_country"),
    ("ig_age", "ig_joined"), ("threads_age", "threads_joined"),
])
def test_every_checkbox_has_its_own_result_column(
    check: str, column: str,
) -> None:
    """A single check shows its result without irrelevant platform columns."""
    assert visible_columns((check,)) == (
        "idx", "username", column, "quality", "duration", "error",
    )
    assert column in visible_columns(CHECK_NAMES)


@pytest.mark.parametrize("ig,threads", [
    ("active", "not_found"), ("not_found", "active"),
    ("suspended", "active"), ("private", "error"),
])
def test_selected_alive_preserves_independent_observations(
    monkeypatch: pytest.MonkeyPatch, ig: str, threads: str,
) -> None:
    """Selected checks retain raw statuses even when legacy linking differs."""
    async def read(
        page: object, username: str, platform: str, timeout: float,
    ) -> dict:
        """Return independent public observations without linked statuses."""
        status = ig if platform == "ig" else threads
        return {
            "status": status, "stage": "status_only",
            "error": "Unreadable profile" if status == "error" else None,
        }
    monkeypatch.setattr("src.core.alive_records.read_public", read)
    scraper = MultiWorkerScraper(checks=("ig_alive", "threads_alive"))
    record = asyncio.run(scraper._check_account(object(), "fixture"))
    assert record["ig_status"] == ig
    assert record["threads_status"] == threads
    assert record["ig_country"] is record["threads_country"] is None
    if threads == "error":
        assert record["error_message"]
        assert record["data_quality"] != "Complete"


def test_excluded_platform_never_claims_alive() -> None:
    """Defensive rendering respects the stored request scope."""
    assert platform_status_cell({
        "requested_checks": ["ig_country"], "threads_status": "active",
    }, "threads") == "Not checked"
