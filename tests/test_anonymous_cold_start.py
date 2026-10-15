"""Cold anonymous budgets, bounded warm retries and final-only progress."""

import asyncio
from collections import Counter
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.core.anonymous_status import (
    ANONYMOUS_PAGE_READY_TIMEOUT_S, status_record,
)
from src.core.scraper import MultiWorkerScraper


def fake_browser(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Expose only fresh context APIs without a persistent browser profile."""
    context = SimpleNamespace(
        pages=[], new_page=AsyncMock(side_effect=[object(), object()]),
        close=AsyncMock(),
    )
    browser = SimpleNamespace(
        new_context=AsyncMock(return_value=context), close=AsyncMock(),
    )
    playwright = SimpleNamespace(
        chromium=SimpleNamespace(launch=AsyncMock(return_value=browser)),
    )

    @asynccontextmanager
    async def launch() -> AsyncIterator[SimpleNamespace]:
        """Provide a browser lifetime with real production finally blocks."""
        yield playwright

    monkeypatch.setattr("src.core.anonymous_status.async_playwright", launch)
    return context


def test_retry_waits_for_main_pass_and_publishes_once(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    """Unknowns get one warm attempt; successful verdicts are never retried."""
    context = fake_browser(monkeypatch)
    seen: list[tuple[int, int, dict]] = []
    events: list[dict] = []
    users = ["cold", "persistent", "ready", "missing", "last"]
    calls: Counter[str] = Counter()
    scraper = MultiWorkerScraper(
        mode="ig_status_only", workers=2, resource_blocker_enabled=False,
        profile_dir=tmp_path / "unused",
        progress_callback=lambda *args: seen.append(args),
    )
    monkeypatch.setattr(scraper, "_save_event", events.append)
    pacing = AsyncMock(side_effect=AssertionError("No account pacing"))
    monkeypatch.setattr(scraper, "_interruptible_sleep", pacing)

    async def check(page: object, username: str, timeout_s: float) -> dict:
        """Simulate cold recovery and an unresolved warm page."""
        calls[username] += 1
        assert timeout_s == ANONYMOUS_PAGE_READY_TIMEOUT_S > 10
        if calls[username] == 2:
            assert set(calls) == set(users), "Main pass must finish first"
        await asyncio.sleep(0)
        if (username == "persistent"
                or (username == "cold" and calls[username] == 1)):
            return status_record(
                username, "unknown", "No marker on this attempt", .25,
            )
        status = "not_found" if username == "missing" else "active"
        return status_record(username, status, "", .25)

    monkeypatch.setattr("src.core.anonymous_status.check_status", check)
    records = scraper.run(users)
    assert [row["username"] for row in records] == users
    assert calls == Counter(cold=2, persistent=2, ready=1, missing=1, last=1)
    assert records[0]["ig_status"] == "active"
    assert records[0]["error_message"] is None
    assert records[0]["seconds"] == .5
    assert records[1]["ig_status"] == "unknown"
    assert records[1]["error_message"] == "No marker on this attempt"
    assert [item[0] for item in seen] == [1, 2, 3, 4, 5]
    assert len({item[2]["username"] for item in seen}) == 5
    assert scraper._done == 5 and scraper.unstarted_usernames == []
    summaries = [
        event for event in events
        if event.get("event", "").startswith("anonymous_")
    ]
    journal_rows = [event for event in events if "username" in event]
    assert len(journal_rows) == 5
    assert {row["username"] for row in journal_rows} == set(users)
    assert summaries[0]["unknown_count"] == 2
    assert summaries[1]["attempts"] == 2 and summaries[1]["unknown_count"] == 1
    context.close.assert_awaited_once()
    pacing.assert_not_awaited()


@pytest.mark.parametrize("stop_during_retry", [False, True])
def test_stop_preserves_deferred_unknowns_without_duplicate_progress(
    monkeypatch: pytest.MonkeyPatch, stop_during_retry: bool,
) -> None:
    """A stopped run preserves Unknowns without starting extra retries."""
    fake_browser(monkeypatch)
    calls: Counter[str] = Counter()
    scraper = MultiWorkerScraper(mode="ig_status_only", workers=1,
                                 resource_blocker_enabled=False)

    async def check(page: object, username: str, timeout_s: float) -> dict:
        """Stop either during the main attempt or the first warm retry."""
        calls[username] += 1
        if not stop_during_retry or calls[username] == 2:
            scraper.stop()
        return status_record(username, "unknown", "Unresolved marker", .1)

    monkeypatch.setattr("src.core.anonymous_status.check_status", check)
    records = scraper.run(["one", "two"])
    assert scraper._done == len(records)
    assert all(
        row["ig_status"] == "unknown" and row["error_message"]
        for row in records
    )
    expected = Counter(one=2, two=1) if stop_during_retry else Counter(one=1)
    assert calls == expected
    assert scraper.unstarted_usernames == (
        [] if stop_during_retry else ["two"]
    )


@pytest.mark.parametrize("configured,expected", [(10, 30), (45, 45)])
def test_anonymous_budget_does_not_change_shared_budget(
    monkeypatch: pytest.MonkeyPatch, configured: float, expected: float,
) -> None:
    """Anonymous gets a longer floor; Combined keeps its own budget."""
    check = AsyncMock(return_value={"fixture": True})
    monkeypatch.setattr("src.core.anonymous_status.check_status", check)
    scraper = MultiWorkerScraper(
        mode="ig_status_only", page_ready_timeout_s=configured,
    )
    page = object()
    result = asyncio.run(scraper._check_account(page, "one"))
    assert result == {"fixture": True}
    check.assert_awaited_once_with(page, "one", expected)
    assert MultiWorkerScraper(mode="combined").page_ready_timeout_s == 10


def test_retry_exception_stays_unknown_with_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A failed retry cannot become a guessed verdict or a third attempt."""
    fake_browser(monkeypatch)
    check = AsyncMock(side_effect=[
        status_record("one", "unknown", "Main pass deadline", .1),
        RuntimeError("fixture read failure"),
    ])
    monkeypatch.setattr("src.core.anonymous_status.check_status", check)
    scraper = MultiWorkerScraper(
        mode="ig_status_only", resource_blocker_enabled=False,
    )
    records = scraper.run(["one"])
    assert check.await_count == 2
    assert records[0]["ig_status"] == "unknown"
    assert "RuntimeError" in records[0]["error_message"]
    assert scraper._done == 1
