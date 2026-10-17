"""Independent check planning, extraction scope and export filtering."""

import asyncio
from copy import deepcopy
from itertools import combinations
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from playwright.async_api import Page

from src.core.check_plan import (
    CHECK_NAMES, apply_check_selection, metadata_fields, mode_for_checks,
    normalize_checks,
)
from src.core.dialogs import _poll_dialog
from src.core.export_selection import export_preset, filter_records
from src.core.extractors import extract_instagram, extract_threads
from src.core.scraper import MultiWorkerScraper
from src.gui.components.data_table import metadata_cell
from test_accuracy_regressions import run_browser

COMBINATIONS = [
    choice for size in range(1, len(CHECK_NAMES) + 1)
    for choice in combinations(CHECK_NAMES, size)
]


@pytest.mark.parametrize("checks", COMBINATIONS)
def test_all_nonempty_combinations_choose_only_required_platforms(
    checks: tuple[str, ...],
) -> None:
    """Every possible checkbox combination has a valid session strategy."""
    mode = mode_for_checks(checks)
    scraper = MultiWorkerScraper(checks=checks)
    assert scraper.mode == mode
    assert scraper.checks == normalize_checks(checks)
    ig = any(name.startswith("ig_") for name in checks)
    threads = any(name.startswith("threads_") for name in checks)
    if checks == ("ig_alive",):
        assert mode == "ig_status_only" and scraper.checkers == []
    else:
        expected = "combined" if ig and threads else (
            "ig_only" if ig else "threads_only"
        )
        assert mode == expected
    for platform in ("ig", "threads"):
        assert ("country" in metadata_fields(checks, platform)) == (
            f"{platform}_country" in checks
        )
        assert ("date_joined" in metadata_fields(checks, platform)) == (
            f"{platform}_age" in checks
        )


@pytest.mark.parametrize("checks", [(), ("invalid",)])
def test_empty_or_unknown_selection_is_rejected(
    checks: tuple[str, ...],
) -> None:
    """Invalid scope never starts a hidden default full check."""
    with pytest.raises(ValueError, match="Select at least"):
        MultiWorkerScraper(checks=checks)


@pytest.mark.parametrize("checks,ig_fields,threads_fields", [
    (("ig_alive", "ig_country"), ("country",), None),
    (("ig_age",), ("date_joined",), None),
    (("threads_alive",), None, ()),
    (("ig_alive", "threads_alive"), (), ()),
    (("ig_country", "threads_age"), ("country",), ("date_joined",)),
])
def test_dispatcher_passes_exact_fields_and_masks_incidental_data(
    monkeypatch: pytest.MonkeyPatch, checks: tuple[str, ...],
    ig_fields: tuple[str, ...] | None,
    threads_fields: tuple[str, ...] | None,
) -> None:
    """Exclude unselected platforms and mask incidental panel data."""
    result = {
        "status": "active", "country": "Canada", "date_joined": "April 2016",
        "join_badge": "1M+", "stage": "complete", "error": None,
    }
    extractors = {
        "ig": AsyncMock(return_value=deepcopy(result)),
        "threads": AsyncMock(return_value=deepcopy(result)),
    }
    for platform, extract in extractors.items():
        name = "instagram" if platform == "ig" else "threads"
        monkeypatch.setattr(
            f"src.core.selected_checks.extract_{name}", extract,
        )
    scraper = MultiWorkerScraper(checks=checks)
    record = asyncio.run(scraper._check_account(object(), "target"))
    assert record["requested_checks"] == list(checks)
    assert record["data_quality"] == "Complete"
    assert record["error_message"] is None
    for platform, fields in (("ig", ig_fields), ("threads", threads_fields)):
        extract = extractors[platform]
        if fields is None:
            extract.assert_not_awaited()
            assert record[f"{platform}_status"] == "skipped"
        else:
            extract.assert_awaited_once()
            assert extract.await_args.kwargs["requested_fields"] == fields
        for suffix, raw in (("country", "country"), ("age", "date_joined")):
            field = f"{platform}_{raw}"
            if f"{platform}_{suffix}" not in checks:
                assert record[field] is None
                assert metadata_cell(record, field) == "Not checked"


