"""Authentication, result quality and persistence regression coverage."""

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.core.about_parser import detect_session_challenge, parse_about_dialog
from src.core.ban_engine import BanLinkEngine
from src.core.checker_health import verify_platform
from src.core.diagnostics import RunJournal
from src.core.scraper import MultiWorkerScraper, build_record, empty_platform_result
from src.core.validation import clean_usernames, positive_seconds


def test_live_observed_threads_login_text_is_blocked() -> None:
    """The exact observed login heading must not become an About-menu error."""
    assert detect_session_challenge(
        "https://www.threads.com/@target", "Log in or sign up for Threads\nContinue with Instagram",
    ) == "Threads login required"
    assert detect_session_challenge("https://www.instagram.com/target/", "Log In\nSign Up")
    assert detect_session_challenge("https://www.instagram.com/loginking/", "loginking\nPosts") is None


def test_preflight_checks_platform_cookie_and_login_page() -> None:
    """An IG cookie cannot authenticate Threads, nor can a stale cookie pass a wall."""
    page = SimpleNamespace(
        url="https://www.threads.com/", goto=AsyncMock(),
        inner_text=AsyncMock(return_value="Log in or sign up for Threads\nContinue with Instagram"),
        context=SimpleNamespace(cookies=AsyncMock(return_value=[{"name": "sessionid"}])),
    )
    assert asyncio.run(verify_platform(page, "threads")) == "Threads login required"
    page.inner_text.return_value = "Home\nFollowing\nProfile\nSearch\nNotifications\nFor you"
    page.context.cookies.return_value = []
    assert "no platform session cookie" in asyncio.run(verify_platform(page, "threads"))
    page.context.cookies.assert_awaited_with("https://www.threads.com/")


def test_adjacent_label_is_not_a_date() -> None:
    """Keep a missing value empty without rewriting legitimate October dates."""
    parsed = parse_about_dialog("Date joined\nAccount based in\nChina")
    assert parsed["date_joined"] is None and parsed["country"] == "China"
    assert parse_about_dialog("Date joined\nOctober 2025")["date_joined"] == "October 2025"


def test_live_threads_not_shared_is_preserved_but_not_complete_country() -> None:
    """Exact captured label/value structure, with only identity anonymized."""
    raw = "Name\nExample (@target)\nJoined\nOctober 2025 · 100M+\nBased in\nNot shared"
    parsed = parse_about_dialog(raw)
    assert parsed == {"date_joined": "October 2025", "join_badge": "100M+", "country": "Not shared"}
    record = build_record("target", empty_platform_result(), {
        **empty_platform_result(), **parsed, "status": "active",
    }, 1)
    assert record["threads_country"] == "Not shared"
    assert record["threads_date_joined"] == "October 2025"
    assert record["data_quality"] == "Partial"


@pytest.mark.parametrize("value", [-1, 0, float("nan"), float("inf"), 121])
def test_invalid_timeouts_are_rejected(value: float) -> None:
    """Polling never accepts nonfinite, negative or excessively long budgets."""
    with pytest.raises(ValueError):
        positive_seconds(value)


def test_profile_urls_normalize_without_changing_handle() -> None:
    """Case-insensitive duplicate removal preserves the first exact handle."""
    assert clean_usernames([
        "\ufeffhttps://www.instagram.com/brenda_1074/", "@BRENDA_1074",
        "https://www.threads.com/@second.user?x=1",
    ]) == ["brenda_1074", "second.user"]
    for value in ("bad user", "https://example.com/user", "https://instagram.com/p/post"):
        with pytest.raises(ValueError):
            clean_usernames([value])


def test_data_quality_is_independent_of_account_status() -> None:
    """ACTIVE must not imply complete transparency extraction."""
    partial = {**empty_platform_result(), "status": "active", "date_joined": "April 2016"}
    assert build_record("target", partial, empty_platform_result(), 1)["data_quality"] == "Partial"
    full = {**partial, "country": "Canada"}
    assert build_record("target", full, empty_platform_result(), 1)["data_quality"] == "Complete"
    failed = {**empty_platform_result(), "status": "active", "error": "Menu missing"}
    record = build_record("target", failed, empty_platform_result(), 1)
    assert record["data_quality"] == "Failed" and record["composite_status"] == "ACTIVE"
    assert BanLinkEngine.evaluate("banned", "session_blocked")["composite_status"] == "BLOCKED"


def test_combined_checks_threads_after_ig_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    """Same-handle platforms are checked independently, without identity assumptions."""
    import src.core.scraper as module

    monkeypatch.setattr(module, "extract_instagram", AsyncMock(return_value={
        **empty_platform_result(), "status": "not_found",
    }))
    threads = AsyncMock(return_value={**empty_platform_result(), "status": "active"})
    monkeypatch.setattr(module, "extract_threads", threads)
    record = asyncio.run(MultiWorkerScraper()._check_account(object(), "target"))
    threads.assert_awaited_once()
    assert record["ig_status"] == "not_found" and record["threads_status"] == "active"


def test_global_stop_prevents_next_platform(monkeypatch: pytest.MonkeyPatch) -> None:
    """Finishing an in-flight IG request cannot start Threads after Stop."""
    import src.core.scraper as module

    scraper = MultiWorkerScraper()

    async def ig(*args: object, **kwargs: object) -> dict:
        """Simulate stop arriving while Instagram is running."""
        scraper.stop()
        return {**empty_platform_result(), "status": "active"}

    monkeypatch.setattr(module, "extract_instagram", ig)
    threads = AsyncMock()
    monkeypatch.setattr(module, "extract_threads", threads)
    asyncio.run(scraper._check_account(object(), "target"))
    threads.assert_not_awaited()


def test_journal_retains_completed_rows_before_finish(tmp_path: Path) -> None:
    """A crash after a row cannot erase earlier completed records."""
    journal = RunJournal(tmp_path)
    journal.append({"username": "target", "country": "Türkiye", "checker_id": "checker_2"})
    saved = json.loads(journal.path.read_text(encoding="utf-8"))
    assert saved["country"] == "Türkiye"
    journal.append({"event": "finished", "count": 1})
    assert len(journal.path.read_text(encoding="utf-8").splitlines()) == 2


def test_frozen_paths_ignore_extraction_and_working_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Browser state survives different onefile extraction directories."""
    import src.core.paths as paths

    monkeypatch.setattr(paths.sys, "frozen", True, raising=False)
    monkeypatch.setattr(paths.sys, "_MEIPASS", str(tmp_path / "temp"), raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "local"))
    monkeypatch.chdir(tmp_path)
    assert paths.data_root() == tmp_path / "local" / "MetaInspector"
