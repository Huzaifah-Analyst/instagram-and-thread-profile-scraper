"""Regression coverage for requested completeness and clean error channels."""

import asyncio
import csv
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from playwright.async_api import Error as PlaywrightError

from src.core.anonymous_status import check_status, status_record
from src.core.export import export_csv
from src.core.result_records import build_record
from src.gui.components.data_table import record_to_row

IG_FULL = {"status": "active", "country": "Canada", "date_joined": "April 2016"}
SKIPPED = {"status": "skipped_ig_sufficient", "stage": "skipped"}


@pytest.mark.parametrize("mode,threads,quality", [
    ("combined_smart", SKIPPED, "Complete"),
    ("combined", SKIPPED, "Partial"),
    ("combined", {"status": None}, "Partial"),
    ("combined", IG_FULL, "Complete"),
    ("combined", {"status": "active"}, "Partial"),
    ("combined_smart", {"status": "active"}, "Partial"),
    ("combined_smart", {"status": None}, "Partial"),
    ("combined_smart", {**IG_FULL, "error": "Read failed"}, "Partial"),
])
def test_completeness_respects_requested_platforms(mode: str, threads: dict, quality: str) -> None:
    """Only the deliberate Smart skip removes a required platform."""
    result = build_record("fixture", IG_FULL, threads, .5, mode)
    assert result["data_quality"] == quality


@pytest.mark.parametrize("country", [None, "Not shared"])
def test_smart_fallback_without_threads_data_is_incomplete(country: str | None) -> None:
    """No country from either requested source must not become Complete."""
    ig = {**IG_FULL, "country": country}
    result = build_record("fixture", ig, {"status": "active"}, .5, "combined_smart")
    assert result["data_quality"] == "Partial"


def test_smart_skip_preserves_real_ig_error_and_missing_joined() -> None:
    """Skipping a platform does not erase failures or incomplete IG metadata."""
    for ig in ({**IG_FULL, "date_joined": None}, {**IG_FULL, "error": "IG read failed"}):
        result = build_record("fixture", ig, SKIPPED, .5, "combined_smart")
        assert result["data_quality"] == "Partial"
        assert result["error_message"] == ig.get("error")


def test_clean_rows_keep_errors_empty_in_table_and_csv(tmp_path: Path) -> None:
    """Mode omissions stay visible as statuses without false error output."""
    smart = build_record("smart", IG_FULL, SKIPPED, .5, "combined_smart")
    anonymous = status_record("anonymous", "active", "", .2)
    assert smart["error_message"] is None
    assert anonymous["error_message"] is None
    assert record_to_row(1, smart)[-1] == ""
    assert "Skipped (IG country)" in record_to_row(1, smart)
    assert record_to_row(2, anonymous)[-1] == ""
    assert "Unavailable (status only)" in record_to_row(2, anonymous)
    path = export_csv([smart, anonymous], tmp_path / "clean.csv")
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["Error"] for row in rows] == ["", ""]


def test_anonymous_read_failure_keeps_error() -> None:
    """A real browser read exception must remain Unknown with a useful error."""
    page = SimpleNamespace(goto=AsyncMock(side_effect=PlaywrightError("fixture transport failure")))
    result = asyncio.run(check_status(page, "fixture", .5))
    assert result["ig_status"] == "unknown"
    assert "Anonymous page could not be read" in result["error_message"]
    assert "Status only:" not in result["error_message"]