@pytest.mark.parametrize("platform", ["ig", "threads"])
@pytest.mark.parametrize("fields", [(), ("country",), ("date_joined",)])
def test_extractor_ignores_unrequested_panels_and_fields(
    monkeypatch: pytest.MonkeyPatch, platform: str, fields: tuple[str, ...],
) -> None:
    """Status avoids menus; country/date reads require only selected fields."""
    monkeypatch.setattr(
        "src.core.extractors._open_profile", AsyncMock(return_value="Profile"),
    )
    monkeypatch.setattr(
        "src.core.extractors.profile_matches", AsyncMock(return_value=True),
    )
    options = AsyncMock(return_value=object())
    monkeypatch.setattr("src.core.extractors._options", options)
    monkeypatch.setattr("src.core.extractors._safe_click", AsyncMock())
    monkeypatch.setattr(
        "src.core.extractors._click_menu_item", AsyncMock(return_value=True),
    )
    dismiss = AsyncMock()
    monkeypatch.setattr("src.core.extractors._dismiss", dismiss)
    parsed = {
        "country": "Canada" if fields == ("country",) else None,
        "date_joined": "April 2016" if fields == ("date_joined",) else None,
        "join_badge": None,
    }
    poll = AsyncMock(return_value=parsed)
    monkeypatch.setattr("src.core.extractors._poll_dialog", poll)
    extract = extract_instagram if platform == "ig" else extract_threads
    result = asyncio.run(extract(
        SimpleNamespace(url="https://example.test/target/"), "target",
        requested_fields=fields,
    ))
    assert result["status"] == "active"
    assert result["stage"] == "complete" and result["error"] is None
    if fields:
        assert poll.await_args.kwargs["required_fields"] == fields
    else:
        options.assert_not_awaited()
        poll.assert_not_awaited()
        dismiss.assert_not_awaited()


def test_requested_country_withheld_and_read_failures() -> None:
    """An omitted or failed requested country cannot be graded Complete."""
    withheld = {
        "ig_status": "active", "ig_country_availability": "not_disclosed",
        "ig_country": None, "ig_date_joined": "April 2016",
    }
    apply_check_selection(withheld, ("ig_country",))
    assert withheld["data_quality"] == "Partial"
    assert withheld["ig_date_joined"] is None
    failed = {"ig_status": "error", "error_message": "Read failed"}
    apply_check_selection(failed, ("ig_country",))
    assert failed["data_quality"] == "Failed"
    assert failed["error_message"] == "Read failed"


def test_real_dialog_returns_without_waiting_for_unrequested_country(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Actual Chromium date-only data satisfies a date-only request at once."""
    async def check(page: Page) -> None:
        """A sleep would prove that a nonrequested field was still awaited."""
        await page.set_content(
            '<div role="dialog">target<br>Joined<br>April 2016</div>',
        )
        original_sleep = asyncio.sleep
        waits: list[float] = []

        async def sleep(seconds: float) -> None:
            """Observe polling while preserving browser transport yields."""
            waits.append(seconds)
            await original_sleep(seconds)

        with monkeypatch.context() as patch:
            patch.setattr("src.core.dialogs.asyncio.sleep", sleep)
            result = await _poll_dialog(
                page, ('[role="dialog"]',), expected_username="target",
                required_fields=("date_joined",),
            )
        assert result["date_joined"] == "April 2016"
        assert result["country"] is None
        assert not any(seconds > 0 for seconds in waits)
    run_browser(check)


@pytest.mark.parametrize("scope,expected", [
    ("All results", ["both", "ig", "threads", "unknown"]),
    ("IG Alive only", ["both", "ig"]),
    ("Threads Alive only", ["both", "threads"]),
    ("Both Alive only", ["both"]),
])
def test_alive_filters_use_each_platform_and_snapshot_finished_rows(
    scope: str, expected: list[str],
) -> None:
    """Unknown/skipped is not Alive; later arrivals do not alter an export."""
    records = [
        {"username": "both", "ig_status": "private",
         "threads_status": "active"},
        {"username": "ig", "ig_status": "active", "threads_status": "skipped"},
        {"username": "threads", "ig_status": "not_found",
         "threads_status": "active"},
        {"username": "unknown", "ig_status": "unknown"},
    ]
    original = deepcopy(records)
    rows = filter_records(records, scope)
    assert [row["username"] for row in rows] == expected
    assert records == original
    records.append({"username": "later", "ig_status": "active"})
    assert [row["username"] for row in rows] == expected


@pytest.mark.parametrize("preset,fields", [
    ("Country only", ("Username", "IG Country", "Threads Country")),
    ("Age/joined only", ("Username", "IG Joined", "Threads Joined")),
    ("Checked fields", ("Username", "IG Status", "Threads Country")),
])
def test_export_presets_allow_requested_field_groups(
    preset: str, fields: tuple[str, ...],
) -> None:
    """Country/age/status exports are independent from diagnostic columns."""
    chosen = export_preset(preset, ("ig_alive", "threads_country"))
    assert set(chosen) == set(fields)
