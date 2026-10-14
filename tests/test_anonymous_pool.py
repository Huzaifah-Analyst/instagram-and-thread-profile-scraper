"""Anonymous browser lifecycle, result completeness and unpaced scheduling."""

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.core.anonymous_status import status_record
from src.core.checkers import Checker
from src.core.scraper import MultiWorkerScraper


class AnonymousPlaywright:
    """Expose only fresh launch/context APIs; persistent launch is unavailable."""

    def __init__(self) -> None:
        """Prepare inspectable browser and empty new-context boundaries."""
        self.context = SimpleNamespace(pages=[], new_page=AsyncMock(side_effect=[object(), object()]),
                                       close=AsyncMock())
        self.browser = SimpleNamespace(new_context=AsyncMock(return_value=self.context), close=AsyncMock())
        self.chromium = SimpleNamespace(launch=AsyncMock(return_value=self.browser))

    async def __aenter__(self) -> "AnonymousPlaywright":
        """Enter the fake browser lifetime."""
        return self

    async def __aexit__(self, *args: object) -> None:
        """Allow production finally blocks to close resources."""
        return None


def test_anonymous_pool_never_uses_checkers_or_pacing(tmp_path: Path,
                                                  monkeypatch: pytest.MonkeyPatch) -> None:
    """Use fresh contexts, return exception rows and never sleep between targets."""
    browser = AnonymousPlaywright()
    monkeypatch.setattr("src.core.anonymous_status.async_playwright", lambda: browser)
    profile = tmp_path / "never_create"
    scraper = MultiWorkerScraper(
        mode="ig_status_only", workers=2, profile_dir=profile,
        checkers=[Checker("checker_1", profile)], resource_blocker_enabled=False,
    )
    pacing = AsyncMock(side_effect=AssertionError("Anonymous mode must not pace"))
    monkeypatch.setattr(scraper, "_interruptible_sleep", pacing)

    async def check(page: object, username: str, timeout_s: float) -> dict:
        """Let workers interleave and exercise one unexpected target error."""
        await asyncio.sleep(0)
        if username == "bad":
            raise ValueError("fixture")
        return status_record(username, "active", "", .01)

    monkeypatch.setattr("src.core.anonymous_status.check_status", check)
    records = scraper.run(["one", "bad", "three", "four"])
    assert [row["username"] for row in records] == ["one", "bad", "three", "four"]
    assert records[1]["ig_status"] == "unknown"
    assert scraper.checkers == scraper.active_checker_ids == []
    assert scraper.checker_health == {}
    assert scraper.unstarted_usernames == []
    assert scraper._done == 4
    assert not profile.exists()
    pacing.assert_not_awaited()
    browser.browser.new_context.assert_awaited_once_with(viewport={"width": 1280, "height": 800})
    browser.context.close.assert_awaited_once()
    browser.browser.close.assert_awaited_once()


def test_anonymous_stop_keeps_unstarted_targets(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stopping a one-worker anonymous batch returns only the completed target."""
    browser = AnonymousPlaywright()
    monkeypatch.setattr("src.core.anonymous_status.async_playwright", lambda: browser)
    scraper = MultiWorkerScraper(mode="ig_status_only", workers=1, resource_blocker_enabled=False)

    async def check(page: object, username: str, timeout_s: float) -> dict:
        """Stop while completing the first target."""
        scraper.stop()
        return status_record(username, "active", "", .01)

    monkeypatch.setattr("src.core.anonymous_status.check_status", check)
    records = scraper.run(["one", "two"])
    assert len(records) == 1
    assert scraper.unstarted_usernames == ["two"]
    browser.context.close.assert_awaited_once()
