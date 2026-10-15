"""Display explanations preserve the raw result and exported field values."""

from copy import deepcopy
from pathlib import Path

import pytest

from src.core.export import export_csv
from src.core.records import EXPORT_COLUMNS
from src.gui.components.data_table import metadata_cell, record_to_row


@pytest.mark.parametrize("platform", ["ig", "threads"])
@pytest.mark.parametrize("suffix", ["country", "date_joined"])
@pytest.mark.parametrize("status,stage,error,expected", [
    ("skipped", None, None, "Not checked"),
    ("not_found", "navigate", None, "No account"),
    ("error", "navigate", "Original failure", "Page not loaded"),
    ("active", "profile_menu", "Original failure", "Menu not found"),
    ("active", "about_menu", "Original failure", "About unavailable"),
    ("active", "about_dialog", "Original failure", "Panel incomplete"),
    ("error", "identity", None, "Identity unverified"),
    ("error", None, None, "Check failed"),
    ("active", "complete", None, "N/A"),
    ("active", None, "Other platform error", "N/A"),
])
def test_empty_metadata_uses_only_structured_state(
    platform: str, suffix: str, status: str, stage: str | None,
    error: str | None, expected: str,
) -> None:
    """Both platforms and dates use state without parsing error prose."""
    field = f"{platform}_{suffix}"
    record = {field: None, f"{platform}_status": status,
              f"{platform}_stage": stage, "error_message": error}
    original = deepcopy(record)
    assert metadata_cell(record, field) == expected
    assert record == original and record[field] is None


@pytest.mark.parametrize("mode,platform,expected", [
    ("ig_only", "threads", "Not checked"),
    ("threads_only", "ig", "Not checked"),
    ("ig_status_only", "ig", "Unavailable (status only)"),
    ("ig_status_only", "threads", "Not checked"),
    ("combined_smart", "threads", "Skipped (IG country)"),
])
@pytest.mark.parametrize("suffix", ["country", "date_joined"])
def test_mode_omissions_are_explicit(
    mode: str, platform: str, expected: str, suffix: str,
) -> None:
    """Deliberate omissions explain both country and date cells."""
    record = {"checking_mode": mode, f"{platform}_{suffix}": None}
    if mode == "combined_smart":
        record["threads_status"] = "skipped_ig_sufficient"
    assert metadata_cell(record, f"{platform}_{suffix}") == expected


@pytest.mark.parametrize("platform", ["ig", "threads"])
def test_country_disclosure_does_not_invent_a_missing_date_reason(
    platform: str,
) -> None:
    """Country availability cannot explain a missing joined date."""
    record = {f"{platform}_country": None, f"{platform}_date_joined": None,
              f"{platform}_country_availability": "not_disclosed",
              f"{platform}_stage": "complete",
              "error_message": "Platform disclosure"}
    country = metadata_cell(record, f"{platform}_country")
    assert country == "Not shown by platform"
    assert metadata_cell(record, f"{platform}_date_joined") == "N/A"
    record[f"{platform}_country"] = "Not shared"
    record[f"{platform}_country_availability"] = "not_shared"
    assert metadata_cell(record, f"{platform}_country") == "Not shared"


@pytest.mark.parametrize("platform", ["ig", "threads"])
def test_display_does_not_change_records_or_raw_export(
    platform: str, tmp_path: Path,
) -> None:
    """Rendering cannot overwrite raw None or availability states."""
    record = {"username": "fixture", "checking_mode": "combined",
              f"{platform}_country": None,
              f"{platform}_date_joined": "April 2016",
              f"{platform}_country_availability": "not_disclosed",
              f"{platform}_status": "active", f"{platform}_stage": "complete"}
    original = deepcopy(record)
    before = export_csv(
        [record], tmp_path / "before.csv", columns=EXPORT_COLUMNS,
    ).read_bytes()
    assert "Not shown by platform" in record_to_row(1, record)
    after = export_csv(
        [record], tmp_path / "after.csv", columns=EXPORT_COLUMNS,
    ).read_bytes()
    assert before == after and record == original
    assert record[f"{platform}_country"] is None
    record[f"{platform}_country"] = "Canada"
    record[f"{platform}_status"] = "error"
    assert metadata_cell(record, f"{platform}_country") == "Canada"
